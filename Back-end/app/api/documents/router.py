# ============================================================
# PaySentinelIQ — Documents API Router (Fase 3A)
# ============================================================
# Official entry point for document fraud analysis.
# Accepts multipart file upload. Runs CanonicalPipeline.
# Backward-compatible response (legacy + new format).
# Shadow mode support via feature flag.
# ============================================================

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze")
async def analyze_document(
    file: UploadFile = File(...),
    document_type: str = Form("unknown"),
    observations: str = Form(""),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Analyze a document for fraud using the CanonicalPipeline.

    This is the OFFICIAL entry point. All new integrations should use this endpoint.

    Input: multipart/form-data
      - file: PDF, PNG, or JPEG document
      - document_type: "boleto", "contracheque", "holerite"
      - observations: Optional user notes

    Output: Backward-compatible response with both legacy (RISK_ASSESSMENT)
            and new (risk_score, evidence, explainability) formats.
    """
    settings = get_settings()

    # ── Read file ──
    file_data = await file.read()
    file_name = file.filename or "document.pdf"
    mime_type = file.content_type or "application/octet-stream"

    # ── Validate size ──
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1_048_576
    if len(file_data) > max_size:
        raise HTTPException(status_code=400, detail=f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")

    document_id = str(uuid.uuid4())

    # ── Use CanonicalPipeline if feature flag enabled ──
    use_canonical = getattr(settings, "USE_CANONICAL_PIPELINE", False)

    if use_canonical:
        return await _run_canonical(file_data, document_type, document_id, file_name, mime_type, tenant_id, observations)

    # ── Fallback: legacy pipeline ──
    return await _run_legacy(file_data, document_type, document_id, file_name, mime_type, tenant_id, observations)


async def _run_canonical(
    file_data: bytes, document_type: str, document_id: str,
    file_name: str, mime_type: str, tenant_id: str, observations: str,
) -> dict[str, Any]:
    """Run CanonicalPipeline and return backward-compatible response."""
    import time
    from app.core.contracts.pipeline_context import PipelineContext
    from app.services.pipeline.canonical_pipeline import CanonicalPipeline

    ctx = PipelineContext(
        document_id=document_id,
        tenant_id=tenant_id,
        file_bytes=file_data,
        filename=file_name,
        mime_type=mime_type,
        document_type=document_type,
    )
    if observations:
        ctx.metadata["observations"] = observations

    t0 = time.monotonic()
    pipeline = CanonicalPipeline()
    result = pipeline.execute(ctx)
    elapsed = time.monotonic() - t0

    # ── Persist document + fraud alert (if HIGH risk) ──
    await _persist_analysis(ctx, result, document_id, tenant_id)

    # ── Send notification ──
    await _send_analysis_notification(ctx, result, document_id, tenant_id)

    # ── Shadow mode ──
    settings = get_settings()
    if getattr(settings, "ENABLE_SHADOW_PIPELINE", False):
        try:
            from app.services.pipeline.shadow_runner import ShadowRunner
            legacy_result = await _run_legacy_internal(
                file_data, document_type, document_id, file_name, mime_type, tenant_id, observations
            )
            runner = ShadowRunner()
            comparison = await runner.run_shadow(
                file_data=file_data, document_type=document_type,
                tenant_id=tenant_id, legacy_result=legacy_result,
                file_name=file_name, mime_type=mime_type,
            )
            logger.info("SHADOW comparison: %s", comparison.to_dict())
        except Exception as e:
            logger.warning("Shadow mode failed: %s", e)

    # ── Build response with extracted metadata ──
    response = result.to_dict()
    response["document_id"] = document_id
    response["processing_time_seconds"] = round(elapsed, 2)
    response["extracted_metadata"] = _build_extracted_metadata(ctx)
    return response


async def _persist_analysis(
    ctx, result, document_id: str, tenant_id: str,
) -> None:
    """Persist document record and fraud alert to database."""
    import uuid as _uuid
    from app.shared.database import get_engine
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.shared.orm_models import DocumentModel, FraudAlertModel

    try:
        engine = get_engine()
        async with AsyncSession(engine) as db:
            # Create document record
            doc = DocumentModel(
                id=_uuid.UUID(document_id),
                tenant_id=_uuid.UUID(tenant_id),
                filename=ctx.filename or "document.pdf",
                file_type=ctx.mime_type or "application/pdf",
                file_size=len(ctx.file_bytes),
                document_type=ctx.document_type,
            )
            db.add(doc)
            await db.flush()

            # If HIGH risk, create fraud alert with extracted metadata
            if result.risk_score >= 70:
                flagged = []
                for e in result.evidence:
                    flagged.append({
                        "field_name": e.code,
                        "detected_value": e.description[:200],
                        "confidence": e.confidence * 100,
                        "explanation": f"[{e.severity.value.upper()}] {e.source.value}: {e.description[:300]}",
                    })
                fields = ctx.extracted_fields
                if fields.get("data_vencimento") or fields.get("dates"):
                    flagged.append({
                        "field_name": "data_vencimento",
                        "detected_value": str(fields.get("data_vencimento") or (fields.get("dates", [None])[0] if fields.get("dates") else "N/A")),
                        "confidence": 90,
                        "explanation": "Data de vencimento extraida do documento",
                    })
                if fields.get("beneficiario"):
                    flagged.append({
                        "field_name": "beneficiario",
                        "detected_value": str(fields.get("beneficiario")),
                        "confidence": 85,
                        "explanation": "Nome do beneficiario/emissor extraido do documento",
                    })
                if fields.get("cnpj"):
                    flagged.append({
                        "field_name": "cnpj",
                        "detected_value": str(fields.get("cnpj")),
                        "confidence": 90,
                        "explanation": "CNPJ do emissor extraido do documento",
                    })
                if fields.get("valor_nominal") or fields.get("amounts"):
                    flagged.append({
                        "field_name": "valor",
                        "detected_value": str(fields.get("valor_nominal") or (fields.get("amounts", [0])[0] if fields.get("amounts") else "N/A")),
                        "confidence": 95,
                        "explanation": "Valor do documento extraido",
                    })
                if fields.get("codigo_banco") or ctx.extracted_text:
                    flagged.append({
                        "field_name": "banco_emissor",
                        "detected_value": str(fields.get("codigo_banco") or "N/A"),
                        "confidence": 85,
                        "explanation": "Codigo do banco emissor extraido do documento",
                    })

                alert = FraudAlertModel(
                    tenant_id=_uuid.UUID(tenant_id),
                    document_id=_uuid.UUID(document_id),
                    risk_level=result.risk_level.lower(),
                    risk_score=result.risk_score,
                    ai_confidence=result.confidence,
                    anomaly_category="document_fraud",
                    description=f"Documento {ctx.document_type} classificado como {result.risk_level} (score: {result.risk_score:.0f}/100)",
                    ai_explanation=result.reasoning_summary or "Analise deterministica detectou multiplas evidencias de fraude",
                    flagged_fields=flagged,
                    status="new",
                )
                db.add(alert)
                logger.info("Fraud alert created: doc=%s score=%.0f level=%s", document_id[:8], result.risk_score, result.risk_level)

            await db.commit()
    except Exception as e:
        logger.warning("Failed to persist fraud alert (non-fatal): %s", e)


def _build_extracted_metadata(ctx) -> dict:
    """Build extracted metadata for the frontend."""
    fields = ctx.extracted_fields
    return {
        "due_date": str(fields.get("data_vencimento") or (fields.get("dates", [None])[0] if fields.get("dates") else None) or ""),
        "issuer": str(fields.get("beneficiario") or fields.get("razao_social") or ""),
        "cnpj": str(fields.get("cnpj") or ""),
        "amount": str(fields.get("valor_nominal") or (fields.get("amounts", [None])[0] if fields.get("amounts") else "") or ""),
        "bank_code": str(fields.get("codigo_banco") or ""),
        "linha_digitavel": str(fields.get("linha_digitavel") or ""),
        "document_type": ctx.document_type,
        "file_name": ctx.filename,
    }


async def _send_analysis_notification(
    ctx, result, document_id: str, tenant_id: str,
) -> None:
    """Push real-time notification via WebSocket when analysis completes."""
    try:
        level = result.risk_level
        score = result.risk_score
        doc_type = ctx.document_type or "documento"

        if level == "HIGH":
            title = f"ALERTA: Documento fraudulento detectado ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — {len(result.evidence)} evidencias. REJEITAR."
            severity = "critical"
        elif level == "MEDIUM":
            title = f"Analise concluida: {level} ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — Anomalias detectadas. Revisar."
            severity = "warning"
        else:
            title = f"Analise concluida: {level} ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — Nenhum indicador critico."
            severity = "normal"

        try:
            from app.websocket.router import publish_ws_notification
            await publish_ws_notification({
                "id": document_id,
                "tenant_id": tenant_id,
                "type": "analysis_complete",
                "title": title,
                "message": msg,
                "severity": severity,
                "action_url": f"/verification-center?document={document_id}",
                "metadata": {
                    "document_type": doc_type,
                    "risk_score": score,
                    "risk_level": level,
                    "evidence_count": len(result.evidence),
                    "file_name": ctx.filename,
                },
            })
            logger.info("Notification sent: doc=%s level=%s", document_id[:8], level)
        except Exception as e:
            logger.warning("WS notification failed (non-fatal): %s", e)
    except Exception as e:
        logger.warning("Notification dispatch failed: %s", e)


async def _run_legacy(
    file_data: bytes, document_type: str, document_id: str,
    file_name: str, mime_type: str, tenant_id: str, observations: str,
) -> dict[str, Any]:
    """Run legacy pipeline (backward compat)."""
    return await _run_legacy_internal(file_data, document_type, document_id, file_name, mime_type, tenant_id, observations)


async def _run_legacy_internal(
    file_data: bytes, document_type: str, document_id: str,
    file_name: str, mime_type: str, tenant_id: str, observations: str,
) -> dict[str, Any]:
    """Internal legacy pipeline execution."""
    from app.services.pipeline_service import get_pipeline_service

    pipeline = get_pipeline_service()
    return await pipeline.process_document(
        file_data=file_data,
        file_name=file_name,
        content_type=mime_type,
        tenant_id=tenant_id,
        extra_context={"document_type": document_type, "observations": observations},
    )
