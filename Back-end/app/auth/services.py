# ============================================================
# PaySentinelIQ — Auth Service
# JWT token generation, password hashing, MFA, RBAC enforcement
# ============================================================

import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pyotp
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.auth.domain import User
from app.shared.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
)
from app.shared.settings import get_settings

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Authentication and authorization service."""

    # ── Password Hashing ──

    @staticmethod
    def hash_password(password: str) -> str:
        return cast(str, pwd_context.hash(password))

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return cast(bool, pwd_context.verify(plain_password, hashed_password))

    # ── JWT Token Generation ──

    @staticmethod
    def create_access_token(
        user_id: str,
        tenant_id: str,
        role: str,
        extra_claims: dict[str, Any] | None = None,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "role": role,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            "jti": str(uuid.uuid4()),
        }
        if extra_claims:
            payload.update(extra_claims)

        return cast(str, jwt.encode(
            payload,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM,
        ))

    @staticmethod
    def create_refresh_token(user_id: str) -> tuple[str, str]:
        """Returns (raw_token, hashed_token) for secure storage."""
        now = datetime.now(UTC)
        jti = str(uuid.uuid4())
        payload = {
            "sub": user_id,
            "type": "refresh",
            "iat": now,
            "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            "jti": jti,
        }
        raw_token = cast(str, jwt.encode(
            payload,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithm=settings.JWT_ALGORITHM,
        ))
        hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
        return raw_token, hashed_token

    # ── Token Verification ──

    @staticmethod
    def decode_token(token: str) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM],
            )
            return cast(dict[str, Any], payload)
        except JWTError as e:
            if "expired" in str(e).lower():
                raise TokenExpiredError() from e
            raise AuthenticationError("Invalid token") from e

    @staticmethod
    def verify_access_token(token: str) -> dict[str, Any]:
        payload = AuthService.decode_token(token)
        if payload.get("type") != "access":
            raise AuthenticationError("Invalid token type")
        return payload

    # ── MFA ──

    @staticmethod
    def generate_mfa_secret() -> str:
        return cast(str, pyotp.random_base32())

    @staticmethod
    def get_mfa_uri(secret: str, email: str) -> str:
        return cast(str, pyotp.totp.TOTP(secret).provisioning_uri(
            name=email,
            issuer_name=settings.MFA_ISSUER,
        ))

    @staticmethod
    def verify_mfa_code(secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return cast(bool, totp.verify(code))

    # ── RBAC Enforcement ──

    @staticmethod
    def require_role(user: User, *allowed_roles: str) -> None:
        """Raise AuthorizationError if user's role not in allowed_roles."""
        if user.role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{user.role}' is not authorized. Required: {', '.join(allowed_roles)}"
            )

    @staticmethod
    def require_tenant(user: User, tenant_id: str) -> None:
        """Ensure user belongs to the specified tenant."""
        if str(user.tenant_id) != tenant_id:
            raise AuthorizationError("Cross-tenant access denied")
