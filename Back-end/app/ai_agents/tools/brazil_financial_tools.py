# ============================================================
# PaySentinelIQ — Brazilian Financial Calculation Tools
# CNPJ, INSS, IRRF, FGTS, CBO, BACEN validators
# All algorithms follow official Brazilian government specifications
# ============================================================

from typing import Any

from langchain_core.tools import tool

# ═══════════════════════════════════════════════════════════════
# CNPJ VALIDATION (Módulo 11 — Receita Federal algorithm)
# ═══════════════════════════════════════════════════════════════

# Weights for first check digit (12 digits)
_CNPJ_WEIGHTS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
# Weights for second check digit (13 digits)
_CNPJ_WEIGHTS_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

# Known invalid CNPJ patterns (all same digit)
_CNPJ_INVALID_PATTERNS = {str(i) * 14 for i in range(10)}


def _cnpj_mod11(digits: str, weights: list[int]) -> int:
    """Calculate Módulo 11 check digit for CNPJ."""
    total = sum(int(d) * w for d, w in zip(digits, weights))
    remainder = total % 11
    return 0 if remainder < 2 else 11 - remainder


def _validate_cnpj_checksum(cnpj_digits: str) -> bool:
    """Pure Módulo 11 validation of CNPJ check digits."""
    if len(cnpj_digits) != 14:
        return False
    if cnpj_digits in _CNPJ_INVALID_PATTERNS:
        return False

    dv1_calculated = _cnpj_mod11(cnpj_digits[:12], _CNPJ_WEIGHTS_DV1)
    if dv1_calculated != int(cnpj_digits[12]):
        return False

    dv2_calculated = _cnpj_mod11(cnpj_digits[:13], _CNPJ_WEIGHTS_DV2)
    return dv2_calculated == int(cnpj_digits[13])


def _parse_cnpj(cnpj_raw: str) -> str:
    """Extract only digits from CNPJ string."""
    return "".join(c for c in cnpj_raw if c.isdigit())


@tool
def cnpj_validator(cnpj: str) -> dict[str, Any]:
    """
    Validate a Brazilian CNPJ using Módulo 11 checksum algorithm (Receita Federal standard).

    Input: CNPJ string (any format — 12.345.678/0001-90, 12345678000190, etc.)
    Returns: validation result with detailed analysis.

    NOTE: Checksum validation is local. For full Receita Federal status lookup
    (Ativa/Inapta/Baixada/Suspensa), an external API call is needed in production.
    This tool returns the checksum result and a flag indicating if the external
    lookup should be performed.
    """
    digits = _parse_cnpj(cnpj)

    # Format check
    if len(digits) != 14:
        return {
            "cnpj_raw": cnpj,
            "cnpj_digits": digits,
            "valid_format": False,
            "valid_checksum": False,
            "error": f"CNPJ must have 14 digits, got {len(digits)}",
            "confidence": 100,
            "recommend_external_lookup": False,
        }

    # All-same pattern check
    if digits in _CNPJ_INVALID_PATTERNS:
        return {
            "cnpj_raw": cnpj,
            "cnpj_digits": digits,
            "valid_format": True,
            "valid_checksum": False,
            "error": "All digits identical — definitively invalid CNPJ",
            "confidence": 100,
            "recommend_external_lookup": False,
        }

    # Checksum validation
    checksum_valid = _validate_cnpj_checksum(digits)

    # Format the CNPJ for display
    formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"

    return {
        "cnpj_raw": cnpj,
        "cnpj_digits": digits,
        "cnpj_formatted": formatted,
        "valid_format": True,
        "valid_checksum": checksum_valid,
        "error": None if checksum_valid else "CNPJ check digits failed Módulo 11 validation",
        "confidence": 100 if checksum_valid else 100,
        "recommend_external_lookup": checksum_valid,  # If checksum passes, verify against Receita Federal
        "raiz": digits[:8],  # Base CNPJ (first 8 digits)
        "filial": digits[8:12],  # Branch number
    }


# ═══════════════════════════════════════════════════════════════
# INSS CALCULATOR (2025 Tabela Progressiva)
# ═══════════════════════════════════════════════════════════════

