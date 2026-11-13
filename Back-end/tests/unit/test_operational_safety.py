# ============================================================
# PaySentinelIQ — Operational safety: timeouts, cancellation,
# sanitized errors and failure states for upload routes.
# ============================================================

import asyncio
import threading
import uuid
from unittest.mock import patch

import fitz
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.api.documents.router import _run_canonical
from app.auth.services import AuthService
from app.core.contracts.pipeline_result import PipelineResult
from app.core.contracts.pipeline_status import PipelineStatus
from app.main import create_app
from app.services.ocr.base import OCRPageResult, OCRProvider, OCRResult
from app.services.ocr.exceptions import OCRProcessingException
from app.services.pipeline_service import DocumentPipelineService
from app.services.storage.exceptions import InvalidFileTypeError
from app.shared.database import get_db
from app.shared.orm_models import (
    DocumentModel,
    FraudAlertModel,
    TenantModel,
    UserModel,
)
from app.shared.settings import Settings
from tests.unit._storage_fakes import InMemoryStorageProvider


_BASE_SETTINGS = Settings(
    _env_file=None,
    MAX_UPLOAD_SIZE_MB=1,
    MAX_UPLOAD_REQUEST_OVERHEAD_MB=1,
    OCR_MAX_PAGES=2,
    MAX_PDF_PAGE_DIMENSION_PT=5000,
    MAX_PDF_PAGE_AREA_PT2=10_000_000,
    MAX_IMAGE_PIXELS=10_000,
    MAX_IMAGE_DIMENSION=100,
    USE_CANONICAL_PIPELINE=True,
    ENABLE_OCR=True,
    ENABLE_CANONICAL_EXTRACTION=False,
    ENABLE_SHADOW_PIPELINE=False,
    OCR_SERVICE_TIMEOUT=0.05,
)


class _NoOpInstrumentator:
    def instrument(self, app):
        return self

    def expose(self, app, **kwargs):
        return self


async def _allow_rate_limit(self, **kwargs):
    return {"limit": 1000, "remaining": 1000, "reset": 0}


@pytest_asyncio.fixture(scope="module")
async def safety_app(test_engine):
    with patch("app.main.settings", _BASE_SETTINGS):
        with patch(
            "app.main.Instrumentator",
            new=lambda *args, **kwargs: _NoOpInstrumentator(),
        ):
            app = create_app()

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with patch(
        "app.api.documents.router.get_settings",
        lambda: _BASE_SETTINGS,
    ), patch(
        "app.verification.presentation.router.get_settings",
        lambda: _BASE_SETTINGS,
    ), patch(
        "app.shared.settings.get_settings",
        lambda: _BASE_SETTINGS,
    ), patch(
        "app.shared.rate_limiter.RateLimiter.check",
        new=_allow_rate_limit,
    ):
        yield app
    app.dependency_overrides.clear()


def _use_settings(monkeypatch, **overrides):
    settings = _BASE_SETTINGS.model_copy(update=overrides)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "app.verification.presentation.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: settings,
    )
    return settings


async def _seed_tenant(db_session, label: str = "safety") -> uuid.UUID:
    tenant_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name=f"{label}-{tenant_id}",
            slug=f"{label}-{tenant_id}",
            plan="starter",
            is_active=True,
        )
    )
    await db_session.commit()
    return tenant_id


async def _seed_user(
    db_session,
    tenant_id: uuid.UUID,
    *,
    label: str = "safety-user",
    role: str = "fraud_analyst",
) -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"{label}-{user_id}@example.com",
            full_name="Safety Test User",
            hashed_password=AuthService.hash_password("correct-password"),
            role=role,
            is_active=True,
        )
    )
    await db_session.commit()
    return user_id


