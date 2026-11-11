"""Provisional OCR provenance mitigation.

Evidence that depends on reading digits or names is less trustworthy when the
text came from OCR instead of the PDF native text layer. Until the corroboration
by a second reading exists, these codes are downgraded by one severity level
when the OCR provider is not ``native_text``.
"""

from __future__ import annotations

from dataclasses import replace

from app.core.contracts.evidence import Evidence, Severity
from app.core.contracts.pipeline_context import PipelineContext

OCR_SENSITIVE_CODES: frozenset[str] = frozenset(
    {
        "BOLETO_GENERAL_DV_INVALID",
        "BOLETO_AMOUNT_MISMATCH",
        "BOLETO_BARCODE_MISMATCH",
        "BOLETO_DUE_DATE_MISMATCH",
        "BOLETO_BANK_MISMATCH",
        "LINHA_DIGITAVEL_FORMATO_INCORRETO",
        "DIGITO_VERIFICADOR_CAMPO1_INVALIDO",
        "DIGITO_VERIFICADOR_CAMPO2_INVALIDO",
        "DIGITO_VERIFICADOR_CAMPO3_INVALIDO",
        "BANCO_INVALIDO",
        "PAYSLIP_NET_MISMATCH",
        "PAYSLIP_DEDUCTIONS_INCONSISTENT",
        "PAYSLIP_INSS_ABOVE_CEILING",
        "PAYSLIP_INSS_MISMATCH",
        "PAYSLIP_IRRF_MISMATCH",
        "PAYSLIP_FGTS_MISMATCH",
        "PAYSLIP_BASE_EXCEEDS_GROSS",
        "PAYSLIP_CPF_INVALID",
        "PAYSLIP_CNPJ_INVALID",
        "CNPJ_INVALID_PATTERN",
    }
)

_DOWNGRADE: dict[Severity, Severity] = {
    Severity.CRITICAL: Severity.HIGH,
    Severity.HIGH: Severity.MEDIUM,
    Severity.MEDIUM: Severity.LOW,
    Severity.LOW: Severity.INFO,
    Severity.INFO: Severity.INFO,
}


def apply_ocr_uncertainty(context: PipelineContext) -> int:
    """Downgrade OCR-sensitive evidence by one level.

    Returns the number of evidence objects that were replaced. Evidence is
    treated as immutable: the replacement object carries the new severity and
    keeps the original confidence.
    """
    ocr = context.metadata.get("ocr")
    if not isinstance(ocr, dict):
        return 0
    if ocr.get("status") != "completed":
        return 0
    if ocr.get("provider") == "native_text":
        return 0

    replaced = 0
    updated: list[Evidence] = []
    for evidence in context.evidences:
        if evidence.code not in OCR_SENSITIVE_CODES:
            updated.append(evidence)
            continue
        metadata = dict(evidence.metadata or {})
        metadata["ocr_uncertain"] = True
        metadata["original_severity"] = evidence.severity.value
        updated.append(
            replace(
                evidence,
                severity=_DOWNGRADE[evidence.severity],
                metadata=metadata,
            )
        )
        replaced += 1
    context.evidences = updated
    return replaced
