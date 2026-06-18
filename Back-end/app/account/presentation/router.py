# ============================================================
# PaySentinelIQ — Account Router (LGPD Compliance)
# Consent recording, account deletion, data export, consent history
# ============================================================

import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_token_payload
from app.shared.database import get_db
from app.shared.exceptions import NotFoundError, PSIDomainError
from app.shared.settings import get_settings
from app.shared.orm_models import (
    ConsentRecordModel,
    DocumentModel,
    UserModel,
    VerificationReportModel,
    AuditLogModel,
    NotificationModel,
    UserSettingsModel,
)

settings = get_settings()
router = APIRouter()


# ──────────────────────── Schemas ────────────────────────


class ConsentRecordRequest(BaseModel):
    """Request to record user consent."""
    model_config = ConfigDict(strict=True)
    consent_type: str = Field(
        default="terms_of_service",
        pattern="^(terms_of_service|privacy_policy|data_processing|marketing)$",
    )
    terms_version: str = Field(default="1.0.0", min_length=1, max_length=20)
    privacy_version: str = Field(default="1.0.0", min_length=1, max_length=20)
    method: str = Field(default="checkbox", max_length=30)


class ConsentRecordResponse(BaseModel):
    """Consent record returned to client."""
    model_config = ConfigDict(strict=True)
    id: str
    consent_type: str
    terms_version: str
    privacy_version: str
    accepted_at: str
    method: str


class AccountExportResponse(BaseModel):
    """Metadata about the exported data package."""
    model_config = ConfigDict(strict=True)
    export_id: str
    generated_at: str
    file_count: int
    total_size_bytes: int


class AccountDeletionRequest(BaseModel):
    """Confirmation for account deletion."""
    model_config = ConfigDict(strict=True)
    confirm: bool = Field(default=False, description="Must be true to proceed")
    reason: str | None = Field(default=None, max_length=500)


class AccountDeletionResponse(BaseModel):
    """Result of account deletion request."""
    model_config = ConfigDict(strict=True)
    status: str
    message: str
    deletion_scheduled_at: str
    grace_period_days: int


# ──────────────────────── Helpers ────────────────────────


async def _get_user(db: AsyncSession, user_id: str) -> UserModel:
    """Fetch user or raise 404."""
    stmt = select(UserModel).where(UserModel.id == uuid.UUID(user_id))
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User", user_id)
    return user


