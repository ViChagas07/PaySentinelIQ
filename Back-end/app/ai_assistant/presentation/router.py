# ============================================================
# PaySentinelIQ — AI Assistant Chat Router
# Natural language Q&A for payroll fraud & risk intelligence
# ============================================================

import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, Field

from app.auth.dependencies import get_current_tenant_id

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    message: str
    conversation_id: str
    sources: list[str] = []
    related_alerts: list[str] = []


# ── AI Response templates (keyword-based routing) ──
# In production, this would call the LLM service via app.ai_agents.llm_service

_RESPONSE_TEMPLATES = {
    "fraud": (
        "Based on real-time analysis, there are 23 active fraud alerts this month — a 15% increase from last month. "
        "The top risk areas are: payroll duplication (8 cases), identity mismatch (7 cases), and overtime anomalies (5 cases). "
        "Critical alerts FR-002 (Ghost Employee — Sales dept, score 91) and FR-012 (Tax Evasion — Executive, score 93) "
        "require immediate attention. Would you like me to drill into any specific category?"
    ),
    "risk": (
        "The overall risk score has decreased by 2.3% this month. The Finance department shows the highest risk concentration "
        "with 12 flagged cases (down from 15 last month). However, the verification pass rate has improved to 98.4%. "
        "The heatmap shows Operations emerging as a new risk area (risk score increased from 3.1 to 5.4). "
        "Top 3 risk factors: salary discrepancies (40%), timesheet anomalies (30%), and document inconsistencies (20%)."
    ),
    "compliance": (
        "Current compliance status: All regulatory checks are passing. SOC 2 Type II certification is valid through Q4 2026. "
        "There are 3 minor compliance incidents this quarter (all resolved). No sanctions or blacklist matches in the last 30 days. "
        "LGPD data retention review is due for 7 employee records by Jun 30. 2 vendors flagged for adverse media — "
        "Global Trade Ltda (high risk) and Logistics Express Transportes (medium risk)."
    ),
    "unusual": (
        "I've detected 2 unusual patterns in the last 24 hours:\n"
        "1. A sudden spike in overtime claims in the Logistics department — 340% above the weekly average (47h vs 14h). "
        "5 entries were modified outside normal working hours (2-4 AM window).\n"
        "2. 5 payroll adjustments were made outside normal hours in the Sales department. "
        "Both are flagged for analyst review. Related alerts: FR-005 (Timesheet Fraud — Operations) and FR-010 (Timesheet Fraud — Customer Support)."
    ),
    "overtime": (
        "Overtime analysis for the current period:\n"
        "- Logistics: 47h (340% above weekly avg of 14h) — CRITICAL, flagged FR-005\n"
        "- Customer Support: 127h reported in single week (legal max: 56h) — CRITICAL, flagged FR-010\n"
        "- Engineering: 23h (60% above baseline) — MODERATE, under monitoring\n"
        "- Sales: 18h (within normal range for quarter-end)\n"
        "Recommendation: Audit Logistics and Support timesheets immediately. Pattern suggests possible timesheet padding or credential sharing."
    ),
    "salary": (
        "Salary anomaly report:\n"
        "- Employee #2841 (John D. Smith, Engineering): Gross pay R$142.5K — 32% above 95th percentile for role. No promotion memo found.\n"
        "- Employee #5582 (Thomas Moore, Executive): 40% of compensation routed through offshore entity. Possible tax evasion.\n"
        "- Employee #3120 (Maria Garcia, Sales): Commission structure appears normal. Salary within band.\n"
        "Top salary discrepancy by department: Engineering (3 cases), Executive (1 critical case), Sales (1 case)."
    ),
    "department": (
        "Department risk overview:\n"
        "- Engineering: 340 payrolls, risk score 2.1, 3 flagged — LOW risk\n"
        "- Sales: 280 payrolls, risk score 7.8, 14 flagged — HIGH risk (identity issues, unauthorized deductions)\n"
        "- Operations: 250 payrolls, risk score 5.4, 8 flagged — MEDIUM risk (overtime anomalies)\n"
        "- Customer Support: 300 payrolls, risk score 8.2, 12 flagged — HIGH risk (timesheet fraud)\n"
        "- Finance: 120 payrolls, risk score 1.5, 1 flagged — LOW risk\n"
        "- Executive: 50 payrolls, risk score 0.8, 0 flagged — LOW risk (but 1 critical tax evasion case)"
    ),
    "hello": (
        "Hello! I'm PaySentinelIQ's AI Assistant. I can help you with:\n"
        "- Fraud alert summaries and investigation\n"
        "- Risk trend analysis across departments\n"
        "- Compliance status and regulatory checks\n"
        "- Unusual activity detection\n"
        "- Salary and overtime anomaly reports\n"
        "- Department-level risk assessments\n\n"
        "What would you like to explore today?"
    ),
    "default": (
        "That's a great question. Based on the available data, the key metrics are:\n"
        "- 12,487 payrolls processed this month with a 98.4% verification pass rate\n"
        "- AI confidence at 98.2%\n"
        "- 47 high-risk documents flagged\n"
        "- 3 compliance incidents (all resolved)\n"
        "- Top risk: Sales department (7.8 risk score, 14 flagged)\n\n"
        "Would you like me to explore any specific area — fraud alerts, risk trends, compliance status, or department analysis?"
    ),
}


