# ============================================================
# PaySentinelIQ — Tesseract OCR Provider
# Production OCR implementation using Tesseract + pdf2image.
# ============================================================

from __future__ import annotations

import os
import time
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Any

from app.services.ocr.base import OCRProvider, OCRResult, OCRPageResult
from app.services.ocr.exceptions import (
    UnsupportedFileTypeException,
    OCRProcessingException,
    PDFConversionException,
    TesseractNotInstalledException,
)
from app.services.ocr.image_preprocessing import preprocess_for_document

logger = logging.getLogger(__name__)

# ── Lazy imports for optional dependencies ──
try:
    import pytesseract
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None  # type: ignore

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    Image = None  # type: ignore

try:
    from pdf2image import convert_from_path
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
    convert_from_path = None  # type: ignore


# ── Supported file types ──
SUPPORTED_TYPES = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}


class TesseractOCRProvider(OCRProvider):
    """Tesseract OCR provider with PDF support via pdf2image.

    Handles:
    - Single images (PNG, JPG, JPEG, TIFF, BMP)
    - Multi-page PDFs (converted to images via pdf2image)
    - Image preprocessing for accuracy enhancement
    - Confidence scoring per page
    """

    def __init__(
        self,
        tesseract_cmd: str | None = None,
        language: str = "por+eng",  # Portuguese + English by default
        preprocess: bool = True,
        temp_dir: str | None = None,
    ):
        self._tesseract_cmd = tesseract_cmd
        self._language = language
        self._preprocess = preprocess
        self._temp_dir = temp_dir or tempfile.gettempdir()

        # Validate Tesseract availability
        if not HAS_TESSERACT:
            raise TesseractNotInstalledException()

        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        self._verify_installation()

    # ── Public API ──

    async def extract_text(self, file_path: str) -> OCRResult:
        """Extract text from a document using Tesseract OCR.

        Supports PDFs (multi-page) and images (PNG, JPG, etc.).
        """
        start_time = time.monotonic()
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise OCRProcessingException(f"File not found: {file_path}")

        ext = file_path_obj.suffix.lower()
        if ext not in SUPPORTED_TYPES:
            raise UnsupportedFileTypeException(ext, list(SUPPORTED_TYPES))

        # ── PDF handling ──
        if ext == ".pdf":
            result = await self._process_pdf(file_path)
        else:
            result = await self._process_image(file_path)

        result.processing_time_seconds = round(time.monotonic() - start_time, 2)
        result.provider = "tesseract"
        result.metadata["language"] = self._language
        result.metadata["preprocessing"] = str(self._preprocess)

        logger.info(
            "OCR completed: provider=tesseract pages=%d confidence=%.2f duration=%.1fs",
            result.page_count,
            result.confidence,
            result.processing_time_seconds,
        )

        return result

    async def health_check(self) -> bool:
        """Verify Tesseract is functional."""
        try:
            version = pytesseract.get_tesseract_version()
            return version is not None and len(str(version)) > 0
        except Exception:
            return False

    def get_info(self) -> dict[str, str]:
        return {
            "provider": "tesseract",
            "language": self._language,
            "preprocessing": str(self._preprocess),
            "supported_types": ", ".join(SUPPORTED_TYPES),
            "tesseract_version": str(pytesseract.get_tesseract_version()) if HAS_TESSERACT else "N/A",
        }

    # ── Private: PDF Processing ──

    async def _process_pdf(self, file_path: str) -> OCRResult:
        """Extract text from PDF using multi-method approach.

        Strategy:
            1. Try robust text extraction first (PyMuPDF → pdfplumber → pypdf)
               — this is faster and more accurate for text-based PDFs
            2. If text extraction yields meaningful result, use it directly
            3. If text extraction fails or returns near-empty text,
               fall back to image-based OCR (Tesseract via pdf2image)

        This dual approach eliminates the false-negative root cause
        where canvas-generated PDFs (ReportLab, iText) produce garbled
        or empty text with simple extractors.
        """
        start_time = time.monotonic()

        # ── Phase 1: Try robust text extraction ──
        extracted_text = ""
        text_method = "none"
        try:
            with open(file_path, "rb") as f:
                pdf_bytes = f.read()

            from app.services.ocr.pdf_text_extractor import (
                extract_pdf_text_robust,
                is_text_extraction_viable,
            )

            if is_text_extraction_viable(pdf_bytes):
                extracted_text = extract_pdf_text_robust(pdf_bytes)
                text_method = "robust_text_extraction"
                logger.info(
                    "Robust text extraction succeeded: %d chars via %s",
                    len(extracted_text),
                    text_method,
                )
        except Exception as e:
            logger.info(
                "Robust text extraction not viable, falling back to OCR: %s", e
            )

        # ── Phase 2: If text extraction worked, use it ──
        # Threshold: at least 50 word characters = meaningful content
        word_chars = sum(1 for c in extracted_text if c.isalnum())
        if word_chars >= 50:
            elapsed = round(time.monotonic() - start_time, 2)
            page_result = OCRPageResult(
                page_number=1,
                text=extracted_text.strip(),
                confidence=0.98,  # Text extraction is highly reliable
            )
            logger.info(
                "Using text-extracted content (%d chars, %d word chars) — "
                "skipping image-based OCR. Saved time.",
                len(extracted_text),
                word_chars,
            )
            return OCRResult(
                text=extracted_text.strip(),
                pages=[page_result],
                confidence=0.98,
                provider="tesseract",
                processing_time_seconds=elapsed,
                metadata={
                    "extraction_method": text_method,
                    "ocr_skipped": "true",
                    "language": self._language,
                },
            )

        # ── Phase 3: Fall back to image-based OCR ──
        logger.info(
            "Text extraction insufficient (%d word chars), "
            "falling back to image-based OCR",
            word_chars,
        )

        if not HAS_PDF2IMAGE:
            raise PDFConversionException(
                "pdf2image is not installed. Install it with: pip install pdf2image",
                file_path=file_path,
            )

        temp_work_dir = None
        try:
            # Create temp directory for converted images
            temp_work_dir = tempfile.mkdtemp(dir=self._temp_dir, prefix="psi_ocr_")

            # Convert PDF to images
            logger.debug("Converting PDF to images: %s", file_path)
            images = convert_from_path(
                file_path,
                dpi=300,  # High DPI for better OCR
                fmt="png",
                output_folder=temp_work_dir,
                thread_count=2,
            )

            if not images:
                raise PDFConversionException(
                    f"PDF produced no images: {file_path}", file_path=file_path
                )

            # OCR each page
            page_results: list[OCRPageResult] = []
            all_text: list[str] = []

            for i, image in enumerate(images, 1):
                page_result = await self._ocr_image(image, page_number=i)
                page_results.append(page_result)
                all_text.append(page_result.text)

            # Calculate average confidence
            avg_confidence = (
                sum(p.confidence for p in page_results) / len(page_results)
                if page_results
                else 0.0
            )

            return OCRResult(
                text="\n\n".join(all_text),
                pages=page_results,
                confidence=round(avg_confidence, 4),
            )

        except PDFConversionException:
            raise
        except Exception as e:
            raise PDFConversionException(
                f"PDF processing failed: {e}", file_path=file_path
            ) from e
        finally:
            # Cleanup temp directory
            if temp_work_dir and os.path.exists(temp_work_dir):
                try:
                    shutil.rmtree(temp_work_dir, ignore_errors=True)
                except Exception:
                    pass

    # ── Private: Image Processing ──

    async def _process_image(self, file_path: str) -> OCRResult:
        """Process a single image file."""
        if not HAS_PILLOW:
            raise OCRProcessingException("Pillow is not installed for image processing")

        try:
            image = Image.open(file_path)
            page_result = await self._ocr_image(image, page_number=1)

            return OCRResult(
                text=page_result.text,
                pages=[page_result],
                confidence=page_result.confidence,
            )
        except Exception as e:
            raise OCRProcessingException(
                f"Image OCR failed: {e}", provider="tesseract"
            ) from e

    async def _ocr_image(self, image: Any, page_number: int) -> OCRPageResult:
        """Run OCR on a single PIL Image."""
        # Preprocessing
        if self._preprocess:
            image = preprocess_for_document(image)

        # Run OCR with confidence data
        try:
            ocr_data = pytesseract.image_to_data(
                image,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
                config="--psm 6",  # Assume uniform block of text
            )

            # Extract text and confidence
            texts = []
            confidences = []

            for i, conf in enumerate(ocr_data.get("conf", [])):
                if conf != "-1" and int(conf) > 0:
                    texts.append(ocr_data["text"][i])
                    confidences.append(int(conf))

            full_text = " ".join(texts)
            avg_conf = sum(confidences) / len(confidences) / 100.0 if confidences else 0.0

            return OCRPageResult(
                page_number=page_number,
                text=full_text.strip(),
                confidence=round(avg_conf, 4),
                width=image.width if hasattr(image, "width") else None,
                height=image.height if hasattr(image, "height") else None,
            )

        except Exception as e:
            # Fallback: simple text extraction without confidence
            logger.warning("Detailed OCR failed, using simple extraction: %s", e)
            text = pytesseract.image_to_string(image, lang=self._language, config="--psm 6")
            return OCRPageResult(
                page_number=page_number,
                text=text.strip(),
                confidence=0.0,
            )

    def _verify_installation(self) -> None:
        """Verify Tesseract is installed and accessible."""
        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract version: %s", version)
        except Exception as e:
            raise TesseractNotInstalledException() from e
