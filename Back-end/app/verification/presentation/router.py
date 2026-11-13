# ============================================================
# PaySentinelIQ — Verification Router
# Real S3 upload + OCR + AI pipeline endpoint.
# ============================================================

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import get_current_tenant_id, get_current_user_id, require_fraud_analyst
from app.services.storage import InvalidFileTypeError, FileTooLargeError
from app.services.pipeline_service import get_pipeline_service
from app.services.upload_validation import (
    UploadPolicy,
    read_upload_limited,
    validate_upload_bytes,
)
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
    correlation_id: str | None = None


class PipelineStatusResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    document_id: str
    pipeline_status: str  # processing, completed, failed
    risk_score: float | None = None
    risk_level: str | None = None
    processing_time_seconds: float | None = None
    stages: dict[str, Any] = {}
    error: str | None = None


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

    # 1. Read bounded bytes and validate before OCR or pipeline work.
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

    if not settings.ENABLE_OCR:
        return UploadResponse(
            document_id="ocr-disabled",
            status="skipped",
            message="OCR feature is disabled (ENABLE_OCR=false).",
        )

    # 2. Run pipeline (synchronous for now — Celery async in production)
    document_id = str(uuid.uuid4())
    logger.info(
        "Starting pipeline for document %s (%d bytes)",
        document_id,
        len(file_data),
    )

    try:
        pipeline = get_pipeline_service()
        result = await pipeline.process_document(
            file_data=file_data,
            file_name=file_name,
            content_type=mime_type,
            tenant_id=tenant_id,
            user_id=user_id,
            extra_context=payload,
        )

        status = result.get("pipeline_status", "failed")
        base_headers = {
            "Deprecation": "true",
            "Sunset": "Sat, 01 Jan 2027 00:00:00 GMT",
            "Link": '</api/documents/analyze>; rel="successor-version"',
            "Warning": '299 - "This endpoint is deprecated. Use POST /api/documents/analyze"',
        }

        if status != "completed":
            correlation_id = str(uuid.uuid4())
            logger.error(
                "Upload pipeline failed: correlation_id=%s document_id=%s tenant_id=%s pipeline_status=%s",
                correlation_id,
                document_id,
                tenant_id,
                status,
            )
            response = UploadResponse(
                document_id=document_id,
                status="failed",
                message="Analysis could not be completed.",
                s3_key=None,
                presigned_url=None,
                correlation_id=correlation_id,
            )
            return JSONResponse(
                content=response.model_dump(),
                headers={
                    **base_headers,
                    "X-Correlation-ID": correlation_id,
                },
            )

        response = UploadResponse(
            document_id=document_id,
            status="completed",
            message="Document analyzed successfully.",
            s3_key=result.get("stages", {}).get("upload", {}).get("s3_key"),
            presigned_url=result.get("stages", {}).get("upload", {}).get("presigned_url"),
        )
        # Fase 5: Deprecation — use POST /api/documents/analyze instead
        return JSONResponse(
            content=response.model_dump(),
            headers=base_headers,
        )

    except FileTooLargeError:
        raise HTTPException(
            status_code=413,
            detail="File exceeds the allowed size",
        ) from None
    except InvalidFileTypeError:
        raise HTTPException(
            status_code=415,
            detail="Unsupported file type",
        ) from None
    except Exception as exc:
        correlation_id = str(uuid.uuid4())
        logger.error(
            "Upload pipeline failed: correlation_id=%s document_id=%s tenant_id=%s error_type=%s",
            correlation_id,
            document_id,
            tenant_id,
            type(exc).__name__,
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
