from datetime import date
from decimal import Decimal

from app.services.extraction.payslip_extractor import extract_payslip_fields

PAYSLIP_PT = """
Empregador: ACME S.A.
CNPJ: 12.345.678/0001-90
Funcionário: Maria Silva
CPF: 123.456.789-09
Cargo: Analista
CBO: 411005
Competência: 01/2026
Admissão: 15/03/2020
Salário Base: 3.000,00
0010 INSS 11,00 330,00
0020 IRRF 137,45
0030 FGTS 240,00
Total de Proventos: 5.000,00
Total de Descontos: 707,45
Líquido a Receber: 4.292,55
Base de Cálculo INSS: 3.000,00
Base IRRF: 2.670,00
Base FGTS: 3.000,00
Dependentes: 2
"""

PAYSLIP_ES = """
Empleador: ANDES S.A.
CNPJ: 12.345.678/0001-90
Trabajador: JUAN PEREZ
CPF: 123.456.789-09
Cargo: Analista
CBO: 411005
Período: 01/2026
Fecha de ingreso: 15/03/2020
Salario base: 3.000,00
0010 INSS 11,00 330,00
0020 IRRF 137,45
0030 FGTS 240,00
Total haberes: 5.000,00
Total descuentos: 707,45
Neto a pagar: 4.292,55
Base de cálculo INSS: 3.000,00
Base IRRF: 2.670,00
Base FGTS: 3.000,00
Dependientes: 2
"""

PAYSLIP_EN = """
Employer: ACME INC.
CNPJ: 12.345.678/0001-90
Employee: MARY SMITH
CPF: 123.456.789-09
Position: Analyst
CBO: 411005
Pay Period: 01/2026
Hire Date: 15/03/2020
Base Salary: 3,000.00
0010 INSS 11.00 330.00
0020 IRRF 137.45
0030 FGTS 240.00
Total Earnings: 5,000.00
Total Deductions: 707.45
Net Pay: 4,292.55
INSS Base: 3,000.00
IRRF Base: 2,670.00
FGTS Base: 3,000.00
Dependents: 2
"""

PAYSLIP_NOISE = """
Empregador: ACME S.A.
CNPJ: 12.345.678/0001-9O
Funcionario: Maria Silva
CPF: 123.456.789-09
Cargo: Analista
CBO: 4110O5
Competencia: O1/2O26
Admissao: 15/03/2020
Salario Base: 3.0O0,00
0010 INSS 11,00 33O,00
0020 IRRF 137,45
0030 FGTS 24O,00
Total de Proventos: 5.0O0,00
Total de Descontos: 707,45
Liquido a Receber: 4.292,55
Base de Calculo INSS: 3.0O0,00
Base IRRF: 2.670,00
Base FGTS: 3.000,00
Dependentes: 2
"""


def _assert_common_amounts(fields):
    assert fields.salario_base is not None
    assert fields.salario_base.value == Decimal("3000.00")
    assert fields.salario_bruto is not None
    assert fields.salario_bruto.value == Decimal("5000.00")
    assert fields.total_descontos is not None
    assert fields.total_descontos.value == Decimal("707.45")
    assert fields.salario_liquido is not None
    assert fields.salario_liquido.value == Decimal("4292.55")
    assert fields.inss is not None
    assert fields.inss.value == Decimal("330.00")
    assert fields.irrf is not None
    assert fields.irrf.value == Decimal("137.45")
    assert fields.fgts is not None
    assert fields.fgts.value == Decimal("240.00")
    assert fields.base_inss is not None
    assert fields.base_inss.value == Decimal("3000.00")
    assert fields.base_irrf is not None
    assert fields.base_irrf.value == Decimal("2670.00")
    assert fields.base_fgts is not None
    assert fields.base_fgts.value == Decimal("3000.00")


