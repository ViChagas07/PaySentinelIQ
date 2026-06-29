"""pgvector vector store for knowledge chunks."""

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge.models import KnowledgeChunk
from app.knowledge.exceptions import VectorStoreException

logger = logging.getLogger(__name__)


class KnowledgeVectorStore:
    """Manages pgvector storage and similarity search for knowledge chunks."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def ensure_extension(self) -> None:
        async with self._session_factory() as session:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await session.commit()

    async def create_index(self, index_type: str = "hnsw") -> None:
        """Create HNSW or IVFFlat vector index."""
        async with self._session_factory() as session:
            if index_type == "hnsw":
                await session.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_hnsw "
                    "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops) "
                    "WITH (m = 16, ef_construction = 200)"
                ))
            else:
                await session.execute(text(
                    "CREATE INDEX IF NOT EXISTS idx_knowledge_embedding_ivfflat "
                    "ON knowledge_chunks USING ivfflat (embedding vector_cosine_ops) "
                    "WITH (lists = 100)"
                ))
            await session.commit()

    async def insert_chunks(self, chunks: list[dict]) -> int:
        """Insert knowledge chunks in bulk."""
        if not chunks:
            return 0
        async with self._session_factory() as session:
            models = [
                KnowledgeChunk(
                    document_name=c["document_name"],
                    category=c.get("category", ""),
                    subcategory=c.get("subcategory", ""),
                    section=c.get("section", ""),
                    page=c.get("page", 1),
                    chunk_index=c.get("chunk_index", 0),
                    text=c["text"],
                    embedding=c.get("embedding"),
                    rag_weight=c.get("rag_weight", 0.5),
                    metadata_json=c.get("metadata", {}),
                    document_hash=c.get("document_hash", ""),
                )
                for c in chunks
            ]
            session.add_all(models)
            await session.commit()
            return len(models)

    async def similarity_search(
        self, query_embedding: list[float], top_k: int = 5,
        category_filter: str | None = None,
    ) -> list[dict]:
        """Semantic similarity search using pgvector."""
        async with self._session_factory() as session:
            q = (
                text(
                    "SELECT id, document_name, category, subcategory, section, "
                    "chunk_index, text, rag_weight, metadata_json, "
                    "1 - (embedding <=> :embedding) AS similarity "
                    "FROM knowledge_chunks "
                    + ("WHERE category = :category " if category_filter else "")
                    + "ORDER BY embedding <=> :embedding LIMIT :top_k"
                )
            )
            params = {"embedding": str(query_embedding), "top_k": top_k}
            if category_filter:
                params["category"] = category_filter
            result = await session.execute(q, params)
            rows = result.fetchall()
            return [dict(r._mapping) for r in rows]

    async def keyword_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Full-text keyword search."""
        async with self._session_factory() as session:
            q = text(
                "SELECT id, document_name, category, chunk_index, text, rag_weight "
                "FROM knowledge_chunks "
                "WHERE to_tsvector('portuguese', text) @@ plainto_tsquery('portuguese', :query) "
                "ORDER BY ts_rank(to_tsvector('portuguese', text), plainto_tsquery('portuguese', :query)) DESC "
                "LIMIT :top_k"
            )
            result = await session.execute(q, {"query": query, "top_k": top_k})
            return [dict(r._mapping) for r in result.fetchall()]

    async def get_document_hashes(self) -> dict[str, str]:
        """Return {document_hash: document_name} for all indexed docs."""
        async with self._session_factory() as session:
            result = await session.execute(
                text("SELECT DISTINCT document_hash, document_name FROM knowledge_chunks WHERE document_hash != ''")
            )
            return {r[0]: r[1] for r in result.fetchall()}
