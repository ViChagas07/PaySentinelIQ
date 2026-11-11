from datetime import date
from decimal import Decimal

import pytest

from app.services.extraction.adapter import to_pipeline_fields
from app.services.extraction.payslip_extractor import extract_payslip_fields
from app.services.validation.payslip_rules import validate_payslip

TODAY = date(2026, 11, 11)


def _fields(**overrides):
    fields = {
        "salario_bruto": Decimal("5000.00"),
        "total_descontos": Decimal("501.51"),
        "salario_liquido": Decimal("4498.49"),
        "inss": Decimal("501.51"),
        "irrf": Decimal("0.00"),
        "fgts": Decimal("400.00"),
        "base_inss": Decimal("5000.00"),
        "base_fgts": Decimal("5000.00"),
        "dependentes": "0",
        "cargo": "Analista",
        "periodo": "01/2026",
        "data_admissao": "15/03/2020",
        "cpf": "123.456.789-09",
        "cnpj": "12.345.678/0001-95",
    }
    fields.update(overrides)
    return fields


def _codes(fields) -> set[str]:
    evidences, _expected, _skipped = validate_payslip(fields, today=TODAY)
    return {evidence.code for evidence in evidences}


def test_consistent_payslip_has_no_evidence():
    evidences, expected, skipped = validate_payslip(_fields(), today=TODAY)

    assert evidences == []
    assert expected["inss_expected"] == "501.51"
    assert expected["tables"]["inss"] == "INSS_2026"
    assert skipped == []


def test_net_mismatch_is_critical_above_one_real():
    codes = _codes(
        _fields(
            salario_liquido=Decimal("4500.00"),
        )
    )

    assert "PAYSLIP_NET_MISMATCH" in codes


def test_inss_above_ceiling_is_critical():
    fields = _fields(
        salario_bruto=Decimal("10000.00"),
        total_descontos=Decimal("1000.00"),
        salario_liquido=Decimal("9000.00"),
        inss=Decimal("1000.00"),
        fgts=Decimal("800.00"),
        base_inss=Decimal("10000.00"),
        base_fgts=Decimal("10000.00"),
    )
    evidences, _expected, _skipped = validate_payslip(fields, today=TODAY)
    by_code = {evidence.code: evidence for evidence in evidences}

    assert "PAYSLIP_INSS_ABOVE_CEILING" in by_code
    assert by_code["PAYSLIP_INSS_ABOVE_CEILING"].severity.value == "critical"


def test_inss_mismatch_and_downgrade_when_base_presumed():
    fields = _fields(
        total_descontos=Decimal("400.00"),
        salario_liquido=Decimal("4600.00"),
        inss=Decimal("400.00"),
        base_inss=None,
    )
    evidences, _expected, _skipped = validate_payslip(fields, today=TODAY)
    by_code = {evidence.code: evidence for evidence in evidences}

    assert by_code["PAYSLIP_INSS_MISMATCH"].severity.value == "medium"
    assert by_code["PAYSLIP_INSS_MISMATCH"].metadata["base_presumida"] is True


def test_irrf_mismatch_is_high_for_large_delta():
    fields = _fields(
        total_descontos=Decimal("601.51"),
        salario_liquido=Decimal("4398.49"),
        irrf=Decimal("100.00"),
    )
    evidences, _expected, _skipped = validate_payslip(fields, today=TODAY)
    by_code = {evidence.code: evidence for evidence in evidences}

    assert by_code["PAYSLIP_IRRF_MISMATCH"].severity.value == "high"


def test_fgts_mismatch_is_medium():
    evidences, _expected, _skipped = validate_payslip(
        _fields(fgts=Decimal("300.00")),
        today=TODAY,
    )
    by_code = {evidence.code: evidence for evidence in evidences}

    assert by_code["PAYSLIP_FGTS_MISMATCH"].severity.value == "medium"


def test_future_period_is_high():
    codes = _codes(_fields(periodo="12/2099"))

    assert "PAYSLIP_PERIOD_FUTURE" in codes


def test_unsupported_period_only_emits_info():
    evidences, expected, skipped = validate_payslip(
        _fields(periodo="01/2025"),
        today=TODAY,
    )

    assert {evidence.code for evidence in evidences} == {
        "PAYSLIP_TAX_TABLE_UNSUPPORTED"
    }
    assert evidences[0].severity.value == "info"
    assert expected["tables"]["inss"] == "unsupported"
    assert "inss_irrf:tax_table_unsupported" in skipped


