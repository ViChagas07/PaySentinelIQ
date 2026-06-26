"""Test: fraudulent boleto with structured fields only (no ocr_text) — MUST still detect."""

from app.core.contracts.pipeline_context import PipelineContext
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.scoring.fusion_engine import FusionEngine


def test_fraudulent_boleto_structured_fields_only():
    """Structured fields only (no raw OCR text) — must still score >= 70."""
    ctx = PipelineContext(document_type="boleto")
    ctx.extracted_fields = {
        "cnpj": "00.000.000/0001-99",
        "linha_digitavel": "99990.12345 67890.123456 78901.234567 8 90123456789012",
        "valor_nominal": 500.0,
        "beneficiario": "Solucoes Rapidas Digital LTDA",
    }

    vs = ValidateStage()
    vs._execute(ctx)
    evidence_count = len(ctx.evidences)

    rs = RiskStage()
    rs._execute(ctx)

    fusion = FusionEngine()
    result = fusion.fuse(ctx.evidences)

    print(f"Evidence: {evidence_count}")
    for e in ctx.evidences:
        print(f"  [{e.severity.value.upper()}] {e.code}: {e.description[:80]}")
    print(f"Score: {result['final_score']}/100, Level: {result['final_level']}")

    # MUST detect at least 3 indicators even without OCR text
    assert evidence_count >= 3, (
        f"Only {evidence_count} evidence for structured-only boleto with 4 fraud indicators"
    )
    # MUST score HIGH (>= 70)
    assert result["final_score"] >= 70, (
        f"Score {result['final_score']} too low. Should be >= 70 with invalid bank + invalid CNPJ"
    )
    assert result["final_level"] == "HIGH"
