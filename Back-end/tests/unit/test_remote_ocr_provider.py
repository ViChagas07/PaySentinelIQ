from pathlib import Path

import httpx
import pytest

from app.services.ocr.exceptions import OCRProcessingException
from app.services.ocr.factory import OCRFactory
from app.services.ocr.remote_provider import RemoteOCRProvider
from app.shared.settings import Settings

PAYLOAD = {
    "text": "hello\nworld",
    "pages": [
        {
            "page_number": 1,
            "text": "hello",
            "confidence": 0.9,
            "width": 100,
            "height": 200,
        },
        {
            "page_number": 2,
            "text": "world",
            "confidence": 0.8,
            "width": 100,
            "height": 200,
        },
    ],
    "confidence": 0.85,
    "provider": "paddleocr",
    "processing_time_seconds": 1.25,
    "metadata": {"dpi": 300, "fallback": False},
}


def _write_file(path: Path) -> None:
    path.write_bytes(b"%PDF-1.7 test")


def _provider(handler, api_key=None):
    return RemoteOCRProvider(
        url="http://ocr.test:8010",
        timeout=30,
        api_key=api_key,
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_maps_remote_json(tmp_path):
    file_path = tmp_path / "doc.pdf"
    _write_file(file_path)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=PAYLOAD)

    result = await _provider(handler).extract_text(str(file_path))

    assert result.text == "hello\nworld"
    assert result.provider == "paddleocr"
    assert result.confidence == 0.85
    assert result.page_count == 2
    assert result.pages[0].page_number == 1
    assert result.pages[1].text == "world"
    assert result.pages[1].width == 100
    assert result.processing_time_seconds == 1.25
    assert result.metadata == {"dpi": "300", "fallback": "False"}
    assert str(requests[0].url) == "http://ocr.test:8010/ocr"


@pytest.mark.asyncio
async def test_key_header_only_when_configured(tmp_path):
    file_path = tmp_path / "doc.pdf"
    _write_file(file_path)
    requests = []

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json=PAYLOAD)

    await _provider(handler, api_key="secret").extract_text(str(file_path))
    await _provider(handler, api_key=None).extract_text(str(file_path))

    assert requests[0].headers["X-OCR-Key"] == "secret"
    assert "X-OCR-Key" not in requests[1].headers


@pytest.mark.asyncio
async def test_retries_only_connection_errors(tmp_path):
    file_path = tmp_path / "doc.pdf"
    _write_file(file_path)
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ConnectError("connection refused", request=request)
        return httpx.Response(200, json=PAYLOAD)

    result = await _provider(handler).extract_text(str(file_path))

    assert attempts == 2
    assert result.text == "hello\nworld"


@pytest.mark.asyncio
async def test_does_not_retry_4xx(tmp_path):
    file_path = tmp_path / "doc.pdf"
    _write_file(file_path)
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        return httpx.Response(400, text="bad request")

    with pytest.raises(OCRProcessingException, match="HTTP 400"):
        await _provider(handler).extract_text(str(file_path))

    assert attempts == 1


@pytest.mark.asyncio
async def test_timeout_is_not_retried(tmp_path):
    file_path = tmp_path / "doc.pdf"
    _write_file(file_path)
    attempts = 0

    def handler(request):
        nonlocal attempts
        attempts += 1
        raise httpx.ReadTimeout("read timed out", request=request)

    with pytest.raises(OCRProcessingException, match="timed out"):
        await _provider(handler).extract_text(str(file_path))

    assert attempts == 1


@pytest.mark.asyncio
async def test_health_check_true_and_false():
    def healthy(request):
        return httpx.Response(200, json={"status": "ready"})

    def unhealthy(request):
        return httpx.Response(503, json={"status": "not_ready"})

    assert await _provider(healthy).health_check() is True
    assert await _provider(unhealthy).health_check() is False


@pytest.mark.asyncio
async def test_health_check_without_url_is_false():
    provider = RemoteOCRProvider(url="")

    assert await provider.health_check() is False


def test_factory_remote_and_auto(monkeypatch):
    settings = Settings(
        _env_file=None,
        OCR_SERVICE_URL="http://ocr.test:8010",
        OCR_SERVICE_TIMEOUT=30,
        OCR_SERVICE_API_KEY=None,
    )
    monkeypatch.setattr("app.shared.settings.get_settings", lambda: settings)

    remote = OCRFactory.create("remote")
    auto_remote = OCRFactory.create("auto")

    assert remote.get_info()["primary"] == "remote"
    assert auto_remote.get_info()["primary"] == "remote"

    settings.OCR_SERVICE_URL = ""
    auto_local = OCRFactory.create("auto")

    assert auto_local.get_info()["primary"] == "paddleocr"


def test_factory_remote_get_info():
    provider = RemoteOCRProvider(
        url="http://ocr.test:8010",
        timeout=30,
    )

    info = provider.get_info()

    assert info["provider"] == "remote"
    assert info["url"] == "http://ocr.test:8010"
    assert info["timeout"] == "30"
