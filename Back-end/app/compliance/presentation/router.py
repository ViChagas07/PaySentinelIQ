# ============================================================
# PaySentinelIQ — Compliance Router
# ============================================================


from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from app.auth.dependencies import get_current_tenant_id, require_compliance_officer

router = APIRouter()

# ── Rich mock compliance data ──

_MOCK_COMPLIANCE_RECORDS: list[dict[str, Any]] = [
    {
        "id": "comp-001",
        "tenant_id": "t1",
        "entity_name": "Acme Corporation",
        "entity_type": "company",
        "verification_status": "verified",
        "risk_level": "low",
        "public_records_summary": (
            "No adverse findings in public registries. Registered at "
            "Junta Comercial de Sao Paulo since 2010. Active CNPJ with regular tax filings."
        ),
        "lawsuit_summary": None,
        "sanctions_check": True,
        "pep_check": True,
        "adverse_media": [],
        "last_checked": "2025-05-16T10:00:00Z",
    },
    {
        "id": "comp-002",
        "tenant_id": "t1",
        "entity_name": "Global Trade Ltda",
        "entity_type": "vendor",
        "verification_status": "flagged",
        "risk_level": "high",
        "public_records_summary": (
            "Company registered in Panama with opaque ownership structure. "
            "Beneficial owner not disclosed in public records."
        ),
        "lawsuit_summary": (
            "2 active labor lawsuits (TRT-SP) for unpaid overtime "
            "— total claimed R$450,000. 1 civil suit for breach of contract."
        ),
        "sanctions_check": False,
        "pep_check": True,
        "adverse_media": [
            "2024-12: Investigation by Ministerio Publico do Trabalho "
            "for irregular subcontracting practices",
            "2025-03: Negative press coverage regarding supply chain labor conditions",
        ],
        "last_checked": "2025-05-15T14:30:00Z",
    },
    {
        "id": "comp-003",
        "tenant_id": "t1",
        "entity_name": "Maria Garcia",
        "entity_type": "employee",
        "verification_status": "unverified",
        "risk_level": "medium",
        "public_records_summary": (
            "Pending background check completion. CPF validation passed. "
            "No criminal records found in preliminary search."
        ),
        "lawsuit_summary": None,
        "sanctions_check": True,
        "pep_check": False,
        "adverse_media": [],
        "last_checked": "2025-05-14T09:00:00Z",
    },
    {
        "id": "comp-004",
        "tenant_id": "t1",
        "entity_name": "TechServices Brasil S.A.",
        "entity_type": "vendor",
        "verification_status": "verified",
        "risk_level": "low",
        "public_records_summary": (
            "Publicly traded company (B3: TCSV3). Regular CVM filings. "
            "Audited financial statements available. ISO 27001 certified."
        ),
        "lawsuit_summary": None,
        "sanctions_check": True,
        "pep_check": True,
        "adverse_media": [],
        "last_checked": "2025-05-13T11:00:00Z",
    },
    {
        "id": "comp-005",
        "tenant_id": "t1",
        "entity_name": "Roberto Almeida MEI",
        "entity_type": "vendor",
        "verification_status": "flagged",
        "risk_level": "medium",
        "public_records_summary": (
            "MEI registered since 2022. Revenue within MEI limits. "
            "CNPJ active with regular DASN filings."
        ),
        "lawsuit_summary": (
            "1 small claims court case (JEC) — consumer complaint, R$3,500. Settled in 2024."
        ),
        "sanctions_check": True,
        "pep_check": False,
        "adverse_media": [],
        "last_checked": "2025-05-12T15:00:00Z",
    },
    {
        "id": "comp-006",
        "tenant_id": "t1",
        "entity_name": "Thomas Moore",
        "entity_type": "employee",
        "verification_status": "flagged",
        "risk_level": "critical",
        "public_records_summary": (
            "Executive-level position. Offshore company connections "
            "detected in Panama Papers database. Complex corporate structure "
            "involving 3 offshore entities."
        ),
        "lawsuit_summary": (
            "Named in 1 ongoing investigation by COAF "
            "(Conselho de Controle de Atividades Financeiras) "
            "regarding unusual financial transactions."
        ),
        "sanctions_check": False,
        "pep_check": True,
        "adverse_media": [
            "2024-08: Mentioned in investigacao sobre esquema de evasao fiscal via offshores",
            "2025-01: Corporate restructuring flagged by compliance monitoring systems",
        ],
        "last_checked": "2025-05-10T16:00:00Z",
    },
    {
        "id": "comp-007",
        "tenant_id": "t1",
        "entity_name": "Instituto de Pesquisa Avancada",
        "entity_type": "company",
        "verification_status": "verified",
        "risk_level": "low",
        "public_records_summary": (
            "Non-profit research institute. Registered with CNPq and "
            "Ministerio da Ciencia e Tecnologia. Regular grant reporting."
        ),
        "lawsuit_summary": None,
        "sanctions_check": True,
        "pep_check": True,
        "adverse_media": [],
        "last_checked": "2025-05-09T10:00:00Z",
    },
    {
        "id": "comp-008",
        "tenant_id": "t1",
        "entity_name": "Logistics Express Transportes",
        "entity_type": "vendor",
        "verification_status": "unverified",
        "risk_level": "medium",
        "public_records_summary": (
            "Transportation company with ANTT registration. "
            "Fleet of 47 vehicles. 3 pending labor inspections."
        ),
        "lawsuit_summary": (
            "5 active labor lawsuits (TRT-RJ) — predominantly overtime "
            "and hazard pay claims. Total potential liability: R$1.2M."
        ),
        "sanctions_check": True,
        "pep_check": False,
        "adverse_media": [
            "2025-02: Local news report on driver working conditions",
        ],
        "last_checked": "2025-05-08T13:00:00Z",
    },
]


class ComplianceResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    entity_name: str
    entity_type: str
    verification_status: str
    risk_level: str
    public_records_summary: str | None = None
    sanctions_check: bool = False
    pep_check: bool = False
    adverse_media: list[str] = []
    last_checked: str | None = None


def _filter_compliance(entity_type: str | None = None) -> list[dict[str, Any]]:
    if entity_type:
        result: list[dict[str, Any]] = []
        for r in _MOCK_COMPLIANCE_RECORDS:
            if isinstance(r, dict) and r.get("entity_type") == entity_type:
                result.append(r)
        return result
    return _MOCK_COMPLIANCE_RECORDS


@router.get("")
async def list_compliance_records(
    tenant_id: str = Depends(get_current_tenant_id),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    entity_type: str | None = None,
) -> dict[str, Any]:
    """List compliance records for the tenant."""
    filtered = _filter_compliance(entity_type)
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


@router.get("/{compliance_id}", response_model=ComplianceResponse)
async def get_compliance_record(
    compliance_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ComplianceResponse:
    """Get a single compliance record."""
    for record in _MOCK_COMPLIANCE_RECORDS:
        if isinstance(record, dict) and record.get("id") == compliance_id:
            return ComplianceResponse(**record)

    return ComplianceResponse(
        id=compliance_id,
        entity_name="Unknown Entity",
        entity_type="company",
        verification_status="unverified",
        risk_level="low",
        public_records_summary="No records found.",
        sanctions_check=False,
        pep_check=False,
        last_checked=None,
    )


@router.post("/check")
async def trigger_compliance_check(
    entity_id: str,
    entity_type: str = "company",
    payload: dict[str, Any] = Depends(require_compliance_officer),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    """
    Trigger a compliance check for an entity.
    Emits ComplianceCheckTriggeredEvent.
    """
    from app.tasks import run_compliance_check

    task = run_compliance_check.delay(entity_id, tenant_id, entity_type)
    return {"status": "triggered", "task_id": task.id}
