# ============================================================
# PaySentinelIQ — Fusion Engine
# ============================================================
# Architecture Hardening: The SINGLE component responsible for
# converting Evidence[] → final risk score.
#
# Key principles:
#   1. Only component that produces a score from evidence
#   2. Evidence-source trust hierarchy (deterministic > external > heuristic > AI)
#   3. Weighted fusion with confidence multipliers
#   4. Complete explainability — every point in the score is traceable
#
# In Fase 1.5 this is a SKELETON — it replaces NO existing code.
# In Fase 3 it will replace all max() calls with proper fusion.
# ============================================================

from __future__ import annotations

from typing import Any

from app.core.contracts.evidence import Evidence, Severity, EvidenceSource
from app.core.contracts.pipeline_result import EvidenceContribution
from app.services.scoring.threshold_provider import ThresholdProvider, get_thresholds


class FusionEngine:
    """Converts Evidence[] → risk score with full explainability.

    SINGLE source of truth for risk scoring. All pipeline scoring
    must go through this engine. No component may calculate its own score.

    3-dimensional weighting model:
        1. Severity weight (CRITICAL=35, HIGH=20, ...)
        2. Source confidence multiplier (deterministic=1.5, crewai=0.9)
        3. Evidence confidence (0.0-1.0 per evidence item)
    """

    # ── Severity weights ──
    SEVERITY_WEIGHTS: dict[Severity, float] = {
        Severity.CRITICAL: 35.0,
        Severity.HIGH: 20.0,
        Severity.MEDIUM: 10.0,
        Severity.LOW: 5.0,
        Severity.INFO: 2.0,
    }

    # ── Source confidence multipliers ──
    SOURCE_MULTIPLIERS: dict[EvidenceSource, float] = {
        EvidenceSource.DETERMINISTIC: 1.5,
        EvidenceSource.BRASILAPI: 1.3,
        EvidenceSource.OCR: 1.2,
        EvidenceSource.HEURISTIC: 1.0,
        EvidenceSource.CREWAI: 0.9,
        EvidenceSource.USER: 0.8,
    }

    def __init__(self, thresholds: ThresholdProvider | None = None):
        self._thresholds = thresholds or get_thresholds()

    def fuse(self, evidences: list[Evidence]) -> dict[str, Any]:
        """Convert a list of Evidence into a final risk score.

        Args:
            evidences: All evidence collected across pipeline stages.

        Returns:
            Dict with final_score, final_level, contributions, explainability.
        """
        if not evidences:
            return self._empty_result()

        contributions = self._calculate_contributions(evidences)
        raw_score = sum(c.contribution for c in contributions)

        # ── Normalize ──
        # Cap at 100, but also apply a compound multiplier for multiple criticals
        critical_count = sum(1 for e in evidences if e.severity == Severity.CRITICAL)
        if critical_count >= 2:
            raw_score = min(raw_score * 1.2, 100.0)  # Multiple criticals compound

        final_score = round(min(raw_score, 100.0), 1)

        # ── Classify (via ThresholdProvider — single source of truth) ──
        level = self._thresholds.classify(final_score).value

        # ── Explainability ──
        source_breakdown = self._source_breakdown(contributions)
        severity_breakdown = self._severity_breakdown(evidences, contributions)

        return {
            "final_score": final_score,
            "final_level": level,
            "contributions": contributions,
            "weights": {
                "severity_weights": {k.value: v for k, v in self.SEVERITY_WEIGHTS.items()},
                "source_multipliers": {k.value: v for k, v in self.SOURCE_MULTIPLIERS.items()},
            },
            "explainability": {
                "evidence_count": len(evidences),
                "critical_count": critical_count,
                "high_count": sum(1 for e in evidences if e.severity == Severity.HIGH),
                "medium_count": sum(1 for e in evidences if e.severity == Severity.MEDIUM),
                "source_breakdown": source_breakdown,
                "severity_breakdown": severity_breakdown,
                "compound_multiplier": 1.2 if critical_count >= 2 else 1.0,
            },
        }

    def _calculate_contributions(
        self, evidences: list[Evidence]
    ) -> list[EvidenceContribution]:
        """Calculate how much each evidence contributes to the final score."""
        contributions = []
        for ev in evidences:
            weight = self.SEVERITY_WEIGHTS.get(ev.severity, 2.0)
            multiplier = self.SOURCE_MULTIPLIERS.get(ev.source, 1.0)
            contribution = weight * multiplier * ev.confidence
            contributions.append(EvidenceContribution(
                evidence_code=ev.code,
                source=ev.source.value,
                severity=ev.severity.value,
                base_weight=weight,
                confidence=ev.confidence,
                multiplier=multiplier,
                contribution=round(contribution, 2),
                explanation=(
                    f"{ev.severity.value.upper()} evidence from {ev.source.value}: "
                    f"weight={weight} × multiplier={multiplier} × confidence={ev.confidence} "
                    f"= {contribution:.1f}"
                ),
            ))
        return contributions

    def _source_breakdown(
        self, contributions: list[EvidenceContribution]
    ) -> dict[str, float]:
        """Break down score by evidence source."""
        breakdown: dict[str, float] = {}
        for c in contributions:
            breakdown[c.source] = breakdown.get(c.source, 0.0) + c.contribution
        return {k: round(v, 1) for k, v in breakdown.items()}

    def _severity_breakdown(
        self, evidences: list[Evidence], contributions: list[EvidenceContribution]
    ) -> dict[str, dict[str, Any]]:
        """Break down score by severity level."""
        breakdown: dict[str, dict[str, Any]] = {}
        for ev, c in zip(evidences, contributions):
            sev = ev.severity.value
            if sev not in breakdown:
                breakdown[sev] = {"count": 0, "total_contribution": 0.0, "evidence_codes": []}
            breakdown[sev]["count"] += 1
            breakdown[sev]["total_contribution"] = round(
                breakdown[sev]["total_contribution"] + c.contribution, 1
            )
            breakdown[sev]["evidence_codes"].append(ev.code)
        return breakdown

    def _empty_result(self) -> dict[str, Any]:
        return {
            "final_score": 0.0,
            "final_level": "LOW",
            "contributions": [],
            "weights": {},
            "explainability": {
                "evidence_count": 0,
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "source_breakdown": {},
                "severity_breakdown": {},
                "compound_multiplier": 1.0,
            },
        }
