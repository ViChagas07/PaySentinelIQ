from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, ROUND_HALF_UP

CENT = Decimal("0.01")
INSS_LIMITS = (
    (Decimal("1621.00"), Decimal("0.075")),
    (Decimal("2902.84"), Decimal("0.09")),
    (Decimal("4354.27"), Decimal("0.12")),
    (Decimal("8475.55"), Decimal("0.14")),
)
IRRF_BRACKETS = (
    (Decimal("2428.80"), Decimal("0"), Decimal("0")),
    (Decimal("2826.65"), Decimal("0.075"), Decimal("182.16")),
    (Decimal("3751.05"), Decimal("0.15"), Decimal("394.16")),
    (Decimal("4664.68"), Decimal("0.225"), Decimal("675.49")),
    (None, Decimal("0.275"), Decimal("908.73")),
)
DEPENDENT_DEDUCTION = Decimal("189.59")
SIMPLIFIED_DEDUCTION = Decimal("607.20")


def _round(value: Decimal, mode: str = ROUND_HALF_UP) -> Decimal:
    return value.quantize(CENT, rounding=mode)


def inss(base: Decimal, mode: str = "end") -> Decimal:
    taxable = min(max(base, Decimal("0")), INSS_LIMITS[-1][0])
    previous = Decimal("0")
    total = Decimal("0")
    for limit, rate in INSS_LIMITS:
        if taxable <= previous:
            break
        slice_base = min(taxable, limit) - previous
        if mode == "per_bracket":
            total += _round(slice_base * rate)
        else:
            total += slice_base * rate
        previous = limit
    if mode == "truncate":
        return _round(total, ROUND_DOWN)
    return _round(total)


def _irrf_table(base: Decimal) -> tuple[Decimal, Decimal]:
    taxable = max(base, Decimal("0"))
    rate = Decimal("0")
    deduction = Decimal("0")
    for limit, bracket_rate, bracket_deduction in IRRF_BRACKETS:
        if limit is None or taxable <= limit:
            rate = bracket_rate
            deduction = bracket_deduction
            break
    table_tax = _round(
        max(Decimal("0"), taxable * rate - deduction),
        ROUND_HALF_EVEN,
    )
    return table_tax, taxable


def _reduction(gross: Decimal, tax: Decimal) -> Decimal:
    if gross <= Decimal("5000.00"):
        return min(tax, Decimal("312.89"))
    if gross <= Decimal("7350.00"):
        return min(
            tax,
            max(Decimal("0"), Decimal("978.62") - Decimal("0.133145") * gross),
        )
    return Decimal("0.00")


def irrf(gross: Decimal, inss_value: Decimal, dependents: int) -> Decimal:
    legal_base = gross - inss_value - DEPENDENT_DEDUCTION * dependents
    simplified_base = gross - SIMPLIFIED_DEDUCTION
    legal_tax, _ = _irrf_table(legal_base)
    simplified_tax, _ = _irrf_table(simplified_base)
    legal_final = max(
        Decimal("0"),
        legal_tax - _round(_reduction(gross, legal_tax), ROUND_HALF_EVEN),
    )
    simplified_final = max(
        Decimal("0"),
        simplified_tax - _round(_reduction(gross, simplified_tax), ROUND_HALF_EVEN),
    )
    return _round(min(legal_final, simplified_final))


def calculate_payslip(
    *,
    base_salary: Decimal,
    additional: Decimal,
    dependents: int,
    other_deductions: Decimal,
    mode: str = "end",
) -> dict[str, str]:
    gross = _round(base_salary + additional)
    inss_value = inss(gross, mode)
    irrf_value = irrf(gross, inss_value, dependents)
    fgts_value = _round(gross * Decimal("0.08"))
    total_deductions = _round(inss_value + irrf_value + other_deductions)
    net = _round(gross - total_deductions)
    return {
        "salario_base": str(_round(base_salary)),
        "proventos_adicionais": str(_round(additional)),
        "salario_bruto": str(gross),
        "total_descontos": str(total_deductions),
        "salario_liquido": str(net),
        "inss": str(inss_value),
        "irrf": str(irrf_value),
        "fgts": str(fgts_value),
        "base_inss": str(gross),
        "base_irrf": str(gross),
        "base_fgts": str(gross),
        "dependentes": str(dependents),
    }
