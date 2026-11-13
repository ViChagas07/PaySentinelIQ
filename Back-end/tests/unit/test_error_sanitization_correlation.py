"""PR-07 regression tests for error sanitization and correlation."""

from __future__ import annotations

import io
import json
import logging
import re
import uuid
from unittest.mock import patch

import fitz
import pytest
import pytest_asyncio
from botocore.exceptions import ClientError
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from starlette.requests import Request

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_result import PipelineResult
from app.main import create_app
from app.services.storage.exceptions import UploadFailedError
from app.services.storage.s3_storage import S3StorageProvider
from app.shared.orm_models import (
    DocumentModel,
    FraudAlertModel,
    TenantModel,
    UserModel,
)
from app.shared.settings import Settings
from tests.unit._storage_fakes import InMemoryStorageProvider


CANARY_CREDENTIAL = "AKIA-PR07-CANARY-CREDENTIAL-9F4C2A"
CANARY_ENDPOINT = "https://s3.pr07-canary.invalid.internal"
CANARY_KEY = "receipts/pr07-canary-tenant/00000000-pr07-canary.pdf"
CANARY_FILE_NAME = "pr07-canary-secret-file-name.pdf"
CANARY_SQL = "SELECT password_hash FROM pr07_canary_users WHERE token='pr07-canary-sql'"
CANARY_MESSAGE = (
    f"credential={CANARY_CREDENTIAL}; endpoint={CANARY_ENDPOINT}; "
    f"key={CANARY_KEY}; file_name={CANARY_FILE_NAME}; sql={CANARY_SQL}"
)
CANARIES = (
    CANARY_CREDENTIAL,
    CANARY_ENDPOINT,
    CANARY_KEY,
    CANARY_FILE_NAME,
    CANARY_SQL,
)

_CORRELATION_RE = re.compile(
    r"correlation_id=([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12})"
)

_BASE_SETTINGS = Settings(
    _env_file=None,
    MAX_UPLOAD_SIZE_MB=1,
    MAX_UPLOAD_REQUEST_OVERHEAD_MB=1,
    USE_CANONICAL_PIPELINE=True,
    ENABLE_OCR=False,
    ENABLE_CANONICAL_EXTRACTION=False,
    ENABLE_SHADOW_PIPELINE=False,
)


class _NoOpInstrumentator:
    def instrument(self, app):
        return self

    def expose(self, app, **kwargs):
        return self


async def _allow_rate_limit(self, **kwargs):
    return {"limit": 1000, "remaining": 1000, "reset": 0}


@pytest_asyncio.fixture(scope="module")
async def sanitization_app(test_engine):
    with patch("app.main.settings", _BASE_SETTINGS):
        with patch(
            "app.main.Instrumentator",
            new=lambda *args, **kwargs: _NoOpInstrumentator(),
        ):
            app = create_app()
    with patch(
        "app.shared.settings.get_settings",
        lambda: _BASE_SETTINGS,
    ), patch(
        "app.shared.rate_limiter.RateLimiter.check",
        new=_allow_rate_limit,
    ):
        yield app


@pytest.fixture(autouse=True)
def _clear_dependency_overrides(sanitization_app):
    yield
    sanitization_app.dependency_overrides.clear()


def _settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: _BASE_SETTINGS,
    )
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _BASE_SETTINGS,
    )


