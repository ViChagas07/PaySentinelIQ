# ============================================================
# PaySentinelIQ — Explainability Engine (Fase 3B)
# ============================================================
# Explains HOW the FusionEngine arrived at a score.
# Does NOT calculate score. Only produces human-readable breakdowns.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.services.scoring.threshold_provider import ThresholdProvider, get_thresholds


@dataclass
class ContributionDetail:
    evidence_code: str
    source: str
    severity: str
    base_weight: float
    source_multiplier: float
    confidence: float
    contribution: float
    description: str = ""


@dataclass
class ExplainabilityResult:
    """Complete explainability output for a risk assessment."""

    score: float = 0.0
    level: str = ""
    contributions: list[ContributionDetail] = field(default_factory=list)
    source_breakdown: dict[str, float] = field(default_factory=dict)
    severity_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    deterministic_vs_ai: dict[str, float] = field(default_factory=dict)
    evidence_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    top_contributors: list[ContributionDetail] = field(default_factory=list)
    reasoning: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "level": self.level,
            "evidence_count": self.evidence_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "source_breakdown": self.source_breakdown,
            "severity_breakdown": self.severity_breakdown,
            "deterministic_vs_ai": self.deterministic_vs_ai,
            "top_contributors": [
                {"code": c.evidence_code, "source": c.source, "severity": c.severity,
                 "contribution": round(c.contribution, 1), "description": c.description}
                for c in self.top_contributors[:5]
            ],
            "reasoning": self.reasoning,
        }


class ExplainabilityEngine:
    """Explains FusionEngine results in human-readable detail.

    Usage:
        engine = ExplainabilityEngine()
        result = engine.explain(evidences, fusion_result, thresholds)
    """

    def __init__(self, thresholds: ThresholdProvider | None = None):
        self._thresholds = thresholds or get_thresholds()

    def explain(
        self,
        evidences: list[Evidence],
        fusion_result: dict[str, Any],
    ) -> ExplainabilityResult:
        """Generate a complete explainability breakdown."""
        score = fusion_result.get("final_score", 0.0)
        level = fusion_result.get("final_level", "LOW")
        contributions_raw = fusion_result.get("contributions", [])

        # Build contribution details
        contributions = self._build_contributions(evidences, contributions_raw)

        # Source breakdown
        source_breakdown = self._source_breakdown(contributions)

        # Severity breakdown
        severity_breakdown = self._severity_breakdown(evidences, contributions)

        # Deterministic vs AI
        det_vs_ai = self._deterministic_vs_ai(source_breakdown)

        # Evidence counts
        counts = self._count_by_severity(evidences)

        # Top contributors
        top = sorted(contributions, key=lambda c: c.contribution, reverse=True)[:5]

        # Auto-generated reasoning
        reasoning = self._generate_reasoning(score, level, counts, top)

        return ExplainabilityResult(
            score=score,
            level=level,
            contributions=contributions,
            source_breakdown=source_breakdown,
            severity_breakdown=severity_breakdown,
            deterministic_vs_ai=det_vs_ai,
            evidence_count=len(evidences),
            critical_count=counts.get("critical", 0),
            high_count=counts.get("high", 0),
            medium_count=counts.get("medium", 0),
            low_count=counts.get("low", 0) + counts.get("info", 0),
            top_contributors=top,
            reasoning=reasoning,
        )

    def _build_contributions(
        self, evidences: list[Evidence], raw_contributions: list[Any]
    ) -> list[ContributionDetail]:
        """Build ContributionDetail list from evidence and fusion result."""
        contributions = []
        for i, ev in enumerate(evidences):
            contrib = raw_contributions[i] if i < len(raw_contributions) else None
            cont_value = contrib.contribution if hasattr(contrib, 'contribution') else (
                contrib.get('contribution', 0) if isinstance(contrib, dict) else 0
            )
            base_w = contrib.base_weight if hasattr(contrib, 'base_weight') else (
                contrib.get('base_weight', 0) if isinstance(contrib, dict) else 0
            )
            mult = contrib.multiplier if hasattr(contrib, 'multiplier') else (
                contrib.get('multiplier', 1.0) if isinstance(contrib, dict) else 1.0
            )

            contributions.append(ContributionDetail(
                evidence_code=ev.code,
                source=ev.source.value,
                severity=ev.severity.value,
                base_weight=base_w,
                source_multiplier=mult,
                confidence=ev.confidence,
                contribution=cont_value,
                description=ev.description[:100],
            ))
        return contributions

    def _source_breakdown(self, contributions: list[ContributionDetail]) -> dict[str, float]:
        breakdown: dict[str, float] = {}
        for c in contributions:
            breakdown[c.source] = round(breakdown.get(c.source, 0.0) + c.contribution, 1)
        return breakdown

    def _severity_breakdown(
        self, evidences: list[Evidence], contributions: list[ContributionDetail]
    ) -> dict[str, dict[str, Any]]:
        breakdown: dict[str, dict[str, Any]] = {}
        for ev, c in zip(evidences, contributions):
            sev = ev.severity.value
            if sev not in breakdown:
                breakdown[sev] = {"count": 0, "total_contribution": 0.0, "codes": []}
            breakdown[sev]["count"] += 1
            breakdown[sev]["total_contribution"] = round(
                breakdown[sev]["total_contribution"] + c.contribution, 1
            )
            breakdown[sev]["codes"].append(ev.code)
        return breakdown

    def _deterministic_vs_ai(self, source_breakdown: dict[str, float]) -> dict[str, float]:
        det_total = source_breakdown.get("deterministic", 0.0) + source_breakdown.get("brasilapi", 0.0)
        ai_total = source_breakdown.get("crewai", 0.0)
        return {"deterministic": round(det_total, 1), "ai": round(ai_total, 1)}

    def _count_by_severity(self, evidences: list[Evidence]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for ev in evidences:
            counts[ev.severity.value] = counts.get(ev.severity.value, 0) + 1
        return counts

    def _generate_reasoning(
        self, score: float, level: str,
        counts: dict[str, int],
        top: list[ContributionDetail],
    ) -> str:
        parts = []
        critical = counts.get("critical", 0)
        high = counts.get("high", 0)
        medium = counts.get("medium", 0)

        if critical > 0:
            parts.append(f"{critical} evidencia(s) CRITICA(S) detectada(s)")
        if high > 0:
            parts.append(f"{high} evidencia(s) de ALTA severidade")
        if medium > 0 and critical == 0:
            parts.append(f"{medium} evidencia(s) de MEDIA severidade")

        parts.append(f"Score final: {score:.1f}/100 — Classificacao: {level}")

        if top:
            top_contributor = top[0]
            parts.append(
                f"Maior contribuicao: {top_contributor.evidence_code} "
                f"({top_contributor.source}, +{top_contributor.contribution:.1f} pontos)"
            )

        return ". ".join(parts)
