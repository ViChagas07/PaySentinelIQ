# ============================================================
# PaySentinelIQ — Golden Dataset Tests (Fase 5)
# ============================================================

import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.services.pipeline.canonical_pipeline import CanonicalPipeline
from app.services.scoring.fusion_engine import FusionEngine
from app.services.scoring.threshold_provider import ThresholdProvider


class TestGoldenDatasetFraudulent:
    """Fraudulent boletos MUST be classified as HIGH (>= 70)."""

    def test_banco_invalido_scores_high(self):
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidence(Evidence(
            code="BANCO_INVALIDO", description="Bank code 999 not in BACEN ISPB",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score >= 70, f"Expected >=70, got {result.risk_score}"
        assert result.risk_level == "HIGH"

    def test_cnpj_falso_scores_high(self):
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidence(Evidence(
            code="CNPJ_INVALIDO", description="CNPJ 00.000.000/0001-99 is fake",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score >= 70, f"Expected >=70, got {result.risk_score}"

    def test_multa_ilegal_scores_high(self):
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidence(Evidence(
            code="MULTA_ILEGAL", description="Late fee 5% per day — limit is 2%",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score >= 70

    def test_vencido_2anos_scores_high(self):
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidence(Evidence(
            code="VENCIDO_2ANOS", description="Overdue 892 days",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score >= 70

    def test_todos_indicadores_scores_high(self):
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidences([
            Evidence(code="BANCO_INVALIDO", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="CNPJ_INVALIDO", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="MULTA_ILEGAL", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="VENCIDO", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="VALOR_REDONDO", description="x", severity=Severity.MEDIUM, source=EvidenceSource.HEURISTIC, confidence=0.7),
        ])
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score >= 85, f"5 indicators should score >=85, got {result.risk_score}"


class TestGoldenDatasetLegitimate:
    """Legitimate documents without evidence MUST be LOW (< 40)."""

    def test_no_evidence_scores_low(self):
        ctx = PipelineContext(document_type="boleto")
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score < 40
        assert result.risk_level == "LOW"

    def test_contracheque_no_evidence_scores_low(self):
        ctx = PipelineContext(document_type="contracheque")
        result = CanonicalPipeline().execute(ctx)
        assert result.risk_score < 40


class TestGoldenDatasetStatistics:
    """Automated accuracy/precision/recall/F1 computation."""

    def test_perfect_detection_rate(self):
        """All 5 fraudulent + 2 legitimate cases from above must be correct."""
        tp = tn = fp = fn = 0

        # Fraudulent tests (expected HIGH)
        fraud_cases = [
            [Evidence(code="B1", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)],
            [Evidence(code="C1", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)],
            [Evidence(code="M1", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)],
            [Evidence(code="V1", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)],
            [Evidence(code="X1", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
             Evidence(code="X2", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
             Evidence(code="X3", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
             Evidence(code="X4", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
             Evidence(code="X5", description="x", severity=Severity.MEDIUM, source=EvidenceSource.HEURISTIC, confidence=0.7)],
        ]

        pipeline = CanonicalPipeline()
        for evs in fraud_cases:
            ctx = PipelineContext(document_type="boleto")
            ctx.add_evidences(evs)
            result = pipeline.execute(ctx)
            if result.risk_score >= 70:
                tp += 1
            else:
                fn += 1

        # Legitimate tests (expected LOW)
        for _ in range(2):
            ctx = PipelineContext(document_type="boleto")
            result = pipeline.execute(ctx)
            if result.risk_score < 40:
                tn += 1
            else:
                fp += 1

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)

        assert tp == 5, f"TP should be 5, got {tp}"
        assert tn == 2, f"TN should be 2, got {tn}"
        assert fp == 0, f"FP should be 0, got {fp}"
        assert fn == 0, f"FN should be 0, got {fn}"
        assert precision == 1.0, f"Precision: {precision}"
        assert recall == 1.0, f"Recall: {recall}"
        assert f1 == 1.0, f"F1: {f1}"
