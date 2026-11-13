# ============================================================
# PaySentinelIQ — Documents persistence tests
# ============================================================

import hashlib
import uuid

import pytest
from sqlalchemy import select

from app.api.documents.router import _persist_analysis
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.shared.domain_primitives import percent_confidence_to_ratio
from app.shared.orm_models import DocumentModel, FraudAlertModel, TenantModel, UserModel
from tests.unit._storage_fakes import InMemoryStorageProvider


def _install_storage(monkeypatch) -> InMemoryStorageProvider:
    storage = InMemoryStorageProvider()
    monkeypatch.setattr(
        "app.api.documents.router._get_storage_provider",
        lambda: storage,
    )
    return storage


async def _seed_tenant_and_user(db_session) -> tuple[uuid.UUID, uuid.UUID]:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(id=tenant_id, name="Persistence Tenant", slug=f"tenant-{tenant_id}")
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=f"user-{user_id}@example.com",
            full_name="Persistence User",
            hashed_password="not-used",
        )
    )
    await db_session.commit()
    return tenant_id, user_id


def _build_context(
    document_id: uuid.UUID,
    tenant_id: uuid.UUID,
    *,
    ocr_confidence: float = 93.0,
) -> PipelineContext:
    return PipelineContext(
        document_id=str(document_id),
        tenant_id=str(tenant_id),
        file_bytes=b"%PDF-1.4 test document",
        filename="boleto.pdf",
        mime_type="application/pdf",
        document_type="boleto",
        extracted_fields={"cnpj": "12345678000199"},
        ocr_confidence=ocr_confidence,
    )


def _build_result(
    *,
    risk_score: float = 85.0,
    risk_level: str = "HIGH",
    confidence: float = 91.0,
) -> PipelineResult:
    return PipelineResult(
        risk_score=risk_score,
        risk_level=risk_level,
        confidence=confidence,
        evidence=[
            Evidence(
                code="CNPJ_INVALIDO",
                description="CNPJ invalido",
                severity=Severity.HIGH,
                source=EvidenceSource.DETERMINISTIC,
                confidence=0.99,
            )
        ],
        reasoning_summary="Documento com indicios de fraude",
    )


async def _documents_for(db_session, document_id: uuid.UUID) -> list[DocumentModel]:
    result = await db_session.execute(
        select(DocumentModel).where(DocumentModel.id == document_id)
    )
    return list(result.scalars().all())


async def _alerts_for(db_session, document_id: uuid.UUID) -> list[FraudAlertModel]:
    result = await db_session.execute(
        select(FraudAlertModel).where(FraudAlertModel.document_id == document_id)
    )
    return list(result.scalars().all())


