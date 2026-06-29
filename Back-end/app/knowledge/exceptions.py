"""Knowledge module exception hierarchy."""

class KnowledgeException(Exception): pass
class ChunkingException(KnowledgeException): pass
class EmbeddingException(KnowledgeException): pass
class RetrieverException(KnowledgeException): pass
class VectorStoreException(KnowledgeException): pass
class DocumentParsingException(KnowledgeException): pass
