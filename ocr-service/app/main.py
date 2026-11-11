from __future__ import annotations

import logging
import secrets
import uuid
from typing import Annotated

from fastapi import FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from app.config import ServiceSettings
from app.engine import (
    OCREngine,
    OCRServiceError,
    PageLimitError,
    UnsupportedFileError,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

settings = ServiceSettings.from_env()
engine = OCREngine(
    default_dpi=settings.dpi,
    max_pages=settings.max_pages,
    force_fallback=settings.force_fallback,
)

app = FastAPI(title="PaySentinelIQ OCR Service", version="1.0.0")


def _detect_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF"):
        return "pdf"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg"
    return None


def _check_api_key(x_ocr_key: str | None) -> None:
    if not settings.api_key:
        return
    if not x_ocr_key or not secrets.compare_digest(
        settings.api_key,
        x_ocr_key,
    ):
        raise HTTPException(status_code=401, detail="Invalid OCR API key")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    if engine.is_ready():
        return JSONResponse(status_code=200, content={"status": "ready"})
    return JSONResponse(status_code=503, content={"status": "not_ready"})


@app.post("/ocr")
async def ocr(
    file: Annotated[UploadFile, File()],
    dpi: Annotated[int | None, Form()] = None,
    max_pages: Annotated[int | None, Form()] = None,
    x_ocr_key: Annotated[
        str | None,
        Header(alias="X-OCR-Key"),
    ] = None,
) -> dict:
    _check_api_key(x_ocr_key)

    request_id = uuid.uuid4().hex[:8]
    max_bytes = int(settings.max_mb * 1024 * 1024)
    data = await file.read(max_bytes + 1)

    if not data:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(data) > max_bytes:
        logger.warning(
            "ocr request id=%s rejected: size=%d max=%d",
            request_id,
            len(data),
            max_bytes,
        )
        raise HTTPException(status_code=413, detail="File too large")

    file_type = _detect_type(data)
    if file_type is None:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type (expected PDF, PNG or JPEG)",
        )

    effective_dpi = dpi if dpi is not None else settings.dpi
    effective_max_pages = (
        max_pages if max_pages is not None else settings.max_pages
    )
    if effective_dpi <= 0 or effective_max_pages <= 0:
        raise HTTPException(
            status_code=422,
            detail="dpi and max_pages must be positive",
        )

    logger.info(
        "ocr request id=%s started size=%d type=%s dpi=%d max_pages=%d",
        request_id,
        len(data),
        file_type,
        effective_dpi,
        effective_max_pages,
    )

    try:
        result = await run_in_threadpool(
            engine.extract,
            data,
            f"upload.{file_type}",
            effective_dpi,
            effective_max_pages,
        )
    except PageLimitError as exc:
        logger.warning(
            "ocr request id=%s page_limit pages=%d max=%d",
            request_id,
            exc.page_count,
            exc.max_pages,
        )
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OCRServiceError as exc:
        logger.error(
            "ocr request id=%s failed error=%s",
            request_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=500,
            detail="OCR processing failed",
        ) from exc

    logger.info(
        "ocr request id=%s completed provider=%s pages=%d",
        request_id,
        result.get("provider"),
        len(result.get("pages", [])),
    )
    return result
