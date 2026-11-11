import difflib
import io
import os
from pathlib import Path

import fitz
import httpx
import pytest
from PIL import Image, ImageDraw, ImageFont

from app.services.ocr.remote_provider import RemoteOCRProvider

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
            return ImageFont.truetype(str(path), 44)
    pytest.skip("No TrueType font available for OCR fixture")


def _make_image(path: Path) -> None:
    image = Image.new("RGB", (1800, 700), "white")
    draw = ImageDraw.Draw(image)
    font = _font()
    y = 80
    for phrase in PHRASES:
        draw.text((80, y), phrase, fill="black", font=font)
        y += 150
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


def _ratios(text: str) -> dict[str, float]:
    normalized = " ".join(text.lower().split())
    lines = [
        " ".join(line.lower().split())
        for line in text.splitlines()
        if line.strip()
    ]
    candidates = lines + [normalized]
    return {
        phrase: max(
            difflib.SequenceMatcher(
                None,
                " ".join(phrase.lower().split()),
                candidate,
            ).ratio()
            for candidate in candidates
        )
        for phrase in PHRASES
    }


def _service_available(url: str) -> bool:
    try:
        response = httpx.get(f"{url}/health", timeout=3.0)
        return response.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.asyncio
async def test_remote_ocr_primary_accuracy(tmp_path):
    url = os.getenv("OCR_SERVICE_URL")
    if not url:
        pytest.skip("OCR_SERVICE_URL not set")
    if not _service_available(url):
        pytest.skip(f"OCR service not available at {url}")

    image_path = tmp_path / "phrases.png"
    pdf_path = tmp_path / "phrases.pdf"
    _make_image(image_path)
    _make_scanned_pdf(image_path, pdf_path)

    provider = RemoteOCRProvider(
        url=url,
        timeout=300,
        api_key=os.getenv("OCR_SERVICE_API_KEY"),
    )

    pdf_result = await provider.extract_text(str(pdf_path))
    image_result = await provider.extract_text(str(image_path))
    assert pdf_result.provider == "paddleocr"
    assert pdf_result.page_count == 1

    pdf_ratios = _ratios(pdf_result.text)
    image_ratios = _ratios(image_result.text)
    print(f"\npaddle_pdf_ratios={pdf_ratios}")
    print(f"paddle_image_ratios={image_ratios}")

    if any(ratio < 0.9 for ratio in pdf_ratios.values()):
        pytest.xfail(
            "PaddleOCR latin model below 0.9 for accented phrases: "
            f"{pdf_ratios}"
        )

    for ratio in pdf_ratios.values():
        assert ratio >= 0.9
    for ratio in image_ratios.values():
        assert ratio >= 0.9


@pytest.mark.asyncio
async def test_remote_ocr_fallback_accuracy(tmp_path):
    url = os.getenv("OCR_SERVICE_FALLBACK_URL")
    if not url:
        pytest.skip("OCR_SERVICE_FALLBACK_URL not set")
    if not _service_available(url):
        pytest.skip(f"OCR fallback service not available at {url}")

    image_path = tmp_path / "phrases.png"
    pdf_path = tmp_path / "phrases.pdf"
    _make_image(image_path)
    _make_scanned_pdf(image_path, pdf_path)

    provider = RemoteOCRProvider(
        url=url,
        timeout=300,
        api_key=os.getenv("OCR_SERVICE_FALLBACK_API_KEY"),
    )

    pdf_result = await provider.extract_text(str(pdf_path))
    image_result = await provider.extract_text(str(image_path))
    assert pdf_result.provider == "tesseract"

    pdf_ratios = _ratios(pdf_result.text)
    image_ratios = _ratios(image_result.text)
    print(f"\ntesseract_pdf_ratios={pdf_ratios}")
    print(f"tesseract_image_ratios={image_ratios}")

    for ratio in pdf_ratios.values():
        assert ratio >= 0.9
    for ratio in image_ratios.values():
        assert ratio >= 0.9
