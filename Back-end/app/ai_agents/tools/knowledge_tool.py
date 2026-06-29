"""Knowledge RAG Tool — LangChain tool for CrewAI agents."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

from app.knowledge.retriever import KnowledgeRetriever
from app.knowledge.embedder import BGEEmbeddingService
from app.knowledge.knowledge_registry import get_weight

logger = logging.getLogger(__name__)


# ── Query Expansion ──

_EXPANSIONS: dict[str, list[str]] = {
    "boleto": ["linha digitavel", "codigo de barras", "FEBRABAN", "DAC", "modulo 10",
               "modulo 11", "banco", "beneficiario", "cedente", "sacado", "vencimento"],
    "pix": ["QR Code", "EMV", "chave PIX", "BACEN", "DICT", "ISPB", "CRC16"],
    "holerite": ["contracheque", "INSS", "IRRF", "FGTS", "salario", "CBO", "CLT"],
    "fraude": ["falso", "adulterado", "golpe", "fraudulento", "crime", "art 171"],
    "cnpj": ["Receita Federal", "pessoa juridica", "empresa", "CNAE"],
    "banco": ["BACEN", "ISPB", "instituicao financeira", "codigo bancario"],
}


def expand_query(query: str) -> str:
    """Expand query with related terms for better recall."""
    terms = [query]
    query_lower = query.lower()
    for keyword, expansions in _EXPANSIONS.items():
        if keyword in query_lower:
            terms.extend(expansions[:5])
    return " | ".join(terms)


# ── LRU Cache ──

class QueryCache:
    """Simple LRU cache keyed by SHA-256 query hash with TTL."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 1800):
        self._max = max_size
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, list[dict]]] = {}

    def _key(self, query: str) -> str:
        return hashlib.sha256(query.encode()).hexdigest()

    def get(self, query: str) -> list[dict] | None:
        import time
        k = self._key(query)
        if k in self._cache:
            ts, result = self._cache[k]
            if time.monotonic() - ts < self._ttl:
                return result
            del self._cache[k]
        return None

    def set(self, query: str, result: list[dict]) -> None:
        import time
        if len(self._cache) >= self._max:
            oldest = min(self._cache, key=lambda x: self._cache[x][0])
            del self._cache[oldest]
        self._cache[self._key(query)] = (time.monotonic(), result)


# ── Knowledge Search Tool ──

class KnowledgeSearchTool:
    """LangChain-compatible tool for RAG-powered knowledge retrieval.

    Agents call this tool to consult the official PaySentinelIQ knowledge base
    (FEBRABAN, BACEN, fraud patterns, layouts, algorithms, etc.) before
    producing conclusions.

    NEVER returns raw text. Always returns structured results with citations.
    """

    name = "knowledge_search"
    description = (
        "Search the official PaySentinelIQ knowledge base for regulations, "
        "fraud patterns, bank layouts, FEBRABAN rules, BACEN norms, and "
        "historical cases. Always use this before concluding about fraud. "
        "Input: a search query about boleto, PIX, payroll, or compliance. "
        "Returns structured results with document citations and authority."
    )

    def __init__(self, retriever: KnowledgeRetriever | None = None,
                 embedder: Any = None):
        self._retriever = retriever
        self._embedder = embedder  # Can be None (tests), or BGEEmbeddingService singleton
        self._cache = QueryCache()

    async def search(
        self, query: str, document_type: str = "",
        category: str | None = None, top_k: int = 10,
    ) -> list[dict]:
        """Search knowledge base with caching and query expansion."""
        if not self._retriever:
            return []

        # Check cache
        cached = self._cache.get(query)
        if cached:
            logger.debug("Cache HIT for: %s", query[:50])
            return cached

        # Expand query
        expanded = expand_query(query)

        # Hybrid search
        results = await self._retriever.semantic_search(expanded, top_k=top_k * 2, category=category)

        # Enrich with authority and weight
        enriched = []
        for r in results:
            cat = r.get("category", "")
            r["authority"] = self._resolve_authority(cat)
            r["rag_weight"] = get_weight(cat)
            r["excerpt"] = r.get("text", "")[:500]
            enriched.append(r)

        # Rank by hybrid score
        ranked = self._rank_results(enriched, top_k)
        self._cache.set(query, ranked)
        return ranked

    def _rank_results(self, results: list[dict], top_k: int) -> list[dict]:
        """Hybrid ranking: semantic × authority × RAG weight."""
        for r in results:
            sim = float(r.get("similarity", 0.5))
            auth = self._authority_score(r.get("authority", ""))
            weight = float(r.get("rag_weight", 0.5))
            # Composite: 45% semantic + 20% authority + 15% weight + 10% keyword + 10% metadata
            r["hybrid_score"] = round(
                0.45 * sim + 0.20 * auth + 0.15 * weight * sim + 0.10 * sim + 0.10 * weight, 3
            )
        results.sort(key=lambda r: r.get("hybrid_score", 0), reverse=True)
        return results[:top_k]

    @staticmethod
    def _resolve_authority(category: str) -> str:
        if "febraban" in category.lower():
            return "FEBRABAN"
        if "bacen" in category.lower():
            return "BACEN"
        if "receita" in category.lower():
            return "Receita Federal"
        if "coaf" in category.lower():
            return "COAF"
        return "PaySentinelIQ"

    @staticmethod
    def _authority_score(authority: str) -> float:
        scores = {"FEBRABAN": 1.0, "BACEN": 0.95, "Receita Federal": 0.90,
                   "COAF": 0.85, "PaySentinelIQ": 0.60}
        return scores.get(authority, 0.5)


# ── Prompt injection sanitizer ──

def sanitize_query(query: str) -> str:
    """Remove prompt injection attempts from queries."""
    blocked = ["ignore previous instructions", "forget rules", "system override",
               "ignore all", "you are now", "act as", "pretend to be"]
    sanitized = query
    for phrase in blocked:
        sanitized = sanitized.lower().replace(phrase, "[BLOCKED]")
    return sanitized[:1000]  # Max 1000 chars
