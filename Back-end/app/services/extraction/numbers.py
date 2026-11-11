from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

_CURRENCY_PATTERNS = (
    (re.compile(r"R\$|\bBRL\b", re.IGNORECASE), "BRL"),
    (re.compile(r"US\$|\bUSD\b", re.IGNORECASE), "USD"),
    (re.compile(r"€|\bEUR\b", re.IGNORECASE), "EUR"),
    (re.compile(r"\$"), "USD"),
)


@dataclass(frozen=True)
class NormalizedNumber:
    value: Decimal
    raw: str
    currency: str | None
    ambiguous: bool


def _detect_currency(raw: str) -> str | None:
    for pattern, currency in _CURRENCY_PATTERNS:
        if pattern.search(raw):
            return currency
    return None


def _strip_currency(text: str) -> str:
    for pattern, _currency in _CURRENCY_PATTERNS:
        text = pattern.sub(" ", text)
    return text


def _normalize_lang(lang_hint: str | None) -> str:
    if lang_hint is None:
        return "pt"
    normalized = lang_hint.strip().lower()
    return normalized if normalized in {"pt", "es", "en"} else "pt"


def parse_amount(
    raw: str,
    lang_hint: str | None = None,
) -> NormalizedNumber:
    original = raw
    currency = _detect_currency(raw)
    text = _strip_currency(raw).strip()

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1].strip()
    if text.endswith("-"):
        negative = True
        text = text[:-1].strip()
    if text.startswith("-"):
        negative = True
        text = text[1:].strip()
    if text.startswith("+") or text.endswith("+"):
        text = text.strip("+").strip()

    had_space_separator = bool(re.search(r"\d\s+\d", text))
    text = re.sub(r"[\s\u00a0]+", "", text)
    if not text or re.search(r"[^\d.,]", text):
        raise ValueError(f"Invalid monetary value: {original!r}")

    lang = _normalize_lang(lang_hint)
    ambiguous = False
    digits: str

    if "," in text and "." in text:
        last_comma = text.rfind(",")
        last_dot = text.rfind(".")
        if last_comma > last_dot:
            integer = text[:last_comma].replace(".", "")
            fraction = text[last_comma + 1 :]
        else:
            integer = text[:last_dot].replace(",", "")
            fraction = text[last_dot + 1 :]
        if not integer or not fraction:
            raise ValueError(f"Invalid monetary value: {original!r}")
        digits = f"{integer}.{fraction}"
    elif "," in text or "." in text:
        separator = "," if "," in text else "."
        parts = text.split(separator)
        if any(part == "" for part in parts):
            raise ValueError(f"Invalid monetary value: {original!r}")

        if len(parts) == 2:
            integer, fraction = parts
            if len(fraction) == 2:
                digits = f"{integer}.{fraction}"
            elif len(fraction) == 3:
                ambiguous = True
                if separator == ",":
                    if lang in {"pt", "es"}:
                        digits = f"{integer}.{fraction}"
                    else:
                        digits = f"{integer}{fraction}"
                else:
                    if lang == "en":
                        digits = f"{integer}.{fraction}"
                    else:
                        digits = f"{integer}{fraction}"
            else:
                digits = f"{integer}.{fraction}"
        else:
            if all(len(part) == 3 for part in parts[1:]):
                digits = "".join(parts)
            else:
                digits = "".join(parts[:-1]) + "." + parts[-1]
                ambiguous = True
    else:
        digits = text
        ambiguous = had_space_separator

    try:
        value = Decimal(digits)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid monetary value: {original!r}") from exc
    if negative:
        value = -value

    return NormalizedNumber(
        value=value,
        raw=original,
        currency=currency,
        ambiguous=ambiguous,
    )
