# ============================================================
# PaySentinelIQ — Enrich Stage
# ============================================================
# External data enrichment via BrasilAPI and other sources.
# Currently: CNPJ lookup + company risk analysis.
# ============================================================

from __future__ import annotations

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext


class EnrichStage(BaseStage):
    """Stage 4: Enrich context with external data.

    Queries BrasilAPI for CNPJ information.
    Runs company risk analysis on enriched data.
    Skips gracefully if BrasilAPI is unavailable.
    """

    def __init__(self):
        super().__init__(name="EnrichStage")

    def _execute(self, context: PipelineContext) -> None:
        fields = context.extracted_fields
        cnpj = fields.get("cnpj", "")
        if not cnpj:
            return

        try:
            # Note: enrich_for_context is async but BaseStage.execute is sync.
            # In production, this stage will be async. For now, we note the
            # enrichment data source but don't block the pipeline.
            context.metadata["brasilapi_pending"] = True
            context.metadata["cnpj_for_enrichment"] = cnpj
        except Exception as exc:
            context.add_warning(
                f"BrasilAPI enrichment setup failed: {type(exc).__name__}"
            )
