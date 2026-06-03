# ============================================================
# PaySentinelIQ — Fraud Detection Domain Models
# Anomaly types, risk scoring models, fraud case entities
# ============================================================

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class FraudType(str, Enum):
    """Known payroll and document fraud types in the Brazilian context."""
    GHOST_EMPLOYEE = "ghost_employee"
    SALARY_PADDING = "salary_padding"
    JOB_TITLE_INFLATION = "job_title_inflation"
    TAX_EVASION = "tax_evasion"
    DOCUMENT_FORGERY = "document_forgery"
    DOCUMENT_TAMPERING = "document_tampering"
    CNPJ_FRAUD = "cnpj_fraud"
    BOLETO_TAMPERING = "boleto_tampering"
    LINHA_DIGITAVEL_TAMPERING = "linha_digitavel_tampering"
    PIX_QR_FRAUD = "pix_qr_fraud"
    TROCA_BOLETO = "troca_boleto"
    BENEFICIARY_BINDING_BROKEN = "beneficiary_binding_broken"
    AI_GENERATED_DOCUMENT = "ai_generated_document"
    FABRICATED_DOCUMENT = "fabricated_document"
    INSS_MANIPULATION = "inss_manipulation"
    IRRF_MANIPULATION = "irrf_manipulation"
    FGTS_MANIPULATION = "fgts_manipulation"
    LIQUIDO_INCONSISTENCY = "liquido_inconsistency"
    IDENTITY_MISMATCH = "identity_mismatch"
    UNKNOWN = "unknown"


@dataclass
class FraudCase:
    """A complete fraud case assembled from pipeline analysis."""
    id: UUID = field(default_factory=uuid4)
    document_id: str = ""
    fraud_types: list[FraudType] = field(default_factory=list)
    risk_score: float = 0.0
    confidence: float = 0.0
    anomaly_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    description: str = ""
    evidence_summary: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_critical(self) -> bool:
        return self.risk_score >= 86

    @property
    def is_high(self) -> bool:
        return 66 <= self.risk_score < 86

    @property
    def requires_escalation(self) -> bool:
        return self.risk_score >= 70

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "document_id": self.document_id,
            "fraud_types": [ft.value for ft in self.fraud_types],
            "risk_score": self.risk_score,
            "confidence": self.confidence,
            "anomaly_count": self.anomaly_count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "description": self.description,
            "evidence_summary": self.evidence_summary,
            "created_at": self.created_at.isoformat(),
        }
