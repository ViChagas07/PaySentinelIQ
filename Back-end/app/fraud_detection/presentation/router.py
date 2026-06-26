# ============================================================
# PaySentinelIQ — Fraud Detection Router
# All endpoints query the database for real user-submitted data.
# No hardcoded/mock/dummy fraud alerts.
# ============================================================

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_tenant_id, require_fraud_analyst
from app.shared.database import get_db
from app.shared.orm_models import FraudAlertModel

router = APIRouter()


class FraudAlertResponse(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    id: str
    document_id: str
    risk_level: str
    risk_score: float
    ai_confidence: float
    anomaly_category: str
    description: str
    ai_explanation: str | None = None
    flagged_fields: list[Any] = []
    status: str
    assigned_to: str | None = None
    created_at: str


class FraudAlertResolveRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    resolution: str  # confirmed_fraud, false_positive, escalated
    notes: str


class DocumentAnalyzeRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    document_id: str = ""  # optional; auto-generated if not provided
    document_type: str | None = None  # boleto, contracheque, holerite
    # Optional fields for direct analysis without OCR
    salario_bruto: float | None = None
    inss: float | None = None
    irrf: float | None = None
    fgts: float | None = None
    liquido: float | None = None
    cargo: str | None = None
    cbo: str | None = None
    cnpj: str | None = None
    razao_social: str | None = None
    cnae: str | None = None
    linha_digitavel: str | None = None
    qr_code_payload: str | None = None
    valor_nominal: float | None = None
    beneficiario: str | None = None


async def _alerts_query(
    tenant_id: uuid.UUID,
    db: AsyncSession,
    risk_level: str | None = None,
    status: str | None = None,
    anomaly_category: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[FraudAlertModel]:
    """Build and execute a filtered fraud alerts query."""
    stmt = select(FraudAlertModel).where(FraudAlertModel.tenant_id == tenant_id)
    if risk_level:
        stmt = stmt.where(FraudAlertModel.risk_level == risk_level)
    if status:
        stmt = stmt.where(FraudAlertModel.status == status)
    if anomaly_category:
        stmt = stmt.where(FraudAlertModel.anomaly_category == anomaly_category)
    stmt = stmt.order_by(FraudAlertModel.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


def _alert_to_dict(alert: FraudAlertModel) -> dict[str, Any]:
    """Convert a FraudAlertModel ORM instance to a dict matching the front-end schema."""
    flagged = []
    if alert.flagged_fields:
        for field in alert.flagged_fields:
            if isinstance(field, dict):
                flagged.append(field)

    return {
        "id": str(alert.id),
        "tenant_id": str(alert.tenant_id),
        "document_id": str(alert.document_id) if alert.document_id else "",
        "document_type": "",
        "risk_level": alert.risk_level,
        "risk_score": alert.risk_score,
        "ai_confidence": alert.ai_confidence,
        "anomaly_category": alert.anomaly_category,
        "description": alert.description,
        "ai_explanation": alert.ai_explanation,
        "flagged_fields": flagged,
        "status": alert.status,
        "assigned_to": str(alert.assigned_to) if alert.assigned_to else None,
        "created_at": alert.created_at.isoformat() if alert.created_at else "",
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
    }


@router.get("")
async def list_fraud_alerts(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    risk_level: str | None = None,
    status: str | None = None,
    anomaly_category: str | None = None,
) -> dict[str, Any]:
    """List fraud alerts with filtering. Returns real data from the database."""
    tid = uuid.UUID(tenant_id)
    skip = (page - 1) * page_size

    alerts = await _alerts_query(tid, db, risk_level, status, anomaly_category, skip, page_size)

    # Count total matching records for pagination
    count_stmt = select(func.count(FraudAlertModel.id)).where(FraudAlertModel.tenant_id == tid)
    if risk_level:
        count_stmt = count_stmt.where(FraudAlertModel.risk_level == risk_level)
    if status:
        count_stmt = count_stmt.where(FraudAlertModel.status == status)
    if anomaly_category:
        count_stmt = count_stmt.where(FraudAlertModel.anomaly_category == anomaly_category)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    total_pages = max(1, (total + page_size - 1) // page_size)

    return {
        "data": [_alert_to_dict(a) for a in alerts],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


@router.post("/analyze")
async def analyze_document(
    body: DocumentAnalyzeRequest,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """
    Submit a document for real-time 7-stage fraud analysis.
    Returns the complete PSI Fraud Analysis Report.
    This endpoint invokes the full deterministic pipeline immediately.
    LLM enhancement via CrewAI agents runs if ENABLE_AI_AGENTS=true.
    """
    from app.fraud_detection.domain.pipeline import get_fraud_pipeline

    pipeline = get_fraud_pipeline()

    document_data = {
        "document_id": body.document_id,
        "document_type": body.document_type or "unknown",
    }

    for field in [
        "salario_bruto",
        "inss",
        "irrf",
        "fgts",
        "liquido",
        "cargo",
        "cbo",
        "cnpj",
        "razao_social",
        "cnae",
        "linha_digitavel",
        "qr_code_payload",
        "valor_nominal",
        "beneficiario",
    ]:
        value = getattr(body, field, None)
        if value is not None:
            document_data[field] = value

    result = pipeline.run_full_pipeline(document_data)
    report = pipeline.generate_psi_report(result, document_data)
    return report


@router.get("/stats")
async def get_fraud_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get fraud alert counts by status from real user data."""
    tid = uuid.UUID(tenant_id)

    stmt = (
        select(FraudAlertModel.status, func.count(FraudAlertModel.id))
        .where(FraudAlertModel.tenant_id == tid)
        .group_by(FraudAlertModel.status)
    )
    result = await db.execute(stmt)
    rows = result.all()

    stats = {
        "total": 0,
        "new": 0,
        "under_review": 0,
        "escalated": 0,
        "confirmed": 0,
        "resolved": 0,
    }
    for status, count in rows:
        if status in stats:
            stats[status] = count
        elif status == "confirmed_fraud":
            stats["confirmed"] = count
        elif status == "false_positive":
            stats["resolved"] += count
    stats["total"] = sum(stats.values())
    return stats


@router.get("/{alert_id}")
async def get_fraud_alert(
    alert_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get a single fraud alert with full details from the database."""
    tid = uuid.UUID(tenant_id)
    stmt = select(FraudAlertModel).where(
        FraudAlertModel.id == alert_id,
        FraudAlertModel.tenant_id == tid,
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Fraud alert '{alert_id}' not found for this tenant.",
        )

    return _alert_to_dict(alert)


@router.patch("/{alert_id}/resolve")
async def resolve_fraud_alert(
    alert_id: str,
    body: FraudAlertResolveRequest,
    payload: dict[str, Any] = Depends(require_fraud_analyst),
    tenant_id: str = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Resolve a fraud alert in the database."""
    tid = uuid.UUID(tenant_id)
    stmt = select(FraudAlertModel).where(
        FraudAlertModel.id == alert_id,
        FraudAlertModel.tenant_id == tid,
    )
    result = await db.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail=f"Fraud alert '{alert_id}' not found for this tenant.",
        )

    alert.status = body.resolution
    alert.resolved_at = datetime.now(UTC)
    await db.flush()

    return {
        "alert_id": alert_id,
        "status": body.resolution,
        "resolution": body.resolution,
        "resolved_at": alert.resolved_at.isoformat(),
    }
