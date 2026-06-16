# ============================================================
# PaySentinelIQ — OCR Base Models & Abstract Provider
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class OCRPageResult:
    """OCR result for a single page."""

    page_number: int
    text: str
    confidence: float  # 0.0 to 1.0
    width: int | None = None
    height: int | None = None


@dataclass
class OCRResult:
    """Complete OCR result for a document (may contain multiple pages)."""

    text: str
    pages: list[OCRPageResult] = field(default_factory=list)
    confidence: float = 0.0  # average across all pages
    provider: str = ""
    processing_time_seconds: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def page_count(self) -> int:
        return len(self.pages) if self.pages else 1

    @property
    def full_text(self) -> str:
        """Concatenated text from all pages."""
        if self.pages:
            return "\n\n".join(p.text for p in self.pages)
        return self.text

    def to_dict(self) -> dict:
        return {
            "text": self.full_text,
            "page_count": self.page_count,
            "confidence": round(self.confidence, 4),
            "provider": self.provider,
            "processing_time_seconds": round(self.processing_time_seconds, 2),
            "metadata": self.metadata,
            "pages": [
                {
                    "page": p.page_number,
                    "confidence": round(p.confidence, 4),
                    "text_length": len(p.text),
                }
                for p in self.pages
            ],
        }


class OCRProvider(ABC):
    """Abstract OCR provider — all implementations must use this interface.

    This abstraction enables swapping Tesseract for AWS Textract
    or Google Vision without changing any business logic.
    """

    @abstractmethod
    async def extract_text(self, file_path: str) -> OCRResult:
        """Extract text from a document file.

        Args:
            file_path: Path to the document file (PDF, PNG, JPG, JPEG).

        Returns:
            OCRResult with extracted text, confidence scores, and metadata.

        Raises:
            UnsupportedFileTypeException: If the file type is not supported.
            OCRProcessingException: If OCR processing fails.
            PDFConversionException: If PDF-to-image conversion fails.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the OCR provider is available and functional."""
        ...

    @abstractmethod
    def get_info(self) -> dict[str, str]:
        """Return provider information for diagnostics."""
        ...
