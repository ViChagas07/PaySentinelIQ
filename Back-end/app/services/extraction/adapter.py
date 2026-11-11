from __future__ import annotations

from datetime import date, datetime, time, timezone
from decimal import Decimal
from typing import Any, Callable

from app.services.extraction.fields import CanonicalFields, ExtractedValue

_CONFIDENCE_THRESHOLD = 0.5
_CANONICAL_META = {"language", "warnings", "corrections"}


def _float_value(value: Any) -> float | None:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _date_value(value: Any) -> date | None:
    return value if isinstance(value, date) else None


def _text_value(value: Any) -> str | None:
    return str(value) if value is not None else None


def _digits_value(value: Any) -> str | None:
    if value is None:
        return None
    digits = "".join(char for char in str(value) if char.isdigit())
    return digits or None


def _int_value(value: Any) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _ambiguous_date(fields: CanonicalFields, name: str) -> bool:
    prefix = f"{name}: ambiguous date"
    return any(warning.startswith(prefix) for warning in fields.warnings)


def _detail(field: ExtractedValue) -> dict[str, Any]:
    if isinstance(field.value, Decimal):
        value = str(field.value)
    elif isinstance(field.value, date):
        value = field.value.isoformat()
    else:
        value = str(field.value)
    return {
        "value": value,
        "raw": field.raw,
        "line_no": field.line_no,
        "method": field.method,
        "confidence": field.confidence,
    }


def _add_mapped(
    output: dict[str, Any],
    fields: CanonicalFields,
    name: str,
    key: str,
    converter: Callable[[Any], Any],
) -> None:
    field = getattr(fields, name)
    if field is None or field.confidence < _CONFIDENCE_THRESHOLD:
        return
    converted = converter(field.value)
    if converted is not None:
        output[key] = converted


def _map_boleto(output: dict[str, Any], fields: CanonicalFields) -> None:
    _add_mapped(output, fields, "valor_nominal", "valor_nominal", _float_value)
    _add_mapped(output, fields, "valor_nominal", "amount", _float_value)
    _add_mapped(output, fields, "valor_cobrado", "valor_cobrado", _float_value)

    due = fields.data_vencimento
    if due is not None and due.confidence >= _CONFIDENCE_THRESHOLD:
        due_date = _date_value(due.value)
        if due_date is not None:
            if _ambiguous_date(fields, "data_vencimento"):
                output["data_vencimento"] = None
                output["due_date"] = None
                output["data_vencimento_ambiguous"] = True
                output["data_vencimento_raw"] = due.raw
            else:
                output["data_vencimento"] = due_date.strftime("%d/%m/%Y")
                output["due_date"] = datetime.combine(
                    due_date,
                    time.min,
                    tzinfo=timezone.utc,
                ).isoformat()

    issued = fields.data_documento
    if issued is not None and issued.confidence >= _CONFIDENCE_THRESHOLD:
        issue_date = _date_value(issued.value)
        if issue_date is not None:
            output["data_documento"] = issue_date.strftime("%d/%m/%Y")
            output["issue_date"] = datetime.combine(
                issue_date,
                time.min,
                tzinfo=timezone.utc,
            ).isoformat()

    _add_mapped(output, fields, "beneficiario", "beneficiario", _text_value)
    _add_mapped(
        output,
        fields,
        "beneficiario",
        "beneficiary_name",
        _text_value,
    )
    _add_mapped(output, fields, "pagador", "pagador", _text_value)
    _add_mapped(output, fields, "codigo_banco", "codigo_banco", _text_value)
    _add_mapped(output, fields, "codigo_banco", "bank_code", _text_value)
    _add_mapped(
        output,
        fields,
        "linha_digitavel",
        "linha_digitavel",
        _digits_value,
    )
    _add_mapped(output, fields, "codigo_barras", "codigo_barras", _digits_value)
    _add_mapped(output, fields, "cnpj", "cnpj", _text_value)
    _add_mapped(output, fields, "cpf", "cpf", _text_value)
    _add_mapped(output, fields, "nosso_numero", "nosso_numero", _text_value)
    _add_mapped(
        output,
        fields,
        "numero_documento",
        "numero_documento",
        _text_value,
    )
    _add_mapped(output, fields, "carteira", "carteira", _text_value)
    _add_mapped(output, fields, "local_pagamento", "local_pagamento", _text_value)
    _add_mapped(
        output,
        fields,
        "agencia_codigo_beneficiario",
        "agencia_codigo_beneficiario",
        _text_value,
    )
    _add_mapped(output, fields, "multa", "multa", _text_value)
    _add_mapped(output, fields, "juros", "juros", _text_value)


