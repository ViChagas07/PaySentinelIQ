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

    Runs in BACKGROUND mode by default — does NOT block the HTTP response.
    Deterministic score is always returned immediately. AI agents enrich
    the analysis asynchronously.

    Receives PipelineContext with deterministic evidence.
    Passes it to the AI orchestrator (CrewAI or FraudCopilot).
    Adds agent-found Evidence to context.evidences.
    Records agent findings in context.agent_findings.

    Degrades gracefully: if orchestrator unavailable, stage
    completes successfully with empty findings — pipeline continues.
    """

    def __init__(self, orchestrator=None, background: bool = True):
        super().__init__(name="CrewAIStage")
        self._orchestrator = orchestrator
        self._background = background  # True = fire-and-forget, False = sync

    def _execute(self, context: PipelineContext) -> None:
        orchestrator = self._get_orchestrator()
        if orchestrator is None or not orchestrator.is_available():
            context.add_warning("AI orchestrator unavailable — deterministic-only mode")
            context.metadata["agents_mode"] = "unavailable"
            return

        if self._background:
            # ── Background mode: fire-and-forget, don't block ──
            self._launch_background(context, orchestrator)
            context.add_warning("AI agents running in background — results will enrich analysis asynchronously")
            context.metadata["agents_mode"] = "background"
        else:
            # ── Sync mode: block until agents complete (for shadow/comparison) ──
            self._run_sync(context, orchestrator)

    def _launch_background(self, context: PipelineContext, orchestrator) -> None:
        """Fire agents in background thread. Does NOT block pipeline."""
        import threading

        def _bg_run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                crew_result = loop.run_until_complete(orchestrator.execute_agents(context))
                if crew_result:
                    for af in crew_result.agent_findings:
                        context.add_evidences(af.evidence)
                        context.agent_findings.append(af.to_dict())
                    context.crew_result = crew_result.to_dict()
                    logger.info(
                        "CrewAI background: agents=%d evidence=%d",
                        crew_result.agents_executed, len(crew_result.total_evidence),
                    )
            except Exception as e:
                logger.warning("CrewAI background failed: %s", e)

        thread = threading.Thread(target=_bg_run, daemon=True)
        thread.start()

    def _run_sync(self, context: PipelineContext, orchestrator) -> None:
        """Run agents synchronously. Blocks until complete or timeout."""
        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, orchestrator.execute_agents(context))
                crew_result: CrewResult = future.result(timeout=60)
        except Exception as e:
            context.add_warning(f"CrewAI sync failed: {e}")
            context.agent_findings = []
            return

        if crew_result is None:
            crew_result = CrewResult()

        for af in crew_result.agent_findings:
            context.add_evidences(af.evidence)
            context.agent_findings.append(af.to_dict())

        context.crew_result = crew_result.to_dict()
        context.metadata["agents_mode"] = "sync"

        logger.info(
            "CrewAI sync: agents=%d failed=%d evidence=%d",
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
