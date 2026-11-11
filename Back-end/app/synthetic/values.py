from __future__ import annotations

from datetime import date
from decimal import Decimal
import random

MONTHS_EN = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

COMPANIES = {
    "pt": (
        "Alfa FictÃ­cia ComÃ©rcio Ltda",
        "Beta Inventada ServiÃ§os S.A.",
        "Gama ImaginÃ¡ria ParticipaÃ§Ãµes Ltda",
        "Delta HipotÃ©tica LogÃ­stica Ltda",
        "Ã‰psilon FictÃ­cia Tecnologia Ltda",
        "Zeta Simulada IndÃºstria S.A.",
        "Omega Inventada Consultoria Ltda",
        "Sigma FictÃ­cia Alimentos Ltda",
    ),
    "es": (
        "Alfa Ficticia Comercio S.A.",
        "Beta Inventada Servicios S.A.",
        "Gama Imaginaria Participaciones S.A.",
        "Delta Hipotetica Logistica S.A.",
        "Epsilon Ficticia Tecnologia S.A.",
        "Zeta Simulada Industria S.A.",
        "Omega Inventada Consultoria S.A.",
        "Sigma Ficticia Alimentos S.A.",
    ),
    "en": (
        "Alpha Fictional Trading Inc.",
        "Beta Invented Services Inc.",
        "Gamma Imaginary Holdings Inc.",
        "Delta Hypothetical Logistics Inc.",
        "Epsilon Fictional Technology Inc.",
        "Zeta Simulated Manufacturing Inc.",
        "Omega Invented Consulting Inc.",
        "Sigma Fictional Foods Inc.",
    ),
}

SHIFT_COMPANIES = {
    "pt": (
        "Aurora HipotÃ©tica Papelaria Ltda",
        "Boreal ImaginÃ¡ria Metais Ltda",
        "Criativa FictÃ­cia Software Ltda",
        "Duna Inventada Facilities Ltda",
    ),
    "es": (
        "Aurora Hipotetica Papeleria S.A.",
        "Boreal Imaginaria Metales S.A.",
        "Creativa Ficticia Software S.A.",
        "Duna Inventada Facilities S.A.",
    ),
    "en": (
        "Aurora Hypothetical Stationery Inc.",
        "Boreal Imaginary Metals Inc.",
        "Creative Fictional Software Inc.",
        "Dune Invented Facilities Inc.",
    ),
}

PEOPLE = {
    "pt": (
        "Marina FictÃ­cia Alves",
        "Rafael Inventado Costa",
        "Helena HipotÃ©tica Souza",
        "Bruno Simulado Ribeiro",
        "Clara ImaginÃ¡ria Nunes",
        "Diego FictÃ­cio Martins",
    ),
    "es": (
        "Marina Ficticia Alvarez",
        "Rafael Inventado Costa",
        "Helena Hipotetica Suarez",
        "Bruno Simulado Rivas",
        "Clara Imaginaria Nunez",
        "Diego Ficticio Martinez",
    ),
    "en": (
        "Marina Fictional Allen",
        "Rafael Invented Costa",
        "Helena Hypothetical Smith",
        "Bruno Simulated Rivers",
        "Clara Imaginary Nunes",
        "Diego Fictional Martin",
    ),
}

ROLES = {
    "pt": ("Analista FictÃ­cio", "Assistente Inventado", "Coordenador HipotÃ©tico"),
    "es": ("Analista Ficticio", "Asistente Inventado", "Coordinador Hipotetico"),
    "en": ("Fictional Analyst", "Invented Assistant", "Hypothetical Coordinator"),
}

CITIES = {
    "pt": "Cidade FictÃ­cia",
    "es": "Ciudad Ficticia",
    "en": "Fictional City",
}

BOLETO_BANKS = ("001", "033", "104", "237", "341", "260", "077")
SHIFT_BANKS = ("104", "237", "341")

