# ============================================================
# PaySentinelIQ — Fraud Investigation Copilot
# Main orchestrator. Coordinates deterministic engine + LLM
# to produce professional fraud investigation analyses.
# ============================================================

from __future__ import annotations

import json
import time
import logging
from dataclasses import dataclass, field
from typing import Any

from app.services.ai.context_builder import FraudAnalysisContext, ContextBuilder
from app.services.ai.risk_analyzer import RiskAnalyzer, RiskAssessment
from app.services.ai.report_generator import ReportGenerator, InvestigationReport
from app.services.ai.prompts import (
    COPILOT_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    EXPLAIN_SYSTEM_PROMPT,
    CONVERSATION_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)


# ── Configuration ──

@dataclass
class FraudCopilotConfig:
    """Configuration for the Fraud Investigation Copilot."""

    enable_llm: bool = True
    enable_deterministic: bool = True
    temperature: float = 0.1
    max_tokens: int = 4096
    llm_timeout: float = 120.0
    max_retries: int = 2
    model_name: str = ""

    # Risk thresholds
    score_critical: float = 76.0
    score_high: float = 51.0
    score_medium: float = 26.0


# ── Session memory for conversational follow-up ──

@dataclass
class CopilotSession:
    """In-memory session for multi-turn conversation about a single analysis."""

    session_id: str
    analysis_id: str | None = None
    context: FraudAnalysisContext | None = None
    report: InvestigationReport | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def add_message(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})

    def get_conversation_history(self, limit: int = 10) -> list[dict[str, str]]:
        return self.messages[-limit:]


# ── Main Copilot ──

