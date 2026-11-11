from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.services.extraction.text_utils import fold, normalize_text

_MONTHS: dict[str, int] = {
    "janeiro": 1,
    "jan": 1,
    "fevereiro": 2,
    "fev": 2,
    "marco": 3,
    "mar": 3,
    "abril": 4,
    "abr": 4,
    "maio": 5,
    "mai": 5,
    "junho": 6,
    "jun": 6,
    "julho": 7,
    "jul": 7,
    "agosto": 8,
    "ago": 8,
    "setembro": 9,
    "set": 9,
    "outubro": 10,
    "out": 10,
    "novembro": 11,
    "nov": 11,
    "dezembro": 12,
    "dez": 12,
    "enero": 1,
    "ene": 1,
    "febrero": 2,
    "feb": 2,
    "marzo": 3,
    "mayo": 5,
    "may": 5,
    "junio": 6,
    "julio": 7,
    "septiembre": 9,
    "setiembre": 9,
    "sep": 9,
    "octubre": 10,
    "oct": 10,
    "noviembre": 11,
    "diciembre": 12,
    "dic": 12,
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "june": 6,
    "july": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sept": 9,
    "october": 10,
    "november": 11,
    "december": 12,
    "dec": 12,
}


@dataclass(frozen=True)
class NormalizedDate:
    value: date
    raw: str
    ambiguous: bool


def _month_from_name(name: str) -> int | None:
    cleaned = name.strip().strip(".").lower()
    return _MONTHS.get(cleaned)


def _expand_year(raw_year: str) -> int:
    year = int(raw_year)
    if len(raw_year) == 2:
        return 2000 + year if year <= 68 else 1900 + year
    return year


def _make_date(year: int, month: int, day: int, raw: str, ambiguous: bool) -> NormalizedDate:
    try:
        value = date(year, month, day)
    except ValueError as exc:
        raise ValueError(f"Invalid date: {raw!r}") from exc
    return NormalizedDate(value=value, raw=raw, ambiguous=ambiguous)


def parse_date(
    raw: str,
    lang_hint: str | None = None,
) -> NormalizedDate:
    text = normalize_text(raw)
    if not text:
        raise ValueError("Empty date")

    year_first = re.fullmatch(
        r"(\d{4})[./-](\d{1,2})[./-](\d{1,2})",
        text,
    )
    if year_first:
        year, month, day = (int(part) for part in year_first.groups())
        return _make_date(year, month, day, raw, False)

    numeric = re.fullmatch(
        r"(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})",
        text,
    )
    if numeric:
        first, second, year_text = numeric.groups()
        first_int = int(first)
        second_int = int(second)
        year = _expand_year(year_text)
        lang = (lang_hint or "").strip().lower()

        if first_int > 12:
            return _make_date(year, second_int, first_int, raw, False)
        if second_int > 12:
            if lang != "en":
                raise ValueError(
                    f"Ambiguous date interpreted as month-first: {raw!r}"
                )
            return _make_date(year, first_int, second_int, raw, False)
        return _make_date(year, second_int, first_int, raw, True)

    folded = fold(text).replace("º", "").replace("ª", "")
    folded = re.sub(r"\b(?:de|del|of)\b", " ", folded)
    folded = " ".join(folded.split())

    day_month_year = re.fullmatch(
        r"(\d{1,2})[\s./-]*([a-z]+)[\s./-]*(\d{4})",
        folded,
    )
    if day_month_year:
        day = int(day_month_year.group(1))
        month_value = _month_from_name(day_month_year.group(2))
        year = int(day_month_year.group(3))
        if month_value is None:
            raise ValueError(f"Unknown month in date: {raw!r}")
        return _make_date(year, month_value, day, raw, False)

    month_day_year = re.fullmatch(
        r"([a-z]+)[\s./-]+(\d{1,2})(?:,)?[\s./-]+(\d{4})",
        folded,
    )
    if month_day_year:
        month_value = _month_from_name(month_day_year.group(1))
        day = int(month_day_year.group(2))
        year = int(month_day_year.group(3))
        if month_value is None:
            raise ValueError(f"Unknown month in date: {raw!r}")
        return _make_date(year, month_value, day, raw, False)

    month_year = re.fullmatch(
        r"([a-z]+)[\s./-]*(\d{4})",
        folded,
    )
    if month_year:
        month_value = _month_from_name(month_year.group(1))
        year = int(month_year.group(2))
        if month_value is None:
            raise ValueError(f"Unknown month in date: {raw!r}")
        return _make_date(year, month_value, 1, raw, False)

    year_month = re.fullmatch(
        r"(\d{4})[\s./-]+([a-z]+)",
        folded,
    )
    if year_month:
        year = int(year_month.group(1))
        month_value = _month_from_name(year_month.group(2))
        if month_value is None:
            raise ValueError(f"Unknown month in date: {raw!r}")
        return _make_date(year, month_value, 1, raw, False)

    raise ValueError(f"Unrecognized date: {raw!r}")


def parse_competence(raw: str) -> tuple[int, int]:
    text = normalize_text(raw)
    if not text:
        raise ValueError("Empty competence")

    numeric = re.fullmatch(r"(\d{1,2})[./-](\d{4})", text)
    if numeric:
        month, year = int(numeric.group(1)), int(numeric.group(2))
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid competence month: {raw!r}")
        return year, month

    year_first = re.fullmatch(r"(\d{4})[./-](\d{1,2})", text)
    if year_first:
        year, month = int(year_first.group(1)), int(year_first.group(2))
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid competence month: {raw!r}")
        return year, month

    folded = fold(text).replace("º", "").replace("ª", "")
    folded = " ".join(folded.split())

    month_year = re.fullmatch(r"([a-z]+)[\s./-]*(\d{4})", folded)
    if month_year:
        month_value = _month_from_name(month_year.group(1))
        if month_value is None:
            raise ValueError(f"Unknown competence month: {raw!r}")
        return int(month_year.group(2)), month_value

    year_month = re.fullmatch(r"(\d{4})[\s./-]+([a-z]+)", folded)
    if year_month:
        month_value = _month_from_name(year_month.group(2))
        if month_value is None:
            raise ValueError(f"Unknown competence month: {raw!r}")
        return int(year_month.group(1)), month_value

    raise ValueError(f"Unrecognized competence: {raw!r}")
