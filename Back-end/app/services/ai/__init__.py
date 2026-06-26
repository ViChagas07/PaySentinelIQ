# ============================================================
# PaySentinelIQ — Fraud Investigation Copilot
# AI Service Layer — Clean Architecture
# ============================================================

from app.services.ai.fraud_copilot import FraudCopilot, FraudCopilotConfig
from app.services.ai.context_builder import ContextBuilder, FraudAnalysisContext
from app.services.ai.risk_analyzer import RiskAnalyzer, RiskFlag, RiskAssessment
from app.services.ai.report_generator import ReportGenerator, InvestigationReport
from app.services.ai.prompts import (
    UNIVERSAL_FRAUD_SYSTEM_PROMPT,
    COPILOT_SYSTEM_PROMPT,
    REPORT_SYSTEM_PROMPT,
    EXPLAIN_SYSTEM_PROMPT,
    BOLETO_FRAUD_SYSTEM_PROMPT,
    BOLETO_EXTENSION,
    CONTRACHEQUE_EXTENSION,
    BATCH_EXTENSION,
    build_agent_prompt,
)
from app.services.ai.boleto_analyzer import analyze_boleto_pipeline

__all__ = [
    "FraudCopilot",
    "FraudCopilotConfig",
    "ContextBuilder",
    "FraudAnalysisContext",
    "RiskAnalyzer",
    "RiskFlag",
    "RiskAssessment",
    "ReportGenerator",
    "InvestigationReport",
    "UNIVERSAL_FRAUD_SYSTEM_PROMPT",
    "COPILOT_SYSTEM_PROMPT",
    "REPORT_SYSTEM_PROMPT",
    "EXPLAIN_SYSTEM_PROMPT",
    "BOLETO_FRAUD_SYSTEM_PROMPT",
    "BOLETO_EXTENSION",
    "CONTRACHEQUE_EXTENSION",
    "BATCH_EXTENSION",
    "build_agent_prompt",
    "analyze_boleto_pipeline",
]
