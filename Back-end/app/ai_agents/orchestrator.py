# ============================================================
# PaySentinelIQ — AI Orchestration Layer (Fase 2)
# ============================================================
# AIOrchestrationPort: Abstract port (Fase 1.5)
# NoOpOrchestrator: Fallback when LLM unavailable
# FraudCopilotOrchestrator: Adapter preserving FraudCopilot
# CrewAIOrchestrator: Full 5-agent implementation
# ============================================================

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from abc import ABC, abstractmethod
from typing import Any

from app.core.contracts.agent_result import AgentFinding, CrewResult
from app.core.contracts.evidence import Evidence, EvidenceSource, Severity
from app.core.contracts.pipeline_context import PipelineContext

logger = logging.getLogger(__name__)

# ── Configuration ──
AGENT_TIMEOUT_S = 30.0
TOTAL_TIMEOUT_S = 120.0
MAX_RETRIES = 2
CB_THRESHOLD = 3
CB_RESET_S = 60.0


class CircuitBreaker:
    def __init__(self, threshold: int = CB_THRESHOLD, reset_s: float = CB_RESET_S):
        self._threshold = threshold
        self._reset_s = reset_s
        self._failures = 0
        self._last_failure = 0.0
        self._open = False

    @property
    def is_open(self) -> bool:
        if not self._open:
            return False
        if time.monotonic() - self._last_failure > self._reset_s:
            self._open = False
            self._failures = 0
        return self._open

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure = time.monotonic()
        if self._failures >= self._threshold:
            self._open = True

    def record_success(self) -> None:
        self._failures = 0
        self._open = False


# ═══════════════════════════════════════════════════════
# Abstract Port
# ═══════════════════════════════════════════════════════

class AIOrchestrationPort(ABC):
    @abstractmethod
    async def execute_agents(self, context: PipelineContext) -> CrewResult: ...
    @abstractmethod
    def is_available(self) -> bool: ...
    @abstractmethod
    def get_info(self) -> dict[str, Any]: ...


class NoOpOrchestrator(AIOrchestrationPort):
    async def execute_agents(self, context: PipelineContext) -> CrewResult:
        return CrewResult()
    def is_available(self) -> bool:
        return False
    def get_info(self) -> dict[str, Any]:
        return {"orchestrator": "NoOpOrchestrator", "status": "unavailable"}


class FraudCopilotOrchestrator(AIOrchestrationPort):
    def __init__(self, copilot: Any = None):
        self._copilot = copilot
    async def execute_agents(self, context: PipelineContext) -> CrewResult:
        return CrewResult()
    def is_available(self) -> bool:
        return self._copilot is not None and getattr(self._copilot, "llm_available", False)
    def get_info(self) -> dict[str, Any]:
        return {"orchestrator": "FraudCopilotOrchestrator", "available": self.is_available()}


# ═══════════════════════════════════════════════════════
# CrewAIOrchestrator — 5 Agents, Parallel A,B,C
# ═══════════════════════════════════════════════════════

