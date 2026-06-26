# ============================================================
# PaySentinelIQ — OCR Service Layer
# Clean Architecture OCR abstraction with Tesseract provider.
# Prepared for future AWS Textract swap without refactoring.
# ============================================================

from app.services.ocr.base import OCRProvider, OCRResult, OCRPageResult
from app.services.ocr.models import ExtractionResult, ExtractedField
from app.services.ocr.exceptions import (
    OCRException,
    UnsupportedFileTypeException,
    OCRProcessingException,
    PDFConversionException,
)
from app.services.ocr.tesseract_provider import TesseractOCRProvider
from app.services.ocr.factory import OCRFactory, get_ocr_provider
from app.services.ocr.extraction_service import DocumentExtractionService
from app.services.ocr.pdf_text_extractor import (
    extract_text_robust,
    extract_pdf_text_robust,
    is_text_extraction_viable,
)

__all__ = [
    "OCRProvider",
    "OCRResult",
    "OCRPageResult",
    "ExtractionResult",
    "ExtractedField",
    "OCRException",
    "UnsupportedFileTypeException",
    "OCRProcessingException",
    "PDFConversionException",
    "TesseractOCRProvider",
    "OCRFactory",
    "get_ocr_provider",
    "DocumentExtractionService",
    "extract_text_robust",
    "extract_pdf_text_robust",
    "is_text_extraction_viable",
]
