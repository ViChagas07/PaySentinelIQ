from __future__ import annotations

import asyncio
import importlib
import importlib.util
import logging
import threading
import time
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from app.services.ocr.base import OCRPageResult, OCRProvider, OCRResult
from app.services.ocr.exceptions import (
    OCRProcessingException,
    UnsupportedFileTypeException,
)

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}

_ENGINE_INIT_LOCK = threading.Lock()
_ENGINE_RUN_LOCK = threading.Lock()
_ENGINE: Any = None
_ENGINE_LANGUAGE: str | None = None
_ENGINE_VERSION: str | None = None


def _package_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "N/A"


def _preload_torch() -> None:
    try:
        importlib.import_module("torch")
    except Exception:
        return


def _get_engine(language: str) -> tuple[Any, str]:
    global _ENGINE, _ENGINE_LANGUAGE, _ENGINE_VERSION

    with _ENGINE_INIT_LOCK:
        if _ENGINE is not None and _ENGINE_LANGUAGE == language:
            return _ENGINE, _ENGINE_VERSION or ""

        if importlib.util.find_spec("paddleocr") is None:
            raise OCRProcessingException(
                "PaddleOCR is not installed. Run: poetry install --with ocr-paddle",
                provider="paddleocr",
            )

        _preload_torch()

        try:
            paddleocr_module = importlib.import_module("paddleocr")
        except ImportError as exc:
            raise OCRProcessingException(
                "PaddleOCR is not installed. Run: poetry install --with ocr-paddle",
                provider="paddleocr",
            ) from exc

        engine_version = _package_version("paddleocr")
        try:
            if engine_version.startswith("3."):
                engine = paddleocr_module.PaddleOCR(
                    lang=language,
                    device="cpu",
                    use_doc_orientation_classify=True,
                    use_doc_unwarping=False,
                    use_textline_orientation=True,
                )
            else:
                engine = paddleocr_module.PaddleOCR(
                    lang=language,
                    use_angle_cls=True,
                    use_gpu=False,
                    show_log=False,
                )
        except Exception as exc:
            raise OCRProcessingException(
                f"Could not initialize PaddleOCR: {exc}",
                provider="paddleocr",
            ) from exc

        _ENGINE = engine
        _ENGINE_LANGUAGE = language
        _ENGINE_VERSION = engine_version
        return engine, engine_version


def _parse_v2_result(raw: Any) -> tuple[str, float]:
    if not raw:
        return "", 0.0

    first = raw[0] if isinstance(raw, list) else raw
    lines = first if isinstance(first, list) else []

    texts: list[str] = []
    scores: list[float] = []
    for item in lines:
        if not item or not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        payload = item[1]
        if isinstance(payload, (list, tuple)) and len(payload) >= 2:
            text = str(payload[0])
            score = float(payload[1])
        elif isinstance(payload, str):
            text = payload
            score = 0.0
        else:
            continue
        if text.strip():
            texts.append(text.strip())
            scores.append(max(0.0, min(1.0, score)))

    if not texts:
        return "", 0.0
    confidence = sum(scores) / len(scores) if scores else 0.0
    return "\n".join(texts), round(confidence, 4)


def _parse_v3_result(raw: Any) -> tuple[str, float]:
    texts: list[str] = []
    scores: list[float] = []

    for page in raw or []:
        data: Any = page
        if hasattr(page, "json"):
            data = page.json
        elif hasattr(page, "res"):
            data = page.res
        if isinstance(data, dict):
            result = data.get("res", data)
            if not isinstance(result, dict):
                continue
            page_texts = result.get("rec_texts") or []
            page_scores = result.get("rec_scores") or []
            for index, text in enumerate(page_texts):
                if not text:
                    continue
                score = (
                    float(page_scores[index])
                    if index < len(page_scores)
                    else 0.0
                )
                texts.append(str(text))
                scores.append(max(0.0, min(1.0, score)))

    if not texts:
        return "", 0.0
    confidence = sum(scores) / len(scores) if scores else 0.0
    return "\n".join(texts), round(confidence, 4)


