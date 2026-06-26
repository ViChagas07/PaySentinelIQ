# ============================================================
# PaySentinelIQ — AI Agent Result Contracts
# ============================================================
# Architecture Hardening: CrewAI agents produce Evidence, NEVER scores.
# The FusionEngine is the ONLY component that converts Evidence → score.
# These contracts enforce that separation.
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.contracts.evidence import Evidence


@dataclass
class AgentFinding:
    """Output from a SINGLE CrewAI agent.

    Each agent produces:
    - New evidence discovered during analysis
    - Correlated connections between existing evidence
    - Investigative hypotheses
    - Recommended actions

    AGENTS NEVER PRODUCE:
    - final_score
    - risk_level
    - classification
    These belong to the FusionEngine.
    """

    agent_name: str
    evidence: list[Evidence] = field(default_factory=list)
    correlated_evidence: list[str] = field(default_factory=list)
    hypotheses: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning: str = ""
    execution_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "evidence": [e.to_dict() for e in self.evidence],
            "correlated_evidence": self.correlated_evidence,
            "hypotheses": self.hypotheses,
            "recommended_actions": self.recommended_actions,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "execution_time_ms": self.execution_time_ms,
        }


@dataclass
class CrewResult:
    """Aggregated output from ALL CrewAI agents.

    Contains findings from every agent that executed.
    Does NOT contain a final score — FusionEngine determines that.
    """

    agent_findings: list[AgentFinding] = field(default_factory=list)
    total_evidence: list[Evidence] = field(default_factory=list)
    execution_time_ms: float = 0.0
    agents_executed: int = 0
    agents_failed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_findings": [af.to_dict() for af in self.agent_findings],
            "total_evidence": [e.to_dict() for e in self.total_evidence],
            "execution_time_ms": self.execution_time_ms,
            "agents_executed": self.agents_executed,
            "agents_failed": self.agents_failed,
        }
