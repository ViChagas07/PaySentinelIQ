# ============================================================
# PaySentinelIQ — Contract Tests
# Architecture Hardening v1.0 (Fase 1.5)
# ============================================================

import pytest
from app.core.contracts.pipeline_status import PipelineStatus
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.agent_result import AgentFinding, CrewResult
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult, EvidenceContribution


class TestPipelineStatus:
    def test_all_statuses_defined(self):
        assert PipelineStatus.SUCCESS.value == "success"
        assert PipelineStatus.PARTIAL.value == "partial"
        assert PipelineStatus.FAILED.value == "failed"
        assert PipelineStatus.INCONCLUSIVE.value == "inconclusive"

    def test_status_is_string_enum(self):
        assert isinstance(PipelineStatus.SUCCESS, str)


class TestEvidence:
    def test_create_evidence(self):
        ev = Evidence(
            code="BANCO_INVALIDO",
            description="Banco 999 não existe no BACEN",
            severity=Severity.CRITICAL,
            source=EvidenceSource.DETERMINISTIC,
            confidence=1.0,
            category="structural",
            rule_reference="BACEN ISPB",
        )
        assert ev.code == "BANCO_INVALIDO"
        assert ev.severity == Severity.CRITICAL
        assert ev.source == EvidenceSource.DETERMINISTIC

    def test_confidence_validation(self):
        with pytest.raises(ValueError):
            Evidence(code="X", description="x", confidence=1.5)
        with pytest.raises(ValueError):
            Evidence(code="X", description="x", confidence=-0.5)

    def test_roundtrip_dict(self):
        ev = Evidence(
            code="TEST",
            description="Test evidence",
            severity=Severity.HIGH,
            source=EvidenceSource.HEURISTIC,
            confidence=0.9,
            metadata={"key": "value"},
        )
        d = ev.to_dict()
        ev2 = Evidence.from_dict(d)
        assert ev2.code == ev.code
        assert ev2.severity == ev.severity
        assert ev2.confidence == ev.confidence
        assert ev2.metadata == ev.metadata

    def test_severity_values(self):
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"
        assert Severity.INFO.value == "info"

    def test_evidence_source_values(self):
        sources = list(EvidenceSource)
        assert EvidenceSource.DETERMINISTIC in sources
        assert EvidenceSource.CREWAI in sources
        assert EvidenceSource.BRASILAPI in sources


class TestPipelineContext:
    def test_create_empty_context(self):
        ctx = PipelineContext()
        assert ctx.document_id != ""
        assert ctx.correlation_id != ""
        assert ctx.evidences == []
        assert ctx.pipeline_status == PipelineStatus.SUCCESS

    def test_add_evidence_deduplicates(self):
        ctx = PipelineContext()
        ev1 = Evidence(code="A", description="First")
        ev2 = Evidence(code="A", description="Duplicate")
        ev3 = Evidence(code="B", description="Second")
        ctx.add_evidence(ev1)
        ctx.add_evidence(ev2)
        ctx.add_evidence(ev3)
        assert len(ctx.evidences) == 2  # "A" not duplicated

    def test_add_evidences_batch(self):
        ctx = PipelineContext()
        ctx.add_evidences([
            Evidence(code="A", description="First"),
            Evidence(code="B", description="Second"),
            Evidence(code="A", description="Duplicate"),
        ])
        assert len(ctx.evidences) == 2

    def test_add_warning_and_error(self):
        ctx = PipelineContext()
        ctx.add_warning("Warning 1")
        ctx.add_error("Error 1")
        assert len(ctx.warnings) == 1
        assert len(ctx.errors) == 1
        assert ctx.pipeline_status == PipelineStatus.PARTIAL  # error degrades status

    def test_record_stage_time(self):
        ctx = PipelineContext()
        ctx.record_stage_time("IngestStage", 1.5)
        assert ctx.processing_times["IngestStage"] == 1.5


class TestPipelineResult:
    def test_backward_compat_risk_assessment(self):
        result = PipelineResult(
            document_id="doc-1",
            document_type="boleto",
            risk_score=72.5,
            risk_level="HIGH",
        )
        d = result.to_dict()
        # Legacy format
        assert "RISK_ASSESSMENT" in d
        ra = d["RISK_ASSESSMENT"]
        assert ra["fraud_risk_score"] == 72.5
        assert ra["risk_classification"] == "HIGH"
        assert ra["recommended_action"] == "REJECT"

    def test_backward_compat_medium_score(self):
        result = PipelineResult(risk_score=55, risk_level="MEDIUM")
        d = result.to_dict()
        assert d["RISK_ASSESSMENT"]["recommended_action"] == "MANUAL_REVIEW"

    def test_backward_compat_low_score(self):
        result = PipelineResult(risk_score=20, risk_level="LOW")
        d = result.to_dict()
        assert d["RISK_ASSESSMENT"]["recommended_action"] == "ACCEPT"

    def test_anomaly_list_backward_compat(self):
        ev = Evidence(
            code="TEST_FLAG",
            description="Test anomaly",
            severity=Severity.CRITICAL,
            source=EvidenceSource.DETERMINISTIC,
            category="structural",
        )
        result = PipelineResult(evidence=[ev])
        d = result.to_dict()
        assert "ANOMALY_LIST" in d
        assert len(d["ANOMALY_LIST"]) == 1
        assert d["ANOMALY_LIST"][0]["severity"] == "critical"

    def test_new_contract_fields(self):
        result = PipelineResult(
            pipeline_status=PipelineStatus.SUCCESS,
            risk_score=85.0,
            risk_level="HIGH",
            reasoning_summary="Multiple critical indicators",
        )
        d = result.to_dict()
        assert d["pipeline_status"] == "success"
        assert d["risk_score"] == 85.0
        assert d["risk_level"] == "HIGH"
        assert d["reasoning_summary"] == "Multiple critical indicators"


class TestAgentFinding:
    def test_create_agent_finding(self):
        ev = Evidence(code="TEST", description="Test")
        finding = AgentFinding(
            agent_name="FraudAnalyst",
            evidence=[ev],
            hypotheses=["Possible ghost bank"],
            confidence=0.92,
        )
        d = finding.to_dict()
        assert d["agent_name"] == "FraudAnalyst"
        assert len(d["evidence"]) == 1
        assert d["confidence"] == 0.92

    def test_no_score_in_agent_finding(self):
        """AgentFinding must NOT have a score field."""
        finding = AgentFinding(agent_name="Test")
        d = finding.to_dict()
        assert "score" not in d
        assert "final_score" not in d
        assert "risk_score" not in d
