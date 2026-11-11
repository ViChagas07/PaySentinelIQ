from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.services.extraction.dates import parse_date

FACTOR_BASE = date(1997, 10, 7)
NEW_FACTOR_BASE = date(2025, 2, 22)
WINDOW_PAST_DAYS = 3000
WINDOW_FUTURE_DAYS = 5500


def _digits(value: str | None) -> str:
    return "".join(char for char in (value or "") if char.isdigit())


def _mod10(digits: str) -> int:
    total = 0
    weight = 2
    for char in reversed(digits):
        product = int(char) * weight
        total += product // 10 + product % 10
        weight = 1 if weight == 2 else 2
    return (10 - total % 10) % 10


def _general_dv(barcode: str) -> int:
    digits = barcode[:4] + barcode[5:]
    total = 0
    weight = 2
    for char in reversed(digits):
        total += int(char) * weight
        weight = 2 if weight == 9 else weight + 1
    dv = 11 - total % 11
    return 1 if dv in {0, 10, 11} else dv


def _factor_window(today: date) -> tuple[date, date]:
    return (
        today - timedelta(days=WINDOW_PAST_DAYS),
        today + timedelta(days=WINDOW_FUTURE_DAYS),
    )


def _decode_factor(
    factor: int,
    today: date,
) -> tuple[str, date | None]:
    if factor == 0:
        return "sem_vencimento", None

    candidates: list[date] = []
    first = FACTOR_BASE + timedelta(days=factor)
    candidates.append(first)
    if factor >= 1000:
        candidates.append(
            NEW_FACTOR_BASE + timedelta(days=factor - 1000)
        )

    start, end = _factor_window(today)
    valid = sorted({candidate for candidate in candidates if start <= candidate <= end})
    if len(valid) == 1:
        return "ok", valid[0]
    if not valid:
        return "fora_da_janela", None
    return "ambiguo", None


def decode_linha_digitavel(
    linha_digitavel: str,
    today: date | None = None,
) -> dict[str, Any]:
    line = _digits(linha_digitavel)
    if len(line) == 48 and line.startswith("8"):
        return {
            "status": "arrecadacao",
            "digits": line,
            "length": 48,
        }
    if len(line) != 47:
        return {
            "status": "formato_invalido",
            "digits": line,
            "length": len(line),
        }

    field1 = line[0:10]
    field2 = line[10:21]
    field3 = line[21:32]
    general_dv = int(line[32])
    factor = int(line[33:37])
    cents = int(line[37:47])
    barcode = (
        line[0:4]
        + line[32]
        + line[33:47]
        + line[4:9]
        + line[10:20]
        + line[21:31]
    )
    factor_status, due_date = _decode_factor(
        factor,
        today or date.today(),
    )
    value = (Decimal(cents) / Decimal("100")).quantize(Decimal("0.01"))

    return {
        "status": "ok",
        "digits": line,
        "length": 47,
        "banco": line[0:3],
        "moeda": line[3],
        "campo1": field1,
        "campo2": field2,
        "campo3": field3,
        "dv1": line[9],
        "dv2": line[20],
        "dv3": line[31],
        "dv_geral": line[32],
        "dv_geral_calculado": _general_dv(barcode),
        "dv_geral_valido": _general_dv(barcode) == general_dv,
        "campo_dvs_validos": {
            "campo1": _mod10(line[0:9]) == int(line[9]),
            "campo2": _mod10(line[10:20]) == int(line[20]),
            "campo3": _mod10(line[21:31]) == int(line[31]),
        },
        "codigo_barras": barcode,
        "fator": factor,
        "status_fator": factor_status,
        "vencimento": due_date.isoformat() if due_date is not None else None,
        "valor": str(value),
    }


def _evidence(
    code: str,
    severity: Severity,
    description: str,
    metadata: dict[str, Any],
    rule_reference: str,
) -> Evidence:
    return Evidence(
        code=code,
        description=description,
        severity=severity,
        source=EvidenceSource.DETERMINISTIC,
        confidence=1.0,
        category="boleto",
        rule_reference=rule_reference,
        metadata=metadata,
    )


def _printed_date(value: date | str | None) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return parse_date(str(value)).value
    except ValueError:
        return None


def _printed_decimal(value: Decimal | int | float | str | None) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _bank_candidates(
    text: str,
    codigo_banco: str | None = None,
) -> list[str]:
    header = "\n".join(text.splitlines()[:15])
    candidates: list[str] = [
        match.group(1)
        for match in re.finditer(r"\b(\d{3})\s*-\s*\d\b", header)
    ]
    candidates.extend(
        match.group(1)
        for match in re.finditer(
            r"(?:banco|c[oó]digo\s*(?:do\s*)?banco)\s*:?\s*(\d{3})",
            header,
            re.IGNORECASE,
        )
    )
    return sorted(set(candidates))


