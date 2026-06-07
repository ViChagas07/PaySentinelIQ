# ============================================================
# PaySentinelIQ — Notifications Router
# Production endpoints backed by NotificationService + DB.
# Falls back to rich mock data when the database is unavailable
# (e.g., during local development without a running DB).
# ============================================================

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_tenant_id, get_current_user_id
from app.shared.database import get_db
from app.notifications.services import NotificationService

router = APIRouter()

# ── Rich mock fallback (used when DB is unavailable) ──

_MOCK_NOTIFICATIONS: list[dict[str, Any]] = [
    {
        "id": "n1",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "fraud_alert",
        "title": "Critical Fraud Alert: Ghost Employee Detected",
        "message": (
            "AI detected duplicate bank account across 3 payroll records "
            "in the Sales department. Risk Score: 91. "
            "Immediate analyst review required."
        ),
        "severity": "critical",
        "is_read": False,
        "action_url": "/fraud-intelligence",
        "metadata": {"department": "Sales", "riskScore": 91, "employeesAffected": 3},
        "created_at": (datetime.now(UTC).isoformat()),
    },
    {
        "id": "n2",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "verification_complete",
        "title": "Document Verification Complete",
        "message": (
            "Q1 Payroll batch #2841 verification finished. 98.4% pass rate. "
            "15 documents flagged for review. Full report available."
        ),
        "severity": "success",
        "is_read": False,
        "action_url": "/verification-center",
        "metadata": {"batchId": "#2841", "passRate": "98.4%", "flagged": 15},
        "created_at": (datetime.now(UTC).isoformat()),
    },
    {
        "id": "n3",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "ai_insight",
        "title": "AI Insight: Salary Anomaly Pattern Detected",
        "message": (
            "10 employees in Engineering department show unusual "
            "overtime patterns. Average overtime 340% above company baseline. "
            "Recommend department-wide audit."
        ),
        "severity": "ai",
        "is_read": False,
        "action_url": "/fraud-intelligence",
        "metadata": {"department": "Engineering", "overtimeIncrease": "340%", "employeesAffected": 10},
        "created_at": (datetime.now(UTC).isoformat()),
    },
    {
        "id": "n4",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "compliance_alert",
        "title": "Compliance Alert: LGPD Data Retention Review",
        "message": (
            "7 employee records approaching 5-year retention limit "
            "per LGPD Article 16. Review and anonymize or document "
            "continued necessity by Jun 30."
        ),
        "severity": "warning",
        "is_read": True,
        "action_url": "/compliance",
        "metadata": {"regulation": "LGPD", "dueDate": "Jun 30", "recordsAffected": 7},
        "created_at": "2025-05-16T10:00:00Z",
    },
    {
        "id": "n5",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "system",
        "title": "System Update: AI Pipeline v2.4 Deployed",
        "message": (
            "Fraud detection pipeline upgraded to v2.4 with improved "
            "Brazilian document forgery detection. 7-stage analysis "
            "now includes CNAE cross-referencing."
        ),
        "severity": "normal",
        "is_read": True,
        "action_url": None,
        "metadata": {"version": "v2.4", "feature": "CNAE cross-referencing"},
        "created_at": "2025-05-15T08:00:00Z",
    },
    {
        "id": "n6",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "payment",
        "title": "Invoice #482 Approved",
        "message": "Payment for invoice #482 (Acme Corp) has been successfully approved and scheduled for tomorrow.",
        "severity": "normal",
        "is_read": False,
        "action_url": "/payroll",
        "metadata": {"invoiceId": "#482", "company": "Acme Corp", "amount": "$5,000"},
        "created_at": (datetime.now(UTC).isoformat()),
    },
    {
        "id": "n7",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "document_event",
        "title": "New Payslip Uploaded",
        "message": "A new payslip for John Doe has been uploaded and is awaiting verification.",
        "severity": "normal",
        "is_read": False,
        "action_url": "/verification-center",
        "metadata": {"employee": "John Doe", "documentType": "Payslip"},
        "created_at": (datetime.now(UTC).isoformat()),
    },
    {
        "id": "n8",
        "user_id": "u1",
        "tenant_id": "t1",
        "type": "fraud_alert",
        "title": "Risk Score Exceeded Safe Limit",
        "message": "Employee #EMP-5678 risk score increased to 85/100 due to multiple timesheet discrepancies.",
        "severity": "critical",
        "is_read": False,
        "action_url": "/fraud-intelligence",
        "metadata": {"employeeId": "EMP-5678", "riskScore": 85},
        "created_at": (datetime.now(UTC).isoformat()),
    },
]


# ── Response Models ──


class NotificationResponse(BaseModel):
    model_config = ConfigDict(strict=False)
    id: str
    user_id: str | None = None
    tenant_id: str | None = None
    type: str
    title: str
    message: str
    severity: str = "normal"
    is_read: bool = False
    action_url: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: str


class NotificationSettingsRequest(BaseModel):
    model_config = ConfigDict(strict=False)
    email: bool | None = None
    whatsapp: bool | None = None
    telegram: bool | None = None
    slack: bool | None = None
    inApp: bool | None = None


# ── Helper: convert ORM model to response dict ──


