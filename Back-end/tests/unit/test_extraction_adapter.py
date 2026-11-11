import json
from datetime import date
from decimal import Decimal

from app.services.extraction.adapter import to_pipeline_fields
from app.services.extraction.fields import CanonicalFields, ExtractedValue
from app.services.extraction.language import LanguageGuess


def _value(value, confidence=0.9):
    return ExtractedValue(
        value=value,
        raw=str(value),
        line_no=1,
        method="regex",
        confidence=confidence,
    )


def _lang():
    return LanguageGuess(
        lang="pt",
        scores={"pt": 3.0, "es": 0.0, "en": 0.0},
        confidence=1.0,
    )


def _boleto_fields():
    return CanonicalFields(
        language=_lang(),
        valor_nominal=_value(Decimal("1234.56")),
        valor_cobrado=_value(Decimal("1234.56")),
        data_vencimento=_value(date(2026, 1, 20)),
        data_documento=_value(date(2026, 1, 15)),
        beneficiario=_value("ACME SERVIÇOS LTDA"),
        pagador=_value("JOÃO DA SILVA", confidence=0.4),
        codigo_banco=_value("001"),
        linha_digitavel=_value("00190000090123456700812345678901234560000123456"),
        codigo_barras=_value("12345678901234567890123456789012345678901234"),
        cnpj=_value("12.345.678/0001-90"),
        cpf=_value("123.456.789-09"),
        nosso_numero=_value("12345678901"),
        numero_documento=_value("98765"),
        carteira=_value("17"),
        local_pagamento=_value("PAGÁVEL EM QUALQUER BANCO"),
        agencia_codigo_beneficiario=_value("1234/123456-7"),
        multa=_value("2,00%"),
        juros=_value("1,00% ao mês"),
        warnings=["valor_nominal: ambiguous amount"],
        corrections=["text: O->0@3"],
    )


def test_boleto_adapter_types_and_mapping():
    output = to_pipeline_fields(_boleto_fields(), "boleto")

    assert output["valor_nominal"] == 1234.56
    assert output["amount"] == 1234.56
    assert output["valor_cobrado"] == 1234.56
    assert output["data_vencimento"] == "20/01/2026"
    assert output["due_date"] == "2026-01-20"
    assert output["data_documento"] == "15/01/2026"
    assert output["issue_date"] == "2026-01-15"
    assert output["beneficiario"] == "ACME SERVIÇOS LTDA"
    assert output["beneficiary_name"] == "ACME SERVIÇOS LTDA"
    assert output["codigo_banco"] == "001"
    assert output["bank_code"] == "001"
    assert output["linha_digitavel"] == "00190000090123456700812345678901234560000123456"
    assert output["codigo_barras"] == "12345678901234567890123456789012345678901234"
    assert output["cnpj"] == "12.345.678/0001-90"
    assert output["cpf"] == "123.456.789-09"

    assert "salario_bruto" not in output
    assert "salario_liquido" not in output
    assert "cnpj_valid" not in output
    assert "cnpj_active" not in output
    assert "checksum_valid" not in output
    assert "bank_valid" not in output

    canonical = output["canonical"]
    assert canonical["beneficiario"]["value"] == "ACME SERVIÇOS LTDA"
    assert canonical["valor_nominal"]["value"] == "1234.56"
    assert canonical["data_vencimento"]["value"] == "2026-01-20"
    assert canonical["language"]["lang"] == "pt"
    assert canonical["warnings"]
    assert canonical["corrections"]
    json.dumps(output)


def test_low_confidence_does_not_override_top_level():
    output = to_pipeline_fields(_boleto_fields(), "boleto")

    assert "pagador" not in output
    assert output["canonical"]["pagador"]["confidence"] == 0.4


def test_payslip_adapter_types_and_mapping():
    fields = CanonicalFields(
        language=_lang(),
        razao_social=_value("ACME S.A."),
        nome_funcionario=_value("Maria Silva"),
        cargo=_value("Analista"),
        cbo=_value("411005"),
        cpf=_value("123.456.789-09"),
        cnpj=_value("12.345.678/0001-90"),
        periodo=_value("01/2026"),
        data_admissao=_value(date(2020, 3, 15)),
        salario_base=_value(Decimal("3000.00")),
        salario_bruto=_value(Decimal("5000.00")),
        total_descontos=_value(Decimal("707.45")),
        salario_liquido=_value(Decimal("4292.55")),
        inss=_value(Decimal("330.00")),
        irrf=_value(Decimal("137.45")),
        fgts=_value(Decimal("240.00")),
        base_inss=_value(Decimal("3000.00")),
        base_irrf=_value(Decimal("2670.00")),
        base_fgts=_value(Decimal("3000.00")),
        dependentes=_value("2"),
    )

    output = to_pipeline_fields(fields, "contracheque")

    assert output["razao_social"] == "ACME S.A."
    assert output["company_name"] == "ACME S.A."
    assert output["nome_funcionario"] == "Maria Silva"
    assert output["periodo"] == "01/2026"
    assert output["data_admissao"] == "15/03/2020"
    assert output["salario_bruto"] == 5000.0
    assert output["gross_salary"] == 5000.0
    assert output["salario_liquido"] == 4292.55
    assert output["liquido"] == 4292.55
    assert output["net_salary"] == 4292.55
    assert output["inss"] == 330.0
    assert output["inss_amount"] == 330.0
    assert output["dependentes"] == 2
    assert isinstance(output["dependentes"], int)

    assert "valor_nominal" not in output
    assert "amount" not in output
    assert "due_date" not in output
    assert "bank_code" not in output
    json.dumps(output)


def test_unknown_kind_only_returns_canonical():
    output = to_pipeline_fields(_boleto_fields(), "unknown")

    assert set(output) == {"canonical"}
    json.dumps(output)
