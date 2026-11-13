import hashlib
import uuid

import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from prometheus_client import REGISTRY
from sqlalchemy import select

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_result import PipelineResult
from app.main import create_app
from app.services.ocr.base import OCRPageResult, OCRResult
from app.shared.orm_models import (
    DocumentModel,
    FraudAlertModel,
    TenantModel,
    UserModel,
)
from app.shared.settings import Settings
from tests.unit._storage_fakes import InMemoryStorageProvider
from tests.unit._validation_helpers import build_linha_digitavel

BOLETO_PT = """
Beneficiário: ACME SERVIÇOS LTDA
CNPJ: 12.345.678/0001-90
Pagador: JOÃO DA SILVA
Data de Vencimento: 20/01/2099
Valor do Documento: R$ 1.234,56
Nosso Número: 12345678901
Nº do Documento: 98765
Código do Banco: 001
"""

BOLETO_ES = """
Beneficiario: SERVICIOS ANDINOS S.A.
CNPJ: 12.345.678/0001-90
Pagador: JUAN PEREZ
Fecha de vencimiento: 20/01/2099
Valor del documento: R$ 1.234,56
Nuestro número: 12345678901
Número del documento: 98765
Código del banco: 001
Banco: 001
"""

BOLETO_EN = """
Beneficiary: ANDEAN SERVICES INC.
CNPJ: 12.345.678/0001-90
Payer: JOHN DOE
Due Date: 20/01/2099
Document Amount: 1,234.56
Our Number: 12345678901
Document Number: 98765
Bank Code: 001
Banco: 001
"""

FIXTURES = [
    ("pt", BOLETO_PT),
    ("es", BOLETO_ES),
    ("en", BOLETO_EN),
]


class FakeOCRProvider:
    def __init__(self, text: str):
        self.text = text

    async def extract_text(self, file_path: str) -> OCRResult:
        return OCRResult(
            text=self.text,
            pages=[
                OCRPageResult(
                    page_number=1,
                    text=self.text,
                    confidence=0.9,
                )
            ],
            confidence=0.9,
            provider="fake",
            processing_time_seconds=0.2,
            metadata={"native_pages": "0", "ocr_pages": "1"},
        )


def _pdf_bytes() -> bytes:
    document = fitz.open()
    document.new_page()
    data = document.tobytes()
    document.close()
    return data


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=True,
        ENABLE_CANONICAL_EXTRACTION=True,
        ENABLE_SHADOW_PIPELINE=False,
    )


def _install_storage(monkeypatch) -> InMemoryStorageProvider:
    storage = InMemoryStorageProvider()
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        lambda: storage,
    )
    return storage


def _reset_inprogress_metric() -> None:
    collector = REGISTRY._names_to_collectors.get(
        "http_requests_inprogress"
    )
    if collector is not None:
        try:
            REGISTRY.unregister(collector)
        except KeyError:
            pass


@pytest.fixture(scope="module")
def router_app():
    _reset_inprogress_metric()
    application = create_app()
    yield application
    _reset_inprogress_metric()


