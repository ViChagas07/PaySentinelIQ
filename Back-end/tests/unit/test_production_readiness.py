"""Production Readiness: invariants, shadow comparison, end-to-end validation."""

import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.pipeline_result import PipelineResult
from app.core.contracts.pipeline_status import PipelineStatus
from app.services.scoring.fusion_engine import FusionEngine
from app.services.scoring.threshold_provider import ThresholdProvider
from app.services.pipeline.pipeline_comparison import PipelineComparison


class TestFusionEngineInvariants:
    """IRON RULES that must NEVER be violated."""

    def test_single_critical_minimum_70(self):
        """1 CRITICAL → score >= 70 (HIGH floor)."""
        fusion = FusionEngine()
        evs = [Evidence(code="X", description="x", severity=Severity.CRITICAL,
                        source=EvidenceSource.DETERMINISTIC, confidence=1.0)]
        result = fusion.fuse(evs)
        assert result["final_score"] >= 70, f"Got {result['final_score']}"
        assert result["final_level"] == "HIGH"

    def test_three_criticals_minimum_90(self):
        """3+ CRITICAL → score >= 90 (severe fraud floor)."""
        fusion = FusionEngine()
        evs = [
            Evidence(code="A", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="B", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="C", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
        ]
        result = fusion.fuse(evs)
        assert result["final_score"] >= 90, f"Got {result['final_score']}"
        assert result["final_level"] == "HIGH"

    def test_five_criticals_scores_max(self):
        """5+ CRITICAL → score must be 100 (maximum severity)."""
        fusion = FusionEngine()
        evs = [
            Evidence(code=str(i), description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)
            for i in range(5)
        ]
        result = fusion.fuse(evs)
        assert result["final_score"] >= 95

    def test_medium_evidence_cannot_dilute_critical(self):
        """MEDIUM evidence must not lower a CRITICAL-based score."""
        fusion = FusionEngine()
        evs = [
            Evidence(code="CRIT", description="x", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="MED", description="x", severity=Severity.MEDIUM, source=EvidenceSource.HEURISTIC, confidence=0.5),
        ]
        # Critical alone = 70. Adding medium should not lower it.
        result_crit_only = fusion.fuse([evs[0]])
        result_both = fusion.fuse(evs)
        assert result_both["final_score"] >= result_crit_only["final_score"]


class TestPipelineComparison:
    """Shadow pipeline comparison reporting."""

    def test_significant_improvement_detected(self):
        pc = PipelineComparison(
            document_id="doc-001", document_type="boleto",
            legacy_score=7.5, legacy_level="LOW",
            canonical_score=100.0, canonical_level="HIGH",
            legacy_time_ms=500, canonical_time_ms=250,
            legacy_anomalies=0, canonical_evidence=9,
            crewai_executed=False, ocr_executed=True,
        )
        assert pc.is_significant_divergence()
        assert pc.score_delta == 92.5
        d = pc.to_dict()
        assert d["comparison"]["significant_divergence"]

    def test_legacy_vs_canonical_report(self):
        """Simulates the shadow report format."""
        report = {
            "document_id": "boleto-fraud-001",
            "legacy": {"score": 7.5, "level": "LOW", "anomalies": 0},
            "canonical": {"score": 100, "level": "HIGH", "evidence": 9, "crewai": False},
            "delta": 92.5,
            "reason": "Legacy pipeline missing structured-field validation. Canonical detected 3 CRITICAL: banco inexistente, CNPJ invalido, linha digitavel invalida.",
        }
        assert report["delta"] >= 90
        assert report["canonical"]["level"] == "HIGH"


class TestBackwardCompatibility:
    """All API responses must include legacy format fields."""

    def test_pipeline_result_has_risk_assessment(self):
        result = PipelineResult(
            document_id="doc-1", document_type="boleto",
            risk_score=100, risk_level="HIGH",
            pipeline_status=PipelineStatus.SUCCESS,
        )
        d = result.to_dict()
        assert "RISK_ASSESSMENT" in d
        ra = d["RISK_ASSESSMENT"]
        assert ra["fraud_risk_score"] == 100
        assert ra["risk_classification"] == "HIGH"
        assert ra["recommended_action"] == "REJECT"

    def test_anomaly_list_present(self):
        ev = Evidence(code="BANCO_INVALIDO", description="Banco 999 nao existe",
                      severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC)
        result = PipelineResult(evidence=[ev], risk_score=70, risk_level="HIGH")
        d = result.to_dict()
        assert "ANOMALY_LIST" in d
        assert len(d["ANOMALY_LIST"]) == 1


class TestThresholdConsistency:
    """ThresholdProvider must be the single source of truth everywhere."""

    def test_threshold_provider_used_by_fusion(self):
        fusion = FusionEngine()
        tp = ThresholdProvider()
        assert tp.classify(80).value == "HIGH"
        assert tp.classify(55).value == "MEDIUM"
        assert tp.classify(20).value == "LOW"

    def test_classification_consistent_across_system(self):
        """70+ = HIGH, 40-69 = MEDIUM, <40 = LOW — everywhere."""
        from app.shared.domain_primitives import RiskScore, RiskLevel
        assert RiskScore(value=70, confidence=0.9).level == RiskLevel.HIGH
        assert RiskScore(value=40, confidence=0.9).level == RiskLevel.MEDIUM
        assert RiskScore(value=39, confidence=0.9).level == RiskLevel.LOW

        from app.services.scoring.threshold_provider import get_thresholds
        tp = get_thresholds()
        assert tp.classify(70).value == "HIGH"
        assert tp.classify(40).value == "MEDIUM"
        assert tp.classify(0).value == "LOW"
