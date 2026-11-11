from datetime import date
from decimal import Decimal

from app.services.ai.risk_analyzer import RiskAnalyzer
from app.services.extraction.adapter import to_pipeline_fields
from app.services.extraction.fields import CanonicalFields, ExtractedValue
from app.services.extraction.language import LanguageGuess


def _value(value):
    return ExtractedValue(
        value=value,
        raw=str(value),
        line_no=1,
        method="regex",
        confidence=0.9,
    )


def test_risk_analyzer_receives_amount_due_date_and_bank_code():
    fields = CanonicalFields(
        language=LanguageGuess(
            lang="pt",
            scores={"pt": 1.0, "es": 0.0, "en": 0.0},
            confidence=1.0,
        ),
        valor_nominal=_value(Decimal("1000.00")),
        data_vencimento=_value(date(2020, 1, 1)),
        codigo_banco=_value("999"),
        cnpj=_value("12.345.678/0001-90"),
    )
    mapped = to_pipeline_fields(fields, "boleto")
    assert mapped["due_date"] == "2020-01-01"
    risk_ctx = {
        "document_type": "boleto",
        **mapped,
        "ocr_confidence": 90.0,
        "bank_valid": False,
    }

    assessment = RiskAnalyzer().analyze(risk_ctx)
    codes = {flag.code for flag in assessment.flags}

    assert "BOLETO_ROUND_AMOUNT" in codes
    assert "BANK_CODE_INVALID" in codes
    assert "DATE_PARSE_ERROR" in codes
    assert "OCR_VERY_LOW" not in codes
