# ============================================================
# PaySentinelIQ — Upload validation and resource-limit tests
# ============================================================

import hashlib
import io
import uuid
from unittest.mock import patch

import fitz
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.auth.services import AuthService
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_result import PipelineResult
from app.main import create_app
from app.shared.database import get_db
from app.shared.orm_models import (
    DocumentModel,
    FraudAlertModel,
    TenantModel,
    UserModel,
)
from app.services.upload_validation import (
    UploadPolicy,
    UploadValidationError,
    sanitize_filename,
    validate_upload_bytes,
)
from app.shared.settings import Settings
from app.shared.upload_limits import UploadBodyLimitMiddleware
from tests.unit._storage_fakes import InMemoryStorageProvider


class _NoOpInstrumentator:
    def instrument(self, app):
        return self

    def expose(self, app, **kwargs):
        return self


async def _allow_rate_limit(self, **kwargs):
    return {"limit": 1000, "remaining": 1000, "reset": 0}


@pytest_asyncio.fixture(scope="module")
async def upload_app(test_engine):
    test_settings = Settings(
        _env_file=None,
        MAX_UPLOAD_SIZE_MB=1,
        MAX_UPLOAD_REQUEST_OVERHEAD_MB=1,
        OCR_MAX_PAGES=2,
        MAX_PDF_PAGE_DIMENSION_PT=5000,
        MAX_PDF_PAGE_AREA_PT2=10_000_000,
        MAX_IMAGE_PIXELS=10_000,
        MAX_IMAGE_DIMENSION=100,
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=False,
        ENABLE_CANONICAL_EXTRACTION=False,
        ENABLE_SHADOW_PIPELINE=False,
    )

    with patch("app.main.settings", test_settings):
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
        lambda: test_settings,
    ), patch(
        "app.verification.presentation.router.get_settings",
        lambda: test_settings,
    ), patch(
        "app.shared.rate_limiter.RateLimiter.check",
        new=_allow_rate_limit,
    ):
        yield app
    app.dependency_overrides.clear()


async def _seed_tenant(db_session, label: str = "upload") -> uuid.UUID:
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
    label: str = "upload-user",
    role: str = "fraud_analyst",
) -> uuid.UUID:
    user_id = uuid.uuid4()
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"{label}-{user_id}@example.com",
            full_name="Upload Test User",
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


def _pdf_bytes(pages: int = 1) -> bytes:
    doc = fitz.open()
    try:
        for index in range(pages):
            page = doc.new_page()
            page.insert_text((72, 72), f"Boleto test page {index + 1}")
        return doc.tobytes()
    finally:
        doc.close()


def _pdf_with_size(target_size: int) -> bytes:
    base = _pdf_bytes()
    marker = b"%%EOF"
    index = base.rfind(marker)
    assert index != -1
    padding_size = target_size - len(base) - 2
    assert padding_size >= 0
    padding = b"%" + b"A" * padding_size + b"\n"
    data = base[:index] + padding + base[index:]
    assert len(data) == target_size
    return data


def _image_bytes(fmt: str, size: tuple[int, int] = (20, 20)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=(200, 30, 30)).save(buffer, format=fmt)
    return buffer.getvalue()


def _encrypted_pdf_bytes() -> bytes:
    doc = fitz.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), "Encrypted boleto")
        return doc.tobytes(
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner-secret",
            user_pw="user-secret",
        )
    finally:
        doc.close()


def _install_pipeline(
    monkeypatch,
    test_engine,
    *,
    risk_score: float = 20.0,
    risk_level: str = "LOW",
    confidence: float = 91.0,
):
    fake_storage = InMemoryStorageProvider()
    pipeline_calls: list[bool] = []
    storage_calls: list[bool] = []

    result = PipelineResult(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=confidence,
        evidence=[
            Evidence(
                code="UPLOAD_TEST",
                description="Upload test evidence",
                severity=Severity.LOW,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.9,
            )
        ],
        reasoning_summary="Upload test",
    )

    def execute(self, ctx):
        pipeline_calls.append(True)
        return result

    def get_storage():
        storage_calls.append(True)
        return fake_storage

    async def no_event(*args, **kwargs):
        return None

    monkeypatch.setattr(
        "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
        execute,
    )
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        get_storage,
    )
    monkeypatch.setattr(
        "app.api.documents.router._publish_analysis_event",
        no_event,
    )
    monkeypatch.setattr(
        "app.api.documents.router._send_analysis_notification",
        no_event,
    )
    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )
    return fake_storage, pipeline_calls, storage_calls


