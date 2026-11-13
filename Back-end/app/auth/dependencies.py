# ============================================================
# PaySentinelIQ — Auth Dependencies (FastAPI)
# Reusable dependency injection for auth, RBAC, multi-tenancy
# ============================================================


import uuid
from typing import Any

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.repository import UserRepository
from app.auth.services import AuthService
from app.shared.database import get_db
from app.shared.exceptions import AuthenticationError, AuthorizationError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def _extract_access_token(
    request: Request,
    authorization: str | None,
) -> str:
    """Read the bearer token from the header or the OAuth2 scheme."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

    if not token:
        token = await oauth2_scheme(request)

    if not token:
        raise AuthenticationError("Authentication required")
    return token


async def get_token_payload(
    request: Request,
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """Verify the JWT and resolve its owner against the server database.

    A valid signature is necessary but not sufficient: the subject must still
    exist, be active, and belong to the tenant asserted by the token. Current
    role and tenant values are taken from the database, not from the token.
    """
    token = await _extract_access_token(request, authorization)
    payload = AuthService.verify_access_token(token)

    subject = payload.get("sub")
    token_tenant_id = payload.get("tenant_id")
    if not subject or not token_tenant_id:
        raise AuthenticationError("Invalid token")

    try:
        user_id = uuid.UUID(str(subject))
        tenant_id = uuid.UUID(str(token_tenant_id))
    except (TypeError, ValueError, AttributeError):
        raise AuthenticationError("Invalid token") from None

    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("Authentication required")
    if user.tenant_id != tenant_id:
        raise AuthenticationError("Invalid token")

    payload["sub"] = str(user.id)
    payload["tenant_id"] = str(user.tenant_id)
    payload["role"] = user.role
    return payload


async def get_current_user_id(
    payload: dict[str, Any] = Depends(get_token_payload),  # noqa: B008
) -> str:
    """Extract the verified user ID from the authenticated payload."""
    return str(payload["sub"])


async def get_current_tenant_id(
    payload: dict[str, Any] = Depends(get_token_payload),  # noqa: B008
) -> str:
    """Extract the verified tenant ID from the authenticated payload."""
    return str(payload["tenant_id"])


async def get_current_user_role(
    payload: dict[str, Any] = Depends(get_token_payload),  # noqa: B008
) -> str:
    """Extract the current role from the authenticated payload."""
    return str(payload["role"])


# ── RBAC Dependency Factory ──


def require_roles(*allowed_roles: str) -> Any:
    """Factory that creates a dependency requiring specific roles."""

    async def role_checker(payload: dict[str, Any] = Depends(get_token_payload)) -> dict[str, Any]:  # noqa: B008
        user_role = payload.get("role")
        if user_role not in allowed_roles:
            raise AuthorizationError(
                f"Role '{user_role}' is not authorized. Required: {', '.join(allowed_roles)}"
            )
        return payload

    return role_checker


# Common role dependencies
require_admin = require_roles("super_admin")
require_fraud_analyst = require_roles("super_admin", "fraud_analyst")
require_compliance_officer = require_roles("super_admin", "compliance_analyst")
require_hr_or_payroll = require_roles("super_admin", "hr_manager", "payroll_manager")
require_auditor = require_roles("super_admin", "auditor")
