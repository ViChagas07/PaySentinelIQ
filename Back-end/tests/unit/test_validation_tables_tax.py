from decimal import Decimal

from app.services.validation.tax import (
    inss_for,
    irrf_candidates,
    table_versions,
)


def test_inss_table_values():
    assert inss_for(Decimal("1621.00"), "01/2026") == Decimal("121.58")
    assert inss_for(Decimal("2000.00"), "01/2026") == Decimal("155.69")
    assert inss_for(Decimal("5000.00"), "01/2026") == Decimal("501.51")
    assert inss_for(Decimal("10000.00"), "01/2026") == Decimal("988.09")
    assert inss_for(Decimal("10000.00"), "01/2025") == "unsupported"


def _candidate(
    candidates,
    method: str,
):
    assert candidates != "unsupported"
    return next(item for item in candidates if item[0] == method)


def test_irrf_candidates_with_reduction_values():
    first = _candidate(
        irrf_candidates("6000.00", None, 0, "5392.80", "01/2026"),
        "base_impressa",
    )
    assert first[1] == Decimal("394.54")
    assert first[2]["tabela"] == Decimal("574.29")
    assert first[2]["reducao"] == Decimal("179.75")

    second = _candidate(
        irrf_candidates("6500.00", None, 0, "5788.49", "01/2026"),
        "base_impressa",
    )
    assert second[1] == Decimal("569.92")
    assert second[2]["tabela"] == Decimal("683.10")
    assert second[2]["reducao"] == Decimal("113.18")

    third = _candidate(
        irrf_candidates("5892.33", None, 0, "5257.80", "01/2026"),
        "base_impressa",
    )
    assert third[1] == Decimal("343.07")
    assert third[2]["tabela"] == Decimal("537.16")
    assert third[2]["reducao"] == Decimal("194.09")

    fourth = _candidate(
        irrf_candidates("4500.00", None, 0, "3892.80", "01/2026"),
        "base_impressa",
    )
    assert fourth[1] == Decimal("0.00")
    assert fourth[2]["tabela"] == Decimal("200.39")
    assert fourth[2]["reducao"] == Decimal("200.39")


def test_irrf_above_reduction_limit_has_no_reduction():
    candidates = irrf_candidates("8000.00", None, 0, None, "01/2026")
    assert candidates != "unsupported"
    assert all(item[2]["reducao"] == Decimal("0.00") for item in candidates)


def test_irrf_before_reduction_and_unsupported():
    candidates = irrf_candidates("5000.00", None, 0, None, "06/2025")
    assert candidates != "unsupported"
    assert all(item[2]["reducao"] == Decimal("0.00") for item in candidates)
    assert irrf_candidates("5000.00", None, 0, None, "01/2027") == "unsupported"


def test_table_versions():
    versions = table_versions("01/2026")
    assert versions["inss"] == "INSS_2026"
    assert versions["irrf"] == "IRRF_2025_05"
    assert versions["reducao"] == "IRRF_REDUCAO_2026"
    assert table_versions("01/2025")["inss"] == "unsupported"