def _override_auth(app, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
    app.dependency_overrides[get_current_tenant_id] = lambda: str(tenant_id)
    app.dependency_overrides[get_current_user_id] = lambda: str(user_id)


async def _seed_tenant_and_user(db_session, label: str):
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name=f"{label}-{tenant_id}",
            slug=f"{label}-{tenant_id}",
            plan="starter",
            is_active=True,
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"{label}-{user_id}@example.com",
            full_name="PR07 Test User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()
    return tenant_id, user_id


def _pdf_bytes() -> bytes:
    document = fitz.open()
    try:
        page = document.new_page()
        page.insert_text((72, 72), "PR-07 sanitization test")
        return document.tobytes()
    finally:
        document.close()


def _result(
    *,
    risk_score: float = 85.0,
    risk_level: str = "HIGH",
) -> PipelineResult:
    return PipelineResult(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=91.0,
        evidence=[
            Evidence(
                code="PR07_TEST",
                description="PR-07 test evidence",
                severity=Severity.HIGH,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.99,
            )
        ],
        reasoning_summary="PR-07 test reasoning",
    )


def _patch_analysis(
    monkeypatch,
    test_engine,
    storage,
    result: PipelineResult,
) -> None:
    _settings(monkeypatch)
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        lambda: storage,
    )
    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )
    monkeypatch.setattr(
        "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
        lambda self, ctx: result,
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


async def _post_analyze(app, *, headers=None):
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        return await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    _pdf_bytes(),
                    "application/pdf",
                )
            },
            headers=headers or {},
        )


def _assert_no_canaries(*texts: str) -> None:
    for text in texts:
        for canary in CANARIES:
            assert canary not in text


def _assert_no_traceback(caplog) -> None:
    for record in caplog.records:
        assert record.exc_info is None
        assert record.exc_text is None
    assert "Traceback" not in caplog.text


def _logged_correlation_ids(caplog, logger_name: str) -> list[str]:
    ids: list[str] = []
    for record in caplog.records:
        if record.name == logger_name:
            ids.extend(_CORRELATION_RE.findall(record.getMessage()))
    return ids


async def _documents_for(db_session, document_id: uuid.UUID):
    result = await db_session.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    return list(result.scalars().all())


