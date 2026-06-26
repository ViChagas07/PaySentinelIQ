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
    # CRITICAL: Raw OCR text enables deep boleto analysis (Stage 4B)
    ocr_text: str | None = None
    raw_text: str | None = None


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
    Submit a document for real-time fraud analysis.

    Fase 5: Migrated to CanonicalPipeline when USE_CANONICAL_PIPELINE=true.
    Falls back to legacy FraudDetectionPipeline when flag is disabled.
    """
    import logging
    logger = logging.getLogger(__name__)

    from app.shared.settings import get_settings
    settings = get_settings()

    # ── Fase 5: CanonicalPipeline migration ──
    # Runs even without ocr_text — ValidateStage uses structured fields for detection
    if getattr(settings, "USE_CANONICAL_PIPELINE", False):
        return await _run_canonical_from_analyze(body, tenant_id)

    from app.fraud_detection.domain.pipeline import get_fraud_pipeline

    pipeline = get_fraud_pipeline()

    document_data = {
        "document_id": body.document_id,
        "document_type": body.document_type or "unknown",
    }

    for field in [
        "salario_bruto", "inss", "irrf", "fgts", "liquido",
        "cargo", "cbo", "cnpj", "razao_social", "cnae",
        "linha_digitavel", "qr_code_payload", "valor_nominal",
        "beneficiario",
    ]:
        value = getattr(body, field, None)
        if value is not None:
            document_data[field] = value

    # Pass raw text to enable Stage 4B boleto deep analysis
    raw_text = body.ocr_text or body.raw_text or ""
    if raw_text:
        document_data["ocr_text"] = raw_text
        document_data["raw_text"] = raw_text

    # ── Run 7-stage deterministic pipeline ──
    result = pipeline.run_full_pipeline(document_data)

    # ── Boleto: also run the 4-stage boleto pipeline on raw text ──
    boleto_score = 0.0
    is_boleto = (
        body.document_type == "boleto"
        or bool(body.linha_digitavel)
        or (raw_text and any(
            term in raw_text.lower()
            for term in ["boleto", "linha digitável", "código de barras",
                         "vencimento", "cedente", "sacado"]
        ))
    )
    if is_boleto and raw_text and len(raw_text) > 50:
        try:
            from app.services.ai.boleto_analyzer import analyze_boleto_pipeline
            boleto_analysis = await analyze_boleto_pipeline(raw_text, llm_generate_fn=None)
            boleto_score = boleto_analysis["risk_score"]
            logger.info(
                "Boleto pipeline via API: score=%d level=%s indicators=%d",
                boleto_score,
                boleto_analysis["risk_level"],
                boleto_analysis["total_indicators"],
            )
        except Exception as e:
            logger.warning("Boleto pipeline via API failed: %s", e)

    # ── Generate report ──
    report = pipeline.generate_psi_report(result, document_data)

    # ── Enforce boleto score as FLOOR ──
    if boleto_score > 0:
        current_score = report.get("RISK_ASSESSMENT", {}).get("fraud_risk_score", 0)
        final_score = max(current_score, boleto_score)
        if final_score > current_score:
            report["RISK_ASSESSMENT"]["fraud_risk_score"] = final_score
            if final_score >= 70:
                report["RISK_ASSESSMENT"]["risk_classification"] = "HIGH"
                report["RISK_ASSESSMENT"]["recommended_action"] = "REJECT"
            elif final_score >= 40:
                report["RISK_ASSESSMENT"]["risk_classification"] = "MEDIUM"
                report["RISK_ASSESSMENT"]["recommended_action"] = "MANUAL_REVIEW"
            logger.info(
                "Boleto score override: pipeline=%.0f boleto=%.0f final=%.0f",
                current_score, boleto_score, final_score,
            )

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


# ═══════════════════════════════════════════════════════
# Fase 5: CanonicalPipeline migration helper
# ═══════════════════════════════════════════════════════

async def _run_canonical_from_analyze(
    body: DocumentAnalyzeRequest,
    tenant_id: str,
) -> dict[str, Any]:
    """Run CanonicalPipeline for the /analyze endpoint."""
    import re as _re
    import time
    from app.core.contracts.pipeline_context import PipelineContext
    from app.services.pipeline.canonical_pipeline import CanonicalPipeline

    raw_text = body.ocr_text or body.raw_text or ""

    ctx = PipelineContext(
        document_id=body.document_id,
        tenant_id=tenant_id,
        document_type=body.document_type or "unknown",
        extracted_text=raw_text,
    )

    # Populate extracted fields from request body
    for field in ["cnpj", "razao_social", "cnae", "linha_digitavel",
                   "valor_nominal", "beneficiario"]:
        value = getattr(body, field, None)
        if value is not None:
            ctx.extracted_fields[field] = value

    # ── Smart CNPJ extraction: if cnpj is not directly provided,
    #     try to extract from razao_social (frontend may map CNPJ there) ──
    if not ctx.extracted_fields.get("cnpj"):
        razao = ctx.extracted_fields.get("razao_social", "")
        cnpj_match = _re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14}", razao)
        if cnpj_match:
            ctx.extracted_fields["cnpj"] = cnpj_match.group()
    # Also check raw_text for CNPJ patterns
    if not ctx.extracted_fields.get("cnpj") and raw_text:
        cnpj_match = _re.search(r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}|\d{14}", raw_text)
        if cnpj_match:
            ctx.extracted_fields["cnpj"] = cnpj_match.group()

    # ── Smart linha_digitavel extraction ──
    if not ctx.extracted_fields.get("linha_digitavel") and raw_text:
        linha_match = _re.search(
            r"(\d{5}\.\d{5}\s\d{6}\.\d{6}\s\d{6}\.\d{6}\s\d\s\d{14})", raw_text
        )
        if linha_match:
            ctx.extracted_fields["linha_digitavel"] = linha_match.group()

    # ── Smart value extraction ──
    if not ctx.extracted_fields.get("valor_nominal") and raw_text:
        amt_match = _re.search(r"(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})", raw_text)
        if amt_match:
            try:
                clean = amt_match.group(1).replace(".", "").replace(",", ".")
                ctx.extracted_fields["valor_nominal"] = float(clean)
            except ValueError:
                pass

    t0 = time.monotonic()
    pipeline = CanonicalPipeline()
    result = pipeline.execute(ctx)
    elapsed = time.monotonic() - t0

    response = result.to_dict()
    response["processing_time_seconds"] = round(elapsed, 2)
    return response
