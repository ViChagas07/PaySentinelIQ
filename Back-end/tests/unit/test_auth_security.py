# ============================================================
# PaySentinelIQ — Authentication security regression tests
# ============================================================

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pyotp
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from jose import jwt
from pydantic import SecretStr
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.auth.services import AuthService
from app.main import create_app
from app.shared.database import get_db
from app.shared.orm_models import (
    DocumentModel,
    FraudAlertModel,
    RefreshTokenModel,
    TenantModel,
    UserModel,
)
from app.shared.settings import (
    Settings,
    get_settings,
    validate_production_auth_settings,
)


class _NoOpInstrumentator:
    def instrument(self, app):
        return self

    def expose(self, app, **kwargs):
        return self


async def _allow_rate_limit(self, **kwargs):
    return {"limit": 1000, "remaining": 1000, "reset": 0}


@pytest_asyncio.fixture(scope="module")
async def auth_app(test_engine):
    with patch(
        "app.main.Instrumentator",
        new=lambda *args, **kwargs: _NoOpInstrumentator(),
    ):
        app = create_app()

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    with patch("app.shared.rate_limiter.RateLimiter.check", new=_allow_rate_limit):
        yield app
    app.dependency_overrides.clear()


async def _seed_user(
    db_session,
    *,
    email: str,
    password: str,
    full_name: str = "Real User",
    role: str = "fraud_analyst",
    is_active: bool = True,
    mfa_enabled: bool = False,
    mfa_secret: str | None = None,
) -> tuple[uuid.UUID, uuid.UUID]:
    tenant_id = uuid.uuid4()
    user_id = uuid.uuid4()
    db_session.add(
        TenantModel(
            id=tenant_id,
            name="Auth Tenant",
            slug=f"auth-{tenant_id}",
            plan="starter",
            is_active=True,
        )
    )
    db_session.add(
        UserModel(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            hashed_password=AuthService.hash_password(password),
            role=role,
            is_active=is_active,
            mfa_enabled=mfa_enabled,
            mfa_secret=mfa_secret,
        )
    )
    await db_session.commit()
    return tenant_id, user_id


def _login_payload(email: str, password: str) -> dict[str, object]:
    return {
        "email": email,
        "password": password,
        "consent_given": True,
        "terms_version": "1.0.0",
        "privacy_version": "1.0.0",
    }


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _count(db_session, model) -> int:
    return (
        await db_session.execute(select(func.count()).select_from(model))
    ).scalar_one()


def _token_payload(
    user_id,
    tenant_id,
    *,
    token_type: str | None = "access",
    expires_delta: timedelta = timedelta(minutes=5),
) -> dict:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "role": "fraud_analyst",
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if token_type is not None:
        payload["type"] = token_type
    return payload


def _sign(payload: dict, *, secret: str | None = None) -> str:
    settings = get_settings()
    return jwt.encode(
        payload,
        secret or settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )


async def _insert_refresh_row(db_session, user_id, token: str) -> None:
    db_session.add(
        RefreshTokenModel(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=AuthService.hash_refresh_token(token),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            is_revoked=False,
        )
    )
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "path", "kwargs"),
    [
        (
            "POST",
            "/api/documents/analyze",
            {
                "files": {
                    "file": ("boleto.pdf", b"%PDF-1.4 real bytes", "application/pdf")
                },
                "data": {"document_type": "boleto"},
            },
        ),
        (
            "POST",
            "/api/analysis/save",
            {
                "json": {
                    "document_type": "BOLETO",
                    "file_name": "x.pdf",
                    "file_size": 1,
                    "risk_level": "LOW",
                    "risk_score": 1,
                    "status": "completed",
                }
            },
        ),
        ("GET", "/api/analysis/history", {}),
        ("GET", "/api/fraud-alerts", {}),
        ("GET", "/api/breach-notifications", {}),
        ("GET", "/api/account/status", {}),
        ("GET", "/api/auth/me", {}),
    ],
)
async def test_sensitive_routes_require_authentication(
    auth_app,
    method,
    path,
    kwargs,
):
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        response = await client.request(method, path, **kwargs)

    assert response.status_code == 401
    body = response.json()
    assert body["error"] == "AUTHENTICATION_ERROR"
    assert "Authentication required" in body["message"]
    assert "Traceback" not in response.text
    assert "SQL" not in response.text