LABELS = {
    "boleto": {
        "pt": {
            "set1": {
                "beneficiario": "BeneficiÃ¡rio do TÃ­tulo",
                "pagador": "Pagador do TÃ­tulo",
                "data_vencimento": "Data de Vencimento",
                "valor_nominal": "Valor Nominal",
                "codigo_banco": "Banco",
                "nosso_numero": "Nosso NÃºmero",
                "numero_documento": "NÃºmero do Documento",
                "data_documento": "Data do Documento",
                "local_pagamento": "Local de Pagamento",
                "carteira": "Carteira",
                "agencia_codigo_beneficiario": "AgÃªncia/CÃ³digo do BeneficiÃ¡rio",
                "multa": "Multa",
                "juros": "Juros",
                "linha_digitavel": "Linha DigitÃ¡vel",
            },
            "set2": {
                "beneficiario": "Credor do TÃ­tulo",
                "pagador": "Sacado do TÃ­tulo",
                "data_vencimento": "Data Limite de Pagamento",
                "valor_nominal": "Montante do TÃ­tulo",
                "codigo_banco": "InstituiÃ§Ã£o Financeira",
                "nosso_numero": "Identificador do TÃ­tulo",
                "numero_documento": "NÃºmero do TÃ­tulo",
                "data_documento": "Data de EmissÃ£o",
                "local_pagamento": "PraÃ§a de Pagamento",
                "carteira": "Carteira de CobranÃ§a",
                "agencia_codigo_beneficiario": "AgÃªncia e CÃ³digo do Credor",
                "multa": "Penalidade",
                "juros": "Encargos",
                "linha_digitavel": "RepresentaÃ§Ã£o NumÃ©rica",
            },
        },
        "es": {
            "set1": {
                "beneficiario": "Beneficiario del Titulo",
                "pagador": "Pagador del Titulo",
                "data_vencimento": "Fecha de vencimiento",
                "valor_nominal": "Valor Nominal del Titulo",
                "codigo_banco": "Banco",
                "nosso_numero": "Nuestro numero",
                "numero_documento": "Numero del documento",
                "data_documento": "Fecha del documento",
                "local_pagamento": "Lugar de pago",
                "carteira": "Cartera",
                "agencia_codigo_beneficiario": "Agencia/Codigo del beneficiario",
                "multa": "Multa",
                "juros": "Intereses de mora",
                "linha_digitavel": "Linea digitable",
            },
            "set2": {
                "beneficiario": "Acreedor del Titulo",
                "pagador": "Deudor del Titulo",
                "data_vencimento": "Fecha Limite de Pago",
                "valor_nominal": "Importe del Titulo",
                "codigo_banco": "Entidad Financiera",
                "nosso_numero": "Identificador del Titulo",
                "numero_documento": "Numero de Titulo",
                "data_documento": "Fecha de Emision",
                "local_pagamento": "Plaza de Pago",
                "carteira": "Cartera de Cobro",
                "agencia_codigo_beneficiario": "Agencia y Codigo del Acreedor",
                "multa": "Penalidad",
                "juros": "Recargos",
                "linha_digitavel": "Representacion Numerica",
            },
        },
        "en": {
            "set1": {
                "beneficiario": "Beneficiary Name",
                "pagador": "Payer Name",
                "data_vencimento": "Due Date",
                "valor_nominal": "Document Amount",
                "codigo_banco": "Bank Code",
                "nosso_numero": "Our Number",
                "numero_documento": "Document Number",
                "data_documento": "Document Date",
                "local_pagamento": "Place of Payment",
                "carteira": "Wallet",
                "agencia_codigo_beneficiario": "Agency/Beneficiary Code",
                "multa": "Fine",
                "juros": "Late Interest",
                "linha_digitavel": "Digitable Line",
            },
            "set2": {
                "beneficiario": "Creditor",
                "pagador": "Debtor",
                "data_vencimento": "Payment Deadline",
                "valor_nominal": "Face Amount",
                "codigo_banco": "Financial Institution",
                "nosso_numero": "Instrument Identifier",
                "numero_documento": "Instrument Number",
                "data_documento": "Issue Date",
                "local_pagamento": "Payment Venue",
                "carteira": "Collection Portfolio",
                "agencia_codigo_beneficiario": "Agency and Creditor Code",
                "multa": "Penalty",
                "juros": "Charges",
                "linha_digitavel": "Numeric Representation",
            },
        },
    },
    "contracheque": {
        "pt": {
            "set1": {
                "razao_social": "Empregador",
                "cnpj": "CNPJ do Empregador",
                "nome_funcionario": "Nome do FuncionÃ¡rio",
                "cpf": "CPF",
                "cargo": "Cargo",
                "cbo": "CBO",
                "periodo": "CompetÃªncia",
                "data_admissao": "Data de AdmissÃ£o",
                "salario_base": "SalÃ¡rio Base",
                "inss": "INSS",
                "irrf": "IRRF",
                "fgts": "FGTS",
                "salario_bruto": "Total de Proventos",
                "total_descontos": "Total de Descontos",
                "salario_liquido": "LÃ­quido a Receber",
                "base_inss": "Base de CÃ¡lculo INSS",
                "base_irrf": "Base IRRF",
                "base_fgts": "Base FGTS",
                "dependentes": "Dependentes",
            },
            "set2": {
                "razao_social": "RazÃ£o Social do Empregador",
                "cnpj": "CNPJ da Empresa",
                "nome_funcionario": "Colaborador",
                "cpf": "Documento Pessoal",
                "cargo": "OcupaÃ§Ã£o",
                "cbo": "ClassificaÃ§Ã£o CBO",
                "periodo": "MÃªs de ReferÃªncia",
                "data_admissao": "Data de ContrataÃ§Ã£o",
                "salario_base": "RemuneraÃ§Ã£o Base",
                "inss": "PrevidÃªncia",
                "irrf": "Imposto de Renda",
                "fgts": "Fundo de Garantia",
                "salario_bruto": "Total de Vencimentos",
                "total_descontos": "Abatimentos",
                "salario_liquido": "Valor LÃ­quido",
                "base_inss": "Base PrevidenciÃ¡ria",
                "base_irrf": "Base Fiscal",
                "base_fgts": "Base do Fundo",
                "dependentes": "NÃºmero de Dependentes",
            },
        },
        "es": {
            "set1": {
                "razao_social": "Empleador",
                "cnpj": "CNPJ",
                "nome_funcionario": "Trabajador",
                "cpf": "CPF",
                "cargo": "Cargo",
                "cbo": "CBO",
                "periodo": "PerÃ­odo",
                "data_admissao": "Fecha de ingreso",
                "salario_base": "Salario base",
                "inss": "INSS",
                "irrf": "IRRF",
                "fgts": "FGTS",
                "salario_bruto": "Total haberes",
                "total_descontos": "Total descuentos",
                "salario_liquido": "Neto a pagar",
                "base_inss": "Base de cÃ¡lculo INSS",
                "base_irrf": "Base IRRF",
                "base_fgts": "Base FGTS",
                "dependentes": "Dependientes",
            },
            "set2": {
                "razao_social": "RazÃ³n Social del Empleador",
                "cnpj": "CNPJ de la Empresa",
                "nome_funcionario": "Empleado",
                "cpf": "Documento Personal",
                "cargo": "OcupaciÃ³n",
                "cbo": "ClasificaciÃ³n CBO",
                "periodo": "Mes de Referencia",
                "data_admissao": "Fecha de ContrataciÃ³n",
                "salario_base": "RemuneraciÃ³n Base",
                "inss": "Seguridad Social",
                "irrf": "Impuesto sobre la Renta",
                "fgts": "Fondo de GarantÃ­a",
                "salario_bruto": "Total de Devengos",
                "total_descontos": "Deducciones",
                "salario_liquido": "Importe Neto",
                "base_inss": "Base Previsional",
                "base_irrf": "Base Fiscal",
                "base_fgts": "Base del Fondo",
                "dependentes": "NÃºmero de Dependientes",
            },
        },
        "en": {
            "set1": {
                "razao_social": "Employer",
                "cnpj": "CNPJ",
                "nome_funcionario": "Employee Name",
                "cpf": "CPF",
                "cargo": "Position",
                "cbo": "CBO",
                "periodo": "Pay Period",
                "data_admissao": "Hire Date",
                "salario_base": "Base Salary",
                "inss": "INSS",
                "irrf": "IRRF",
                "fgts": "FGTS",
                "salario_bruto": "Total Earnings",
                "total_descontos": "Total Deductions",
                "salario_liquido": "Net Pay",
                "base_inss": "INSS Base",
                "base_irrf": "IRRF Base",
                "base_fgts": "FGTS Base",
                "dependentes": "Dependents",
            },
            "set2": {
                "razao_social": "Employer Legal Name",
                "cnpj": "Company CNPJ",
                "nome_funcionario": "Worker",
                "cpf": "Personal Document",
                "cargo": "Occupation",
                "cbo": "CBO Classification",
                "periodo": "Reference Month",
                "data_admissao": "Employment Date",
                "salario_base": "Base Remuneration",
                "inss": "Social Insurance",
                "irrf": "Income Tax",
                "fgts": "Severance Fund",
                "salario_bruto": "Gross Compensation",
                "total_descontos": "Withholdings",
                "salario_liquido": "Net Amount",
                "base_inss": "Social Insurance Base",
                "base_irrf": "Tax Base",
                "base_fgts": "Fund Base",
                "dependentes": "Number of Dependents",
            },
        },
    },
}


