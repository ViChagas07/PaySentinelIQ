# ============================================================
# PaySentinelIQ — Shadow Runner
# ============================================================
# Executes legacy and canonical pipelines side-by-side.
# User sees legacy result. Canonical result is logged for comparison.
# Controlled by ENABLE_SHADOW_PIPELINE feature flag.
# ============================================================

from __future__ import annotations

import time
import logging
from typing import Any

from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_result import PipelineResult
from app.services.pipeline.pipeline_comparison import PipelineComparison

logger = logging.getLogger(__name__)


class ShadowRunner:
    """Runs legacy + canonical pipelines, compares results.

    Usage:
        runner = ShadowRunner()
        legacy_result = await legacy_pipeline.process_document(...)
        comparison = await runner.run_shadow(file_bytes, doc_type, tenant_id, legacy_result)
    """

    def __init__(self, canonical_pipeline=None):
        self._canonical = canonical_pipeline

    async def run_shadow(
        self,
        file_data: bytes,
        document_type: str,
        tenant_id: str,
        legacy_result: dict[str, Any],
        file_name: str = "document.pdf",
        mime_type: str = "application/pdf",
    ) -> PipelineComparison:
        """Run canonical pipeline in shadow mode. Returns comparison, not result."""

        from app.services.pipeline.canonical_pipeline import CanonicalPipeline

        canonical = self._canonical or CanonicalPipeline()

        ctx = PipelineContext(
            file_bytes=file_data,
            document_type=document_type,
            tenant_id=tenant_id,
            filename=file_name,
            mime_type=mime_type,
        )

        # ── Run canonical pipeline ──
        t0 = time.monotonic()
        try:
            canonical_result = canonical.execute(ctx)
            canonical_ok = True
        except Exception as e:
            logger.error("Shadow canonical pipeline failed: %s", e)
            canonical_result = PipelineResult()
            canonical_ok = False
        canonical_time = (time.monotonic() - t0) * 1000

        # ── Extract legacy scores ──
        legacy_score = legacy_result.get("risk_score", legacy_result.get(
            "stages", {}).get("risk_analysis", {}).get("risk_score", 0))
        legacy_level = legacy_result.get("risk_level", legacy_result.get(
            "stages", {}).get("risk_analysis", {}).get("risk_level", "LOW"))
        legacy_time = legacy_result.get("processing_time_seconds", 0) * 1000

        # ── Build comparison ──
        comparison = PipelineComparison(
            document_id=ctx.document_id,
            document_type=document_type,
            legacy_score=float(legacy_score),
            legacy_level=str(legacy_level),
            legacy_time_ms=legacy_time,
            legacy_anomalies=len(legacy_result.get("stages", {}).get("risk_analysis", {}).get("flags", [])),
            legacy_status=legacy_result.get("pipeline_status", "unknown"),
            canonical_score=canonical_result.risk_score,
            canonical_level=canonical_result.risk_level,
            canonical_time_ms=round(canonical_time),
            canonical_evidence=len(canonical_result.evidence),
            canonical_status=canonical_result.pipeline_status.value if canonical_ok else "failed",
            crewai_executed=len(canonical_result.agent_findings) > 0,
            brasilapi_executed=bool(ctx.metadata.get("brasilapi_pending")),
            ocr_executed=bool(ctx.extracted_text),
            agents_executed=len(canonical_result.agent_findings),
            warnings=ctx.warnings,
            errors=ctx.errors,
        )

        # ── Log comparison ──
        logger.info(
            "SHADOW: doc=%s legacy=%.1f/%s canonical=%.1f/%s delta=%.1f match=%s",
            ctx.document_id[:8], comparison.legacy_score, comparison.legacy_level,
            comparison.canonical_score, comparison.canonical_level,
            comparison.score_delta, comparison.score_match,
        )

        if comparison.is_significant_divergence():
            logger.warning(
                "SHADOW DIVERGENCE: doc=%s delta=%.1f — legacy=%.1f canonical=%.1f",
                ctx.document_id[:8], comparison.score_delta,
                comparison.legacy_score, comparison.canonical_score,
            )

        return comparison