@pytest.mark.asyncio
async def test_health_remains_public(auth_app):
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(auth_app, db_session):
    _, user_id = await _seed_user(
        db_session,
        email="wrong-password@example.com",
        password="correct-password",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json=_login_payload("wrong-password@example.com", "wrong-password"),
        )

    assert response.status_code == 401
    assert "access_token" not in response.json()

    db_session.expire_all()
    tokens = (
        await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        )
    ).scalars().all()
    assert tokens == []


@pytest.mark.asyncio
async def test_login_rejects_unknown_email(auth_app):
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json=_login_payload("unknown@example.com", "correct-password"),
        )

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_login_rejects_inactive_user(auth_app, db_session):
    _, user_id = await _seed_user(
        db_session,
        email="inactive@example.com",
        password="correct-password",
        is_active=False,
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json=_login_payload("inactive@example.com", "correct-password"),
        )

    assert response.status_code == 401

    db_session.expire_all()
    tokens = (
        await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        )
    ).scalars().all()
    assert tokens == []


@pytest.mark.asyncio
async def test_login_issues_real_tokens_and_me_returns_identity(
    auth_app,
    db_session,
):
    tenant_id, user_id = await _seed_user(
        db_session,
        email="real@example.com",
        password="correct-password",
        full_name="Real User",
        role="fraud_analyst",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("real@example.com", "correct-password"),
        )
        assert login.status_code == 200
        tokens = login.json()
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["user"]["id"] == str(user_id)
        assert tokens["user"]["email"] == "real@example.com"
        assert tokens["user"]["tenant_id"] == str(tenant_id)

        payload = AuthService.verify_access_token(tokens["access_token"])
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)
        assert payload["role"] == "fraud_analyst"

        me = await client.get(
            "/api/auth/me",
            headers=_bearer(tokens["access_token"]),
        )
        assert me.status_code == 200
        body = me.json()
        assert body["id"] == str(user_id)
        assert body["email"] == "real@example.com"
        assert body["full_name"] == "Real User"
        assert body["role"] == "fraud_analyst"
        assert body["tenant_id"] == str(tenant_id)

    db_session.expire_all()
    refresh_hash = AuthService.hash_refresh_token(tokens["refresh_token"])
    stored = (
        await db_session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == refresh_hash
            )
        )
    ).scalar_one_or_none()
    assert stored is not None
    assert stored.user_id == user_id
    assert stored.is_revoked is False


