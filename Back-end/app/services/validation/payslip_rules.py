from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from typing import Any

from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.services.extraction.dates import parse_date
from app.services.validation.tables import INSS_2026
from app.services.validation.tax import (
    inss_for,
    irrf_candidates,
    table_versions,
)

NET_TOLERANCE = Decimal("0.02")
NET_CRITICAL_THRESHOLD = Decimal("1.00")
INSS_TOLERANCE = Decimal("0.10")
IRRF_TOLERANCE = Decimal("1.00")
FGTS_TOLERANCE = Decimal("0.10")
DEDUCTIONS_TOLERANCE = Decimal("0.10")
BASE_TOLERANCE = Decimal("0.10")

INSS_MISMATCH_MEDIUM_LIMIT = Decimal("5.00")
IRRF_HIGH_DELTA = Decimal("50.00")
IRRF_HIGH_RATIO = Decimal("0.20")

FGTS_RATES = (Decimal("0.08"), Decimal("0.02"), Decimal("0.112"))


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _int_value(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _period(value: Any) -> tuple[int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"(\d{1,2})[/-](\d{4})", str(value).strip())
    if not match:
        return None
    month, year = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        return None
    return year, month


def _date_value(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return parse_date(str(value)).value
    except ValueError:
        return None


def _cpf_valid(value: Any) -> bool:
    digits = "".join(char for char in str(value or "") if char.isdigit())
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    first = sum(int(digits[index]) * (10 - index) for index in range(9))
    first_dv = 0 if first % 11 < 2 else 11 - first % 11
    if first_dv != int(digits[9]):
        return False
    second = sum(int(digits[index]) * (11 - index) for index in range(10))
    second_dv = 0 if second % 11 < 2 else 11 - second % 11
    return second_dv == int(digits[10])


def _cnpj_valid(value: Any) -> bool:
    from app.ai_agents.tools.brazil_financial_tools import (
        _parse_cnpj,
        _validate_cnpj_checksum,
    )

    return _validate_cnpj_checksum(_parse_cnpj(str(value or "")))


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
        category="payroll",
        rule_reference=rule_reference,
        metadata=metadata,
    )


def _downgrade(severity: Severity) -> Severity:
    if severity == Severity.HIGH:
        return Severity.MEDIUM
    if severity == Severity.MEDIUM:
        return Severity.LOW
    return severity


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def validate_payslip(
    fields: dict[str, Any],
    today: date | None = None,
) -> tuple[list[Evidence], dict[str, Any], list[str]]:
    current = today or date.today()
    evidences: list[Evidence] = []
    skipped: list[str] = []

    bruto = _decimal(fields.get("salario_bruto"))
    descontos = _decimal(fields.get("total_descontos"))
    liquido = _decimal(fields.get("salario_liquido"))
    inss_printed = _decimal(fields.get("inss"))
    irrf_printed = _decimal(fields.get("irrf"))
    fgts_printed = _decimal(fields.get("fgts"))
    base_inss = _decimal(fields.get("base_inss"))
    base_irrf = _decimal(fields.get("base_irrf"))
    base_fgts = _decimal(fields.get("base_fgts"))
    dependentes = _int_value(fields.get("dependentes"))
    periodo_text = fields.get("periodo")
    periodo = _period(periodo_text)
    admissao = _date_value(fields.get("data_admissao"))
    cpf = fields.get("cpf")
    cnpj = fields.get("cnpj")

    if bruto is not None and descontos is not None and liquido is not None:
        expected_liquid = bruto - descontos
        difference = abs(liquido - expected_liquid)
        if difference > NET_TOLERANCE:
            severity = (
                Severity.CRITICAL
                if difference > NET_CRITICAL_THRESHOLD
                else Severity.MEDIUM
            )
            evidences.append(
                _evidence(
                    "PAYSLIP_NET_MISMATCH",
                    severity,
                    "Líquido impresso não fecha com proventos menos descontos.",
                    {
                        "liquido_impresso": str(liquido),
                        "liquido_calculado": str(expected_liquid),
                        "diferenca": str(difference),
                    },
                    "Aritmética de contracheque",
                )
            )
    else:
        skipped.append("net:missing_fields")

    if (
        descontos is not None
        and inss_printed is not None
        and irrf_printed is not None
    ):
        if descontos < inss_printed + irrf_printed - DEDUCTIONS_TOLERANCE:
            evidences.append(
                _evidence(
                    "PAYSLIP_DEDUCTIONS_INCONSISTENT",
                    Severity.HIGH,
                    "Total de descontos é menor que INSS + IRRF.",
                    {
                        "total_descontos": str(descontos),
                        "inss_irrf": str(inss_printed + irrf_printed),
                    },
                    "Aritmética de contracheque",
                )
            )
    else:
        skipped.append("deductions:missing_fields")

    versions = table_versions(str(periodo_text or ""))
    tax_supported = periodo is not None and versions["inss"] != "unsupported"
    irrf_supported = periodo is not None and versions["irrf"] != "unsupported"
    tax_rules_supported = tax_supported and irrf_supported
    inss_expected: Decimal | None = None
    irrf_values: list[tuple[str, Decimal, dict[str, Any]]] = []
    fgts_expected: list[tuple[str, Decimal]] = []

    if periodo is not None and not tax_rules_supported:
        evidences.append(
            _evidence(
                "PAYSLIP_TAX_TABLE_UNSUPPORTED",
                Severity.INFO,
                "Competência sem tabela de INSS/IRRF suportada.",
                {"competencia": str(periodo_text or "")},
                "Tabelas versionadas",
            )
        )
        skipped.append("inss_irrf:tax_table_unsupported")
    elif periodo is None:
        skipped.append("inss_irrf:missing_period")

    if tax_rules_supported:
        if inss_printed is None:
            skipped.append("inss:missing_inss")
        else:
            base = base_inss if base_inss is not None else bruto
            presumed = base_inss is None
            if base is None:
                skipped.append("inss:missing_base")
            else:
                expected = inss_for(base, str(periodo_text or ""))
                if expected == "unsupported":
                    skipped.append("inss:tax_table_unsupported")
                else:
                    inss_expected = expected
                    if inss_printed > INSS_2026.max_contribution + INSS_TOLERANCE:
                        evidences.append(
                            _evidence(
                                "PAYSLIP_INSS_ABOVE_CEILING",
                                Severity.CRITICAL,
                                "INSS impresso acima do teto de contribuição.",
                                {
                                    "inss_impresso": str(inss_printed),
                                    "teto": str(INSS_2026.max_contribution),
                                },
                                "Portaria MPS/MF 13/2026",
                            )
                        )
                    delta = abs(inss_printed - expected)
                    if delta > INSS_TOLERANCE:
                        severity = (
                            Severity.MEDIUM
                            if delta <= INSS_MISMATCH_MEDIUM_LIMIT
                            else Severity.HIGH
                        )
                        if presumed:
                            severity = _downgrade(severity)
                        evidences.append(
                            _evidence(
                                "PAYSLIP_INSS_MISMATCH",
                                severity,
                                "INSS impresso difere do cálculo progressivo.",
                                {
                                    "inss_impresso": str(inss_printed),
                                    "inss_esperado": str(expected),
                                    "delta": str(delta),
                                    "base": str(base),
                                    "base_presumida": presumed,
                                },
                                "Portaria MPS/MF 13/2026",
                            )
                        )

    if tax_rules_supported and irrf_printed is not None:
        if bruto is None:
            skipped.append("irrf:missing_bruto")
        else:
            candidates = irrf_candidates(
                bruto,
                inss_printed,
                dependentes,
                base_irrf,
                str(periodo_text or ""),
            )
            if candidates == "unsupported":
                skipped.append("irrf:tax_table_unsupported")
            else:
                irrf_values = candidates
                nearest = min(
                    candidates,
                    key=lambda candidate: abs(irrf_printed - candidate[1]),
                )
                delta = abs(irrf_printed - nearest[1])
                if delta > IRRF_TOLERANCE:
                    severity = Severity.MEDIUM
                    if (
                        delta > IRRF_HIGH_DELTA
                        and delta > IRRF_HIGH_RATIO * abs(nearest[1])
                    ):
                        severity = Severity.HIGH
                    if dependentes is None:
                        severity = _downgrade(severity)
                    evidences.append(
                        _evidence(
                            "PAYSLIP_IRRF_MISMATCH",
                            severity,
                            "IRRF impresso não é consistente com nenhum método.",
                            {
                                "irrf_impresso": str(irrf_printed),
                                "metodo": nearest[0],
                                "irrf_esperado": str(nearest[1]),
                                "delta": str(delta),
                                "dependentes_presumidos": dependentes is None,
                            },
                            "Tabela IRRF vigente desde maio/2025 + Lei 15.270/2025",
                        )
                    )
    elif irrf_printed is None:
        skipped.append("irrf:missing_irrf")

    if fgts_printed is None:
        skipped.append("fgts:missing_fgts")
    else:
        base = base_fgts if base_fgts is not None else bruto
        if base is None:
            skipped.append("fgts:missing_base")
        else:
            fgts_expected = [
                (
                    str(rate),
                    (base * rate).quantize(Decimal("0.01")),
                )
                for rate in FGTS_RATES
            ]
            matched = any(
                abs(fgts_printed - expected) <= FGTS_TOLERANCE
                for _rate, expected in fgts_expected
            )
            if not matched:
                evidences.append(
                    _evidence(
                        "PAYSLIP_FGTS_MISMATCH",
                        Severity.MEDIUM,
                        "FGTS impresso não bate com 8%, 2% ou 11,2% da base.",
                        {
                            "fgts_impresso": str(fgts_printed),
                            "base": str(base),
                            "esperados": {
                                rate: str(expected)
                                for rate, expected in fgts_expected
                            },
                        },
                        "Regras de FGTS",
                    )
                )

    if bruto is not None:
        exceeded = [
            name
            for name, value in (
                ("base_inss", base_inss),
                ("base_fgts", base_fgts),
            )
            if value is not None and value > bruto + BASE_TOLERANCE
        ]
        if exceeded:
            evidences.append(
                _evidence(
                    "PAYSLIP_BASE_EXCEEDS_GROSS",
                    Severity.MEDIUM,
                    "Base de cálculo maior que o total de proventos.",
                    {
                        "campos": exceeded,
                        "salario_bruto": str(bruto),
                    },
                    "Aritmética de contracheque",
                )
            )

    if cpf:
        if not _cpf_valid(cpf):
            evidences.append(
                _evidence(
                    "PAYSLIP_CPF_INVALID",
                    Severity.HIGH,
                    "CPF impresso possui dígitos verificadores inválidos.",
                    {"cpf": str(cpf)},
                    "Módulo 11 CPF",
                )
            )
    else:
        skipped.append("cpf:missing_cpf")

    if cnpj:
        if not _cnpj_valid(cnpj):
            evidences.append(
                _evidence(
                    "PAYSLIP_CNPJ_INVALID",
                    Severity.HIGH,
                    "CNPJ impresso possui dígitos verificadores inválidos.",
                    {"cnpj": str(cnpj)},
                    "Módulo 11 CNPJ",
                )
            )
    else:
        skipped.append("cnpj:missing_cnpj")

    if periodo is None:
        skipped.append("period:missing_or_invalid")
    else:
        current_key = (current.year, current.month)
        if periodo > current_key:
            evidences.append(
                _evidence(
                    "PAYSLIP_PERIOD_FUTURE",
                    Severity.HIGH,
                    "Competência posterior ao mês atual.",
                    {"competencia": str(periodo_text or "")},
                    "Competência de contracheque",
                )
            )
        if admissao is not None and periodo < (admissao.year, admissao.month):
            evidences.append(
                _evidence(
                    "PAYSLIP_PERIOD_BEFORE_ADMISSION",
                    Severity.HIGH,
                    "Competência anterior à data de admissão.",
                    {
                        "competencia": str(periodo_text or ""),
                        "admissao": admissao.isoformat(),
                    },
                    "Competência de contracheque",
                )
            )

    expected_block = {
        "inss_expected": str(inss_expected) if inss_expected is not None else None,
        "irrf_candidates": [
            {
                "method": method,
                "value": str(value),
                "details": details,
            }
            for method, value, details in irrf_values
        ],
        "fgts_expected": [
            {"rate": rate, "value": str(value)}
            for rate, value in fgts_expected
        ],
        "tables": versions,
    }
    return evidences, _json_safe(expected_block), skipped
