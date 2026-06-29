"""Intelligent text chunking using RecursiveCharacterTextSplitter."""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.knowledge.settings import get_knowledge_settings
from app.knowledge.exceptions import ChunkingException


class KnowledgeChunker:
    """Splits documents into semantic chunks preserving context.

    Uses RecursiveCharacterTextSplitter with separators ordered by priority:
    headers > paragraphs > sentences > words.
    """

    def __init__(self, settings=None):
        s = settings or get_knowledge_settings()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=s.chunk_size,
            chunk_overlap=s.chunk_overlap,
            separators=["# ", "## ", "\n\n", "\n", ". ", " ", ""],
            keep_separator=True,
            length_function=len,
        )

    def split(self, text: str, metadata: dict | None = None) -> list[dict]:
        """Split text into chunks with enriched metadata.

        Args:
            text: Full document text.
            metadata: Document-level metadata (title, category, etc.).

        Returns:
            List of dicts with 'text' and 'metadata' keys.
        """
        if not text or not text.strip():
            raise ChunkingException("Cannot chunk empty text")

        meta = metadata or {}
        chunks = self._splitter.split_text(text)
        result = []
        for i, chunk in enumerate(chunks):
            chunk_meta = {**meta, "chunk_index": i, "total_chunks": len(chunks)}
            result.append({"text": chunk, "metadata": chunk_meta})
        return result

    def split_document(self, text: str, document_name: str,
                       category: str = "", page: int = 1) -> list[dict]:
        """Split a single document page into chunks."""
        return self.split(text, {
            "document_name": document_name,
            "category": category,
            "page": page,
        })
