from __future__ import annotations

import re
from typing import Literal, cast

from app.services.extraction.dates import parse_date
from app.services.extraction.fields import CanonicalFields, ExtractedValue
from app.services.extraction.labels import find_label_matches
from app.services.extraction.language import (
    LanguageCode,
    LanguageGuess,
    detect_language,
)
from app.services.extraction.numbers import parse_amount
from app.services.extraction.text_utils import (
    fix_digit_confusions,
    normalize_text,
)
from app.services.ocr.extraction_service import DocumentExtractionService

_METHOD = Literal["label_same_line", "label_next_line", "regex"]

_MONETARY_FIELDS = {
    "valor_nominal",
    "valor_cobrado",
}
_DATE_FIELDS = {
    "data_vencimento",
    "data_documento",
}
_NUMERIC_TEXT_FIELDS = {
    "nosso_numero",
    "numero_documento",
    "agencia_codigo_beneficiario",
    "carteira",
}
_TEXT_FIELDS = {
    "beneficiario",
    "pagador",
    "nosso_numero",
    "numero_documento",
    "local_pagamento",
    "carteira",
    "agencia_codigo_beneficiario",
    "multa",
    "juros",
}
_LABEL_FIELDS = _MONETARY_FIELDS | _DATE_FIELDS | _TEXT_FIELDS


def _resolve_language(
    text: str,
    lang: str | LanguageGuess | None,
) -> LanguageGuess:
    if isinstance(lang, LanguageGuess):
        return lang
    if lang:
        language = cast(LanguageCode, lang)
        return LanguageGuess(
            lang=language,
            scores={language: 1.0},
            confidence=1.0,
        )
    return detect_language(text)


def _amount_token(raw: str) -> str | None:
    candidates = re.findall(
        r"\(?-?(?:R\$\s*|BRL\s*)?"
        r"(?:\d{1,3}(?:[.\s]\d{3})+(?:,\d{1,4})?"
        r"|\d{1,3}(?:,\d{3})+(?:\.\d{1,4})?"
        r"|\d+(?:[.,]\d{1,4})?)"
        r"\)?-?",
        raw,
    )
    combined = [
        candidate.strip()
        for candidate in candidates
        if any(char.isdigit() for char in candidate)
    ]
    if not combined:
        return None
    monetary = [
        candidate
        for candidate in combined
        if "," in candidate or "." in candidate
    ]
    return str((monetary or combined)[-1])


def _date_token(raw: str) -> str:
    match = re.search(r"\d{1,4}[./-]\d{1,2}[./-]\d{2,4}", raw)
    if match:
        return match.group(0)
    return raw.strip()


def _clean_text(raw: str) -> str:
    return raw.strip().strip(":;-–—").strip()


def _fix_numeric(
    fields: CanonicalFields,
    field: str,
    raw: str,
) -> str:
    fixed, corrections = fix_digit_confusions(raw)
    for correction in corrections:
        fields.corrections.append(f"{field}: {correction}")
    return fixed


def _assign(
    fields: CanonicalFields,
    field: str,
    value: ExtractedValue,
) -> None:
    setattr(fields, field, value)


def _next_line(lines: list[str], index: int) -> tuple[str, int] | None:
    for next_index in range(index + 1, len(lines)):
        if lines[next_index].strip():
            return lines[next_index].strip(), next_index + 1
    return None


def _extract_labeled(
    fields: CanonicalFields,
    lines: list[str],
    language: str,
) -> None:
    assigned: set[str] = set()

    for index, line in enumerate(lines):
        for match in find_label_matches(line):
            field = match.canonical
            if field not in _LABEL_FIELDS or field in assigned:
                continue

            raw_value = line[match.end:].strip()
            method: _METHOD = "label_same_line"
            value_line = index + 1

            if raw_value and any(
                match.start == 0
                and (
                    match.end == len(raw_value)
                    or raw_value[match.end : match.end + 1] in {":", ";", "-"}
                )
                for match in find_label_matches(raw_value)
            ):
                raw_value = ""

            raw_value = _clean_text(raw_value)
            if not raw_value:
                next_value = _next_line(lines, index)
                if next_value is None:
                    continue
                raw_value, value_line = next_value
                raw_value = _clean_text(raw_value)
                method = "label_next_line"

            confidence = 0.9 if method == "label_same_line" else 0.75

            if field in _MONETARY_FIELDS:
                token = _amount_token(raw_value)
                if token is None:
                    continue
                token = _fix_numeric(fields, field, token)
                try:
                    parsed = parse_amount(token, language)
                except ValueError:
                    continue
                if parsed.ambiguous:
                    fields.warnings.append(
                        f"{field}: ambiguous amount {parsed.raw!r}"
                    )
                    confidence = 0.6
                _assign(
                    fields,
                    field,
                    ExtractedValue(
                        value=parsed.value,
                        raw=parsed.raw,
                        line_no=value_line,
                        method=method,
                        confidence=confidence,
                    ),
                )
                assigned.add(field)
            elif field in _DATE_FIELDS:
                token = _fix_numeric(fields, field, _date_token(raw_value))
                try:
                    parsed_date = parse_date(token, language)
                except ValueError:
                    continue
                if parsed_date.ambiguous:
                    fields.warnings.append(
                        f"{field}: ambiguous date {parsed_date.raw!r}"
                    )
                    confidence = 0.6
                _assign(
                    fields,
                    field,
                    ExtractedValue(
                        value=parsed_date.value,
                        raw=parsed_date.raw,
                        line_no=value_line,
                        method=method,
                        confidence=confidence,
                    ),
                )
                assigned.add(field)
            else:
                value = _clean_text(raw_value)
                if not value:
                    continue
                if field in _NUMERIC_TEXT_FIELDS:
                    value = _fix_numeric(fields, field, value)
                _assign(
                    fields,
                    field,
                    ExtractedValue(
                        value=value,
                        raw=raw_value,
                        line_no=value_line,
                        method=method,
                        confidence=confidence,
                    ),
                )
                assigned.add(field)


