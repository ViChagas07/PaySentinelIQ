import fitz

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.extract_stage import ExtractStage
from app.shared.settings import Settings

BOLETO_TEXT = """
Beneficiário: ACME SERVIÇOS LTDA
CNPJ: 12.345.678/0001-90
Pagador: JOÃO DA SILVA
Data de Vencimento: 20/01/2026
Valor do Documento: R$ 1.234,56
Nosso Número: 12345678901
Nº do Documento: 98765
Código do Banco: 001
"""


def _settings(*, canonical=True) -> Settings:
    return Settings(
        _env_file=None,
        ENABLE_CANONICAL_EXTRACTION=canonical,
    )


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "boleto", fontsize=12)
    data = document.tobytes()
    document.close()
    return data


def _context(document_type="boleto") -> PipelineContext:
    return PipelineContext(
        file_bytes=_pdf_bytes(),
        filename="doc.pdf",
        mime_type="application/pdf",
        document_type=document_type,
    )


def test_extract_stage_uses_ocr_prelude_and_keeps_metadata(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(canonical=True),
    )

    def fail_robust(*args, **kwargs):
        raise AssertionError("extract_text_robust must not run")

    monkeypatch.setattr(
        "app.services.ocr.pdf_text_extractor.extract_text_robust",
        fail_robust,
    )
    ctx = _context()
    ctx.extracted_text = BOLETO_TEXT
    ctx.extraction_method = "fake_ocr"
    ctx.page_count = 1
    ctx.ocr_confidence = 91.0
    ctx.metadata["ocr"] = {"status": "completed", "provider": "fake_ocr"}
    ctx.metadata["ocr_prelude"] = True

    ExtractStage().execute(ctx)

    assert ctx.extracted_text == BOLETO_TEXT
    assert ctx.extraction_method == "fake_ocr"
    assert ctx.page_count == 1
    assert ctx.ocr_confidence == 91.0
    assert ctx.metadata["ocr_prelude"] is True
    assert ctx.metadata["ocr"]["status"] == "completed"
    assert ctx.metadata["extraction"]["language"]["lang"] == "pt"
    assert ctx.extracted_fields["beneficiario"] == "ACME SERVIÇOS LTDA"
    assert ctx.extracted_fields["valor_nominal"] == 1234.56
    assert ctx.extracted_fields["amount"] == 1234.56
    assert ctx.extracted_fields["due_date"] == "2026-01-20"
    assert ctx.extracted_fields["bank_code"] == "001"
    assert "canonical" in ctx.extracted_fields
    assert ctx.extracted_fields["data_vencimento"] == "20/01/2026"


def test_extract_stage_without_prelude_keeps_legacy_behavior(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(canonical=True),
    )
    monkeypatch.setattr(
        "app.services.ocr.pdf_text_extractor.extract_text_robust",
        lambda *args, **kwargs: {
            "text": BOLETO_TEXT,
            "method": "native_text",
            "pages": 1,
        },
    )
    ctx = _context()

    ExtractStage().execute(ctx)

    assert ctx.extracted_text == BOLETO_TEXT
    assert ctx.extraction_method == "native_text"
    assert ctx.page_count == 1
    assert ctx.extracted_fields["cnpj"] == "12.345.678/0001-90"
    assert ctx.extracted_fields["beneficiario"] == "ACME SERVIÇOS LTDA"
    assert ctx.extracted_fields["valor_nominal"] == 1234.56


def test_extract_stage_infers_unknown_document_type(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(canonical=True),
    )
    monkeypatch.setattr(
        "app.services.ocr.pdf_text_extractor.extract_text_robust",
        lambda *args, **kwargs: {
            "text": BOLETO_TEXT,
            "method": "native_text",
            "pages": 1,
        },
    )
    ctx = _context(document_type="unknown")

    ExtractStage().execute(ctx)

    assert ctx.document_type == "unknown"
    assert ctx.metadata["extraction"]["document_type_inferred"] == "boleto"
    assert ctx.extracted_fields["valor_nominal"] == 1234.56


def test_extract_stage_canonical_failure_is_non_fatal(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(canonical=True),
    )
    monkeypatch.setattr(
        "app.services.ocr.pdf_text_extractor.extract_text_robust",
        lambda *args, **kwargs: {
            "text": BOLETO_TEXT,
            "method": "native_text",
            "pages": 1,
        },
    )

    def fail(*args, **kwargs):
        raise RuntimeError("canonical exploded")

    monkeypatch.setattr(
        "app.services.extraction.boleto_extractor.extract_boleto_fields",
        fail,
    )
    ctx = _context()

    ExtractStage().execute(ctx)

    assert any("Canonical extraction failed" in w for w in ctx.warnings)
    assert ctx.extracted_fields["cnpj"] == "12.345.678/0001-90"
    assert "canonical" not in ctx.extracted_fields


def test_extract_stage_skips_canonical_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(
        "app.shared.settings.get_settings",
        lambda: _settings(canonical=False),
    )
    monkeypatch.setattr(
        "app.services.ocr.pdf_text_extractor.extract_text_robust",
        lambda *args, **kwargs: {
            "text": BOLETO_TEXT,
            "method": "native_text",
            "pages": 1,
        },
    )
    ctx = _context()

    ExtractStage().execute(ctx)

    assert ctx.extracted_fields["cnpj"] == "12.345.678/0001-90"
    assert "canonical" not in ctx.extracted_fields
    assert "extraction" not in ctx.metadata


