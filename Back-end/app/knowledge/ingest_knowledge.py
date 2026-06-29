#!/usr/bin/env python3
"""Knowledge ingestion: PDF → text → chunks → embeddings → pgvector."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from pathlib import Path

from app.knowledge.settings import get_knowledge_settings
from app.knowledge.chunker import KnowledgeChunker
from app.knowledge.embedder import BGEEmbeddingService
from app.knowledge.vector_store import KnowledgeVectorStore
from app.knowledge.knowledge_registry import get_weight, get_label
from app.knowledge.metadata import compute_file_hash
from app.knowledge.exceptions import KnowledgeException

logger = logging.getLogger(__name__)


class KnowledgeIngestionService:
    """Finds PDFs, extracts text, chunks, embeds, and persists to pgvector."""

    def __init__(self, base_dir: str = "knowledge",
                 vector_store: KnowledgeVectorStore | None = None):
        self._base = Path(base_dir)
        self._settings = get_knowledge_settings()
        self._chunker = KnowledgeChunker()
        self._embedder = BGEEmbeddingService()
        self._store = vector_store
        self._stats: dict[str, int] = {}

    async def run(self) -> dict:
        """Execute full ingestion pipeline."""
        logger.info("=== Knowledge Ingestion Started ===")
        t0 = time.monotonic()

        # Find PDFs
        pdfs = self._discover_pdfs()
        logger.info("Found %d PDFs to process", len(pdfs))

        total_chunks = 0
        for pdf_path in pdfs:
            try:
                chunks = self._process_pdf(pdf_path)
                total_chunks += len(chunks)
                if self._store:
                    await self._persist_chunks(chunks)
            except Exception as e:
                logger.error("Failed %s: %s", pdf_path.name, e)

        elapsed = time.monotonic() - t0
        logger.info("=== Ingestion Complete: %d chunks in %.1fs ===", total_chunks, elapsed)

        self._stats["total_chunks"] = total_chunks
        self._stats["total_pdfs"] = len(pdfs)
        self._stats["elapsed_seconds"] = round(elapsed, 1)
        return dict(self._stats)

    def _discover_pdfs(self) -> list[Path]:
        return sorted(self._base.rglob("*.pdf"))

    def _process_pdf(self, pdf_path: Path) -> list[dict]:
        """Process one PDF: extract text → chunk → embed."""
        logger.info("Processing: %s", pdf_path)

        # Check if already indexed
        file_hash = compute_file_hash(pdf_path)
        if self._store:
            existing = asyncio.get_event_loop().run_until_complete(
                self._store.get_document_hashes()
            )
            if file_hash in existing:
                logger.info("  Already indexed (hash match) — skipping")
                return []

        # Extract text
        try:
            import fitz
            doc = fitz.open(pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text() + "\n"
            doc.close()
        except Exception as e:
            logger.warning("  PyMuPDF failed for %s: %s", pdf_path.name, e)
            return []

        if not full_text.strip():
            logger.warning("  Empty text — skipping %s", pdf_path.name)
            return []

        # Determine category from path
        rel = pdf_path.relative_to(self._base)
        category = str(rel.parent).replace("\\", "/")
        weight = get_weight(category)
        label = get_label(category)

        # Chunk
        chunker = KnowledgeChunker()
        raw_chunks = chunker.split_document(full_text, pdf_path.name, category)

        # Embed (batch)
        texts = [c["text"] for c in raw_chunks]
        embeddings = self._embedder.embed_documents(texts)

        # Build chunk records
        chunks = []
        for i, (rc, emb) in enumerate(zip(raw_chunks, embeddings)):
            chunks.append({
                "text": rc["text"],
                "embedding": emb,
                "document_name": pdf_path.name,
                "category": category,
                "subcategory": "",
                "section": category,
                "page": rc["metadata"].get("page", 1),
                "chunk_index": rc["metadata"].get("chunk_index", i),
                "rag_weight": weight,
                "document_hash": file_hash,
                "metadata": {
                    "source": str(pdf_path),
                    "category_label": label,
                    "chunk_index": i,
                    "total_chunks": len(raw_chunks),
                },
            })

        self._stats[category] = self._stats.get(category, 0) + len(chunks)
        logger.info("  %s: %d chunks (weight=%.2f)", pdf_path.name, len(chunks), weight)
        return chunks

    async def _persist_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        count = await self._store.insert_chunks(chunks)
        logger.info("  Persisted %d chunks", count)


# ═══════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════

async def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    svc = KnowledgeIngestionService(base_dir="knowledge")
    stats = await svc.run()
    print("\n=== Knowledge Ingestion Report ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