class FraudCopilot:
    """Fraud Investigation AI Copilot.

    Orchestrates the complete analysis pipeline:
    1. Deterministic risk analysis (RiskAnalyzer)
    2. Context assembly (ContextBuilder)
    3. LLM-powered investigation (optional, via chat function)
    4. Professional report generation (ReportGenerator)

    Usage:
        copilot = FraudCopilot(llm_chat_fn=my_llm.chat)
        result = await copilot.analyze(pipeline_report)
        report = copilot.generate_report(result)
    """

    def __init__(
        self,
        llm_chat_fn: Any = None,
        config: FraudCopilotConfig | None = None,
    ):
        self.config = config or FraudCopilotConfig()
        self._llm_chat_fn = llm_chat_fn  # async fn(messages, **kwargs) -> str
        self._risk_analyzer = RiskAnalyzer()
        self._context_builder = ContextBuilder()
        self._report_generator = ReportGenerator()
        self._sessions: dict[str, CopilotSession] = {}

    @property
    def llm_available(self) -> bool:
        return self.config.enable_llm and self._llm_chat_fn is not None

    # ── Public API ──

    async def analyze_document(
        self,
        pipeline_report: dict[str, Any] | None = None,
        request_data: dict[str, Any] | None = None,
        document_id: str | None = None,
    ) -> InvestigationReport:
        """Run full analysis: deterministic engine → optional LLM enhancement → report.

        Args:
            pipeline_report: Output from the 7-stage FraudDetectionPipeline.
            request_data: Raw request payload (fallback if no pipeline report).
            document_id: External document identifier.

        Returns:
            Complete InvestigationReport.
        """
        # Step 1: Build context
        ctx = FraudAnalysisContext()
        if pipeline_report:
            ctx = self._context_builder.build_from_pipeline_result(pipeline_report)
        if request_data:
            req_ctx = self._context_builder.build_from_request(request_data)
            ctx = self._context_builder.merge(ctx, req_ctx)

        # Step 2: Deterministic risk analysis
        risk_assessment = self._risk_analyzer.analyze(ctx.to_dict())

        # Merge risk results into context
        ctx.risk_score = risk_assessment.risk_score
        ctx.risk_level = risk_assessment.risk_level
        ctx.risk_flags = [
            {"code": f.code, "description": f.description, "severity": f.severity}
            for f in risk_assessment.flags
        ]
        ctx.anomaly_count = risk_assessment.flag_count

        # Step 3: Build base report from deterministic results
        report = self._report_generator.build_from_risk_assessment(
            ctx, risk_assessment, document_id, ctx.document_type
        )

        # Step 4: LLM enhancement (if available)
        if self.llm_available and pipeline_report:
            try:
                report = await self._enhance_with_llm(ctx, report, risk_assessment)
            except Exception as e:
                logger.warning(f"LLM enhancement failed, using deterministic results: {e}")

        return report

    async def generate_report(
        self,
        context: FraudAnalysisContext,
        risk_assessment: RiskAssessment | None = None,
    ) -> InvestigationReport:
        """Generate a professional investigation report from context and assessment."""
        if risk_assessment is None:
            risk_assessment = self._risk_analyzer.analyze(context.to_dict())

        report = self._report_generator.build_from_risk_assessment(
            context, risk_assessment, context.document_id, context.document_type
        )

        if self.llm_available:
            try:
                report = await self._enhance_with_llm(context, report, risk_assessment)
            except Exception as e:
                logger.warning(f"LLM report enhancement failed: {e}")

        return report

    async def explain_risk(
        self,
        context: FraudAnalysisContext,
        question: str,
    ) -> str:
        """Answer a specific question about the analysis using LLM.

        Only uses data from the context — never fabricates.
        """
        if not self.llm_available:
            return self._fallback_explanation(context)

        messages = [
            {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
            {"role": "user", "content": f"""## ANALYSIS CONTEXT

{context.to_context_text()}

## USER QUESTION

{question}

Answer the question using ONLY the information provided in the analysis context above. If the answer cannot be determined, say so explicitly."""},
        ]

        try:
            response = await self._call_llm(messages)
            return response
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return self._fallback_explanation(context)

    async def generate_recommendations(
        self,
        context: FraudAnalysisContext,
    ) -> list[str]:
        """Generate prioritized investigation recommendations."""
        if not self.llm_available:
            assessment = self._risk_analyzer.analyze(context.to_dict())
            return self._report_generator._build_recommendations(assessment)

        messages = [
            {"role": "system", "content": COPILOT_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Based on the following analysis context, generate a prioritized list of investigation recommendations. Be specific and actionable.

{context.to_context_text()}

Return ONLY a JSON array of strings: ["recommendation 1", "recommendation 2", ...]"""},
        ]

        try:
            response = await self._call_llm(messages)
            # Try to extract JSON array
            recs = self._parse_json_array(response)
            return recs if recs else self._fallback_recommendations(context)
        except Exception as e:
            logger.error(f"LLM recommendations failed: {e}")
            return self._fallback_recommendations(context)

    async def answer_user_question(
        self,
        session_id: str,
        question: str,
        analysis_context: FraudAnalysisContext | None = None,
    ) -> str:
        """Handle a conversational follow-up question within a session.

        Maintains memory of the conversation for context-aware responses.
        """
        session = self._get_or_create_session(session_id)
        if analysis_context:
            session.context = analysis_context

        if not session.context:
            return "No analysis context available. Please analyze a document first."

        if not self.llm_available:
            return self._fallback_conversation(question, session.context)

        # Build conversation messages
        messages = [{"role": "system", "content": CONVERSATION_SYSTEM_PROMPT}]

        # Add analysis context
        messages.append({
            "role": "system",
            "content": f"Current document analysis:\n\n{session.context.to_context_text()}",
        })

        # Add conversation history
        history = session.get_conversation_history(limit=8)
        messages.extend(history)

        # Add current question
        messages.append({"role": "user", "content": question})

        try:
            response = await self._call_llm(messages)
            session.add_message("user", question)
            session.add_message("assistant", response)
            return response
        except Exception as e:
            logger.error(f"LLM conversation failed: {e}")
            return self._fallback_conversation(question, session.context)

    # ── Session management ──

    def _get_or_create_session(self, session_id: str) -> CopilotSession:
        if session_id not in self._sessions:
            self._sessions[session_id] = CopilotSession(session_id=session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    # ── LLM helpers ──

    async def _enhance_with_llm(
        self,
        ctx: FraudAnalysisContext,
        report: InvestigationReport,
        assessment: RiskAssessment,
    ) -> InvestigationReport:
        """Run LLM enhancement on the deterministic report."""
        messages = [
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Generate a professional fraud investigation report based on this analysis:

{ctx.to_context_text()}

Deterministic Risk Score: {assessment.risk_score:.0f}/100 ({assessment.risk_level})
Anomalies Found: {assessment.flag_count}

Return a valid JSON object following the report structure."""},
        ]

        llm_response = await self._call_llm(messages)
        report = self._report_generator.enhance_with_llm(report, llm_response)
        report.ai_model_used = self.config.model_name or "llm"
        return report

    async def _call_llm(self, messages: list[dict[str, str]]) -> str:
        """Call the LLM with retry and timeout."""
        if not self._llm_chat_fn:
            raise RuntimeError("LLM chat function not configured")

        start = time.monotonic()
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                response = await self._llm_chat_fn(
                    messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    timeout=self.config.llm_timeout,
                )
                elapsed = time.monotonic() - start
                logger.info(f"LLM call completed in {elapsed:.2f}s (attempt {attempt + 1})")
                return response
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries:
                    wait = 2 ** attempt
                    time.sleep(wait)

        raise last_error or RuntimeError("LLM call failed after all retries")

    def _parse_json_array(self, text: str) -> list[str] | None:
        """Try to extract a JSON array from LLM output."""
        try:
            # Try direct parse
            data = json.loads(text)
            if isinstance(data, list):
                return [str(item) for item in data]
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        import re
        match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    return [str(item) for item in data]
            except json.JSONDecodeError:
                pass

        return None

    # ── Fallback methods (when LLM is unavailable) ──

    def _fallback_explanation(self, ctx: FraudAnalysisContext) -> str:
        """Generate a deterministic explanation without LLM."""
        lines = [
            f"Risk Score: {ctx.risk_score:.0f}/100 ({ctx.risk_level})",
            f"Anomalies Detected: {ctx.anomaly_count}",
            "",
        ]
        if ctx.risk_flags:
            lines.append("Detected Risk Flags:")
            for flag in ctx.risk_flags:
                lines.append(f"  - {flag.get('code', 'UNKNOWN')}: {flag.get('description', 'No description')}")
        else:
            lines.append("No risk flags were triggered during analysis.")
        return "\n".join(lines)

    def _fallback_recommendations(self, ctx: FraudAnalysisContext) -> list[str]:
        assessment = self._risk_analyzer.analyze(ctx.to_dict())
        return self._report_generator._build_recommendations(assessment)

    def _fallback_conversation(self, question: str, ctx: FraudAnalysisContext) -> str:
        """Fallback response for conversational questions."""
        question_lower = question.lower()

        if "score" in question_lower or "risco" in question_lower:
            return f"The risk score is {ctx.risk_score:.0f}/100, classified as {ctx.risk_level}. This is based on {ctx.anomaly_count} detected anomalies."
        elif "flag" in question_lower or "sinal" in question_lower:
            if ctx.risk_flags:
                flags_text = "\n".join(f"- {f.get('code', '?')}: {f.get('description', '')}" for f in ctx.risk_flags)
                return f"The following risk flags were raised:\n{flags_text}"
            return "No risk flags were raised for this document."
        elif "evid" in question_lower or "prova" in question_lower:
            if ctx.risk_flags:
                flags_text = "\n".join(f"- {f.get('code', '?')}: {f.get('evidence', 'No evidence recorded')}" for f in ctx.risk_flags if f.get('evidence'))
                return f"Evidence for detected anomalies:\n{flags_text}" if flags_text else "No detailed evidence is available for the detected flags."
            return "No anomalies were detected, so there is no evidence to report."
        else:
            return f"Document analysis summary: {ctx.risk_level} risk (score {ctx.risk_score:.0f}/100). {ctx.anomaly_count} anomalies detected. For more details, ask about specific risk flags or evidence."