async def _count(db_session, model) -> int:
    return (
        await db_session.execute(select(func.count()).select_from(model))
    ).scalar_one()


@pytest.mark.asyncio
async def test_valid_pdf_is_accepted_and_persisted(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-pdf")
    user_id = await _seed_user(db_session, tenant_id, label="upload-pdf")
    storage, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
        risk_score=85.0,
        risk_level="HIGH",
    )
    pdf_bytes = _pdf_bytes()

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-pdf-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "saved"
    assert pipeline_calls == [True]
    assert storage_calls == [True]

    document_id = uuid.UUID(body["document_id"])
    document = (
        await db_session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
    ).scalar_one()
    alert = (
        await db_session.execute(
            select(FraudAlertModel).where(
                FraudAlertModel.document_id == document_id
            )
        )
    ).scalar_one()

    assert document.tenant_id == tenant_id
    assert document.uploaded_by == user_id
    assert document.s3_key
    assert document.s3_bucket == storage.bucket
    assert document.file_hash == hashlib.sha256(pdf_bytes).hexdigest()
    assert await storage.download_file(document.s3_key) == pdf_bytes
    assert storage.uploaded_content_types == ["application/pdf"]
    assert alert.ai_confidence == pytest.approx(0.91)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fmt", "filename", "declared_type", "expected_type", "expected_ext"),
    [
        ("PNG", "receipt.png", "image/png", "image/png", ".png"),
        ("JPEG", "receipt.jpg", "image/jpeg", "image/jpeg", ".jpg"),
        (
            "PNG",
            "receipt.png",
            "application/octet-stream",
            "image/png",
            ".png",
        ),
    ],
)
async def test_valid_images_are_accepted_with_validated_type(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
    fmt,
    filename,
    declared_type,
    expected_type,
    expected_ext,
):
    tenant_id = await _seed_tenant(db_session, f"upload-{fmt.lower()}")
    user_id = await _seed_user(
        db_session,
        tenant_id,
        label=f"upload-{fmt.lower()}",
    )
    storage, _, _ = _install_pipeline(
        monkeypatch,
        test_engine,
        risk_score=20.0,
        risk_level="LOW",
    )
    image_bytes = _image_bytes(fmt)

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(
            client,
            f"upload-{fmt.lower()}-{user_id}@example.com",
        )
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": (filename, image_bytes, declared_type)},
            headers=_bearer(token),
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "saved"

    document_id = uuid.UUID(body["document_id"])
    document = (
        await db_session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
    ).scalar_one()

    assert document.s3_key.endswith(expected_ext)
    assert expected_type in storage.uploaded_content_types


@pytest.mark.asyncio
async def test_file_size_limit_plus_one_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-size")
    user_id = await _seed_user(db_session, tenant_id, label="upload-size")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    oversized_pdf = _pdf_with_size(1_048_577)
    db_session.expire_all()
    before_documents = await _count(db_session, DocumentModel)

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-size-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", oversized_pdf, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 413
    assert pipeline_calls == []
    assert storage_calls == []
    assert await _count(db_session, DocumentModel) == before_documents
    assert "Traceback" not in response.text


