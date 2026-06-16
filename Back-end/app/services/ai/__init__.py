# ============================================================
# PaySentinelIQ — Fraud Investigation Copilot
# AI Service Layer — Clean Architecture
# ============================================================

from app.services.ai.fraud_copilot import FraudCopilot, FraudCopilotConfig
from app.services.ai.context_builder import ContextBuilder, FraudAnalysisContext
from app.services.ai.risk_analyzer import RiskAnalyzer, RiskFlag, RiskAssessment
from app.services.ai.report_generator import ReportGenerator, InvestigationReport
from app.services.ai.prompts import COPILOT_SYSTEM_PROMPT, REPORT_SYSTEM_PROMPT, EXPLAIN_SYSTEM_PROMPT

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
    "COPILOT_SYSTEM_PROMPT",
    "REPORT_SYSTEM_PROMPT",
    "EXPLAIN_SYSTEM_PROMPT",
]
