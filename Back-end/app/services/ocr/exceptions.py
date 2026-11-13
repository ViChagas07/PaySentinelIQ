# ============================================================
# PaySentinelIQ — OCR Exceptions
# Typed exception hierarchy for OCR-specific errors.
# ============================================================

import asyncio


class OCRException(Exception):
    """Base exception for all OCR-related errors."""

    def __init__(self, message: str, provider: str | None = None, file_path: str | None = None):
        self.provider = provider
        self.file_path = file_path
        super().__init__(message)


class UnsupportedFileTypeException(OCRException):
    """Raised when the uploaded file type is not supported for OCR."""

    def __init__(self, file_type: str, supported: list[str] | None = None):
        self.file_type = file_type
        self.supported = supported or ["pdf", "png", "jpg", "jpeg"]
        super().__init__(
            f"Unsupported file type '{file_type}'. Supported types: {', '.join(self.supported)}"
        )


class OCRProcessingException(OCRException):
    """Raised when OCR processing fails for any reason."""

    def __init__(self, message: str, provider: str | None = None, page: int | None = None):
        self.page = page
        super().__init__(message, provider=provider)


class PDFConversionException(OCRException):
    """Raised when PDF-to-image conversion fails."""

    def __init__(self, message: str, file_path: str | None = None):
        super().__init__(message, file_path=file_path)


class TesseractNotInstalledException(OCRException):
    """Raised when Tesseract OCR engine is not found on the system."""

    def __init__(self):
        super().__init__(
            "Tesseract OCR engine is not installed. "
            "Install it from https://github.com/UB-Mannheim/tesseract/wiki "
            "or run: winget install UB-Mannheim.TesseractOCR"
        )


_OCR_STATUS_BY_CATEGORY = {
    "timeout": (503, "ocr_timeout", "OCR processing timed out"),
    "unavailable": (503, "ocr_unavailable", "OCR service is unavailable"),
    "invalid_response": (
        502,
        "ocr_invalid_response",
        "OCR service returned an invalid response",
    ),
    "empty": (
        422,
        "analysis_inconclusive",
        "Document contains insufficient text for analysis",
    ),
    "error": (502, "ocr_error", "OCR processing failed"),
}


def classify_ocr_exception(exc: Exception) -> str:
    """Classify an OCR failure without exposing its raw message."""
    message = str(exc).lower()
    if isinstance(exc, (asyncio.TimeoutError, TimeoutError)):
        return "timeout"
    if "timed out" in message or "timeout" in message:
        return "timeout"
    if isinstance(exc, TesseractNotInstalledException):
        return "unavailable"
    if any(
        marker in message
        for marker in (
            "could not connect",
            "not installed",
            "not configured",
            "no response",
            "unavailable",
        )
    ):
        return "unavailable"
    if any(
        marker in message
        for marker in (
            "invalid json",
            "invalid payload",
            "returned http",
        )
    ):
        return "invalid_response"
    return "error"


class OCRFailureError(Exception):
    """Operational OCR failure with a stable public category and ID."""

    def __init__(self, category: str, correlation_id: str) -> None:
        safe_category = category if category in _OCR_STATUS_BY_CATEGORY else "error"
        self.category = safe_category
        (
            self.status_code,
            self.error_code,
            self.public_message,
        ) = _OCR_STATUS_BY_CATEGORY[safe_category]
        self.correlation_id = correlation_id
        super().__init__(self.public_message)
