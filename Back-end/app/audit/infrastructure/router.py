# ============================================================
# PaySentinelIQ — Audit Logs Router (Read-Only)
# ============================================================


from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_tenant_id, require_auditor

router = APIRouter()

# ── Rich mock audit log entries ──

_MOCK_AUDIT_LOGS = [
    {
        "id": "al-001",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "fraud.alert_reviewed",
        "entity_type": "fraud_alert",
        "entity_id": "FR-002",
        "details": {"resolution": "Escalated to compliance team", "review_time_seconds": 340},
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-16T14:30:00Z",
    },
    {
        "id": "al-002",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "user.login",
        "entity_type": "user",
        "entity_id": "user-001",
        "details": {"method": "password", "mfa_verified": True, "ip": "192.168.1.45"},
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-16T08:00:00Z",
    },
    {
        "id": "al-003",
        "tenant_id": "t1",
        "user_id": "user-002",
        "user_name": "Carlos Oliveira",
        "action": "document.uploaded",
        "entity_type": "document",
        "entity_id": "doc-014",
        "details": {
            "file_name": "Q2_Payroll_2025.pdf",
            "file_size_bytes": 2457600,
            "document_type": "payroll_report",
        },
        "ip_address": "192.168.1.52",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "created_at": "2025-05-16T09:45:00Z",
    },
    {
        "id": "al-004",
        "tenant_id": "t1",
        "user_id": "user-002",
        "user_name": "Carlos Oliveira",
        "action": "fraud.alert_created",
        "entity_type": "fraud_alert",
        "entity_id": "FR-001",
        "details": {
            "risk_score": 72,
            "anomaly_category": "salary_discrepancy",
            "ai_confidence": 0.92,
        },
        "ip_address": "192.168.1.52",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "created_at": "2025-05-16T09:15:00Z",
    },
    {
        "id": "al-005",
        "tenant_id": "t1",
        "user_id": "user-003",
        "user_name": "Ana Silva",
        "action": "compliance.checked",
        "entity_type": "compliance_report",
        "entity_id": "comp-001",
        "details": {
            "entity_name": "Acme Corporation",
            "result": "verified",
            "checks_performed": ["sanctions", "pep", "adverse_media"],
        },
        "ip_address": "192.168.1.60",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "created_at": "2025-05-15T16:00:00Z",
    },
    {
        "id": "al-006",
        "tenant_id": "t1",
        "user_id": "user-004",
        "user_name": "Roberto Lima",
        "action": "payroll.created",
        "entity_type": "payroll",
        "entity_id": "pr-001",
        "details": {
            "employee_name": "John D. Smith",
            "gross_pay": 14250.00,
            "period": "2025-05-01 to 2025-05-15",
        },
        "ip_address": "192.168.1.70",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-16T08:00:00Z",
    },
    {
        "id": "al-007",
        "tenant_id": "t1",
        "user_id": "user-004",
        "user_name": "Roberto Lima",
        "action": "payroll.approved",
        "entity_type": "payroll",
        "entity_id": "pr-004",
        "details": {"approved_by": "Roberto Lima", "risk_score": 10, "verified_by_ai": True},
        "ip_address": "192.168.1.70",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-14T16:00:00Z",
    },
    {
        "id": "al-008",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "fraud.alert_resolved",
        "entity_type": "fraud_alert",
        "entity_id": "FR-007",
        "details": {
            "resolution": "false_positive",
            "notes": "Schema version mismatch only — no financial impact",
        },
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-13T14:00:00Z",
    },
    {
        "id": "al-009",
        "tenant_id": "t1",
        "user_id": "user-005",
        "user_name": "Julia Costa",
        "action": "document.verified",
        "entity_type": "document",
        "entity_id": "doc-005",
        "details": {"ocr_confidence": 97.5, "risk_score": 47, "fraud_indicators_found": 2},
        "ip_address": "192.168.1.80",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "created_at": "2025-05-14T11:30:00Z",
    },
    {
        "id": "al-010",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "report.generated",
        "entity_type": "report",
        "entity_id": "rpt-003",
        "details": {"report_type": "monthly_fraud_summary", "period": "2025-04", "format": "pdf"},
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-12T10:00:00Z",
    },
    {
        "id": "al-011",
        "tenant_id": "t1",
        "user_id": "user-002",
        "user_name": "Carlos Oliveira",
        "action": "settings.updated",
        "entity_type": "settings",
        "entity_id": "user-002",
        "details": {
            "changed_fields": ["alert_threshold", "email_notifications"],
            "old_threshold": 70,
            "new_threshold": 60,
        },
        "ip_address": "192.168.1.52",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        "created_at": "2025-05-15T14:20:00Z",
    },
    {
        "id": "al-012",
        "tenant_id": "t1",
        "user_id": "user-003",
        "user_name": "Ana Silva",
        "action": "document.flagged",
        "entity_type": "document",
        "entity_id": "doc-012",
        "details": {"risk_level": "critical", "anomaly": "tax_evasion", "risk_score": 93},
        "ip_address": "192.168.1.60",
        "user_agent": "Mozilla/5.0 (X11; Linux x86_64)",
        "created_at": "2025-05-10T11:30:00Z",
    },
    {
        "id": "al-013",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "user.logout",
        "entity_type": "user",
        "entity_id": "user-001",
        "details": {"session_duration_minutes": 480},
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-15T18:00:00Z",
    },
    {
        "id": "al-014",
        "tenant_id": "t1",
        "user_id": "user-001",
        "user_name": "Sarah Mitchell",
        "action": "user.mfa_verified",
        "entity_type": "user",
        "entity_id": "user-001",
        "details": {"method": "totp", "verified": True},
        "ip_address": "192.168.1.45",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-16T08:01:00Z",
    },
    {
        "id": "al-015",
        "tenant_id": "t1",
        "user_id": "user-004",
        "user_name": "Roberto Lima",
        "action": "payroll.created",
        "entity_type": "payroll",
        "entity_id": "pr-003",
        "details": {
            "employee_name": "Robert Chen",
            "gross_pay": 21500.00,
            "period": "2025-05-01 to 2025-05-15",
        },
        "ip_address": "192.168.1.70",
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "created_at": "2025-05-14T10:30:00Z",
    },
]


def _filter_audit_logs(
    action: str | None = None,
    user_id: str | None = None,
    entity_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> list[dict]:
    result = _MOCK_AUDIT_LOGS
    if action:
        result = [rec for rec in result if rec["action"] == action]
    if user_id:
        result = [rec for rec in result if rec["user_id"] == user_id]
    if entity_type:
        result = [rec for rec in result if rec["entity_type"] == entity_type]
    if from_date:
        result = [rec for rec in result if rec["created_at"] >= from_date]
    if to_date:
        result = [rec for rec in result if rec["created_at"] <= to_date]
    return result


@router.get("")
async def list_audit_logs(
    tenant_id: str = Depends(get_current_tenant_id),
    payload: dict = Depends(require_auditor),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    action: str | None = None,
    user_id: str | None = None,
    entity_type: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
):
    """
    List immutable audit log entries.
    Read-only — audit logs are append-only by design.
    """
    filtered = _filter_audit_logs(action, user_id, entity_type, from_date, to_date)
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": filtered[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
