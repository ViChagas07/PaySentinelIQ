# ============================================================
# PaySentinelIQ — Architecture Hardening Smoke Tests
# ============================================================
"""Integration tests for the new architecture contracts and pipeline."""

import pytest
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.pipeline_result import PipelineResult
from app.core.contracts.agent_result import AgentFinding
from app.services.pipeline.canonical_pipeline import CanonicalPipeline
from app.services.scoring.fusion_engine import FusionEngine


class TestCanonicalPipelineSmoke:
    def test_pipeline_with_critical_evidence_scores_high(self):
        """A boleto with 3 CRITICAL indicators MUST score >= 70."""
        ctx = PipelineContext(document_type="boleto")
        ctx.add_evidence(Evidence(
            code="BANCO_INVALIDO", description="Banco 999 inexistente",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        ctx.add_evidence(Evidence(
            code="CNPJ_INVALIDO", description="CNPJ falso",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))
        ctx.add_evidence(Evidence(
            code="MULTA_ILEGAL", description="Multa 5% ao dia",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        ))

        pipeline = CanonicalPipeline()
        result = pipeline.execute(ctx)

        assert result.risk_score >= 70, f"Expected >=70, got {result.risk_score}"
        assert result.risk_level == "HIGH"

    def test_pipeline_with_no_evidence_scores_low(self):
        ctx = PipelineContext(document_type="boleto")
        pipeline = CanonicalPipeline()
        result = pipeline.execute(ctx)
        assert result.risk_score < 40

    def test_pipeline_backward_compat(self):
        result = PipelineResult(
            document_id="doc-1", document_type="boleto",
            risk_score=72.5, risk_level="HIGH",
        )
        d = result.to_dict()
        ra = d["RISK_ASSESSMENT"]
        assert ra["fraud_risk_score"] == 72.5
        assert ra["risk_classification"] == "HIGH"
        assert ra["recommended_action"] == "REJECT"

    def test_pipeline_result_medium_score_action(self):
        result = PipelineResult(risk_score=55, risk_level="MEDIUM")
        d = result.to_dict()
        assert d["RISK_ASSESSMENT"]["recommended_action"] == "MANUAL_REVIEW"

    def test_pipeline_result_low_score_action(self):
        result = PipelineResult(risk_score=20, risk_level="LOW")
        d = result.to_dict()
        assert d["RISK_ASSESSMENT"]["recommended_action"] == "ACCEPT"


class TestFusionEngineSmoke:
    def test_fusion_with_critical_and_high(self):
        fusion = FusionEngine()
        evs = [
            Evidence(code="A", description="Critical",
                     severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="B", description="High",
                     severity=Severity.HIGH, source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="C", description="Medium",
                     severity=Severity.MEDIUM, source=EvidenceSource.HEURISTIC, confidence=0.7),
        ]
        result = fusion.fuse(evs)
        # 35*1.5*1.0 + 20*1.5*1.0 + 10*1.0*0.7 = 52.5 + 30 + 7 = 89.5
        assert result["final_score"] >= 85
        assert result["final_level"] == "HIGH"

    def test_fusion_crewai_evidence_gets_lower_weight(self):
        """AI-generated evidence should get lower source multiplier (tested with HIGH to avoid critical floor)."""
        fusion = FusionEngine()
        ev_det = Evidence(
            code="DET", description="Deterministic",
            severity=Severity.HIGH, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        )
        ev_ai = Evidence(
            code="AI", description="AI found",
            severity=Severity.HIGH, source=EvidenceSource.CREWAI, confidence=1.0,
        )
        result_det = fusion.fuse([ev_det])
        result_ai = fusion.fuse([ev_ai])
        assert result_det["final_score"] > result_ai["final_score"], \
            "Deterministic evidence must carry more weight than AI evidence"

    def test_fusion_empty_evidence(self):
        fusion = FusionEngine()
        result = fusion.fuse([])
        assert result["final_score"] == 0.0
        assert result["final_level"] == "LOW"

    def test_fusion_explainability_has_source_breakdown(self):
        fusion = FusionEngine()
        evs = [
            Evidence(code="A", description="Det", severity=Severity.HIGH,
                     source=EvidenceSource.DETERMINISTIC, confidence=1.0),
            Evidence(code="B", description="AI", severity=Severity.MEDIUM,
                     source=EvidenceSource.CREWAI, confidence=0.8),
        ]
        result = fusion.fuse(evs)
        exp = result["explainability"]
        assert "source_breakdown" in exp
        assert "deterministic" in exp["source_breakdown"]


class TestAgentFindingsNoScore:
    def test_agent_finding_has_no_score_field(self):
        """CrewAI agents must NEVER output a score."""
        af = AgentFinding(agent_name="Test")
        d = af.to_dict()
        assert "score" not in d
        assert "final_score" not in d
        assert "risk_score" not in d
        assert "classification" not in d

    def test_crew_result_has_no_score_field(self):
        from app.core.contracts.agent_result import CrewResult
        cr = CrewResult()
        d = cr.to_dict()
        assert "score" not in d
        assert "final_score" not in d