@pytest.mark.asyncio
@pytest.mark.parametrize(("language", "text"), FIXTURES)
async def test_router_canonical_with_ocr_prelude(
    language,
    text,
    router_app,
    db_session,
    test_engine,
    monkeypatch,
):
    settings = _settings()
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "app.services.ocr.factory.get_ocr_provider",
        lambda *args, **kwargs: FakeOCRProvider(text),
    )
    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )
    storage = _install_storage(monkeypatch)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
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

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name="OCR Tenant",
            slug=f"ocr-{tenant_id}",
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"ocr-{user_id}@example.com",
            full_name="OCR User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()

    router_app.dependency_overrides[get_current_tenant_id] = (
        lambda: str(tenant_id)
    )
    router_app.dependency_overrides[get_current_user_id] = (
        lambda: str(user_id)
    )

    pdf_bytes = _pdf_bytes()
    async with AsyncClient(
        transport=ASGITransport(app=router_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert "risk_score" in body
    assert "risk_level" in body
    assert "RISK_ASSESSMENT" in body
    assert "ANOMALY_LIST" in body
    assert "AI_REASONING_SUMMARY" in body
    assert "extracted_metadata" in body

    # HTTP contract keeps the pipeline confidence on the 0-100 scale.
    assert body["confidence"] == 90.0
    assert body["RISK_ASSESSMENT"]["ai_confidence"] == 90.0
    assert body["persistence_status"] == "saved"

    extraction = body["extraction"]
    assert extraction["language"]["lang"] == language
    assert extraction["method"] == "fake"
    assert extraction["ocr_status"] == "completed"
    assert extraction["ocr_confidence"] == 90.0
    assert extraction["page_count"] == 1
    assert extraction["ocr_seconds"] == 0.2
    assert extraction["fields"]["beneficiario"]["value"]
    assert extraction["fields"]["valor_nominal"]["value"] == "1234.56"

    assert body["extracted_metadata"]["amount"] == "1234.56"
    assert body["extracted_metadata"]["due_date"] == "20/01/2099"
    assert body["extracted_metadata"]["bank_code"] == "001"

    document_id = uuid.UUID(body["document_id"])
    result = await db_session.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    document = result.scalar_one()
    assert document.extracted_fields is not None
    assert document.extracted_fields["valor_nominal"] == 1234.56
    assert document.extracted_fields["amount"] == 1234.56
    assert document.extracted_fields["canonical"]["beneficiario"]["value"]
    assert document.ocr_confidence == 90.0
    assert document.s3_key
    assert document.s3_bucket == storage.bucket
    assert document.file_hash == hashlib.sha256(pdf_bytes).hexdigest()
    assert await storage.download_file(document.s3_key) == pdf_bytes


@pytest.mark.asyncio
async def test_router_reports_failed_persistence_without_partial_rows(
    router_app,
    db_session,
    test_engine,
    monkeypatch,
):
    settings = Settings(
        _env_file=None,
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=False,
        ENABLE_CANONICAL_EXTRACTION=False,
        ENABLE_SHADOW_PIPELINE=False,
    )
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    result = PipelineResult(
        risk_score=85.0,
        risk_level="BROKEN",
        confidence=91.0,
        evidence=[
            Evidence(
                code="PERSISTENCE_TEST",
                description="Falha posterior proposital",
                severity=Severity.HIGH,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.99,
            )
        ],
        reasoning_summary="Falha de persistencia simulada",
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

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name="Persistence Failure Tenant",
            slug=f"persistence-failure-{tenant_id}",
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"persistence-failure-{user_id}@example.com",
            full_name="Persistence Failure User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()

    router_app.dependency_overrides[get_current_tenant_id] = (
        lambda: str(tenant_id)
    )
    router_app.dependency_overrides[get_current_user_id] = (
        lambda: str(user_id)
    )

    pdf_bytes = _pdf_bytes()
    async with AsyncClient(
        transport=ASGITransport(app=router_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "failed"
    assert "IntegrityError" not in response.text
    assert "chk_fraud_risk_level" not in response.text
    assert "INSERT INTO" not in response.text

    assert len(storage.uploaded_keys) == 1
    assert storage.uploaded_blobs == [pdf_bytes]
    assert storage.deleted_keys == storage.uploaded_keys
    assert storage.objects == {}

    document_id = uuid.UUID(body["document_id"])
    documents = (
        (
            await db_session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
        )
        .scalars()
        .all()
    )
    alerts = (
        (
            await db_session.execute(
                select(FraudAlertModel).where(
                    FraudAlertModel.document_id == document_id
                )
            )
        )
        .scalars()
        .all()
    )
    assert documents == []
    assert alerts == []


@pytest.mark.asyncio
async def test_router_persists_original_file_and_alert(
    router_app,
    db_session,
    test_engine,
    monkeypatch,
):
    settings = Settings(
        _env_file=None,
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=False,
        ENABLE_CANONICAL_EXTRACTION=False,
        ENABLE_SHADOW_PIPELINE=False,
    )
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    result = PipelineResult(
        risk_score=85.0,
        risk_level="HIGH",
        confidence=91.0,
        evidence=[
            Evidence(
                code="ORIGINAL_FILE_TEST",
                description="Evidencia de fraude",
                severity=Severity.HIGH,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.99,
            )
        ],
        reasoning_summary="Documento com indicios de fraude",
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

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name="Original File Tenant",
            slug=f"original-file-{tenant_id}",
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"original-file-{user_id}@example.com",
            full_name="Original File User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()

    router_app.dependency_overrides[get_current_tenant_id] = (
        lambda: str(tenant_id)
    )
    router_app.dependency_overrides[get_current_user_id] = (
        lambda: str(user_id)
    )

    pdf_bytes = _pdf_bytes()
    async with AsyncClient(
        transport=ASGITransport(app=router_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={"file": ("boleto.pdf", pdf_bytes, "application/pdf")},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "saved"
    assert body["confidence"] == 91.0

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

    assert document.s3_key
    assert document.s3_bucket == storage.bucket
    assert document.file_hash == hashlib.sha256(pdf_bytes).hexdigest()
    assert await storage.download_file(document.s3_key) == pdf_bytes
    assert alert.ai_confidence == pytest.approx(0.91)
    assert alert.risk_score == pytest.approx(85.0)
    assert alert.risk_level == "high"


@pytest.mark.asyncio
async def test_router_reports_storage_failure_without_database_rows(
    router_app,
    db_session,
    test_engine,
    monkeypatch,
):
    settings = Settings(
        _env_file=None,
        USE_CANONICAL_PIPELINE=True,
        ENABLE_OCR=False,
        ENABLE_CANONICAL_EXTRACTION=False,
        ENABLE_SHADOW_PIPELINE=False,
    )
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)
    storage.fail_upload = True

    result = PipelineResult(
        risk_score=85.0,
        risk_level="HIGH",
        confidence=91.0,
        evidence=[
            Evidence(
                code="STORAGE_FAILURE_TEST",
                description="Evidencia de fraude",
                severity=Severity.HIGH,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.99,
            )
        ],
        reasoning_summary="Documento com indicios de fraude",
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

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name="Storage Failure Tenant",
            slug=f"storage-failure-{tenant_id}",
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"storage-failure-{user_id}@example.com",
            full_name="Storage Failure User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()

    router_app.dependency_overrides[get_current_tenant_id] = (
        lambda: str(tenant_id)
    )
    router_app.dependency_overrides[get_current_user_id] = (
        lambda: str(user_id)
    )

    pdf_bytes = _pdf_bytes()
    async with AsyncClient(
        transport=ASGITransport(app=router_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    pdf_bytes,
                    "application/pdf",
                )
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["persistence_status"] == "failed"
    assert "simulated upload failure" not in response.text
    assert "UploadFailedError" not in response.text
    assert "Traceback" not in response.text

    document_id = uuid.UUID(body["document_id"])
    documents = (
        (
            await db_session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
        )
        .scalars()
        .all()
    )
    alerts = (
        (
            await db_session.execute(
                select(FraudAlertModel).where(
                    FraudAlertModel.document_id == document_id
                )
            )
        )
        .scalars()
        .all()
    )
    assert documents == []
    assert alerts == []
    assert storage.uploaded_keys == []
    assert storage.objects == {}


LINHA_VALID = build_linha_digitavel(factor=2000, value_cents=123456)

BOLETO_VALID = f"""
Beneficiário: ACME SERVIÇOS LTDA
CNPJ: 12.345.678/0001-95
Pagador: JOÃO DA SILVA
Data de Vencimento: 19/11/2027
Valor do Documento: R$ 1.234,56
Linha Digitável: {LINHA_VALID}
"""

BOLETO_ADULTERATED = BOLETO_VALID.replace(
    "R$ 1.234,56",
    "R$ 1.300,00",
)


@pytest.mark.asyncio
async def test_router_exposes_validation_and_changes_risk(
    router_app,
    db_session,
    test_engine,
    monkeypatch,
):
    settings = _settings()
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)
    monkeypatch.setattr(
        "app.api.documents.router.get_settings",
        lambda: settings,
    )
    monkeypatch.setattr(
        "app.shared.database.get_engine",
        lambda: test_engine,
    )
    storage = _install_storage(monkeypatch)
    monkeypatch.setattr(
        "app.services.pipeline.stages.crewai_stage.CrewAIStage._execute",
        lambda self, ctx: None,
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

    async def run_document(text: str) -> dict:
        tenant_id = uuid.uuid4()
        user_id = uuid.uuid4()
        db_session.add(
            TenantModel(
                id=tenant_id,
                name="Validation Tenant",
                slug=f"validation-{tenant_id}",
            )
        )
        db_session.add(
            UserModel(
                id=user_id,
                tenant_id=tenant_id,
                email=f"validation-{user_id}@example.com",
                full_name="Validation User",
                hashed_password="not-used",
            )
        )
        await db_session.commit()
        router_app.dependency_overrides[get_current_tenant_id] = (
            lambda: str(tenant_id)
        )
        router_app.dependency_overrides[get_current_user_id] = (
            lambda: str(user_id)
        )
        monkeypatch.setattr(
            "app.services.ocr.factory.get_ocr_provider",
            lambda *args, **kwargs: FakeOCRProvider(text),
        )
        async with AsyncClient(
            transport=ASGITransport(app=router_app),
            base_url="http://test",
        ) as client:
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
            )
        assert response.status_code == 200
        return response.json()

    consistent = await run_document(BOLETO_VALID)
    assert consistent["risk_score"] < 70
    assert consistent["metadata"]["validation"]["document_type"] == "boleto"
    assert (
        consistent["metadata"]["validation"]["boleto_decoded"]["status"]
        == "ok"
    )
    assert consistent["metadata"]["validation"]["findings"] == {}

    adulterated = await run_document(BOLETO_ADULTERATED)
    # OCR provenance mitigation (5B.6) downgrades the critical amount mismatch
    # by one level, so the OCR path lands in MEDIUM instead of HIGH.
    assert adulterated["risk_score"] >= 40
    assert (
        "BOLETO_AMOUNT_MISMATCH"
        in adulterated["metadata"]["validation"]["findings"]
    )

    assert consistent["persistence_status"] == "saved"
    assert adulterated["persistence_status"] == "saved"
    assert len(storage.uploaded_keys) == 2
    assert len(set(storage.uploaded_keys)) == 2


