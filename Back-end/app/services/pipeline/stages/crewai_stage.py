# ============================================================
# PaySentinelIQ — CrewAI Stage (Fase 2)
# ============================================================
# Stage 6: Executes AI agents via AIOrchestrationPort.
# Adds agent discoveries as Evidence to PipelineContext.
# NEVER produces a score — only enriches context with AI evidence.
# ============================================================

from __future__ import annotations

import asyncio
import logging

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.agent_result import CrewResult

logger = logging.getLogger(__name__)


class CrewAIStage(BaseStage):
    """Stage 6: AI Agent Execution via AIOrchestrationPort.

    Receives PipelineContext with deterministic evidence.
    Passes it to the AI orchestrator (CrewAI or FraudCopilot).
    Adds agent-found Evidence to context.evidences.
    Records agent findings in context.agent_findings.

    Degrades gracefully: if orchestrator unavailable, stage
    completes successfully with empty findings — pipeline continues.
    """

    def __init__(self, orchestrator=None):
        super().__init__(name="CrewAIStage")
        self._orchestrator = orchestrator  # AIOrchestrationPort

    def _execute(self, context: PipelineContext) -> None:
        orchestrator = self._get_orchestrator()
        if orchestrator is None or not orchestrator.is_available():
            context.add_warning("AI orchestrator unavailable — skipping AI agents")
            return

        try:
            # Run async orchestration in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context — create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, orchestrator.execute_agents(context))
                    crew_result: CrewResult = future.result(timeout=130)
            else:
                crew_result = asyncio.run(orchestrator.execute_agents(context))
        except Exception as e:
            context.add_warning(f"CrewAI stage failed: {e}")
            context.agent_findings = []
            return

        if crew_result is None:
            crew_result = CrewResult()

        # ── Add agent evidence to context ──
        for af in crew_result.agent_findings:
            context.add_evidences(af.evidence)
            context.agent_findings.append(af.to_dict())

        # ── Update crew_result in context ──
        context.crew_result = crew_result.to_dict()

        logger.info(
            "CrewAI stage: agents=%d failed=%d evidence=%d",
            crew_result.agents_executed, crew_result.agents_failed,
            len(crew_result.total_evidence),
        )

    def _get_orchestrator(self):
        """Get the orchestrator — injected or created lazily."""
        if self._orchestrator is not None:
            return self._orchestrator

        try:
            from app.ai_agents.orchestrator import CrewAIOrchestrator
            self._orchestrator = CrewAIOrchestrator()
            return self._orchestrator
        except Exception as e:
            logger.warning("Could not create CrewAIOrchestrator: %s", e)
            return None
