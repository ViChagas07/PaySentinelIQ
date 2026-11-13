# ============================================================
# PaySentinelIQ — Sentry SDK Initialization
# Initializes Sentry error tracking and performance monitoring.
# Must be called BEFORE the FastAPI app is created.
# ============================================================

import logging

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from app.shared.settings import get_settings

logger = logging.getLogger(__name__)

# Project DSN — used when SENTRY_DSN is not set in the environment.
# Sentry DSNs are safe to commit: they are write-only ingestion keys.
DEFAULT_SENTRY_DSN = (
    "https://4247a607bbd08d21ed443765660be1e0@o4511407142535168"
    ".ingest.us.sentry.io/4512425012625408"
)


def init_sentry() -> None:
    """
    Initialize the Sentry SDK for error tracking and performance monitoring.

    Reads SENTRY_DSN from application settings. If the DSN is not configured
    (e.g., in local development or CI), Sentry is silently skipped.

    Must be called once at application startup, **before** the FastAPI app
    is created, so that the Starlette/FastAPI integrations can patch the
    framework internals correctly.
    """
    settings = get_settings()

    dsn = settings.SENTRY_DSN or DEFAULT_SENTRY_DSN
    if not dsn:
        logger.info("Sentry DSN not configured — skipping Sentry initialization.")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=settings.ENVIRONMENT,
        release=f"{settings.APP_NAME}@{settings.APP_VERSION}",
        # ── Performance Monitoring ──
        traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        # ── Framework Integrations ──
        integrations=[
            StarletteIntegration(
                transaction_style="url",
            ),
            FastApiIntegration(
                transaction_style="url",
            ),
        ],
        # ── Data Privacy ──
        send_default_pii=False,
        # ── Instrument extra logging ──
        enable_tracing=True,
        _experiments={
            # Enable continuous profiling (Python 3.11+)
            "continuous_profiling_auto_start": True,
        },
    )

    logger.info(
        "Sentry initialized — environment=%s  traces_rate=%.2f  profiles_rate=%.2f",
        settings.ENVIRONMENT,
        settings.SENTRY_TRACES_SAMPLE_RATE,
        settings.SENTRY_PROFILES_SAMPLE_RATE,
    )
