# ============================================================
# PaySentinelIQ — Documents API Router (Fase 3A)
# ============================================================
# Official entry point for document fraud analysis.
# Accepts multipart file upload. Runs CanonicalPipeline.
# Backward-compatible response (legacy + new format).
# Shadow mode support via feature flag.
# ============================================================

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.observability.correlation import (
    CORRELATION_HEADER,
    bind_request_correlation,
    get_correlation,
)
from app.services.ocr.exceptions import OCRFailureError
from app.services.storage.base import StorageProvider
from app.services.upload_validation import (
    UploadPolicy,
    read_upload_limited,
    validate_upload_bytes,
)
from app.shared.domain_primitives import percent_confidence_to_ratio
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}
_SAFE_STORAGE_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}


def _get_storage_provider() -> StorageProvider:
    """Return the configured object-storage provider."""
    from app.services.storage import S3StorageProvider

    return S3StorageProvider()


def _storage_extension(file_name: str, mime_type: str) -> str:
    """Derive a safe extension for the server-generated storage key."""
    normalized_mime = (mime_type or "").split(";", 1)[0].strip().lower()
    if normalized_mime in _MIME_EXTENSIONS:
        return _MIME_EXTENSIONS[normalized_mime]

    suffix = Path(file_name or "").suffix.lower()
    if suffix in _SAFE_STORAGE_EXTENSIONS:
        return suffix
    return ".bin"


