# ============================================================
# PaySentinelIQ — Documents persistence tests
# ============================================================

import uuid

import pytest
from sqlalchemy import select

from app.api.documents.router import _persist_analysis
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.shared.orm_models import DocumentModel, FraudAlertModel, TenantModel, UserModel


@pytest.mark.asyncio
async def test_persist_analysis_creates_document_and_fraud_alert(
    test_engine, db_session, monkeypatch
):
    monkeypatch.setattr("app.shared.database.get_engine", lambda: test_engine)

    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    document_id = uuid.uuid4()

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

    ctx = PipelineContext(
        document_id=str(document_id),
        tenant_id=str(tenant_id),
        file_bytes=b"%PDF-1.4 test document",
        filename="boleto.pdf",
        mime_type="application/pdf",
        document_type="boleto",
        extracted_fields={"cnpj": "12345678000199"},
        ocr_confidence=0.93,
    )
    result = PipelineResult(
        risk_score=85.0,
        risk_level="HIGH",
        confidence=0.91,
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

    await _persist_analysis(ctx, result, str(document_id), str(tenant_id), str(user_id))

    documents = (
        (
            await db_session.execute(
                select(DocumentModel).where(DocumentModel.id == document_id)
            )
        )
        .scalars()
        .all()
    )
    assert len(documents) == 1
    document = documents[0]
    assert document.tenant_id == tenant_id
    assert document.uploaded_by == user_id
    assert document.document_type == "boleto"
    assert document.file_name == "boleto.pdf"
    assert document.file_size_bytes == len(ctx.file_bytes)
    assert document.ocr_status == "pending"
    assert document.ocr_confidence == pytest.approx(0.93)
    assert document.extracted_fields == {"cnpj": "12345678000199"}
    assert document.s3_key == ""
    assert document.s3_bucket == ""

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
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.tenant_id == tenant_id
    assert alert.risk_level == "high"
    assert alert.risk_score == pytest.approx(85.0)
    assert alert.status == "new"
