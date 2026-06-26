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

    # ── Shadow mode ──
    settings = get_settings()
    if getattr(settings, "ENABLE_SHADOW_PIPELINE", False):
        try:
            from app.services.pipeline.shadow_runner import ShadowRunner
            # Legacy path: use existing pipeline service for comparison
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

    # ── Build response ──
    response = result.to_dict()
    response["document_id"] = document_id
    response["processing_time_seconds"] = round(elapsed, 2)
    return response


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
