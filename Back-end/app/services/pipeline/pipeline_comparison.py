# ============================================================
# PaySentinelIQ — Pipeline Comparison (Shadow Mode)
# ============================================================
# Records and compares legacy vs canonical pipeline results.
# Used by ShadowRunner to detect regressions.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PipelineComparison:
    """Result of running legacy and canonical pipelines side-by-side.

    The legacy score is what the user sees.
    The canonical score is logged for comparison.
    If they diverge significantly, an alert is raised.
    """

    document_id: str = ""
    document_type: str = ""

    # ── Legacy Pipeline ──
    legacy_score: float = 0.0
    legacy_level: str = ""
    legacy_time_ms: float = 0.0
    legacy_anomalies: int = 0
    legacy_status: str = ""

    # ── Canonical Pipeline ──
    canonical_score: float = 0.0
    canonical_level: str = ""
    canonical_time_ms: float = 0.0
    canonical_evidence: int = 0
    canonical_status: str = ""
    crewai_executed: bool = False
    brasilapi_executed: bool = False
    ocr_executed: bool = False
    agents_executed: int = 0

    # ── Comparison ──
    score_delta: float = 0.0  # canonical - legacy
    level_match: bool = False
    score_match: bool = False

    # ── Metadata ──
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.score_delta = round(self.canonical_score - self.legacy_score, 1)
        self.score_match = abs(self.score_delta) < 1.0
        self.level_match = self.canonical_level == self.legacy_level

    def is_significant_divergence(self, threshold: float = 10.0) -> bool:
        """True if canonical and legacy scores diverge by more than threshold."""
        return abs(self.score_delta) > threshold

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "legacy": {
                "score": self.legacy_score, "level": self.legacy_level,
                "time_ms": self.legacy_time_ms, "anomalies": self.legacy_anomalies,
                "status": self.legacy_status,
            },
            "canonical": {
                "score": self.canonical_score, "level": self.canonical_level,
                "time_ms": self.canonical_time_ms, "evidence": self.canonical_evidence,
                "status": self.canonical_status,
                "crewai_executed": self.crewai_executed,
                "brasilapi_executed": self.brasilapi_executed,
                "ocr_executed": self.ocr_executed,
                "agents_executed": self.agents_executed,
            },
            "comparison": {
                "score_delta": self.score_delta,
                "level_match": self.level_match,
                "score_match": self.score_match,
                "significant_divergence": self.is_significant_divergence(),
            },
            "warnings": self.warnings, "errors": self.errors,
        }
