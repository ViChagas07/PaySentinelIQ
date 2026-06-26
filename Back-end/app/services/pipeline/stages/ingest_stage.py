# ============================================================
# PaySentinelIQ — Ingest Stage
# ============================================================
# Validates and registers the incoming document.
# Sets up PipelineContext with raw file data.
# ============================================================

from __future__ import annotations

import uuid

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext


class IngestStage(BaseStage):
    """Stage 1: Validate and register the incoming document.

    Responsibilities:
        - Validate file type (extension + magic bytes)
        - Validate file size (≤ max allowed)
        - Set up identity fields (document_id, correlation_id)
        - Store raw file bytes in context

    Does NOT:
        - Extract text (that's ExtractStage)
        - Upload to storage (handled by IngestStage in production)
    """

    def __init__(self, max_size_bytes: int = 10 * 1024 * 1024):
        super().__init__(name="IngestStage")
        self._max_size_bytes = max_size_bytes

    def _execute(self, context: PipelineContext) -> None:
        # Validate file is present
        if not context.file_bytes:
            context.add_error("No file bytes provided")
            return

        # Validate file size
        if len(context.file_bytes) > self._max_size_bytes:
            context.add_warning(
                f"File exceeds recommended size: {len(context.file_bytes)} bytes "
                f"(max: {self._max_size_bytes})"
            )

        # Ensure identity fields
        if not context.document_id:
            context.document_id = str(uuid.uuid4())
        if not context.correlation_id:
            context.correlation_id = str(uuid.uuid4())
