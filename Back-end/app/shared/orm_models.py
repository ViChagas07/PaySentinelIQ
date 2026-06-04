# ============================================================
# PaySentinelIQ — ORM Models (All Modules)
# SQLAlchemy 2.0 async mapped classes with PostgreSQL
# ============================================================

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import Base, SoftDeleteMixin

# ============================================================
# Tenant / Company
# ============================================================


class TenantModel(Base):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    plan: Mapped[str] = mapped_column(String(50), default="starter")
    features: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    users: Mapped[list["UserModel"]] = relationship(back_populates="tenant")


# ============================================================
# Users & Roles
# ============================================================


class UserModel(Base):
    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="viewer")
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mfa_secret: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    tenant: Mapped["TenantModel"] = relationship(back_populates="users")

    __table_args__ = (
        CheckConstraint(
            "role IN ('super_admin','compliance_analyst','fraud_analyst',"
            "'hr_manager','auditor','payroll_manager','viewer')",
            name="chk_user_role",
        ),
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)


# ============================================================
# Employees
# ============================================================


class EmployeeModel(Base):
    __tablename__ = "employees"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    hire_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    tax_id_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint("salary > 0", name="chk_salary_positive"),
        CheckConstraint("status IN ('active','terminated','on_leave')", name="chk_employee_status"),
        UniqueConstraint("tenant_id", "email", name="uq_tenant_employee_email"),
    )


# ============================================================
# Payrolls
# ============================================================


class PayrollModel(Base, SoftDeleteMixin):
    __tablename__ = "payrolls"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.id"), nullable=False, index=True
    )
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    gross_pay: Mapped[float] = mapped_column(Float, nullable=False)
    net_pay: Mapped[float] = mapped_column(Float, nullable=False)
    tax_withheld: Mapped[float] = mapped_column(Float, default=0.0)
    deductions: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    verified_by_ai: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint("gross_pay > 0", name="chk_gross_pay_positive"),
        CheckConstraint("net_pay >= 0", name="chk_net_pay_non_negative"),
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_risk_score_range"),
        CheckConstraint(
            "status IN ('draft','pending_verification','verified','flagged','approved','rejected')",
            name="chk_payroll_status",
        ),
    )


# ============================================================
# Documents
# ============================================================


class DocumentModel(Base, SoftDeleteMixin):
    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    document_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    file_name: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(200), nullable=False)
    ocr_status: Mapped[str] = mapped_column(String(30), default="pending")
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_fields: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("file_size_bytes > 0", name="chk_file_size_positive"),
        CheckConstraint(
            "document_type IN ('payroll_report','tax_form','timesheet',"
            "'employment_contract','bank_statement','identity_document','compliance_report')",
            name="chk_document_type",
        ),
    )


# ============================================================
# Verification Reports
# ============================================================


class VerificationReportModel(Base):
    __tablename__ = "verification_reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    extracted_fields: Mapped[dict] = mapped_column(JSONB, default=dict)
    metadata_analysis: Mapped[dict] = mapped_column(JSONB, default=dict)
    fraud_indicators: Mapped[list] = mapped_column(JSONB, default=list)
    ocr_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','in_progress','verified','failed','needs_review')",
            name="chk_verification_status",
        ),
    )


# ============================================================
# Fraud Alerts
# ============================================================


class FraudAlertModel(Base):
    __tablename__ = "fraud_alerts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, index=True
    )
    verification_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("verification_reports.id"), nullable=True
    )
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    anomaly_category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    ai_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    flagged_fields: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(30), default="new", index=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_fraud_risk_score"),
        CheckConstraint("ai_confidence >= 0 AND ai_confidence <= 1", name="chk_ai_confidence"),
        CheckConstraint(
            "risk_level IN ('low','medium','high','critical')",
            name="chk_fraud_risk_level",
        ),
        CheckConstraint(
            "status IN ('new','under_review','escalated',"
            "'confirmed_fraud','false_positive','resolved')",
            name="chk_fraud_alert_status",
        ),
    )


# ============================================================
# Compliance Reports
# ============================================================


class ComplianceReportModel(Base):
    __tablename__ = "compliance_reports"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    entity_name: Mapped[str] = mapped_column(String(300), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    verification_status: Mapped[str] = mapped_column(String(30), default="unverified")
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    public_records_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    lawsuit_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    sanctions_check: Mapped[bool] = mapped_column(Boolean, default=False)
    pep_check: Mapped[bool] = mapped_column(Boolean, default=False)
    adverse_media: Mapped[list] = mapped_column(JSONB, default=list)
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('company','employee','vendor')",
            name="chk_entity_type",
        ),
    )


# ============================================================
# Audit Logs (Immutable — Append Only)
# ============================================================


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    user_name: Mapped[str] = mapped_column(String(200), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    details: Mapped[dict] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        # NO UPDATE/DELETE — immutable by design
    )


# ============================================================
# Notifications
# ============================================================


class NotificationModel(Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    action_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "type IN ('fraud_alert','verification_complete',"
            "'compliance_alert','system','ai_insight')",
            name="chk_notification_type",
        ),
    )


# ============================================================
# Risk Scores (Historical)
# ============================================================


class RiskScoreModel(Base):
    __tablename__ = "risk_scores"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True
    )
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    ai_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    fraud_weight: Mapped[float] = mapped_column(Float, default=0.0)
    compliance_weight: Mapped[float] = mapped_column(Float, default=0.0)
    verification_weight: Mapped[float] = mapped_column(Float, default=0.0)
    explanation: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 100", name="chk_risk_score"),
        CheckConstraint("ai_confidence >= 0 AND ai_confidence <= 1", name="chk_rs_confidence"),
    )


# ============================================================
# User Settings / Preferences
# ============================================================


class UserSettingsModel(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    # Appearance
    theme: Mapped[str] = mapped_column(String(20), default="dark")
    primary_color: Mapped[str] = mapped_column(String(20), default="blue")
    background_color: Mapped[str] = mapped_column(String(20), default="navy")
    bold_text: Mapped[bool] = mapped_column(Boolean, default=False)
    font_size: Mapped[str] = mapped_column(String(20), default="medium")
    element_size: Mapped[str] = mapped_column(String(20), default="comfortable")
    # Language
    locale: Mapped[str] = mapped_column(String(10), default="en")
    # Accessibility
    high_contrast: Mapped[bool] = mapped_column(Boolean, default=False)
    screen_reader_optimized: Mapped[bool] = mapped_column(Boolean, default=False)
    keyboard_nav: Mapped[bool] = mapped_column(Boolean, default=True)
    focus_indicator: Mapped[bool] = mapped_column(Boolean, default=True)
    dyslexia_font: Mapped[bool] = mapped_column(Boolean, default=False)
    reduced_motion: Mapped[bool] = mapped_column(Boolean, default=False)
    # Notifications
    email_alerts: Mapped[bool] = mapped_column(Boolean, default=True)
    push_notifications: Mapped[bool] = mapped_column(Boolean, default=False)
    desktop_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    sound_alerts: Mapped[bool] = mapped_column(Boolean, default=False)
    alert_threshold: Mapped[int] = mapped_column(Integer, default=70)
    fraud_alert_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    digest_frequency: Mapped[str] = mapped_column(String(20), default="daily")
    # Account
    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")
    # Developer
    developer_mode: Mapped[bool] = mapped_column(Boolean, default=False)

    __table_args__ = (
        CheckConstraint(
            "alert_threshold >= 0 AND alert_threshold <= 100", name="chk_alert_threshold"
        ),
    )
