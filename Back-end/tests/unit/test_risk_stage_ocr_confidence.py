from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.risk_stage import RiskStage


def _context(ocr_confidence: float = 0.0) -> PipelineContext:
    return PipelineContext(
        document_type="boleto",
        extracted_fields={"cnpj": "12.345.678/0001-90"},
        ocr_confidence=ocr_confidence,
    )


def _codes(context: PipelineContext) -> set[str]:
    RiskStage().execute(context)
    return {evidence.code for evidence in context.evidences}


def test_ocr_failed_does_not_generate_very_low():
    context = _context(0.0)
    context.metadata["ocr"] = {"status": "failed", "error": "RuntimeError"}

    assert "OCR_VERY_LOW" not in _codes(context)


def test_ocr_empty_does_not_generate_very_low():
    context = _context(0.0)
    context.metadata["ocr"] = {"status": "empty"}

    assert "OCR_VERY_LOW" not in _codes(context)


def test_ocr_confidence_40_still_generates_very_low():
    context = _context(40.0)
    context.metadata["ocr"] = {"status": "completed"}

    assert "OCR_VERY_LOW" in _codes(context)


def test_old_flow_without_ocr_block_keeps_behavior():
    context = _context(0.0)

    assert "OCR_VERY_LOW" in _codes(context)
