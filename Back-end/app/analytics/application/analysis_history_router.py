# ============================================================
# PaySentinelIQ — Analysis History Router
# Persist + query AI-powered document analysis results.
# Feeds the Dashboard KPIs, Reports page, and History table
# with real, tenant-scoped data — never ephemeral.
# ============================================================

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.shared.database import get_db
from app.shared.orm_models import AnalysisRecordModel

router = APIRouter()

# ── Pydantic Schemas ──────────────────────────────────────


class AnalysisSaveRequest(BaseModel):
    document_type: str                      # "BOLETO" | "CONTRACHEQUE"
    file_name: str
    file_size: int | None = None
    risk_level: str = "LOW"                 # "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
    risk_score: float = 0.0
    confidence_score: float | None = None
    fraud_probability: float | None = None
    is_fraudulent: bool = False
    fraud_indicators: list[str] | None = None
    analysis_result: dict[str, Any] | None = None
    amount: float | None = None
    ai_summary: str | None = None
    processing_duration: float | None = None
    status: str = "completed"               # "completed" | "flagged" | "failed"


class AnalysisRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID
    tenant_id: UUID
    document_type: str
    file_name: str
    file_size: int | None = None
    risk_level: str
    risk_score: float
    confidence_score: float | None = None
    fraud_probability: float | None = None
    is_fraudulent: bool
    fraud_indicators: list[str] | None = None
    analysis_result: dict[str, Any] | None = None
    amount: float | None = None
    ai_summary: str | None = None
    processing_duration: float | None = None
    analyzed_at: datetime
    status: str
    created_at: datetime


class AnalysisDashboardStats(BaseModel):
    total_documents: int
    fraudulent_count: int
    fraud_rate: float                # percent 0-100
    avg_confidence_score: float
    avg_risk_score: float
    losses_prevented: float          # sum of amounts where is_fraudulent=True
    high_risk_count: int             # risk_level="HIGH" or "CRITICAL"
    pass_rate: float                 # percent of non-fraudulent documents
    recent_analyses: list[AnalysisRecordResponse]


# ── Helper ────────────────────────────────────────────────


def _map_risk_level(risk_score: float) -> str:
    """Fase 3B: Unified thresholds (40/70)."""
    if risk_score >= 70:
        return "HIGH"
    if risk_score >= 40:
        return "MEDIUM"
    return "LOW"


# ── POST /analysis/save ───────────────────────────────────


@router.post("/analysis/save", response_model=AnalysisRecordResponse)
async def save_analysis(
    payload: AnalysisSaveRequest,
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> AnalysisRecordModel:
    """Persist a completed document analysis to the database."""
    tid = UUID(tenant_id)
    uid = UUID(current_user_id)

    record = AnalysisRecordModel(
        user_id=uid,
        tenant_id=tid,
        document_type=payload.document_type,
        file_name=payload.file_name,
        file_size=payload.file_size,
        risk_level=payload.risk_level or _map_risk_level(payload.risk_score),
        risk_score=payload.risk_score,
        confidence_score=payload.confidence_score,
        fraud_probability=payload.fraud_probability,
        is_fraudulent=payload.is_fraudulent,
        fraud_indicators=payload.fraud_indicators,
        analysis_result=payload.analysis_result,
        amount=payload.amount,
        ai_summary=payload.ai_summary,
        processing_duration=payload.processing_duration,
        status=payload.status,
        analyzed_at=datetime.utcnow(),
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


# ── GET /analysis/history ─────────────────────────────────


@router.get("/analysis/history", response_model=list[AnalysisRecordResponse])
async def get_analysis_history(
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    document_type: str | None = Query(None),
    risk_level: str | None = Query(None),
) -> list[AnalysisRecordModel]:
    """List analysis records for the authenticated user, with optional filters."""
    tid = UUID(tenant_id)
    uid = UUID(current_user_id)

    stmt = (
        select(AnalysisRecordModel)
        .where(
            AnalysisRecordModel.tenant_id == tid,
            AnalysisRecordModel.user_id == uid,
        )
    )
    if document_type:
        stmt = stmt.where(AnalysisRecordModel.document_type == document_type)
    if risk_level:
        stmt = stmt.where(AnalysisRecordModel.risk_level == risk_level)

    stmt = stmt.order_by(desc(AnalysisRecordModel.analyzed_at))
    stmt = stmt.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(stmt)
    return list(result.scalars().all())


# ── GET /analysis/stats ───────────────────────────────────


@router.get("/analysis/stats", response_model=AnalysisDashboardStats)
async def get_analysis_stats(
    tenant_id: str = Depends(get_current_tenant_id),
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Aggregated analysis statistics for dashboard KPIs."""
    tid = UUID(tenant_id)
    uid = UUID(current_user_id)

    base_filter = (
        AnalysisRecordModel.tenant_id == tid,
        AnalysisRecordModel.user_id == uid,
    )

    # Total documents analyzed
    total_result = await db.execute(
        select(func.count(AnalysisRecordModel.id)).where(*base_filter)
    )
    total_documents = total_result.scalar_one()

    # Fraudulent count
    fraudulent_result = await db.execute(
        select(func.count(AnalysisRecordModel.id))
        .where(*base_filter)
        .where(AnalysisRecordModel.is_fraudulent.is_(True))
    )
    fraudulent_count = fraudulent_result.scalar_one()

    # High-risk count
    high_risk_result = await db.execute(
        select(func.count(AnalysisRecordModel.id))
        .where(*base_filter)
        .where(AnalysisRecordModel.risk_level.in_(["HIGH", "CRITICAL"]))
    )
    high_risk_count = high_risk_result.scalar_one()

    # Average confidence score
    avg_conf_result = await db.execute(
        select(func.avg(AnalysisRecordModel.confidence_score))
        .where(*base_filter)
        .where(AnalysisRecordModel.confidence_score.isnot(None))
    )
    avg_confidence_score = avg_conf_result.scalar_one() or 0.0

    # Average risk score
    avg_risk_result = await db.execute(
        select(func.avg(AnalysisRecordModel.risk_score))
        .where(*base_filter)
    )
    avg_risk_score = avg_risk_result.scalar_one() or 0.0

    # Losses prevented (sum of amounts on fraudulent docs)
    losses_result = await db.execute(
        select(func.sum(AnalysisRecordModel.amount))
        .where(*base_filter)
        .where(
            AnalysisRecordModel.is_fraudulent.is_(True),
            AnalysisRecordModel.amount.isnot(None),
        )
    )
    losses_prevented = losses_result.scalar_one() or 0.0

    # Fraud rate
    fraud_rate = round((fraudulent_count / total_documents * 100), 2) if total_documents > 0 else 0.0

    # Pass rate
    pass_rate = round(((total_documents - fraudulent_count) / total_documents * 100), 2) if total_documents > 0 else 0.0

    # Recent analyses (last 5)
    recent_result = await db.execute(
        select(AnalysisRecordModel)
        .where(*base_filter)
        .order_by(desc(AnalysisRecordModel.analyzed_at))
        .limit(5)
    )
    recent_analyses = list(recent_result.scalars().all())

    return {
        "total_documents": total_documents,
        "fraudulent_count": fraudulent_count,
        "fraud_rate": fraud_rate,
        "avg_confidence_score": round(float(avg_confidence_score), 4),
        "avg_risk_score": round(float(avg_risk_score), 2),
        "losses_prevented": round(float(losses_prevented), 2),
        "high_risk_count": high_risk_count,
        "pass_rate": pass_rate,
        "recent_analyses": recent_analyses,
    }
