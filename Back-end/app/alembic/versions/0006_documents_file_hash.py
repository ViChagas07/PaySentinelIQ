# ============================================================
# PaySentinelIQ — Documents original-file hash
# Revision: f6a7b8c9d0e1
#
# Adds the SHA-256 hash of the exact original bytes uploaded to
# object storage. Nullable so existing rows remain valid until
# they are backfilled or re-uploaded.
# ============================================================

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6a7b8c9d0e1"
down_revision: str | None = "e5f6a7b8c9d0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("file_hash", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "file_hash")
