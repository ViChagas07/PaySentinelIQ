# ============================================================
# PaySentinelIQ — Investigation Report Generator
# Produces professional, structured investigation reports
# from AI copilot output + deterministic engine results.
# ============================================================

from dataclasses import dataclass, field
from typing import Any
import json


@dataclass
class InvestigationFinding:
    """A single finding in the investigation report."""

    title: str
    description: str
    evidence: str = ""
    severity: str = "info"  # info, low, medium, high, critical
    impact: str = ""
    recommendation: str = ""


@dataclass
class InvestigationReport:
    """Complete professional investigation report."""

    document_id: str | None = None
    document_type: str | None = None
    risk_level: str = "LOW"
    risk_score: float = 0.0
    summary: str = ""
    findings: list[InvestigationFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    requires_manual_review: bool = False
    additional_verification_steps: list[str] = field(default_factory=list)
    analysis_timestamp: str = ""
    ai_model_used: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "summary": self.summary,
            "findings": [
                {
                    "title": f.title,
                    "description": f.description,
                    "evidence": f.evidence,
                    "severity": f.severity,
                    "impact": f.impact,
                    "recommendation": f.recommendation,
                }
                for f in self.findings
            ],
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "requires_manual_review": self.requires_manual_review,
            "additional_verification_steps": self.additional_verification_steps,
            "analysis_timestamp": self.analysis_timestamp,
            "ai_model_used": self.ai_model_used,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class ReportGenerator:
    """Generates structured investigation reports.

    Combines deterministic engine output with AI copilot analysis
    to produce professional, audit-ready reports.
    """

    def build_from_risk_assessment(
        self,
        context: Any,  # FraudAnalysisContext
        risk_assessment: Any,  # RiskAssessment
        document_id: str | None = None,
        document_type: str | None = None,
    ) -> InvestigationReport:
        """Build a report purely from deterministic risk analysis (no LLM needed)."""

        report = InvestigationReport(
            document_id=document_id or context.document_id,
            document_type=document_type or context.document_type,
            risk_score=risk_assessment.risk_score,
            risk_level=risk_assessment.risk_level,
            confidence=0.85,  # deterministic engine confidence
            requires_manual_review=risk_assessment.risk_level in ("HIGH", "CRITICAL"),
        )

        # Build findings from risk flags
        for flag in risk_assessment.flags:
            report.findings.append(InvestigationFinding(
                title=flag.code.replace("_", " ").title(),
                description=flag.description,
                evidence=flag.evidence,
                severity=flag.severity,
                impact=self._assess_impact(flag.severity),
                recommendation=self._generate_recommendation(flag),
            ))

        # Build summary
        report.summary = self._generate_summary(report, risk_assessment)

        # Build recommendations
        report.recommendations = self._build_recommendations(risk_assessment)

        # Additional verification steps
        report.additional_verification_steps = self._build_verification_steps(risk_assessment)

        return report

    def enhance_with_llm(
        self,
        base_report: InvestigationReport,
        llm_json_response: str,
    ) -> InvestigationReport:
        """Enhance a deterministic report with LLM-generated insights.

        Parses the LLM's structured JSON response and merges it with
        the deterministic findings. LLM findings are ADDITIVE — they
        never replace deterministic flags, only supplement with deeper analysis.
        """
        try:
            llm_data = json.loads(llm_json_response)
        except (json.JSONDecodeError, TypeError):
            return base_report

        # Update risk assessment from LLM (only if it provides higher confidence)
        if llm_data.get("risk_level"):
            base_report.risk_level = llm_data["risk_level"]
        if llm_data.get("risk_score") is not None:
            base_report.risk_score = max(base_report.risk_score, llm_data["risk_score"])
        if llm_data.get("confidence") is not None:
            base_report.confidence = llm_data["confidence"]
        if llm_data.get("summary"):
            base_report.summary = llm_data["summary"]

        # Merge LLM findings (additive)
        for finding_data in llm_data.get("findings", []):
            base_report.findings.append(InvestigationFinding(
                title=finding_data.get("title", "AI Insight"),
                description=finding_data.get("description", ""),
                evidence=finding_data.get("evidence", ""),
                severity=finding_data.get("severity", "info"),
                impact=finding_data.get("impact", ""),
                recommendation=finding_data.get("recommendation", ""),
            ))

        # Merge recommendations
        llm_recs = llm_data.get("recommendations", [])
        for rec in llm_recs:
            if rec not in base_report.recommendations:
                base_report.recommendations.append(rec)

        # Merge verification steps
        llm_steps = llm_data.get("additional_verification_steps", [])
        for step in llm_steps:
            if step not in base_report.additional_verification_steps:
                base_report.additional_verification_steps.append(step)

        base_report.requires_manual_review = llm_data.get(
            "requires_manual_review", base_report.requires_manual_review
        )

        return base_report

    # ── Private helpers ──

    def _assess_impact(self, severity: str) -> str:
        mapping = {
            "critical": "Potential financial loss. Immediate action required to prevent fraud.",
            "high": "Significant compliance or financial risk. Investigation warranted.",
            "medium": "Moderate concern. Should be reviewed before processing.",
            "low": "Minor anomaly. Low risk of fraud or error.",
            "info": "Informational only. No immediate action needed.",
        }
        return mapping.get(severity, "Unknown impact.")

    def _generate_recommendation(self, flag: Any) -> str:
        """Generate a specific, actionable recommendation for each flag type."""
        code = flag.code if hasattr(flag, "code") else flag.get("code", "")

        recommendations = {
            "CNPJ_INVALID": "Verify CNPJ directly on Receita Federal website (www.gov.br/receitafederal). Request updated CNPJ card from the company.",
            "CNPJ_INACTIVE": "Check CNPJ status on Receita Federal. If confirmed inapto, reject document and report to compliance.",
            "CNPJ_NOT_VERIFIED": "Perform manual CNPJ verification via Receita Federal consulta pública.",
            "BENEFICIARY_MISMATCH": "Cross-reference beneficiary name with company registration. Request clarification from document issuer.",
            "AMOUNT_ZERO_OR_NEGATIVE": "Document contains invalid amount. Request corrected version from issuer.",
            "AMOUNT_UNUSUALLY_HIGH": "Verify amount against contract or purchase order. Require additional approval for high-value documents.",
            "NET_EXCEEDS_GROSS": "This is mathematically impossible. Document is likely fabricated. Request original from HR/payroll department.",
            "NET_TOO_LOW": "Verify deduction breakdown. Check for unauthorized or excessive deductions.",
            "PDF_MULTI_LAYER": "PDF shows signs of content overlay. Request original document. Compare with known authentic samples.",
            "FONT_INCONSISTENCY": "Document shows font tampering indicators. Perform manual visual inspection of all numeric fields.",
            "BOLETO_CHECKSUM_FAILED": "Barcode failed FEBRABAN validation. DO NOT process payment. Report to fraud department.",
            "BANK_CODE_INVALID": "Verify bank code against BACEN ISPB registry. If confirmed invalid, treat as fraud attempt.",
            "OCR_VERY_LOW": "OCR quality too low for reliable analysis. Re-scan document at higher resolution (300+ DPI).",
            "OCR_MODERATE": "OCR quality is moderate. Manually verify critical fields (amount, CNPJ, dates).",
            "DOCUMENT_EXPIRED": "Document is past due date. Verify if payment should still be processed per business rules.",
            "ISSUE_AFTER_DUE": "Issue date is after due date — chronological impossibility. Document metadata may be manipulated.",
            "DATE_ANOMALY": "Creation/modification timestamps are inconsistent. Document may have been altered after creation.",
            "DATE_PARSE_ERROR": "Date format is unrecognized. Manually verify all date fields on the document.",
            "INSS_UNUSUALLY_HIGH": "INSS exceeds legal maximum rate. Verify calculation against 2025 INSS progressive table.",
        }

        return recommendations.get(code, "Manual review recommended for this finding.")

    def _generate_summary(self, report: InvestigationReport, assessment: Any) -> str:
        """Generate an executive summary from the assessment results."""
        total = assessment.flag_count
        critical = assessment.critical_count
        high = assessment.high_count

        if total == 0:
            return "No fraud indicators or anomalies were detected in this document. The document appears legitimate based on automated checks."

        parts = [f"Analysis detected {total} anomaly(s)."]

        if critical > 0:
            parts.append(f"{critical} critical finding(s) require immediate attention.")
        if high > 0:
            parts.append(f"{high} high-severity finding(s) warrant further investigation.")

        parts.append(f"Overall risk classification: {report.risk_level} (score: {report.risk_score:.0f}/100).")

        if report.requires_manual_review:
            parts.append("MANUAL REVIEW IS REQUIRED before processing this document.")

        return " ".join(parts)

    def _build_recommendations(self, assessment: Any) -> list[str]:
        """Build a prioritized list of recommendations."""
        recs = []

        for flag in assessment.flags:
            rec = self._generate_recommendation(flag)
            if rec and rec not in recs:
                recs.append(rec)

        if assessment.risk_level in ("CRITICAL", "HIGH"):
            recs.insert(0, "ESCALATE to senior fraud analyst for immediate review.")
            recs.insert(1, "Block any associated payments pending investigation.")

        if not recs:
            recs.append("No specific actions required. Document passed automated checks.")

        return recs[:10]  # Cap at 10 recommendations

    def _build_verification_steps(self, assessment: Any) -> list[str]:
        """Build additional manual verification steps."""
        steps = []

        if assessment.critical_count > 0 or assessment.high_count > 0:
            steps.append("Request original document from issuer for comparison.")
            steps.append("Cross-reference document data with internal HR/finance records.")
            steps.append("Contact document issuer to verify authenticity.")

        has_cnpj = any("CNPJ" in (f.code if hasattr(f, "code") else "") for f in assessment.flags)
        if has_cnpj:
            steps.append("Verify CNPJ on Receita Federal website (https://solucoes.receita.fazenda.gov.br).")

        has_boleto = any("BOLETO" in (f.code if hasattr(f, "code") else "") for f in assessment.flags)
        if has_boleto:
            steps.append("Contact issuing bank to verify barcode and payment destination.")

        has_ocr = any("OCR" in (f.code if hasattr(f, "code") else "") for f in assessment.flags)
        if has_ocr:
            steps.append("Re-scan or re-upload document at higher resolution.")

        return steps