@pytest.mark.asyncio
async def test_persist_analysis_creates_document_and_fraud_alert(
    test_engine, db_session, monkeypatch
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_id = uuid.uuid4()
    ctx = _build_context(document_id, tenant_id)
    result = _build_result()

    persisted = await _persist_analysis(
        ctx, result, str(document_id), str(tenant_id), str(user_id)
    )

    assert persisted is True
    documents = await _documents_for(db_session, document_id)
    assert len(documents) == 1
    document = documents[0]
    assert document.tenant_id == tenant_id
    assert document.uploaded_by == user_id
    assert document.document_type == "boleto"
    assert document.file_name == "boleto.pdf"
    assert document.file_size_bytes == len(ctx.file_bytes)
    assert document.ocr_status == "pending"
    assert document.ocr_confidence == pytest.approx(93.0)
    assert document.extracted_fields == {"cnpj": "12345678000199"}
    assert document.s3_key
    assert document.s3_bucket == storage.bucket
    assert document.file_hash == hashlib.sha256(ctx.file_bytes).hexdigest()
    assert document.file_hash == document.file_hash.lower()
    assert storage.uploaded_keys == [document.s3_key]
    assert await storage.download_file(document.s3_key) == ctx.file_bytes
    assert storage.uploaded_content_types == ["application/pdf"]

    alerts = await _alerts_for(db_session, document_id)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.tenant_id == tenant_id
    assert alert.risk_level == "high"
    assert alert.risk_score == pytest.approx(85.0)
    assert alert.ai_confidence == pytest.approx(0.91)
    assert 0.0 <= alert.ai_confidence <= 1.0
    assert alert.ai_explanation == "Documento com indicios de fraude"
    assert any(
        field["field_name"] == "CNPJ_INVALIDO"
        and field["confidence"] == pytest.approx(99.0)
        for field in alert.flagged_fields
    )
    assert alert.status == "new"


@pytest.mark.asyncio
async def test_persist_analysis_without_alert_keeps_document(
    test_engine, db_session, monkeypatch
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_id = uuid.uuid4()
    ctx = _build_context(document_id, tenant_id)
    result = _build_result(risk_score=42.0, risk_level="MEDIUM")

    assert (
        await _persist_analysis(
            ctx, result, str(document_id), str(tenant_id), str(user_id)
        )
        is True
    )

    documents = await _documents_for(db_session, document_id)
    assert len(documents) == 1
    assert documents[0].ocr_confidence == pytest.approx(93.0)
    assert documents[0].s3_key
    assert documents[0].s3_bucket == storage.bucket
    assert storage.objects[documents[0].s3_key] == ctx.file_bytes
    assert await _alerts_for(db_session, document_id) == []


@pytest.mark.asyncio
async def test_persist_analysis_rolls_back_document_when_alert_write_fails(
    test_engine, db_session, monkeypatch, caplog
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_id = uuid.uuid4()
    ctx = _build_context(document_id, tenant_id)
    result = _build_result(risk_level="BROKEN")

    caplog.set_level("ERROR", logger="app.api.documents.router")
    assert (
        await _persist_analysis(
            ctx, result, str(document_id), str(tenant_id), str(user_id)
        )
        is False
    )

    assert await _documents_for(db_session, document_id) == []
    assert await _alerts_for(db_session, document_id) == []
    assert len(storage.uploaded_keys) == 1
    assert storage.deleted_keys == storage.uploaded_keys
    assert storage.objects == {}
    assert any(
        "Failed to persist document/fraud alert" in record.getMessage()
        for record in caplog.records
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_confidence", [-0.1, 100.1])
async def test_invalid_confidence_is_rejected_without_partial_persistence(
    invalid_confidence, test_engine, db_session, monkeypatch
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_id = uuid.uuid4()
    ctx = _build_context(document_id, tenant_id)
    result = _build_result(confidence=invalid_confidence)

    assert (
        await _persist_analysis(
            ctx, result, str(document_id), str(tenant_id), str(user_id)
        )
        is False
    )

    assert await _documents_for(db_session, document_id) == []
    assert await _alerts_for(db_session, document_id) == []
    assert len(storage.uploaded_keys) == 1
    assert storage.deleted_keys == storage.uploaded_keys
    assert storage.objects == {}


@pytest.mark.asyncio
async def test_persist_analysis_uses_distinct_storage_keys(
    test_engine, db_session, monkeypatch
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_ids = [uuid.uuid4(), uuid.uuid4()]

    for document_id in document_ids:
        ctx = _build_context(document_id, tenant_id)
        result = _build_result()
        assert (
            await _persist_analysis(
                ctx, result, str(document_id), str(tenant_id), str(user_id)
            )
            is True
        )

    documents = [
        (await _documents_for(db_session, document_id))[0]
        for document_id in document_ids
    ]
    assert documents[0].s3_key
    assert documents[1].s3_key
    assert documents[0].s3_key != documents[1].s3_key
    assert set(storage.objects) == {documents[0].s3_key, documents[1].s3_key}


@pytest.mark.asyncio
async def test_persist_analysis_logs_orphan_when_compensation_delete_fails(
    test_engine, db_session, monkeypatch, caplog
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)
    storage = _install_storage(monkeypatch)
    storage.fail_delete = True

    tenant_id, user_id = await _seed_tenant_and_user(db_session)
    document_id = uuid.uuid4()
    ctx = _build_context(document_id, tenant_id)
    result = _build_result(risk_level="BROKEN")

    caplog.set_level("WARNING", logger="app.api.documents.router")
    assert (
        await _persist_analysis(
            ctx, result, str(document_id), str(tenant_id), str(user_id)
        )
        is False
    )

    assert await _documents_for(db_session, document_id) == []
    assert await _alerts_for(db_session, document_id) == []
    assert len(storage.uploaded_keys) == 1
    assert storage.objects
    assert any(
        "Orphan storage object remains" in record.getMessage()
        for record in caplog.records
    )


@pytest.mark.parametrize(
    ("confidence_percent", "expected_ratio"),
    [(0.0, 0.0), (1.0, 0.01), (91.0, 0.91), (100.0, 1.0)],
)
def test_percent_confidence_to_ratio_limits(confidence_percent, expected_ratio):
    assert percent_confidence_to_ratio(confidence_percent) == pytest.approx(
        expected_ratio
    )


@pytest.mark.parametrize(
    "invalid_confidence",
    [-0.1, -1.0, 100.1, 101.0, float("nan"), float("inf"), float("-inf")],
)
def test_percent_confidence_to_ratio_rejects_invalid_values(invalid_confidence):
    with pytest.raises(ValueError):
        percent_confidence_to_ratio(invalid_confidence)
