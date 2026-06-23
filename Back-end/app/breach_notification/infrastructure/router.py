# ============================================================
# PaySentinelIQ — Breach Notification Router
# LGPD Art. 48: Register, track, and resolve data breaches
# ============================================================

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_token_payload
from app.breach_notification.application.service import BreachNotificationService
from app.shared.database import get_db
from app.shared.orm_models import DataBreachModel

router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────


class BreachCreateRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    title: str = Field(min_length=3, max_length=300)
    description: str = Field(min_length=10, max_length=5000)
    discovered_at: str = Field(
        description="ISO 8601 timestamp of when the breach was discovered",
    )
    occurred_at: str | None = Field(
        default=None,
        description="ISO 8601 timestamp of when the breach occurred (defaults to discovered_at)",
    )
    affected_data_categories: list[str] = Field(
        default_factory=list,
        description="e.g. ['name','email','cpf','financial']",
    )
    number_affected_subjects: int | None = Field(default=None, ge=1)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")
    containment_actions: dict[str, Any] | None = None


class BreachResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    title: str
    description: str
    discovered_at: str
    occurred_at: str | None
    risk_level: str
    affected_data_categories: list[str]
    number_affected_subjects: int | None
    anpd_notification_status: str
    resolution_status: str
    subjects_communicated: bool
    created_at: str


class BreachDetailResponse(BreachResponse):
    """Full detail including optional fields."""
    anpd_notification_date: str | None = None
    anpd_protocol_number: str | None = None
    anpd_justification: str | None = None
    subject_communication_date: str | None = None
    containment_actions: dict[str, Any] | None = None
    root_cause: str | None = None
    resolution_date: str | None = None
    lessons_learned: str | None = None


class ANPDNotifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    protocol_number: str | None = Field(default=None, max_length=100)
    justification: str | None = Field(default=None, max_length=2000)


class ResolveRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    resolution_status: str = Field(
        default="resolved",
        pattern="^(resolved|closed)$",
    )
    lessons_learned: str | None = Field(default=None, max_length=5000)


# ── Helpers ────────────────────────────────────────────────────────


def _model_to_response(record: DataBreachModel) -> BreachResponse:
    return BreachResponse(
        id=str(record.id),
        title=record.title,
        description=record.description,
        discovered_at=record.discovered_at.isoformat(),
        occurred_at=record.occurred_at.isoformat() if record.occurred_at else None,
        risk_level=record.risk_level,
        affected_data_categories=record.affected_data_categories or [],
        number_affected_subjects=record.number_affected_subjects,
        anpd_notification_status=record.anpd_notification_status,
        resolution_status=record.resolution_status,
        subjects_communicated=record.subjects_communicated,
        created_at=record.created_at.isoformat(),
    )


def _model_to_detail(record: DataBreachModel) -> BreachDetailResponse:
    return BreachDetailResponse(
        id=str(record.id),
        title=record.title,
        description=record.description,
        discovered_at=record.discovered_at.isoformat(),
        occurred_at=record.occurred_at.isoformat() if record.occurred_at else None,
        risk_level=record.risk_level,
        affected_data_categories=record.affected_data_categories or [],
        number_affected_subjects=record.number_affected_subjects,
        anpd_notification_status=record.anpd_notification_status,
        anpd_notification_date=record.anpd_notification_date.isoformat()
            if record.anpd_notification_date else None,
        anpd_protocol_number=record.anpd_protocol_number,
        anpd_justification=record.anpd_justification,
        subjects_communicated=record.subjects_communicated,
        subject_communication_date=record.subject_communication_date.isoformat()
            if record.subject_communication_date else None,
        containment_actions=record.containment_actions,
        root_cause=record.root_cause,
        resolution_status=record.resolution_status,
        resolution_date=record.resolution_date.isoformat()
            if record.resolution_date else None,
        lessons_learned=record.lessons_learned,
        created_at=record.created_at.isoformat(),
    )


# ── Endpoints ──────────────────────────────────────────────────────