@router.post("/analyze")
async def analyze_document(
    request: Request,
    response: Response,
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
            Canonical responses also expose ``persistence_status``: "saved"
            only after the original file is stored and the document/alert
            commit succeeds, otherwise "failed".
    """
    correlation_id = bind_request_correlation(
        request.headers,
        tenant_id=tenant_id,
        user_id=user_id,
    )
    request.state.correlation_id = correlation_id
    settings = get_settings()

    # ── Read bounded bytes and validate before any business side effect ──
    policy = UploadPolicy.from_settings(settings)
    file_data = await read_upload_limited(file, policy.max_file_bytes)
    validated = await asyncio.to_thread(
        validate_upload_bytes,
        file_data,
        declared_content_type=file.content_type,
        file_name=file.filename,
        policy=policy,
    )
    file_data = validated.data
    file_name = validated.safe_filename
    mime_type = validated.content_type

    document_id = str(uuid.uuid4())

    # ── Publish analysis started event (activity history) ──
    from app.messaging.domain.event_types import analysis_event_types
    started_type, completed_type, failed_type = analysis_event_types(document_type)
    await _publish_analysis_event(
        started_type,
        document_id=document_id,
        document_type=document_type,
        file_name=file_name,
        user_id=user_id,
        tenant_id=tenant_id,
        correlation_id=correlation_id,
    )

    # ── Use CanonicalPipeline if feature flag enabled ──
    use_canonical = getattr(settings, "USE_CANONICAL_PIPELINE", False)

    try:
        if use_canonical:
            result = await _run_canonical(
                file_data,
                document_type,
                document_id,
                file_name,
                mime_type,
                tenant_id,
                user_id,
                observations,
                correlation_id=correlation_id,
            )
        else:
            # ── Fallback: legacy pipeline ──
            result = await _run_legacy(file_data, document_type, document_id, file_name, mime_type, tenant_id, observations)

        # ── Publish analysis completed event ──
        await _publish_analysis_event(
            completed_type,
            document_id=document_id,
            document_type=document_type,
            file_name=file_name,
            user_id=user_id,
            tenant_id=tenant_id,
            risk_score=_safe_risk_score(result),
            risk_level=str(result.get("risk_level") or result.get("RISK_ASSESSMENT", {}).get("risk_classification", "")),
            correlation_id=correlation_id,
        )
        if result.get("persistence_status") == "failed":
            response.headers[CORRELATION_HEADER] = correlation_id
        return result
    except OCRFailureError as exc:
        logger.error(
            "Analysis failed: correlation_id=%s document_id=%s tenant_id=%s category=%s",
            exc.correlation_id,
            document_id,
            tenant_id,
            exc.category,
        )
        await _publish_analysis_event(
            failed_type,
            document_id=document_id,
            document_type=document_type,
            file_name="document",
            user_id=user_id,
            tenant_id=tenant_id,
            error=exc.error_code,
            correlation_id=correlation_id,
        )
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "error": exc.error_code,
                "message": exc.public_message,
                "correlation_id": exc.correlation_id,
            },
            headers={"X-Correlation-ID": exc.correlation_id},
        ) from None
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "event=analysis_pipeline_failed correlation_id=%s document_id=%s tenant_id=%s error_type=%s",
            correlation_id,
            document_id,
            tenant_id,
            type(exc).__name__,
        )
        await _publish_analysis_event(
            failed_type,
            document_id=document_id,
            document_type=document_type,
            file_name="document",
            user_id=user_id,
            tenant_id=tenant_id,
            error="analysis_error",
            correlation_id=correlation_id,
        )
        raise HTTPException(
            status_code=500,
            detail={
                "error": "analysis_error",
                "message": "Analysis could not be completed.",
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-ID": correlation_id},
        ) from None


async def _run_canonical(
    file_data: bytes, document_type: str, document_id: str,
    file_name: str, mime_type: str, tenant_id: str, user_id: str, observations: str,
    *, correlation_id: str | None = None,
) -> dict[str, Any]:
    """Run CanonicalPipeline and return backward-compatible response."""
    import asyncio
    import time
    from app.core.contracts.pipeline_context import PipelineContext
    from app.services.pipeline.canonical_pipeline import CanonicalPipeline

    settings = get_settings()
    correlation_id = correlation_id or get_correlation().request_id
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

    if getattr(settings, "ENABLE_OCR", False):
        from app.services.extraction.prelude import run_ocr_prelude

        await run_ocr_prelude(ctx)

    t0 = time.monotonic()
    pipeline = CanonicalPipeline()
    result = await asyncio.to_thread(pipeline.execute, ctx)
    elapsed = time.monotonic() - t0

    from app.core.contracts.pipeline_status import PipelineStatus

    if result.pipeline_status == PipelineStatus.FAILED:
        category = ctx.metadata.get("ocr", {}).get("status", "error")
        raise OCRFailureError(category, ctx.correlation_id)

    # ── Persist document + fraud alert (if HIGH risk) ──
    persisted = await _persist_analysis(
        ctx,
        result,
        document_id,
        tenant_id,
        user_id,
        correlation_id=correlation_id or get_correlation().request_id,
    )

    # ── Send notification ──
    await _send_analysis_notification(
        ctx,
        result,
        document_id,
        tenant_id,
        user_id,
        correlation_id=correlation_id,
    )

    # ── Shadow mode ──
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
            logger.info(
                "event=shadow_comparison correlation_id=%s document_id=%s "
                "legacy_score=%.1f canonical_score=%.1f score_delta=%.1f "
                "level_match=%s score_match=%s",
                correlation_id,
                document_id[:8],
                comparison.legacy_score,
                comparison.canonical_score,
                comparison.score_delta,
                comparison.level_match,
                comparison.score_match,
            )
        except Exception as exc:
            logger.warning(
                "event=shadow_pipeline_failed correlation_id=%s document_id=%s "
                "error_type=%s",
                correlation_id,
                document_id[:8],
                type(exc).__name__,
            )

    # ── Build response with extracted metadata ──
    response = result.to_dict()
    response["document_id"] = document_id
    response["processing_time_seconds"] = round(elapsed, 2)
    response["persistence_status"] = "saved" if persisted else "failed"
    response["extracted_metadata"] = _build_extracted_metadata(ctx)

    extraction_metadata = ctx.metadata.get("extraction", {})
    ocr_metadata = ctx.metadata.get("ocr", {})
    response["extraction"] = {
        "language": extraction_metadata.get("language"),
        "method": ctx.extraction_method or extraction_metadata.get("method"),
        "ocr_confidence": ctx.ocr_confidence,
        "page_count": ctx.page_count,
        "ocr_status": ocr_metadata.get("status"),
        "ocr_seconds": ocr_metadata.get("duration_s"),
        "warnings": extraction_metadata.get("warnings", []),
        "corrections": extraction_metadata.get("corrections", []),
        "fields": extraction_metadata.get("fields", {}),
    }
    response["metadata"] = {
        "validation": ctx.metadata.get("validation", {}),
    }
    return response


async def _compensate_upload(
    storage: StorageProvider,
    key: str,
    *,
    correlation_id: str = "",
) -> None:
    """Remove only the object created by the failed analysis operation."""
    try:
        deleted = await storage.delete_file(key)
    except Exception as exc:
        logger.warning(
            "Orphan storage object remains after failed persistence: "
            "event=storage_compensation_failed correlation_id=%s error_type=%s",
            correlation_id,
            type(exc).__name__,
        )
        return
    if deleted:
        logger.info(
            "Compensated orphan storage object: event=storage_compensated correlation_id=%s",
            correlation_id,
        )
    else:
        logger.warning(
            "Orphan storage object remains after failed persistence: "
            "event=storage_compensation_orphan correlation_id=%s",
            correlation_id,
        )


async def _persist_analysis(
    ctx: PipelineContext,
    result: PipelineResult,
    document_id: str,
    tenant_id: str,
    user_id: str,
    *,
    correlation_id: str | None = None,
) -> bool:
    """Persist original file, document record and fraud alert.

    Flow:
        1. Compute SHA-256 over the exact original bytes.
        2. Upload those bytes under a server-generated key.
        3. Commit document + alert in one transaction.
        4. On DB failure, roll back and delete only the object just uploaded.

    ``PipelineResult.confidence`` is produced on the 0-100 scale, while
    ``fraud_alerts.ai_confidence`` is constrained to 0-1. The conversion is
    explicit at this persistence boundary and rejects out-of-range values.

    Returns ``True`` only when the original object is stored and the DB commit
    succeeds. Failures are logged and returned as ``False``; callers expose
    them as ``persistence_status="failed"`` without claiming a successful save.
    """
    import uuid as _uuid
    from app.services.storage import S3StorageProvider

    correlation_id = correlation_id or get_correlation().request_id
    file_bytes = ctx.file_bytes
    if not file_bytes:
        logger.error(
            "Cannot persist analysis without file bytes: "
            "event=document_persistence_skipped correlation_id=%s "
            "document_id=%s tenant_id=%s reason=missing_file_bytes",
            correlation_id,
            document_id,
            tenant_id,
        )
        return False

    file_hash = hashlib.sha256(file_bytes).hexdigest()
    extension = _storage_extension(ctx.filename or "", ctx.mime_type or "")
    requested_key = S3StorageProvider.build_key(
        S3StorageProvider.get_folder_for_type(ctx.document_type),
        tenant_id,
        document_id,
        extension,
    )

    try:
        storage = _get_storage_provider()
        upload_result = await storage.upload_file(
            file_bytes,
            requested_key,
            ctx.mime_type or "application/octet-stream",
            metadata={
                "sha256": file_hash,
                "tenant_id": tenant_id,
                "document_id": document_id,
            },
        )
    except Exception as exc:
        logger.error(
            "Failed to upload original document (non-fatal): "
            "event=document_storage_upload_failed correlation_id=%s "
            "document_id=%s tenant_id=%s error_type=%s",
            correlation_id,
            document_id,
            tenant_id,
            type(exc).__name__,
        )
        return False

    if (
        not upload_result.success
        or not upload_result.key
        or not upload_result.bucket
    ):
        logger.error(
            "Storage returned an incomplete upload result (non-fatal): "
            "event=document_storage_upload_incomplete correlation_id=%s "
            "document_id=%s tenant_id=%s",
            correlation_id,
            document_id,
            tenant_id,
        )
        return False

    uploaded_key = upload_result.key
    uploaded_bucket = upload_result.bucket

    committed = False
    try:
        from app.shared.database import get_engine
        engine = get_engine()
        if engine is None:
            raise RuntimeError("database engine unavailable")
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.shared.orm_models import DocumentModel, FraudAlertModel

        async with AsyncSession(engine, expire_on_commit=False) as db:
            try:
                doc = DocumentModel(
                    id=_uuid.UUID(document_id),
                    tenant_id=_uuid.UUID(tenant_id),
                    uploaded_by=_uuid.UUID(user_id),
                    document_type=ctx.document_type,
                    file_name=ctx.filename or "document.pdf",
                    file_size_bytes=len(file_bytes),
                    s3_key=uploaded_key,
                    s3_bucket=uploaded_bucket,
                    file_hash=file_hash,
                    ocr_confidence=ctx.ocr_confidence,
                    extracted_fields=ctx.extracted_fields or None,
                )
                db.add(doc)
                await db.flush()

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
                        ai_confidence=percent_confidence_to_ratio(result.confidence),
                        anomaly_category="document_fraud",
                        description=f"Documento {ctx.document_type} classificado como {result.risk_level} (score: {result.risk_score:.0f}/100)",
                        ai_explanation=result.reasoning_summary or "Analise deterministica detectou multiplas evidencias de fraude",
                        flagged_fields=flagged,
                        status="new",
                    )
                    db.add(alert)
                    logger.info("Fraud alert created: doc=%s score=%.0f level=%s", document_id[:8], result.risk_score, result.risk_level)

                await db.commit()
                committed = True
            except Exception:
                await db.rollback()
                raise
    except Exception as exc:
        if committed:
            logger.error(
                "Persistence committed but session cleanup failed: "
                "event=persistence_cleanup_failed correlation_id=%s "
                "document_id=%s tenant_id=%s error_type=%s",
                correlation_id,
                document_id,
                tenant_id,
                type(exc).__name__,
            )
            return True
        logger.error(
            "Failed to persist document/fraud alert (non-fatal): "
            "event=document_persistence_failed correlation_id=%s "
            "document_id=%s tenant_id=%s error_type=%s",
            correlation_id,
            document_id,
            tenant_id,
            type(exc).__name__,
        )
        await _compensate_upload(
            storage,
            uploaded_key,
            correlation_id=correlation_id,
        )
        return False
    return True


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


def _safe_risk_score(result: dict[str, Any]) -> float | None:
    """Extract a numeric risk score from legacy or canonical responses."""
    try:
        score = result.get("risk_score")
        if isinstance(score, (int, float)):
            return float(score)
        nested = result.get("RISK_ASSESSMENT", {}).get("fraud_risk_score")
        if isinstance(nested, (int, float)):
            return float(nested)
    except Exception:
        return None
    return None


async def _publish_analysis_event(
    event_type: str,
    *,
    document_id: str,
    document_type: str,
    file_name: str,
    user_id: str,
    tenant_id: str,
    risk_score: float | None = None,
    risk_level: str | None = None,
    error: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Publish an analysis lifecycle event (non-fatal — never blocks the API)."""
    correlation_id = correlation_id or get_correlation().request_id
    try:
        from app.messaging.domain.envelope import new_event
        from app.messaging.infrastructure.factory import get_event_publisher

        payload: dict[str, Any] = {
            "document_id": document_id,
            "document_type": document_type or "unknown",
            "file_name": file_name,
        }
        if risk_score is not None:
            payload["risk_score"] = risk_score
        if risk_level:
            payload["risk_level"] = risk_level
        if error:
            payload["error"] = error

        event = new_event(
            event_type,
            payload=payload,
            user_id=user_id,
            tenant_id=tenant_id,
        )
        ok = await get_event_publisher().publish(event)
        if not ok:
            logger.warning(
                "event=analysis_event_not_published correlation_id=%s "
                "event_type=%s document_id=%s",
                correlation_id,
                event_type,
                document_id[:8],
            )
    except Exception as exc:  # pragma: no cover - events must never fail analysis
        logger.warning(
            "event=analysis_event_publish_failed correlation_id=%s "
            "event_type=%s document_id=%s error_type=%s",
            correlation_id,
            event_type,
            document_id[:8],
            type(exc).__name__,
        )


async def _send_analysis_notification(
    ctx,
    result,
    document_id: str,
    tenant_id: str,
    user_id: str,
    *,
    correlation_id: str | None = None,
) -> None:
    """Push real-time WS notification + persist to DB when analysis completes."""
    import uuid as _uuid
    correlation_id = correlation_id or get_correlation().request_id
    try:
        level = result.risk_level
        score = result.risk_score
        doc_type = ctx.document_type or "documento"

        if level == "HIGH":
            title = f"ALERTA: Documento fraudulento detectado ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — {len(result.evidence)} evidencias. REJEITAR."
            severity = "critical"
            ntype = "fraud_alert"
        elif level == "MEDIUM":
            title = f"Analise concluida: {level} ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — Anomalias detectadas. Revisar."
            severity = "warning"
            ntype = "compliance_alert"
        else:
            title = f"Analise concluida: {level} ({score:.0f}/100)"
            msg = f"'{ctx.filename}' — Nenhum indicador critico."
            severity = "success"
            ntype = "verification_complete"

        notification_data = {
            "id": document_id,
            "tenant_id": tenant_id,
            "type": ntype,
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
        }

        # ── Persist to database ──
        try:
            from app.shared.database import get_engine
            engine = get_engine()
            if engine:
                from sqlalchemy.ext.asyncio import AsyncSession
                from app.shared.orm_models import NotificationModel
                async with AsyncSession(engine, expire_on_commit=False) as db:
                    notif = NotificationModel(
                        user_id=_uuid.UUID(user_id),
                        tenant_id=_uuid.UUID(tenant_id),
                        type=ntype,
                        title=title,
                        message=msg,
                        severity=severity,
                        action_url=f"/verification-center?document={document_id}",
                        metadata_=notification_data.get("metadata", {}),
                    )
                    db.add(notif)
                    await db.commit()
                    logger.info(
                        "event=notification_persisted correlation_id=%s document_id=%s",
                        correlation_id,
                        document_id[:8],
                    )
        except Exception as exc:
            logger.warning(
                "event=notification_persist_failed correlation_id=%s "
                "document_id=%s error_type=%s",
                correlation_id,
                document_id[:8],
                type(exc).__name__,
            )

        # ── Push via WebSocket ──
        try:
            from app.websocket.router import publish_ws_notification
            await publish_ws_notification(notification_data)
            logger.info(
                "event=ws_notification_sent correlation_id=%s document_id=%s level=%s",
                correlation_id,
                document_id[:8],
                level,
            )
        except Exception as exc:
            logger.warning(
                "event=ws_notification_failed correlation_id=%s document_id=%s "
                "error_type=%s",
                correlation_id,
                document_id[:8],
                type(exc).__name__,
            )
    except Exception as exc:
        logger.warning(
            "event=notification_dispatch_failed correlation_id=%s document_id=%s "
            "error_type=%s",
            correlation_id,
            document_id[:8],
            type(exc).__name__,
        )


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
