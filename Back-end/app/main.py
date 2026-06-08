# ============================================================
# PaySentinelIQ — FastAPI Application Factory
# Creates and configures the FastAPI app with all middleware, routers.
# Startup is non-blocking — heavy initializations run in the background.
# ============================================================

import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.responses import Response

from app.shared.database import engine
from app.shared.exceptions import PSIDomainError
from app.shared.redis_client import close_redis, get_redis
from app.shared.sentry import init_sentry
from app.shared.settings import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Sentry must be initialized BEFORE FastAPI app is created ──
# This is synchronous and lightweight (skips if no DSN configured)
init_sentry()

# ── Module-level readiness flags (set by background init, read by /health/full) ──
redis_healthy: bool = False


async def _background_init_redis() -> None:
    """Initialize Redis connection pool in the background."""
    global redis_healthy
    try:
        await get_redis()
        redis_healthy = True
        logger.info("Redis connection pool initialized")
    except Exception as exc:
        logger.warning("Redis initialization deferred (non-fatal): %s", exc)


async def _background_init_llm() -> None:
    """Initialize LLM provider in the background."""
    try:
        from app.ai_agents.llm_service import get_llm_service

        llm_service = await get_llm_service()
        info = llm_service.get_info()
        logger.info(
            "LLM service initialized: provider=%s model=%s healthy=%s",
            info["provider"],
            info["model"],
            info["healthy"],
        )
    except Exception as exc:
        logger.warning("LLM service initialization deferred (non-fatal): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifecycle.

    YIELDS IMMEDIATELY so Railway healthchecks pass within 2-5 seconds.
    Heavy initialization (Redis, LLM) runs as background tasks and
    does NOT block the app from accepting requests.
    """
    # ── Schedule background initialization ──
    asyncio.create_task(_background_init_redis())
    asyncio.create_task(_background_init_llm())

    # Yield immediately — app is ready for /health
    yield

    # ── Shutdown ──
    try:
        await close_redis()
    except Exception as exc:
        logger.warning("Redis shutdown error (non-fatal): %s", exc)
    try:
        await engine.dispose()
    except Exception as exc:
        logger.warning("DB engine dispose error (non-fatal): %s", exc)


def create_app() -> FastAPI:
    """Factory function to create and configure the FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="AI-Powered Payroll Verification & Fraud Risk Intelligence Platform",
        docs_url="/api/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/api/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security Headers middleware ──
    @app.middleware("http")
    async def add_security_headers(
        request: Request, call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        return response

    # ── Prometheus Metrics ──
    instrumentator = Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
    )
    instrumentator.instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    # ── Global Exception Handler ──
    @app.exception_handler(PSIDomainError)
    async def domain_error_handler(request: Request, exc: PSIDomainError) -> JSONResponse:
        status_map = {
            "AUTHENTICATION_ERROR": 401,
            "AUTHORIZATION_ERROR": 403,
            "NOT_FOUND": 404,
            "ALREADY_EXISTS": 409,
            "VALIDATION_ERROR": 422,
            "RATE_LIMIT_EXCEEDED": 429,
        }
        status_code = status_map.get(exc.code, 400)
        return JSONResponse(
            status_code=status_code,
            content={
                "error": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # ── Standard web roots ──
    @app.get("/", tags=["Health"])
    async def root() -> dict[str, Any]:
        return {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/robots.txt", tags=["Health"], include_in_schema=False)
    async def robots() -> str:
        return "User-agent: *\nDisallow: /"

    @app.get("/sitemap.xml", tags=["Health"], include_in_schema=False)
    async def sitemap() -> str:
        return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"/>\n'

    # ══════════════════════════════════════════════════════
    # HEALTH CHECK ENDPOINTS
    # ══════════════════════════════════════════════════════

    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, Any]:
        """
        Lightweight health check for Railway / load balancers.

        Returns IMMEDIATELY with HTTP 200.
        Does NOT depend on Redis, DB, LLM, Celery, or any external service.
        Only verifies the FastAPI process is running.
        """
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/health/full", tags=["Health"])
    async def health_check_full() -> dict[str, Any]:
        """
        Deep health check — verifies all backend dependencies.

        Checks: database, Redis, LLM provider.
        Used for monitoring dashboards and debugging.
        NOT used by Railway (Railway uses /health only).
        """
        checks: dict[str, Any] = {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dependencies": {},
        }

        # ── Database check ──
        try:
            from sqlalchemy import text

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["dependencies"]["database"] = {"status": "healthy"}
        except Exception as exc:
            checks["status"] = "degraded"
            checks["dependencies"]["database"] = {"status": "unhealthy", "error": str(exc)}

        # ── Redis check ──
        try:
            client = await get_redis()
            await client.ping()
            checks["dependencies"]["redis"] = {"status": "healthy"}
        except Exception as exc:
            checks["status"] = "degraded"
            checks["dependencies"]["redis"] = {"status": "unhealthy", "error": str(exc)}

        # ── LLM check ──
        try:
            from app.ai_agents.llm_service import get_llm_service

            llm_service = await get_llm_service()
            info = llm_service.get_info()
            checks["dependencies"]["llm"] = {
                "status": "healthy" if info.get("healthy") else "unhealthy",
                "provider": info.get("provider", "unknown"),
                "model": info.get("model", "unknown"),
            }
        except Exception as exc:
            checks["dependencies"]["llm"] = {"status": "unhealthy", "error": str(exc)}

        return checks

    # ── Register Routers ──
    _register_routers(app)

    return app


def _register_routers(app: FastAPI) -> None:
    """Register all module routers with proper prefixes and tags."""

    # Auth
    from app.auth.presentation.router import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])

    # Payroll
    from app.payroll.presentation.router import router as payroll_router
    app.include_router(payroll_router, prefix="/api/payrolls", tags=["Payroll"])

    # Employees
    from app.employees.presentation.router import router as employees_router
    app.include_router(employees_router, prefix="/api/employees", tags=["Employees"])

    # Verification
    from app.verification.presentation.router import router as verification_router
    app.include_router(verification_router, prefix="/api/verifications", tags=["Verification"])

    # Fraud Detection
    from app.fraud_detection.presentation.router import router as fraud_router
    app.include_router(fraud_router, prefix="/api/fraud-alerts", tags=["Fraud Detection"])

    # Compliance
    from app.compliance.presentation.router import router as compliance_router
    app.include_router(compliance_router, prefix="/api/compliance", tags=["Compliance"])

    # Audit Logs
    from app.audit.infrastructure.router import router as audit_router
    app.include_router(audit_router, prefix="/api/audit-logs", tags=["Audit Logs"])

    # Notifications
    from app.notifications.infrastructure.router import router as notification_router
    app.include_router(notification_router, prefix="/api/notifications", tags=["Notifications"])

    # AI Assistant (Chat)
    from app.ai_assistant.presentation.router import router as ai_assistant_router
    app.include_router(ai_assistant_router, prefix="/api/ai-assistant", tags=["AI Assistant"])

    # User Settings / Preferences
    from app.settings_module.presentation.router import router as settings_router
    app.include_router(settings_router, prefix="/api/settings", tags=["Settings"])

    # AI Insights (Dashboard)
    from app.analytics.application.router import router as analytics_router
    app.include_router(analytics_router, prefix="/api", tags=["Analytics"])

    # WebSocket
    from app.websocket.router import router as ws_router
    app.include_router(ws_router, prefix="/ws", tags=["WebSocket"])

    # ── Debug Router (non-production only) ──
    if settings.ENVIRONMENT != "production":
        from app.shared.debug_router import router as debug_router
        app.include_router(debug_router, prefix="/api", tags=["Debug"])
