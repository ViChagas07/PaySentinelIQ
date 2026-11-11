from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.deterministic_rules_stage import (
    DeterministicRulesStage,
)
from app.services.validation.ocr_provenance import (
    OCR_SENSITIVE_CODES,
    apply_ocr_uncertainty,
)


def _evidence(code: str, severity: Severity = Severity.CRITICAL) -> Evidence:
    return Evidence(
        code=code,
        description=code,
        severity=severity,
        source=EvidenceSource.DETERMINISTIC,
        confidence=0.7,
        metadata={"source": "test"},
    )


def _context(provider: str, status: str = "completed") -> PipelineContext:
    return PipelineContext(
        document_type="unknown",
        metadata={"ocr": {"status": status, "provider": provider}},
    )


def test_ocr_downgrades_one_level_and_preserves_confidence():
    context = _context("tesseract")
    context.evidences = [_evidence("BANCO_INVALIDO")]

    replaced = apply_ocr_uncertainty(context)

    assert replaced == 1
    evidence = context.evidences[0]
    assert evidence.severity == Severity.HIGH
    assert evidence.confidence == 0.7
    assert evidence.metadata["ocr_uncertain"] is True
    assert evidence.metadata["original_severity"] == "critical"
    assert evidence.metadata["source"] == "test"


def test_native_text_does_not_downgrade():
    context = _context("native_text")
    context.evidences = [_evidence("BANCO_INVALIDO")]

    replaced = apply_ocr_uncertainty(context)

    assert replaced == 0
    assert context.evidences[0].severity == Severity.CRITICAL


def test_evidence_outside_sensitive_set_is_untouched():
    context = _context("tesseract")
    context.evidences = [_evidence("SOMETHING_ELSE", Severity.HIGH)]

    replaced = apply_ocr_uncertainty(context)

    assert replaced == 0
    assert context.evidences[0].severity == Severity.HIGH
    assert "ocr_uncertain" not in context.evidences[0].metadata


def test_every_low_sensitive_code_becomes_info():
    context = _context("paddleocr")
    context.evidences = [
        _evidence(code, Severity.LOW) for code in sorted(OCR_SENSITIVE_CODES)
    ]

    apply_ocr_uncertainty(context)

    assert all(
        evidence.severity == Severity.INFO for evidence in context.evidences
    )


def test_stage_applies_downgrade_after_validation():
    context = _context("tesseract")
    context.document_type = "unknown"
    context.metadata["extraction"] = {"document_type_inferred": None}
    context.evidences = [_evidence("PAYSLIP_CPF_INVALID", Severity.HIGH)]

    DeterministicRulesStage().execute(context)

    assert context.evidences[0].severity == Severity.MEDIUM
