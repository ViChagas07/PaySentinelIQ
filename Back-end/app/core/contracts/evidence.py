# ============================================================
# PaySentinelIQ — Evidence Contract
# ============================================================
# Architecture Hardening: Every fraud signal is an Evidence object.
# No more anonymous dicts. No more "flags" lists that lose metadata.
# All scoring components produce Evidence[] and the FusionEngine
# is the ONLY component that converts Evidence → score.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Severity of a fraud indicator.

    Weights (used ONLY by FusionEngine):
        CRITICAL = 35, HIGH = 20, MEDIUM = 10, LOW = 5, INFO = 2
    """
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class EvidenceSource(str, Enum):
    """Origin of the evidence — determines trust multiplier in FusionEngine.

    Trust hierarchy:
        deterministic > brasilapi > heuristic > crewai
    """
    DETERMINISTIC = "deterministic"    # Mathematical certainty (checksums, modulo 10/11)
    BRASILAPI = "brasilapi"            # Official government source (Receita Federal)
    HEURISTIC = "heuristic"            # Established heuristics (round amounts, generic names)
    CREWAI = "crewai"                  # AI agent analysis (lower trust weight)
    OCR = "ocr"                        # OCR quality signals
    USER = "user"                      # User-provided observations


@dataclass
class Evidence:
    """A single piece of fraud evidence.

    This is the universal currency of the PaySentinelIQ architecture.
    Every component produces Evidence. Only the FusionEngine consumes
    Evidence to produce a score.

    Attributes:
        code: Machine-readable identifier (e.g. "BANCO_INVALIDO_ISPB")
        description: Human-readable explanation (Portuguese for BR users)
        severity: How serious this finding is
        source: Where this evidence came from (determines trust weight)
        confidence: 0.0-1.0 — how certain we are about this finding
        category: Classification bucket ("structural", "entity", "financial", etc.)
        rule_reference: Citation of the rule/regulation violated
        metadata: Arbitrary extra data (line numbers, bounding boxes, raw values)
    """

    code: str
    description: str
    severity: Severity = Severity.INFO
    source: EvidenceSource = EvidenceSource.HEURISTIC
    confidence: float = 1.0
    category: str = ""
    rule_reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0-1, got {self.confidence}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "description": self.description,
            "severity": self.severity.value,
            "source": self.source.value,
            "confidence": self.confidence,
            "category": self.category,
            "rule_reference": self.rule_reference,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Evidence":
        return cls(
            code=data.get("code", "UNKNOWN"),
            description=data.get("description", ""),
            severity=Severity(data.get("severity", "info")),
            source=EvidenceSource(data.get("source", "heuristic")),
            confidence=data.get("confidence", 1.0),
            category=data.get("category", ""),
            rule_reference=data.get("rule_reference", ""),
            metadata=data.get("metadata", {}),
        )
