from datetime import date
from decimal import Decimal

from app.core.contracts.pipeline_context import PipelineContext
from app.services.ai.boleto_analyzer import BANCOS_VALIDOS
from app.services.pipeline.stages.validate_stage import (
    ValidateStage,
    _bank_invalid_severity,
)
from app.services.validation.febraban import validate_boleto
from tests.unit._validation_helpers import build_linha_digitavel

REQUIRED_BANKS = {
    "001",
    "003",
    "004",
    "033",
    "041",
    "070",
    "077",
    "085",
    "104",
    "136",
    "197",
    "208",
    "212",
    "218",
    "237",
    "260",
    "290",
    "318",
    "323",
    "336",
    "341",
    "380",
    "422",
    "623",
    "633",
    "655",
    "748",
    "756",
}


def _boleto_context(line: str, text: str, bank: str | None = None):
    fields = {
        "linha_digitavel": line,
        "codigo_banco": bank or line[:3],
        "valor_nominal": Decimal("1234.56"),
        "data_vencimento": date(2027, 1, 20),
    }
    return PipelineContext(
        document_type="boleto",
        extracted_fields=fields,
        extracted_text=text,
    )


def test_required_bank_codes_are_registered():
    assert REQUIRED_BANKS <= BANCOS_VALIDOS


def test_encoded_bank_wins_and_text_fragments_do_not_invalidate():
    line = build_linha_digitavel(bank="003")
    context = _boleto_context(
        line,
        (
            "CNPJ do Beneficiario: 12.345.678/0001-90\n"
            "Valor do Documento: 2068.79\n"
            "Banco: 003-1\n"
            "Linha Digitavel: " + line
        ),
    )

    ValidateStage().execute(context)

    assert "BANCO_INVALIDO" not in {
        evidence.code for evidence in context.evidences
    }


def test_structured_bank_999_is_critical():
    line = build_linha_digitavel(bank="999")
    context = _boleto_context(line, "", bank="999")

    ValidateStage().execute(context)

    severities = {
        evidence.code: evidence.severity.value
        for evidence in context.evidences
    }
    assert severities["BANCO_INVALIDO"] == "critical"


def test_structured_bank_outside_list_is_medium():
    line = build_linha_digitavel(bank="345")
    context = _boleto_context(line, "", bank="345")

    ValidateStage().execute(context)

    severities = {
        evidence.code: evidence.severity.value
        for evidence in context.evidences
    }
    assert severities["BANCO_INVALIDO"] == "medium"


def test_non_numeric_bank_is_high():
    assert _bank_invalid_severity("BANCO_INVALIDO: banco X").value == "high"


def test_b3_style_mismatch_ignores_canonical_bank():
    line = build_linha_digitavel(bank="001")
    evidences, decoded, skipped = validate_boleto(
        linha_digitavel=line,
        valor_nominal=Decimal("1234.56"),
        data_vencimento=date(2027, 1, 20),
        codigo_barras=decoded_barcode(line),
        codigo_banco="001",
        text="Banco: 999-1\nLinha Digitavel: " + line,
        today=date(2026, 11, 11),
    )

    codes = {evidence.code for evidence in evidences}
    assert "BOLETO_BANK_MISMATCH" in codes
    assert decoded["banco"] == "001"
    assert "missing_banco_impresso" not in skipped


def test_no_printed_candidate_skips_mismatch_rule():
    line = build_linha_digitavel(bank="001")
    evidences, _decoded, skipped = validate_boleto(
        linha_digitavel=line,
        valor_nominal=Decimal("1234.56"),
        data_vencimento=date(2027, 1, 20),
        codigo_barras=decoded_barcode(line),
        codigo_banco="001",
        text="",
        today=date(2026, 11, 11),
    )

    assert "BOLETO_BANK_MISMATCH" not in {
        evidence.code for evidence in evidences
    }
    assert "missing_banco_impresso" in skipped


def decoded_barcode(line: str) -> str:
    from app.services.validation.febraban import decode_linha_digitavel

    return str(decode_linha_digitavel(line, today=date(2026, 11, 11))["codigo_barras"])
