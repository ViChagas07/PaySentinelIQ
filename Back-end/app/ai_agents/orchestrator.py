# ============================================================
# PaySentinelIQ — AI Orchestration Port
# ============================================================
# Architecture Hardening: Abstraction layer for AI agent execution.
# Allows swapping between CrewAI, FraudCopilot, or future orchestrators
# without changing the CanonicalPipeline.
#
# The pipeline depends on AIOrchestrationPort (abstraction),
# NOT on CrewAIOrchestrator or FraudCopilot directly.
# ============================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.contracts.evidence import Evidence
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.agent_result import CrewResult


class AIOrchestrationPort(ABC):
    """Abstract port for AI agent execution.

    The CanonicalPipeline depends on this interface, not on any
    concrete implementation. This enables:
      - CrewAIOrchestrator (multi-agent via CrewAI)
      - FraudCopilotOrchestrator (single-agent via FraudCopilot)
      - NoOpOrchestrator (skip AI when LLM unavailable)
      - Future orchestrators (new frameworks, custom agents)
    """

    @abstractmethod
    async def execute_agents(
        self,
        context: PipelineContext,
    ) -> CrewResult:
        """Execute AI agents on the given pipeline context.

        Args:
            context: PipelineContext with all previous stage outputs.

        Returns:
            CrewResult containing agent findings and new evidence.
            NEVER contains a final score — that's FusionEngine's job.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the orchestrator is healthy and ready."""
        ...

    @abstractmethod
    def get_info(self) -> dict[str, Any]:
        """Return orchestrator metadata for diagnostics."""
        ...


class NoOpOrchestrator(AIOrchestrationPort):
    """No-op orchestrator — used when LLM is unavailable.

    Returns empty CrewResult. Does NOT block the pipeline.
    The FusionEngine will use only deterministic evidence.
    """

    async def execute_agents(self, context: PipelineContext) -> CrewResult:
        return CrewResult()

    def is_available(self) -> bool:
        return False

    def get_info(self) -> dict[str, Any]:
        return {
            "orchestrator": "NoOpOrchestrator",
            "status": "unavailable",
            "reason": "LLM provider not configured or unhealthy",
        }


class FraudCopilotOrchestrator(AIOrchestrationPort):
    """Adapter that wraps FraudCopilot as an AIOrchestrationPort.

    Preserves the existing FraudCopilot implementation while
    exposing it through the standard AIOrchestrationPort interface.

    The FraudCopilot is NOT removed — it's adapted.
    """

    def __init__(self, fraud_copilot: Any = None):
        self._copilot = fraud_copilot

    async def execute_agents(self, context: PipelineContext) -> CrewResult:
        if self._copilot is None:
            return CrewResult()

        try:
            # Build context for FraudCopilot
            request_data = {
                "document_type": context.document_type,
                "document_id": context.document_id,
                **context.extracted_fields,
            }
            report = await self._copilot.analyze_document(
                request_data=request_data,
                document_id=context.document_id,
            )

            # Convert FraudCopilot findings to AgentFinding format
            from app.core.contracts.agent_result import AgentFinding
            from app.core.contracts.evidence import Evidence, Severity, EvidenceSource

            evidence_list = []
            for finding in report.findings:
                sev = Severity(finding.severity) if finding.severity in Severity._value2member_map_ else Severity.INFO
                evidence_list.append(Evidence(
                    code=finding.title.upper().replace(" ", "_"),
                    description=finding.description,
                    severity=sev,
                    source=EvidenceSource.CREWAI,
                    confidence=report.confidence,
                    category="fraud_copilot",
                    rule_reference=finding.evidence,
                ))

            finding = AgentFinding(
                agent_name="FraudCopilot",
                evidence=evidence_list,
                recommended_actions=report.recommendations,
                confidence=report.confidence,
                reasoning=report.summary,
            )

            return CrewResult(
                agent_findings=[finding],
                total_evidence=evidence_list,
                agents_executed=1,
            )
        except Exception:
            return CrewResult(agents_failed=1)

    def is_available(self) -> bool:
        return self._copilot is not None and self._copilot.llm_available

    def get_info(self) -> dict[str, Any]:
        return {
            "orchestrator": "FraudCopilotOrchestrator",
            "status": "available" if self.is_available() else "unavailable",
            "copilot_configured": self._copilot is not None,
        }
