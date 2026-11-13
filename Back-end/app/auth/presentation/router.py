# ============================================================
# PaySentinelIQ — Auth Router (FastAPI)
# Login, register, MFA, token refresh, logout, Google OIDC
# LGPD-compliant: consent required for all authentication methods
# ============================================================

import logging
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select as sa_select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_token_payload
from app.auth.repository import UserRepository
from app.auth.services import AuthService
from app.observability.correlation import get_correlation
from app.shared.database import get_db
from app.shared.exceptions import AuthenticationError, InvalidCredentialsError, TokenExpiredError
from app.shared.orm_models import (
    ConsentRecordModel,
    RefreshTokenModel,
    TenantModel,
    UserModel,
)
from app.shared.settings import get_settings

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)


# ── Request/Response Schemas ──


class LoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    email: EmailStr
    password: str = Field(min_length=8)
    terms_version: str | None = Field(default=None, min_length=1, max_length=20)
    privacy_version: str | None = Field(default=None, min_length=1, max_length=20)
    consent_given: bool = Field(default=False)


class MFAVerifyRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    session_token: str
    code: str = Field(pattern=r"^\d{6}$")


class TokenRefreshRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    email: str
    full_name: str
    role: str
    tenant_id: str
    mfa_enabled: bool
    avatar_url: str | None = None


class TokenResponse(BaseModel):
    model_config = ConfigDict(strict=True)
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_mfa: bool = False
    mfa_session_token: str | None = None
    user: UserResponse | None = None


class GoogleLoginRequest(BaseModel):
    model_config = ConfigDict(strict=True)
    credential: str | None = Field(default=None, min_length=1)
    access_token: str | None = Field(default=None, min_length=1)
    terms_version: str | None = Field(default=None, min_length=1, max_length=20)
    privacy_version: str | None = Field(default=None, min_length=1, max_length=20)
    consent_given: bool = Field(default=False)


# ── Token Issuance Helpers ──


def _user_response(user: UserModel) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        tenant_id=str(user.tenant_id),
        mfa_enabled=bool(user.mfa_enabled),
        avatar_url=user.avatar_url,
    )


async def _issue_auth_tokens(
    db: AsyncSession,
    user: UserModel,
) -> tuple[str, str]:
    """Issue an access token and persist the hashed refresh token."""
    now = datetime.now(dt_timezone.utc)
    access_token = AuthService.create_access_token(
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role,
    )
    refresh_token_raw, refresh_token_hash = AuthService.create_refresh_token(
        str(user.id)
    )
    db.add(
        RefreshTokenModel(
            id=uuid.uuid4(),
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False,
        )
    )
    user.last_login = now
    await db.commit()
    await db.refresh(user)
    return access_token, refresh_token_raw


# ── Endpoints ──


