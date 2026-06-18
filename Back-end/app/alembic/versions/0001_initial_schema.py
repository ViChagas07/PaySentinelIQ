# ============================================================
# PaySentinelIQ — Initial Schema Migration
# Creates all tables from orm_models.py including consent_records
# Revision: a1b2c3d4e5f6
# ============================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── tenants (no foreign keys) ────────────────────────────
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True, index=True),
        sa.Column("plan", sa.String(50), server_default=sa.text("'starter'")),
        sa.Column(
            "features",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
    )

    # ── users ────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "email", sa.String(255), nullable=False, unique=True, index=True
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role", sa.String(50), nullable=False, server_default=sa.text("'viewer'")
        ),
        sa.Column(
            "mfa_enabled", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column("mfa_secret", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("google_id", sa.String(255), nullable=True, unique=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.CheckConstraint(
            "role IN ('super_admin','compliance_analyst','fraud_analyst',"
            "'hr_manager','auditor','payroll_manager','viewer')",
            name="chk_user_role",
        ),
    )

    # ── refresh_tokens ───────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "token_hash", sa.String(255), nullable=False, unique=True
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "is_revoked", sa.Boolean(), server_default=sa.text("false")
        ),
    )

    # ── employees ────────────────────────────────────────────
    op.create_table(
        "employees",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "department", sa.String(100), nullable=False, index=True
        ),
        sa.Column("position", sa.String(100), nullable=False),
        sa.Column("salary", sa.Float(), nullable=False),
        sa.Column("hire_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'active'"),
        ),
        sa.Column(
            "risk_score", sa.Float(), server_default=sa.text("0.0")
        ),
        sa.Column("tax_id_encrypted", sa.Text(), nullable=True),
        sa.CheckConstraint("salary > 0", name="chk_salary_positive"),
        sa.CheckConstraint(
            "status IN ('active','terminated','on_leave')",
            name="chk_employee_status",
        ),
        sa.UniqueConstraint(
            "tenant_id", "email", name="uq_tenant_employee_email"
        ),
    )

    # ── payrolls (SoftDeleteMixin) ───────────────────────────
    op.create_table(
        "payrolls",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "employee_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("employees.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "period_start", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "period_end", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("gross_pay", sa.Float(), nullable=False),
        sa.Column("net_pay", sa.Float(), nullable=False),
        sa.Column(
            "tax_withheld", sa.Float(), server_default=sa.text("0.0")
        ),
        sa.Column(
            "deductions",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(30),
            server_default=sa.text("'draft'"),
            index=True,
        ),
        sa.Column(
            "risk_score", sa.Float(), server_default=sa.text("0.0")
        ),
        sa.Column(
            "verified_by_ai",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.CheckConstraint("gross_pay > 0", name="chk_gross_pay_positive"),
        sa.CheckConstraint(
            "net_pay >= 0", name="chk_net_pay_non_negative"
        ),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="chk_risk_score_range",
        ),
        sa.CheckConstraint(
            "status IN ('draft','pending_verification','verified','flagged','approved','rejected')",
            name="chk_payroll_status",
        ),
    )

    # ── documents (SoftDeleteMixin) ──────────────────────────
    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "uploaded_by",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "document_type",
            sa.String(50),
            nullable=False,
            index=True,
        ),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("s3_bucket", sa.String(200), nullable=False),
        sa.Column(
            "ocr_status",
            sa.String(30),
            server_default=sa.text("'pending'"),
        ),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column(
            "extracted_fields",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
    )

    # ── verification_reports ─────────────────────────────────
    op.create_table(
        "verification_reports",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("documents.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "status",
            sa.String(30),
            server_default=sa.text("'pending'"),
            index=True,
        ),
        sa.Column(
            "risk_score", sa.Float(), server_default=sa.text("0.0")
        ),
        sa.Column(
            "extracted_fields",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "metadata_analysis",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "fraud_indicators",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("ocr_confidence", sa.Float(), nullable=True),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column(
            "verified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.CheckConstraint(
            "status IN ('pending','in_progress','verified','failed','needs_review')",
            name="chk_verification_status",
        ),
    )

    # ── fraud_alerts ─────────────────────────────────────────
    op.create_table(
        "fraud_alerts",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "document_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("documents.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "verification_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("verification_reports.id"),
            nullable=True,
        ),
        sa.Column(
            "risk_level", sa.String(20), nullable=False, index=True
        ),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=False),
        sa.Column(
            "anomaly_category", sa.String(50), nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ai_explanation", sa.Text(), nullable=True),
        sa.Column(
            "flagged_fields",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "status",
            sa.String(30),
            server_default=sa.text("'new'"),
            index=True,
        ),
        sa.Column(
            "assigned_to",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "resolved_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="chk_fraud_risk_score",
        ),
        sa.CheckConstraint(
            "ai_confidence >= 0 AND ai_confidence <= 1",
            name="chk_ai_confidence",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low','medium','high','critical')",
            name="chk_fraud_risk_level",
        ),
        sa.CheckConstraint(
            "status IN ('new','under_review','escalated',"
            "'confirmed_fraud','false_positive','resolved')",
            name="chk_fraud_alert_status",
        ),
    )

    # ── compliance_reports ───────────────────────────────────
    op.create_table(
        "compliance_reports",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("entity_name", sa.String(300), nullable=False),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column(
            "verification_status",
            sa.String(30),
            server_default=sa.text("'unverified'"),
        ),
        sa.Column(
            "risk_level",
            sa.String(20),
            server_default=sa.text("'low'"),
        ),
        sa.Column(
            "public_records_summary", sa.Text(), nullable=True
        ),
        sa.Column("lawsuit_summary", sa.Text(), nullable=True),
        sa.Column(
            "sanctions_check",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "pep_check", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column(
            "adverse_media",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "last_checked", sa.DateTime(timezone=True), nullable=True
        ),
        sa.CheckConstraint(
            "entity_type IN ('company','employee','vendor')",
            name="chk_entity_type",
        ),
    )

    # ── audit_logs ───────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("user_name", sa.String(200), nullable=False),
        sa.Column(
            "action", sa.String(100), nullable=False, index=True
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column(
            "entity_id", sa.String(100), nullable=False, index=True
        ),
        sa.Column(
            "details",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
    )

    # ── notifications ────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "severity",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'normal'"),
        ),
        sa.Column(
            "is_read", sa.Boolean(), server_default=sa.text("false"), index=True
        ),
        sa.Column("action_url", sa.String(500), nullable=True),
        sa.Column(
            "metadata",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),
        sa.CheckConstraint(
            "type IN ('payment','fraud_alert','verification_complete',"
            "'compliance_alert','document_event','system','ai_insight','critical')",
            name="chk_notification_type",
        ),
        sa.CheckConstraint(
            "severity IN ('critical','warning','normal','success','ai')",
            name="chk_notification_severity",
        ),
    )

    # ── risk_scores ──────────────────────────────────────────
    op.create_table(
        "risk_scores",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("entity_type", sa.String(20), nullable=False),
        sa.Column(
            "entity_id",
            sa.dialects.postgresql.UUID(),
            nullable=False,
            index=True,
        ),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("ai_confidence", sa.Float(), nullable=False),
        sa.Column(
            "fraud_weight", sa.Float(), server_default=sa.text("0.0")
        ),
        sa.Column(
            "compliance_weight",
            sa.Float(),
            server_default=sa.text("0.0"),
        ),
        sa.Column(
            "verification_weight",
            sa.Float(),
            server_default=sa.text("0.0"),
        ),
        sa.Column("explanation", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.CheckConstraint(
            "risk_score >= 0 AND risk_score <= 100",
            name="chk_risk_score",
        ),
        sa.CheckConstraint(
            "ai_confidence >= 0 AND ai_confidence <= 1",
            name="chk_rs_confidence",
        ),
    )

    # ── user_settings ────────────────────────────────────────
    op.create_table(
        "user_settings",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("theme", sa.String(20), server_default=sa.text("'dark'")),
        sa.Column(
            "primary_color",
            sa.String(20),
            server_default=sa.text("'blue'"),
        ),
        sa.Column(
            "background_color",
            sa.String(20),
            server_default=sa.text("'navy'"),
        ),
        sa.Column(
            "bold_text", sa.Boolean(), server_default=sa.text("false")
        ),
        sa.Column(
            "font_size",
            sa.String(20),
            server_default=sa.text("'medium'"),
        ),
        sa.Column(
            "element_size",
            sa.String(20),
            server_default=sa.text("'comfortable'"),
        ),
        sa.Column("locale", sa.String(10), server_default=sa.text("'en'")),
        sa.Column(
            "high_contrast",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "screen_reader_optimized",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "keyboard_nav",
            sa.Boolean(),
            server_default=sa.text("true"),
        ),
        sa.Column(
            "focus_indicator",
            sa.Boolean(),
            server_default=sa.text("true"),
        ),
        sa.Column(
            "dyslexia_font",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "reduced_motion",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "email_alerts",
            sa.Boolean(),
            server_default=sa.text("true"),
        ),
        sa.Column(
            "push_notifications",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "desktop_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "sound_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "whatsapp_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "telegram_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "slack_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "in_app_alerts",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.Column(
            "alert_threshold",
            sa.Integer(),
            server_default=sa.text("70"),
        ),
        sa.Column(
            "fraud_alert_email", sa.String(255), nullable=True
        ),
        sa.Column(
            "digest_frequency",
            sa.String(20),
            server_default=sa.text("'daily'"),
        ),
        sa.Column(
            "telegram_username", sa.String(64), nullable=True
        ),
        sa.Column(
            "whatsapp_number", sa.String(32), nullable=True
        ),
        sa.Column(
            "slack_destination", sa.String(128), nullable=True
        ),
        sa.Column(
            "reminder_preferences",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text(
                """'{"every_2_days": false, "weekly": false, "monthly": false, "on_due_date": true}'::jsonb"""
            ),
        ),
        sa.Column(
            "timezone",
            sa.String(50),
            server_default=sa.text("'America/Sao_Paulo'"),
        ),
        sa.Column(
            "developer_mode",
            sa.Boolean(),
            server_default=sa.text("false"),
        ),
        sa.CheckConstraint(
            "alert_threshold >= 0 AND alert_threshold <= 100",
            name="chk_alert_threshold",
        ),
    )

    # ── consent_records (LGPD / GDPR) ───────────────────────
    op.create_table(
        "consent_records",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "consent_type",
            sa.String(50),
            nullable=False,
            index=True,
        ),
        sa.Column("terms_version", sa.String(20), nullable=False),
        sa.Column("privacy_version", sa.String(20), nullable=False),
        sa.Column(
            "accepted_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ip_address", sa.String(50), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column(
            "method",
            sa.String(30),
            nullable=False,
            server_default=sa.text("'checkbox'"),
        ),
        sa.CheckConstraint(
            "consent_type IN ('terms_of_service','privacy_policy','data_processing','marketing')",
            name="chk_consent_type",
        ),
        sa.UniqueConstraint(
            "user_id",
            "consent_type",
            "terms_version",
            "privacy_version",
            name="uq_user_consent_version",
        ),
    )

    # ── payment_schedules ────────────────────────────────────
    op.create_table(
        "payment_schedules",
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "user_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "boleto_data",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "due_date",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
        ),
        sa.Column("amount", sa.Float(), server_default=sa.text("0.0")),
        sa.Column(
            "beneficiary",
            sa.String(300),
            server_default=sa.text("''"),
        ),
        sa.Column(
            "bank_code",
            sa.String(10),
            server_default=sa.text("''"),
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'pending'"),
            index=True,
        ),
        sa.Column(
            "notified_at", sa.DateTime(timezone=True), nullable=True
        ),
        sa.CheckConstraint(
            "status IN ('pending','paid','overdue','cancelled')",
            name="chk_payment_status",
        ),
    )


def downgrade() -> None:
    op.drop_table("payment_schedules")
    op.drop_table("consent_records")
    op.drop_table("user_settings")
    op.drop_table("risk_scores")
    op.drop_table("notifications")
    op.drop_table("audit_logs")
    op.drop_table("compliance_reports")
    op.drop_table("fraud_alerts")
    op.drop_table("verification_reports")
    op.drop_table("documents")
    op.drop_table("payrolls")
    op.drop_table("employees")
    op.drop_table("refresh_tokens")
    op.drop_table("users")
    op.drop_table("tenants")
