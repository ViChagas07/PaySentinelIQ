from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import math
from typing import Any

import numpy as np

from app.services.ai.boleto_analyzer import BANCOS_VALIDOS
from app.services.validation.febraban import decode_linha_digitavel

SEVERITY_ORDINAL = {
    "info": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}
SOURCE_NAMES = (
    "deterministic",
    "heuristic",
    "knowledge_base",
    "brasilapi",
    "ocr",
    "crewai",
    "user",
    "other",
)
FIELDS = (
    "linha_digitavel",
    "codigo_barras",
    "valor_nominal",
    "data_vencimento",
    "codigo_banco",
    "cnpj",
    "cpf",
    "salario_bruto",
    "salario_liquido",
    "total_descontos",
    "inss",
    "irrf",
    "fgts",
    "base_inss",
    "base_irrf",
    "base_fgts",
    "dependentes",
    "periodo",
    "beneficiario",
    "nome_funcionario",
)
FACT_GROUPS = {
    "BOLETO_OVERDUE": "temporal",
    "BOLETO_VENCIDO": "temporal",
    "BOLETO_SEVERELY_OVERDUE": "temporal",
    "DOCUMENT_EXPIRED": "temporal",
    "BOLETO_DUE_DATE_MISMATCH": "temporal",
    "BOLETO_DUE_DATE_UNRESOLVABLE": "temporal",
    "BOLETO_AMOUNT_MISMATCH": "amount",
    "BOLETO_ROUND_AMOUNT": "amount",
    "VALOR_REDONDO_SUSPEITO": "amount",
    "ROUND_AMOUNT_SUSPICIOUS": "amount",
    "BANCO_INVALIDO": "bank",
    "BOLETO_BANK_MISMATCH": "bank",
    "LINHA_DIGITAVEL_FORMATO_INCORRETO": "linha",
    "DIGITO_VERIFICADOR_CAMPO1_INVALIDO": "linha",
    "DIGITO_VERIFICADOR_CAMPO2_INVALIDO": "linha",
    "DIGITO_VERIFICADOR_CAMPO3_INVALIDO": "linha",
    "BOLETO_BARCODE_MISMATCH": "barcode",
    "BOLETO_GENERAL_DV_INVALID": "barcode",
    "BOLETO_CNPJ_MISMATCH": "beneficiary",
    "CNPJ_INVALID_PATTERN": "beneficiary",
    "PAYSLIP_CNPJ_INVALID": "beneficiary",
    "PAYSLIP_CPF_INVALID": "beneficiary",
    "PAYSLIP_NET_MISMATCH": "payslip_net",
    "PAYSLIP_DEDUCTIONS_INCONSISTENT": "payslip_deductions",
    "PAYSLIP_BASE_EXCEEDS_GROSS": "payslip_deductions",
    "PAYSLIP_INSS_MISMATCH": "payslip_inss",
    "PAYSLIP_INSS_ABOVE_CEILING": "payslip_inss",
    "PAYSLIP_IRRF_MISMATCH": "payslip_irrf",
    "PAYSLIP_FGTS_MISMATCH": "payslip_fgts",
    "PAYSLIP_PERIOD_FUTURE": "period",
    "PAYSLIP_PERIOD_BEFORE_ADMISSION": "period",
}
GROUPS = sorted(set(FACT_GROUPS.values()))
RATIOS = (
    "inss_gross",
    "irrf_gross",
    "fgts_gross",
    "deductions_gross",
    "net_gross",
    "net_residual",
    "base_inss_gross",
    "base_irrf_gross",
    "base_fgts_gross",
)
LINE_FEATURES = (
    "line_47",
    "line_status_ok",
    "line_dv_valid",
    "line_bank_valid",
    "amount_line_delta_norm",
    "due_line_delta_days_norm",
    "bank_matches_line",
    "barcode_matches_line",
)
EVIDENCE_FEATURES = (
    "evidence_total",
    "evidence_confidence_mean",
    "evidence_confidence_max",
    "evidence_info",
    "evidence_low",
    "evidence_medium",
    "evidence_high",
    "evidence_critical",
    "evidence_confirmed",
    "evidence_uncertain",
    "evidence_confirmed_material",
    "evidence_confirmed_critical",
    "evidence_uncertain_material",
) + tuple(f"source_{name}" for name in SOURCE_NAMES)

FEATURE_NAMES: list[str] = [
    "document_type_boleto",
    "document_type_payslip",
    "path_is_ocr",
    "path_is_degraded",
    "extraction_confidence",
    "field_present_count",
    "field_coverage",
    "field_missing_count",
    "due_ambiguous",
    "due_locale_inconsistent",
    "warnings_count",
    *[f"has_{field}" for field in FIELDS],
    *RATIOS,
    "due_days_past_norm",
    "due_days_future_norm",
    *LINE_FEATURES,
    *EVIDENCE_FEATURES,
    *[
        f"group_{group}_{kind}"
        for group in GROUPS
        for kind in (
            "count",
            "max_severity",
            "confirmed_material",
            "uncertain_material",
        )
    ],
]

