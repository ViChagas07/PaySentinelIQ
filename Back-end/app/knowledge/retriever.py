"""Knowledge retriever — semantic + keyword search."""

import logging

from app.knowledge.vector_store import KnowledgeVectorStore
from app.knowledge.embedder import BGEEmbeddingService
from app.knowledge.settings import get_knowledge_settings
from app.knowledge.exceptions import RetrieverException

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    """Retrieves relevant knowledge chunks for a given query."""

    def __init__(self, vector_store: KnowledgeVectorStore, embedder: BGEEmbeddingService):
        self._store = vector_store
        self._embedder = embedder
        self._settings = get_knowledge_settings()

    async def semantic_search(self, query: str, top_k: int = 5,
                              category: str | None = None) -> list[dict]:
        """Semantic similarity search using BGE-M3 embeddings."""
        embedding = self._embedder.embed_text(query)
        return await self._store.similarity_search(embedding, top_k=top_k, category_filter=category)

    async def keyword_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Full-text keyword search."""
        return await self._store.keyword_search(query, top_k=top_k)

    async def hybrid_search(self, query: str, top_k: int = 5) -> list[dict]:
        """Combine semantic + keyword results (prepared for future use)."""
        semantic = await self.semantic_search(query, top_k=top_k)
        keyword = await self.keyword_search(query, top_k=top_k)
        seen = set()
        merged = []
        for r in semantic + keyword:
            if r["id"] not in seen:
                merged.append(r)
                seen.add(r["id"])
        return merged[:top_k]
