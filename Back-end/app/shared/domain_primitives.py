# ============================================================
# PaySentinelIQ — Shared Domain Primitives
# Value objects and enums used across all modules
# ============================================================

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import NewType


# ── Strongly-typed IDs ──

TenantId = NewType("TenantId", uuid.UUID)
UserId = NewType("UserId", uuid.UUID)
EmployeeId = NewType("EmployeeId", uuid.UUID)
PayrollId = NewType("PayrollId", uuid.UUID)
DocumentId = NewType("DocumentId", uuid.UUID)
FraudAlertId = NewType("FraudAlertId", uuid.UUID)
ComplianceReportId = NewType("ComplianceReportId", uuid.UUID)
AuditLogId = NewType("AuditLogId", uuid.UUID)


# ── Enums ──

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentType(str, Enum):
    PAYROLL_REPORT = "payroll_report"
    TAX_FORM = "tax_form"
    TIMESHEET = "timesheet"
    EMPLOYMENT_CONTRACT = "employment_contract"
    BANK_STATEMENT = "bank_statement"
    IDENTITY_DOCUMENT = "identity_document"
    COMPLIANCE_REPORT = "compliance_report"


class PayrollStatus(str, Enum):
    DRAFT = "draft"
    PENDING_VERIFICATION = "pending_verification"
    VERIFIED = "verified"
    FLAGGED = "flagged"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class FraudAlertStatus(str, Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    CONFIRMED_FRAUD = "confirmed_fraud"
    FALSE_POSITIVE = "false_positive"
    RESOLVED = "resolved"


class AnomalyCategory(str, Enum):
    SALARY_DISCREPANCY = "salary_discrepancy"
    DUPLICATE_PAYMENT = "duplicate_payment"
    GHOST_EMPLOYEE = "ghost_employee"
    TAX_EVASION = "tax_evasion"
    TIMESHEET_FRAUD = "timesheet_fraud"
    UNAUTHORIZED_DEDUCTION = "unauthorized_deduction"
    IDENTITY_MISMATCH = "identity_mismatch"
    DOCUMENT_FORGERY = "document_forgery"
    COMPLIANCE_VIOLATION = "compliance_violation"
    OTHER = "other"


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    COMPLIANCE_ANALYST = "compliance_analyst"
    FRAUD_ANALYST = "fraud_analyst"
    HR_MANAGER = "hr_manager"
    AUDITOR = "auditor"
    PAYROLL_MANAGER = "payroll_manager"
    VIEWER = "viewer"


class EntityType(str, Enum):
    COMPANY = "company"
    EMPLOYEE = "employee"
    VENDOR = "vendor"


# ── Value Objects ──

@dataclass(frozen=True)
class Money:
    """Immutable money value object with currency."""
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Money cannot be negative")
        return Money(result, self.currency)

    def to_dict(self) -> dict:
        return {"amount": self.amount, "currency": self.currency}


@dataclass(frozen=True)
class RiskScore:
    """Immutable risk score value object (0-100)."""
    value: float
    confidence: float  # AI confidence 0-1

    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError("Risk score must be between 0 and 100")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

    @property
    def level(self) -> RiskLevel:
        if self.value >= 85:
            return RiskLevel.CRITICAL
        if self.value >= 70:
            return RiskLevel.HIGH
        if self.value >= 40:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"


@dataclass(frozen=True)
class TaxId:
    """Tax identification number (SSN/EIN) — handles masking."""
    value: str
    id_type: str = "SSN"

    def __post_init__(self):
        if not self.value or len(self.value) < 4:
            raise ValueError("Tax ID must have at least 4 characters")

    @property
    def masked(self) -> str:
        return f"***-**-{self.value[-4:]}"

    def __str__(self) -> str:
        return self.masked
