# ============================================================
# PaySentinelIQ — Breach Notification Service
# LGPD Art. 48: 72-hour breach notification to ANPD + data subjects
# ============================================================

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.exceptions import NotFoundError, ValidationError
from app.shared.orm_models import DataBreachModel
from app.shared.settings import get_settings

settings = get_settings()


class BreachNotificationService:
    """Business logic for security incident management and ANPD compliance."""

    # ── Deadline helpers ───────────────────────────────────

    @staticmethod
    def compute_anpd_deadline(discovered_at: datetime) -> datetime:
        """Return the absolute deadline (72h from discovery) for ANPD notification."""
        return discovered_at + timedelta(hours=settings.BREACH_DEADLINE_HOURS)

    @staticmethod
    def is_within_deadline(discovered_at: datetime) -> bool:
        """Check if the current time is still within the 72-hour notification window."""
        return datetime.now(timezone.utc) < BreachNotificationService.compute_anpd_deadline(discovered_at)

    # ── CRUD ───────────────────────────────────────────────

    @staticmethod
    async def create_breach(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        reported_by: uuid.UUID,
        title: str,
        description: str,
        discovered_at: datetime,
        occurred_at: datetime | None = None,
        affected_data_categories: list[str] | None = None,
        number_affected_subjects: int | None = None,
        risk_level: str = "medium",
        containment_actions: dict[str, Any] | None = None,
    ) -> DataBreachModel:
        """Register a new security incident / data breach."""
        record = DataBreachModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            reported_by=reported_by,
            title=title,
            description=description,
            discovered_at=discovered_at,
            occurred_at=occurred_at or discovered_at,
            affected_data_categories=affected_data_categories or [],
            number_affected_subjects=number_affected_subjects,
            risk_level=risk_level,
            containment_actions=containment_actions or {},
        )
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def get_breach(
        db: AsyncSession,
        breach_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> DataBreachModel:
        """Fetch a single breach record by ID (scoped to tenant)."""
        stmt = select(DataBreachModel).where(
            DataBreachModel.id == breach_id,
            DataBreachModel.tenant_id == tenant_id,
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()
        if record is None:
            raise NotFoundError("DataBreach", str(breach_id))
        return record

    @staticmethod
    async def list_breaches(
        db: AsyncSession,
        tenant_id: uuid.UUID,
        status: str | None = None,
        risk_level: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[DataBreachModel]:
        """List breach records for a tenant, optionally filtered."""
        stmt = select(DataBreachModel).where(
            DataBreachModel.tenant_id == tenant_id,
        )
        if status:
            stmt = stmt.where(DataBreachModel.resolution_status == status)
        if risk_level:
            stmt = stmt.where(DataBreachModel.risk_level == risk_level)
        stmt = stmt.order_by(DataBreachModel.discovered_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    # ── ANPD Notification ──────────────────────────────────

    @staticmethod
    async def mark_anpd_notified(
        db: AsyncSession,
        breach_id: uuid.UUID,
        tenant_id: uuid.UUID,
        protocol_number: str | None = None,
        justification: str | None = None,
    ) -> DataBreachModel:
        """Record that ANPD has been notified about a breach."""
        record = await BreachNotificationService.get_breach(db, breach_id, tenant_id)

        if record.anpd_notification_status in ("notified", "exempt"):
            raise ValidationError(f"ANPD already notified (status: {record.anpd_notification_status})")

        if BreachNotificationService.is_within_deadline(record.discovered_at):
            record.anpd_notification_status = "within_deadline"
        else:
            record.anpd_notification_status = "missed_deadline"

        record.anpd_notification_date = datetime.now(timezone.utc)
        if protocol_number:
            record.anpd_protocol_number = protocol_number
        if justification:
            record.anpd_justification = justification
        db.add(record)
        await db.flush()
        return record

    @staticmethod
    async def mark_subjects_communicated(
        db: AsyncSession,
        breach_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> DataBreachModel:
        """Record that affected data subjects have been notified."""
        record = await BreachNotificationService.get_breach(db, breach_id, tenant_id)
        record.subjects_communicated = True
        record.subject_communication_date = datetime.now(timezone.utc)
        db.add(record)
        await db.flush()
        return record

    # ── Resolution ─────────────────────────────────────────

    @staticmethod
    async def resolve_breach(
        db: AsyncSession,
        breach_id: uuid.UUID,
        tenant_id: uuid.UUID,
        resolution_status: str = "resolved",
        lessons_learned: str | None = None,
    ) -> DataBreachModel:
        """Mark a breach as resolved/closed."""
        record = await BreachNotificationService.get_breach(db, breach_id, tenant_id)
        record.resolution_status = resolution_status
        record.resolution_date = datetime.now(timezone.utc)
        if lessons_learned:
            record.lessons_learned = lessons_learned
        db.add(record)
        await db.flush()
        return record