class CrewAIOrchestrator(AIOrchestrationPort):
    """Full CrewAI integration. 5 agents: A(Fraud), B(Forensics), C(Compliance), D(Investigator), E(Reviewer).
    A,B,C run in PARALLEL. D and E sequential. All output JSON AgentFinding. Zero score fields."""

    def __init__(self):
        self._cb = CircuitBreaker()
        self._llm_available = False
        self._init_llm()

    # ── Public ──

    async def execute_agents(self, context: PipelineContext) -> CrewResult:
        if not self.is_available():
            return CrewResult()
        if self._cb.is_open:
            return CrewResult(agents_failed=5)

        start = time.monotonic()
        try:
            results_abc = await asyncio.wait_for(
                self._run_parallel(context, ["A", "B", "C"]),
                timeout=AGENT_TIMEOUT_S * 2,
            )
            finding_d = await self._retry_agent("D", context, results_abc)
            all_findings = [f for f in results_abc.values() if f] + ([finding_d] if finding_d else [])
            finding_e = await self._retry_agent("E", context, all_findings)

            agent_findings = [f for f in list(results_abc.values()) if f]
            if finding_d: agent_findings.append(finding_d)
            if finding_e: agent_findings.append(finding_e)

            total_evidence: list[Evidence] = []
            for af in agent_findings:
                total_evidence.extend(af.evidence)

            self._cb.record_success()
            return CrewResult(
                agent_findings=agent_findings,
                total_evidence=total_evidence,
                execution_time_ms=round((time.monotonic() - start) * 1000),
                agents_executed=len(agent_findings),
                agents_failed=5 - len(agent_findings),
            )
        except asyncio.TimeoutError:
            self._cb.record_failure()
            return CrewResult(agents_failed=5)
        except Exception as e:
            logger.error("CrewAI crashed: %s", e)
            self._cb.record_failure()
            return CrewResult(agents_failed=5)

    def is_available(self) -> bool:
        return self._llm_available and not self._cb.is_open

    def get_info(self) -> dict[str, Any]:
        return {"orchestrator": "CrewAIOrchestrator", "llm_healthy": self._llm_available,
                "circuit_open": self._cb.is_open}

    # ── LLM Init ──

    def _init_llm(self) -> None:
        try:
            from app.shared.settings import get_settings
            if not get_settings().ENABLE_AI_AGENTS:
                return
            from app.providers.factory import get_crewai_llm, get_llm_provider
            llm = get_crewai_llm()
            if llm:
                provider = get_llm_provider()
                self._llm_available = provider.health_check()
        except Exception as e:
            logger.warning("LLM init failed: %s", e)

    # ── Parallel ──

    async def _run_parallel(self, ctx: PipelineContext, names: list[str]) -> dict[str, AgentFinding | None]:
        tasks = {n: self._retry_agent(n, ctx) for n in names}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        out: dict[str, AgentFinding | None] = {}
        for (n, _), r in zip(tasks.items(), results):
            out[n] = None if isinstance(r, Exception) else r
        return out

    # ── Retry ──

    async def _retry_agent(
        self, name: str, ctx: PipelineContext,
        prev: list[AgentFinding] | dict[str, AgentFinding | None] | None = None,
        timeout: float = AGENT_TIMEOUT_S,
    ) -> AgentFinding | None:
        for attempt in range(MAX_RETRIES + 1):
            try:
                result = await asyncio.wait_for(self._run_one(name, ctx, prev), timeout=timeout)
                if result:
                    return result
            except asyncio.TimeoutError:
                logger.warning("Agent %s timeout (attempt %d)", name, attempt + 1)
            except Exception as e:
                logger.warning("Agent %s error (attempt %d): %s", name, attempt + 1, e)
            if attempt < MAX_RETRIES:
                await asyncio.sleep(2 ** attempt)
        return None

    # ── Single Agent ──

    async def _run_one(
        self, name: str, ctx: PipelineContext,
        prev: list[AgentFinding] | dict[str, AgentFinding | None] | None = None,
    ) -> AgentFinding | None:
        from app.ai_agents.agent_prompts import (
            get_prompt_fraud_analyst, get_prompt_forensics, get_prompt_compliance,
            get_prompt_investigator, get_prompt_reviewer,
        )
        prompts = {
            "A": get_prompt_fraud_analyst(),
            "B": get_prompt_forensics(),
            "C": get_prompt_compliance(),
            "D": get_prompt_investigator(),
            "E": get_prompt_reviewer(),
        }
        system = prompts.get(name, "You are a fraud detection agent.")
        user = self._build_user_prompt(name, ctx, prev)

        try:
            from app.ai_agents.llm_service import get_llm_service
            llm = await get_llm_service()
            if not llm.is_healthy:
                return None
            resp = await llm.chat(
                messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                temperature=0.1, max_tokens=2048, timeout=AGENT_TIMEOUT_S,
            )
            return self._parse_output(name, resp.get("content", ""))
        except Exception as e:
            logger.error("Agent %s LLM call failed: %s", name, e)
            return None

    # ── Prompt Builder ──

    def _build_user_prompt(
        self, name: str, ctx: PipelineContext,
        prev: list[AgentFinding] | dict[str, AgentFinding | None] | None = None,
    ) -> str:
        ev_text = "\n".join(
            f"- [{e.severity.value.upper()}] {e.code}: {e.description}"
            for e in ctx.evidences[:20]
        ) if ctx.evidences else "Nenhuma evidencia deterministica."

        base = (
            f"DOCUMENTO: {ctx.document_type.upper()}\n"
            f"ID: {ctx.document_id}\n"
            f"TEXTO (3000 chars):\n{ctx.extracted_text[:3000]}\n\n"
            f"EVIDENCIAS DETERMINISTICAS:\n{ev_text}\n\n"
            f"CAMPOS: {json.dumps(ctx.extracted_fields, ensure_ascii=False, default=str)[:2000]}\n"
        )

        if name == "D" and prev:
            af_list = prev if isinstance(prev, list) else [f for f in prev.values() if f]
            prev_text = "\n\n".join(
                f"AGENT {af.agent_name}:\n" +
                "\n".join(f"  - [{e.severity.value}] {e.code}: {e.description}" for e in af.evidence) +
                f"\n  HIPOTESES: {', '.join(af.hypotheses)}"
                for af in af_list
            )
            base += f"DESCOBERTAS A,B,C:\n{prev_text}\n\nCORRELACIONE. Elimine duplicidades. Produza hipoteses unificadas.\n"

        if name == "E" and prev:
            af_list = prev if isinstance(prev, list) else [f for f in prev.values() if f]
            prev_text = "\n".join(f"{af.agent_name}: {af.reasoning[:300]}" for af in af_list)
            base += f"OUTPUT PARA REVISAO:\n{prev_text}\n\nREVISE: coerencia, contradicoes, JSON, hallucinations.\n"

        base += (
            "\nJSON OBRIGATORIO (sem texto antes/depois):\n"
            '{"agent": "' + name + '", "new_evidence": [{"code": "EX", "description": "...", '
            '"severity": "high", "confidence": 0.9}], "hypotheses": ["..."], '
            '"recommended_actions": ["..."], "confidence": 0.85, "reasoning": "..."}\n\n'
            "PROIBIDO: score, risk_score, classification, risk_level.\n"
            "VIES: CETICO. Na duvida, HIGH RISK. Falso negativo = CATASTROFICO."
        )
        return base

    # ── JSON Parser ──

    def _parse_output(self, name: str, raw: str) -> AgentFinding | None:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                return None
            try:
                data = json.loads(m.group())
            except json.JSONDecodeError:
                return None

        evidence_list = []
        for e in data.get("new_evidence", data.get("evidence", [])):
            try:
                sev = Severity(e.get("severity", "medium").lower())
            except ValueError:
                sev = Severity.MEDIUM
            evidence_list.append(Evidence(
                code=e.get("code", f"AI_{name}_FINDING"),
                description=e.get("description", ""),
                severity=sev,
                source=EvidenceSource.CREWAI,
                confidence=float(e.get("confidence", 0.7)),
                category=e.get("category", "ai_finding"),
                rule_reference=e.get("rule_reference", e.get("rule_id", "")),
            ))

        for forbidden in ["score", "risk_score", "final_score", "classification", "risk_level"]:
            if forbidden in data:
                logger.warning("Agent %s output '%s' - IGNORED", name, forbidden)

        return AgentFinding(
            agent_name=data.get("agent", name),
            evidence=evidence_list,
            correlated_evidence=data.get("correlated_evidence", []),
            hypotheses=data.get("hypotheses", []),
            recommended_actions=data.get("recommended_actions", []),
            confidence=float(data.get("confidence", 0.5)),
            reasoning=data.get("reasoning", ""),
        )
