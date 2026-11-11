from app.services.validation.febraban import _general_dv, _mod10


def build_linha_digitavel(
    *,
    bank: str = "001",
    currency: str = "9",
    free: str = "12345",
    field2_base: str = "0123456789",
    field3_base: str = "1234567890",
    factor: int = 9999,
    value_cents: int = 123456,
) -> str:
    field1_base = f"{bank}{currency}{free}"
    field2 = f"{field2_base}{_mod10(field2_base)}"
    field3 = f"{field3_base}{_mod10(field3_base)}"
    factor_text = f"{factor:04d}"
    value_text = f"{value_cents:010d}"
    provisional = (
        f"{field1_base}{_mod10(field1_base)}"
        f"{field2}{field3}0{factor_text}{value_text}"
    )
    barcode = (
        provisional[0:4]
        + "0"
        + provisional[33:47]
        + provisional[4:9]
        + provisional[10:20]
        + provisional[21:31]
    )
    general = str(_general_dv(barcode))
    return (
        f"{field1_base}{_mod10(field1_base)}"
        f"{field2}{field3}{general}{factor_text}{value_text}"
    )


def first_field_dv_from_line(line: str) -> int:
    return _mod10(line[0:9])