class PaddleOCRProvider(OCRProvider):
    def __init__(
        self,
        language: str = "latin",
        dpi: int = 300,
        max_pages: int = 10,
    ) -> None:
        self._language = language
        self._dpi = dpi
        self._max_pages = max_pages

    async def extract_text(self, file_path: str) -> OCRResult:
        start_time = time.monotonic()
        path = Path(file_path)

        if not path.exists():
            raise OCRProcessingException(
                f"File not found: {file_path}",
                provider="paddleocr",
            )

        extension = path.suffix.lower()
        if extension not in SUPPORTED_TYPES:
            raise UnsupportedFileTypeException(extension, list(SUPPORTED_TYPES))

        if extension == ".pdf":
            pages = await asyncio.to_thread(
                self._extract_pdf_pages,
                str(path),
            )
        else:
            pages = await asyncio.to_thread(
                self._extract_image_page,
                str(path),
            )

        confidence = (
            sum(page.confidence for page in pages) / len(pages)
            if pages
            else 0.0
        )
        duration_ms = int((time.monotonic() - start_time) * 1000)

        return OCRResult(
            text="\n\n".join(page.text for page in pages),
            pages=pages,
            confidence=round(confidence, 4),
            provider="paddleocr",
            processing_time_seconds=round(duration_ms / 1000, 2),
            metadata={
                "language": self._language,
                "dpi": str(self._dpi),
                "max_pages": str(self._max_pages),
                "duration_ms": str(duration_ms),
                "page_count": str(len(pages)),
            },
        )

    async def health_check(self) -> bool:
        try:
            return (
                importlib.util.find_spec("paddleocr") is not None
                and importlib.util.find_spec("paddle") is not None
            )
        except Exception:
            return False

    def get_info(self) -> dict[str, str]:
        engine_version = _package_version("paddleocr")
        major = engine_version.split(".", 1)[0]
        if major == "3":
            orientation = "use_doc_orientation_classify=true"
            unwarping = "use_doc_unwarping=false"
        else:
            orientation = "use_angle_cls=true"
            unwarping = "not_available"

        return {
            "provider": "paddleocr",
            "language": self._language,
            "paddleocr_version": engine_version,
            "paddle_version": _package_version("paddlepaddle"),
            "orientation": orientation,
            "unwarping": unwarping,
            "dpi": str(self._dpi),
            "max_pages": str(self._max_pages),
            "supported_types": ", ".join(SUPPORTED_TYPES),
        }

    def _run_engine(self, image: Any) -> tuple[str, float]:
        engine, engine_version = _get_engine(self._language)
        with _ENGINE_RUN_LOCK:
            if engine_version.startswith("3."):
                raw = engine.predict(image)
                return _parse_v3_result(raw)
            raw = engine.ocr(image, cls=True)
            return _parse_v2_result(raw)

    def _extract_pdf_pages(self, file_path: str) -> list[OCRPageResult]:
        fitz = importlib.import_module("fitz")
        import numpy as np

        document = fitz.open(file_path)
        try:
            if document.page_count > self._max_pages:
                raise OCRProcessingException(
                    "PDF has "
                    f"{document.page_count} pages, exceeding OCR_MAX_PAGES="
                    f"{self._max_pages}",
                    provider="paddleocr",
                )

            pages: list[OCRPageResult] = []
            for index, page in enumerate(document, start=1):
                pixmap = page.get_pixmap(dpi=self._dpi, alpha=False)
                image = np.frombuffer(
                    pixmap.samples,
                    dtype=np.uint8,
                ).reshape(pixmap.height, pixmap.width, pixmap.n)
                if pixmap.n == 1:
                    image = np.repeat(image, 3, axis=2)
                elif pixmap.n == 4:
                    image = image[:, :, :3]
                image = image[:, :, ::-1].copy()

                text, confidence = self._run_engine(image)
                pages.append(
                    OCRPageResult(
                        page_number=index,
                        text=text,
                        confidence=confidence,
                        width=pixmap.width,
                        height=pixmap.height,
                    )
                )
            return pages
        finally:
            document.close()

    def _extract_image_page(self, file_path: str) -> list[OCRPageResult]:
        from PIL import Image

        with Image.open(file_path) as image:
            width, height = image.size

        text, confidence = self._run_engine(file_path)
        return [
            OCRPageResult(
                page_number=1,
                text=text,
                confidence=confidence,
                width=width,
                height=height,
            )
        ]