@pytest.mark.asyncio
async def test_signed_token_for_unknown_user_is_rejected(auth_app):
    token = AuthService.create_access_token(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="fraud_analyst",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        me = await client.get("/api/auth/me", headers=_bearer(token))
        alerts = await client.get("/api/fraud-alerts", headers=_bearer(token))

    assert me.status_code == 401
    assert alerts.status_code == 401


@pytest.mark.asyncio
async def test_mfa_session_token_cannot_be_used_as_access_token(
    auth_app,
    db_session,
    monkeypatch,
):
    secret = AuthService.generate_mfa_secret()
    await _seed_user(
        db_session,
        email="mfa-purpose@example.com",
        password="correct-password",
        mfa_enabled=True,
        mfa_secret=secret,
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("mfa-purpose@example.com", "correct-password"),
        )
        assert login.status_code == 200
        body = login.json()
        mfa_token = body["mfa_session_token"]
        assert body["access_token"] == ""
        assert body["refresh_token"] == ""
        assert mfa_token

        me = await client.get("/api/auth/me", headers=_bearer(mfa_token))
        assert me.status_code == 401

        db_session.expire_all()
        before_documents = await _count(db_session, DocumentModel)
        before_alerts = await _count(db_session, FraudAlertModel)

        pipeline_calls: list[bool] = []
        storage_calls: list[bool] = []

        def record_pipeline(self, ctx):
            pipeline_calls.append(True)

        def record_storage():
            storage_calls.append(True)

        monkeypatch.setattr(
            "app.services.pipeline.canonical_pipeline.CanonicalPipeline.execute",
            record_pipeline,
        )
        monkeypatch.setattr(
            "app.api.documents.router._get_storage_provider",
            record_storage,
        )

        analyze = await client.post(
            "/api/documents/analyze",
            data={"document_type": "boleto"},
            files={
                "file": (
                    "boleto.pdf",
                    b"%PDF-1.4 real bytes",
                    "application/pdf",
                )
            },
            headers=_bearer(mfa_token),
        )
        assert analyze.status_code == 401
        assert pipeline_calls == []
        assert storage_calls == []

        db_session.expire_all()
        assert await _count(db_session, DocumentModel) == before_documents
        assert await _count(db_session, FraudAlertModel) == before_alerts


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(
    auth_app,
    db_session,
):
    _, user_id = await _seed_user(
        db_session,
        email="refresh-as-access@example.com",
        password="correct-password",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload(
                "refresh-as-access@example.com",
                "correct-password",
            ),
        )
        assert login.status_code == 200
        refresh_token = login.json()["refresh_token"]

        db_session.expire_all()
        stored = (
            await db_session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
        ).scalars().all()
        assert len(stored) == 1
        assert stored[0].is_revoked is False

        before = await _count(db_session, RefreshTokenModel)

        me = await client.get(
            "/api/auth/me",
            headers=_bearer(refresh_token),
        )
        alerts = await client.get(
            "/api/fraud-alerts",
            headers=_bearer(refresh_token),
        )

        assert me.status_code == 401
        assert alerts.status_code == 401

        db_session.expire_all()
        assert await _count(db_session, RefreshTokenModel) == before


@pytest.mark.asyncio
async def test_non_refresh_tokens_cannot_act_as_mfa_or_rotate_refresh(
    auth_app,
    db_session,
):
    secret = AuthService.generate_mfa_secret()
    tenant_id, user_id = await _seed_user(
        db_session,
        email="purpose@example.com",
        password="correct-password",
        mfa_enabled=True,
        mfa_secret=secret,
    )
    valid_code = pyotp.TOTP(secret).now()

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("purpose@example.com", "correct-password"),
        )
        assert login.status_code == 200
        mfa_token = login.json()["mfa_session_token"]

        verified = await client.post(
            "/api/auth/mfa/verify",
            json={"session_token": mfa_token, "code": valid_code},
        )
        assert verified.status_code == 200
        access_token = verified.json()["access_token"]

        no_type = _sign(
            _token_payload(user_id, tenant_id, token_type=None)
        )
        unknown_type = _sign(
            _token_payload(user_id, tenant_id, token_type="unknown")
        )

        # Store the hashes of every non-refresh token in the refresh table.
        # A missing purpose check would then let them rotate a real row.
        for token in (access_token, mfa_token, no_type, unknown_type):
            await _insert_refresh_row(db_session, user_id, token)

        before = await _count(db_session, RefreshTokenModel)

        for token in (access_token, no_type, unknown_type):
            response = await client.post(
                "/api/auth/mfa/verify",
                json={"session_token": token, "code": valid_code},
            )
            assert response.status_code == 401

        for token in (access_token, mfa_token, no_type, unknown_type):
            response = await client.post(
                "/api/auth/refresh",
                json={"refresh_token": token},
            )
            assert response.status_code == 401

        db_session.expire_all()
        assert await _count(db_session, RefreshTokenModel) == before
        rows = (
            await db_session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
        ).scalars().all()
        assert all(row.is_revoked is False for row in rows)


@pytest.mark.asyncio
async def test_malformed_invalid_signature_expired_and_wrong_purpose_tokens(
    auth_app,
    db_session,
):
    tenant_id, user_id = await _seed_user(
        db_session,
        email="invalid-token@example.com",
        password="correct-password",
    )

    malformed = "not-a-jwt"
    invalid_signature = _sign(
        _token_payload(user_id, tenant_id),
        secret="definitely-wrong-secret",
    )
    expired = _sign(
        _token_payload(
            user_id,
            tenant_id,
            expires_delta=timedelta(minutes=-1),
        )
    )
    missing_type = _sign(
        _token_payload(user_id, tenant_id, token_type=None)
    )
    unknown_type = _sign(
        _token_payload(user_id, tenant_id, token_type="unknown")
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        for token in (
            malformed,
            invalid_signature,
            expired,
            missing_type,
            unknown_type,
        ):
            me = await client.get("/api/auth/me", headers=_bearer(token))
            alerts = await client.get(
                "/api/fraud-alerts",
                headers=_bearer(token),
            )
            assert me.status_code == 401
            assert alerts.status_code == 401


@pytest.mark.asyncio
async def test_mfa_login_requires_valid_session_and_totp(auth_app, db_session):
    secret = AuthService.generate_mfa_secret()
    tenant_id, user_id = await _seed_user(
        db_session,
        email="mfa@example.com",
        password="correct-password",
        mfa_enabled=True,
        mfa_secret=secret,
    )
    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("mfa@example.com", "correct-password"),
        )
        assert login.status_code == 200
        body = login.json()
        assert body["requires_mfa"] is True
        assert body["access_token"] == ""
        assert body["refresh_token"] == ""
        session_token = body["mfa_session_token"]
        assert session_token

        db_session.expire_all()
        pre_totp_tokens = (
            await db_session.execute(
                select(RefreshTokenModel).where(
                    RefreshTokenModel.user_id == user_id
                )
            )
        ).scalars().all()
        assert pre_totp_tokens == []

        empty_refresh = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": ""},
        )
        assert empty_refresh.status_code == 401

        current_code = pyotp.TOTP(secret).now()
        invalid_code = "000000" if current_code != "000000" else "111111"

        no_session = await client.post(
            "/api/auth/mfa/verify",
            json={"session_token": "not-a-real-session", "code": invalid_code},
        )
        assert no_session.status_code == 401

        bad_code = await client.post(
            "/api/auth/mfa/verify",
            json={"session_token": session_token, "code": invalid_code},
        )
        assert bad_code.status_code == 401

        valid_code = pyotp.TOTP(secret).now()
        verified = await client.post(
            "/api/auth/mfa/verify",
            json={"session_token": session_token, "code": valid_code},
        )
        assert verified.status_code == 200
        tokens = verified.json()
        assert tokens["access_token"]
        assert tokens["refresh_token"]
        assert tokens["user"]["id"] == str(user_id)

        payload = AuthService.verify_access_token(tokens["access_token"])
        assert payload["sub"] == str(user_id)
        assert payload["tenant_id"] == str(tenant_id)

    db_session.expire_all()
    refresh_hash = AuthService.hash_refresh_token(tokens["refresh_token"])
    stored = (
        await db_session.execute(
            select(RefreshTokenModel).where(
                RefreshTokenModel.token_hash == refresh_hash
            )
        )
    ).scalar_one_or_none()
    assert stored is not None
    assert stored.is_revoked is False


