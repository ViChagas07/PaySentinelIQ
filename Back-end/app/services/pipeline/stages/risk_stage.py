# ============================================================
# PaySentinelIQ — Risk Stage
# ============================================================
# Deterministic risk assessment.
# Feeds Evidence[] to the FusionEngine to produce initial score.
# This stage is the bridge between validation and scoring.
# ============================================================

from __future__ import annotations

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.evidence import Severity


class RiskStage(BaseStage):
    """Stage 5: Deterministic risk assessment.

    Delegates to RiskAnalyzer for heuristic checks.
    Uses FusionEngine to convert Evidence[] → score.
    Sets context.deterministic_score and context.risk_level.
    """

    def __init__(self):
        super().__init__(name="RiskStage")

    def _execute(self, context: PipelineContext) -> None:
        # ── Run RiskAnalyzer for additional heuristics ──
        try:
            from app.services.ai.risk_analyzer import RiskAnalyzer

            analyzer = RiskAnalyzer()
            ocr_metadata = context.metadata.get("ocr")
            ocr_confidence: float | None = context.ocr_confidence
            if isinstance(ocr_metadata, dict) and ocr_metadata.get(
                "status"
            ) in {"failed", "empty", "not_needed"}:
                ocr_confidence = None
            risk_ctx = {
                "document_type": context.document_type,
                "cnpj": context.extracted_fields.get("cnpj"),
                "company_cnpj": context.extracted_fields.get("cnpj"),
                "amount": context.extracted_fields.get("amount"),
                "ocr_confidence": ocr_confidence,
                **context.extracted_fields,
            }
            assessment = analyzer.analyze(risk_ctx)

            # Convert RiskAnalyzer flags to Evidence
            for flag in assessment.flags:
                try:
                    flag_severity = Severity(str(flag.severity).lower())
                except ValueError:
                    flag_severity = Severity.MEDIUM
                context.add_evidence(
                    __import__("app.core.contracts.evidence", fromlist=["Evidence", "Severity", "EvidenceSource"]).Evidence(
                        code=flag.code,
                        description=flag.description,
                        severity=flag_severity,
                        source=__import__("app.core.contracts.evidence", fromlist=["EvidenceSource"]).EvidenceSource.DETERMINISTIC,
                        confidence=1.0,
                        category=flag.category,
                        rule_reference="RiskAnalyzer heuristics",
                    )
                )
        except Exception as e:
            context.add_warning(f"RiskAnalyzer failed: {e}")

        # ── Compute deterministic score via FusionEngine ──
        if context.evidences:
            try:
                from app.services.scoring.fusion_engine import FusionEngine

                fusion = FusionEngine()
                result = fusion.fuse(context.evidences)
                context.deterministic_score = result["final_score"]
                context.risk_level = result["final_level"]

                # Store explainability data
                context.metadata["fusion_result"] = result
            except Exception as e:
                context.add_warning(f"FusionEngine failed: {e}")
                # Fallback: simple severity-weighted score
                weights = {
                    Severity.CRITICAL: 35,
                    Severity.HIGH: 20,
                    Severity.MEDIUM: 10,
                    Severity.LOW: 5,
                    Severity.INFO: 2,
                }
                total = sum(weights.get(e.severity, 1) for e in context.evidences)
                context.deterministic_score = min(total, 100.0)
                if context.deterministic_score >= 70:
                    context.risk_level = "HIGH"
                elif context.deterministic_score >= 40:
                    context.risk_level = "MEDIUM"
                else:
                    context.risk_level = "LOW"
