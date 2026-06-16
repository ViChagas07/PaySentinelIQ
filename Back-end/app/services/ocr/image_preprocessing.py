# ============================================================
# PaySentinelIQ — Image Preprocessing for OCR
# Improves accuracy via grayscale, contrast, denoising, threshold.
# ============================================================

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageFilter, ImageEnhance, ImageOps
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    logger.warning("Pillow not installed. Image preprocessing disabled.")


def preprocess_image(image: Any) -> Any:
    """Apply preprocessing pipeline to improve OCR accuracy.

    Steps:
    1. Convert to grayscale
    2. Increase contrast (1.5x)
    3. Apply adaptive threshold for binarization
    4. Remove noise (median filter)
    5. Sharpen

    Args:
        image: PIL Image object.

    Returns:
        Preprocessed PIL Image ready for OCR.
    """
    if not HAS_PILLOW:
        return image

    try:
        # Step 1: Grayscale
        if image.mode != "L":
            image = ImageOps.grayscale(image)

        # Step 2: Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.5)

        # Step 3: Adaptive threshold-like binarization
        # PIL doesn't have built-in adaptive threshold, so we use a point operation
        # that maps mid-tones more aggressively
        image = image.point(lambda p: 0 if p < 140 else 255 if p > 180 else p)

        # Step 4: Denoise with median filter
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Step 5: Sharpen
        image = image.filter(ImageFilter.SHARPEN)

        return image

    except Exception as e:
        logger.warning(f"Image preprocessing failed, using original: {e}")
        return image


def preprocess_for_document(image: Any) -> Any:
    """Preprocessing optimized for document OCR (invoices, payrolls, bank slips).

    More aggressive threshold and deskew for structured documents.
    """
    if not HAS_PILLOW:
        return image

    try:
        # Grayscale
        if image.mode != "L":
            image = ImageOps.grayscale(image)

        # High contrast for document text
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Aggressive binarization — documents are mostly black text on white
        image = image.point(lambda p: 0 if p < 128 else 255)

        # Denoise
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Auto-deskew using pixel projection (simple approach)
        # For production, consider using a dedicated deskew library
        try:
            image = _auto_deskew(image)
        except Exception:
            pass  # deskew is optional

        return image

    except Exception as e:
        logger.warning(f"Document preprocessing failed, using original: {e}")
        return image


def _auto_deskew(image: Any) -> Any:
    """Simple auto-deskew using moment-based angle detection."""
    import numpy as np

    img_array = np.array(image)
    # Binarize
    binary = img_array < 128
    # Find all non-zero points
    coords = np.column_stack(np.where(binary))
    if len(coords) < 100:
        return image

    # Calculate moments
    moments = {}
    moments["mu11"] = np.sum((coords[:, 0] - coords[:, 0].mean()) * (coords[:, 1] - coords[:, 1].mean()))
    moments["mu02"] = np.sum((coords[:, 1] - coords[:, 1].mean()) ** 2)
    moments["mu20"] = np.sum((coords[:, 0] - coords[:, 0].mean()) ** 2)

    if moments["mu02"] == 0:
        return image

    # Calculate skew angle
    skew = moments["mu11"] / moments["mu02"]
    angle = np.degrees(np.arctan(skew))

    # Only deskew if angle is significant (>0.5 degrees)
    if abs(angle) < 0.5:
        return image

    return image.rotate(angle, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)