async def _alerts_for(db_session, document_id: uuid.UUID):
    result = await db_session.execute(
        select(FraudAlertModel).where(FraudAlertModel.document_id == document_id)
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_storage_upload_failure_is_sanitized_and_correlated(
    sanitization_app,
    db_session,
    test_engine,
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    tenant_id, user_id = await _seed_tenant_and_user(db_session, "pr07-upload")
    _override_auth(sanitization_app, tenant_id, user_id)

    storage = InMemoryStorageProvider()

    async def fail_upload(*args, **kwargs):
        raise RuntimeError(CANARY_MESSAGE)

    monkeypatch.setattr(storage, "upload_file", fail_upload)
    _patch_analysis(monkeypatch, test_engine, storage, _result())

    response = await _post_analyze(sanitization_app)

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "failed"
    assert body["persistence_status"] != "saved"
    correlation_id = response.headers.get("x-correlation-id")
    assert correlation_id is not None
    uuid.UUID(correlation_id)

    _assert_no_canaries(response.text, caplog.text)
    _assert_no_traceback(caplog)

    ids = _logged_correlation_ids(caplog, "app.api.documents.router")
    assert ids
    assert all(value.lower() == correlation_id.lower() for value in ids)
    assert any(
        "event=document_storage_upload_failed" in record.getMessage()
        for record in caplog.records
        if record.name == "app.api.documents.router"
    )
    assert storage.uploaded_keys == []
    assert await _documents_for(db_session, uuid.UUID(body["document_id"])) == []


@pytest.mark.asyncio
async def test_non_fatal_persistence_failure_is_correlated_and_compensated(
    sanitization_app,
    db_session,
    test_engine,
    monkeypatch,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    tenant_id, user_id = await _seed_tenant_and_user(db_session, "pr07-persist")
    _override_auth(sanitization_app, tenant_id, user_id)

    storage = InMemoryStorageProvider()
    _patch_analysis(monkeypatch, test_engine, storage, _result())

    class ExplodingAlert:
        def __init__(self, **kwargs):
            raise RuntimeError(CANARY_MESSAGE)

    monkeypatch.setattr("app.shared.orm_models.FraudAlertModel", ExplodingAlert)

    response = await _post_analyze(sanitization_app)

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "failed"
    assert body["persistence_status"] != "saved"
    correlation_id = response.headers.get("x-correlation-id")
    assert correlation_id is not None
    uuid.UUID(correlation_id)

    _assert_no_canaries(response.text, caplog.text)
    _assert_no_traceback(caplog)

    ids = _logged_correlation_ids(caplog, "app.api.documents.router")
    assert ids
    assert all(value.lower() == correlation_id.lower() for value in ids)
    assert any(
        "event=document_persistence_failed" in record.getMessage()
        for record in caplog.records
        if record.name == "app.api.documents.router"
    )

    document_id = uuid.UUID(body["document_id"])
    assert await _documents_for(db_session, document_id) == []
    assert await _alerts_for(db_session, document_id) == []
    assert len(storage.uploaded_keys) == 1
    assert storage.deleted_keys == storage.uploaded_keys
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_catchall_returns_generic_500_with_matching_correlation_id(
    sanitization_app,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    handler = sanitization_app.exception_handlers[Exception]
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/pr07-canary-endpoint",
            "raw_path": b"/api/pr07-canary-endpoint",
            "query_string": b"",
            "headers": [],
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 12345),
            "root_path": "",
            "http_version": "1.1",
        }
    )

    response = await handler(request, RuntimeError(CANARY_MESSAGE))
    payload = json.loads(response.body)
    detail = payload["detail"]
    correlation_id = detail["correlation_id"]

    assert response.status_code == 500
    assert detail["error"] == "internal_error"
    assert detail["message"] == "Internal server error"
    uuid.UUID(correlation_id)
    assert response.headers["x-correlation-id"] == correlation_id
    assert "/api/pr07-canary-endpoint" not in response.body.decode()
    assert CANARY_MESSAGE not in response.body.decode()
    _assert_no_canaries(response.body.decode(), caplog.text)
    _assert_no_traceback(caplog)

    ids = _logged_correlation_ids(caplog, "app.main")
    assert ids
    assert all(value.lower() == correlation_id.lower() for value in ids)
    assert any(
        "event=unhandled_exception" in record.getMessage()
        for record in caplog.records
        if record.name == "app.main"
    )


@pytest.mark.asyncio
async def test_catchall_uses_valid_incoming_correlation_id(
    sanitization_app,
    caplog,
):
    caplog.set_level(logging.DEBUG)
    handler = sanitization_app.exception_handlers[Exception]
    incoming = str(uuid.uuid4())
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/pr07-correlation",
            "raw_path": b"/pr07-correlation",
            "query_string": b"",
            "headers": [(b"x-correlation-id", incoming.encode())],
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 12345),
            "root_path": "",
            "http_version": "1.1",
        }
    )

    response = await handler(request, RuntimeError(CANARY_MESSAGE))
    detail = json.loads(response.body)["detail"]

    assert detail["correlation_id"] == incoming
    assert response.headers["x-correlation-id"] == incoming
    ids = _logged_correlation_ids(caplog, "app.main")
    assert ids
    assert all(value == incoming for value in ids)
    _assert_no_canaries(response.body.decode(), caplog.text)


@pytest.mark.asyncio
async def test_catchall_replaces_invalid_correlation_id(
    sanitization_app,
):
    handler = sanitization_app.exception_handlers[Exception]
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/pr07-invalid-correlation",
            "raw_path": b"/pr07-invalid-correlation",
            "query_string": b"",
            "headers": [(b"x-correlation-id", b"not-a-uuid")],
            "scheme": "http",
            "server": ("test", 80),
            "client": ("test", 12345),
            "root_path": "",
            "http_version": "1.1",
        }
    )

    response = await handler(request, RuntimeError(CANARY_MESSAGE))
    correlation_id = json.loads(response.body)["detail"]["correlation_id"]

    assert correlation_id != "not-a-uuid"
    uuid.UUID(correlation_id)
    assert response.headers["x-correlation-id"] == correlation_id


