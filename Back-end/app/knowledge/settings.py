"""Knowledge module settings."""

from dataclasses import dataclass


@dataclass
class KnowledgeSettings:
    chunk_size: int = 900
    chunk_overlap: int = 200
    embedding_model: str = "BAAI/bge-m3"
    embedding_dimension: int = 1024
    batch_size: int = 16
    vector_index_type: str = "hnsw"  # hnsw or ivfflat
    hnsw_m: int = 16
    hnsw_ef_construction: int = 200
    knowledge_base_dir: str = "knowledge"
    similarity_threshold: float = 0.7
    top_k: int = 5
    max_retries: int = 3


def get_knowledge_settings() -> KnowledgeSettings:
    return KnowledgeSettings()