FORBIDDEN_FEATURE_TOKENS = (
    "tamper",
    "sophistication",
    "intended_band",
    "gabarito",
    "seed",
    "document_id",
    "page_text",
    "raw_text",
    "beneficiario_nome",
    "company_name",
    "expected",
)


def _decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _float(value: Any) -> float:
    number = _decimal(value)
    return float(number) if number is not None else math.nan


def _ratio(numerator: Any, denominator: Any) -> float:
    top = _decimal(numerator)
    bottom = _decimal(denominator)
    if top is None or bottom is None or bottom == 0:
        return math.nan
    value = float(top / bottom)
    if not math.isfinite(value):
        return math.nan
    return max(-5.0, min(5.0, value))


def _date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value)
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%d/%m/%Y").date()
    except ValueError:
        return None


def _digits(value: Any) -> str:
    return "".join(char for char in str(value or "") if char.isdigit())


def _present(value: Any) -> int:
    return 0 if value in (None, "", [], {}) else 1


def _is_uncertain(evidence: dict[str, Any]) -> bool:
    return bool((evidence.get("metadata") or {}).get("ocr_uncertain"))


def _line_features(
    extracted: dict[str, Any],
    reference_date: date | None = None,
) -> dict[str, float]:
    features = {
        "line_47": 0.0,
        "line_status_ok": 0.0,
        "line_dv_valid": 0.0,
        "line_bank_valid": 0.0,
        "amount_line_delta_norm": math.nan,
        "due_line_delta_days_norm": math.nan,
        "bank_matches_line": math.nan,
        "barcode_matches_line": math.nan,
    }
    line = _digits(extracted.get("linha_digitavel"))
    if len(line) == 47:
        features["line_47"] = 1.0
    decoded = decode_linha_digitavel(
        extracted.get("linha_digitavel") or "",
        today=reference_date,
    )
    if decoded.get("status") == "ok":
        features["line_status_ok"] = 1.0
        features["line_dv_valid"] = float(
            bool(decoded.get("dv_geral_valido"))
            and all((decoded.get("campo_dvs_validos") or {}).values())
        )
        features["line_bank_valid"] = float(
            str(decoded.get("banco")) in BANCOS_VALIDOS
        )
        amount = _decimal(extracted.get("valor_nominal"))
        line_amount = _decimal(decoded.get("valor"))
        if amount is not None and line_amount is not None:
            features["amount_line_delta_norm"] = min(
                abs(float(amount - line_amount)) / max(abs(float(amount)), 1.0),
                5.0,
            )
        due = _date(extracted.get("data_vencimento"))
        line_due = _date(decoded.get("vencimento"))
        if due is not None and line_due is not None:
            features["due_line_delta_days_norm"] = min(
                abs((due - line_due).days) / 365.0,
                10.0,
            )
        features["bank_matches_line"] = float(
            _digits(extracted.get("codigo_banco"))[:3]
            == str(decoded.get("banco"))
        )
        features["barcode_matches_line"] = float(
            _digits(extracted.get("codigo_barras"))
            == _digits(decoded.get("codigo_barras"))
        )
    return features


