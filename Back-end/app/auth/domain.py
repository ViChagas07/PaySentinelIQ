# ============================================================
# PaySentinelIQ — Auth Domain Entities & Value Objects
# ============================================================

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

from app.shared.domain_primitives import UserRole
from app.shared.exceptions import ValidationError


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
    mfa_secret: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def verify_password(self, password: str, hasher) -> bool:
        return hasher.verify(password, self.hashed_password)

    def enable_mfa(self, secret: str) -> None:
        self.mfa_secret = secret
        self.mfa_enabled = True
        self.updated_at = datetime.now(timezone.utc)

    def record_login(self) -> None:
        self.last_login = datetime.now(timezone.utc)

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class RefreshToken:
    """Refresh token entity for JWT rotation."""

    id: uuid.UUID
    user_id: uuid.UUID
    token_hash: str
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

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
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at
