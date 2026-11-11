import importlib.util
import subprocess
import sys
from pathlib import Path

import fitz
import pytest
from PIL import Image

from app.services.ocr import paddle_provider
from app.services.ocr.exceptions import OCRProcessingException
from app.services.ocr.paddle_provider import (
    PaddleOCRProvider,
    _parse_v2_result,
    _parse_v3_result,
)


def _write_pdf(path: Path, pages: int) -> None:
    document = fitz.open()
    for _ in range(pages):
        document.new_page()
    document.save(str(path))
    document.close()


def _write_image(path: Path) -> None:
    Image.new("RGB", (100, 50), "white").save(path)


def test_parse_v2_confidence_scale():
    box = [[0, 0], [1, 0], [1, 1], [0, 1]]
    raw = [
        [
            [box, ("Linha um", 0.95)],
            [box, ("Linha dois", 0.85)],
        ]
    ]

    text, confidence = _parse_v2_result(raw)

    assert text == "Linha um\nLinha dois"
    assert confidence == pytest.approx(0.9)
    assert 0.0 <= confidence <= 1.0


def test_parse_v3_confidence_scale():
    raw = [
        {
            "res": {
                "rec_texts": ["Português", "Español"],
                "rec_scores": [0.9, 0.8],
            }
        }
    ]

    text, confidence = _parse_v3_result(raw)

    assert text == "Português\nEspañol"
    assert confidence == pytest.approx(0.85)
    assert 0.0 <= confidence <= 1.0


@pytest.mark.asyncio
async def test_paddle_page_limit_raises_before_engine(tmp_path):
    pdf_path = tmp_path / "many.pdf"
    _write_pdf(pdf_path, 11)
    provider = PaddleOCRProvider(max_pages=10)

    with pytest.raises(OCRProcessingException, match="OCR_MAX_PAGES"):
        await provider.extract_text(str(pdf_path))


@pytest.mark.asyncio
async def test_paddle_image_uses_engine_and_confidence(tmp_path, monkeypatch):
    image_path = tmp_path / "image.png"
    _write_image(image_path)
    box = [[0, 0], [1, 0], [1, 1], [0, 1]]

    class FakeEngine:
        def ocr(self, image, cls=True):
            return [
                [
                    [box, ("Linha um", 0.9)],
                    [box, ("Linha dois", 0.8)],
                ]
            ]

    monkeypatch.setattr(
        paddle_provider,
        "_get_engine",
        lambda language: (FakeEngine(), "2.10.0"),
    )
    provider = PaddleOCRProvider(language="latin", dpi=300, max_pages=10)

    result = await provider.extract_text(str(image_path))

    assert result.provider == "paddleocr"
    assert result.text == "Linha um\nLinha dois"
    assert result.confidence == pytest.approx(0.85)
    assert result.page_count == 1
    assert result.pages[0].width == 100
    assert result.pages[0].height == 50


@pytest.mark.asyncio
async def test_paddle_health_check_false_without_library(monkeypatch):
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name):
        if name in ("paddleocr", "paddle"):
            return None
        return real_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    provider = PaddleOCRProvider()

    assert await provider.health_check() is False


@pytest.mark.asyncio
async def test_paddle_health_check_true_when_available(monkeypatch):
    monkeypatch.setattr(
        importlib.util,
        "find_spec",
        lambda name: object() if name in ("paddleocr", "paddle") else None,
    )
    provider = PaddleOCRProvider()

    assert await provider.health_check() is True


@pytest.mark.asyncio
async def test_paddle_extract_raises_when_library_missing(
    tmp_path,
    monkeypatch,
):
    image_path = tmp_path / "image.png"
    _write_image(image_path)
    real_find_spec = importlib.util.find_spec

    def fake_find_spec(name):
        if name == "paddleocr":
            return None
        return real_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
    provider = PaddleOCRProvider()

    with pytest.raises(OCRProcessingException, match="not installed"):
        await provider.extract_text(str(image_path))


def test_paddle_get_info_contains_version_and_language():
    provider = PaddleOCRProvider(language="latin", dpi=300, max_pages=10)

    info = provider.get_info()

    assert info["provider"] == "paddleocr"
    assert info["language"] == "latin"
    assert "paddleocr_version" in info
    assert "paddle_version" in info
    assert "orientation" in info
    assert "unwarping" in info


def test_paddle_module_import_is_lazy():
    backend_root = Path(__file__).resolve().parents[2]
    code = (
        "import sys; "
        "import app.services.ocr.paddle_provider; "
        "print('paddleocr' in sys.modules, 'paddle' in sys.modules)"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=backend_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "False False"
