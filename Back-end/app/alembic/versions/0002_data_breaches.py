# ============================================================
# PaySentinelIQ — Data Breach Notification Tables
# LGPD Art. 48: Security incident tracking and ANPD notification
# Revision: b2c3d4e5f6a7
# ============================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "data_breaches",
        # ── Primary key (inherited from Base) ─────────────
        sa.Column(
            "id",
            sa.dialects.postgresql.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        # ── Tenant / Reporter ────────────────────────────
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "reported_by",
            sa.dialects.postgresql.UUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),

        # ── Timeline ─────────────────────────────────────
        sa.Column(
            "discovered_at",
            sa.DateTime(timezone=True),
            nullable=False,
            index=True,
            comment="When the breach was first detected",
        ),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When the breach actually occurred",
        ),
        sa.Column(
            "contained_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # ── Description ──────────────────────────────────
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("root_cause", sa.Text(), nullable=True),
        sa.Column(
            "containment_actions",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
        ),

        # ── Impact ───────────────────────────────────────
        sa.Column(
            "affected_data_categories",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
            comment="e.g. ['name','email','cpf','address','financial']",
        ),
        sa.Column(
            "number_affected_subjects",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "risk_level",
            sa.String(20),
            nullable=False,
            server_default="medium",
        ),

        # ── ANPD Notification ────────────────────────────
        sa.Column(
            "anpd_notification_status",
            sa.String(20),
            nullable=False,
            server_default="not_notified",
        ),
        sa.Column(
            "anpd_notification_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "anpd_protocol_number",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "anpd_justification",
            sa.Text(),
            nullable=True,
            comment="Justification if not reported to ANPD",
        ),

        # ── Communication to data subjects ───────────────
        sa.Column(
            "subjects_communicated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "subject_communication_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # ── Resolution ───────────────────────────────────
        sa.Column(
            "resolution_status",
            sa.String(20),
            nullable=False,
            server_default="open",
        ),
        sa.Column(
            "resolution_date",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("lessons_learned", sa.Text(), nullable=True),

        # ── Constraints ──────────────────────────────────
        sa.CheckConstraint(
            "anpd_notification_status IN ("
            "'not_notified','within_deadline','notified','exempt','missed_deadline')",
            name="chk_breach_anpd_status",
        ),
        sa.CheckConstraint(
            "resolution_status IN ('open','contained','investigating','resolved','closed')",
            name="chk_breach_resolution",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low','medium','high','critical')",
            name="chk_breach_risk_level",
        ),
    )

    op.create_index(
        "ix_data_breaches_tenant_discovered",
        "data_breaches",
        ["tenant_id", "discovered_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_data_breaches_tenant_discovered", table_name="data_breaches")
    op.drop_table("data_breaches")