def _login_payload(email: str) -> dict[str, object]:
    return {
        "email": email,
        "password": "correct-password",
        "consent_given": True,
        "terms_version": "1.0.0",
        "privacy_version": "1.0.0",
    }


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _login(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/auth/login", json=_login_payload(email))
    assert response.status_code == 200
    return response.json()["access_token"]


def _pdf_bytes(*, blank: bool = False) -> bytes:
    document = fitz.open()
    try:
        page = document.new_page()
        if not blank:
            page.insert_text((72, 72), "Boleto safety test")
        return document.tobytes()
    finally:
        document.close()


async def _count(db_session, model) -> int:
    return (
        await db_session.execute(select(func.count()).select_from(model))
    ).scalar_one()


class _SlowOCRProvider(OCRProvider):
    supports_hard_timeout = True

    def __init__(
        self,
        delay: float,
        started: threading.Event,
        cancelled: threading.Event,
    ) -> None:
        self._delay = delay
        self._started = started
        self._cancelled = cancelled

    async def extract_text(self, file_path: str) -> OCRResult:
        self._started.set()
        try:
            await asyncio.sleep(self._delay)
            return OCRResult(
                text="OCR safety text",
                pages=[
                    OCRPageResult(
                        page_number=1,
                        text="OCR safety text",
                        confidence=0.9,
                    )
                ],
                confidence=0.9,
                provider="slow-fake",
            )
        finally:
            self._cancelled.set()

    async def health_check(self) -> bool:
        return True

    def get_info(self) -> dict[str, str]:
        return {"provider": "slow-fake"}


class _FailingOCRProvider(OCRProvider):
    supports_hard_timeout = True

    def __init__(self, message: str) -> None:
        self._message = message

    async def extract_text(self, file_path: str) -> OCRResult:
        raise OCRProcessingException(self._message, provider="fake")

    async def health_check(self) -> bool:
        return False

    def get_info(self) -> dict[str, str]:
        return {"provider": "failing-fake"}


class _EmptyOCRProvider(OCRProvider):
    supports_hard_timeout = True

    async def extract_text(self, file_path: str) -> OCRResult:
        return OCRResult(text="", pages=[], confidence=0.0, provider="empty-fake")

    async def health_check(self) -> bool:
        return True

    def get_info(self) -> dict[str, str]:
        return {"provider": "empty-fake"}


class _LegacyPipeline:
    def __init__(self, *, result=None, error=None):
        self._result = result
        self._error = error

    async def process_document(self, **kwargs):
        if self._error is not None:
            raise self._error
        return self._result


def _patch_legacy_pipeline(monkeypatch, pipeline: _LegacyPipeline) -> None:
    monkeypatch.setattr(
        "app.verification.presentation.router.get_pipeline_service",
        lambda: pipeline,
    )


def _patch_canonical_pipeline(monkeypatch, test_engine) -> InMemoryStorageProvider:
    storage = InMemoryStorageProvider()
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        lambda: storage,
    )
    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )

    async def no_event(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.api.documents.router._publish_analysis_event",
        no_event,
    )
    monkeypatch.setattr(
        "app.api.documents.router._send_analysis_notification",
        no_event,
    )
    return storage


# ── Legacy route: sanitized errors + correlation ID ────────


@pytest.mark.asyncio
async def test_legacy_pipeline_failure_response_is_sanitized(
    safety_app,
    db_session,
    caplog,
):
    tenant_id = await _seed_tenant(db_session, "legacy-return")
    user_id = await _seed_user(db_session, tenant_id, label="legacy-return")
    secret = "SUPER_SECRET /tmp/private SQL SELECT * FROM users"
    fake = _LegacyPipeline(
        result={"pipeline_status": "failed", "error": secret}
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"legacy-return-{user_id}@example.com")
        with patch(
            "app.verification.presentation.router.get_pipeline_service",
            lambda: fake,
        ):
            response = await client.post(
                "/api/verifications/upload",
                files={
                    "file": (
                        "boleto.pdf",
                        _pdf_bytes(),
                        "application/pdf",
                    )
                },
                headers=_bearer(token),
            )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body.get("s3_key") is None
    assert body.get("presigned_url") is None
    assert body.get("correlation_id")
    assert response.headers.get("x-correlation-id") == body["correlation_id"]
    assert "SUPER_SECRET" not in response.text
    assert "SELECT" not in response.text
    assert "/tmp/" not in response.text
    assert "SUPER_SECRET" not in caplog.text


@pytest.mark.asyncio
async def test_legacy_unexpected_failure_is_sanitized(
    safety_app,
    db_session,
    caplog,
):
    tenant_id = await _seed_tenant(db_session, "legacy-raise")
    user_id = await _seed_user(db_session, tenant_id, label="legacy-raise")
    secret = "SUPER_SECRET /tmp/private SQL INSERT INTO documents"
    fake = _LegacyPipeline(error=RuntimeError(secret))

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"legacy-raise-{user_id}@example.com")
        with patch(
            "app.verification.presentation.router.get_pipeline_service",
            lambda: fake,
        ):
            response = await client.post(
                "/api/verifications/upload",
                files={
                    "file": (
                        "boleto.pdf",
                        _pdf_bytes(),
                        "application/pdf",
                    )
                },
                headers=_bearer(token),
            )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail.get("correlation_id")
    assert response.headers.get("x-correlation-id") == detail["correlation_id"]
    assert "SUPER_SECRET" not in response.text
    assert "SELECT" not in response.text
    assert "INSERT" not in response.text
    assert "/tmp/" not in response.text
    assert "SUPER_SECRET" not in caplog.text


