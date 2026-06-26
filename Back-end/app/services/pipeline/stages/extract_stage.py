# ============================================================
# PaySentinelIQ — Extract Stage
# ============================================================
# OCR + structured field extraction + metadata + visual analysis.
# This stage populates extracted_text, extracted_fields, metadata.
# ============================================================

from __future__ import annotations

import tempfile
import os

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext


class ExtractStage(BaseStage):
    """Stage 2: Extract text and structured data from the document.

    Uses the centralized extract_text_robust() function for OCR.
    Delegates to DocumentExtractionService for structured fields.
    Extracts PDF metadata when available.

    Future: Add visual analysis (font consistency, layer detection).
    """

    def __init__(self):
        super().__init__(name="ExtractStage")

    def _execute(self, context: PipelineContext) -> None:
        if not context.file_bytes:
            context.add_error("No file bytes to extract from")
            return

        # ── OCR: Multi-method text extraction ──
        try:
            from app.services.ocr.pdf_text_extractor import extract_text_robust

            extraction = extract_text_robust(context.file_bytes, document_type=context.document_type)
            context.extracted_text = extraction["text"]
            context.extraction_method = extraction["method"]
            context.page_count = extraction.get("pages", extraction.get("all_attempts", [{}])[0].get("pages", 1))
        except Exception as e:
            context.add_warning(f"Text extraction failed: {e}")

        # ── Structured field extraction ──
        if context.extracted_text:
            try:
                from app.services.ocr.extraction_service import DocumentExtractionService

                extractor = DocumentExtractionService()
                extraction_result = extractor.extract(context.extracted_text)
                context.extracted_fields = extraction_result.to_dict()
            except Exception as e:
                context.add_warning(f"Structured extraction failed: {e}")

        # ── PDF Metadata ──
        try:
            import fitz
            doc = fitz.open(stream=context.file_bytes, filetype="pdf")
            meta = doc.metadata
            context.metadata = {
                "producer": meta.get("producer", ""),
                "creator": meta.get("creator", ""),
                "creation_date": meta.get("creationDate", ""),
                "modification_date": meta.get("modDate", ""),
                "format": meta.get("format", ""),
                "page_count": doc.page_count,
                "pdf_version": doc.metadata.get("format", ""),
            }
            doc.close()
        except Exception:
            pass  # Not a PDF or no metadata available
