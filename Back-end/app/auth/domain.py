# ============================================================
# PaySentinelIQ — Auth Domain Entities & Value Objects
# ============================================================

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.shared.domain_primitives import UserRole


@dataclass
class User:
    """User aggregate root."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    email: str
    full_name: str
    hashed_password: str
    role: UserRole
    mfa_enabled: bool = False
    mfa_secret: str | None = None
    is_active: bool = True
    last_login: datetime | None = None
    avatar_url: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def verify_password(self, password: str, hasher) -> bool:
        return hasher.verify(password, self.hashed_password)

    def enable_mfa(self, secret: str) -> None:
        self.mfa_secret = secret
        self.mfa_enabled = True
        self.updated_at = datetime.now(UTC)

    def record_login(self) -> None:
        self.last_login = datetime.now(UTC)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(UTC)


@dataclass
class RefreshToken:
    """Refresh token entity for JWT rotation."""

    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at

    @property
    def is_valid(self) -> bool:
        return not self.is_revoked and not self.is_expired

    def revoke(self) -> None:
        self.is_revoked = True


@dataclass
class MFASession:
    """Pending MFA session before full authentication."""

    id: uuid.UUID
    user_id: uuid.UUID
    temp_token: str
    expires_at: datetime
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expires_at
