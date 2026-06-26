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

logger = logging.getLogger(__name__)


class CanonicalPipeline:
    """Thin orchestrator for the 5-stage deterministic pipeline.

    ZERO business logic. Only sequences stages and builds the
    final PipelineResult from PipelineContext.

    Usage:
        pipeline = CanonicalPipeline()
        context = PipelineContext(file_bytes=pdf_bytes, document_type="boleto")
        result = pipeline.execute(context)

    Future (Fase 2): Add Stage 6 (CrewAI) and Stage 7 (FusionEngine
    with explainability). These will be injected via constructor.
    """

    def __init__(
        self,
        ingest: IngestStage | None = None,
        extract: ExtractStage | None = None,
        validate: ValidateStage | None = None,
        enrich: EnrichStage | None = None,
        risk: RiskStage | None = None,
    ):
        self._stages: list[Any] = [
            ingest or IngestStage(),
            extract or ExtractStage(),
            validate or ValidateStage(),
            enrich or EnrichStage(),
            risk or RiskStage(),
        ]

    def execute(self, context: PipelineContext) -> PipelineResult:
        """Execute ALL stages sequentially on the given context.

        Stages cannot be skipped. If a stage fails, the pipeline
        continues with remaining stages (graceful degradation).
        Only OCR failure is fatal (no text = no analysis).

        Args:
            context: Initial PipelineContext with at least file_bytes set.

        Returns:
            PipelineResult with backward-compatible serialization.
        """
        start = time.monotonic()

        for stage in self._stages:
            logger.debug("Executing stage: %s", stage.name)
            try:
                context = stage.execute(context)
            except Exception as e:
                logger.error("Stage %s crashed: %s", stage.name, e)
                context.add_error(f"Stage {stage.name}: {e}")
                context.pipeline_status = PipelineStatus.PARTIAL

        context.mark_completed()
        elapsed = time.monotonic() - start

        return self._build_result(context, elapsed)

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