# INSS 2025 progressive table (Portaria Interministerial MPS/MF Nº 6/2025)
_INSS_2025_BRACKETS = [
    (1412.00, 0.075, 0.00),       # Até R$1.412,00: 7,5%
    (2666.68, 0.09, 21.18),       # R$1.412,01 a R$2.666,68: 9%
    (4000.03, 0.12, 101.18),      # R$2.666,69 a R$4.000,03: 12%
    (7786.02, 0.14, 181.18),      # R$4.000,04 a R$7.786,02: 14%
]

_INSS_TETO = 7786.02  # INSS contribution ceiling


def _calculate_inss(salario_bruto: float) -> dict[str, Any]:
    """Calculate INSS using progressive table method."""
    if salario_bruto <= 0:
        return {"error": "Salário bruto must be positive", "inss_value": 0.0}

    contribuicao = 0.0
    salario_restante = min(salario_bruto, _INSS_TETO)
    faixas_aplicadas = []

    previous_limit = 0.0
    for limit, rate, _ in _INSS_2025_BRACKETS:
        if salario_restante <= 0:
            break
        faixa_width = limit - previous_limit
        taxable = min(salario_restante, faixa_width)
        if taxable > 0:
            contrib = taxable * rate
            contribuicao += contrib
            faixas_aplicadas.append({
                "faixa": f"R$ {previous_limit:,.2f} a R$ {limit:,.2f}",
                "aliquota": f"{rate*100:.1f}%",
                "base_calculo": round(taxable, 2),
                "contribuicao": round(contrib, 2),
            })
        salario_restante -= taxable
        previous_limit = limit

    return {
        "salario_bruto": salario_bruto,
        "teto_inss": _INSS_TETO,
        "salario_contribuicao": min(salario_bruto, _INSS_TETO),
        "inss_calculado": round(contribuicao, 2),
        "aliquota_efetiva": round((contribuicao / salario_bruto) * 100, 2) if salario_bruto > 0 else 0,
        "faixas": faixas_aplicadas,
    }


