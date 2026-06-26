# ============================================================
# PaySentinelIQ — CrewAI Integration Tests (Fase 2)
# ============================================================

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.agent_result import AgentFinding, CrewResult
from app.ai_agents.orchestrator import (
    CrewAIOrchestrator, NoOpOrchestrator, FraudCopilotOrchestrator,
    CircuitBreaker, AIOrchestrationPort,
)


class TestCircuitBreaker:
    def test_starts_closed(self):
        cb = CircuitBreaker()
        assert not cb.is_open

    def test_opens_after_threshold_failures(self):
        cb = CircuitBreaker(threshold=3, reset_s=999)
        for _ in range(3):
            cb.record_failure()
        assert cb.is_open

    def test_resets_after_success(self):
        cb = CircuitBreaker(threshold=3, reset_s=999)
        cb.record_failure()
        cb.record_failure()
        cb.record_success()
        assert not cb.is_open

    def test_does_not_open_below_threshold(self):
        cb = CircuitBreaker(threshold=3, reset_s=999)
        cb.record_failure()
        cb.record_failure()
        assert not cb.is_open


class TestNoOpOrchestrator:
    def test_not_available(self):
        orch = NoOpOrchestrator()
        assert not orch.is_available()

    async def test_returns_empty_crew_result(self):
        orch = NoOpOrchestrator()
        ctx = PipelineContext()
        result = await orch.execute_agents(ctx)
        assert isinstance(result, CrewResult)
        assert result.agents_executed == 0


class TestFraudCopilotOrchestrator:
    def test_not_available_without_copilot(self):
        orch = FraudCopilotOrchestrator()
        assert not orch.is_available()


class TestJSONParser:
    def test_valid_json_parsed(self):
        raw = json.dumps({
            "agent": "A",
            "new_evidence": [
                {"code": "TEST", "description": "Test evidence",
                 "severity": "high", "confidence": 0.9}
            ],
            "hypotheses": ["Possible fraud"],
            "recommended_actions": ["Reject payment"],
            "confidence": 0.85,
            "reasoning": "Multiple indicators detected",
        })
        orch = CrewAIOrchestrator()
        finding = orch._parse_output("A", raw)
        assert finding is not None
        assert finding.agent_name == "A"
        assert len(finding.evidence) == 1
        assert finding.evidence[0].code == "TEST"
        assert finding.evidence[0].severity == Severity.HIGH
        assert finding.confidence == 0.85

    def test_json_with_text_wrapper(self):
        raw = 'Some text before\n{"agent": "B", "new_evidence": [], "hypotheses": [], "confidence": 0.5, "reasoning": "ok"}\nMore text after'
        orch = CrewAIOrchestrator()
        finding = orch._parse_output("B", raw)
        assert finding is not None
        assert finding.agent_name == "B"

    def test_invalid_json_returns_none(self):
        orch = CrewAIOrchestrator()
        finding = orch._parse_output("C", "Not JSON at all")
        assert finding is None

    def test_score_field_ignored(self):
        raw = json.dumps({
            "agent": "A",
            "score": 95,
            "risk_score": 100,
            "classification": "HIGH",
            "new_evidence": [],
            "hypotheses": [],
            "confidence": 0.5,
            "reasoning": "test",
        })
        orch = CrewAIOrchestrator()
        finding = orch._parse_output("A", raw)
        assert finding is not None
        # Score fields were ignored, finding is still valid
        assert finding.confidence == 0.5

    def test_agent_finding_has_no_score_field(self):
        finding = AgentFinding(agent_name="Test")
        d = finding.to_dict()
        forbidden = ["score", "risk_score", "final_score", "classification", "risk_level"]
        for key in forbidden:
            assert key not in d, f"AgentFinding has forbidden field: {key}"


class TestEvidenceSourceWeight:
    def test_crewai_evidence_is_tagged(self):
        ev = Evidence(
            code="AI_FINDING", description="AI found something",
            severity=Severity.HIGH, source=EvidenceSource.CREWAI, confidence=0.8,
        )
        assert ev.source == EvidenceSource.CREWAI

    def test_deterministic_evidence_is_tagged(self):
        ev = Evidence(
            code="BANCO_INVALIDO", description="Banco invalido",
            severity=Severity.CRITICAL, source=EvidenceSource.DETERMINISTIC, confidence=1.0,
        )
        assert ev.source == EvidenceSource.DETERMINISTIC


class TestPipelineContextWithAgentFindings:
    def test_agent_findings_added_to_context(self):
        ctx = PipelineContext()
        finding = AgentFinding(
            agent_name="FraudAnalyst",
            evidence=[Evidence(code="AI_FOUND", description="AI discovery",
                               severity=Severity.HIGH, source=EvidenceSource.CREWAI)],
        )
        ctx.add_evidences(finding.evidence)
        ctx.agent_findings.append(finding.to_dict())
        assert len(ctx.evidences) >= 1
        assert ctx.evidences[0].source == EvidenceSource.CREWAI

    def test_crew_result_stored_in_context(self):
        ctx = PipelineContext()
        cr = CrewResult(agents_executed=3, agents_failed=0)
        ctx.crew_result = cr.to_dict()
        assert ctx.crew_result["agents_executed"] == 3