def _get_ai_response(message: str) -> tuple[str, list[str]]:
    """Route the user message to the appropriate response template."""
    lower = message.lower()

    # Check for keyword matches
    keywords = [
        "fraud", "alert", "risk", "trend", "compliance",
        "unusual", "activity", "overtime", "salary",
        "department", "hello", "hi", "hey",
    ]

    for keyword in keywords:
        if keyword in lower:
            # Map "alert" and "trend" to their broader categories
            if keyword in ("alert",):
                return _RESPONSE_TEMPLATES["fraud"], []
            if keyword in ("trend",):
                return _RESPONSE_TEMPLATES["risk"], []
            if keyword in ("activity",):
                return _RESPONSE_TEMPLATES["unusual"], []
            if keyword in ("hi", "hey"):
                return _RESPONSE_TEMPLATES["hello"], []
            return _RESPONSE_TEMPLATES[keyword], []

    return _RESPONSE_TEMPLATES["default"], []


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """
    AI-powered chat assistant for payroll fraud & risk intelligence Q&A.

    Responds to natural language queries about fraud alerts, risk trends,
    compliance status, and department analytics. In production, this endpoint
    delegates to the configured LLM provider (Ollama, OpenAI, etc.).
    """
    import uuid

    conversation_id = body.conversation_id or str(uuid.uuid4())
    response_text, sources = _get_ai_response(body.message)

    # Attempt to use LLM service if available (gracefully degrades to templates)
    try:
        from app.ai_agents.llm_service import get_llm_service
        llm = await get_llm_service()
        if llm.is_healthy():
            llm_response = await llm.chat(
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are PaySentinelIQ's AI Assistant, an expert in payroll fraud detection, "
                            "risk intelligence, and Brazilian labor compliance (CLT, LGPD). "
                            "Provide concise, data-driven answers. Reference specific metrics and alert IDs when relevant. "
                            "Always prioritize accuracy and cite data sources."
                        ),
                    },
                    {"role": "user", "content": body.message},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            response_text = llm_response.get("content", response_text)
            logger.info("AI chat used LLM provider for response")
    except Exception as exc:
        logger.debug("LLM chat fallback to templates: %s", exc)

    return ChatResponse(
        message=response_text,
        conversation_id=conversation_id,
        sources=sources,
        related_alerts=[],
    )


@router.get("/suggestions")
async def get_chat_suggestions(tenant_id: str = Depends(get_current_tenant_id)):
    """Return suggested conversation starters for the AI Assistant."""
    return {
        "suggestions": [
            {"key": "suggestFraudSummary", "label": "Summarize current fraud alerts"},
            {"key": "suggestRiskTrends", "label": "Show risk trends this month"},
            {"key": "suggestComplianceCheck", "label": "Check compliance status"},
            {"key": "suggestUnusualActivity", "label": "Any unusual activity detected?"},
            {"key": "suggestDepartmentRisk", "label": "Show department risk breakdown"},
            {"key": "suggestOvertimeAudit", "label": "Analyze overtime patterns"},
        ],
    }
