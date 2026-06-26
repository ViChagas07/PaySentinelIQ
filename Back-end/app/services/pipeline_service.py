# ============================================================
# PaySentinelIQ — Document Analysis Pipeline Service
# Orchestrates: S3 → OCR → BrasilAPI → Risk → BoletoPipeline → LLM → Report.
# ============================================================
# CAUSA 2 FIX (2025-06-25): Added 4-stage boleto analysis pipeline
# between risk analysis and copilot for boleto-type documents.
# This replaces the single generic LLM call with a calibrated
# multi-stage pipeline combining deterministic rules + LLM semantic
# analysis + FEBRABAN checksum validation.
# ============================================================

from __future__ import annotations

import uuid
import logging
import tempfile
import os
from datetime import datetime, timezone
from typing import Any, BinaryIO

from app.services.storage import S3StorageProvider, FileValidator
from app.services.storage.exceptions import FileTooLargeError, InvalidFileTypeError
from app.services.ocr import get_ocr_provider, DocumentExtractionService
from app.services.enrichment import EnrichmentService
from app.services.ai import FraudCopilot
from app.services.ai.context_builder import FraudAnalysisContext, ContextBuilder
from app.services.ai.risk_analyzer import RiskAnalyzer
from app.shared.settings import settings

logger = logging.getLogger(__name__)


