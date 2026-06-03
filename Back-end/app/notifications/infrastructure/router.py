# ============================================================
# PaySentinelIQ — Notifications Router
# ============================================================

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import get_current_tenant_id, get_current_user_id

router = APIRouter()

# ── Rich mock notifications matching front-end NotificationPanel expectations ──

_MOCK_NOTIFICATIONS = [
    {
        "id": "n1", "user_id": "u1",
        "type": "fraud_alert",
        "title": "Critical Fraud Alert: Ghost Employee Detected",
        "message": "AI detected duplicate bank account across 3 payroll records in the Sales department. Risk Score: 91. Immediate analyst review required.",
        "is_read": False, "action_url": "/fraud-intelligence",
        "created_at": (datetime.now(timezone.utc).isoformat()),
    },
    {
        "id": "n2", "user_id": "u1",
        "type": "verification_complete",
        "title": "Document Verification Complete",
        "message": "Q1 Payroll batch #2841 verification finished. 98.4% pass rate. 15 documents flagged for review. Full report available.",
        "is_read": False, "action_url": "/verification-center",
        "created_at": (datetime.now(timezone.utc).isoformat()),
    },
    {
        "id": "n3", "user_id": "u1",
        "type": "ai_insight",
        "title": "AI Insight: Salary Anomaly Pattern Detected",
        "message": "10 employees in Engineering department show unusual overtime patterns. Average overtime 340% above company baseline. Recommend department-wide audit.",
        "is_read": False, "action_url": "/ai-insights",
        "created_at": (datetime.now(timezone.utc).isoformat()),
    },
    {
        "id": "n4", "user_id": "u1",
        "type": "compliance_alert",
        "title": "Compliance Alert: LGPD Data Retention Review",
        "message": "7 employee records approaching 5-year retention limit per LGPD Article 16. Review and anonymize or document continued necessity by Jun 30.",
        "is_read": True, "action_url": "/compliance",
        "created_at": "2025-05-16T10:00:00Z",
    },
    {
        "id": "n5", "user_id": "u1",
        "type": "system",
        "title": "System Update: AI Pipeline v2.4 Deployed",
        "message": "Fraud detection pipeline upgraded to v2.4 with improved Brazilian document forgery detection. 7-stage analysis now includes CNAE cross-referencing.",
        "is_read": True, "action_url": None,
        "created_at": "2025-05-15T08:00:00Z",
    },
    {
        "id": "n6", "user_id": "u1",
        "type": "fraud_alert",
        "title": "Fraud Alert Resolved: False Positive Cleared",
        "message": "Alert FR-007 (Compliance Violation — minor schema version) cleared as false positive. No action required.",
        "is_read": True, "action_url": "/fraud-intelligence",
        "created_at": "2025-05-14T15:30:00Z",
    },
    {
        "id": "n7", "user_id": "u1",
        "type": "verification_complete",
        "title": "Executive Payroll Q1 Verification Finished",
        "message": "Executive payroll batch processed. 1 critical alert (FR-012: potential tax evasion via offshore entity). Escalated to compliance team.",
        "is_read": False, "action_url": "/verification-center",
        "created_at": "2025-05-14T11:00:00Z",
    },
    {
        "id": "n8", "user_id": "u1",
        "type": "ai_insight",
        "title": "AI Insight: Risk Trend Reversal Detected",
        "message": "Overall risk score decreased 2.3% this month. Finance department showing improvement. Operations now flagged as emerging risk area.",
        "is_read": True, "action_url": "/ai-insights",
        "created_at": "2025-05-13T09:00:00Z",
    },
]


class NotificationResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    type: str
    title: str
    message: str
    is_read: bool
    action_url: str | None = None
    created_at: str


@router.get("")
async def list_notifications(
    user_id: str = Depends(get_current_user_id),
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    unread_only: bool = False,
):
    """List notifications for the current user."""
    notifications = _MOCK_NOTIFICATIONS
    if unread_only:
        notifications = [n for n in notifications if not n["is_read"]]
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
):
    """Get count of unread notifications."""
    unread = sum(1 for n in _MOCK_NOTIFICATIONS if not n["is_read"])
    return {"count": unread}


@router.patch("/{notification_id}/read")
async def mark_as_read(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Mark a notification as read."""
    return {"status": "read", "notification_id": notification_id}


@router.post("/read-all")
async def mark_all_read(user_id: str = Depends(get_current_user_id)):
    """Mark all notifications as read."""
    return {"status": "all_read"}
