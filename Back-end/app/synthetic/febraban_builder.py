from __future__ import annotations

from datetime import date


def _mod10(digits: str) -> int:
    total = 0
    weight = 2
    for char in reversed(digits):
        product = int(char) * weight
        total += product // 10 + product % 10
        weight = 1 if weight == 2 else 2
    return (10 - total % 10) % 10


def _general_dv(barcode: str) -> int:
    total = 0
    weight = 2
    for char in reversed(barcode[:4] + barcode[5:]):
        total += int(char) * weight
        weight = 2 if weight == 9 else weight + 1
    value = 11 - total % 11
    return 1 if value in {0, 10, 11} else value


def factor_for_due_date(due_date: date) -> int:
    return 1000 + (due_date - date(2025, 2, 22)).days


def build_linha_digitavel(
    bank: str,
    currency: str,
    free_field: str,
    factor: int,
    value_cents: int,
) -> tuple[str, str]:
    field1_base = f"{bank}{currency}{free_field[:5]}"
    field2_base = free_field[5:15]
    field3_base = free_field[15:25]
    field1 = f"{field1_base}{_mod10(field1_base)}"
    field2 = f"{field2_base}{_mod10(field2_base)}"
    field3 = f"{field3_base}{_mod10(field3_base)}"
    factor_text = f"{factor:04d}"
    value_text = f"{value_cents:010d}"
    provisional = f"{field1}{field2}{field3}0{factor_text}{value_text}"
    barcode = (
        provisional[0:4]
        + "0"
        + provisional[33:47]
        + provisional[4:9]
        + provisional[10:20]
        + provisional[21:31]
    )
    general = str(_general_dv(barcode))
    line = f"{field1}{field2}{field3}{general}{factor_text}{value_text}"
    barcode = (
        line[0:4]
        + line[32]
        + line[33:47]
        + line[4:9]
        + line[10:20]
        + line[21:31]
    )
    return line, barcode


def format_linha_digitavel(line: str) -> str:
    return (
        f"{line[0:5]}.{line[5:10]} "
        f"{line[10:15]}.{line[15:21]} "
        f"{line[21:26]}.{line[26:32]} "
        f"{line[32]} "
        f"{line[33:47]}"
    )