def _notification_to_response(notification: Any) -> dict[str, Any]:
    """Convert NotificationModel or mock dict to API response format."""
    if isinstance(notification, dict):
        return notification
    return {
        "id": str(notification.id),
        "user_id": str(notification.user_id),
        "tenant_id": str(notification.tenant_id),
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,
        "severity": getattr(notification, "severity", "normal"),
        "is_read": notification.is_read,
        "action_url": notification.action_url,
        "metadata": getattr(notification, "metadata_", None),
        "created_at": notification.created_at.isoformat() if hasattr(notification.created_at, "isoformat") else notification.created_at,
    }


# ══════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════


@router.get("")
async def list_notifications(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
    severity: str | None = None,
    type: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    List notifications for the current user with optional filtering and pagination.
    Falls back to mock data if the database query fails.
    """
    try:
        service = NotificationService(db)
        notifications = await service.get_notifications_for_user(
            user_id=uuid.UUID(user_id),
            skip=(page - 1) * page_size,
            limit=page_size,
            is_read=False if unread_only else None,
            severity=severity,
            type=type,
        )

        if notifications:
            total = len(notifications)
            return {
                "data": [_notification_to_response(n) for n in notifications],
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": max(1, (total + page_size - 1) // page_size),
            }

        # If DB returned empty, fall back to mock for a richer dev experience
        raise Exception("Empty result — using mock fallback")

    except Exception:
        # Fall back to mock data
        notifications = _MOCK_NOTIFICATIONS
        if unread_only:
            notifications = [n for n in notifications if not n["is_read"]]
        if severity:
            notifications = [n for n in notifications if n.get("severity") == severity]
        if type:
            notifications = [n for n in notifications if n.get("type") == type]
        total = len(notifications)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start = (page - 1) * page_size
        end = start + page_size
        return {
            "data": notifications[start:end],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }


@router.get("/unread-count")
async def get_unread_count(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get count of unread notifications for the current user."""
    try:
        service = NotificationService(db)
        count = await service.get_unread_notification_count(user_id=uuid.UUID(user_id))
        return {"count": count}
    except Exception:
        unread = sum(1 for n in _MOCK_NOTIFICATIONS if not n["is_read"])
        return {"count": unread}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Mark a single notification as read."""
    try:
        service = NotificationService(db)
        notification = await service.mark_notification_as_read(
            notification_id=uuid.UUID(notification_id),
            user_id=uuid.UUID(user_id),
        )
        await db.commit()
        return {
            "status": "read",
            "notification_id": str(notification.id),
            "notification": _notification_to_response(notification),
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/read-all")
async def mark_all_read(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Mark all unread notifications as read for the current user."""
    try:
        service = NotificationService(db)
        count = await service.mark_all_notifications_as_read(user_id=uuid.UUID(user_id))
        await db.commit()
        return {"status": "all_read", "marked_count": count}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/{notification_id}")
async def dismiss_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Dismiss (delete) a notification."""
    try:
        service = NotificationService(db)
        result = await service.delete_notification(
            notification_id=uuid.UUID(notification_id),
            user_id=uuid.UUID(user_id),
        )
        await db.commit()
        return result
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/settings")
async def get_notification_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Get the current user's notification delivery preferences."""
    try:
        service = NotificationService(db)
        settings = await service.get_user_notification_settings(user_id=uuid.UUID(user_id))
        return {
            "email_alerts": settings.email_alerts,
            "push_notifications": settings.push_notifications,
            "desktop_alerts": settings.desktop_alerts,
            "sound_alerts": settings.sound_alerts,
            "whatsapp_alerts": settings.whatsapp_alerts,
            "telegram_alerts": settings.telegram_alerts,
            "slack_alerts": settings.slack_alerts,
            "in_app_alerts": settings.in_app_alerts,
            "alert_threshold": settings.alert_threshold,
            "fraud_alert_email": settings.fraud_alert_email,
            "digest_frequency": settings.digest_frequency,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.patch("/settings")
async def update_notification_settings(
    settings: NotificationSettingsRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Update user notification delivery channel preferences.
    Accepts a flat object with boolean values for each channel.
    """
    try:
        service = NotificationService(db)

        update_kwargs: dict[str, Any] = {}
        if settings.email is not None:
            update_kwargs["email_alerts"] = settings.email
        if settings.whatsapp is not None:
            update_kwargs["whatsapp_alerts"] = settings.whatsapp
        if settings.telegram is not None:
            update_kwargs["telegram_alerts"] = settings.telegram
        if settings.slack is not None:
            update_kwargs["slack_alerts"] = settings.slack
        if settings.inApp is not None:
            update_kwargs["in_app_alerts"] = settings.inApp

        updated = await service.update_user_notification_settings(
            user_id=uuid.UUID(user_id),
            **update_kwargs,
        )
        await db.commit()

        return {
            "status": "updated",
            "email_alerts": updated.email_alerts,
            "whatsapp_alerts": updated.whatsapp_alerts,
            "telegram_alerts": updated.telegram_alerts,
            "slack_alerts": updated.slack_alerts,
            "in_app_alerts": updated.in_app_alerts,
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
