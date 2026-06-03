# ============================================================
# PaySentinelIQ — FastAPI Application Factory
# Creates and configures the FastAPI app with all middleware, routers
# ============================================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.shared.database import engine
from app.shared.exceptions import PSIDomainError
from app.shared.redis_client import close_redis, get_redis
from app.shared.sentry import init_sentry
from app.shared.settings import get_settings

settings = get_settings()

# ── Sentry must be initialized BEFORE FastAPI app is created ──
init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle: startup and shutdown."""
    # Startup
    await get_redis()  # Initialize Redis connection pool

    # Initialize LLM provider health check (non-blocking — fails gracefully)
    try:
        from app.ai_agents.llm_service import get_llm_service
        llm_service = await get_llm_service()
        info = llm_service.get_info()
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "LLM service initialized: provider=%s model=%s healthy=%s",
            info["provider"], info["model"], info["healthy"],
        )
    except Exception as exc:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("LLM service initialization deferred: %s", exc)

    yield
    # Shutdown
    await close_redis()
    await engine.dispose()


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

    # ── Health Check ──
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/health/llm", tags=["Health"])
    async def llm_health_check():
        """Return LLM provider status for monitoring/diagnostics."""
        try:
            from app.ai_agents.llm_service import get_llm_service
            llm_service = await get_llm_service()
            info = llm_service.get_info()
            # Run a fresh health check
            await llm_service.ensure_healthy()
            info["status"] = "healthy"
            return info
        except Exception as exc:
            return {
                "status": "unhealthy",
                "error": str(exc),
                "provider": settings.LLM_PROVIDER,
            }

    # ── Register Routers (imported lazily to avoid circular imports) ──
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
