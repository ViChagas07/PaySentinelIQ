# ============================================================
# PaySentinelIQ — Pipeline Result (Backward-Compatible)
# ============================================================
# This is the FINAL output of the CanonicalPipeline.
# It supports BOTH the new structured format AND the legacy
# RISK_ASSESSMENT format used by the current frontend.
#
# Frontend sees: report["RISK_ASSESSMENT"]["fraud_risk_score"]
# New consumers see: result.risk_score, result.explainability
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.contracts.evidence import Evidence
from app.core.contracts.pipeline_status import PipelineStatus


@dataclass
class EvidenceContribution:
    """How much each evidence contributed to the final score."""
    evidence_code: str
    source: str
    severity: str
    base_weight: float
    confidence: float
    multiplier: float
    contribution: float
    explanation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_code": self.evidence_code,
            "source": self.source,
            "severity": self.severity,
            "base_weight": self.base_weight,
            "confidence": self.confidence,
            "multiplier": self.multiplier,
            "contribution": self.contribution,
            "explanation": self.explanation,
        }


@dataclass
class PipelineResult:
    """Final output of the CanonicalPipeline.

    This dataclass serializes to BOTH:
      - New format: { pipeline_status, risk_score, risk_level, evidence, ... }
      - Legacy format: { RISK_ASSESSMENT: { fraud_risk_score, ... } }

    The `to_dict()` method produces the new format.
    The `to_legacy_dict()` method produces the old format for backward compat.
    """

    # ── New Contract ──
    pipeline_status: PipelineStatus = PipelineStatus.SUCCESS
    document_id: str = ""
    document_type: str = "unknown"
    risk_score: float = 0.0
    risk_level: str = "LOW"
    confidence: float = 0.0
    evidence: list[Evidence] = field(default_factory=list)
    evidence_contributions: list[EvidenceContribution] = field(default_factory=list)
    fusion_weights: dict[str, float] = field(default_factory=dict)
    agent_findings: list[dict[str, Any]] = field(default_factory=list)
    explainability: dict[str, Any] = field(default_factory=dict)
    reasoning_summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    processing_time_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    analysis_timestamp: str = ""

    # ── Serialization ──

    def to_dict(self) -> dict[str, Any]:
        """New contract format — full structured output."""
        return {
            "pipeline_status": self.pipeline_status.value,
            "document_id": self.document_id,
            "document_type": self.document_type,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "confidence": self.confidence,
            "evidence": [e.to_dict() for e in self.evidence],
            "evidence_contributions": [c.to_dict() for c in self.evidence_contributions],
            "fusion_weights": self.fusion_weights,
            "agent_findings": self.agent_findings,
            "explainability": self.explainability,
            "reasoning_summary": self.reasoning_summary,
            "recommendations": self.recommendations,
            "processing_time_seconds": self.processing_time_seconds,
            "warnings": self.warnings,
            "errors": self.errors,
            "analysis_timestamp": self.analysis_timestamp,
            # Backward-compat aliases
            "RISK_ASSESSMENT": self._build_legacy_risk_assessment(),
            "ANOMALY_LIST": self._build_legacy_anomaly_list(),
            "AI_REASONING_SUMMARY": self.reasoning_summary,
        }

    def _build_legacy_risk_assessment(self) -> dict[str, Any]:
        """Build the legacy RISK_ASSESSMENT block for backward compat."""
        action = "ACCEPT"
        if self.risk_score >= 70:
            action = "REJECT"
        elif self.risk_score >= 40:
            action = "MANUAL_REVIEW"
        return {
            "fraud_risk_score": self.risk_score,
            "risk_classification": self.risk_level.upper(),
            "ai_confidence": self.confidence,
            "recommended_action": action,
        }

    def _build_legacy_anomaly_list(self) -> list[dict[str, Any]]:
        """Build the legacy ANOMALY_LIST for backward compat."""
        return [
            {
                "id": f"EVD-{i:04d}",
                "severity": e.severity.value,
                "category": e.category,
                "description": e.description,
                "evidence": e.rule_reference,
                "confidence": e.confidence * 100,
                "stage_detected": e.source.value,
            }
            for i, e in enumerate(self.evidence)
        ]

    def to_legacy_dict(self) -> dict[str, Any]:
        """Full legacy-format output (for deprecated endpoints)."""
        return {
            "DOCUMENT_METADATA": {
                "document_id": self.document_id,
                "document_type": self.document_type,
                "analysis_timestamp": self.analysis_timestamp,
            },
            "RISK_ASSESSMENT": self._build_legacy_risk_assessment(),
            "ANOMALY_LIST": self._build_legacy_anomaly_list(),
            "AI_REASONING_SUMMARY": self.reasoning_summary,
            "ANALYST_NOTES": (
                "Recomenda-se verificar o documento original diretamente com o emissor."
            ),
        }