class DocumentPipelineService:
    """Orchestrates the complete document analysis pipeline.

    Flow:
        1. Validate file (type, size)
        2. Upload to S3
        3. Download from S3 → temp file
        4. OCR extraction (Tesseract with robust text extraction)
        5. Structured field extraction (CNPJ, amounts, dates...)
        6. BrasilAPI enrichment (if CNPJ found)
        7. Deterministic risk analysis
        8. [NEW] 4-Stage Boleto Pipeline (if document is boleto)
        9. LLM copilot enhancement (optional)
        10. Professional report generation
        11. Report saved to S3
        12. Cleanup temp files
    """

    def __init__(
        self,
        storage: S3StorageProvider | None = None,
        copilot: FraudCopilot | None = None,
    ):
        self._storage = storage or S3StorageProvider()
        self._validator = FileValidator(max_size_bytes=settings.MAX_UPLOAD_SIZE_MB * 1_048_576)
        self._ocr = get_ocr_provider()
        self._extractor = DocumentExtractionService()
        self._enrichment = EnrichmentService()
        self._risk_analyzer = RiskAnalyzer()
        self._context_builder = ContextBuilder()
        self._copilot = copilot

    async def process_document(
        self,
        file_data: bytes,
        file_name: str,
        content_type: str,
        tenant_id: str,
        user_id: str | None = None,
        extra_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute the complete document analysis pipeline.

        Args:
            file_data: Raw file bytes.
            file_name: Original file name.
            content_type: MIME type.
            tenant_id: Tenant ID for S3 path organization.
            user_id: User who uploaded (optional).
            extra_context: Additional context fields from the user.

        Returns:
            Complete pipeline result dict with all stages.
        """
        document_id = str(uuid.uuid4())
        start_time = datetime.now(timezone.utc)
        result: dict[str, Any] = {
            "document_id": document_id,
            "file_name": file_name,
            "tenant_id": tenant_id,
            "pipeline_status": "processing",
            "stages": {},
        }

        temp_file_path = None

        try:
            # ── Stage 1: Validate ──
            validation = self._validator.validate(
                file_name, len(file_data), content_type
            )
            if not validation.is_valid:
                raise InvalidFileTypeError(
                    "; ".join(validation.errors),
                    [],
                )
            result["stages"]["validation"] = {"status": "passed", "file_size": len(file_data)}

            # ── Stage 2: Upload to S3 ──
            folder = S3StorageProvider.get_folder_for_type(
                extra_context.get("document_type", "document") if extra_context else "document"
            )
            s3_key = S3StorageProvider.build_key(folder, tenant_id, document_id)
            upload_result = await self._storage.upload_file(
                file_data, s3_key, content_type,
                metadata={"original_name": file_name, "tenant_id": tenant_id},
            )
            result["stages"]["upload"] = {
                "status": "completed",
                "s3_key": s3_key,
                "presigned_url": upload_result.presigned_url,
            }

            # ── Stage 3: Download + OCR ──
            s3_data = await self._storage.download_file(s3_key)
            temp_file_path = self._write_temp_file(s3_data, file_name)
            ocr_result = await self._ocr.extract_text(temp_file_path)
            result["stages"]["ocr"] = {
                "status": "completed",
                "confidence": ocr_result.confidence,
                "pages": ocr_result.page_count,
                "text_length": len(ocr_result.full_text),
            }

            # ── Stage 4: Structured Extraction ──
            extraction = self._extractor.extract(ocr_result.full_text)
            result["stages"]["extraction"] = {
                "status": "completed",
                "cnpj": extraction.cnpj,
                "amounts": extraction.amounts,
                "dates": extraction.dates,
                "confidence": extraction.extraction_confidence,
            }

            # Build context
            context_data = {
                "document_type": extra_context.get("document_type") if extra_context else "unknown",
                "cnpj": extraction.cnpj,
                "amount": extraction.amounts[0] if extraction.amounts else None,
                **extraction.to_dict(),
            }
            if extra_context:
                context_data.update(extra_context)

            # ── Stage 5: BrasilAPI Enrichment ──
            if extraction.cnpj:
                context_data = await self._enrichment.enrich_for_context(
                    extraction.cnpj, context_data
                )
                result["stages"]["brasilapi"] = {
                    "status": "completed",
                    "company": context_data.get("company_enrichment"),
                    "risk_score": context_data.get("company_risk_score"),
                    "risk_flags": context_data.get("risk_flags"),
                }

            # ── Stage 6: Risk Analysis ──
            ctx = self._context_builder.build_from_request(context_data)
            risk_assessment = self._risk_analyzer.analyze(ctx.to_dict())
            result["stages"]["risk_analysis"] = {
                "status": "completed",
                "risk_score": risk_assessment.risk_score,
                "risk_level": risk_assessment.risk_level,
                "flags": [
                    {"code": f.code, "description": f.description}
                    for f in risk_assessment.flags
                ],
            }

            # ── Stage 6B: 4-Stage Boleto Pipeline (if document is boleto) ──
            # CAUSA 2 FIX: Replaces single generic LLM call with calibrated
            # 4-stage pipeline for boleto fraud detection.
            doc_type = extra_context.get("document_type", "").lower() if extra_context else ""
            is_boleto = (
                doc_type == "boleto"
                or context_data.get("linha_digitavel")
                or ocr_result.full_text
                and any(
                    term in ocr_result.full_text.lower()
                    for term in ["boleto", "linha digitável", "código de barras",
                                 "vencimento", "cedente", "sacado"]
                )
            )
            if is_boleto:
                try:
                    from app.services.ai.boleto_analyzer import analyze_boleto_pipeline
                    # Use the raw OCR text for the boleto pipeline
                    boleto_text = ocr_result.full_text
                    # Pass LLM generate function if copilot is available
                    llm_fn = None
                    if self._copilot and self._copilot.llm_available:
                        async def _llm_generate(prompt: str) -> str:
                            return await self._copilot._call_llm([
                                {"role": "user", "content": prompt}
                            ])
                        llm_fn = _llm_generate

                    boleto_analysis = await analyze_boleto_pipeline(boleto_text, llm_fn)
                    result["stages"]["boleto_pipeline"] = {
                        "status": "completed",
                        "risk_score": boleto_analysis["risk_score"],
                        "risk_level": boleto_analysis["risk_level"],
                        "fraud_probability": boleto_analysis["fraud_probability"],
                        "is_fraudulent": boleto_analysis["is_fraudulent"],
                        "total_indicators": boleto_analysis["total_indicators"],
                        "fraud_indicators": boleto_analysis["fraud_indicators"],
                        "recommendation": boleto_analysis["recommendation"],
                        "stage_details": boleto_analysis["stage_details"],
                    }
                    # Override risk score with boleto pipeline result
                    # (more accurate than generic risk analyzer for boletos)
                    risk_assessment.risk_score = boleto_analysis["risk_score"]
                    risk_assessment.risk_level = boleto_analysis["risk_level"]
                    logger.info(
                        "Boleto pipeline: score=%d level=%s indicators=%d",
                        boleto_analysis["risk_score"],
                        boleto_analysis["risk_level"],
                        boleto_analysis["total_indicators"],
                    )
                except Exception as e:
                    logger.warning("Boleto pipeline failed, using generic analysis: %s", e)
                    result["stages"]["boleto_pipeline"] = {
                        "status": "skipped",
                        "reason": str(e),
                    }

            # ── Stage 7: LLM Copilot (if available) ──
            if self._copilot and self._copilot.llm_available:
                try:
                    report = await self._copilot.analyze_document(
                        request_data=context_data,
                        document_id=document_id,
                    )
                    result["stages"]["copilot"] = {
                        "status": "completed",
                        "report": report.to_dict(),
                    }
                except Exception as e:
                    logger.warning("Copilot enhancement failed: %s", e)
                    result["stages"]["copilot"] = {"status": "skipped", "reason": str(e)}

            # ── Final ──
            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
            result["pipeline_status"] = "completed"
            result["processing_time_seconds"] = round(elapsed, 2)
            result["risk_score"] = risk_assessment.risk_score
            result["risk_level"] = risk_assessment.risk_level

            logger.info(
                "Pipeline completed: doc=%s score=%.0f level=%s time=%.1fs",
                document_id, risk_assessment.risk_score, risk_assessment.risk_level, elapsed,
            )

            return result

        except Exception as e:
            logger.error("Pipeline failed for %s: %s", document_id, e)
            result["pipeline_status"] = "failed"
            result["error"] = str(e)
            return result

        finally:
            # Cleanup temp file
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

    def _write_temp_file(self, data: bytes, original_name: str) -> str:
        """Write bytes to a temporary file for OCR processing."""
        import tempfile
        suffix = os.path.splitext(original_name)[1] or ".pdf"
        fd, path = tempfile.mkstemp(suffix=suffix, prefix="psi_pipeline_")
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        return path


# ── Singleton ──
_pipeline_service: DocumentPipelineService | None = None


def get_pipeline_service(
    copilot: FraudCopilot | None = None,
) -> DocumentPipelineService:
    """Get or create the singleton pipeline service."""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = DocumentPipelineService(copilot=copilot)
    return _pipeline_service