def _map_payslip(output: dict[str, Any], fields: CanonicalFields) -> None:
    _add_mapped(output, fields, "razao_social", "razao_social", _text_value)
    _add_mapped(output, fields, "razao_social", "company_name", _text_value)
    _add_mapped(output, fields, "nome_funcionario", "nome_funcionario", _text_value)
    _add_mapped(output, fields, "cargo", "cargo", _text_value)
    _add_mapped(output, fields, "cbo", "cbo", _text_value)
    _add_mapped(output, fields, "cpf", "cpf", _text_value)
    _add_mapped(output, fields, "cnpj", "cnpj", _text_value)

    period = fields.periodo
    if period is not None and period.confidence >= _CONFIDENCE_THRESHOLD:
        output["periodo"] = str(period.value)

    admission = fields.data_admissao
    if admission is not None and admission.confidence >= _CONFIDENCE_THRESHOLD:
        admission_date = _date_value(admission.value)
        if admission_date is not None:
            output["data_admissao"] = admission_date.strftime("%d/%m/%Y")

    _add_mapped(output, fields, "salario_base", "salario_base", _float_value)
    _add_mapped(output, fields, "salario_bruto", "salario_bruto", _float_value)
    _add_mapped(output, fields, "salario_bruto", "gross_salary", _float_value)
    _add_mapped(output, fields, "total_descontos", "total_descontos", _float_value)
    _add_mapped(output, fields, "salario_liquido", "salario_liquido", _float_value)
    _add_mapped(output, fields, "salario_liquido", "liquido", _float_value)
    _add_mapped(output, fields, "salario_liquido", "net_salary", _float_value)
    _add_mapped(output, fields, "inss", "inss", _float_value)
    _add_mapped(output, fields, "inss", "inss_amount", _float_value)
    _add_mapped(output, fields, "irrf", "irrf", _float_value)
    _add_mapped(output, fields, "fgts", "fgts", _float_value)
    _add_mapped(output, fields, "base_inss", "base_inss", _float_value)
    _add_mapped(output, fields, "base_irrf", "base_irrf", _float_value)
    _add_mapped(output, fields, "base_fgts", "base_fgts", _float_value)

    dependents = fields.dependentes
    if dependents is not None and dependents.confidence >= _CONFIDENCE_THRESHOLD:
        count = _int_value(dependents.value)
        if count is not None:
            output["dependentes"] = count


def to_pipeline_fields(
    fields: CanonicalFields,
    doc_kind: str,
) -> dict[str, Any]:
    output: dict[str, Any] = {}

    canonical: dict[str, Any] = {}
    for name in CanonicalFields.model_fields:
        if name in _CANONICAL_META:
            continue
        field = getattr(fields, name)
        if field is not None:
            canonical[name] = _detail(field)

    canonical["language"] = fields.language.model_dump()
    canonical["warnings"] = list(fields.warnings)
    canonical["corrections"] = list(fields.corrections)
    output["canonical"] = canonical

    kind = doc_kind.strip().lower()
    if kind == "boleto":
        _map_boleto(output, fields)
    elif kind in {"contracheque", "holerite", "payslip", "payroll"}:
        _map_payslip(output, fields)

    return output

