from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.extraction.text_utils import fold

CANONICAL_LABELS: dict[str, dict[str, tuple[str, ...]]] = {
    "beneficiario": {
        "pt": ("Beneficiário", "Cedente", "Nome do Beneficiário"),
        "es": ("Beneficiario", "Nombre del Beneficiario"),
        "en": ("Beneficiary", "Payee", "Beneficiary Name"),
    },
    "pagador": {
        "pt": ("Pagador", "Sacado", "Nome do Pagador"),
        "es": ("Pagador", "Nombre del Pagador"),
        "en": ("Payer", "Payer Name"),
    },
    "data_vencimento": {
        "pt": (
            "Vencimento",
            "Data de Vencimento",
            "Data Vencimento",
            "Data Limite de Pagamento",
        ),
        "es": (
            "Vencimiento",
            "Fecha de vencimiento",
            "Fecha Limite de Pago",
        ),
        "en": ("Due Date", "Payment Due Date", "Payment Deadline"),
    },
    "valor_nominal": {
        "pt": (
            "Valor do Documento",
            "Valor Nominal",
            "Valor Documento",
            "Valor do Título",
            "Montante do Título",
            "Montante do Titulo",
        ),
        "es": (
            "Valor del documento",
            "Importe del documento",
            "Valor Nominal del Titulo",
            "Valor Nominal del Título",
            "Importe del Titulo",
            "Importe del Título",
        ),
        "en": (
            "Document Amount",
            "Face Value",
            "Amount Due",
            "Face Amount",
        ),
    },
    "valor_cobrado": {
        "pt": ("Valor Cobrado",),
        "es": ("Valor cobrado",),
        "en": ("Amount Charged",),
    },
    "nosso_numero": {
        "pt": ("Nosso Número", "Nosso Numero", "Nosso Num."),
        "es": ("Nuestro número", "Nuestro numero"),
        "en": ("Our Number",),
    },
    "numero_documento": {
        "pt": (
            "Nº do Documento",
            "Número do Documento",
            "No. do Documento",
            "Numero do Documento",
        ),
        "es": ("Número del documento", "Numero del documento", "Nro. Documento"),
        "en": ("Document Number",),
    },
    "data_documento": {
        "pt": (
            "Data do Documento",
            "Data Documento",
            "Data de Emissão",
            "Data de Emissao",
        ),
        "es": (
            "Fecha del documento",
            "Fecha de Emision",
            "Fecha de Emisión",
        ),
        "en": ("Document Date", "Issue Date"),
    },
    "local_pagamento": {
        "pt": ("Local de Pagamento", "Local Pagamento"),
        "es": ("Lugar de pago",),
        "en": ("Place of Payment",),
    },
    "carteira": {
        "pt": ("Carteira",),
        "es": ("Cartera",),
        "en": ("Wallet",),
    },
    "agencia_codigo_beneficiario": {
        "pt": (
            "Agência/Código do Beneficiário",
            "Agência/Código Cedente",
            "Agencia/Codigo Beneficiario",
        ),
        "es": ("Agencia/Código del beneficiario",),
        "en": ("Agency/Beneficiary Code",),
    },
    "multa": {
        "pt": ("Multa", "Multa (%)"),
        "es": ("Multa",),
        "en": ("Fine", "Penalty"),
    },
    "juros": {
        "pt": ("Juros", "Mora", "Juros/Mora"),
        "es": ("Intereses de mora", "Mora"),
        "en": ("Interest", "Late Interest"),
    },
    "codigo_banco": {
        "pt": ("Código do Banco", "Codigo do Banco", "Código Banco", "Banco"),
        "es": ("Código del banco", "Codigo del banco", "Banco"),
        "en": ("Bank Code", "Bank"),
    },
    "linha_digitavel": {
        "pt": ("Linha Digitável", "Linha Digitavel"),
        "es": ("Línea digitable", "Linea digitable"),
        "en": ("Digitable Line", "Typable Line"),
    },
    "codigo_barras": {
        "pt": ("Código de Barras", "Codigo de Barras"),
        "es": ("Código de barras", "Codigo de barras"),
        "en": ("Barcode", "Bar Code"),
    },
    "razao_social": {
        "pt": ("Empregador", "Empresa", "Razão Social", "Nome da Empresa"),
        "es": ("Empleador", "Empresa", "Razón social"),
        "en": ("Employer", "Company", "Company Name"),
    },
    "cnpj": {
        "pt": ("CNPJ",),
        "es": ("CNPJ",),
        "en": ("CNPJ",),
    },
    "nome_funcionario": {
        "pt": (
            "Funcionário",
            "Nome do Funcionário",
            "Colaborador",
            "Empregado",
            "Nome do Empregado",
        ),
        "es": ("Trabajador", "Empleado", "Nombre del Empleado"),
        "en": ("Employee", "Employee Name"),
    },
    "cpf": {
        "pt": ("CPF",),
        "es": ("CPF",),
        "en": ("CPF",),
    },
    "cargo": {
        "pt": ("Cargo", "Função", "Função/Cargo"),
        "es": ("Cargo", "Puesto", "Función"),
        "en": ("Position", "Job Title"),
    },
    "cbo": {
        "pt": ("CBO",),
        "es": ("CBO",),
        "en": ("CBO",),
    },
    "periodo": {
        "pt": (
            "Competência",
            "Referência",
            "Mês/Ano",
            "Competencia/Mes",
            "Mês de Referência",
        ),
        "es": ("Período", "Periodo", "Mes/Año", "Mes de Referencia"),
        "en": ("Pay Period", "Period", "Reference", "Reference Month"),
    },
    "data_admissao": {
        "pt": (
            "Admissão",
            "Data de Admissão",
            "Data Admissão",
            "Data de Contratação",
            "Data de Contratacao",
        ),
        "es": (
            "Fecha de ingreso",
            "Fecha de admisión",
            "Fecha de Contratación",
            "Fecha de Contratacion",
        ),
        "en": ("Hire Date", "Admission Date", "Employment Date"),
    },
    "salario_base": {
        "pt": (
            "Salário Base",
            "Salário Contratual",
            "Salário Básico",
            "Remuneração Base",
            "Remuneracao Base",
        ),
        "es": (
            "Salario base",
            "Sueldo base",
            "Remuneración Base",
            "Remuneracion Base",
        ),
        "en": ("Base Salary", "Basic Salary", "Base Remuneration"),
    },
    "salario_bruto": {
        "pt": (
            "Total de Proventos",
            "Total Proventos",
            "Total de Vencimentos",
            "Proventos",
        ),
        "es": ("Total haberes", "Total devengado", "Total de Devengos"),
        "en": (
            "Total Earnings",
            "Gross Pay",
            "Gross Salary",
            "Gross Compensation",
        ),
    },
    "total_descontos": {
        "pt": ("Total de Descontos", "Total Descontos", "Abatimentos"),
        "es": ("Total descuentos", "Total de deducciones", "Deducciones"),
        "en": ("Total Deductions", "Withholdings"),
    },
    "salario_liquido": {
        "pt": (
            "Líquido a Receber",
            "Valor Líquido",
            "Total Líquido",
            "Líquido",
            "Salário Líquido",
        ),
        "es": (
            "Neto a pagar",
            "Líquido a recibir",
            "Total neto",
            "Importe Neto",
        ),
        "en": ("Net Pay", "Net Salary", "Take-home Pay", "Net Amount"),
    },
    "inss": {
        "pt": (
            "INSS",
            "Previdência Social",
            "Desconto INSS",
            "Contribuição INSS",
            "Previdência",
        ),
        "es": ("INSS", "Seguridad social", "Seguridad Social"),
        "en": ("INSS", "Social Security", "Social Insurance"),
    },
    "irrf": {
        "pt": ("IRRF", "Imposto de Renda", "IR Retido", "Desconto IRRF"),
        "es": (
            "IRRF",
            "Impuesto a la renta",
            "Impuesto sobre la Renta",
        ),
        "en": ("IRRF", "Income Tax", "Withholding Tax"),
    },
    "fgts": {
        "pt": (
            "FGTS",
            "Depósito FGTS",
            "FGTS do Mês",
            "Fundo de Garantia",
        ),
        "es": ("FGTS", "Fondo de Garantía", "Fondo de Garantia"),
        "en": ("FGTS", "Severance Fund"),
    },
    "base_inss": {
        "pt": (
            "Base de Cálculo INSS",
            "Base INSS",
            "Sal. Contr. INSS",
            "Base Calculo INSS",
            "Base Contribuição INSS",
            "Base Previdenciária",
            "Base Previdenciaria",
        ),
        "es": (
            "Base de cálculo INSS",
            "Base calculo INSS",
            "Base Previsional",
        ),
        "en": ("INSS Base", "INSS Calculation Base", "Social Insurance Base"),
    },
    "base_irrf": {
        "pt": (
            "Base de Cálculo IRRF",
            "Base IRRF",
            "Base Calculo IRRF",
            "Base Contribuição IRRF",
            "Base Fiscal",
        ),
        "es": ("Base de cálculo IRRF", "Base calculo IRRF", "Base Fiscal"),
        "en": ("IRRF Base", "IRRF Calculation Base", "Tax Base"),
    },
    "base_fgts": {
        "pt": (
            "Base de Cálculo FGTS",
            "Base FGTS",
            "Base Calculo FGTS",
            "Base Contribuição FGTS",
            "Base do Fundo",
        ),
        "es": (
            "Base de cálculo FGTS",
            "Base calculo FGTS",
            "Base del Fondo",
        ),
        "en": ("FGTS Base", "FGTS Calculation Base", "Fund Base"),
    },
    "dependentes": {
        "pt": (
            "Dependentes",
            "Dep. IRRF",
            "Nº Dependentes",
            "Número de Dependentes",
            "Numero de Dependentes",
        ),
        "es": (
            "Dependientes",
            "Número de Dependientes",
            "Numero de Dependientes",
        ),
        "en": ("Dependents", "Number of Dependents"),
    },
}


