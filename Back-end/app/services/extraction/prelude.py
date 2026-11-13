from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Any

from app.core.contracts.pipeline_context import PipelineContext
from app.services.ocr.base import OCRProvider
from app.services.ocr.exceptions import classify_ocr_exception

logger = logging.getLogger(__name__)

_SUPPORTED_MIME_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
}


def _useful_chars(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


def _confidence_percent(confidence: float) -> float:
    percent = confidence * 100 if confidence <= 1.0 else confidence
    return max(0.0, min(100.0, percent))


def _set_failure(
    ctx: PipelineContext,
    category: str,
) -> None:
    ctx.metadata["ocr"] = {
        "status": category,
        "error": category,
    }
    ctx.metadata.pop("ocr_prelude", None)
    ctx.add_warning(f"ocr_{category}")


async def run_ocr_prelude(
    ctx: PipelineContext,
    provider: OCRProvider | None = None,
) -> None:
    from app.shared.settings import get_settings

    settings = get_settings()
    if not getattr(settings, "ENABLE_OCR", False):
        return

    mime_type = (ctx.mime_type or "").split(";", 1)[0].strip().lower()
    extension = _SUPPORTED_MIME_EXTENSIONS.get(mime_type)
    if extension is None:
        return

    try:
        if provider is None:
            from app.services.ocr.factory import get_ocr_provider

            provider = get_ocr_provider()

        with tempfile.TemporaryDirectory(prefix="psi_ocr_") as temp_dir:
            file_path = Path(temp_dir) / f"document{extension}"
            file_path.write_bytes(ctx.file_bytes)
            extraction = provider.extract_text(str(file_path))
            if getattr(provider, "supports_hard_timeout", False):
                result = await asyncio.wait_for(
                    extraction,
                    timeout=float(settings.OCR_SERVICE_TIMEOUT),
                )
            else:
                result = await extraction

        if _useful_chars(result.text) < 20:
            ctx.metadata["ocr"] = {"status": "empty"}
            ctx.metadata.pop("ocr_prelude", None)
            ctx.add_warning("ocr_empty_text")
            logger.info(
                "OCR prelude status=empty provider=%s bytes=%d",
                result.provider,
                len(ctx.file_bytes),
            )
            return

        confidence = _confidence_percent(result.confidence)
        ocr_metadata: dict[str, Any] = {
            "status": "completed",
            "provider": result.provider,
            "confidence": confidence,
            "page_count": result.page_count,
            "duration_s": float(result.processing_time_seconds),
        }
        for key in ("native_pages", "ocr_pages"):
            if key in result.metadata:
                ocr_metadata[key] = result.metadata[key]

        ctx.extracted_text = result.text
        ctx.extraction_method = result.provider
        ctx.page_count = result.page_count
        ctx.ocr_confidence = confidence
        ctx.metadata["ocr"] = ocr_metadata
        ctx.metadata["ocr_prelude"] = True

        logger.info(
            "OCR prelude status=completed provider=%s pages=%d "
            "confidence=%.1f duration=%.2fs",
            result.provider,
            result.page_count,
            confidence,
            result.processing_time_seconds,
        )
    except Exception as exc:
        category = classify_ocr_exception(exc)
        _set_failure(ctx, category)
        logger.warning(
            "OCR prelude status=%s bytes=%d",
            category,
            len(ctx.file_bytes),
        )