def generate_cnpj(rng: random.Random) -> str:
    digits = [rng.randrange(10) for _ in range(8)] + [0, 0, 0, 1]
    digits.extend(_cnpj_dv(digits))
    return "".join(str(digit) for digit in digits)


def _cnpj_dv(digits: list[int]) -> list[int]:
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    first = sum(digit * weight for digit, weight in zip(digits[:12], weights1, strict=True)) % 11
    dv1 = 0 if first < 2 else 11 - first
    second = sum(
        digit * weight
        for digit, weight in zip(digits[:12] + [dv1], weights2, strict=True)
    ) % 11
    dv2 = 0 if second < 2 else 11 - second
    return [dv1, dv2]


def generate_cpf(rng: random.Random) -> str:
    digits = [rng.randrange(10) for _ in range(9)]
    first = sum(digit * weight for digit, weight in zip(digits, range(10, 1, -1), strict=True)) % 11
    dv1 = 0 if first < 2 else 11 - first
    second = sum(
        digit * weight
        for digit, weight in zip(digits + [dv1], range(11, 1, -1), strict=True)
    ) % 11
    dv2 = 0 if second < 2 else 11 - second
    return "".join(str(digit) for digit in digits + [dv1, dv2])


def format_cnpj(digits: str) -> str:
    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"


def format_cpf(digits: str) -> str:
    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"


def format_amount(
    value: Decimal,
    language: str,
    *,
    us_format: bool = False,
) -> str:
    if language == "en" and us_format:
        return f"{value:,.2f}"
    text = f"{value:,.2f}"
    if language == "en":
        return text.replace(",", "")
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def format_date(value: date, language: str) -> str:
    if language == "en":
        if value.day > 12:
            return value.strftime("%m/%d/%Y")
        return f"{MONTHS_EN[value.month - 1]} {value.day:02d}, {value.year}"
    return value.strftime("%d/%m/%Y")


def format_period(year: int, month: int) -> str:
    return f"{month:02d}/{year}"

