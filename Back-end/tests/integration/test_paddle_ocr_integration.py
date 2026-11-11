import difflib
import io
import time
from pathlib import Path

import fitz
import pytest
from PIL import Image, ImageDraw, ImageFont

pytest.importorskip("torch", exc_type=ImportError)
pytest.importorskip("paddleocr", exc_type=ImportError)

from app.services.ocr.paddle_provider import PaddleOCRProvider

pytestmark = pytest.mark.ocr

PHRASES = [
    "Português coração ação R$ 1.234,56",
    "Español niño mañana ¿qué tal?",
    "English total 1,234.56",
]


def _font() -> ImageFont.FreeTypeFont:
    candidates = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), 34)
    pytest.skip("No TrueType font available for OCR fixture")


def _make_image(path: Path) -> None:
    image = Image.new("RGB", (1500, 600), "white")
    draw = ImageDraw.Draw(image)
    font = _font()
    y = 60
    for phrase in PHRASES:
        draw.text((60, y), phrase, fill="black", font=font)
        y += 120
    image.save(path)


def _make_scanned_pdf(image_path: Path, pdf_path: Path) -> None:
    image = Image.open(image_path)
    image_bytes = io.BytesIO()
    image.save(image_bytes, format="PNG")
    document = fitz.open()
    page = document.new_page(width=image.width, height=image.height)
    page.insert_image(
        fitz.Rect(0, 0, image.width, image.height),
        stream=image_bytes.getvalue(),
    )
    document.save(str(pdf_path))
    document.close()


def _best_ratio(expected: str, actual: str) -> float:
    expected_norm = " ".join(expected.lower().split())
    candidates = [
        " ".join(line.lower().split())
        for line in actual.splitlines()
        if line.strip()
    ]
    candidates.append(" ".join(actual.lower().split()))
    return max(
        difflib.SequenceMatcher(None, expected_norm, candidate).ratio()
        for candidate in candidates
    )


@pytest.mark.asyncio
async def test_paddle_image_and_scanned_pdf_accuracy(tmp_path):
    image_path = tmp_path / "phrases.png"
    pdf_path = tmp_path / "phrases.pdf"
    _make_image(image_path)
    _make_scanned_pdf(image_path, pdf_path)

    provider = PaddleOCRProvider(language="latin", dpi=300, max_pages=10)

    started = time.perf_counter()
    image_result = await provider.extract_text(str(image_path))
    image_seconds = time.perf_counter() - started

    started = time.perf_counter()
    pdf_result = await provider.extract_text(str(pdf_path))
    pdf_seconds = time.perf_counter() - started

    for label, result in (
        ("image", image_result),
        ("scanned_pdf", pdf_result),
    ):
        ratios = {
            phrase: _best_ratio(phrase, result.text)
            for phrase in PHRASES
        }
        print(f"\n{label} ratios: {ratios}")
        print(f"{label} confidence: {result.confidence}")
        assert ratios, "OCR returned no text"
        for phrase, ratio in ratios.items():
            assert ratio >= 0.9, f"{label} phrase below threshold: {phrase}={ratio}"

    print(f"\nimage_seconds={image_seconds:.3f}")
    print(f"scanned_pdf_seconds={pdf_seconds:.3f}")
    assert image_result.page_count == 1
    assert pdf_result.page_count == 1