@pytest.mark.asyncio
async def test_request_body_limit_is_enforced_before_parser(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-body")
    user_id = await _seed_user(db_session, tenant_id, label="upload-body")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    db_session.expire_all()
    before_documents = await _count(db_session, DocumentModel)

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-body-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", b"A" * 2_500_000, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 413, response.text
    assert pipeline_calls == []
    assert storage_calls == []
    assert await _count(db_session, DocumentModel) == before_documents


@pytest.mark.asyncio
async def test_empty_file_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-empty")
    user_id = await _seed_user(db_session, tenant_id, label="upload-empty")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-empty-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", b"", "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code in {400, 422}
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_random_bytes_disguised_as_pdf_are_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-random")
    user_id = await _seed_user(db_session, tenant_id, label="upload-random")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-random-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    b"this is not a pdf at all",
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 415
    assert pipeline_calls == []
    assert storage_calls == []
    assert "this is not a pdf" not in response.text
    assert "Traceback" not in response.text
    assert "fitz" not in response.text.lower()
    assert "Pillow" not in response.text


@pytest.mark.asyncio
async def test_mime_and_extension_mismatch_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-mismatch")
    user_id = await _seed_user(db_session, tenant_id, label="upload-mismatch")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    png_bytes = _image_bytes("PNG")

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-mismatch-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", png_bytes, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 415
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_truncated_pdf_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-truncated-pdf")
    user_id = await _seed_user(
        db_session,
        tenant_id,
        label="upload-truncated-pdf",
    )
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    pdf_bytes = _pdf_bytes()[:-50]

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(
            client,
            f"upload-truncated-pdf-{user_id}@example.com",
        )
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 422
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_truncated_image_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-truncated-image")
    user_id = await _seed_user(
        db_session,
        tenant_id,
        label="upload-truncated-image",
    )
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    image_bytes = _image_bytes("PNG")
    truncated = image_bytes[: len(image_bytes) // 2]

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(
            client,
            f"upload-truncated-image-{user_id}@example.com",
        )
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("receipt.png", truncated, "image/png")},
            headers=_bearer(token),
        )

    assert response.status_code == 422
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_pdf_page_limit_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-pages")
    user_id = await _seed_user(db_session, tenant_id, label="upload-pages")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    pdf_bytes = _pdf_bytes(pages=3)

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-pages-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 422
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_image_pixel_limit_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-pixels")
    user_id = await _seed_user(db_session, tenant_id, label="upload-pixels")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    image_bytes = _image_bytes("PNG", size=(200, 200))

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-pixels-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("receipt.png", image_bytes, "image/png")},
            headers=_bearer(token),
        )

    assert response.status_code == 422
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_encrypted_pdf_is_rejected(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-encrypted")
    user_id = await _seed_user(db_session, tenant_id, label="upload-encrypted")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    pdf_bytes = _encrypted_pdf_bytes()

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-encrypted-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
            headers=_bearer(token),
        )

    assert response.status_code == 415
    assert pipeline_calls == []
    assert storage_calls == []


