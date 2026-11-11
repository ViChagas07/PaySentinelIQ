from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import main as main_module
from app.engine import OCRServiceError, PageLimitError

RESULT = {
    "text": "hello",
    "pages": [
        {
            "page_number": 1,
            "text": "hello",
            "confidence": 0.9,
            "width": 10,
            "height": 20,
        }
    ],
    "confidence": 0.9,
    "provider": "paddleocr",
    "processing_time_seconds": 0.1,
    "metadata": {"dpi": "300"},
}


class FakeEngine:
    def __init__(self, result=None, error=None, ready=False):
        self.result = result or RESULT
        self.error = error
        self.ready = ready
        self.calls = 0
        self.kwargs = {}

    def is_ready(self):
        return self.ready

    def extract(self, *args, **kwargs):
        self.calls += 1
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.result


def _png_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (10, 20), "white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.fixture
def client(monkeypatch):
    fake = FakeEngine()
    monkeypatch.setattr(main_module, "engine", fake)
    monkeypatch.setattr(main_module.settings, "api_key", None)
    monkeypatch.setattr(main_module.settings, "max_mb", 25.0)
    monkeypatch.setattr(main_module.settings, "max_pages", 10)
    monkeypatch.setattr(main_module.settings, "dpi", 300)
    return TestClient(main_module.app), fake


def test_health_does_not_load_engine(client):
    http_client, fake = client

    response = http_client.get("/health")

    assert response.status_code == 200
    assert fake.calls == 0


def test_ready_reflects_paddle_state(client, monkeypatch):
    http_client, fake = client

    assert http_client.get("/ready").status_code == 503

    fake.ready = True
    assert http_client.get("/ready").status_code == 200


def test_rejects_invalid_magic_bytes(client):
    http_client, fake = client

    response = http_client.post(
        "/ocr",
        files={"file": ("bad.txt", b"not a document", "text/plain")},
    )

    assert response.status_code == 400
    assert fake.calls == 0


def test_rejects_large_file(client, monkeypatch):
    http_client, fake = client
    monkeypatch.setattr(main_module.settings, "max_mb", 0.000001)

    response = http_client.post(
        "/ocr",
        files={"file": ("large.pdf", b"%PDF" + b"x" * 20, "application/pdf")},
    )

    assert response.status_code == 413
    assert fake.calls == 0


def test_page_limit_returns_422(client, monkeypatch):
    http_client, _ = client
    monkeypatch.setattr(
        main_module,
        "engine",
        FakeEngine(error=PageLimitError(11, 10)),
    )

    response = http_client.post(
        "/ocr",
        files={"file": ("doc.pdf", b"%PDF-1.7", "application/pdf")},
    )

    assert response.status_code == 422
    assert "OCR_MAX_PAGES" in response.json()["detail"]


def test_api_key_optional_and_enforced(client, monkeypatch):
    http_client, _ = client
    monkeypatch.setattr(main_module.settings, "api_key", "secret")

    missing = http_client.post(
        "/ocr",
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )
    wrong = http_client.post(
        "/ocr",
        headers={"X-OCR-Key": "wrong"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )
    valid = http_client.post(
        "/ocr",
        headers={"X-OCR-Key": "secret"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert valid.status_code == 200


def test_ocr_returns_expected_json(client):
    http_client, fake = client

    response = http_client.post(
        "/ocr",
        data={"dpi": "300", "max_pages": "10"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "hello"
    assert body["provider"] == "paddleocr"
    assert body["pages"][0]["page_number"] == 1
    assert fake.calls == 1


def test_engine_field_is_forwarded(client):
    http_client, fake = client

    response = http_client.post(
        "/ocr",
        data={"engine": "tesseract"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert fake.kwargs["engine"] == "tesseract"


def test_invalid_engine_returns_422(client):
    http_client, fake = client

    response = http_client.post(
        "/ocr",
        data={"engine": "invalid"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 422
    assert fake.calls == 0


def test_invalid_page_form_returns_422(client):
    http_client, fake = client

    response = http_client.post(
        "/ocr",
        data={"max_pages": "0"},
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 422
    assert fake.calls == 0


def test_engine_error_returns_500(client, monkeypatch):
    http_client, _ = client
    monkeypatch.setattr(
        main_module,
        "engine",
        FakeEngine(error=OCRServiceError("boom")),
    )

    response = http_client.post(
        "/ocr",
        files={"file": ("doc.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 500