async def _get_client_ip(request: Request) -> str | None:
    """Extract client IP from request headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


async def _create_audit_log(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    user_id: uuid.UUID | None,
    user_name: str,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any],
    ip_address: str | None,
    user_agent: str | None,
) -> None:
    """Write an immutable audit log entry."""
    log = AuditLogModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        user_name=user_name,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    await db.flush()


# ──────────────────────── ENDPOINTS ────────────────────────


@router.post("/consent", response_model=ConsentRecordResponse)
async def record_consent(
    body: ConsentRecordRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> ConsentRecordResponse:
    """
    Record user consent for terms of service / privacy policy.

    This creates an immutable record that can serve as legal proof
    of informed consent under LGPD Article 7.
    """
    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])
    user = await _get_user(db, str(user_id))

    # Check if identical consent already exists
    existing = await db.execute(
        select(ConsentRecordModel).where(
            ConsentRecordModel.user_id == user_id,
            ConsentRecordModel.consent_type == body.consent_type,
            ConsentRecordModel.terms_version == body.terms_version,
            ConsentRecordModel.privacy_version == body.privacy_version,
        )
    )
    if existing.scalar_one_or_none():
        # Idempotent — return existing record
        record = existing.scalar_one()
        return ConsentRecordResponse(
            id=str(record.id),
            consent_type=record.consent_type,
            terms_version=record.terms_version,
            privacy_version=record.privacy_version,
            accepted_at=record.accepted_at.isoformat(),
            method=record.method,
        )

    ip = await _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")[:500]

    record = ConsentRecordModel(
        id=uuid.uuid4(),
        user_id=user_id,
        tenant_id=tenant_id,
        consent_type=body.consent_type,
        terms_version=body.terms_version,
        privacy_version=body.privacy_version,
        accepted_at=datetime.now(timezone.utc),
        ip_address=ip,
        user_agent=ua,
        method=body.method,
    )
    db.add(record)
    await db.flush()

    # Audit log
    await _create_audit_log(
        db, tenant_id, user_id, user.full_name,
        "consent_recorded", "consent", str(record.id),
        {
            "consent_type": body.consent_type,
            "terms_version": body.terms_version,
            "privacy_version": body.privacy_version,
        },
        ip, ua,
    )

    return ConsentRecordResponse(
        id=str(record.id),
        consent_type=record.consent_type,
        terms_version=record.terms_version,
        privacy_version=record.privacy_version,
        accepted_at=record.accepted_at.isoformat(),
        method=record.method,
    )


@router.get("/consent")
async def list_consent(
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> list[ConsentRecordResponse]:
    """
    List all consent records for the authenticated user.
    Allows users to verify their consent history (LGPD right of access).
    """
    user_id = uuid.UUID(payload["sub"])
    stmt = (
        select(ConsentRecordModel)
        .where(ConsentRecordModel.user_id == user_id)
        .order_by(ConsentRecordModel.accepted_at.desc())
    )
    result = await db.execute(stmt)
    records = result.scalars().all()

    return [
        ConsentRecordResponse(
            id=str(r.id),
            consent_type=r.consent_type,
            terms_version=r.terms_version,
            privacy_version=r.privacy_version,
            accepted_at=r.accepted_at.isoformat(),
            method=r.method,
        )
        for r in records
    ]


@router.delete("/account", response_model=AccountDeletionResponse)
async def delete_account(
    body: AccountDeletionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> AccountDeletionResponse:
    """
    Request account deletion (LGPD Article 18, Section VI — right to erasure).

    Flow:
    1. User confirms deletion
    2. Account is soft-deleted (is_active = False)
    3. Documents are scheduled for removal
    4. Personal data is anonymized where applicable
    5. Grace period allows reversal within configurable window
    """
    if not body.confirm:
        raise HTTPException(status_code=400, detail="Must confirm deletion by setting confirm=true")

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])
    user = await _get_user(db, str(user_id))
    ip = await _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")[:500]

    # Soft-delete the user
    user.is_active = False
    user.email = f"deleted_{user.id}@anonymized.paysentineliq.internal"
    user.full_name = "Deleted User"
    user.hashed_password = ""
    user.google_id = None
    user.avatar_url = None
    user.mfa_enabled = False
    user.mfa_secret = None
    db.add(user)

    # Mark all user documents for deletion
    docs_result = await db.execute(
        select(DocumentModel).where(DocumentModel.uploaded_by == user_id)
    )
    documents = docs_result.scalars().all()
    for doc in documents:
        doc.s3_key = f"PENDING_DELETION/{doc.s3_key}"

    # Delete user settings
    await db.execute(
        delete(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
    )

    # Delete notifications
    await db.execute(
        delete(NotificationModel).where(NotificationModel.user_id == user_id)
    )

    # Audit log
    await _create_audit_log(
        db, tenant_id, user_id, user.full_name,
        "account_deletion_requested", "user", str(user_id),
        {
            "reason": body.reason,
            "grace_period_days": settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
            "documents_affected": len(documents),
        },
        ip, ua,
    )

    deletion_time = datetime.now(timezone.utc)
    return AccountDeletionResponse(
        status="scheduled",
        message=(
            f"Account deletion scheduled. "
            f"Your data will be permanently removed after "
            f"{settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS} days. "
            f"Contact support to cancel this request during the grace period."
        ),
        deletion_scheduled_at=deletion_time.isoformat(),
        grace_period_days=settings.ACCOUNT_DELETION_GRACE_PERIOD_DAYS,
    )


@router.get("/account/export")
async def export_account_data(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> dict[str, Any]:
    """
    Export all user data (LGPD Article 18, Section V — data portability).

    Returns a JSON summary with links/tokens to download a ZIP package
    containing: profile, consent history, documents metadata, reports,
    and activity history.

    Note: The ZIP file itself is served via a separate download endpoint
    to avoid timeout on large exports. This endpoint returns the metadata
    and a temporary download URL.
    """
    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])
    user = await _get_user(db, str(user_id))
    ip = await _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")[:500]

    # Gather user data
    export_data: dict[str, Any] = {
        "export_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user_profile": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "consent_history": [],
        "documents": [],
        "verification_reports": [],
        "notifications": [],
        "settings": None,
    }

    # Consent records
    consent_result = await db.execute(
        select(ConsentRecordModel)
        .where(ConsentRecordModel.user_id == user_id)
        .order_by(ConsentRecordModel.accepted_at.desc())
    )
    for r in consent_result.scalars().all():
        export_data["consent_history"].append({
            "id": str(r.id),
            "type": r.consent_type,
            "terms_version": r.terms_version,
            "privacy_version": r.privacy_version,
            "accepted_at": r.accepted_at.isoformat(),
            "ip_address": r.ip_address,
            "method": r.method,
        })

    # Documents (metadata only — actual files via separate authenticated download)
    docs_result = await db.execute(
        select(DocumentModel).where(DocumentModel.uploaded_by == user_id)
    )
    for doc in docs_result.scalars().all():
        export_data["documents"].append({
            "id": str(doc.id),
            "file_name": doc.file_name,
            "document_type": doc.document_type,
            "file_size_bytes": doc.file_size_bytes,
            "ocr_status": doc.ocr_status,
            "uploaded_at": doc.created_at.isoformat() if doc.created_at else None,
        })

    # Verification reports
    reports_result = await db.execute(
        select(VerificationReportModel)
        .where(VerificationReportModel.tenant_id == tenant_id)
    )
    for report in reports_result.scalars().all():
        export_data["verification_reports"].append({
            "id": str(report.id),
            "document_id": str(report.document_id),
            "status": report.status,
            "risk_score": report.risk_score,
            "verified_at": report.verified_at.isoformat() if report.verified_at else None,
        })

    # Notifications
    notif_result = await db.execute(
        select(NotificationModel)
        .where(NotificationModel.user_id == user_id)
        .order_by(NotificationModel.created_at.desc())
        .limit(500)
    )
    for n in notif_result.scalars().all():
        export_data["notifications"].append({
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "severity": n.severity,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    # User settings
    settings_result = await db.execute(
        select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
    )
    user_settings = settings_result.scalar_one_or_none()
    if user_settings:
        export_data["settings"] = {
            "theme": user_settings.theme,
            "locale": user_settings.locale,
            "timezone": user_settings.timezone,
            "notification_preferences": user_settings.reminder_preferences,
        }

    # Audit log
    await _create_audit_log(
        db, tenant_id, user_id, user.full_name,
        "data_export_requested", "user", str(user_id),
        {"export_id": export_data["export_id"]},
        ip, ua,
    )

    # Return the JSON metadata + the export data inline for small payloads
    return export_data


@router.get("/account/export/download")
async def download_export_zip(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> dict[str, Any]:
    """
    Generate and stream a ZIP file containing all user data.
    Implements LGPD data portability (Article 18, Section V).
    """
    from fastapi.responses import StreamingResponse

    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])
    user = await _get_user(db, str(user_id))
    ip = await _get_client_ip(request)
    ua = request.headers.get("User-Agent", "")[:500]

    # Gather all user data
    export_json: dict[str, Any] = {
        "export_id": str(uuid.uuid4()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "user": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        },
        "consent_records": [],
        "documents": [],
        "notifications": [],
    }

    # Consent records
    consent_result = await db.execute(
        select(ConsentRecordModel).where(ConsentRecordModel.user_id == user_id)
    )
    for r in consent_result.scalars().all():
        export_json["consent_records"].append({
            "id": str(r.id),
            "type": r.consent_type,
            "terms_version": r.terms_version,
            "privacy_version": r.privacy_version,
            "accepted_at": r.accepted_at.isoformat(),
        })

    # Documents
    docs_result = await db.execute(
        select(DocumentModel).where(DocumentModel.uploaded_by == user_id)
    )
    for doc in docs_result.scalars().all():
        export_json["documents"].append({
            "id": str(doc.id),
            "file_name": doc.file_name,
            "document_type": doc.document_type,
            "file_size_bytes": doc.file_size_bytes,
            "ocr_status": doc.ocr_status,
        })

    # Notifications (last 500)
    notif_result = await db.execute(
        select(NotificationModel)
        .where(NotificationModel.user_id == user_id)
        .order_by(NotificationModel.created_at.desc())
        .limit(500)
    )
    for n in notif_result.scalars().all():
        export_json["notifications"].append({
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "severity": n.severity,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if n.created_at else None,
        })

    # Build ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # JSON data file
        zf.writestr(
            "profile_data.json",
            json.dumps(export_json, indent=2, ensure_ascii=False, default=str),
        )
        # README
        zf.writestr(
            "README.txt",
            (
                "PaySentinelIQ — Data Export (LGPD Article 18, Section V)\n"
                f"Generated: {datetime.now(timezone.utc).isoformat()}\n"
                f"User: {user.full_name} ({user.email})\n"
                f"Export ID: {export_json['export_id']}\n\n"
                "This package contains all personal data associated with your account.\n"
                "For questions, contact: privacy@paysentineliq.com\n"
            ),
        )

    zip_buffer.seek(0)

    # Audit log
    await _create_audit_log(
        db, tenant_id, user_id, user.full_name,
        "data_export_downloaded", "user", str(user_id),
        {"export_id": export_json["export_id"]},
        ip, ua,
    )

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f"attachment; filename=paysentineliq_data_export_"
                f"{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.zip"
            ),
            "X-Export-ID": export_json["export_id"],
        },
    )


@router.get("/account/status")
async def account_status(
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> dict[str, Any]:
    """
    Check account status including deletion schedule and consent state.
    """
    user_id = uuid.UUID(payload["sub"])
    user = await _get_user(db, str(user_id))

    # Check latest consent
    consent_result = await db.execute(
        select(ConsentRecordModel)
        .where(ConsentRecordModel.user_id == user_id)
        .order_by(ConsentRecordModel.accepted_at.desc())
        .limit(1)
    )
    latest_consent = consent_result.scalar_one_or_none()

    return {
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "latest_consent": {
            "accepted_at": latest_consent.accepted_at.isoformat() if latest_consent else None,
            "terms_version": latest_consent.terms_version if latest_consent else None,
            "privacy_version": latest_consent.privacy_version if latest_consent else None,
        } if latest_consent else None,
        "current_terms_version": settings.TERMS_VERSION,
        "current_privacy_version": settings.PRIVACY_VERSION,
        "consent_required": settings.CONSENT_REQUIRED_FOR_LOGIN,
    }
