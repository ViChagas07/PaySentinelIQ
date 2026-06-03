# ============================================================
# PaySentinelIQ — Auth Dependencies (FastAPI)
# Reusable dependency injection for auth, RBAC, multi-tenancy
# ============================================================

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer

from app.auth.services import AuthService
from app.shared.exceptions import AuthenticationError, AuthorizationError, MFARequiredError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


async def get_current_user_id(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract user ID from JWT access token."""
    token = None

    # Try Bearer token from Authorization header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

    # Fall back to OAuth2 scheme
    if not token:
        token = await oauth2_scheme(request)

    if not token:
        raise AuthenticationError("Authentication required")

    payload = AuthService.verify_access_token(token)
    return payload["sub"]


async def get_current_tenant_id(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract tenant ID from JWT access token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

    if not token:
        token = await oauth2_scheme(request)

    if not token:
        raise AuthenticationError("Authentication required")

    payload = AuthService.verify_access_token(token)
    return payload["tenant_id"]


async def get_current_user_role(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> str:
    """Extract user role from JWT access token."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

    if not token:
        token = await oauth2_scheme(request)

    if not token:
        raise AuthenticationError("Authentication required")

    payload = AuthService.verify_access_token(token)
    return payload["role"]


# ── Composite dependency: full token payload ──

async def get_token_payload(
    request: Request,
    authorization: Optional[str] = Header(None),
) -> dict:
    """Extract full JWT payload for comprehensive auth context."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ")

    if not token:
        token = await oauth2_scheme(request)

    if not token:
        raise AuthenticationError("Authentication required")

    return AuthService.verify_access_token(token)


# ── RBAC Dependency Factory ──

def require_roles(*allowed_roles: str):
    """Factory that creates a dependency requiring specific roles."""

    async def role_checker(payload: dict = Depends(get_token_payload)) -> dict:
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
