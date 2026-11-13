# ============================================================
# PaySentinelIQ — Extract Stage
# ============================================================
# OCR + structured field extraction + metadata + visual analysis.
# This stage populates extracted_text, extracted_fields, metadata.
# ============================================================

from __future__ import annotations

from app.services.pipeline.stages.base import BaseStage
from app.core.contracts.pipeline_context import PipelineContext
from app.core.contracts.pipeline_status import PipelineStatus

NATIVE_TEXT_METHODS = {"native_text", "pymupdf", "pdfplumber", "pypdf"}
_OCR_FAILURE_STATUSES = {
    "failed",
    "timeout",
    "unavailable",
    "invalid_response",
    "empty",
}


def _useful_chars(text: str) -> int:
    return sum(1 for char in text if char.isalnum())


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
        if not context.metadata.get("ocr_prelude"):
            try:
                from app.services.ocr.pdf_text_extractor import extract_text_robust

                extraction = extract_text_robust(context.file_bytes, document_type=context.document_type)
                context.extracted_text = extraction["text"]
                context.extraction_method = extraction["method"]
                context.page_count = extraction.get("pages", extraction.get("all_attempts", [{}])[0].get("pages", 1))
            except Exception as exc:
                context.add_warning(
                    f"Text extraction failed: {type(exc).__name__}"
                )

        if (
            context.extraction_method in NATIVE_TEXT_METHODS
            and "ocr" not in context.metadata
        ):
            context.metadata["ocr"] = {
                "status": "not_needed",
                "provider": "native_text",
            }

        # ── Structured field extraction ──
        if context.extracted_text:
            try:
                from app.services.ocr.extraction_service import DocumentExtractionService

                extractor = DocumentExtractionService()
                extraction_result = extractor.extract(context.extracted_text)
                context.extracted_fields = extraction_result.to_dict()
            except Exception as exc:
                context.add_warning(
                    f"Structured extraction failed: {type(exc).__name__}"
                )

        # ── PDF Metadata ──
        try:
            import fitz
            doc = fitz.open(stream=context.file_bytes, filetype="pdf")
            meta = doc.metadata
            context.metadata.update({
                "producer": meta.get("producer", ""),
                "creator": meta.get("creator", ""),
                "creation_date": meta.get("creationDate", ""),
                "modification_date": meta.get("modDate", ""),
                "format": meta.get("format", ""),
                "page_count": doc.page_count,
                "pdf_version": doc.metadata.get("format", ""),
            })
            doc.close()
        except Exception:
            pass  # Not a PDF or no metadata available

        # ── Canonical extraction (additive) ──
        self._apply_canonical_extraction(context)

        # ── OCR failure must not silently become a low-risk result ──
        ocr_status = context.metadata.get("ocr", {}).get("status")
        if _useful_chars(context.extracted_text) < 20:
            if ocr_status in _OCR_FAILURE_STATUSES:
                context.add_error(
                    "OCR did not produce usable text for analysis"
                )
                context.pipeline_status = PipelineStatus.FAILED
        elif ocr_status in _OCR_FAILURE_STATUSES - {"empty"}:
            context.add_warning("ocr_fallback_native_text")

    def _apply_canonical_extraction(self, context: PipelineContext) -> None:
        from app.shared.settings import get_settings

        if not getattr(get_settings(), "ENABLE_CANONICAL_EXTRACTION", True):
            return
        if not context.extracted_text:
            return

        try:
            from app.services.extraction.adapter import to_pipeline_fields
            from app.services.extraction.boleto_extractor import extract_boleto_fields
            from app.services.extraction.fields import CanonicalFields
            from app.services.extraction.payslip_extractor import extract_payslip_fields

            doc_type = (context.document_type or "").lower()
            chosen_kind: str | None = None
            chosen_fields: CanonicalFields | None = None
            inferred: str | None = None

            if doc_type == "boleto":
                chosen_kind = "boleto"
                chosen_fields = extract_boleto_fields(context.extracted_text)
            elif doc_type in {"contracheque", "holerite", "payslip", "payroll"}:
                chosen_kind = "contracheque"
                chosen_fields = extract_payslip_fields(context.extracted_text)
            else:
                boleto_fields = extract_boleto_fields(context.extracted_text)
                payslip_fields = extract_payslip_fields(context.extracted_text)
                boleto_count = self._count_filled_fields(boleto_fields)
                payslip_count = self._count_filled_fields(payslip_fields)
                if boleto_count > payslip_count:
                    chosen_kind = "boleto"
                    chosen_fields = boleto_fields
                    inferred = "boleto"
                elif payslip_count > boleto_count:
                    chosen_kind = "contracheque"
                    chosen_fields = payslip_fields
                    inferred = "contracheque"
                else:
                    context.metadata["extraction"] = {
                        "document_type_inferred": None,
                    }

            if chosen_kind is None or chosen_fields is None:
                return

            adapted = to_pipeline_fields(chosen_fields, chosen_kind)
            canonical_block = adapted.pop("canonical", {})
            context.extracted_fields.update(adapted)
            if canonical_block:
                context.extracted_fields["canonical"] = canonical_block

            extraction_metadata: dict[str, object] = {
                "language": canonical_block.get("language"),
                "warnings": canonical_block.get("warnings", []),
                "corrections": canonical_block.get("corrections", []),
                "fields": canonical_block,
            }
            if inferred is not None:
                extraction_metadata["document_type_inferred"] = inferred
            context.metadata["extraction"] = extraction_metadata

            for warning in canonical_block.get("warnings", []):
                context.add_warning(f"extraction: {warning}")
        except Exception as exc:
            context.add_warning(
                f"Canonical extraction failed: {type(exc).__name__}"
            )

    @staticmethod
    def _count_filled_fields(fields: object) -> int:
        from app.services.extraction.fields import CanonicalFields

        count = 0
        for name in CanonicalFields.model_fields:
            if name in {"language", "warnings", "corrections"}:
                continue
            if getattr(fields, name, None) is not None:
                count += 1
        return count
