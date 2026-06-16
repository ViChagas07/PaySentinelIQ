# ============================================================
# PaySentinelIQ — OCR Exceptions
# Typed exception hierarchy for OCR-specific errors.
# ============================================================


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
