from datetime import date
from decimal import Decimal

from app.services.validation.febraban import (
    decode_linha_digitavel,
    validate_boleto,
)
from tests.unit._validation_helpers import build_linha_digitavel

TODAY = date(2025, 2, 22)


def _line(**kwargs) -> str:
    return build_linha_digitavel(factor=9999, value_cents=123456, **kwargs)


def _validate(line, **kwargs):
    decoded = decode_linha_digitavel(line, today=TODAY)
    return validate_boleto(
        linha_digitavel=line,
        valor_nominal=kwargs.pop("valor_nominal", Decimal("1234.56")),
        data_vencimento=kwargs.pop("data_vencimento", date(2025, 2, 21)),
        codigo_barras=kwargs.pop(
            "codigo_barras",
            decoded.get("codigo_barras"),
        ),
        codigo_banco=kwargs.pop("codigo_banco", "001"),
        text=kwargs.pop("text", "Banco: 001"),
        today=TODAY,
        **kwargs,
    )


def test_valid_line_and_field_general_dvs():
    line = _line()
    decoded = decode_linha_digitavel(line, today=TODAY)

    assert len(line) == 47
    assert decoded["status"] == "ok"
    assert all(decoded["campo_dvs_validos"].values())
    assert decoded["dv_geral_valido"] is True
    assert decoded["banco"] == "001"
    assert decoded["moeda"] == "9"
    assert decoded["valor"] == "1234.56"
    assert decoded["vencimento"] == "2025-02-21"


def test_field_dv_is_not_an_evidence():
    line = _line()
    bad_field = line[:9] + str((int(line[9]) + 1) % 10) + line[10:]

    evidences, decoded, _skipped = _validate(bad_field)

    assert decoded["campo_dvs_validos"]["campo1"] is False
    assert decoded["dv_geral_valido"] is True
    assert all(evidence.code != "CAMPO_DV_INVALID" for evidence in evidences)
    assert evidences == []


def test_general_dv_invalid_is_critical():
    line = _line()
    bad = line[:32] + str((int(line[32]) + 1) % 10) + line[33:]

    evidences, decoded, _ = _validate(bad)

    assert decoded["dv_geral_valido"] is False
    assert [e.code for e in evidences] == ["BOLETO_GENERAL_DV_INVALID"]
    assert evidences[0].severity.value == "critical"


def test_currency_code_is_checked():
    line = _line(currency="0")

    evidences, decoded, _ = _validate(line)

    assert decoded["moeda"] == "0"
    assert "BOLETO_CURRENCY_CODE_INVALID" in {e.code for e in evidences}


def test_amount_due_date_and_bank_mismatches():
    line = _line()

    amount_evidences, _, _ = _validate(
        line,
        valor_nominal=Decimal("1300.00"),
    )
    assert "BOLETO_AMOUNT_MISMATCH" in {e.code for e in amount_evidences}

    date_evidences, _, _ = _validate(
        line,
        data_vencimento=date(2025, 2, 20),
    )
    assert "BOLETO_DUE_DATE_MISMATCH" in {e.code for e in date_evidences}

    bank_evidences, _, _ = _validate(line, codigo_banco="341")
    assert "BOLETO_BANK_MISMATCH" in {e.code for e in bank_evidences}


def test_barcode_mismatch_and_consistent_case():
    line = _line()
    decoded = decode_linha_digitavel(line, today=TODAY)
    wrong_barcode = "9" * 44

    evidences, _, _ = _validate(
        line,
        codigo_barras=wrong_barcode,
    )
    assert "BOLETO_BARCODE_MISMATCH" in {e.code for e in evidences}

    clean, decoded, skipped = _validate(line)
    assert clean == []
    assert decoded["comparisons"]["valor"]["match"] is True
    assert decoded["comparisons"]["vencimento"]["match"] is True
    assert decoded["comparisons"]["banco"]["match"] is True
    assert skipped == []


def test_factor_decoding_values():
    def factor_line(factor: int) -> str:
        return build_linha_digitavel(
            factor=factor,
            value_cents=123456,
        )

    assert decode_linha_digitavel(factor_line(9999), today=TODAY)["vencimento"] == "2025-02-21"
    assert decode_linha_digitavel(factor_line(1000), today=TODAY)["vencimento"] == "2025-02-22"
    assert decode_linha_digitavel(factor_line(1001), today=TODAY)["vencimento"] == "2025-02-23"
    assert decode_linha_digitavel(factor_line(0), today=TODAY)["status_fator"] == "sem_vencimento"
    assert decode_linha_digitavel(factor_line(500), today=TODAY)["status_fator"] == "fora_da_janela"
    assert decode_linha_digitavel(factor_line(9586), today=TODAY)["vencimento"] == "2024-01-05"


def test_factor_outside_window_is_low_evidence():
    line = build_linha_digitavel(factor=500, value_cents=123456)

    evidences, decoded, _ = _validate(line, data_vencimento=None)

    assert decoded["status_fator"] == "fora_da_janela"
    assert [e.code for e in evidences] == ["BOLETO_DUE_DATE_UNRESOLVABLE"]
    assert evidences[0].severity.value == "low"


def test_arrecadacao_and_invalid_lengths():
    arrecadacao = "8" + "1" * 47

    evidences, decoded, _ = validate_boleto(
        linha_digitavel=arrecadacao,
        valor_nominal=None,
        data_vencimento=None,
        codigo_barras=None,
        codigo_banco=None,
        text="",
        today=TODAY,
    )
    assert decoded["status"] == "arrecadacao"
    assert [e.code for e in evidences] == ["BOLETO_ARRECADACAO_UNSUPPORTED"]
    assert evidences[0].severity.value == "info"

    evidences, decoded, skipped = validate_boleto(
        linha_digitavel="123",
        valor_nominal=None,
        data_vencimento=None,
        codigo_barras=None,
        codigo_banco=None,
        text="",
        today=TODAY,
    )
    assert evidences == []
    assert decoded["status"] == "formato_invalido"
    assert skipped == ["linha_formato_invalido"]
