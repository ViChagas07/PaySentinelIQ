from collections.abc import Sequence

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id SERIAL NOT NULL,
            document_name VARCHAR(500) NOT NULL,
            category VARCHAR(200) NOT NULL,
            subcategory VARCHAR(200) NOT NULL,
            section VARCHAR(500) NOT NULL,
            page INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text TEXT NOT NULL,
            embedding vector(1024),
            rag_weight FLOAT NOT NULL,
            metadata_json JSON NOT NULL,
            document_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL,
            PRIMARY KEY (id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_category "
        "ON knowledge_chunks (category)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_hnsw "
        "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_text_fts "
        "ON knowledge_chunks USING gin (to_tsvector('portuguese', text))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_knowledge_chunks_text_fts")
    op.execute("DROP INDEX IF EXISTS idx_knowledge_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_category")
    op.execute("DROP TABLE IF EXISTS knowledge_chunks")
