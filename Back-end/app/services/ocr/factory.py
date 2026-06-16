# ============================================================
# PaySentinelIQ — OCR Factory
# Provider factory pattern. Today: Tesseract. Tomorrow: Textract.
# Swap provider via config — no business logic changes needed.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

from app.services.ocr.base import OCRProvider
from app.services.ocr.tesseract_provider import TesseractOCRProvider
from app.services.ocr.exceptions import OCRException


logger = logging.getLogger(__name__)

# ── Singleton cache ──
_ocr_provider: OCRProvider | None = None
_provider_type: str | None = None


class OCRFactory:
    """Creates OCR provider instances based on configuration.

    Usage:
        provider = OCRFactory.create("tesseract")
        # Future:
        provider = OCRFactory.create("textract")
    """

    @staticmethod
    def create(
        provider_type: str = "tesseract",
        **kwargs: Any,
    ) -> OCRProvider:
        """Create an OCR provider instance.

        Args:
            provider_type: "tesseract" (today) or "textract" (future).
            **kwargs: Provider-specific configuration.
                For Tesseract: tesseract_cmd, language, preprocess, temp_dir.
                For Textract: region_name, role_arn (future).

        Returns:
            Configured OCRProvider instance.

        Raises:
            OCRException: If the provider type is unknown.
        """
        provider_type = provider_type.lower().strip()

        if provider_type == "tesseract":
            return TesseractOCRProvider(
                tesseract_cmd=kwargs.get("tesseract_cmd"),
                language=kwargs.get("language", "por+eng"),
                preprocess=kwargs.get("preprocess", True),
                temp_dir=kwargs.get("temp_dir"),
            )

        elif provider_type == "textract":
            # Future: AWS Textract integration
            # from app.services.ocr.textract_provider import TextractOCRProvider
            # return TextractOCRProvider(
            #     region_name=kwargs.get("region_name", "us-east-1"),
            #     role_arn=kwargs.get("role_arn"),
            # )
            raise OCRException(
                "AWS Textract provider is not yet implemented. Use 'tesseract' instead."
            )

        else:
            raise OCRException(
                f"Unknown OCR provider: '{provider_type}'. Supported: tesseract"
            )


def get_ocr_provider(
    provider_type: str | None = None,
    force_recreate: bool = False,
    **kwargs: Any,
) -> OCRProvider:
    """Get or create a singleton OCR provider instance.

    Args:
        provider_type: Override the default provider type.
        force_recreate: If True, create a new instance even if cached.
        **kwargs: Passed to OCRFactory.create().

    Returns:
        Configured OCRProvider singleton.
    """
    global _ocr_provider, _provider_type

    if provider_type is None:
        # Read from settings
        try:
            from app.shared.settings import settings
            provider_type = getattr(settings, "OCR_PROVIDER", "tesseract")
        except Exception:
            provider_type = "tesseract"

    if force_recreate or _ocr_provider is None or _provider_type != provider_type:
        logger.info("Creating OCR provider: type=%s", provider_type)
        _ocr_provider = OCRFactory.create(provider_type, **kwargs)
        _provider_type = provider_type

    return _ocr_provider


def reset_ocr_provider() -> None:
    """Reset the OCR provider singleton (useful for testing)."""
    global _ocr_provider, _provider_type
    _ocr_provider = None
    _provider_type = None
