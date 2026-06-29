"""Knowledge Management System tests."""

import pytest
import tempfile
from pathlib import Path

from app.knowledge.chunker import KnowledgeChunker
from app.knowledge.knowledge_registry import REGISTRY, get_weight, get_label
from app.knowledge.metadata import compute_file_hash
from app.knowledge.exceptions import ChunkingException


class TestChunker:
    def test_split_text(self):
        c = KnowledgeChunker()
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = c.split(text)
        assert len(chunks) >= 1
        assert all("text" in ch for ch in chunks)
        assert all("metadata" in ch for ch in chunks)

    def test_split_document(self):
        c = KnowledgeChunker()
        text = "Section 1.\n\nSection 2.\n\nSection 3."
        chunks = c.split_document(text, "test.pdf", "test_category", page=1)
        assert len(chunks) >= 1
        assert chunks[0]["metadata"]["document_name"] == "test.pdf"

    def test_empty_text_raises(self):
        c = KnowledgeChunker()
        with pytest.raises(ChunkingException):
            c.split("")

    def test_chunk_metadata_has_index(self):
        c = KnowledgeChunker()
        text = "A" * 500 + "\n\n" + "B" * 500
        chunks = c.split(text)
        for i, ch in enumerate(chunks):
            assert ch["metadata"]["chunk_index"] == i
            assert "total_chunks" in ch["metadata"]


class TestRegistry:
    def test_febraban_weight(self):
        assert get_weight("regulations/febraban") == 1.0

    def test_bacen_weight(self):
        assert get_weight("regulations/bacen") == 0.98

    def test_faq_weight(self):
        assert get_weight("faq") == 0.5

    def test_unknown_category_default(self):
        assert get_weight("nonexistent/category") == 0.5

    def test_label(self):
        assert get_label("regulations/febraban") == "FEBRABAN Regulations"


class TestMetadata:
    def test_compute_hash(self):
        import os as _os
        tmp_path = Path(tempfile.gettempdir()) / f"psi_test_{_os.getpid()}.txt"
        tmp_path.write_bytes(b"test content")
        try:
            h = compute_file_hash(tmp_path)
            assert len(h) == 64
            assert h == compute_file_hash(tmp_path)  # Deterministic
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_different_content_different_hash(self):
        import os as _os
        p1 = Path(tempfile.gettempdir()) / f"psi_test_a_{_os.getpid()}.txt"
        p2 = Path(tempfile.gettempdir()) / f"psi_test_b_{_os.getpid()}.txt"
        p1.write_bytes(b"AAA")
        p2.write_bytes(b"BBB")
        try:
            assert compute_file_hash(p1) != compute_file_hash(p2)
        finally:
            p1.unlink(missing_ok=True)
            p2.unlink(missing_ok=True)
