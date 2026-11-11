from datetime import date
from decimal import Decimal

import pytest

from app.services.extraction.dates import parse_competence, parse_date
from app.services.extraction.numbers import parse_amount


@pytest.mark.parametrize(
    ("raw", "lang", "value", "currency", "ambiguous"),
    [
        ("R$ 1.234,56", "pt", Decimal("1234.56"), "BRL", False),
        ("1.234,56", "pt", Decimal("1234.56"), None, False),
        ("1,234.56", "en", Decimal("1234.56"), None, False),
        ("1234.56", "en", Decimal("1234.56"), None, False),
        ("1 234,56", "pt", Decimal("1234.56"), None, False),
        ("BRL 1.234,56", "pt", Decimal("1234.56"), "BRL", False),
        ("(1.234,56)", "pt", Decimal("-1234.56"), None, False),
        ("1.234,56-", "pt", Decimal("-1234.56"), None, False),
        ("1.234", "pt", Decimal("1234"), None, True),
        ("1.234", "en", Decimal("1.234"), None, True),
        ("1,234", "pt", Decimal("1.234"), None, True),
        ("1,234", "en", Decimal("1234"), None, True),
        ("1.234.567", "pt", Decimal("1234567"), None, False),
        ("1.234,5", "pt", Decimal("1234.5"), None, False),
        ("1,234.5", "en", Decimal("1234.5"), None, False),
        ("1.234.56", "pt", Decimal("1234.56"), None, True),
        ("1 234", "pt", Decimal("1234"), None, True),
    ],
)
def test_parse_amount(raw, lang, value, currency, ambiguous):
    parsed = parse_amount(raw, lang)

    assert parsed.value == value
    assert parsed.currency == currency
    assert parsed.ambiguous is ambiguous


def test_parse_amount_rejects_invalid_values():
    with pytest.raises(ValueError):
        parse_amount("not a number")

    with pytest.raises(ValueError):
        parse_amount("")


@pytest.mark.parametrize(
    ("raw", "lang", "value", "ambiguous"),
    [
        ("20/01/2026", "pt", date(2026, 1, 20), False),
        ("20-01-2026", "pt", date(2026, 1, 20), False),
        ("20.01.2026", "pt", date(2026, 1, 20), False),
        ("20/01/26", "pt", date(2026, 1, 20), False),
        ("2026-01-20", "en", date(2026, 1, 20), False),
        ("01/02/2026", "pt", date(2026, 2, 1), True),
        ("13/02/2026", "pt", date(2026, 2, 13), False),
        ("02/13/2026", "en", date(2026, 2, 13), False),
        ("15 de janeiro de 2026", "pt", date(2026, 1, 15), False),
        ("15 enero 2026", "es", date(2026, 1, 15), False),
        ("15 January 2026", "en", date(2026, 1, 15), False),
        ("January 15, 2026", "en", date(2026, 1, 15), False),
        ("Jan-2026", "en", date(2026, 1, 1), False),
        ("Janeiro/2026", "pt", date(2026, 1, 1), False),
        ("enero 2026", "es", date(2026, 1, 1), False),
        ("jan/2026", "en", date(2026, 1, 1), False),
    ],
)
def test_parse_date(raw, lang, value, ambiguous):
    parsed = parse_date(raw, lang)

    assert parsed.value == value
    assert parsed.ambiguous is ambiguous


def test_parse_date_rejects_invalid_or_month_first_without_en():
    with pytest.raises(ValueError):
        parse_date("31/02/2026", "pt")

    with pytest.raises(ValueError):
        parse_date("02/13/2026", "pt")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("01/2026", (2026, 1)),
        ("Janeiro/2026", (2026, 1)),
        ("Jan-2026", (2026, 1)),
        ("2026-01", (2026, 1)),
    ],
)
def test_parse_competence(raw, expected):
    assert parse_competence(raw) == expected