@pytest.mark.asyncio
async def test_refresh_rotates_and_rejects_reuse(auth_app, db_session):
    tenant_id, user_id = await _seed_user(
        db_session,
        email="refresh@example.com",
        password="correct-password",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("refresh@example.com", "correct-password"),
        )
        assert login.status_code == 200
        old_refresh = login.json()["refresh_token"]

        first = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert first.status_code == 200
        new_tokens = first.json()
        assert new_tokens["refresh_token"]
        assert new_tokens["refresh_token"] != old_refresh
        assert new_tokens["user"]["id"] == str(user_id)

        refreshed_payload = AuthService.verify_access_token(
            new_tokens["access_token"]
        )
        assert refreshed_payload["sub"] == str(user_id)
        assert refreshed_payload["tenant_id"] == str(tenant_id)

        reuse = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert reuse.status_code == 401

    db_session.expire_all()
    old_hash = AuthService.hash_refresh_token(old_refresh)
    old_stored = (
        await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == old_hash)
        )
    ).scalar_one_or_none()
    assert old_stored is not None
    assert old_stored.is_revoked is True

    new_hash = AuthService.hash_refresh_token(new_tokens["refresh_token"])
    new_stored = (
        await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.token_hash == new_hash)
        )
    ).scalar_one_or_none()
    assert new_stored is not None
    assert new_stored.is_revoked is False


@pytest.mark.asyncio
async def test_logout_revokes_refresh_tokens(auth_app, db_session):
    _, user_id = await _seed_user(
        db_session,
        email="logout@example.com",
        password="correct-password",
    )

    async with AsyncClient(
        transport=ASGITransport(app=auth_app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/auth/login",
            json=_login_payload("logout@example.com", "correct-password"),
        )
        assert login.status_code == 200
        tokens = login.json()

        logout = await client.post(
            "/api/auth/logout",
            headers=_bearer(tokens["access_token"]),
        )
        assert logout.status_code == 200

        refresh = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh.status_code == 401

    db_session.expire_all()
    stored = (
        await db_session.execute(
            select(RefreshTokenModel).where(RefreshTokenModel.user_id == user_id)
        )
    ).scalars().all()
    assert stored
    assert all(token.is_revoked for token in stored)


def test_password_hash_roundtrip():
    hashed = AuthService.hash_password("correct-password")

    assert hashed.startswith("$2")
    assert AuthService.verify_password("correct-password", hashed) is True
    assert AuthService.verify_password("wrong-password", hashed) is False
    assert AuthService.verify_password("correct-password", "not-a-hash") is False


def test_production_requires_strong_jwt_secret():
    with pytest.raises(RuntimeError):
        validate_production_auth_settings(
            Settings(_env_file=None, ENVIRONMENT="production")
        )

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="production",
        JWT_SECRET_KEY=SecretStr("x" * 32),
    )
    validate_production_auth_settings(settings)
    assert settings.ENVIRONMENT == "production"