@pytest.mark.asyncio
async def test_legacy_invalid_type_failure_is_sanitized(
    safety_app,
    db_session,
):
    tenant_id = await _seed_tenant(db_session, "legacy-type")
    user_id = await _seed_user(db_session, tenant_id, label="legacy-type")
    fake = _LegacyPipeline(
        error=InvalidFileTypeError(
            "/tmp/SUPER_SECRET.exe",
            ["application/pdf"],
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"legacy-type-{user_id}@example.com")
        with patch(
            "app.verification.presentation.router.get_pipeline_service",
            lambda: fake,
        ):
            response = await client.post(
                "/api/verifications/upload",
                files={
                    "file": (
                        "boleto.pdf",
                        _pdf_bytes(),
                        "application/pdf",
                    )
                },
                headers=_bearer(token),
            )

    assert response.status_code == 415
    assert "SUPER_SECRET" not in response.text
    assert "/tmp/" not in response.text


# ── OCR operational failures: explicit state, no persistence ─


async def _assert_no_persisted_rows(db_session, tenant_id):
    db_session.expire_all()
    documents = (
        await db_session.execute(
            select(DocumentModel).where(DocumentModel.tenant_id == tenant_id)
        )
    ).scalars().all()
    alerts = (
        await db_session.execute(
            select(FraudAlertModel).where(FraudAlertModel.tenant_id == tenant_id)
        )
    ).scalars().all()
    assert documents == []
    assert alerts == []


@pytest.mark.asyncio
async def test_ocr_timeout_is_explicit_and_does_not_persist(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "ocr-timeout")
    user_id = await _seed_user(db_session, tenant_id, label="ocr-timeout")
    storage = _patch_canonical_pipeline(monkeypatch, test_engine)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
    )
    _use_settings(
        monkeypatch,
        ENABLE_OCR=True,
        OCR_SERVICE_TIMEOUT=0.05,
    )

    started = threading.Event()
    cancelled = threading.Event()
    provider = _SlowOCRProvider(0.5, started, cancelled)
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: provider,
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"ocr-timeout-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto", "observations": "test"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(blank=True),
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error"] == "ocr_timeout"
    assert detail["correlation_id"]
    assert response.headers.get("x-correlation-id") == detail["correlation_id"]
    assert started.is_set()
    assert cancelled.is_set()
    assert storage.uploaded_keys == []
    await _assert_no_persisted_rows(db_session, tenant_id)


@pytest.mark.asyncio
async def test_ocr_unavailable_is_explicit_and_does_not_persist(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
    caplog,
):
    tenant_id = await _seed_tenant(db_session, "ocr-unavailable")
    user_id = await _seed_user(db_session, tenant_id, label="ocr-unavailable")
    storage = _patch_canonical_pipeline(monkeypatch, test_engine)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
    )
    _use_settings(monkeypatch, ENABLE_OCR=True)
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: _FailingOCRProvider(
            "Could not connect to OCR service SUPER_SECRET /tmp/private"
        ),
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(
            client,
            f"ocr-unavailable-{user_id}@example.com",
        )
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(blank=True),
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error"] == "ocr_unavailable"
    assert detail["correlation_id"]
    assert "SUPER_SECRET" not in response.text
    assert "SUPER_SECRET" not in caplog.text
    assert storage.uploaded_keys == []
    await _assert_no_persisted_rows(db_session, tenant_id)


@pytest.mark.asyncio
async def test_ocr_invalid_response_is_explicit_and_does_not_persist(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "ocr-invalid")
    user_id = await _seed_user(db_session, tenant_id, label="ocr-invalid")
    storage = _patch_canonical_pipeline(monkeypatch, test_engine)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
    )
    _use_settings(monkeypatch, ENABLE_OCR=True)
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: _FailingOCRProvider(
            "OCR service returned invalid JSON"
        ),
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"ocr-invalid-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(blank=True),
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 502
    detail = response.json()["detail"]
    assert detail["error"] == "ocr_invalid_response"
    assert detail["correlation_id"]
    assert storage.uploaded_keys == []
    await _assert_no_persisted_rows(db_session, tenant_id)


@pytest.mark.asyncio
async def test_ocr_empty_is_inconclusive_and_does_not_persist(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "ocr-empty")
    user_id = await _seed_user(db_session, tenant_id, label="ocr-empty")
    storage = _patch_canonical_pipeline(monkeypatch, test_engine)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
    )
    _use_settings(monkeypatch, ENABLE_OCR=True)
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: _EmptyOCRProvider(),
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"ocr-empty-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(blank=True),
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["error"] == "analysis_inconclusive"
    assert detail["correlation_id"]
    assert storage.uploaded_keys == []
    await _assert_no_persisted_rows(db_session, tenant_id)


# ── Generic canonical failure: sanitized error ─────────────


