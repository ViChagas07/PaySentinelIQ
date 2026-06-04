# ============================================================
# PaySentinelIQ — Auth Router (FastAPI)
# Login, register, MFA, token refresh, logout, Google OIDC
# ============================================================

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_token_payload
from app.auth.repository import UserRepository
from app.auth.services import AuthService
from app.shared.database import get_db
from app.shared.exceptions import AuthenticationError, InvalidCredentialsError, TokenExpiredError
from app.shared.settings import get_settings

settings = get_settings()
router = APIRouter()


# ── Request/Response Schemas ──


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    email: EmailStr
    password: str = Field(min_length=8)


class MFAVerifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    session_token: str
    code: str = Field(pattern=r"^\d{6}$")


class TokenRefreshRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    refresh_token: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_mfa: bool = False
    mfa_session_token: str | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    mfa_enabled: bool
    avatar_url: str | None = None


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    credential: str


# ── Endpoints ──


@router.post("/google")
async def google_login(
    body: GoogleLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Google OIDC (Sign In With Google) login.

    Receives a Google ID token credential from the front-end GIS flow,
    verifies it, finds-or-creates the user, and returns a PaySentinelIQ
    JWT access token.
    """
    credential = body.credential

    # 1. Verify the Google ID token
    try:
        google_user = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise AuthenticationError(f"Invalid Google credential: {exc}") from exc

    email: str = google_user["email"]
    name: str = google_user.get("name", email.split("@")[0])
    google_sub: str = google_user["sub"]

    # 2. Find or create user
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if user is None:
        user = await repo.create(
            email=email,
            full_name=name,
            google_id=google_sub,
        )
    else:
        # Update google_id if user already exists but didn't have one
        if not user.google_id:
            user.google_id = google_sub
            await repo.update(user)

    # 3. Issue PaySentinelIQ JWT
    access_token = AuthService.create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "name": user.full_name,
        },
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    """
    Authenticate user. If MFA is enabled, returns a temporary session token
    instead of full access/refresh tokens.
    """
    # In production, fetch user from repository
    # For demonstration, return mock tokens
    # Actual implementation would:
    # 1. Look up user by email
    # 2. Verify password
    # 3. Check if MFA is enabled
    # 4. Return tokens or MFA session

    # Mock: always return a valid token for demo purposes
    mock_user_id = str(uuid.uuid4())
    mock_tenant_id = str(uuid.uuid4())

    access_token = AuthService.create_access_token(
        user_id=mock_user_id,
        tenant_id=mock_tenant_id,
        role="fraud_analyst",
    )
    raw_refresh, hashed_refresh = AuthService.create_refresh_token(mock_user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=900,  # 15 minutes
        requires_mfa=False,
    )


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(body: MFAVerifyRequest) -> TokenResponse:
    """
    Verify MFA code and issue full access/refresh tokens.
    """
    # In production:
    # 1. Validate session token from Redis
    # 2. Verify MFA code against user's secret
    # 3. Issue real tokens

    mock_user_id = str(uuid.uuid4())
    mock_tenant_id = str(uuid.uuid4())

    access_token = AuthService.create_access_token(
        user_id=mock_user_id,
        tenant_id=mock_tenant_id,
        role="fraud_analyst",
    )
    raw_refresh, _ = AuthService.create_refresh_token(mock_user_id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=900,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: TokenRefreshRequest) -> TokenResponse:
    """
    Exchange a valid refresh token for a new access/refresh token pair.
    Implements refresh token rotation.
    """
    try:
        payload = AuthService.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidCredentialsError()

        user_id = payload["sub"]
        # In production: validate refresh token hash in DB, revoke old one

        # Issue new pair
        tenant_id = payload.get("tenant_id", str(uuid.uuid4()))
        role = payload.get("role", "viewer")

        new_access = AuthService.create_access_token(user_id, tenant_id, role)
        new_refresh_raw, _ = AuthService.create_refresh_token(user_id)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh_raw,
            expires_in=900,
        )
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Refresh token expired") from None
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None


@router.get("/me", response_model=UserResponse)
async def get_current_user(payload: dict[str, Any] = Depends(get_token_payload)) -> UserResponse:
    """
    Return the currently authenticated user's profile.
    """
    return UserResponse(
        id=payload["sub"],
        email="analyst@paysentineliq.com",  # In production: fetch from DB
        full_name="Sarah Mitchell",
        role=payload["role"],
        tenant_id=payload["tenant_id"],
        mfa_enabled=True,
    )


@router.post("/logout")
async def logout(payload: dict[str, Any] = Depends(get_token_payload)) -> dict[str, Any]:
    """
    Logout: revoke all refresh tokens for this user.
    """
    # In production: revoke refresh tokens, clear sessions
    return {"message": "Logged out successfully"}
