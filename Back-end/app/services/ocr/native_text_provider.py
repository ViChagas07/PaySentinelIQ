from __future__ import annotations

import importlib
import logging
import shutil
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.services.ocr.base import OCRPageResult, OCRProvider, OCRResult
from app.services.ocr.exceptions import (
    OCRProcessingException,
    UnsupportedFileTypeException,
)

logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


def _useful_chars(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


class NativeTextFirstOCRProvider(OCRProvider):
    def __init__(
        self,
        primary: OCRProvider,
        fallback: OCRProvider | None = None,
        fallback_factory: Callable[[], OCRProvider] | None = None,
        dpi: int = 300,
        max_pages: int = 10,
        min_native_chars: int = 50,
    ) -> None:
        self._primary = primary
        self._fallback = fallback
        self._fallback_factory = fallback_factory
        self._dpi = dpi
        self._max_pages = max_pages
        self._min_native_chars = min_native_chars
        self._primary_disabled = False

    async def extract_text(self, file_path: str) -> OCRResult:
        start_time = time.monotonic()
        path = Path(file_path)

        if not path.exists():
            raise OCRProcessingException(f"File not found: {file_path}")

        extension = path.suffix.lower()
        if extension not in SUPPORTED_TYPES:
            raise UnsupportedFileTypeException(extension, list(SUPPORTED_TYPES))

        if extension != ".pdf":
            result = await self._extract_with_fallback(str(path))
            duration_ms = int((time.monotonic() - start_time) * 1000)
            result.metadata["duration_ms"] = str(duration_ms)
            result.metadata["native_text"] = "false"
            return result

        return await self._extract_pdf(str(path), start_time)

    async def health_check(self) -> bool:
        try:
            if not self._primary_disabled and await self._primary.health_check():
                return True
        except Exception:
            pass
        fallback = self._get_fallback()
        if fallback is None:
            return False
        try:
            return await fallback.health_check()
        except Exception:
            return False

    def get_info(self) -> dict[str, str]:
        fallback = self._fallback
        return {
            "provider": "native_text_first",
            "primary": self._primary.get_info().get("provider", "unknown"),
            "fallback": (
                fallback.get_info().get("provider", "unknown")
                if fallback is not None
                else "lazy" if self._fallback_factory is not None else "none"
            ),
            "dpi": str(self._dpi),
            "max_pages": str(self._max_pages),
            "min_native_chars": str(self._min_native_chars),
        }

    async def _extract_pdf(
        self,
        file_path: str,
        start_time: float,
    ) -> OCRResult:
        page_texts = await _to_thread(self._extract_native_pages, file_path)
        temp_dir = tempfile.mkdtemp(prefix="psi_native_ocr_")
        pages: list[OCRPageResult] = []
        sources: list[str] = []

        try:
            for page_number, native_text in enumerate(page_texts, start=1):
                if _useful_chars(native_text) >= self._min_native_chars:
                    pages.append(
                        OCRPageResult(
                            page_number=page_number,
                            text=native_text.strip(),
                            confidence=1.0,
                        )
                    )
                    sources.append("native_text")
                    continue

                image_path = await _to_thread(
                    self._render_page,
                    file_path,
                    page_number,
                    temp_dir,
                )
                result = await self._extract_with_fallback(image_path)
                page = result.pages[0] if result.pages else OCRPageResult(
                    page_number=page_number,
                    text=result.text,
                    confidence=result.confidence,
                )
                pages.append(
                    OCRPageResult(
                        page_number=page_number,
                        text=page.text,
                        confidence=page.confidence,
                        width=page.width,
                        height=page.height,
                    )
                )
                sources.append(result.provider or "ocr")
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        confidence = (
            sum(page.confidence for page in pages) / len(pages)
            if pages
            else 0.0
        )
        duration_ms = int((time.monotonic() - start_time) * 1000)
        unique_sources = list(dict.fromkeys(sources))
        provider = "+".join(unique_sources) if unique_sources else "native_text"

        return OCRResult(
            text="\n\n".join(page.text for page in pages),
            pages=pages,
            confidence=round(confidence, 4),
            provider=provider,
            processing_time_seconds=round(duration_ms / 1000, 2),
            metadata={
                "native_pages": str(sources.count("native_text")),
                "ocr_pages": str(len(sources) - sources.count("native_text")),
                "page_sources": ",".join(sources),
                "duration_ms": str(duration_ms),
                "dpi": str(self._dpi),
                "max_pages": str(self._max_pages),
                "min_native_chars": str(self._min_native_chars),
            },
        )

    def _extract_native_pages(self, file_path: str) -> list[str]:
        fitz = importlib.import_module("fitz")

        document = fitz.open(file_path)
        try:
            if document.page_count > self._max_pages:
                raise OCRProcessingException(
                    "PDF has "
                    f"{document.page_count} pages, exceeding OCR_MAX_PAGES="
                    f"{self._max_pages}"
                )
            return [page.get_text("text") for page in document]
        finally:
            document.close()

    def _render_page(
        self,
        file_path: str,
        page_number: int,
        temp_dir: str,
    ) -> str:
        fitz = importlib.import_module("fitz")

        document = fitz.open(file_path)
        try:
            page = document[page_number - 1]
            pixmap = page.get_pixmap(dpi=self._dpi, alpha=False)
            image_path = str(
                Path(temp_dir) / f"page_{page_number}.png"
            )
            pixmap.save(image_path)
            return image_path
        finally:
            document.close()

    async def _extract_with_fallback(self, file_path: str) -> OCRResult:
        if not self._primary_disabled:
            try:
                return await self._primary.extract_text(file_path)
            except Exception:
                if self._get_fallback() is None:
                    raise
                logger.warning(
                    "Primary OCR provider failed; falling back",
                    exc_info=True,
                )
                self._primary_disabled = True

        fallback = self._get_fallback()
        if fallback is None:
            raise OCRProcessingException(
                "Primary OCR provider failed and no fallback is available"
            )
        return await fallback.extract_text(file_path)

    def _get_fallback(self) -> OCRProvider | None:
        if self._fallback is None and self._fallback_factory is not None:
            try:
                self._fallback = self._fallback_factory()
            except Exception:
                logger.warning(
                    "OCR fallback provider is unavailable",
                    exc_info=True,
                )
                return None
        return self._fallback


async def _to_thread(function: Callable[..., Any], *args: Any) -> Any:
    import asyncio

    return await asyncio.to_thread(function, *args)