@pytest.mark.asyncio
async def test_filename_does_not_control_storage_key(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-name")
    user_id = await _seed_user(db_session, tenant_id, label="upload-name")
    storage, _, _ = _install_pipeline(
        monkeypatch,
        test_engine,
        risk_score=20.0,
        risk_level="LOW",
    )
    pdf_bytes = _pdf_bytes()

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-name-{user_id}@example.com")
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "../../evil\x00.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 200
    body = response.json()
    document_id = uuid.UUID(body["document_id"])
    document = (
        await db_session.execute(
            select(DocumentModel).where(DocumentModel.id == document_id)
        )
    ).scalar_one()

    assert ".." not in document.s3_key
    assert "evil" not in document.s3_key
    assert ".." not in document.file_name
    assert "/" not in document.file_name
    assert "\x00" not in document.file_name
    assert document.file_name.endswith(".pdf")
    assert document.s3_key in storage.objects


@pytest.mark.asyncio
async def test_legacy_upload_route_applies_same_validation(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    tenant_id = await _seed_tenant(db_session, "upload-legacy")
    user_id = await _seed_user(db_session, tenant_id, label="upload-legacy")
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        token = await _login(client, f"upload-legacy-{user_id}@example.com")
        response = await client.post(
            "/api/verifications/upload",
            files={
                "file": (
                    "boleto.pdf",
                    b"this is not a pdf at all",
                    "application/pdf",
                )
            },
            headers=_bearer(token),
        )

    assert response.status_code == 415
    assert pipeline_calls == []
    assert storage_calls == []


def test_sanitize_filename_strips_paths_and_control_chars():
    assert sanitize_filename("../../relatório\x00.pdf") == "relatório.pdf"
    assert sanitize_filename("C:\\temp\\arquivo.pdf") == "arquivo.pdf"
    assert sanitize_filename("..") == "document"


def _direct_policy(max_file_bytes: int) -> UploadPolicy:
    return UploadPolicy(
        max_file_bytes=max_file_bytes,
        max_pdf_pages=2,
        max_pdf_page_dimension_pt=5000,
        max_pdf_page_area_pt2=10_000_000,
        max_image_pixels=10_000,
        max_image_dimension=100,
    )


def test_file_exactly_at_limit_is_accepted():
    pdf_bytes = _pdf_bytes()

    validated = validate_upload_bytes(
        pdf_bytes,
        declared_content_type="application/pdf",
        file_name="boleto.pdf",
        policy=_direct_policy(len(pdf_bytes)),
    )

    assert validated.content_type == "application/pdf"
    assert validated.extension == ".pdf"
    assert validated.data == pdf_bytes


def test_file_one_byte_over_limit_is_rejected_directly():
    pdf_bytes = _pdf_bytes()

    with pytest.raises(UploadValidationError) as exc_info:
        validate_upload_bytes(
            pdf_bytes,
            declared_content_type="application/pdf",
            file_name="boleto.pdf",
            policy=_direct_policy(len(pdf_bytes) - 1),
        )

    assert exc_info.value.status_code == 413


def test_malformed_pdf_with_valid_magic_is_rejected():
    data = b"%PDF-1.7\n" + b"garbage" * 100 + b"\n%%EOF\n"

    with pytest.raises(UploadValidationError) as exc_info:
        validate_upload_bytes(
            data,
            declared_content_type="application/pdf",
            file_name="boleto.pdf",
            policy=_direct_policy(1024 * 1024),
        )

    assert exc_info.value.status_code in {415, 422}


async def _run_middleware(
    *,
    path: str,
    chunks: list[bytes],
    headers: list[tuple[bytes, bytes]],
    max_bytes: int,
):
    app_called = False
    sent: list[dict] = []

    async def inner(scope, receive, send):
        nonlocal app_called
        app_called = True
        while True:
            message = await receive()
            if message["type"] != "http.request" or not message.get(
                "more_body", False
            ):
                break
        await send(
            {"type": "http.response.start", "status": 200, "headers": []}
        )
        await send({"type": "http.response.body", "body": b"ok"})

    middleware = UploadBodyLimitMiddleware(inner, max_bytes=max_bytes)
    scope = {
        "type": "http",
        "method": "POST",
        "path": path,
        "headers": headers,
    }
    pending = list(chunks)

    async def receive():
        if pending:
            body = pending.pop(0)
            return {
                "type": "http.request",
                "body": body,
                "more_body": bool(pending),
            }
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    await middleware(scope, receive, send)
    return app_called, sent


@pytest.mark.asyncio
async def test_body_limit_middleware_counts_without_content_length():
    app_called, sent = await _run_middleware(
        path="/api/documents/analyze",
        chunks=[b"a" * 6, b"b" * 6],
        headers=[],
        max_bytes=10,
    )

    assert app_called is False
    assert sent[0]["type"] == "http.response.start"
    assert sent[0]["status"] == 413


@pytest.mark.asyncio
async def test_body_limit_middleware_ignores_understated_content_length():
    app_called, sent = await _run_middleware(
        path="/api/documents/analyze",
        chunks=[b"a" * 6, b"b" * 6],
        headers=[(b"content-length", b"1")],
        max_bytes=10,
    )

    assert app_called is False
    assert sent[0]["status"] == 413


@pytest.mark.asyncio
async def test_body_limit_middleware_allows_exact_limit():
    app_called, sent = await _run_middleware(
        path="/api/documents/analyze",
        chunks=[b"a" * 5, b"b" * 5],
        headers=[],
        max_bytes=10,
    )

    assert app_called is True
    assert sent[0]["status"] == 200


@pytest.mark.asyncio
async def test_body_limit_middleware_does_not_affect_other_paths():
    app_called, sent = await _run_middleware(
        path="/health",
        chunks=[b"a" * 20],
        headers=[],
        max_bytes=10,
    )

    assert app_called is True
    assert sent[0]["status"] == 200


@pytest.mark.asyncio
async def test_anonymous_upload_is_rejected_before_work(
    upload_app,
    db_session,
    test_engine,
    monkeypatch,
):
    _, pipeline_calls, storage_calls = _install_pipeline(
        monkeypatch,
        test_engine,
    )
    pdf_bytes = _pdf_bytes()
    db_session.expire_all()
    before_documents = await _count(db_session, DocumentModel)

    async with AsyncClient(
        transport=ASGITransport(app=upload_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 401
    assert pipeline_calls == []
    assert storage_calls == []
    assert await _count(db_session, DocumentModel) == before_documents
