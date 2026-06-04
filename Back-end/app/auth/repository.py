# ============================================================
# PaySentinelIQ — User Repository
# Database access for UserModel (login, OIDC, CRUD)
# ============================================================

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.orm_models import UserModel
from app.shared.repository import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """Repository for user persistence and queries."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(UserModel, session)

    async def get_by_email(self, email: str) -> UserModel | None:
        """Find a user by email address."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> UserModel | None:
        """Find a user by Google OIDC subject ID."""
        stmt = select(UserModel).where(UserModel.google_id == google_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        email: str,
        full_name: str,
        google_id: str,
        tenant_id: uuid.UUID | None = None,
        role: str = "fraud_analyst",
    ) -> UserModel:
        """Create a new user (typically from Google OIDC)."""
        user = UserModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id or uuid.uuid4(),
            email=email,
            full_name=full_name,
            hashed_password="",  # OIDC users authenticate via Google
            google_id=google_id,
            role=role,
        )
        return await self.add(user)
