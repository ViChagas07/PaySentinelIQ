from pathlib import Path

import pytest

from app.core.contracts.pipeline_context import PipelineContext
from app.services.extraction.prelude import run_ocr_prelude
from app.services.ocr.base import OCRPageResult, OCRResult
from app.shared.settings import Settings


class FakeOCRProvider:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.paths: list[str] = []

    async def extract_text(self, file_path: str) -> OCRResult:
        self.paths.append(file_path)
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def _settings(*, enabled=True) -> Settings:
    return Settings(_env_file=None, ENABLE_OCR=enabled)


def _context(mime_type="application/pdf") -> PipelineContext:
    return PipelineContext(
        file_bytes=b"%PDF-1.7 fake",
        filename="doc.pdf",
        mime_type=mime_type,
        document_type="boleto",
    )


@pytest.mark.asyncio
async def test_ocr_prelude_success(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(enabled=True),
    )
    provider = FakeOCRProvider(
        result=OCRResult(
            text="A" * 30,
            pages=[OCRPageResult(page_number=1, text="A" * 30, confidence=0.9)],
            confidence=0.9,
            provider="fake",
            processing_time_seconds=0.8,
            metadata={"native_pages": "0", "ocr_pages": "1"},
        )
    )
    ctx = _context()

    await run_ocr_prelude(ctx, provider=provider)

    assert ctx.extracted_text == "A" * 30
    assert ctx.extraction_method == "fake"
    assert ctx.page_count == 1
    assert ctx.ocr_confidence == 90.0
    assert ctx.metadata["ocr_prelude"] is True
    assert ctx.metadata["ocr"] == {
        "status": "completed",
        "provider": "fake",
        "confidence": 90.0,
        "page_count": 1,
        "duration_s": 0.8,
        "native_pages": "0",
        "ocr_pages": "1",
    }
    assert provider.paths
    assert not Path(provider.paths[0]).exists()


@pytest.mark.asyncio
async def test_ocr_prelude_failure_is_non_fatal(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(enabled=True),
    )
    provider = FakeOCRProvider(error=RuntimeError("offline"))
    ctx = _context()

    await run_ocr_prelude(ctx, provider=provider)

    assert ctx.metadata["ocr"] == {
        "status": "failed",
        "error": "RuntimeError",
    }
    assert "ocr_prelude" not in ctx.metadata
    assert "ocr_unavailable: RuntimeError" in ctx.warnings
    assert not Path(provider.paths[0]).exists()


@pytest.mark.asyncio
async def test_ocr_prelude_empty_text(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(enabled=True),
    )
    provider = FakeOCRProvider(
        result=OCRResult(
            text="   ",
            confidence=0.9,
            provider="fake",
            processing_time_seconds=0.1,
        )
    )
    ctx = _context()

    await run_ocr_prelude(ctx, provider=provider)

    assert ctx.metadata["ocr"] == {"status": "empty"}
    assert "ocr_prelude" not in ctx.metadata
    assert ctx.warnings
    assert ctx.extracted_text == ""


@pytest.mark.asyncio
async def test_ocr_prelude_skips_unsupported_mime(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(enabled=True),
    )
    provider = FakeOCRProvider()
    ctx = _context(mime_type="text/plain")

    await run_ocr_prelude(ctx, provider=provider)

    assert provider.paths == []
    assert "ocr" not in ctx.metadata


@pytest.mark.asyncio
async def test_ocr_prelude_respects_disabled_flag(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(enabled=False),
    )
    provider = FakeOCRProvider()
    ctx = _context()

    await run_ocr_prelude(ctx, provider=provider)

    assert provider.paths == []
