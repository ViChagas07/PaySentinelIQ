# ============================================================
# PaySentinelIQ — Payroll Router
# ============================================================

from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_current_tenant_id, get_token_payload, require_hr_or_payroll
from app.shared.exceptions import NotFoundError
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

router = APIRouter()

# ── Rich mock payroll data ──

_MOCK_PAYROLLS = [
    {
        "id": "pr-001", "tenant_id": "t1", "employee_id": "emp-001", "employee_name": "John D. Smith",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 14250.00, "net_pay": 11400.00, "tax_withheld": 2850.00,
        "deductions": [
            {"type": "INSS", "amount": 908.85, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 1487.50, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "VT", "amount": 227.50, "description": "Vale Transporte"},
            {"type": "VR", "amount": 226.15, "description": "Vale Refeicao"},
        ],
        "status": "verified", "risk_score": 72.0, "verified_by_ai": True,
        "created_at": "2025-05-16T08:00:00Z", "updated_at": "2025-05-16T09:15:00Z",
    },
    {
        "id": "pr-002", "tenant_id": "t1", "employee_id": "emp-002", "employee_name": "Maria Garcia",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 8900.00, "net_pay": 7510.00, "tax_withheld": 1390.00,
        "deductions": [
            {"type": "INSS", "amount": 751.98, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 438.02, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Plano de Saude", "amount": 200.00, "description": "Plano de Saude Familiar"},
        ],
        "status": "pending_verification", "risk_score": 25.0, "verified_by_ai": False,
        "created_at": "2025-05-15T14:00:00Z", "updated_at": "2025-05-15T14:00:00Z",
    },
    {
        "id": "pr-003", "tenant_id": "t1", "employee_id": "emp-003", "employee_name": "Robert Chen",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 21500.00, "net_pay": 15760.00, "tax_withheld": 5740.00,
        "deductions": [
            {"type": "INSS", "amount": 908.85, "description": "Previdencia Social (teto)"},
            {"type": "IRRF", "amount": 4631.15, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Previdencia Privada", "amount": 200.00, "description": "PGBL"},
        ],
        "status": "flagged", "risk_score": 55.0, "verified_by_ai": True,
        "created_at": "2025-05-14T10:30:00Z", "updated_at": "2025-05-14T11:45:00Z",
    },
    {
        "id": "pr-004", "tenant_id": "t1", "employee_id": "emp-004", "employee_name": "Sarah Johnson",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 6200.00, "net_pay": 5340.00, "tax_withheld": 860.00,
        "deductions": [
            {"type": "INSS", "amount": 620.00, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 75.00, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "VT", "amount": 165.00, "description": "Vale Transporte"},
        ],
        "status": "approved", "risk_score": 10.0, "verified_by_ai": True,
        "created_at": "2025-05-13T09:00:00Z", "updated_at": "2025-05-14T16:00:00Z",
    },
    {
        "id": "pr-005", "tenant_id": "t1", "employee_id": "emp-005", "employee_name": "David Wilson",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 7800.00, "net_pay": 6520.00, "tax_withheld": 1280.00,
        "deductions": [
            {"type": "INSS", "amount": 702.00, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 328.00, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Sindicato", "amount": 150.00, "description": "Contribuicao Sindical"},
            {"type": "VR", "amount": 100.00, "description": "Vale Refeicao"},
        ],
        "status": "verified", "risk_score": 47.0, "verified_by_ai": True,
        "created_at": "2025-05-12T11:00:00Z", "updated_at": "2025-05-12T15:30:00Z",
    },
    {
        "id": "pr-006", "tenant_id": "t1", "employee_id": "emp-006", "employee_name": "Emily Davis",
        "period_start": "2025-05-01", "period_end": "2025-05-15",
        "gross_pay": 5100.00, "net_pay": 4530.00, "tax_withheld": 570.00,
        "deductions": [
            {"type": "INSS", "amount": 459.00, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 0.00, "description": "Isento — abaixo do limite"},
            {"type": "VT", "amount": 111.00, "description": "Vale Transporte"},
        ],
        "status": "draft", "risk_score": 5.0, "verified_by_ai": False,
        "created_at": "2025-05-11T16:00:00Z", "updated_at": "2025-05-11T16:00:00Z",
    },
    {
        "id": "pr-007", "tenant_id": "t1", "employee_id": "emp-007", "employee_name": "Michael Brown",
        "period_start": "2025-04-16", "period_end": "2025-04-30",
        "gross_pay": 18700.00, "net_pay": 13980.00, "tax_withheld": 4720.00,
        "deductions": [
            {"type": "INSS", "amount": 908.85, "description": "Previdencia Social (teto)"},
            {"type": "IRRF", "amount": 3611.15, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Plano de Saude", "amount": 200.00, "description": "Plano de Saude"},
        ],
        "status": "rejected", "risk_score": 88.0, "verified_by_ai": True,
        "created_at": "2025-04-30T08:00:00Z", "updated_at": "2025-05-01T14:00:00Z",
    },
    {
        "id": "pr-008", "tenant_id": "t1", "employee_id": "emp-008", "employee_name": "Lisa Anderson",
        "period_start": "2025-04-16", "period_end": "2025-04-30",
        "gross_pay": 9400.00, "net_pay": 7890.00, "tax_withheld": 1510.00,
        "deductions": [
            {"type": "INSS", "amount": 783.98, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 526.02, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "VR", "amount": 200.00, "description": "Vale Refeicao"},
        ],
        "status": "approved", "risk_score": 8.0, "verified_by_ai": True,
        "created_at": "2025-04-29T15:00:00Z", "updated_at": "2025-04-30T10:00:00Z",
    },
    {
        "id": "pr-009", "tenant_id": "t1", "employee_id": "emp-009", "employee_name": "James Taylor",
        "period_start": "2025-04-16", "period_end": "2025-04-30",
        "gross_pay": 4500.00, "net_pay": 4040.00, "tax_withheld": 460.00,
        "deductions": [
            {"type": "INSS", "amount": 405.00, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 0.00, "description": "Isento"},
            {"type": "VT", "amount": 55.00, "description": "Vale Transporte"},
        ],
        "status": "pending_verification", "risk_score": 30.0, "verified_by_ai": False,
        "created_at": "2025-04-28T12:00:00Z", "updated_at": "2025-04-28T12:00:00Z",
    },
    {
        "id": "pr-010", "tenant_id": "t1", "employee_id": "emp-010", "employee_name": "Anna White",
        "period_start": "2025-04-16", "period_end": "2025-04-30",
        "gross_pay": 11200.00, "net_pay": 9230.00, "tax_withheld": 1970.00,
        "deductions": [
            {"type": "INSS", "amount": 908.85, "description": "Previdencia Social (teto)"},
            {"type": "IRRF", "amount": 861.15, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Previdencia Privada", "amount": 200.00, "description": "PGBL"},
        ],
        "status": "verified", "risk_score": 15.0, "verified_by_ai": True,
        "created_at": "2025-04-27T09:00:00Z", "updated_at": "2025-04-27T11:00:00Z",
    },
    {
        "id": "pr-011", "tenant_id": "t1", "employee_id": "emp-011", "employee_name": "Thomas Moore",
        "period_start": "2025-04-16", "period_end": "2025-04-30",
        "gross_pay": 35000.00, "net_pay": 23350.00, "tax_withheld": 11650.00,
        "deductions": [
            {"type": "INSS", "amount": 908.85, "description": "Previdencia Social (teto)"},
            {"type": "IRRF", "amount": 10541.15, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "Plano de Saude Executivo", "amount": 200.00, "description": "Plano de Saude"},
        ],
        "status": "flagged", "risk_score": 93.0, "verified_by_ai": True,
        "created_at": "2025-04-26T10:00:00Z", "updated_at": "2025-04-27T08:30:00Z",
    },
    {
        "id": "pr-012", "tenant_id": "t1", "employee_id": "emp-012", "employee_name": "Carla Mendes",
        "period_start": "2025-04-01", "period_end": "2025-04-15",
        "gross_pay": 7300.00, "net_pay": 6140.00, "tax_withheld": 1160.00,
        "deductions": [
            {"type": "INSS", "amount": 657.00, "description": "Previdencia Social"},
            {"type": "IRRF", "amount": 303.00, "description": "Imposto de Renda Retido na Fonte"},
            {"type": "VT", "amount": 100.00, "description": "Vale Transporte"},
            {"type": "VR", "amount": 100.00, "description": "Vale Refeicao"},
        ],
        "status": "approved", "risk_score": 12.0, "verified_by_ai": True,
        "created_at": "2025-04-15T14:00:00Z", "updated_at": "2025-04-16T09:00:00Z",
    },
]


class PayrollResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    employee_id: str
    tenant_id: str
    period_start: str
    period_end: str
    gross_pay: float
    net_pay: float
    tax_withheld: float
    status: str
    risk_score: float
    verified_by_ai: bool
    employee_name: Optional[str] = None


class PayrollCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    employee_id: str
    period_start: str
    period_end: str
    gross_pay: float = Field(gt=0)
    tax_withheld: float = Field(ge=0)
    deductions: Optional[list[dict]] = None


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: list
    total: int
    page: int
    page_size: int
    total_pages: int


def _filter_payrolls(status: Optional[str] = None, employee_id: Optional[str] = None) -> list[dict]:
    result = _MOCK_PAYROLLS
    if status:
        result = [p for p in result if p["status"] == status]
    if employee_id:
        result = [p for p in result if p["employee_id"] == employee_id]
    return result


@router.get("", response_model=PaginatedResponse)
async def list_payrolls(
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    employee_id: Optional[str] = None,
):
    """List payrolls for the current tenant with optional filters."""
    filtered = _filter_payrolls(status, employee_id)
    total = len(filtered)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    return PaginatedResponse(
        data=filtered[start:end],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{payroll_id}", response_model=PayrollResponse)
async def get_payroll(
    payroll_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Get a single payroll by ID."""
    for p in _MOCK_PAYROLLS:
        if p["id"] == payroll_id:
            return PayrollResponse(**p)
    raise NotFoundError("Payroll", payroll_id)


@router.post("", response_model=PayrollResponse, status_code=201)
async def create_payroll(
    body: PayrollCreateRequest,
    payload: dict = Depends(require_hr_or_payroll),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Create a new payroll entry."""
    return PayrollResponse(
        id="mock-id",
        employee_id=body.employee_id,
        tenant_id=tenant_id,
        period_start=body.period_start,
        period_end=body.period_end,
        gross_pay=body.gross_pay,
        net_pay=body.gross_pay - body.tax_withheld,
        tax_withheld=body.tax_withheld,
        status="draft",
        risk_score=0.0,
        verified_by_ai=False,
    )


@router.patch("/{payroll_id}/approve")
async def approve_payroll(
    payroll_id: str,
    payload: dict = Depends(require_hr_or_payroll),
    tenant_id: str = Depends(get_current_tenant_id),
):
    """Approve a payroll. Emits PayrollApprovedEvent."""
    return {"status": "approved", "payroll_id": payroll_id}