class _FakeS3Client:
    class exceptions:
        class NoSuchKey(Exception):
            pass

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], bytes] = {}
        self.fail_put = False
        self.fail_delete = False
        self.fail_presign = False

    def put_object(self, Bucket, Key, Body, **kwargs):
        if self.fail_put:
            raise ClientError(
                {"Error": {"Code": "500", "Message": CANARY_MESSAGE}},
                "PutObject",
            )
        self.objects[(Bucket, Key)] = bytes(Body)

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise self.exceptions.NoSuchKey()
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def delete_object(self, Bucket, Key):
        if self.fail_delete:
            raise ClientError(
                {"Error": {"Code": "500", "Message": CANARY_MESSAGE}},
                "DeleteObject",
            )
        self.objects.pop((Bucket, Key), None)

    def generate_presigned_url(self, *args, **kwargs):
        if self.fail_presign:
            raise RuntimeError(CANARY_MESSAGE)
        return "https://storage.test/presigned"


def _s3_provider(monkeypatch) -> tuple[S3StorageProvider, _FakeS3Client]:
    client = _FakeS3Client()
    monkeypatch.setattr(
        "app.services.storage.s3_storage.boto3.client",
        lambda *args, **kwargs: client,
    )
    monkeypatch.setattr(
        "app.services.storage.s3_storage._get_s3_settings",
        lambda: Settings(_env_file=None),
    )
    provider = S3StorageProvider(bucket="pr07-canary-bucket", region="us-east-1")
    return provider, client


@pytest.mark.asyncio
async def test_s3_upload_failure_logs_are_sanitized(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    provider, client = _s3_provider(monkeypatch)
    client.fail_put = True

    with pytest.raises(UploadFailedError):
        await provider.upload_file(
            b"pr07 bytes",
            CANARY_KEY,
            "application/pdf",
        )

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert "event=s3_upload_failed" in caplog.text


@pytest.mark.asyncio
async def test_s3_delete_failure_logs_are_sanitized(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    provider, client = _s3_provider(monkeypatch)
    client.fail_delete = True

    assert await provider.delete_file(CANARY_KEY) is False

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert "event=s3_delete_failed" in caplog.text


@pytest.mark.asyncio
async def test_s3_success_paths_log_without_storage_key(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    provider, client = _s3_provider(monkeypatch)
    data = b"pr07 success bytes"

    result = await provider.upload_file(data, CANARY_KEY, "application/pdf")
    assert result.success is True
    assert result.presigned_url == "https://storage.test/presigned"
    assert await provider.download_file(CANARY_KEY) == data
    assert await provider.delete_file(CANARY_KEY) is True

    _assert_no_canaries(caplog.text)
    _assert_no_traceback(caplog)
    assert "event=s3_upload_succeeded" in caplog.text
    assert "event=s3_download_succeeded" in caplog.text
    assert "event=s3_delete_succeeded" in caplog.text


@pytest.mark.asyncio
async def test_s3_presign_failure_keeps_successful_upload(monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    provider, client = _s3_provider(monkeypatch)
    client.fail_presign = True

    result = await provider.upload_file(
        b"pr07 presign bytes",
        CANARY_KEY,
        "application/pdf",
    )

    assert result.success is True
    assert result.presigned_url is None
    assert await provider.download_file(CANARY_KEY) == b"pr07 presign bytes"
    _assert_no_canaries(caplog.text)
    assert "event=s3_presign_failed" in caplog.text


@pytest.mark.asyncio
async def test_saved_flow_remains_successful(
    sanitization_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id, user_id = await _seed_tenant_and_user(db_session, "pr07-saved")
    _override_auth(sanitization_app, tenant_id, user_id)

    storage = InMemoryStorageProvider()
    _patch_analysis(monkeypatch, test_engine, storage, _result())

    response = await _post_analyze(sanitization_app)

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "saved"

    document_id = uuid.UUID(body["document_id"])
    documents = await _documents_for(db_session, document_id)
    alerts = await _alerts_for(db_session, document_id)
    assert len(documents) == 1
    assert len(alerts) == 1
    assert documents[0].s3_key in storage.objects
    assert await storage.download_file(documents[0].s3_key) == storage.objects[documents[0].s3_key]
