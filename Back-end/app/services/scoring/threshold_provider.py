# ============================================================
# PaySentinelIQ — Threshold Provider (Fase 3B)
# ============================================================
# SINGLE source of truth for risk classification thresholds.
# Replaces 5+ different threshold definitions across the codebase.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


@dataclass(frozen=True)
class ThresholdProvider:
    """Immutable, injectable threshold configuration.

    Usage:
        tp = ThresholdProvider()
        level = tp.classify(72.5)  # → RiskLevel.HIGH
        action = tp.recommended_action(level)  # → "REJECT"
    """

    low_max: float = 39.0
    medium_max: float = 69.0
    # high starts at 70.0 (anything above medium_max)

    def classify(self, score: float) -> RiskLevel:
        """Classify a score into a risk level."""
        if score >= self.high_threshold:
            return RiskLevel.HIGH
        if score >= self.medium_threshold:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    @property
    def high_threshold(self) -> float:
        return 70.0  # >= 70 = HIGH

    @property
    def medium_threshold(self) -> float:
        return 40.0  # >= 40 = MEDIUM

    def recommended_action(self, level: RiskLevel) -> str:
        if level == RiskLevel.HIGH:
            return "REJECT"
        elif level == RiskLevel.MEDIUM:
            return "MANUAL_REVIEW"
        return "ACCEPT"

    def is_high_risk(self, score: float) -> bool:
        return score >= self.high_threshold

    def is_medium_or_higher(self, score: float) -> bool:
        return score >= self.medium_threshold

    def to_dict(self) -> dict:
        return {
            "low": f"0-{int(self.low_max)}",
            "medium": f"{int(self.medium_threshold)}-{int(self.medium_max)}",
            "high": f"{int(self.high_threshold)}+",
            "thresholds": {
                "low_max": self.low_max,
                "medium_max": self.medium_max,
                "high_min": self.high_threshold,
            }
        }


# ── Singleton (cached) ──
_default_thresholds = ThresholdProvider()


def get_thresholds() -> ThresholdProvider:
    """Get the default threshold provider. Override in tests."""
    return _default_thresholds