@router.post("/breach-notifications", response_model=BreachDetailResponse, status_code=201)
async def register_breach(
    body: BreachCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> BreachDetailResponse:
    """
    Register a new data breach / security incident.

    LGPD Article 48 requires that:
      - Every personal data breach is documented
      - ANPD is notified within 72 hours
      - Affected data subjects are informed (in certain cases)

    This endpoint records the incident and can optionally trigger
    the automated ANPD notification workflow.
    """
    user_id = uuid.UUID(payload["sub"])
    tenant_id = uuid.UUID(payload["tenant_id"])

    discovered = datetime.fromisoformat(body.discovered_at)
    occurred = (
        datetime.fromisoformat(body.occurred_at)
        if body.occurred_at else None
    )

    record = await BreachNotificationService.create_breach(
        db=db,
        tenant_id=tenant_id,
        reported_by=user_id,
        title=body.title,
        description=body.description,
        discovered_at=discovered,
        occurred_at=occurred,
        affected_data_categories=body.affected_data_categories,
        number_affected_subjects=body.number_affected_subjects,
        risk_level=body.risk_level,
        containment_actions=body.containment_actions,
    )

    # In production: enqueue Celery task for ANPD notification if configured
    # from app.shared.settings import get_settings
    # if get_settings().BREACH_AUTO_NOTIFY_ANPD:
    #     from app.tasks.breach_tasks import notify_anpd_of_breach
    #     notify_anpd_of_breach.delay(str(record.id), str(tenant_id))

    await db.commit()
    return _model_to_detail(record)


@router.get("/breach-notifications", response_model=list[BreachResponse])
async def list_breaches(
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
    status: str | None = Query(default=None, description="Filter by resolution_status"),
    risk_level: str | None = Query(default=None, description="Filter by risk_level"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[BreachResponse]:
    """
    List all data breaches for the current tenant.
    Supports optional filtering by status and risk level.
    """
    tenant_id = uuid.UUID(payload["tenant_id"])
    records = await BreachNotificationService.list_breaches(
        db=db,
        tenant_id=tenant_id,
        status=status,
        risk_level=risk_level,
        limit=limit,
        offset=offset,
    )
    return [_model_to_response(r) for r in records]


@router.get("/breach-notifications/{breach_id}", response_model=BreachDetailResponse)
async def get_breach(
    breach_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> BreachDetailResponse:
    """Get full details of a specific data breach."""
    tenant_id = uuid.UUID(payload["tenant_id"])
    record = await BreachNotificationService.get_breach(db, breach_id, tenant_id)
    return _model_to_detail(record)


@router.post("/breach-notifications/{breach_id}/notify-anpd", response_model=BreachDetailResponse)
async def notify_anpd(
    breach_id: uuid.UUID,
    body: ANPDNotifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> BreachDetailResponse:
    """
    Record that ANPD has been notified about a data breach.

    In production this would trigger an email to ANPD with the
    structured notification per LGPD Art. 48.
    """
    tenant_id = uuid.UUID(payload["tenant_id"])
    record = await BreachNotificationService.mark_anpd_notified(
        db=db,
        breach_id=breach_id,
        tenant_id=tenant_id,
        protocol_number=body.protocol_number,
        justification=body.justification,
    )
    await db.commit()
    return _model_to_detail(record)


@router.post("/breach-notifications/{breach_id}/notify-subjects", response_model=BreachDetailResponse)
async def notify_subjects(
    breach_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> BreachDetailResponse:
    """
    Record that affected data subjects have been communicated with.
    """
    tenant_id = uuid.UUID(payload["tenant_id"])
    record = await BreachNotificationService.mark_subjects_communicated(
        db=db,
        breach_id=breach_id,
        tenant_id=tenant_id,
    )
    await db.commit()
    return _model_to_detail(record)


@router.post("/breach-notifications/{breach_id}/resolve", response_model=BreachDetailResponse)
async def resolve_breach(
    breach_id: uuid.UUID,
    body: ResolveRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    payload: dict[str, Any] = Depends(get_token_payload),
) -> BreachDetailResponse:
    """
    Mark a data breach as resolved or closed.
    """
    tenant_id = uuid.UUID(payload["tenant_id"])
    record = await BreachNotificationService.resolve_breach(
        db=db,
        breach_id=breach_id,
        tenant_id=tenant_id,
        resolution_status=body.resolution_status,
        lessons_learned=body.lessons_learned,
    )
    await db.commit()
    return _model_to_detail(record)
