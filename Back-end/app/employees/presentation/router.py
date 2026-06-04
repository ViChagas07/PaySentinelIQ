# ============================================================
# PaySentinelIQ — Employees Router
# ============================================================


from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import get_current_tenant_id
from app.shared.exceptions import NotFoundError

router = APIRouter()

# ── Rich mock employee data matching front-end Employee type ──

_MOCK_EMPLOYEES = [
    {
        "id": "emp-001",
        "tenant_id": "t1",
        "full_name": "John D. Smith",
        "email": "john.smith@company.com",
        "department": "Engineering",
        "position": "Senior Software Engineer",
        "salary": 142500.00,
        "hire_date": "2019-03-15",
        "status": "active",
        "risk_score": 72.0,
    },
    {
        "id": "emp-002",
        "tenant_id": "t1",
        "full_name": "Maria Garcia",
        "email": "maria.garcia@company.com",
        "department": "Sales",
        "position": "Regional Sales Manager",
        "salary": 89000.00,
        "hire_date": "2020-07-01",
        "status": "active",
        "risk_score": 25.0,
    },
    {
        "id": "emp-003",
        "tenant_id": "t1",
        "full_name": "Robert Chen",
        "email": "robert.chen@company.com",
        "department": "Finance",
        "position": "CFO",
        "salary": 215000.00,
        "hire_date": "2017-01-10",
        "status": "active",
        "risk_score": 55.0,
    },
    {
        "id": "emp-004",
        "tenant_id": "t1",
        "full_name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "department": "HR",
        "position": "HR Director",
        "salary": 62000.00,
        "hire_date": "2021-04-20",
        "status": "active",
        "risk_score": 10.0,
    },
    {
        "id": "emp-005",
        "tenant_id": "t1",
        "full_name": "David Wilson",
        "email": "david.wilson@company.com",
        "department": "Operations",
        "position": "Operations Manager",
        "salary": 78000.00,
        "hire_date": "2018-09-05",
        "status": "active",
        "risk_score": 47.0,
    },
    {
        "id": "emp-006",
        "tenant_id": "t1",
        "full_name": "Emily Davis",
        "email": "emily.davis@company.com",
        "department": "Marketing",
        "position": "Marketing Coordinator",
        "salary": 51000.00,
        "hire_date": "2023-02-14",
        "status": "active",
        "risk_score": 5.0,
    },
    {
        "id": "emp-007",
        "tenant_id": "t1",
        "full_name": "Michael Brown",
        "email": "michael.brown@company.com",
        "department": "Legal",
        "position": "General Counsel",
        "salary": 187000.00,
        "hire_date": "2016-06-01",
        "status": "active",
        "risk_score": 88.0,
    },
    {
        "id": "emp-008",
        "tenant_id": "t1",
        "full_name": "Lisa Anderson",
        "email": "lisa.anderson@company.com",
        "department": "Sales",
        "position": "Account Executive",
        "salary": 94000.00,
        "hire_date": "2021-11-15",
        "status": "active",
        "risk_score": 8.0,
    },
    {
        "id": "emp-009",
        "tenant_id": "t1",
        "full_name": "James Taylor",
        "email": "james.taylor@company.com",
        "department": "Customer Support",
        "position": "Support Lead",
        "salary": 45000.00,
        "hire_date": "2022-08-01",
        "status": "active",
        "risk_score": 30.0,
    },
    {
        "id": "emp-010",
        "tenant_id": "t1",
        "full_name": "Anna White",
        "email": "anna.white@company.com",
        "department": "Engineering",
        "position": "DevOps Engineer",
        "salary": 112000.00,
        "hire_date": "2020-01-20",
        "status": "active",
        "risk_score": 15.0,
    },
    {
        "id": "emp-011",
        "tenant_id": "t1",
        "full_name": "Thomas Moore",
        "email": "thomas.moore@company.com",
        "department": "Executive",
        "position": "CEO",
        "salary": 350000.00,
        "hire_date": "2015-03-01",
        "status": "active",
        "risk_score": 93.0,
    },
    {
        "id": "emp-012",
        "tenant_id": "t1",
        "full_name": "Carla Mendes",
        "email": "carla.mendes@company.com",
        "department": "Finance",
        "position": "Senior Accountant",
        "salary": 73000.00,
        "hire_date": "2019-05-10",
        "status": "active",
        "risk_score": 12.0,
    },
    {
        "id": "emp-013",
        "tenant_id": "t1",
        "full_name": "Paulo Ferreira",
        "email": "paulo.ferreira@company.com",
        "department": "IT",
        "position": "IT Manager",
        "salary": 98000.00,
        "hire_date": "2018-11-01",
        "status": "active",
        "risk_score": 20.0,
    },
    {
        "id": "emp-014",
        "tenant_id": "t1",
        "full_name": "Fernanda Costa",
        "email": "fernanda.costa@company.com",
        "department": "HR",
        "position": "Payroll Specialist",
        "salary": 55000.00,
        "hire_date": "2022-03-01",
        "status": "on_leave",
        "risk_score": 3.0,
    },
    {
        "id": "emp-015",
        "tenant_id": "t1",
        "full_name": "Ricardo Santos",
        "email": "ricardo.santos@company.com",
        "department": "Operations",
        "position": "Logistics Coordinator",
        "salary": 42000.00,
        "hire_date": "2023-01-10",
        "status": "terminated",
        "risk_score": 60.0,
    },
]


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    tenant_id: str
    full_name: str
    email: str
    department: str
    position: str
    salary: float
    hire_date: str
    status: str
    risk_score: float


class PaginatedResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    data: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


def _filter_employees(
    status: str | None = None,
    department: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = _MOCK_EMPLOYEES
    if status:
        result = [e for e in result if e["status"] == status]
    if department:
        result = [e for e in result if str(e.get("department", "")).lower() == department.lower()]
    if search:
        s = search.lower()
        result = [
            e
            for e in result
            if s in str(e.get("full_name", "")).lower()
            or s in str(e.get("email", "")).lower()
            or s in str(e.get("department", "")).lower()
            or s in str(e.get("position", "")).lower()
        ]
    return result


@router.get("")
async def list_employees(
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    department: str | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """List employees for the current tenant with optional filters."""
    filtered = _filter_employees(status, department, search)
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


@router.get("/{employee_id}", response_model=EmployeeResponse)
async def get_employee(
    employee_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> EmployeeResponse:
    """Get a single employee by ID."""
    for emp in _MOCK_EMPLOYEES:
        if emp["id"] == employee_id:
            return EmployeeResponse(**emp)  # type: ignore[arg-type]
    raise NotFoundError("Employee", employee_id)


@router.get("/department/{department}/stats")
async def get_department_stats(
    department: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """Get aggregate stats for a department."""
    dept_employees: list[dict[str, Any]] = [
        e for e in _MOCK_EMPLOYEES
        if str(e.get("department", "")).lower() == department.lower()
    ]
    if not dept_employees:
        return {
            "department": department,
            "employee_count": 0,
            "avg_salary": 0,
            "avg_risk_score": 0,
            "active_count": 0,
        }

    avg_salary = sum(float(e["salary"]) for e in dept_employees) / len(dept_employees)
    avg_risk = sum(float(e["risk_score"]) for e in dept_employees) / len(dept_employees)
    active = sum(1 for e in dept_employees if str(e.get("status", "")) == "active")

    return {
        "department": department,
        "employee_count": len(dept_employees),
        "avg_salary": round(avg_salary, 2),
        "avg_risk_score": round(avg_risk, 1),
        "active_count": active,
    }