def _line_number(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _assign_regex(
    fields: CanonicalFields,
    text: str,
    field: str,
    match: re.Match[str],
) -> None:
    _assign(
        fields,
        field,
        ExtractedValue(
            value=match.group(0),
            raw=match.group(0),
            line_no=_line_number(text, match.start()),
            method="regex",
            confidence=0.95,
        ),
    )


def _extract_identifiers(fields: CanonicalFields, text: str) -> None:
    has_cnpj_label = re.search(r"\bCNPJ\b", text, re.IGNORECASE) is not None
    cnpj_match = DocumentExtractionService.CNPJ_PATTERN.search(text)
    if cnpj_match and (
        has_cnpj_label or re.search(r"\D", cnpj_match.group(0))
    ):
        _assign_regex(fields, text, "cnpj", cnpj_match)

    has_cpf_label = re.search(r"\bCPF\b", text, re.IGNORECASE) is not None
    cpf_match = DocumentExtractionService.CPF_PATTERN.search(text)
    if cpf_match and (
        has_cpf_label or re.search(r"\D", cpf_match.group(0))
    ):
        cpf_value = cpf_match.group(0)
        if fields.cnpj is None or cpf_value != fields.cnpj.value:
            _assign_regex(fields, text, "cpf", cpf_match)

    linha_match = DocumentExtractionService.LINHA_DIGITAVEL_PATTERN.search(text)
    if linha_match is None:
        linha_match = DocumentExtractionService.BARCODE_PATTERN.search(text)
    if linha_match:
        digits = re.sub(r"\D", "", linha_match.group(0))
        if len(digits) in {47, 48}:
            _assign(
                fields,
                "linha_digitavel",
                ExtractedValue(
                    value=digits,
                    raw=linha_match.group(0),
                    line_no=_line_number(text, linha_match.start()),
                    method="regex",
                    confidence=0.95,
                ),
            )
            _assign(
                fields,
                "codigo_banco",
                ExtractedValue(
                    value=digits[:3],
                    raw=digits[:3],
                    line_no=_line_number(text, linha_match.start()),
                    method="regex",
                    confidence=0.95,
                ),
            )

    barcode_match = DocumentExtractionService.CHAVE_ACESSO_PATTERN.search(text)
    if barcode_match:
        digits = re.sub(r"\D", "", barcode_match.group(0))
        if len(digits) == 44:
            _assign(
                fields,
                "codigo_barras",
                ExtractedValue(
                    value=digits,
                    raw=barcode_match.group(0),
                    line_no=_line_number(text, barcode_match.start()),
                    method="regex",
                    confidence=0.95,
                ),
            )

    if fields.codigo_banco is None:
        bank_match = DocumentExtractionService.BANK_CODE_PATTERN.search(text)
        if bank_match:
            _assign(
                fields,
                "codigo_banco",
                ExtractedValue(
                    value=bank_match.group(1),
                    raw=bank_match.group(0),
                    line_no=_line_number(text, bank_match.start()),
                    method="regex",
                    confidence=0.9,
                ),
            )


def extract_boleto_fields(
    text: str,
    lang: str | LanguageGuess | None = None,
) -> CanonicalFields:
    normalized = normalize_text(text)
    fixed_text, corrections = fix_digit_confusions(normalized)
    language = _resolve_language(normalized, lang)
    fields = CanonicalFields(language=language)
    fields.corrections.extend(f"text: {item}" for item in corrections)
    lines = fixed_text.split("\n")

    _extract_labeled(fields, lines, language.lang)
    _extract_identifiers(fields, fixed_text)
    return fields