def test_extract_payslip_pt():
    fields = extract_payslip_fields(PAYSLIP_PT)

    assert fields.language.lang == "pt"
    assert fields.razao_social is not None
    assert fields.razao_social.value == "ACME S.A."
    assert fields.nome_funcionario is not None
    assert fields.nome_funcionario.value == "Maria Silva"
    assert fields.cargo is not None
    assert fields.cargo.value == "Analista"
    assert fields.cbo is not None
    assert fields.cbo.value == "411005"
    assert fields.periodo is not None
    assert fields.periodo.value == "01/2026"
    assert fields.data_admissao is not None
    assert fields.data_admissao.value == date(2020, 3, 15)
    assert fields.cnpj is not None
    assert fields.cnpj.value == "12.345.678/0001-90"
    assert fields.cpf is not None
    assert fields.cpf.value == "123.456.789-09"
    assert fields.dependentes is not None
    assert fields.dependentes.value == "2"
    _assert_common_amounts(fields)
    assert fields.warnings == []


def test_extract_payslip_es():
    fields = extract_payslip_fields(PAYSLIP_ES)

    assert fields.language.lang == "es"
    assert fields.razao_social is not None
    assert fields.razao_social.value == "ANDES S.A."
    assert fields.nome_funcionario is not None
    assert fields.nome_funcionario.value == "JUAN PEREZ"
    assert fields.periodo is not None
    assert fields.periodo.value == "01/2026"
    assert fields.data_admissao is not None
    assert fields.data_admissao.value == date(2020, 3, 15)
    _assert_common_amounts(fields)


def test_extract_payslip_en_uses_us_amounts():
    fields = extract_payslip_fields(PAYSLIP_EN)

    assert fields.language.lang == "en"
    assert fields.razao_social is not None
    assert fields.razao_social.value == "ACME INC."
    assert fields.nome_funcionario is not None
    assert fields.nome_funcionario.value == "MARY SMITH"
    assert fields.periodo is not None
    assert fields.periodo.value == "01/2026"
    _assert_common_amounts(fields)


def test_extract_payslip_noise_corrections():
    fields = extract_payslip_fields(PAYSLIP_NOISE)

    assert fields.language.lang == "pt"
    assert fields.cnpj is not None
    assert fields.cnpj.value == "12.345.678/0001-90"
    assert fields.cbo is not None
    assert fields.cbo.value == "411005"
    assert fields.periodo is not None
    assert fields.periodo.value == "01/2026"
    assert fields.salario_base is not None
    assert fields.salario_base.value == Decimal("3000.00")
    assert fields.inss is not None
    assert fields.inss.value == Decimal("330.00")
    assert fields.salario_bruto is not None
    assert fields.salario_bruto.value == Decimal("5000.00")
    assert fields.salario_liquido is not None
    assert fields.salario_liquido.value == Decimal("4292.55")
    assert fields.corrections


def test_label_and_value_on_separate_lines():
    fields = extract_payslip_fields(
        "Empregador\nACME S.A.\n"
        "Funcionário\nMaria Silva\n"
        "Competência\n01/2026\n"
        "Salário Base\n3.000,00\n"
    )

    assert fields.razao_social is not None
    assert fields.razao_social.value == "ACME S.A."
    assert fields.razao_social.method == "label_next_line"
    assert fields.nome_funcionario is not None
    assert fields.nome_funcionario.value == "Maria Silva"
    assert fields.periodo is not None
    assert fields.periodo.value == "01/2026"
    assert fields.salario_base is not None
    assert fields.salario_base.value == Decimal("3000.00")


def test_ambiguous_admission_date_produces_warning():
    fields = extract_payslip_fields(
        "Empregador: ACME\nAdmissão: 10/01/2020\n"
    )

    assert fields.data_admissao is not None
    assert fields.data_admissao.value == date(2020, 1, 10)
    assert fields.warnings


def test_missing_payslip_fields_remain_none():
    fields = extract_payslip_fields("Empregador: ACME")

    assert fields.razao_social is not None
    assert fields.salario_liquido is None
    assert fields.inss is None
    assert fields.periodo is None
    assert fields.cpf is None
