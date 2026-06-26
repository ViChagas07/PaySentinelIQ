# ============================================================
# PaySentinelIQ — Analysis Records Table
# Persists AI document analysis results for dashboard, history, KPIs
# Revision: c3d4e5f6a7b8
# ============================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analysis_records",
        # ── Primary key (inherited from Base) ─────────────
        sa.Column(
            "id",
            postgresql.UUID(),
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

        # ── User / Tenant ─────────────────────────────────
        sa.Column(
            "user_id",
            postgresql.UUID(),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(),
            sa.ForeignKey("tenants.id"),
            nullable=False,
            index=True,
        ),

        # ── Document info ─────────────────────────────────
        sa.Column("document_type", sa.String(20), nullable=False, index=True),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),

        # ── Risk / Fraud ──────────────────────────────────
        sa.Column("risk_level", sa.String(10), nullable=False, server_default="LOW", index=True),
        sa.Column("risk_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("fraud_probability", sa.Float(), nullable=True),
        sa.Column("is_fraudulent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("fraud_indicators", postgresql.JSONB(), nullable=True),

        # ── Analysis payload ──────────────────────────────
        sa.Column("analysis_result", postgresql.JSONB(), nullable=True),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("processing_duration", sa.Float(), nullable=True),

        # ── Timestamps ────────────────────────────────────
        sa.Column("analyzed_at", sa.DateTime(timezone=True), index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed", index=True),
    )

    # ── Check constraints ─────────────────────────────────
    op.create_check_constraint(
        "chk_analysis_risk_level",
        "analysis_records",
        "risk_level IN ('LOW','MEDIUM','HIGH','CRITICAL')",
    )
    op.create_check_constraint(
        "chk_analysis_document_type",
        "analysis_records",
        "document_type IN ('BOLETO','CONTRACHEQUE')",
    )
    op.create_check_constraint(
        "chk_analysis_status",
        "analysis_records",
        "status IN ('completed','flagged','failed')",
    )


def downgrade() -> None:
    op.drop_table("analysis_records")
