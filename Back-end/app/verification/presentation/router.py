# ============================================================
# PaySentinelIQ — Verification Router
# ============================================================

from fastapi import APIRouter, Depends, Query, UploadFile, File
from pydantic import BaseModel, ConfigDict
from typing import Optional

from app.auth.dependencies import get_current_tenant_id, require_fraud_analyst

router = APIRouter()


class VerificationResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    document_id: str
    status: str
    risk_score: float
    extracted_fields: dict = {}
    fraud_indicators: list = []
    ocr_confidence: Optional[float] = None
    ai_explanation: Optional[str] = None


class UploadResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    document_id: str
    status: str
    message: str
    presigned_url: Optional[str] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    tenant_id: str = Depends(get_current_tenant_id),
    payload: dict = Depends(require_fraud_analyst),
):
    """
    Upload a document for verification.
    Triggers async OCR + AI analysis pipeline via Celery.
    Emits DocumentUploadedEvent.
    """
    # In production:
    # 1. Validate file type/size
    # 2. Upload to S3 with SSE-KMS encryption
    # 3. Generate presigned URL
    # 4. Create document record in DB
    # 5. Emit DocumentUploadedEvent
    # 6. Trigger analyze_document Celery task

    return UploadResponse(
        document_id="mock-doc-id",
        status="uploaded",
        message="Document uploaded. AI analysis pipeline started.",
    )


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification(
    verification_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get verification status and results."""
    return VerificationResponse(
        id=verification_id,
        document_id="mock-doc-id",
        status="needs_review",
        risk_score=72.0,
        extracted_fields={
            "employee_name": "John D. Smith",
            "gross_salary": "$142,500",
        },
        fraud_indicators=[
            {
                "type": "salary_discrepancy",
                "severity": "high",
                "description": "Salary 32% above department median",
            }
        ],
        ocr_confidence=97.5,
        ai_explanation="Multiple high-confidence anomalies detected.",
    )


@router.post("/trigger")
async def trigger_verification(
    document_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
    payload: dict = Depends(require_fraud_analyst),
):
    """Manually trigger re-verification of a document."""
    # In production: trigger Celery task
    from app.tasks import analyze_document
    task = analyze_document.delay(document_id, tenant_id)
    return {"status": "triggered", "task_id": task.id}