def feature_row(
    row: dict[str, Any],
    reference_date: date | None = None,
) -> dict[str, float]:
    extracted = row.get("extracted_fields") or {}
    evidences = row.get("evidences") or []
    doc_type = row.get("document_type", "")
    features: dict[str, float] = {
        "document_type_boleto": float(doc_type == "boleto"),
        "document_type_payslip": float(doc_type != "boleto"),
        "path_is_ocr": float(row.get("path") != "A_native"),
        "path_is_degraded": float(row.get("path") == "C_ocr_degraded"),
        "extraction_confidence": _float(
            extracted.get("extraction_confidence")
        ),
        "due_ambiguous": float(
            bool(extracted.get("data_vencimento_ambiguous"))
        ),
        "due_locale_inconsistent": float(
            bool(extracted.get("data_vencimento_locale_inconsistent"))
        ),
        "warnings_count": float(len(row.get("warnings") or [])),
    }

    present_count = sum(_present(extracted.get(field)) for field in FIELDS)
    features["field_present_count"] = float(present_count)
    features["field_coverage"] = present_count / len(FIELDS)
    features["field_missing_count"] = float(len(FIELDS) - present_count)
    for field in FIELDS:
        features[f"has_{field}"] = float(_present(extracted.get(field)))

    gross = extracted.get("salario_bruto")
    net = extracted.get("salario_liquido")
    deductions = extracted.get("total_descontos")
    features.update(
        {
            "inss_gross": _ratio(extracted.get("inss"), gross),
            "irrf_gross": _ratio(extracted.get("irrf"), gross),
            "fgts_gross": _ratio(extracted.get("fgts"), gross),
            "deductions_gross": _ratio(deductions, gross),
            "net_gross": _ratio(net, gross),
            "net_residual": _ratio(
                (_decimal(gross) or Decimal(0))
                - (_decimal(deductions) or Decimal(0))
                - (_decimal(net) or Decimal(0)),
                gross,
            ),
            "base_inss_gross": _ratio(extracted.get("base_inss"), gross),
            "base_irrf_gross": _ratio(extracted.get("base_irrf"), gross),
            "base_fgts_gross": _ratio(extracted.get("base_fgts"), gross),
        }
    )

    due = _date(extracted.get("data_vencimento"))
    if due is None:
        features["due_days_past_norm"] = math.nan
        features["due_days_future_norm"] = math.nan
    else:
        delta = ((reference_date or date.today()) - due).days
        features["due_days_past_norm"] = max(0, delta) / 365.0
        features["due_days_future_norm"] = max(0, -delta) / 365.0

    features.update(_line_features(extracted, reference_date))

    severity_counts = {severity: 0 for severity in SEVERITY_ORDINAL}
    source_counts = {source: 0 for source in SOURCE_NAMES}
    confirmed = uncertain = confirmed_material = 0
    confirmed_critical = uncertain_material = 0
    confidences = []
    group_data = {
        group: {
            "count": 0,
            "max_severity": 0.0,
            "confirmed_material": 0,
            "uncertain_material": 0,
        }
        for group in GROUPS
    }
    for evidence in evidences:
        severity = str(evidence.get("severity", "info"))
        ordinal = SEVERITY_ORDINAL.get(severity, 0)
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        source = str(evidence.get("source", "other"))
        source_counts[source] = source_counts.get(source, 0) + 1
        confidence = float(evidence.get("confidence", 1.0) or 0.0)
        confidences.append(confidence)
        uncertain_flag = _is_uncertain(evidence)
        if uncertain_flag:
            uncertain += 1
            if ordinal >= 3:
                uncertain_material += 1
        else:
            confirmed += 1
            if ordinal >= 3:
                confirmed_material += 1
            if ordinal == 4:
                confirmed_critical += 1
        group = FACT_GROUPS.get(str(evidence.get("code")), "other")
        if group in group_data:
            bucket = group_data[group]
            bucket["count"] += 1
            bucket["max_severity"] = max(
                bucket["max_severity"], float(ordinal)
            )
            if ordinal >= 3 and uncertain_flag:
                bucket["uncertain_material"] += 1
            if ordinal >= 3 and not uncertain_flag:
                bucket["confirmed_material"] += 1

    features["evidence_total"] = float(len(evidences))
    features["evidence_confidence_mean"] = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )
    features["evidence_confidence_max"] = max(confidences, default=0.0)
    for severity, count in severity_counts.items():
        features[f"evidence_{severity}"] = float(count)
    features["evidence_confirmed"] = float(confirmed)
    features["evidence_uncertain"] = float(uncertain)
    features["evidence_confirmed_material"] = float(confirmed_material)
    features["evidence_confirmed_critical"] = float(confirmed_critical)
    features["evidence_uncertain_material"] = float(uncertain_material)
    for source in SOURCE_NAMES:
        features[f"source_{source}"] = float(source_counts[source])
    for group, values in group_data.items():
        features[f"group_{group}_count"] = float(values["count"])
        features[f"group_{group}_max_severity"] = float(
            values["max_severity"]
        )
        features[f"group_{group}_confirmed_material"] = float(
            values["confirmed_material"]
        )
        features[f"group_{group}_uncertain_material"] = float(
            values["uncertain_material"]
        )
    return features


def vectorize(
    row: dict[str, Any],
    reference_date: date | None = None,
) -> np.ndarray:
    values = feature_row(row, reference_date=reference_date)
    return np.array(
        [values.get(name, math.nan) for name in FEATURE_NAMES],
        dtype=np.float64,
    )


def align_features(
    features: dict[str, Any],
    names: list[str] | tuple[str, ...] = tuple(FEATURE_NAMES),
) -> np.ndarray:
    """Align an inference dict, ignoring unknown keys and filling missing."""
    return np.array(
        [
            float(features[name])
            if name in features and features[name] is not None
            else math.nan
            for name in names
        ],
        dtype=np.float64,
    )
