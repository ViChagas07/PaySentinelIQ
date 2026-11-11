import subprocess
import sys
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from PIL import Image

from app.engine import OCREngine, OCRServiceError, PageLimitError


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (20, 30), "white").save(buffer, format="PNG")
    return buffer.getvalue()


def _pdf_bytes(pages: int) -> bytes:
    document = fitz.open()
    for _ in range(pages):
        document.new_page()
    data = document.tobytes()
    document.close()
    return data


def test_page_limit_is_explicit():
    engine = OCREngine(max_pages=10)

    with pytest.raises(PageLimitError, match="OCR_MAX_PAGES"):
        engine.extract(_pdf_bytes(11), "doc.pdf", max_pages=10)


def test_force_fallback_uses_tesseract(monkeypatch):
    engine = OCREngine(force_fallback=True)
    called = {"paddle": 0, "tesseract": 0}

    def fake_paddle(pages):
        called["paddle"] += 1
        return []

    def fake_tesseract(pages):
        called["tesseract"] += 1
        return [
            {
                "page_number": 1,
                "text": "fallback",
                "confidence": 0.8,
                "width": 20,
                "height": 30,
            }
        ]

    monkeypatch.setattr(engine, "_run_paddle", fake_paddle)
    monkeypatch.setattr(engine, "_run_tesseract", fake_tesseract)

    result = engine.extract(_png_bytes(), "doc.png")

    assert called == {"paddle": 0, "tesseract": 1}
    assert result["provider"] == "tesseract"
    assert result["text"] == "fallback"
    assert result["metadata"]["fallback"] == "true"


def test_paddle_failure_falls_back(monkeypatch):
    engine = OCREngine()
    called = {"tesseract": 0}

    def failing_paddle(pages):
        raise OCRServiceError("paddle failed")

    def fake_tesseract(pages):
        called["tesseract"] += 1
        return [
            {
                "page_number": 1,
                "text": "recovered",
                "confidence": 0.7,
                "width": 20,
                "height": 30,
            }
        ]

    monkeypatch.setattr(engine, "_run_paddle", failing_paddle)
    monkeypatch.setattr(engine, "_run_tesseract", fake_tesseract)

    result = engine.extract(_png_bytes(), "doc.png")

    assert called["tesseract"] == 1
    assert result["provider"] == "tesseract"
    assert result["text"] == "recovered"


def test_ready_is_false_before_paddle_init():
    engine = OCREngine()

    assert engine.is_ready() is False
    assert engine.paddle_ready is False


def test_engine_import_is_lazy():
    service_root = Path(__file__).resolve().parents[1]
    code = (
        "import sys; "
        "import app.engine; "
        "print('paddle' in sys.modules, 'pytesseract' in sys.modules)"
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=service_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout.strip() == "False False"
