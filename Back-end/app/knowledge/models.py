"""SQLAlchemy + pgvector model for knowledge chunks."""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    subcategory: Mapped[str] = mapped_column(String(200), default="")
    section: Mapped[str] = mapped_column(String(500), default="")
    page: Mapped[int] = mapped_column(Integer, default=1)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(Vector(1024), nullable=True)
    rag_weight: Mapped[float] = mapped_column(Float, default=0.5)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    document_hash: Mapped[str] = mapped_column(String(64), default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
