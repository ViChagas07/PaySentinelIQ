# ============================================================
# PaySentinelIQ — Fase 3B Scoring Tests
# ============================================================

import pytest
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.services.scoring.fusion_engine import FusionEngine
from app.services.scoring.explainability import ExplainabilityEngine
from app.services.scoring.threshold_provider import ThresholdProvider, RiskLevel, get_thresholds


class TestThresholdProvider:
    def test_low_below_40(self):
        tp = ThresholdProvider()
        assert tp.classify(0) == RiskLevel.LOW
        assert tp.classify(20) == RiskLevel.LOW
        assert tp.classify(39.9) == RiskLevel.LOW

    def test_medium_40_to_69(self):
        tp = ThresholdProvider()
        assert tp.classify(40) == RiskLevel.MEDIUM
        assert tp.classify(55) == RiskLevel.MEDIUM
        assert tp.classify(69.9) == RiskLevel.MEDIUM

    def test_high_70_and_above(self):
        tp = ThresholdProvider()
        assert tp.classify(70) == RiskLevel.HIGH
        assert tp.classify(85) == RiskLevel.HIGH
        assert tp.classify(100) == RiskLevel.HIGH

    def test_recommended_action(self):
        tp = ThresholdProvider()
        assert tp.recommended_action(RiskLevel.HIGH) == "REJECT"
        assert tp.recommended_action(RiskLevel.MEDIUM) == "MANUAL_REVIEW"
        assert tp.recommended_action(RiskLevel.LOW) == "ACCEPT"

    def test_immutable(self):
        tp = ThresholdProvider()
        with pytest.raises(Exception):
            tp.low_max = 50

    def test_to_dict(self):
        tp = ThresholdProvider()
        d = tp.to_dict()
        assert "0-39" in str(d["low"])
        assert "40-69" in str(d["medium"])
        assert "70" in str(d["high"])


class TestFusionEngineWithThresholds:
    def test_uses_threshold_provider(self):
        fusion = FusionEngine()
        assert fusion._thresholds.classify(80) == RiskLevel.HIGH

    def test_critical_evidence_scores_high(self):
        fusion = FusionEngine()
        evs = [
            Evidence(code="BANCO_INVALIDO", description="Banco invalido",
                     severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
        ]
        result = fusion.fuse(evs)
        # 35 * 1.5 * 1.0 = 52.5 — close to HIGH threshold
        assert result["final_score"] >= 50

    def test_two_criticals_compound(self):
        fusion = FusionEngine()
        evs = [
            Evidence(code="A", description="x", severity=Severity.CRITICAL,
                     source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="B", description="x", severity=Severity.CRITICAL,
                     source=EvidenceSource.DETERMINISTIC, confidence=1.0),
        ]
        result = fusion.fuse(evs)
        # 35*1.5*1.0 + 35*1.5*1.0 = 105, capped at 100, *1.2 compound = 100
        assert result["final_score"] >= 90
        assert result["final_level"] == "HIGH"

    def test_deterministic_beats_ai(self):
        fusion = FusionEngine()
        det = Evidence(code="DET", description="Det", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0)
        ai = Evidence(code="AI", description="AI", severity=Severity.CRITICAL, source=EvidenceSource.CREWAI, confidence=1.0)
        assert fusion.fuse([det])["final_score"] > fusion.fuse([ai])["final_score"]


class TestExplainabilityEngine:
    def test_generates_reasoning(self):
        engine = ExplainabilityEngine()
        fusion = FusionEngine()
        evs = [
            Evidence(code="BANCO_INVALIDO", description="Banco 999 nao existe",
                     severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
        ]
        result = fusion.fuse(evs)
        expl = engine.explain(evs, result)
        assert expl.score > 0
        assert expl.level in ("LOW", "MEDIUM", "HIGH")
        assert expl.critical_count == 1
        assert len(expl.reasoning) > 10

    def test_source_breakdown(self):
        engine = ExplainabilityEngine()
        fusion = FusionEngine()
        evs = [
            Evidence(code="D1", description="Det", severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="A1", description="AI", severity=Severity.HIGH, source=EvidenceSource.CREWAI, confidence=0.8),
        ]
        result = fusion.fuse(evs)
        expl = engine.explain(evs, result)
        assert "deterministic" in expl.source_breakdown or "crewai" in expl.source_breakdown
        assert "deterministic" in expl.deterministic_vs_ai

    def test_empty_evidence(self):
        engine = ExplainabilityEngine()
        fusion = FusionEngine()
        result = fusion.fuse([])
        expl = engine.explain([], result)
        assert expl.score == 0.0
        assert expl.level == "LOW"
        assert expl.evidence_count == 0

    def test_to_dict(self):
        engine = ExplainabilityEngine()
        fusion = FusionEngine()
        evs = [Evidence(code="T", description="Test", severity=Severity.HIGH, source=EvidenceSource.DETERMINISTIC, confidence=1.0)]
        result = fusion.fuse(evs)
        expl = engine.explain(evs, result)
        d = expl.to_dict()
        assert "score" in d
        assert "source_breakdown" in d
        assert "top_contributors" in d
