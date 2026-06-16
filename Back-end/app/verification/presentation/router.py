# ============================================================
# PaySentinelIQ — Verification Router
# Real S3 upload + OCR + AI pipeline endpoint.
# ============================================================

from __future__ import annotations

import uuid
import logging
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import get_current_tenant_id, get_current_user_id, require_fraud_analyst
from app.services.storage import FileValidator, InvalidFileTypeError, FileTooLargeError
from app.services.pipeline_service import get_pipeline_service
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Models ──

class UploadResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    document_id: str
    status: str
    message: str
    s3_key: str | None = None
    presigned_url: str | None = None


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    document_id: str
    pipeline_status: str  # processing, completed, failed
    risk_score: float | None = None
    risk_level: str | None = None
    processing_time_seconds: float | None = None
    stages: dict[str, Any] = {}
    error: str | None = None


# ── Validator ──
_validator = FileValidator(max_size_bytes=10 * 1024 * 1024)  # 10 MB


# ══════════════════════════════════════════════════════
# UPLOAD + ANALYZE (sync pipeline for immediate results)
# ══════════════════════════════════════════════════════

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant_id),
    user_id: str = Depends(get_current_user_id),
    payload: dict[str, Any] = Depends(require_fraud_analyst),
) -> UploadResponse:
    """Upload a document for real-time AI fraud analysis.

    Flow: validate → S3 → OCR → BrasilAPI → risk → copilot → report.
    """
    settings = get_settings()

    if not settings.ENABLE_OCR:
        return UploadResponse(
            document_id="ocr-disabled",
            status="skipped",
            message="OCR feature is disabled (ENABLE_OCR=false).",
        )

    # 1. Read file bytes
    file_data = await file.read()

    # 2. Validate
    validation = _validator.validate(
        file.filename or "unknown",
        len(file_data),
        file.content_type,
    )
    if not validation.is_valid:
        raise HTTPException(
            status_code=400,
            detail={"errors": validation.errors, "warnings": validation.warnings},
        )

    # 3. Run pipeline (synchronous for now — Celery async in production)
    document_id = str(uuid.uuid4())
    logger.info("Starting pipeline for document %s (%s, %d bytes)", document_id, file.filename, len(file_data))

    try:
        pipeline = get_pipeline_service()
        result = await pipeline.process_document(
            file_data=file_data,
            file_name=file.filename or "document.pdf",
            content_type=file.content_type or "application/octet-stream",
            tenant_id=tenant_id,
            user_id=user_id,
            extra_context=payload,
        )

        status = result.get("pipeline_status", "failed")
        message = (
            "Document analyzed successfully."
            if status == "completed"
            else f"Pipeline {status}: {result.get('error', 'Unknown error')}"
        )

        return UploadResponse(
            document_id=document_id,
            status=status,
            message=message,
            s3_key=result.get("stages", {}).get("upload", {}).get("s3_key"),
            presigned_url=result.get("stages", {}).get("upload", {}).get("presigned_url"),
        )

    except (InvalidFileTypeError, FileTooLargeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Pipeline failed for %s", document_id)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")


# ══════════════════════════════════════════════════════
# GET PIPELINE STATUS
# ══════════════════════════════════════════════════════

@router.get("/status/{document_id}", response_model=PipelineStatusResponse)
async def get_pipeline_status(
    document_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> PipelineStatusResponse:
    """Get the status and results of a document analysis pipeline."""
    # In production: query Celery task result or DB for pipeline status
    # For now, return a placeholder
    return PipelineStatusResponse(
        document_id=document_id,
        pipeline_status="unknown",
        stages={},
    )