def test_missing_fields_skip_rules_without_evidence():
    evidences, _expected, skipped = validate_payslip({}, today=TODAY)

    assert evidences == []
    assert skipped
    assert "inss_irrf:missing_period" in skipped


def test_deductions_inconsistent_is_high():
    evidences, _expected, _skipped = validate_payslip(
        _fields(
            total_descontos=Decimal("400.00"),
            salario_liquido=Decimal("4600.00"),
        ),
        today=TODAY,
    )
    by_code = {evidence.code: evidence for evidence in evidences}

    assert by_code["PAYSLIP_DEDUCTIONS_INCONSISTENT"].severity.value == "high"


def test_base_exceeds_gross_is_medium():
    evidences, _expected, _skipped = validate_payslip(
        _fields(base_inss=Decimal("6000.00")),
        today=TODAY,
    )
    by_code = {evidence.code: evidence for evidence in evidences}

    assert by_code["PAYSLIP_BASE_EXCEEDS_GROSS"].severity.value == "medium"


def test_period_before_admission_is_high():
    codes = _codes(
        _fields(
            periodo="01/2020",
            data_admissao="15/03/2020",
        )
    )

    assert "PAYSLIP_PERIOD_BEFORE_ADMISSION" in codes


def test_invalid_cpf_and_cnpj_are_high():
    codes = _codes(
        _fields(
            cpf="111.111.111-11",
            cnpj="12.345.678/0001-90",
        )
    )

    assert "PAYSLIP_CPF_INVALID" in codes
    assert "PAYSLIP_CNPJ_INVALID" in codes


PAYSLIP_PT = """
Empregador: ACME S.A.
CNPJ: 12.345.678/0001-95
Funcionário: Maria Silva
CPF: 123.456.789-09
Cargo: Analista
CBO: 411005
Competência: 01/2026
Admissão: 15/03/2020
Salário Base: 5.000,00
0010 INSS 11,00 501,51
0020 IRRF 0,00
0030 FGTS 8,00 400,00
Total de Proventos: 5.000,00
Total de Descontos: 501,51
Líquido a Receber: 4.498,49
Base de Cálculo INSS: 5.000,00
Base FGTS: 5.000,00
Dependentes: 0
"""

PAYSLIP_ES = """
Empleador: ANDES S.A.
CNPJ: 12.345.678/0001-95
Trabajador: JUAN PEREZ
CPF: 123.456.789-09
Cargo: Analista
CBO: 411005
Período: 01/2026
Fecha de ingreso: 15/03/2020
Salario base: 5.000,00
0010 INSS 11,00 501,51
0020 IRRF 0,00
0030 FGTS 8,00 400,00
Total haberes: 5.000,00
Total descuentos: 501,51
Neto a pagar: 4.498,49
Base de cálculo INSS: 5.000,00
Base FGTS: 5.000,00
Dependientes: 0
"""

PAYSLIP_EN = """
Employer: ACME INC.
CNPJ: 12.345.678/0001-95
Employee: MARY SMITH
CPF: 123.456.789-09
Position: Analyst
CBO: 411005
Pay Period: 01/2026
Hire Date: 15/03/2020
Base Salary: 5,000.00
0010 INSS 11.00 501.51
0020 IRRF 0.00
0030 FGTS 8.00 400.00
Total Earnings: 5,000.00
Total Deductions: 501.51
Net Pay: 4,498.49
INSS Base: 5,000.00
FGTS Base: 5,000.00
Dependents: 0
"""


@pytest.mark.parametrize(
    ("text", "language"),
    [
        (PAYSLIP_PT, "pt"),
        (PAYSLIP_ES, "es"),
        (PAYSLIP_EN, "en"),
    ],
)
def test_extracted_payslips_are_consistent(text, language):
    fields = extract_payslip_fields(text)
    mapped = to_pipeline_fields(fields, "contracheque")

    evidences, expected, _skipped = validate_payslip(mapped, today=TODAY)

    assert fields.language.lang == language
    assert mapped["salario_bruto"] == 5000.0
    assert expected["inss_expected"] == "501.51"
    assert evidences == []
