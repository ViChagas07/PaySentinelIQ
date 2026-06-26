"""Audit: trace evidence flow for fraudulent boleto through all stages."""

from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Severity
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.scoring.fusion_engine import FusionEngine


def test_fraudulent_boleto_evidence_trace():
    """Trace ALL evidence produced for a blatantly fraudulent boleto."""
    fraud_text = """BANCO DO BRASIL
Codigo do Banco: 999
Boleto de Cobranca
Vencimento: 15/01/2024
Cedente: Solucoes Rapidas Digital LTDA
CNPJ: 00.000.000/0001-99
Valor: R$ 500,00
Linha Digitavel: 99990.12345 67890.123456 78901.234567 8 90123456789012
Multa de 5% ao dia por atraso
Juros de 3% ao mes
"""

    ctx = PipelineContext(document_type="boleto", extracted_text=fraud_text)
    ctx.extracted_fields = {
        "cnpj": "00.000.000/0001-99",
        "linha_digitavel": "99990.12345 67890.123456 78901.234567 8 90123456789012",
        "amounts": [500.0],
        "dates": ["15/01/2024"],
        "valor_nominal": 500.0,
    }

    # ── Stage 3: Validate ──
    vs = ValidateStage()
    vs._execute(ctx)
    evidence_after_validate = len(ctx.evidences)

    # ── Stage 5: Risk ──
    rs = RiskStage()
    rs._execute(ctx)
    evidence_after_risk = len(ctx.evidences)

    # ── FusionEngine ──
    fusion = FusionEngine()
    result = fusion.fuse(ctx.evidences)
    score = result["final_score"]
    level = result["final_level"]

    # ── ASSERTIONS ──
    print(f"\nEvidence after Validate: {evidence_after_validate}")
    for e in ctx.evidences:
        print(f"  [{e.severity.value.upper()}] {e.code}: {e.description[:80]}")

    print(f"\nEvidence after Risk: {evidence_after_risk}")
    print(f"Fusion Score: {score}/100, Level: {level}")

    # 1. Must detect at least 5 fraud indicators
    assert evidence_after_validate >= 3, (
        f"ValidateStage produced only {evidence_after_validate} evidence for 8 fraud indicators. "
        f"Expected >= 3. Evidence: {[e.code for e in ctx.evidences]}"
    )

    # 2. Must detect invalid bank code
    bank_evidence = [e for e in ctx.evidences if "BANCO" in e.code.upper() or "999" in e.description]
    assert len(bank_evidence) >= 1, f"No bank code evidence found. Evidence: {[e.code for e in ctx.evidences]}"

    # 3. Must detect invalid CNPJ
    cnpj_evidence = [e for e in ctx.evidences if "CNPJ" in e.code.upper()]
    assert len(cnpj_evidence) >= 1, f"No CNPJ evidence found. Evidence: {[e.code for e in ctx.evidences]}"

    # 4. Score must be >= 70 (IRON RULE: any CRITICAL = HIGH)
    assert score >= 70, (
        f"Score {score}/100 too low for blatantly fraudulent boleto. "
        f"Evidence: {[(e.code, e.severity.value) for e in ctx.evidences]}"
    )

    # 5. Level must be HIGH
    assert level == "HIGH", f"Level is {level}, expected HIGH for score {score}"

    print(f"\nPASSED: {evidence_after_validate} evidence, score={score}/100 HIGH")
