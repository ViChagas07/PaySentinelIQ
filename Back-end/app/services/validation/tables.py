from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

VERIFIED_ON = date(2026, 11, 11)


@dataclass(frozen=True)
class InssBracket:
    limit: Decimal
    rate: Decimal


@dataclass(frozen=True)
class InssTable:
    name: str
    valid_from: date
    source: str
    verified_on: date
    brackets: tuple[InssBracket, ...]
    ceiling: Decimal
    max_contribution: Decimal


@dataclass(frozen=True)
class IrrfBracket:
    upper_limit: Decimal | None
    rate: Decimal
    deduction: Decimal


@dataclass(frozen=True)
class IrrfTable:
    name: str
    valid_from: date
    source: str
    verified_on: date
    brackets: tuple[IrrfBracket, ...]
    dependent_deduction: Decimal
    simplified_deduction: Decimal


@dataclass(frozen=True)
class IrrfReduction:
    name: str
    valid_from: date
    source: str
    verified_on: date
    full_reduction_limit: Decimal
    full_reduction: Decimal
    partial_limit: Decimal
    partial_base: Decimal
    partial_rate: Decimal


INSS_2026 = InssTable(
    name="INSS_2026",
    valid_from=date(2026, 1, 1),
    source="Portaria Interministerial MPS/MF 13/2026",
    verified_on=VERIFIED_ON,
    brackets=(
        InssBracket(Decimal("1621.00"), Decimal("0.075")),
        InssBracket(Decimal("2902.84"), Decimal("0.09")),
        InssBracket(Decimal("4354.27"), Decimal("0.12")),
        InssBracket(Decimal("8475.55"), Decimal("0.14")),
    ),
    ceiling=Decimal("8475.55"),
    max_contribution=Decimal("988.09"),
)

IRRF_2025_05 = IrrfTable(
    name="IRRF_2025_05",
    valid_from=date(2025, 5, 1),
    source="Tabela mensal IRRF vigente desde maio/2025",
    verified_on=VERIFIED_ON,
    brackets=(
        IrrfBracket(Decimal("2428.80"), Decimal("0"), Decimal("0")),
        IrrfBracket(Decimal("2826.65"), Decimal("0.075"), Decimal("182.16")),
        IrrfBracket(Decimal("3751.05"), Decimal("0.15"), Decimal("394.16")),
        IrrfBracket(Decimal("4664.68"), Decimal("0.225"), Decimal("675.49")),
        IrrfBracket(None, Decimal("0.275"), Decimal("908.73")),
    ),
    dependent_deduction=Decimal("189.59"),
    simplified_deduction=Decimal("607.20"),
)

IRRF_REDUCTION_2026 = IrrfReduction(
    name="IRRF_REDUCAO_2026",
    valid_from=date(2026, 1, 1),
    source="Lei 15.270/2025",
    verified_on=VERIFIED_ON,
    full_reduction_limit=Decimal("5000.00"),
    full_reduction=Decimal("312.89"),
    partial_limit=Decimal("7350.00"),
    partial_base=Decimal("978.62"),
    partial_rate=Decimal("0.133145"),
)

INSS_TABLES: dict[int, InssTable] = {2026: INSS_2026}
IRRF_TABLES: dict[int, IrrfTable] = {2025: IRRF_2025_05, 2026: IRRF_2025_05}
IRRF_REDUCTIONS: dict[int, IrrfReduction] = {2026: IRRF_REDUCTION_2026}
