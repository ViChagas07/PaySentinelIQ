# ============================================================
# PaySentinelIQ — Pipeline Exception Hierarchy
# ============================================================

from __future__ import annotations


class PipelineException(Exception):
    """Base exception for all pipeline errors.

    CanonicalPipeline catches these and maps to PipelineStatus:
      - PipelineException → PARTIAL (stage failed, pipeline continues)
      - FatalPipelineException → FAILED (pipeline cannot continue)
    """


class FatalPipelineException(PipelineException):
    """Pipeline cannot continue. Example: no text extracted from PDF."""


class OCRException(PipelineException):
    """OCR stage failed. Text extraction was impossible."""


class ValidationException(PipelineException):
    """Deterministic validation stage failed."""


class CrewException(PipelineException):
    """CrewAI agent stage failed."""


class FusionException(PipelineException):
    """FusionEngine computation failed."""


class EnrichmentException(PipelineException):
    """BrasilAPI or external enrichment failed."""


class ExtractionException(PipelineException):
    """Structured field extraction from text failed."""


class StorageException(PipelineException):
    """File storage (S3/local) operation failed."""


class RoutingException(PipelineException):
    """Invalid document_type or unsupported format."""
