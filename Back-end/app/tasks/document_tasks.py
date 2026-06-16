# ============================================================
# PaySentinelIQ — Document Analysis Celery Tasks
# Production tasks: real OCR + S3 + pipeline + BrasilAPI.
# ============================================================

from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.tasks import celery_app
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _run_async(coro: Any) -> Any:
    """Helper to run async code inside Celery tasks (sync context)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ═══════════════════════════════════════════════════════════════
# MAIN DOCUMENT ANALYSIS TASK (background)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
    name="analyze_document_async",
)
def analyze_document_async(self: Any, document_id: str, tenant_id: str, s3_key: str) -> dict[str, Any]:
    """Background document analysis: download from S3 → OCR → pipeline → report.

    This runs asynchronously so the upload endpoint returns immediately.
    Results can be polled via GET /verifications/status/{document_id}.
    """
    logger.info("Background analysis starting: %s (s3://%s)", document_id, s3_key)

    try:
        from app.services.pipeline_service import get_pipeline_service
        from app.services.storage import S3StorageProvider

        storage = S3StorageProvider()
        pipeline = get_pipeline_service()

        # Download from S3
        file_data = _run_async(storage.download_file(s3_key))

        # Run full pipeline
        result = _run_async(pipeline.process_document(
            file_data=file_data,
            file_name=s3_key.split("/")[-1],
            content_type="application/pdf",
            tenant_id=tenant_id,
            extra_context={"document_id": document_id},
        ))

        risk_score = result.get("risk_score", 0)
        risk_level = result.get("risk_level", "LOW")

        # Emit alert if HIGH or CRITICAL
        if risk_level in ("HIGH", "CRITICAL"):
            _emit_analyst_alert(document_id, tenant_id, risk_score, risk_level, 0)

        return {
            "status": result.get("pipeline_status", "completed"),
            "document_id": document_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "processing_time": result.get("processing_time_seconds"),
        }

    except Exception as exc:
        logger.error("Background analysis failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# OCR TASK (real Tesseract)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    name="run_ocr",
)
def run_ocr_task(self: Any, s3_key: str) -> dict[str, Any]:
    """Download from S3 and run real Tesseract OCR."""
    logger.info("OCR task: downloading %s", s3_key)

    try:
        from app.services.storage import S3StorageProvider
        from app.services.ocr import get_ocr_provider, DocumentExtractionService

        storage = S3StorageProvider()
        ocr = get_ocr_provider()
        extractor = DocumentExtractionService()

        # Download
        file_data = _run_async(storage.download_file(s3_key))

        # Write temp file
        import tempfile
        import os
        suffix = os.path.splitext(s3_key)[1] or ".pdf"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            # OCR
            ocr_result = _run_async(ocr.extract_text(tmp_path))

            # Extract structured fields
            extraction = extractor.extract(ocr_result.full_text)

            return {
                "status": "completed",
                "s3_key": s3_key,
                "confidence": ocr_result.confidence,
                "pages": ocr_result.page_count,
                "text": ocr_result.full_text[:5000],
                "extracted": extraction.to_dict(),
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as exc:
        logger.error("OCR task failed for %s: %s", s3_key, exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# FRAUD ANALYSIS TASK (real pipeline)
# ═══════════════════════════════════════════════════════════════

@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=120,
    name="run_fraud_analysis",
)
def run_fraud_analysis_task(self: Any, document_id: str, ocr_fields: dict[str, Any]) -> dict[str, Any]:
    """Run the full fraud detection pipeline with real extracted data."""
    logger.info("Fraud analysis: %s", document_id)

    try:
        from app.ai_agents.crew import get_ai_crew

        crew = get_ai_crew()

        # Build document data from OCR extraction
        document_data = {
            "document_id": document_id,
            "document_type": ocr_fields.get("document_type", "contracheque"),
            "salario_bruto": ocr_fields.get("salario_bruto"),
            "inss": ocr_fields.get("inss"),
            "irrf": ocr_fields.get("irrf"),
            "fgts": ocr_fields.get("fgts"),
            "liquido": ocr_fields.get("liquido"),
            "cargo": ocr_fields.get("cargo"),
            "cbo": ocr_fields.get("cbo"),
            "cnpj": ocr_fields.get("cnpj"),
            "razao_social": ocr_fields.get("razao_social"),
            "cnae": ocr_fields.get("cnae"),
            "linha_digitavel": ocr_fields.get("linha_digitavel"),
            "qr_code_payload": ocr_fields.get("qr_code_payload"),
        }
        # Remove None values
        document_data = {k: v for k, v in document_data.items() if v is not None}

        result = crew.run_pipeline(document_data)
        return result

    except Exception as exc:
        logger.error("Fraud analysis failed for %s: %s", document_id, exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════

def _emit_analyst_alert(
    document_id: str,
    tenant_id: str,
    risk_score: float,
    risk_level: str,
    anomaly_count: int,
) -> None:
    """Emit real-time alert to analyst dashboard."""
    try:
        import json
        alert = {
            "document_id": document_id,
            "tenant_id": tenant_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "anomaly_count": anomaly_count,
            "message": (
                f"ALERTA: Documento {document_id} classificado como {risk_level} "
                f"(score: {risk_score:.0f}/100)"
            ),
        }
        logger.info("ANALYST ALERT: %s", json.dumps(alert, indent=2))
    except Exception as e:
        logger.warning("Could not emit alert: %s", e)