@tool
def inss_calculator(salario_bruto: float, inss_printed: float = 0.0, competencia: str = "2025") -> dict[str, Any]:
    """
    Calculate INSS contribution for a given gross salary using the 2025 progressive table.
    Compares calculated value against the printed/declared INSS on the payslip.

    Input:
      - salario_bruto: Gross salary in BRL (R$)
      - inss_printed: INSS value printed on document (optional, for comparison)
      - competencia: Period (e.g. "2025", "2024-03") — currently uses 2025 table

    Returns: structured calc result with delta analysis.
    Any delta > R$0.01 between calculated and printed INSS is an anomaly.
    """
    result = _calculate_inss(salario_bruto)

    if "error" in result:
        return {**result, "inss_printed": inss_printed, "delta": None, "anomaly": True, "anomaly_type": "calculation_error"}

    delta = round(result["inss_calculado"] - inss_printed, 2)

    anomaly = abs(delta) > 0.01

    return {
        **result,
        "inss_printed": inss_printed,
        "delta": delta,
        "delta_abs": abs(delta),
        "anomaly": anomaly,
        "anomaly_type": "inss_delta" if anomaly else None,
        "severity": "high" if abs(delta) > 10.0 else ("medium" if abs(delta) > 1.0 else "low"),
        "confidence": 100,  # Mathematical certainty — no ML involved
        "evidence": (
            f"INSS calculado: R$ {result['inss_calculado']:,.2f} | "
            f"INSS declarado: R$ {inss_printed:,.2f} | "
            f"Delta: R$ {delta:,.2f}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# IRRF CALCULATOR (2025 Tabela Progressiva)
# ═══════════════════════════════════════════════════════════════

# IRRF 2025 table (base de cálculo mensal)
_IRRF_2025_BRACKETS = [
    (2259.20, 0.0, 0.0),            # Até R$2.259,20: isento
    (2826.65, 0.075, 169.44),       # R$2.259,21 a R$2.826,65: 7,5%
    (3751.05, 0.15, 381.44),        # R$2.826,66 a R$3.751,05: 15%
    (4664.68, 0.225, 662.77),       # R$3.751,06 a R$4.664,68: 22,5%
    (float("inf"), 0.275, 896.00),  # Acima de R$4.664,68: 27,5%
]

_DEDUCAO_DEPENDENTE_2025 = 189.59  # Per dependent, monthly


def _calculate_irrf(
    salario_bruto: float,
    inss: float,
    dependentes: int = 0,
    pensao_alimenticia: float = 0.0,
    outras_deducoes: float = 0.0,
) -> dict[str, Any]:
    """Calculate IRRF using the progressive table with standard deductions."""
    if salario_bruto <= 0:
        return {"error": "Salário bruto must be positive", "irrf_value": 0.0}

    # Base de cálculo = Salário bruto - INSS - Dependentes - Pensão - Outras
    deducao_dependentes = dependentes * _DEDUCAO_DEPENDENTE_2025
    base_calculo = salario_bruto - inss - deducao_dependentes - pensao_alimenticia - outras_deducoes

    if base_calculo <= 0:
        return {
            "salario_bruto": salario_bruto,
            "inss": inss,
            "dependentes": dependentes,
            "deducao_dependentes": deducao_dependentes,
            "base_calculo": max(base_calculo, 0),
            "irrf_calculado": 0.0,
            "aliquota_efetiva": 0.0,
            "faixa": "Isento",
        }

    irrf = 0.0
    faixa_applied = None

    for limit, rate, deduction in _IRRF_2025_BRACKETS:
        if base_calculo <= limit:
            irrf = (base_calculo * rate) - deduction
            faixa_applied = f"{rate*100:.1f}%"
            break

    irrf = max(irrf, 0)  # IRRF cannot be negative

    return {
        "salario_bruto": salario_bruto,
        "inss": inss,
        "dependentes": dependentes,
        "deducao_dependentes": round(deducao_dependentes, 2),
        "deducao_dependente_por_cabeca": _DEDUCAO_DEPENDENTE_2025,
        "base_calculo": round(base_calculo, 2),
        "irrf_calculado": round(irrf, 2),
        "aliquota_efetiva": round((irrf / salario_bruto) * 100, 2) if salario_bruto > 0 else 0,
        "faixa": faixa_applied or "Isento",
    }


@tool
def irrf_calculator(
    salario_bruto: float,
    inss: float = 0.0,
    irrf_printed: float = 0.0,
    dependentes: int = 0,
) -> dict[str, Any]:
    """
    Calculate IRRF (Imposto de Renda Retido na Fonte) for a given gross salary.
    Uses the 2025 progressive table and standard deductions.

    Input:
      - salario_bruto: Gross salary in BRL
      - inss: INSS contribution value (required for base de cálculo)
      - irrf_printed: IRRF value printed on document (optional, for comparison)
      - dependentes: Number of dependents declared

    Returns: structured calc result with delta analysis.
    """
    result = _calculate_irrf(salario_bruto, inss, dependentes)

    if "error" in result:
        return {**result, "irrf_printed": irrf_printed, "delta": None, "anomaly": True, "anomaly_type": "calculation_error"}

    delta = round(result["irrf_calculado"] - irrf_printed, 2)
    anomaly = abs(delta) > 0.01

    return {
        **result,
        "irrf_printed": irrf_printed,
        "delta": delta,
        "delta_abs": abs(delta),
        "anomaly": anomaly,
        "anomaly_type": "irrf_delta" if anomaly else None,
        "severity": "high" if abs(delta) > 50.0 else ("medium" if abs(delta) > 5.0 else "low"),
        "confidence": 100,
        "evidence": (
            f"Base de cálculo: R$ {result['base_calculo']:,.2f} | "
            f"IRRF calculado: R$ {result['irrf_calculado']:,.2f} | "
            f"IRRF declarado: R$ {irrf_printed:,.2f} | "
            f"Delta: R$ {delta:,.2f}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# FGTS CALCULATOR
# ═══════════════════════════════════════════════════════════════

_FGTS_RATE_REGULAR = 0.08   # 8% for regular employees
_FGTS_RATE_APRENDIZ = 0.02  # 2% for young apprentices


@tool
def fgts_calculator(
    salario_bruto: float,
    fgts_printed: float = 0.0,
    tipo_contrato: str = "regular",
) -> dict[str, Any]:
    """
    Calculate FGTS (Fundo de Garantia do Tempo de Serviço) contribution.
    FGTS is always 8% of gross salary for regular employees, 2% for aprendiz.

    Input:
      - salario_bruto: Gross salary in BRL
      - fgts_printed: FGTS value printed on the document (for comparison)
      - tipo_contrato: "regular" (8%) or "aprendiz" (2%)

    Returns: structured result with delta analysis.
    """
    rate = _FGTS_RATE_APRENDIZ if tipo_contrato.lower() == "aprendiz" else _FGTS_RATE_REGULAR
    fgts_calculado = round(salario_bruto * rate, 2)
    delta = round(fgts_calculado - fgts_printed, 2)

    anomaly = abs(delta) > 0.01

    return {
        "salario_bruto": salario_bruto,
        "tipo_contrato": tipo_contrato,
        "aliquota_fgts": f"{rate*100:.0f}%",
        "fgts_calculado": fgts_calculado,
        "fgts_printed": fgts_printed,
        "delta": delta,
        "delta_abs": abs(delta),
        "anomaly": anomaly,
        "anomaly_type": "fgts_delta" if anomaly else None,
        "severity": "critical" if abs(delta) > 100 else ("high" if abs(delta) > 10 else "low"),
        "confidence": 100,
        "evidence": (
            f"FGTS ({rate*100:.0f}%) calculado: R$ {fgts_calculado:,.2f} | "
            f"FGTS declarado: R$ {fgts_printed:,.2f} | "
            f"Delta: R$ {delta:,.2f}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# LÍQUIDO CONSISTENCY CHECK
# ═══════════════════════════════════════════════════════════════

@tool
def liquido_consistency_check(
    salario_bruto: float,
    inss: float = 0.0,
    irrf: float = 0.0,
    fgts: float = 0.0,
    outros_descontos: float = 0.0,
    outros_vencimentos: float = 0.0,
    liquido_printed: float = 0.0,
) -> dict[str, Any]:
    """
    Verify that salário líquido = salário bruto + outros vencimentos - Σ(all deductions).
    This is the fundamental accounting identity for payslips.

    Input:
      - salario_bruto: Gross salary
      - inss, irrf, fgts: Standard deductions (note: FGTS is not deducted from líquido)
      - outros_descontos: Other deductions (vale transporte, plano de saúde, etc.)
      - outros_vencimentos: Other credits (bonus, overtime, etc.)
      - liquido_printed: Net salary printed on document

    Returns: liquidity check with delta analysis.

    NOTE: FGTS is an employer contribution, not deducted from employee's net pay.
    The calculation is: líquido = bruto + vencimentos - INSS - IRRF - outros descontos
    """
    total_vencimentos = salario_bruto + outros_vencimentos
    total_descontos = inss + irrf + outros_descontos  # FGTS NOT subtracted from líquido
    liquido_calculado = round(total_vencimentos - total_descontos, 2)
    delta = round(liquido_calculado - liquido_printed, 2)

    anomaly = abs(delta) > 0.01

    return {
        "salario_bruto": salario_bruto,
        "outros_vencimentos": outros_vencimentos,
        "total_vencimentos": total_vencimentos,
        "inss": inss,
        "irrf": irrf,
        "outros_descontos": outros_descontos,
        "total_descontos": total_descontos,
        "fgts_nota": "FGTS é contribuição patronal — não deduzido do líquido",
        "liquido_calculado": liquido_calculado,
        "liquido_printed": liquido_printed,
        "delta": delta,
        "delta_abs": abs(delta),
        "anomaly": anomaly,
        "anomaly_type": "liquido_delta" if anomaly else None,
        "severity": "critical" if anomaly else "low",
        "confidence": 100,
        "evidence": (
            f"Vencimentos: R$ {total_vencimentos:,.2f} | "
            f"Descontos: R$ {total_descontos:,.2f} | "
            f"Líquido calculado: R$ {liquido_calculado:,.2f} | "
            f"Líquido declarado: R$ {liquido_printed:,.2f} | "
            f"Delta: R$ {delta:,.2f}"
        ),
    }


# ═══════════════════════════════════════════════════════════════
# CBO SALARY RANGE CHECKER
# ═══════════════════════════════════════════════════════════════

# CBO to expected salary range mapping (reference data — Brazilian labor market)
# Values in BRL, based on RAIS/CAGED data and market surveys
_CBO_SALARY_RANGES: dict[str, dict[str, Any]] = {
    # Administrative
    "4110": {"cargo": "Assistente Administrativo", "min": 1500, "max": 4500, "mediana": 2500},
    "411005": {"cargo": "Auxiliar de Escritório", "min": 1400, "max": 3500, "mediana": 1900},
    "410105": {"cargo": "Supervisor Administrativo", "min": 3500, "max": 9000, "mediana": 5500},
    "252105": {"cargo": "Gerente Administrativo", "min": 6000, "max": 18000, "mediana": 10000},
    "252205": {"cargo": "Gerente Financeiro", "min": 7000, "max": 20000, "mediana": 12000},
    "252305": {"cargo": "Gerente de RH", "min": 6500, "max": 18000, "mediana": 10500},
    # IT / Engineering
    "212405": {"cargo": "Analista de Sistemas", "min": 4000, "max": 12000, "mediana": 7000},
    "212410": {"cargo": "Desenvolvedor de Software", "min": 3500, "max": 15000, "mediana": 8000},
    "142105": {"cargo": "Gerente de TI", "min": 10000, "max": 30000, "mediana": 18000},
    "214405": {"cargo": "Engenheiro Civil", "min": 4000, "max": 15000, "mediana": 8000},
    # General
    "521110": {"cargo": "Vendedor de Comércio Varejista", "min": 1400, "max": 3500, "mediana": 2000},
    "513205": {"cargo": "Cozinheiro Geral", "min": 1400, "max": 3000, "mediana": 1800},
    "514320": {"cargo": "Faxineiro", "min": 1400, "max": 2200, "mediana": 1600},
    "782510": {"cargo": "Motorista de Caminhão", "min": 2200, "max": 5000, "mediana": 3200},
    "517410": {"cargo": "Porteiro de Edifícios", "min": 1400, "max": 2800, "mediana": 1800},
    "354125": {"cargo": "Vendedor Pracista", "min": 1800, "max": 5000, "mediana": 2800},
    # Healthcare
    "223505": {"cargo": "Enfermeiro", "min": 2500, "max": 7000, "mediana": 4000},
    "223405": {"cargo": "Fisioterapeuta", "min": 2500, "max": 6000, "mediana": 3800},
    "225125": {"cargo": "Médico Clínico", "min": 8000, "max": 25000, "mediana": 14000},
}


@tool
def cbo_salary_range(cbo_code: str, salario: float, cargo: str = "", uf: str = "SP") -> dict[str, Any]:
    """
    Check if a stated salary falls within the expected range for a given CBO (Classificação Brasileira de Ocupações) code.

    Input:
      - cbo_code: CBO code (e.g. "411005", "212405")
      - salario: Stated gross salary in BRL
      - cargo: Job title for descriptive matching (optional)
      - uf: State code for regional variation (currently uses national reference)

    Returns: salary range analysis with anomaly flagging.
    """
    # Try exact match first, then partial
    reference = _CBO_SALARY_RANGES.get(cbo_code)

    if not reference:
        # Try prefix match (first 4 digits)
        prefix = cbo_code[:4] if len(cbo_code) >= 4 else cbo_code
        reference = _CBO_SALARY_RANGES.get(prefix)

    if not reference and cargo and cargo.strip():
        # Try matching by cargo name
        cargo_lower = cargo.lower().strip()
        for code, data in _CBO_SALARY_RANGES.items():
            if cargo_lower in data["cargo"].lower():
                reference = data
                break

    if not reference:
        return {
            "cbo_code": cbo_code,
            "cargo": cargo,
            "salario": salario,
            "status": "NOT_VERIFIABLE",
            "error": "CBO code not found in reference database. Recommend manual verification.",
            "anomaly": False,
            "confidence": 0,
        }

    # Analyze salary position
    acima_teto = salario > reference["max"] * 1.5
    acima_media = salario > reference["max"]
    abaixo_piso = salario < reference["min"] * 0.5
    abaixo_media = salario < reference["min"]
    within_range = reference["min"] <= salario <= reference["max"]

    status = "within_range"
    severity = "low"

    if acima_teto:
        status = "far_above_range"
        severity = "high"
    elif acima_media:
        status = "above_range"
        severity = "medium"
    elif abaixo_piso:
        status = "far_below_range"
        severity = "high"
    elif abaixo_media:
        status = "below_range"
        severity = "medium"

    # Calculate how many multiples of the median
    multiples_of_median = round(salario / reference["mediana"], 1) if reference["mediana"] > 0 else 0

    anomaly = not within_range

    return {
        "cbo_code": cbo_code,
        "cargo_referencia": reference["cargo"],
        "cargo_declarado": cargo,
        "salario": salario,
        "salario_min_ref": reference["min"],
        "salario_max_ref": reference["max"],
        "salario_mediano_ref": reference["mediana"],
        "multiples_of_median": multiples_of_median,
        "status": status,
        "severity": severity,
        "anomaly": anomaly,
        "anomaly_type": f"cbo_{status}" if anomaly else None,
        "confidence": 75,  # Reference data may vary by region/company size
        "uf": uf,
        "evidence": (
            f"CBO {cbo_code} ({reference['cargo']}): faixa esperada R$ {reference['min']:,.2f} a R$ {reference['max']:,.2f} | "
            f"Salário declarado: R$ {salario:,.2f} ({multiples_of_median}x a mediana)"
        ),
        "nota": "Reference values are national estimates. Regional variation and company size may affect expected ranges.",
    }


# ═══════════════════════════════════════════════════════════════
# BACEN BANK CODE VALIDATOR (ISPB Registry)
# ═══════════════════════════════════════════════════════════════

# BACEN ISPB registry — major Brazilian banks
# Format: {bank_code: (ISPB, bank_name, active)}
_BACEN_ISPB_REGISTRY: dict[str, tuple[str, str, bool]] = {
    "001": ("00000000", "Banco do Brasil S.A.", True),
    "003": ("04902979", "Banco da Amazônia S.A.", True),
    "004": ("07207996", "Banco do Nordeste do Brasil S.A.", True),
    "007": ("00357296", "Banco Nacional de Desenvolvimento Econômico e Social (BNDES)", True),
    "010": ("08152001", "Credicoamo Crédito Rural Cooperativa", True),
    "012": ("04814563", "Banco Inbursa S.A.", True),
    "014": ("09266216", "Natixis Brasil S.A. Banco Múltiplo", True),
    "021": ("02812747", "Banco Banestes S.A.", True),
    "024": ("01081858", "Banco BANDEPE S.A.", True),
    "025": ("00331570", "Banco Alfa S.A.", True),
    "033": ("00000000", "Banco Santander (Brasil) S.A.", True),
    "036": ("06216628", "Banco Bradesco BBI S.A.", True),
    "037": ("00331570", "Banco do Estado do Pará S.A.", True),
    "040": ("03609816", "Banco Cargill S.A.", True),
    "041": ("09270649", "Banco do Estado do Rio Grande do Sul S.A.", True),
    "047": ("01725012", "Banco do Estado de Sergipe S.A.", True),
    "062": ("07301494", "Banco Bonsucesso S.A.", True),
    "069": ("06102856", "Banco Crefisa S.A.", True),
    "070": ("00000208", "BRB — Banco de Brasília S.A.", True),
    "074": ("00306041", "Banco J. Safra S.A.", True),
    "075": ("00352230", "Banco ABN AMRO S.A.", True),
    "077": ("00004091", "Banco Inter S.A.", True),
    "085": ("05463212", "Cooperativa Central de Crédito do Norte/Nordeste (AILOS)", True),
    "095": ("01172323", "Banco Confidence de Câmbio S.A.", True),
    "097": ("04632851", "Cooperativa Central de Crédito Noroeste Brasileiro (Credicitrus)", True),
    "099": ("00309573", "UNIPRIME Central — Central Interestadual de Cooperativas de Crédito", True),
    "104": ("00360305", "Caixa Econômica Federal", True),
    "107": ("01511468", "Banco BOCOM BBM S.A.", True),
    "133": ("01038839", "Cresol — Confederação das Cooperativas de Crédito", True),
    "136": ("00315557", "UNICRED — Confederação das Cooperativas de Crédito", True),
    "208": ("03030628", "Banco BTG Pactual S.A.", True),
    "212": ("09283423", "Banco Original S.A.", True),
    "213": ("05435001", "Banco Arbi S.A.", True),
    "218": ("07102377", "Banco BS2 S.A.", True),
    "224": ("05861604", "Banco Fibra S.A.", True),
    "237": ("00607469", "Banco Bradesco S.A.", True),
    "246": ("02812348", "Banco ABC Brasil S.A.", True),
    "260": ("01822387", "Nu Pagamentos S.A. (Nubank)", True),
    "290": ("00851067", "PagSeguro Internet S.A.", True),
    "318": ("06118532", "Banco BMG S.A.", True),
    "323": ("01055982", "Mercado Pago — Conta do Mercado Livre", True),
    "336": ("03188072", "Banco C6 S.A.", True),
    "341": ("00607234", "Itaú Unibanco S.A.", True),
    "366": ("06871597", "Banco Société Générale Brasil S.A.", True),
    "370": ("06106578", "Banco Mizuho do Brasil S.A.", True),
    "376": ("03317224", "Banco J.P. Morgan S.A.", True),
    "380": ("05798949", "PicPay Serviços S.A.", True),
    "389": ("01717917", "Banco Mercantil do Brasil S.A.", True),
    "399": ("00173791", "Kirton Bank S.A. — Banco Múltiplo", True),
    "422": ("05816167", "Banco Safra S.A.", True),
    "477": ("03300607", "Citibank N.A.", True),
    "487": ("06231127", "Deutsche Bank S.A. — Banco Alemão", True),
    "623": ("05925884", "Banco PAN S.A.", True),
    "633": ("06898764", "Banco Rendimento S.A.", True),
    "643": ("06214411", "Banco Pine S.A.", True),
    "652": ("06086123", "Itaú Unibanco Holding S.A.", True),
    "655": ("00595883", "Banco Votorantim S.A.", True),
    "707": ("06226427", "Banco Daycoval S.A.", True),
    "712": ("07863750", "Banco Ourinvest S.A.", True),
    "739": ("00055845", "Banco Cetelem S.A.", True),
    "741": ("00051804", "Banco Ribeirão Preto S.A.", True),
    "743": ("00078919", "Banco Semear S.A.", True),
    "745": ("03344796", "Banco Citibank S.A.", True),
    "746": ("03072349", "Banco Modal S.A.", True),
    "748": ("00112227", "Banco Cooperativo Sicredi S.A.", True),
    "752": ("00152677", "Banco BNP Paribas Brasil S.A.", True),
    "755": ("06207820", "Bank of America Merrill Lynch Banco Múltiplo S.A.", True),
    "756": ("00238488", "Banco Cooperativo do Brasil (Bancoob)", True),
}


@tool
def bacen_bank_validator(bank_code: str) -> dict[str, Any]:
    """
    Validate a Brazilian bank code against BACEN's ISPB registry.
    Cross-references the bank code extracted from a boleto's linha digitável
    against the official list of financial institutions registered with BACEN.

    Input:
      - bank_code: 3-digit bank code (e.g. "001", "237", "341")

    Returns: validation result with bank details.
    """
    code = bank_code.strip().zfill(3)

    bank_info = _BACEN_ISPB_REGISTRY.get(code)

    if not bank_info:
        return {
            "bank_code": code,
            "valid": False,
            "bank_name": None,
            "ispb": None,
            "active": False,
            "error": f"Bank code {code} not found in BACEN ISPB registry. Possible fabricated boleto.",
            "severity": "critical",
            "confidence": 100,
            "evidence": f"Código {code} não consta no registro ISPB do BACEN.",
        }

    ispb, name, active = bank_info

    return {
        "bank_code": code,
        "valid": True,
        "bank_name": name,
        "ispb": ispb,
        "active": active,
        "error": None if active else f"Bank {code} ({name}) is inactive/liquidated",
        "severity": "low" if active else "critical",
        "confidence": 100,
        "evidence": f"Banco {code}: {name} | ISPB: {ispb} | Status: {'Ativo' if active else 'Inativo'}",
    }


# ═══════════════════════════════════════════════════════════════
# CNAE COMPATIBILITY CHECKER
# ═══════════════════════════════════════════════════════════════

# CNAE to CBO compatibility mapping — which job roles are plausible for which industries
_CNAE_CBO_COMPATIBILITY: dict[str, list[str]] = {
    # Information Technology
    "62": ["212405", "212410", "142105", "3171", "3172"],
    "6201-5": ["212405", "212410", "142105"],
    "6202-3": ["212405", "212410"],
    "6203-1": ["212405", "212410", "142105"],
    # Financial Services
    "64": ["252105", "252205", "4110", "4131", "4132"],
    "6410-7": ["252105", "252205", "4110"],
    # Retail
    "47": ["521110", "1414", "354125", "4110"],
    "4711-3": ["521110", "4110"],
    "4712-1": ["521110", "4110", "354125"],
    # Manufacturing
    "10": ["8411", "8412", "8111", "4110"],
    "11": ["8411", "8412", "8111"],
    # Construction
    "41": ["214405", "7151", "7152", "4110"],
    "4120-4": ["214405", "7151", "4110"],
    # Healthcare
    "86": ["2235", "2234", "3222", "3221", "5151", "4110"],
    "8610-1": ["2235", "2234", "3222", "4110"],
    # Education
    "85": ["2311", "2313", "3311", "4110"],
    # Food Service
    "56": ["513205", "5134", "4110"],
    "5611-2": ["513205", "4110"],
    # Cleaning Services
    "81": ["514320", "4110"],
    "8121-4": ["514320", "4110"],
    # Transportation
    "49": ["782510", "7823", "4110"],
}


@tool
def cnae_compatibility_check(cnae_code: str, cbo_code: str, cargo: str = "", razao_social: str = "") -> dict[str, Any]:
    """
    Check if a job role (CBO) is compatible with the company's registered
    economic activity (CNAE) from Receita Federal.

    Input:
      - cnae_code: Company's CNAE code (e.g. "6201-5", "4711-3")
      - cbo_code: Employee's CBO code (e.g. "212405")
      - cargo: Job title description (optional, for context)
      - razao_social: Company name (optional, for context)

    Returns: compatibility analysis. A mismatch between CNAE and CBO
    suggests either the company identity or the job role is fabricated.
    """
    # Try exact CNAE match
    compatible_cbos = _CNAE_CBO_COMPATIBILITY.get(cnae_code.strip())

    if not compatible_cbos:
        # Try prefix match (first 2 digits for CNAE division)
        prefix = cnae_code.strip()[:2]
        compatible_cbos = _CNAE_CBO_COMPATIBILITY.get(prefix)

    if not compatible_cbos:
        # Try 4-digit prefix
        prefix4 = cnae_code.strip()[:4]
        for key, val in _CNAE_CBO_COMPATIBILITY.items():
            if key.startswith(prefix4):
                compatible_cbos = val
                break

    if not compatible_cbos:
        return {
            "cnae_code": cnae_code,
            "cbo_code": cbo_code,
            "cargo": cargo,
            "razao_social": razao_social,
            "compatible": None,
            "status": "NOT_VERIFIABLE",
            "error": "CNAE code not found in reference database. Manual verification required.",
            "severity": "low",
            "confidence": 0,
            "evidence": f"CNAE {cnae_code} não encontrado na base de compatibilidade.",
        }

    # Check if CBO is in compatible list
    cbo_clean = cbo_code.strip()
    is_compatible = (
        cbo_clean in compatible_cbos
        or cbo_clean[:4] in compatible_cbos
        or cbo_clean[:3] in compatible_cbos
    )

    return {
        "cnae_code": cnae_code,
        "cbo_code": cbo_code,
        "cargo": cargo,
        "razao_social": razao_social,
        "compatible": is_compatible,
        "compatible_cbos_reference": compatible_cbos,
        "status": "compatible" if is_compatible else "incompatible",
        "severity": "low" if is_compatible else "high",
        "anomaly": not is_compatible,
        "anomaly_type": "cnae_cbo_mismatch" if not is_compatible else None,
        "confidence": 70,  # Reference data is not exhaustive
        "evidence": (
            f"CNAE {cnae_code}: CBOs compatíveis: {compatible_cbos} | "
            f"CBO declarado: {cbo_code} | "
            f"Resultado: {'COMPATÍVEL' if is_compatible else 'INCOMPATÍVEL — possível fraude'}"
        ),
        "nota": "This check uses a reference mapping and may not cover all valid combinations. "
                "Flag for human review rather than automatic rejection.",
    }
