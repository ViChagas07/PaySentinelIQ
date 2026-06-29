"""BGE-M3 embedding service — singleton, batch-aware."""

import logging
from typing import Any

from app.knowledge.settings import get_knowledge_settings
from app.knowledge.exceptions import EmbeddingException

logger = logging.getLogger(__name__)


class BGEEmbeddingService:
    """Singleton embedding service using BAAI/bge-m3.

    Loads the model once. Supports batch embedding for performance.
    """

    _instance: "BGEEmbeddingService | None" = None
    _model: Any = None

    def __new__(cls, settings=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, settings=None):
        if self._initialized:
            return
        self._settings = settings or get_knowledge_settings()
        self._load_model()
        self._initialized = True

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading BGE-M3 model: %s", self._settings.embedding_model)
            self._model = SentenceTransformer(self._settings.embedding_model)
            logger.info("BGE-M3 loaded. Dimension: %d", self.dimension)
        except Exception as e:
            raise EmbeddingException(f"Failed to load BGE-M3: {e}") from e

    @property
    def dimension(self) -> int:
        if self._model is None:
            return self._settings.embedding_dimension
        return self._model.get_sentence_embedding_dimension()

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text."""
        if self._model is None:
            raise EmbeddingException("Model not loaded")
        return self._model.encode(text, normalize_embeddings=True).tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed multiple texts."""
        if self._model is None:
            raise EmbeddingException("Model not loaded")
        if not texts:
            return []
        embeddings = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=self._settings.batch_size,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def health_check(self) -> bool:
        return self._model is not None
