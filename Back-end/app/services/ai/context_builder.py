# ============================================================
# PaySentinelIQ — Fraud Analysis Context Builder
# Builds structured FraudAnalysisContext from raw inputs
# following Single Responsibility Principle (SOLID)
# ============================================================

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FraudAnalysisContext:
    """Structured context passed to the LLM for fraud investigation.

    All fields are optional — the copilot handles missing data gracefully.
    """

    # ── Document identification ──
    document_id: str | None = None
    document_type: str | None = None  # "contracheque", "boleto", "nota_fiscal", "comprovante", "unknown"

    # ── Entity information ──
    company_name: str | None = None
    company_cnpj: str | None = None
    employee_name: str | None = None
    employee_cpf: str | None = None
    beneficiary_name: str | None = None

    # ── Financial data ──
    amount: float | None = None
    gross_salary: float | None = None
    net_salary: float | None = None
    inss_amount: float | None = None
    irrf_amount: float | None = None
    fgts_amount: float | None = None

    # ── Dates ──
    issue_date: str | None = None
    due_date: str | None = None
    payment_date: str | None = None
    payroll_period: str | None = None

    # ── Document metadata ──
    file_name: str | None = None
    file_type: str | None = None  # "pdf", "png", "jpg"
    pdf_producer: str | None = None
    creation_date: str | None = None
    modification_date: str | None = None
    incremental_saves: int | None = None

    # ── Boleto-specific ──
    barcode: str | None = None
    linha_digitavel: str | None = None
    bank_code: str | None = None
    pix_key: str | None = None
    qr_code_payload: str | None = None

    # ── OCR data ──
    ocr_text: str | None = None
    ocr_confidence: float | None = None
    ocr_fields: dict[str, str] = field(default_factory=dict)

    # ── Risk engine results ──
    risk_score: float = 0.0
    risk_level: str = "LOW"
    risk_flags: list[dict[str, Any]] = field(default_factory=list)
    anomaly_count: int = 0
    ai_confidence: float = 0.0

    # ── Forensic findings ──
    pdf_layers: int | None = None
    font_inconsistency: bool = False
    image_overlays: int | None = None
    ai_generation_suspected: bool = False

    # ── Validation results ──
    cnpj_valid: bool | None = None
    cnpj_active: bool | None = None
    bank_valid: bool | None = None
    checksum_valid: bool | None = None
    beneficiary_match: bool | None = None

    # ── External data ──
    receita_federal_status: str | None = None
    bacen_bank_status: str | None = None
    cnae_description: str | None = None

    def to_context_text(self) -> str:
        """Render context as a human-readable text block for LLM prompts."""
        lines = ["=== FRAUD ANALYSIS CONTEXT ===", ""]

        # Document info
        lines.append(f"Document Type: {self.document_type or 'unknown'}")
        if self.document_id:
            lines.append(f"Document ID: {self.document_id}")
        if self.file_name:
            lines.append(f"File: {self.file_name} ({self.file_type or 'unknown'})")
        lines.append("")

        # Entity
        if self.company_name:
            lines.append(f"Company: {self.company_name}")
        if self.company_cnpj:
            lines.append(f"CNPJ: {self.company_cnpj} (valid: {self.cnpj_valid}, active: {self.cnpj_active})")
        if self.employee_name:
            lines.append(f"Employee: {self.employee_name}")
        if self.beneficiary_name:
            lines.append(f"Beneficiary: {self.beneficiary_name}")
        if any([self.company_name, self.company_cnpj, self.employee_name]):
            lines.append("")

        # Financial
        financial_lines = []
        if self.amount is not None:
            financial_lines.append(f"Amount: R$ {self.amount:,.2f}")
        if self.gross_salary is not None:
            financial_lines.append(f"Gross Salary: R$ {self.gross_salary:,.2f}")
            if self.net_salary is not None:
                financial_lines.append(f"Net Salary: R$ {self.net_salary:,.2f}")
            if self.inss_amount is not None:
                financial_lines.append(f"INSS: R$ {self.inss_amount:,.2f}")
            if self.irrf_amount is not None:
                financial_lines.append(f"IRRF: R$ {self.irrf_amount:,.2f}")
            if self.fgts_amount is not None:
                financial_lines.append(f"FGTS: R$ {self.fgts_amount:,.2f}")
        if financial_lines:
            lines.extend(financial_lines)
            lines.append("")

        # Dates
        date_lines = []
        if self.issue_date:
            date_lines.append(f"Issue Date: {self.issue_date}")
        if self.due_date:
            date_lines.append(f"Due Date: {self.due_date}")
        if self.payroll_period:
            date_lines.append(f"Period: {self.payroll_period}")
        if date_lines:
            lines.extend(date_lines)
            lines.append("")

        # Boleto
        if self.barcode:
            lines.append(f"Barcode: {self.barcode}")
        if self.linha_digitavel:
            lines.append(f"Linha Digitável: {self.linha_digitavel}")
        if self.bank_code:
            lines.append(f"Bank Code: {self.bank_code} (valid: {self.bank_valid})")
        if self.checksum_valid is not None:
            lines.append(f"Checksum Valid: {self.checksum_valid}")
        if any([self.barcode, self.linha_digitavel, self.bank_code]):
            lines.append("")

        # Risk
        lines.append(f"Risk Score: {self.risk_score:.0f}/100 ({self.risk_level})")
        lines.append(f"AI Confidence: {self.ai_confidence:.1%}")
        lines.append(f"Anomalies Detected: {self.anomaly_count}")
        if self.risk_flags:
            lines.append("Risk Flags:")
            for flag in self.risk_flags:
                lines.append(f"  - {flag.get('code', 'UNKNOWN')}: {flag.get('description', '')}")
        lines.append("")

        # Forensic
        if self.pdf_layers is not None:
            lines.append(f"PDF Layers: {self.pdf_layers}")
        if self.font_inconsistency:
            lines.append("Font Inconsistency: YES")
        if self.ai_generation_suspected:
            lines.append("AI Generation Suspected: YES")

        # External
        if self.receita_federal_status:
            lines.append(f"Receita Federal: {self.receita_federal_status}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for JSON serialization."""
        return {
            "document_id": self.document_id,
            "document_type": self.document_type,
            "company_name": self.company_name,
            "company_cnpj": self.company_cnpj,
            "employee_name": self.employee_name,
            "amount": self.amount,
            "gross_salary": self.gross_salary,
            "net_salary": self.net_salary,
            "issue_date": self.issue_date,
            "due_date": self.due_date,
            "file_name": self.file_name,
            "barcode": self.barcode,
            "linha_digitavel": self.linha_digitavel,
            "bank_code": self.bank_code,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "risk_flags": self.risk_flags,
            "anomaly_count": self.anomaly_count,
            "ai_confidence": self.ai_confidence,
            "cnpj_valid": self.cnpj_valid,
            "cnpj_active": self.cnpj_active,
            "checksum_valid": self.checksum_valid,
        }


class ContextBuilder:
    """Builds a FraudAnalysisContext from various input sources.

    Follows Single Responsibility: only responsible for context assembly,
    not for risk analysis or validation.
    """

    def build_from_pipeline_result(self, pipeline_report: dict[str, Any]) -> FraudAnalysisContext:
        """Build context from the 7-stage pipeline PSI report."""
        ctx = FraudAnalysisContext()

        meta = pipeline_report.get("DOCUMENT_METADATA", {})
        ctx.document_id = meta.get("document_id")
        ctx.document_type = meta.get("document_type")
        ctx.pdf_producer = meta.get("pdf_producer")
        ctx.creation_date = meta.get("creation_date")
        ctx.modification_date = meta.get("modification_date")
        ctx.incremental_saves = meta.get("incremental_saves")

        entity = pipeline_report.get("ENTITY_VALIDATION", {})
        ctx.company_cnpj = entity.get("cnpj_extracted")
        ctx.cnpj_valid = entity.get("cnpj_valid")
        ctx.company_name = entity.get("razao_social_match")
        ctx.cnae_description = entity.get("cnae")
        ctx.receita_federal_status = entity.get("receita_status")

        structural = pipeline_report.get("STRUCTURAL_VALIDATION", {})
        ctx.linha_digitavel = structural.get("linha_digitavel")
        ctx.checksum_valid = structural.get("checksum_valid")
        ctx.bank_code = structural.get("bank_code")
        ctx.bank_valid = structural.get("bank_valid")
        ctx.pix_key = structural.get("qr_pix_key")
        ctx.beneficiary_match = structural.get("beneficiary_match") == "MATCH" if structural.get("beneficiary_match") else None

        financial = pipeline_report.get("FINANCIAL_VALIDATION", {})
        ctx.gross_salary = financial.get("salario_bruto")
        ctx.inss_amount = financial.get("inss_printed")
        ctx.irrf_amount = financial.get("irrf_printed")
        ctx.fgts_amount = financial.get("fgts_printed")
        ctx.net_salary = financial.get("liquido_printed")

        forensic = pipeline_report.get("FORENSIC_FINDINGS", {})
        ctx.pdf_layers = forensic.get("pdf_layers")
        ctx.font_inconsistency = forensic.get("font_consistency") == "INCONSISTENT"
        ctx.image_overlays = forensic.get("image_overlays")
        ctx.ocr_confidence = forensic.get("ocr_confidence_min")

        risk = pipeline_report.get("RISK_ASSESSMENT", {})
        ctx.risk_score = risk.get("fraud_risk_score", 0.0)
        ctx.risk_level = risk.get("risk_classification", "LOW")
        ctx.ai_confidence = risk.get("ai_confidence", 0.0)

        anomalies = pipeline_report.get("ANOMALY_LIST", [])
        ctx.anomaly_count = len(anomalies)
        ctx.risk_flags = [
            {
                "code": a.get("category", "UNKNOWN").upper().replace(" ", "_"),
                "description": a.get("description", ""),
                "severity": a.get("severity", "info"),
                "confidence": a.get("confidence", 0.0),
                "evidence": a.get("evidence", ""),
            }
            for a in anomalies
        ]

        return ctx

    def build_from_request(self, request_data: dict[str, Any]) -> FraudAnalysisContext:
        """Build context from the analyze request payload directly."""
        ctx = FraudAnalysisContext()

        ctx.document_type = request_data.get("document_type")
        ctx.document_id = request_data.get("document_id")

        ctx.company_name = request_data.get("razao_social")
        ctx.company_cnpj = request_data.get("cnpj")
        ctx.employee_name = request_data.get("nome_funcionario")
        ctx.beneficiary_name = request_data.get("beneficiario")

        ctx.amount = request_data.get("valor_nominal")
        ctx.gross_salary = request_data.get("salario_bruto")
        ctx.inss_amount = request_data.get("inss")
        ctx.irrf_amount = request_data.get("irrf")
        ctx.fgts_amount = request_data.get("fgts")
        ctx.net_salary = request_data.get("liquido")

        ctx.payroll_period = request_data.get("periodo")
        ctx.linha_digitavel = request_data.get("linha_digitavel")
        ctx.qr_code_payload = request_data.get("qr_code_payload")

        return ctx

    def merge(self, base: FraudAnalysisContext, overlay: FraudAnalysisContext) -> FraudAnalysisContext:
        """Merge two contexts, overlay takes precedence for non-None values."""
        for field_name in base.__dataclass_fields__:
            overlay_val = getattr(overlay, field_name)
            if overlay_val is not None and overlay_val != getattr(FraudAnalysisContext(), field_name):
                setattr(base, field_name, overlay_val)
        return base