@pytest.mark.asyncio
async def test_canonical_unexpected_error_is_sanitized(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
    caplog,
):
    tenant_id = await _seed_tenant(db_session, "canonical-error")
    user_id = await _seed_user(db_session, tenant_id, label="canonical-error")
    _patch_canonical_pipeline(monkeypatch, test_engine)
    _use_settings(monkeypatch, ENABLE_OCR=False)
    secret = "SUPER_SECRET /tmp/private SQL SELECT * FROM documents"

    def explode(self, ctx):
        raise RuntimeError(secret)

    monkeypatch.setattr(
        "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
        explode,
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(
            client,
            f"canonical-error-{user_id}@example.com",
        )
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(),
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 500
    detail = response.json()["detail"]
    assert detail["error"] == "analysis_error"
    assert detail["correlation_id"]
    assert response.headers.get("x-correlation-id") == detail["correlation_id"]
    assert "SUPER_SECRET" not in response.text
    assert "SELECT" not in response.text
    assert "/tmp/" not in response.text
    assert "SUPER_SECRET" not in caplog.text
    await _assert_no_persisted_rows(db_session, tenant_id)


# ── Legacy pipeline service: storage compensation on OCR failure ─


@pytest.mark.asyncio
async def test_legacy_pipeline_service_removes_upload_after_ocr_failure(
    monkeypatch,
):
    storage = InMemoryStorageProvider()
    monkeypatch.setattr(
        "app.services.pipeline_service.get_ocr_provider",
        lambda *args, **kwargs: _FailingOCRProvider(
            "OCR service unavailable SUPER_SECRET"
        ),
    )
    service = DocumentPipelineService(storage=storage)

    result = await service.process_document(
        file_data=_pdf_bytes(),
        file_name="boleto.pdf",
        content_type="application/pdf",
        tenant_id=str(uuid.uuid4()),
        user_id=str(uuid.uuid4()),
        extra_context={"document_type": "boleto"},
    )

    assert result["pipeline_status"] == "failed"
    assert result["error"] == "processing_error"
    assert "SUPER_SECRET" not in str(result)
    assert storage.uploaded_keys
    assert storage.deleted_keys == storage.uploaded_keys
    assert storage.objects == {}


# ── Cancellation: what stops and what continues ────────────


@pytest.mark.asyncio
async def test_client_cancellation_cancels_remote_ocr_without_persisting(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "cancel-ocr")
    user_id = await _seed_user(db_session, tenant_id, label="cancel-ocr")
    _patch_canonical_pipeline(monkeypatch, test_engine)
    _use_settings(
        monkeypatch,
        ENABLE_OCR=True,
        OCR_SERVICE_TIMEOUT=5.0,
    )

    started = threading.Event()
    cancelled = threading.Event()
    provider = _SlowOCRProvider(5.0, started, cancelled)
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: provider,
    )

    async with AsyncClient(
        transport=ASGITransport(app=safety_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"cancel-ocr-{user_id}@example.com")
        task = asyncio.create_task(
            client.post(
                "/api/documents/analyze",
                data={"document_type": "boleto"},
                files={
                    "file": (
                        "boleto.pdf",
                        _pdf_bytes(blank=True),
                        "application/pdf",
                    )
                },
                headers=_bearer(token),
            )
        )
        await asyncio.to_thread(started.wait, 1.0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    assert cancelled.wait(1.0)
    await _assert_no_persisted_rows(db_session, tenant_id)


@pytest.mark.asyncio
async def test_pipeline_thread_continues_after_client_cancellation(
    safety_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "cancel-thread")
    user_id = await _seed_user(db_session, tenant_id, label="cancel-thread")
    _patch_canonical_pipeline(monkeypatch, test_engine)
    _use_settings(monkeypatch, ENABLE_OCR=False)

    started = threading.Event()
    release = threading.Event()
    finished = threading.Event()

    def slow_execute(self, ctx):
        started.set()
        release.wait(3.0)
        finished.set()
        return PipelineResult(
            pipeline_status=PipelineStatus.SUCCESS,
            risk_score=10.0,
            risk_level="LOW",
            confidence=0.0,
        )

    monkeypatch.setattr(
        "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
        slow_execute,
    )
    document_id = str(uuid.uuid4())

    task = asyncio.create_task(
        _run_canonical(
            _pdf_bytes(),
            "boleto",
            document_id,
            "boleto.pdf",
            "application/pdf",
            str(tenant_id),
            str(user_id),
            "",
        )
    )
    await asyncio.to_thread(started.wait, 1.0)
    task.cancel()
    release.set()
    with pytest.raises(asyncio.CancelledError):
        await task

    assert finished.wait(1.0)
    await _assert_no_persisted_rows(db_session, tenant_id)
