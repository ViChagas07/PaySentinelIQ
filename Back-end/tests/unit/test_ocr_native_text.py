from pathlib import Path

import fitz
import pytest
from PIL import Image, ImageDraw

from app.services.ocr.base import OCRPageResult, OCRProvider, OCRResult
from app.services.ocr.exceptions import OCRProcessingException
from app.services.ocr.native_text_provider import NativeTextFirstOCRProvider


class FakeOCRProvider(OCRProvider):
    def __init__(
        self,
        name: str = "fake",
        text: str = "ocr text",
        confidence: float = 0.75,
        fail: bool = False,
    ) -> None:
        self.name = name
        self.text = text
        self.confidence = confidence
        self.fail = fail
        self.calls: list[str] = []

    async def extract_text(self, file_path: str) -> OCRResult:
        self.calls.append(file_path)
        if self.fail:
            raise OCRProcessingException("primary failed")

        return OCRResult(
            text=self.text,
            pages=[
                OCRPageResult(
                    page_number=1,
                    text=self.text,
                    confidence=self.confidence,
                )
            ],
            confidence=self.confidence,
            provider=self.name,
        )

    async def health_check(self) -> bool:
        return not self.fail

    def get_info(self) -> dict[str, str]:
        return {"provider": self.name}


def _write_pdf(path: Path, pages: list[str | None]) -> None:
    document = fitz.open()
    for text in pages:
        page = document.new_page()
        if text:
            page.insert_text((72, 72), text, fontsize=12)
    document.save(str(path))
    document.close()


def _write_image(path: Path) -> None:
    image = Image.new("RGB", (240, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "hello image", fill="black")
    image.save(path)


@pytest.mark.asyncio
async def test_native_text_skips_ocr(tmp_path):
    pdf_path = tmp_path / "native.pdf"
    _write_pdf(pdf_path, ["A" * 60])
    primary = FakeOCRProvider()

    provider = NativeTextFirstOCRProvider(primary=primary, min_native_chars=50)
    result = await provider.extract_text(str(pdf_path))

    assert primary.calls == []
    assert result.provider == "native_text"
    assert result.confidence == 1.0
    assert result.page_count == 1
    assert result.pages[0].text == "A" * 60


@pytest.mark.asyncio
async def test_insufficient_native_text_uses_ocr(tmp_path):
    pdf_path = tmp_path / "short.pdf"
    _write_pdf(pdf_path, ["short"])
    primary = FakeOCRProvider()

    provider = NativeTextFirstOCRProvider(primary=primary, min_native_chars=50)
    result = await provider.extract_text(str(pdf_path))

    assert len(primary.calls) == 1
    assert result.provider == "fake"
    assert result.confidence == 0.75
    assert result.pages[0].text == "ocr text"


@pytest.mark.asyncio
async def test_mixed_document_preserves_page_order(tmp_path):
    pdf_path = tmp_path / "mixed.pdf"
    first_page = "PAGINA UM " * 7
    third_page = "PAGINA TRES " * 6
    _write_pdf(pdf_path, [first_page, None, third_page])
    primary = FakeOCRProvider(text="ocr page", confidence=0.75)

    provider = NativeTextFirstOCRProvider(primary=primary, min_native_chars=50)
    result = await provider.extract_text(str(pdf_path))

    assert len(primary.calls) == 1
    assert result.page_count == 3
    assert " ".join(result.pages[0].text.split()) == " ".join(
        first_page.split()
    )
    assert result.pages[1].text == "ocr page"
    assert " ".join(result.pages[2].text.split()) == " ".join(
        third_page.split()
    )
    assert result.pages[0].page_number == 1
    assert result.pages[1].page_number == 2
    assert result.pages[2].page_number == 3
    assert result.provider == "native_text+fake"
    assert result.confidence == pytest.approx((1.0 + 0.75 + 1.0) / 3, rel=1e-3)
    assert result.metadata["native_pages"] == "2"
    assert result.metadata["ocr_pages"] == "1"


@pytest.mark.asyncio
async def test_page_limit_raises_explicitly(tmp_path):
    pdf_path = tmp_path / "many.pdf"
    _write_pdf(pdf_path, ["X" * 10] * 11)
    primary = FakeOCRProvider()

    provider = NativeTextFirstOCRProvider(
        primary=primary,
        max_pages=10,
        min_native_chars=50,
    )

    with pytest.raises(OCRProcessingException, match="OCR_MAX_PAGES"):
        await provider.extract_text(str(pdf_path))

    assert primary.calls == []


@pytest.mark.asyncio
async def test_auto_fallback_uses_secondary_provider(tmp_path):
    pdf_path = tmp_path / "fallback.pdf"
    _write_pdf(pdf_path, [None])
    primary = FakeOCRProvider(name="primary", fail=True)
    fallback = FakeOCRProvider(
        name="fallback",
        text="fallback text",
        confidence=0.6,
    )

    provider = NativeTextFirstOCRProvider(
        primary=primary,
        fallback=fallback,
        min_native_chars=50,
    )
    result = await provider.extract_text(str(pdf_path))

    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1
    assert result.provider == "fallback"
    assert result.pages[0].text == "fallback text"
    assert result.confidence == 0.6


def test_factory_registers_paddle_and_auto():
    from app.services.ocr.factory import OCRFactory
    from app.services.ocr.native_text_provider import NativeTextFirstOCRProvider

    assert isinstance(
        OCRFactory.create("paddleocr"),
        NativeTextFirstOCRProvider,
    )
    assert isinstance(
        OCRFactory.create("auto"),
        NativeTextFirstOCRProvider,
    )


@pytest.mark.asyncio
async def test_image_goes_directly_to_ocr(tmp_path):
    image_path = tmp_path / "image.png"
    _write_image(image_path)
    primary = FakeOCRProvider(name="paddleocr", text="image text", confidence=0.9)

    provider = NativeTextFirstOCRProvider(primary=primary)
    result = await provider.extract_text(str(image_path))

    assert len(primary.calls) == 1
    assert result.provider == "paddleocr"
    assert result.pages[0].text == "image text"
    assert result.metadata["native_text"] == "false"