@dataclass(frozen=True)
class LabelMatch:
    canonical: str
    text: str
    start: int
    end: int


def normalize_label(text: str) -> str:
    folded = fold(text).replace("º", "").replace("ª", "")
    return " ".join(re.findall(r"[a-z0-9]+", folded))


def _build_pattern(alias: str) -> re.Pattern[str] | None:
    normalized = normalize_label(alias)
    if not normalized:
        return None
    tokens = normalized.split()
    body = r"[\W_]*".join(re.escape(token) for token in tokens)
    return re.compile(rf"(?<!\w){body}(?!\w)")


_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = []
for canonical, by_language in CANONICAL_LABELS.items():
    for aliases in by_language.values():
        for alias in aliases:
            pattern = _build_pattern(alias)
            if pattern is not None:
                _PATTERNS.append((canonical, alias, pattern))


def find_label_matches(line: str) -> list[LabelMatch]:
    folded = fold(line)
    found: list[LabelMatch] = []
    seen: set[tuple[str, int, int]] = set()

    for canonical, _alias, pattern in _PATTERNS:
        match = pattern.search(folded)
        if match is None:
            continue
        key = (canonical, match.start(), match.end())
        if key in seen:
            continue
        seen.add(key)
        found.append(
            LabelMatch(
                canonical=canonical,
                text=match.group(0),
                start=match.start(),
                end=match.end(),
            )
        )

    found.sort(key=lambda item: (item.start, -(item.end - item.start)))
    selected: list[LabelMatch] = []
    occupied: list[tuple[int, int]] = []
    for candidate in found:
        if any(
            not (candidate.end <= start or candidate.start >= end)
            for start, end in occupied
        ):
            continue
        selected.append(candidate)
        occupied.append((candidate.start, candidate.end))

    return sorted(selected, key=lambda item: item.start)
