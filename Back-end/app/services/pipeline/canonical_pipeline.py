# ============================================================
# PaySentinelIQ — Canonical Pipeline (Thin Orchestrator)
# ============================================================
# Architecture Hardening: This class contains ZERO business logic.
# It ONLY orchestrates stages in sequence.
#
# All rules live in:
#   - ValidateStage (deterministic validations)
#   - RiskStage (risk heuristics)
#   - FusionEngine (scoring algorithm)
#   - CrewAI agents (AI reasoning — Fase 2)
# ============================================================

from __future__ import annotations

import time
import logging
from typing import Any

from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.core.contracts.pipeline_status import PipelineStatus
from app.services.pipeline.stages.ingest_stage import IngestStage
from app.services.pipeline.stages.extract_stage import ExtractStage
from app.services.pipeline.stages.validate_stage import ValidateStage
from app.services.pipeline.stages.enrich_stage import EnrichStage
from app.services.pipeline.stages.risk_stage import RiskStage
from app.services.pipeline.stages.crewai_stage import CrewAIStage
from app.services.pipeline.event_bus import (
    PipelineEvent, PipelineEventType, PipelineEventBus,
)

logger = logging.getLogger(__name__)


class CanonicalPipeline:
    """Thin orchestrator for the 6-stage pipeline.

    Stages:
        1. Ingest — validate file, setup identity
        2. Extract — OCR, structured fields, metadata
        3. Validate — FEBRABAN, CNPJ, dates, values (deterministic)
        4. Enrich — BrasilAPI external data
        5. Risk — RiskAnalyzer + FusionEngine scoring
        6. CrewAI — 5 AI agents (A-E), parallel A,B,C (if LLM available)

    ZERO business logic. Dependency injection for all stages.
    Integrated with PipelineEventBus for observability.
    """

    def __init__(
        self,
        ingest: IngestStage | None = None,
        extract: ExtractStage | None = None,
        validate: ValidateStage | None = None,
        enrich: EnrichStage | None = None,
        risk: RiskStage | None = None,
        crewai: CrewAIStage | None = None,
        event_bus: PipelineEventBus | None = None,
    ):
        self._stages: list[Any] = [
            ingest or IngestStage(),
            extract or ExtractStage(),
            validate or ValidateStage(),
            enrich or EnrichStage(),
            risk or RiskStage(),
            crewai or CrewAIStage(),
        ]
        self._event_bus = event_bus or PipelineEventBus()
        self._setup_default_subscribers()

    def _setup_default_subscribers(self) -> None:
        """Register built-in event subscribers (logging + optional metrics)."""
        from app.services.pipeline.event_bus import create_logging_subscriber
        self._event_bus.subscribe(create_logging_subscriber())

    @property
    def event_bus(self) -> PipelineEventBus:
        return self._event_bus

    def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute ALL stages sequentially on the given context."""
        start = time.monotonic()
        doc_id = context.document_id[:8]

        # ── Pipeline started ──
        self._event_bus.publish(PipelineEvent(
            PipelineEventType.PIPELINE_STARTED,
            document_id=context.document_id,
            correlation_id=context.correlation_id,
        ))

        for stage in self._stages:
            logger.debug("Executing stage: %s", stage.name)

            # ── Stage started ──
            self._event_bus.publish(PipelineEvent(
                PipelineEventType.STAGE_STARTED,
                document_id=context.document_id,
                correlation_id=context.correlation_id,
                stage_name=stage.name,
            ))

            try:
                context = stage.execute(context)

                # ── Stage finished ──
                self._event_bus.publish(PipelineEvent(
                    PipelineEventType.STAGE_FINISHED,
                    document_id=context.document_id,
                    stage_name=stage.name,
                    data={"duration": context.processing_times.get(stage.name, 0)},
                ))
            except Exception as e:
                logger.error("Stage %s crashed: %s", stage.name, e)
                context.add_error(f"Stage {stage.name}: {e}")
                context.pipeline_status = PipelineStatus.PARTIAL

                self._event_bus.publish(PipelineEvent(
                    PipelineEventType.STAGE_FAILED,
                    document_id=context.document_id,
                    stage_name=stage.name,
                    data={"error": str(e)},
                ))

        context.mark_completed()
        elapsed = time.monotonic() - start

        result = self._build_result(context, elapsed)

        # ── Pipeline finished ──
        final_event_type = (
            PipelineEventType.PIPELINE_FAILED if context.pipeline_status == PipelineStatus.FAILED
            else PipelineEventType.PIPELINE_PARTIAL if context.pipeline_status == PipelineStatus.PARTIAL
            else PipelineEventType.PIPELINE_FINISHED
        )
        self._event_bus.publish(PipelineEvent(
            final_event_type,
            document_id=context.document_id,
            correlation_id=context.correlation_id,
            data={"score": result.risk_score, "level": result.risk_level,
                  "time": result.processing_time_seconds},
        ))

        logger.info("Pipeline %s: score=%.1f level=%s time=%.1fs",
                     doc_id, result.risk_score, result.risk_level, elapsed)
        return result

    def _build_result(self, ctx: PipelineContext, elapsed: float) -> PipelineResult:
        """Build PipelineResult from PipelineContext.

        Delegates to FusionEngine for score computation if available,
        otherwise uses context.deterministic_score directly.
        """
        # ── Compute final score via FusionEngine ──
        try:
            from app.services.scoring.fusion_engine import FusionEngine

            fusion = FusionEngine()
            fusion_result = fusion.fuse(ctx.evidences)
            final_score = fusion_result["final_score"]
            final_level = fusion_result["final_level"]
            contributions = fusion_result.get("contributions", [])
            explainability = fusion_result.get("explainability", {})
            weights = fusion_result.get("weights", {})
        except Exception:
            # Fallback: use deterministic score from RiskStage
            final_score = ctx.deterministic_score
            final_level = ctx.risk_level
            contributions = []
            explainability = {}
            weights = {}

        return PipelineResult(
            pipeline_status=ctx.pipeline_status,
            document_id=ctx.document_id,
            document_type=ctx.document_type,
            risk_score=final_score,
            risk_level=final_level,
            confidence=ctx.ocr_confidence,
            evidence=list(ctx.evidences),
            evidence_contributions=contributions,
            fusion_weights=weights,
            explainability=explainability,
            reasoning_summary=ctx.metadata.get("reasoning", ""),
            recommendations=self._build_recommendations(final_level, ctx),
            processing_time_seconds=round(elapsed, 2),
            warnings=ctx.warnings,
            errors=ctx.errors,
            analysis_timestamp=ctx.completed_at,
        )

    @staticmethod
    def _build_recommendations(level: str, ctx: PipelineContext) -> list[str]:
        if level == "HIGH":
            return [
                "REJEITAR: Alta probabilidade de fraude. Não efetue o pagamento.",
                "Escale para o time de compliance imediatamente.",
                "Reportar ao BACEN via canal de denúncia se confirmação de fraude.",
            ]
        elif level == "MEDIUM":
            return [
                "REVISAR: Anomalias detectadas. Requisitar confirmação do beneficiário.",
                "Validar dados cadastrais antes de processar pagamento.",
            ]
        return ["APROVADO: Nenhum indicador crítico detectado. Verificar manualmente em caso de valor elevado."]