def validate_boleto(
    *,
    linha_digitavel: str | None,
    valor_nominal: Decimal | int | float | str | None,
    data_vencimento: date | str | None,
    codigo_barras: str | None,
    codigo_banco: str | None,
    text: str,
    today: date | None = None,
) -> tuple[list[Evidence], dict[str, Any], list[str]]:
    skipped: list[str] = []
    if not linha_digitavel:
        return [], {"status": "missing_linha_digitavel"}, [
            "missing_linha_digitavel"
        ]

    decoded = decode_linha_digitavel(linha_digitavel, today=today)
    if decoded["status"] == "arrecadacao":
        evidence = _evidence(
            "BOLETO_ARRECADACAO_UNSUPPORTED",
            Severity.INFO,
            "Linha de arrecadação de 48 dígitos não é validada nesta versão.",
            {"linha": decoded["digits"]},
            "FEBRABAN/ABBC arrecadação",
        )
        return [evidence], decoded, skipped
    if decoded["status"] != "ok":
        return [], decoded, ["linha_formato_invalido"]

    evidences: list[Evidence] = []
    if not decoded["dv_geral_valido"]:
        evidences.append(
            _evidence(
                "BOLETO_GENERAL_DV_INVALID",
                Severity.CRITICAL,
                "Dígito verificador geral do código de barras não confere.",
                {
                    "dv_informado": decoded["dv_geral"],
                    "dv_calculado": decoded["dv_geral_calculado"],
                },
                "FEBRABAN módulo 11",
            )
        )

    if decoded["moeda"] != "9":
        evidences.append(
            _evidence(
                "BOLETO_CURRENCY_CODE_INVALID",
                Severity.MEDIUM,
                f"Código de moeda {decoded['moeda']} difere de 9 (Real).",
                {"moeda": decoded["moeda"]},
                "FEBRABAN código de barras",
            )
        )

    encoded_value = Decimal(decoded["valor"])
    printed_value = _printed_decimal(valor_nominal)
    value_match: bool | None = None
    if printed_value is None:
        skipped.append("missing_valor_nominal")
    elif encoded_value > 0:
        value_match = printed_value == encoded_value
        if not value_match:
            evidences.append(
                _evidence(
                    "BOLETO_AMOUNT_MISMATCH",
                    Severity.CRITICAL,
                    "Valor nominal impresso difere do valor codificado.",
                    {
                        "impresso": str(printed_value),
                        "codificado": str(encoded_value),
                    },
                    "FEBRABAN valor codificado",
                )
            )
    else:
        skipped.append("valor_livre")

    printed_due = _printed_date(data_vencimento)
    due_match: bool | None = None
    if decoded["status_fator"] == "ok":
        if printed_due is None:
            skipped.append("missing_data_vencimento")
        else:
            decoded_due = date.fromisoformat(decoded["vencimento"])
            due_match = printed_due == decoded_due
            if not due_match:
                evidences.append(
                    _evidence(
                        "BOLETO_DUE_DATE_MISMATCH",
                        Severity.HIGH,
                        "Vencimento impresso difere do fator codificado.",
                        {
                            "impresso": printed_due.isoformat(),
                            "codificado": decoded_due.isoformat(),
                            "fator": decoded["fator"],
                        },
                        "FEBRABAN fator de vencimento",
                    )
                )
    elif decoded["status_fator"] == "fora_da_janela":
        evidences.append(
            _evidence(
                "BOLETO_DUE_DATE_UNRESOLVABLE",
                Severity.LOW,
                "Fator de vencimento fora da janela de datas plausíveis.",
                {"fator": decoded["fator"]},
                "FEBRABAN fator de vencimento",
            )
        )
    else:
        skipped.append(f"fator_{decoded['status_fator']}")

    bank_candidates = _bank_candidates(text, codigo_banco)
    bank_match: bool | None = None
    if not bank_candidates:
        skipped.append("missing_banco_impresso")
    else:
        bank_match = decoded["banco"] in bank_candidates
        if not bank_match:
            evidences.append(
                _evidence(
                    "BOLETO_BANK_MISMATCH",
                    Severity.CRITICAL,
                    "Banco impresso difere do banco codificado.",
                    {
                        "impresso": bank_candidates,
                        "codificado": decoded["banco"],
                    },
                    "FEBRABAN código do banco",
                )
            )

    printed_barcode = _digits(codigo_barras)
    barcode_match: bool | None = None
    if len(printed_barcode) != 44:
        skipped.append("missing_codigo_barras")
    else:
        barcode_match = printed_barcode == decoded["codigo_barras"]
        if not barcode_match:
            evidences.append(
                _evidence(
                    "BOLETO_BARCODE_MISMATCH",
                    Severity.HIGH,
                    "Código de barras extraído difere do convertido da linha.",
                    {
                        "impresso": printed_barcode,
                        "codificado": decoded["codigo_barras"],
                    },
                    "FEBRABAN código de barras",
                )
            )

    decoded["comparisons"] = {
        "valor": {
            "impresso": str(printed_value) if printed_value is not None else None,
            "codificado": str(encoded_value),
            "match": value_match,
        },
        "vencimento": {
            "impresso": printed_due.isoformat() if printed_due else None,
            "codificado": decoded["vencimento"],
            "match": due_match,
        },
        "banco": {
            "impresso": bank_candidates,
            "codificado": decoded["banco"],
            "match": bank_match,
        },
        "codigo_barras": {
            "impresso": printed_barcode or None,
            "codificado": decoded["codigo_barras"],
            "match": barcode_match,
        },
    }
    return evidences, decoded, skipped
