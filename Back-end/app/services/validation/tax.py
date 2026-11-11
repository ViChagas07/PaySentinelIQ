from __future__ import annotations

import re
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP
from typing import Any, Literal

from app.services.validation.tables import (
    INSS_TABLES,
    IRRF_REDUCTIONS,
    IRRF_TABLES,
    InssTable,
    IrrfReduction,
    IrrfTable,
)

Unsupported = Literal["unsupported"]

_CENT = Decimal("0.01")
_COMPETENCE_MM_YYYY = re.compile(r"^(\d{1,2})[/-](\d{4})$")
_COMPETENCE_YYYY_MM = re.compile(r"^(\d{4})[/-](\d{1,2})$")


def _decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _parse_competence(competencia: str) -> tuple[int, int] | None:
    text = competencia.strip()
    match = _COMPETENCE_MM_YYYY.fullmatch(text)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
    else:
        match = _COMPETENCE_YYYY_MM.fullmatch(text)
        if not match:
            return None
        year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return year, month


def _money(value: Decimal, rounding: str = ROUND_HALF_UP) -> Decimal:
    return value.quantize(_CENT, rounding=rounding)


def _inss_table(competencia: str) -> InssTable | None:
    parsed = _parse_competence(competencia)
    if parsed is None:
        return None
    year, _month = parsed
    return INSS_TABLES.get(year)


def _irrf_context(
    competencia: str,
) -> tuple[IrrfTable, IrrfReduction | None] | None:
    parsed = _parse_competence(competencia)
    if parsed is None:
        return None
    year, month = parsed
    if (year, month) < (2025, 5):
        return None
    table = IRRF_TABLES.get(year)
    if table is None:
        return None
    reduction = IRRF_REDUCTIONS.get(year) if (year, month) >= (2026, 1) else None
    return table, reduction


def inss_for(
    salario_base: Decimal | int | float | str,
    competencia: str,
) -> Decimal | Unsupported:
    table = _inss_table(competencia)
    if table is None:
        return "unsupported"

    salary = _decimal(salario_base)
    if salary <= 0:
        return Decimal("0.00")

    taxable = min(salary, table.ceiling)
    previous = Decimal("0")
    total = Decimal("0")
    for bracket in table.brackets:
        if taxable <= previous:
            break
        slice_base = min(taxable, bracket.limit) - previous
        total += slice_base * bracket.rate
        previous = bracket.limit

    return _money(total, ROUND_HALF_UP)


def _irrf_tax(
    base: Decimal,
    rendimento: Decimal,
    table: IrrfTable,
    reduction: IrrfReduction | None,
) -> tuple[Decimal, Decimal, Decimal, Decimal]:
    taxable = max(Decimal("0"), base)
    selected = table.brackets[-1]
    for bracket in table.brackets:
        if bracket.upper_limit is None or taxable <= bracket.upper_limit:
            selected = bracket
            break

    table_tax = max(
        Decimal("0"),
        taxable * selected.rate - selected.deduction,
    )
    table_tax = _money(table_tax, ROUND_HALF_EVEN)

    reduction_value = Decimal("0")
    if reduction is not None:
        if rendimento <= reduction.full_reduction_limit:
            reduction_value = min(table_tax, reduction.full_reduction)
        elif rendimento <= reduction.partial_limit:
            reduction_value = max(
                Decimal("0"),
                reduction.partial_base - reduction.partial_rate * rendimento,
            )
            reduction_value = min(table_tax, reduction_value)
        reduction_value = _money(reduction_value, ROUND_HALF_EVEN)

    final = max(Decimal("0"), table_tax - reduction_value)
    return (
        table_tax,
        reduction_value,
        _money(final, ROUND_HALF_UP),
        taxable,
    )


def irrf_candidates(
    rendimento_bruto: Decimal | int | float | str,
    inss_impresso: Decimal | int | float | str | None,
    dependentes: int | None,
    base_irrf_impressa: Decimal | int | float | str | None,
    competencia: str,
) -> list[tuple[str, Decimal, dict[str, Any]]] | Unsupported:
    context = _irrf_context(competencia)
    if context is None:
        return "unsupported"
    table, reduction = context

    rendimento = _decimal(rendimento_bruto)
    inss_value = _decimal(inss_impresso) if inss_impresso is not None else Decimal("0")
    dependents_value = Decimal(dependentes or 0)
    dependent_deduction = dependents_value * table.dependent_deduction

    bases: list[tuple[str, Decimal]] = []
    if base_irrf_impressa is not None:
        bases.append(("base_impressa", _decimal(base_irrf_impressa)))
    bases.append(
        (
            "deducoes_legais",
            rendimento - inss_value - dependent_deduction,
        )
    )
    bases.append(
        (
            "desconto_simplificado",
            rendimento - table.simplified_deduction,
        )
    )

    candidates: list[tuple[str, Decimal, dict[str, Any]]] = []
    for method, base in bases:
        table_tax, reduction_value, final, taxable = _irrf_tax(
            base,
            rendimento,
            table,
            reduction,
        )
        candidates.append(
            (
                method,
                final,
                {
                    "base": taxable,
                    "tabela": table_tax,
                    "reducao": reduction_value,
                    "rendimento": rendimento,
                    "inss": inss_value,
                    "dependentes": dependentes or 0,
                    "tabela_versao": table.name,
                    "reducao_versao": (
                        reduction.name if reduction is not None else None
                    ),
                },
            )
        )
    return candidates


def table_versions(competencia: str) -> dict[str, str]:
    context = _irrf_context(competencia)
    inss_table = _inss_table(competencia)
    parsed = _parse_competence(competencia)
    versions: dict[str, str] = {
        "competencia": (
            f"{parsed[1]:02d}/{parsed[0]}" if parsed is not None else ""
        ),
        "inss": inss_table.name if inss_table is not None else "unsupported",
        "irrf": context[0].name if context is not None else "unsupported",
        "reducao": (
            context[1].name
            if context is not None and context[1] is not None
            else "none"
        ),
    }
    return versions