@router.post("/google")
async def google_login(
    body: GoogleLoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Google OIDC (Sign In With Google) login.

    Accepts either:
      - ``credential`` — a Google ID token JWT (legacy One Tap flow), OR
      - ``access_token`` — a Google OAuth 2.0 access token (GIS popup flow).

    Verifies the token, finds-or-creates the user, records LGPD consent,
    and returns a PaySentinelIQ JWT access token.

    Requires explicit consent to Terms of Service and Privacy Policy
    (LGPD Article 7 compliance).
    """
    # ── LGPD Consent Check ──
    if not body.consent_given:
        raise AuthenticationError(
            "Consent to Terms of Service and Privacy Policy is required (LGPD Article 7). "
            "Please accept the terms before signing in."
        )

    # ── 1. Verify the Google token ──────────────────────────────
    if body.credential:
        # ID token (JWT) path — used by the legacy One Tap flow
        try:
            google_user = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
                body.credential,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
            )
        except ValueError as exc:
            logger.warning(
                "event=google_credential_verification_failed "
                "correlation_id=%s error_type=%s",
                get_correlation().request_id,
                type(exc).__name__,
            )
            raise AuthenticationError("Invalid Google credential") from None
    elif body.access_token:
        # Access token path — used by the modern GIS popup flow
        import httpx
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {body.access_token}"},
                )
            if resp.status_code != 200:
                raise AuthenticationError("Invalid Google access token")
            google_user = resp.json()
        except httpx.RequestError as exc:
            logger.warning(
                "event=google_userinfo_request_failed correlation_id=%s "
                "error_type=%s",
                get_correlation().request_id,
                type(exc).__name__,
            )
            raise AuthenticationError("Google userinfo request failed") from None
    else:
        raise AuthenticationError(
            "Either 'credential' or 'access_token' is required."
        )

    email: str = google_user["email"]
    name: str = google_user.get("name", email.split("@")[0])
    picture: str | None = google_user.get("picture")
    google_sub: str = google_user["sub"]

    # 2. Find or create user
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if user is None:
        # Busca o tenant padrão pelo slug
        tenant_result = await db.execute(
            sa_select(TenantModel).where(TenantModel.slug == "default")
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=500, detail="Default tenant not found")

        user = await repo.create(
            email=email,
            full_name=name,
            google_id=google_sub,
            tenant_id=tenant.id,
            avatar_url=picture,
        )
    else:
        # Update google_id, full_name, and avatar if user already exists
        if not user.google_id:
            user.google_id = google_sub
        if not user.avatar_url and picture:
            user.avatar_url = picture
        user.full_name = name
        await repo.update(user)

    # 3. Record consent (LGPD compliance)
    tv = body.terms_version if body.terms_version else settings.TERMS_VERSION
    pv = body.privacy_version if body.privacy_version else settings.PRIVACY_VERSION

    # Check if identical consent already exists (idempotent)
    existing_consent = await db.execute(
        sa_select(ConsentRecordModel).where(
            ConsentRecordModel.user_id == user.id,
            ConsentRecordModel.consent_type == "terms_of_service",
            ConsentRecordModel.terms_version == tv,
            ConsentRecordModel.privacy_version == pv,
        )
    )
    if not existing_consent.scalar_one_or_none():
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )
        ua = request.headers.get("User-Agent", "")[:500]
        consent_record = ConsentRecordModel(
            id=uuid.uuid4(),
            user_id=user.id,
            tenant_id=user.tenant_id,
            consent_type="terms_of_service",
            terms_version=tv,
            privacy_version=pv,
            accepted_at=datetime.now(dt_timezone.utc),
            ip_address=ip,
            user_agent=ua,
            method="oauth",
        )
        db.add(consent_record)

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # 4. Commit consent + persist refresh token + update last_login
    access_token, refresh_token_raw = await _issue_auth_tokens(db, user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_raw,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": str(user.id),                    # UUID real do banco
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "tenant_id": str(user.tenant_id),
            "avatar_url": user.avatar_url,
            "mfa_enabled": user.mfa_enabled,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


# ═══════════════════════════════════════════════════════════════
# GOOGLE OAUTH2 — Authorization Code Flow (Traditional Redirect)
# ═══════════════════════════════════════════════════════════════


class GoogleCallbackRequest(BaseModel):
    """Query params from Google OAuth2 redirect."""
    model_config = ConfigDict(strict=False, extra="allow")
    code: str | None = None
    state: str | None = None
    error: str | None = None
    error_description: str | None = None


@router.get("/google/callback")
async def google_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
) -> RedirectResponse:
    """
    Google OAuth2 Authorization Code callback.
    
    Flow:
    1. Frontend redirects user to Google OAuth consent screen
    2. User authorizes → Google redirects to this endpoint with `code`
    3. Exchange `code` for access_token + id_token
    4. Verify id_token, find/create user, record LGPD consent
    5. Issue PaySentinelIQ JWT + refresh token
    6. Redirect to frontend dashboard with tokens in query params (or set cookies)
    """
    # Handle OAuth errors from Google
    if error:
        logger.warning(
            "event=google_oauth_callback_error correlation_id=%s",
            get_correlation().request_id,
        )
        frontend_url = settings.APP_BASE_URL.rstrip("/")
        error_msg = error_description or error
        return RedirectResponse(
            url=f"{frontend_url}/auth/login?error={error_msg}",
            status_code=302,
        )

    if not code:
        logger.warning("Google callback missing authorization code")
        frontend_url = settings.APP_BASE_URL.rstrip("/")
        return RedirectResponse(
            url=f"{frontend_url}/auth/login?error=missing_authorization_code",
            status_code=302,
        )

    # ── 1. Exchange authorization code for tokens ──────────────────
    import httpx
    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    
    try:
        async with httpx.AsyncClient() as client:
            token_resp = await client.post(
                token_url,
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET.get_secret_value()
                        if settings.GOOGLE_CLIENT_SECRET else "",
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if token_resp.status_code != 200:
            logger.error(
                "event=google_token_exchange_failed correlation_id=%s "
                "status_code=%s error_type=http_status",
                get_correlation().request_id,
                token_resp.status_code,
            )
            raise AuthenticationError("Failed to exchange authorization code for tokens")
        
        token_data = token_resp.json()
        id_token_jwt = token_data.get("id_token")
        access_token = token_data.get("access_token")
        
        if not id_token_jwt:
            raise AuthenticationError("No ID token in Google response")
            
    except httpx.RequestError as exc:
        logger.warning(
            "event=google_token_exchange_request_failed correlation_id=%s "
            "error_type=%s",
            get_correlation().request_id,
            type(exc).__name__,
        )
        raise AuthenticationError("Google token exchange failed") from None

    # ── 2. Verify ID token ─────────────────────────────────────────
    try:
        google_user = id_token.verify_oauth2_token(  # type: ignore[no-untyped-call]
            id_token_jwt,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        logger.warning(
            "event=google_id_token_verification_failed correlation_id=%s "
            "error_type=%s",
            get_correlation().request_id,
            type(exc).__name__,
        )
        raise AuthenticationError("Invalid Google ID token") from None

    email: str = google_user["email"]
    name: str = google_user.get("name", email.split("@")[0])
    picture: str | None = google_user.get("picture")
    google_sub: str = google_user["sub"]

    # ── 3. Find or create user ─────────────────────────────────────
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if user is None:
        tenant_result = await db.execute(
            sa_select(TenantModel).where(TenantModel.slug == "default")
        )
        tenant = tenant_result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=500, detail="Default tenant not found")

        user = await repo.create(
            email=email,
            full_name=name,
            google_id=google_sub,
            tenant_id=tenant.id,
            avatar_url=picture,
        )
    else:
        if not user.google_id:
            user.google_id = google_sub
        if not user.avatar_url and picture:
            user.avatar_url = picture
        user.full_name = name
        await repo.update(user)

    # ── 4. Record consent (LGPD compliance) ────────────────────────
    tv = settings.TERMS_VERSION
    pv = settings.PRIVACY_VERSION

    existing_consent = await db.execute(
        sa_select(ConsentRecordModel).where(
            ConsentRecordModel.user_id == user.id,
            ConsentRecordModel.consent_type == "terms_of_service",
            ConsentRecordModel.terms_version == tv,
            ConsentRecordModel.privacy_version == pv,
        )
    )
    if not existing_consent.scalar_one_or_none():
        ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or (
            request.client.host if request.client else None
        )
        ua = request.headers.get("User-Agent", "")[:500]
        consent_record = ConsentRecordModel(
            id=uuid.uuid4(),
            user_id=user.id,
            tenant_id=user.tenant_id,
            consent_type="terms_of_service",
            terms_version=tv,
            privacy_version=pv,
            accepted_at=datetime.now(dt_timezone.utc),
            ip_address=ip,
            user_agent=ua,
            method="oauth",
        )
        db.add(consent_record)

    if not user.is_active:
        raise AuthenticationError("Account is inactive")

    # ── 5. Commit consent + persist refresh token + update last_login ──
    access_token, refresh_token_raw = await _issue_auth_tokens(db, user)

    # ── 6. Redirect to frontend with tokens ────────────────────────
    # Option A: Query params (simple, but tokens in URL history)
    # Option B: Set secure HttpOnly cookies (better security)
    # Option C: PostMessage to opener (requires popup)
    # Using Option A for simplicity; frontend extracts tokens from URL
    frontend_url = settings.APP_BASE_URL.rstrip("/")
    params = urlencode({
        "access_token": access_token,
        "refresh_token": refresh_token_raw,
        "token_type": "bearer",
        "expires_in": str(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
    })
    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?{params}",
        status_code=302,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate a user with server-side credential verification.

    If MFA is enabled, returns a short-lived MFA session token instead of
    full access/refresh tokens. LGPD consent is still required.
    """
    # ── LGPD Consent Check ──
    if not body.consent_given:
        raise HTTPException(
            status_code=403,
            detail="Consent to Terms of Service and Privacy Policy is required (LGPD Article 7).",
        )

    repo = UserRepository(db)
    user = await repo.get_by_email(str(body.email))

    password_ok = False
    if user is not None and user.hashed_password:
        try:
            password_ok = AuthService.verify_password(
                body.password,
                user.hashed_password,
            )
        except Exception:
            password_ok = False

    if user is None or not user.is_active or not password_ok:
        raise InvalidCredentialsError()

    if user.mfa_enabled:
        if not user.mfa_secret:
            raise AuthenticationError("MFA is not configured for this account")
        return TokenResponse(
            access_token="",
            refresh_token="",
            expires_in=settings.MFA_SESSION_EXPIRE_MINUTES * 60,
            requires_mfa=True,
            mfa_session_token=AuthService.create_mfa_session_token(
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                role=user.role,
            ),
        )

    access_token, refresh_token_raw = await _issue_auth_tokens(db, user)

    await _publish_user_action(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        "login",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        requires_mfa=False,
        user=_user_response(user),
    )


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/mfa/verify", response_model=TokenResponse)
async def verify_mfa(
    body: MFAVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Verify a short-lived MFA session token and a TOTP code.
    """
    try:
        payload = AuthService.verify_mfa_session_token(body.session_token)
        user_id = uuid.UUID(str(payload["sub"]))
        user = await UserRepository(db).get_by_id(user_id)
        if (
            user is None
            or not user.is_active
            or not user.mfa_enabled
            or not user.mfa_secret
        ):
            raise InvalidCredentialsError()
        if str(user.tenant_id) != str(payload.get("tenant_id")):
            raise InvalidCredentialsError()
        if not AuthService.verify_mfa_code(user.mfa_secret, body.code):
            raise InvalidCredentialsError()
    except (AuthenticationError, InvalidCredentialsError):
        raise HTTPException(
            status_code=401,
            detail="Invalid MFA session or code",
        ) from None
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid MFA session or code",
        ) from None

    access_token, refresh_token_raw = await _issue_auth_tokens(db, user)

    await _publish_user_action(
        {"sub": str(user.id), "tenant_id": str(user.tenant_id)},
        "login",
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Rotate a stored refresh token and issue a new access/refresh pair.
    """
    try:
        payload = AuthService.decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidCredentialsError()

        token_hash = AuthService.hash_refresh_token(body.refresh_token)
        result = await db.execute(
            sa_select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == token_hash,
                RefreshTokenModel.is_revoked.is_(False),
            )
        )
        stored = result.scalar_one_or_none()
        if stored is None:
            raise InvalidCredentialsError()

        now = datetime.now(dt_timezone.utc)
        expires_at = stored.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=dt_timezone.utc)
        if expires_at <= now:
            raise InvalidCredentialsError()

        user = await UserRepository(db).get_by_id(stored.user_id)
        if user is None or not user.is_active:
            raise InvalidCredentialsError()

        stored.is_revoked = True
        new_access, new_refresh_raw = await _issue_auth_tokens(db, user)

        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh_raw,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=_user_response(user),
        )
    except TokenExpiredError:
        raise HTTPException(status_code=401, detail="Refresh token expired") from None
    except (AuthenticationError, InvalidCredentialsError):
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token") from None


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    payload: dict[str, Any] = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Return the currently authenticated user's real server-side profile.
    """
    user = await UserRepository(db).get_by_id(uuid.UUID(str(payload["sub"])))
    if user is None or not user.is_active:
        raise AuthenticationError("Authentication required")
    return _user_response(user)


@router.post("/logout")
async def logout(
    payload: dict[str, Any] = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Logout: revoke all refresh tokens for this user.

    Access tokens remain stateless and expire naturally.
    """
    user_id = uuid.UUID(str(payload["sub"]))
    result = await db.execute(
        sa_select(RefreshTokenModel).where(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.is_revoked.is_(False),
        )
    )
    for token in result.scalars().all():
        token.is_revoked = True
    await db.commit()

    await _publish_user_action(payload, "logout")
    return {"message": "Logged out successfully"}


# ═══════════════════════════════════════════════════════════════
# EVENT PUBLISHING (user.action — feeds the activity history)
# ═══════════════════════════════════════════════════════════════


async def _publish_user_action(
    payload: dict[str, Any],
    action: str,
    *,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Publish a `user.action` event to the activity history (non-fatal)."""
    try:
        from app.messaging.domain.envelope import new_event
        from app.messaging.domain.event_types import EventType
        from app.messaging.infrastructure.factory import get_event_publisher

        event = new_event(
            EventType.USER_ACTION.value,
            payload={
                "action": action,
                "ip_address": ip_address,
                "user_agent": user_agent,
            },
            user_id=payload.get("sub"),
            tenant_id=payload.get("tenant_id"),
        )
        await get_event_publisher().publish(event)
    except Exception as exc:  # pragma: no cover - audit of auth must never fail
        logger.warning(
            "event=user_action_publish_failed correlation_id=%s error_type=%s",
            get_correlation().request_id,
            type(exc).__name__,
        )
