# ============================================================
# PaySentinelIQ — Base Repository Pattern
# Abstract and concrete async repository with common CRUD
# ============================================================

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, Optional, Sequence, TypeVar

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

ModelType = TypeVar("ModelType")


class AbstractRepository(ABC, Generic[ModelType]):
    """Abstract base repository defining the contract."""

    @abstractmethod
    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        ...

    @abstractmethod
    async def get_all(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> Sequence[ModelType]:
        ...

    @abstractmethod
    async def add(self, entity: ModelType) -> ModelType:
        ...

    @abstractmethod
    async def update(self, entity: ModelType) -> ModelType:
        ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> None:
        ...

    @abstractmethod
    async def count(self, tenant_id: uuid.UUID, **filters: Any) -> int:
        ...


class BaseRepository(AbstractRepository[ModelType]):
    """Concrete async repository implementation using SQLAlchemy 2.0."""

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        **filters: Any,
    ) -> Sequence[ModelType]:
        stmt = select(self._model).where(self._model.tenant_id == tenant_id)

        for field, value in filters.items():
            if value is not None and hasattr(self._model, field):
                stmt = stmt.where(getattr(self._model, field) == value)

        stmt = stmt.offset(skip).limit(limit).order_by(self._model.created_at.desc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def add(self, entity: ModelType) -> ModelType:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(self, entity: ModelType) -> ModelType:
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, id: uuid.UUID) -> None:
        entity = await self.get_by_id(id)
        if entity:
            await self._session.delete(entity)
            await self._session.flush()

    async def count(self, tenant_id: uuid.UUID, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self._model).where(
            self._model.tenant_id == tenant_id
        )
        for field, value in filters.items():
            if value is not None and hasattr(self._model, field):
                stmt = stmt.where(getattr(self._model, field) == value)

        result = await self._session.execute(stmt)
        return result.scalar_one()


# ── Specialized Repositories ──

from app.shared.orm_models import FraudAlertModel, PayrollModel, VerificationReportModel


class FraudAlertRepository(BaseRepository[FraudAlertModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(FraudAlertModel, session)

    async def get_stats(self, tenant_id: uuid.UUID) -> dict[str, int]:
        """Get fraud alert counts by status."""
        stmt = (
            select(FraudAlertModel.status, func.count(FraudAlertModel.id))
            .where(FraudAlertModel.tenant_id == tenant_id)
            .group_by(FraudAlertModel.status)
        )
        result = await self._session.execute(stmt)
        rows = result.all()
        stats = {
            "total": 0,
            "new": 0,
            "under_review": 0,
            "escalated": 0,
            "confirmed": 0,
            "resolved": 0,
        }
        for status, count in rows:
            stats[status] = count
        stats["total"] = sum(stats.values())
        return stats

    async def get_by_document(self, document_id: uuid.UUID) -> Sequence[FraudAlertModel]:
        stmt = (
            select(FraudAlertModel)
            .where(FraudAlertModel.document_id == document_id)
            .order_by(FraudAlertModel.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()


class PayrollRepository(BaseRepository[PayrollModel]):
    def __init__(self, session: AsyncSession):
        super().__init__(PayrollModel, session)

    async def get_by_employee(
        self, tenant_id: uuid.UUID, employee_id: uuid.UUID
    ) -> Sequence[PayrollModel]:
        stmt = (
            select(PayrollModel)
            .where(
                PayrollModel.tenant_id == tenant_id,
                PayrollModel.employee_id == employee_id,
            )
            .order_by(PayrollModel.period_start.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()
