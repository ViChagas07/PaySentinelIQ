import fitz

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.extract_stage import ExtractStage
from app.services.pipeline.stages.risk_stage import RiskStage


def _native_pdf(*lines: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    y = 72
    for line in lines:
        page.insert_text((72, y), line, fontsize=12)
        y += 20
    data = document.tobytes()
    document.close()
    return data


def _context(file_bytes: bytes, mime_type: str = "application/pdf") -> PipelineContext:
    return PipelineContext(
        file_bytes=file_bytes,
        filename="doc.pdf",
        mime_type=mime_type,
        document_type="boleto",
    )


def test_native_pdf_marks_ocr_not_needed_and_skips_very_low():
    ctx = _context(
        _native_pdf(
            "Beneficiario: ACME SERVICOS LTDA",
            "CNPJ: 12.345.678/0001-90",
            "Data de Vencimento: 20/01/2027",
            "Valor do Documento: R$ 1.234,56",
        )
    )

    ExtractStage().execute(ctx)
    RiskStage().execute(ctx)

    assert ctx.metadata["ocr"] == {
        "status": "not_needed",
        "provider": "native_text",
    }
    assert "OCR_VERY_LOW" not in {evidence.code for evidence in ctx.evidences}


def test_image_ocr_confidence_40_still_generates_very_low():
    ctx = _context(b"\x89PNG\r\n\x1a\nfake", mime_type="image/png")
    ctx.extracted_text = "Boleto " * 20
    ctx.extraction_method = "tesseract"
    ctx.ocr_confidence = 40.0
    ctx.metadata["ocr"] = {"status": "completed", "provider": "tesseract"}

    ExtractStage().execute(ctx)
    RiskStage().execute(ctx)

    assert ctx.metadata["ocr"]["status"] == "completed"
    assert "OCR_VERY_LOW" in {evidence.code for evidence in ctx.evidences}


def test_existing_ocr_block_is_not_overwritten():
    ctx = _context(_native_pdf("Boleto nativo com texto suficiente " * 2))
    ctx.extracted_text = "Boleto nativo com texto suficiente " * 2
    ctx.extraction_method = "native_text"
    ctx.metadata["ocr"] = {"status": "completed", "provider": "native_text"}

    ExtractStage().execute(ctx)

    assert ctx.metadata["ocr"] == {
        "status": "completed",
        "provider": "native_text",
    }
