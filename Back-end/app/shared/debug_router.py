# ============================================================
# PaySentinelIQ — Debug Router (Sentry Verification)
# Endpoints to test Sentry error tracking. Only available in
# development and staging environments — NEVER in production.
# ============================================================

import logging
import math
from typing import Any, Literal

import sentry_sdk
from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/debug-sentry/check", tags=["Debug"])
async def sentry_status_check() -> dict[str, Any]:
    """
    Check whether Sentry SDK is initialized and provide its current config.

    Returns the DSN (masked), environment, and whether the client
    is actively capturing events.
    """
    client = sentry_sdk.get_client()
    dsn = sentry_sdk.get_current_scope().client.dsn if client else None

    return {
        "sentry_initialized": client is not None and client.is_active(),
        "environment": str(sentry_sdk.get_current_scope()._scope.get("environment")),  # type: ignore[attr-defined]
        "dsn_masked": str(dsn)[:30] + "..." if dsn else None,
        "sdk_version": sentry_sdk.consts.VERSION,
    }


@router.get("/debug-sentry/trigger-unhandled", tags=["Debug"])
async def trigger_unhandled_exception(
    error_type: str = Query(
        default="zero_division",
        description=(
            "Type of unhandled error: zero_division, value_error, index_error, or key_error"
        ),
    ),
) -> dict[str, Any]:
    """
    ⚠️ TRIGGER an unhandled exception to verify Sentry captures it.

    This endpoint **intentionally** raises an exception that is NOT caught,
    so FastAPI's default exception handler + Sentry integration pick it up.

    After calling, check your Sentry dashboard for a new error event within
    a few seconds (Sentry flushes on shutdown / periodically).
    """
    if error_type == "zero_division":
        result = 1 / 0  # noqa: F841 — intentionally triggers ZeroDivisionError
    elif error_type == "value_error":
        raise ValueError("Sentry debug: deliberate ValueError for testing")
    elif error_type == "index_error":
        _ = [1, 2, 3][99]  # IndexError
    elif error_type == "key_error":
        _ = {}["nonexistent_key"]  # type: ignore[index]  # KeyError
    else:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown error_type '{error_type}'. "
                f"Use: zero_division, value_error, index_error, key_error"
            ),
        )

    return {"message": "This should never be reached."}


@router.get("/debug-sentry/trigger-handled", tags=["Debug"])
async def trigger_handled_exception() -> dict[str, Any]:
    """
    Intentionally raises a handled exception caught by our domain error handler.

    This tests that PSIDomainError exceptions are properly routed and optionally
    reported to Sentry (depending on your `sample_rate` and Sentry config).
    """
    try:
        raise ValueError("Inner error that gets caught")
    except ValueError as exc:
        # Capture the exception manually with extra context
        sentry_sdk.capture_exception(
            exc,
            extras={
                "endpoint": "/debug-sentry/trigger-handled",
                "note": "This was intentionally triggered for Sentry verification",
            },
        )
        return {
            "status": "error_captured",
            "message": "Sentry should have received a handled exception event.",
        }


@router.get("/debug-sentry/capture-message", tags=["Debug"])
async def capture_custom_message(
    message: str = Query(default="Hello from Sentry debug endpoint!"),
    level: str = Query(
        default="info", description="Sentry level: debug, info, warning, error, fatal"
    ),
) -> dict[str, Any]:
    """
    Send a custom message/event to Sentry at the specified severity level.

    Useful to verify that the Sentry transport is working correctly
    without triggering an actual error in the application.
    """
    level_map: dict[str, Literal["debug", "info", "warning", "error", "fatal"]] = {
        "debug": "debug",
        "info": "info",
        "warning": "warning",
        "error": "error",
        "fatal": "fatal",
    }

    sentry_level = level_map.get(level, "info")

    event_id = sentry_sdk.capture_message(
        f"[Sentry Verification] {message}",
        level=sentry_level,
        extras={
            "endpoint": "/debug-sentry/capture-message",
            "custom_message": message,
        },
    )

    logger.info("Sentry capture_message sent — event_id=%s", event_id)

    return {
        "status": "message_sent",
        "event_id": event_id,
        "level": sentry_level,
        "message": message,
    }


@router.get("/debug-sentry/performance", tags=["Debug"])
async def performance_test(
    iterations: int = Query(default=10, ge=1, le=100),
) -> dict[str, Any]:
    """
    Simulate a span of work for Sentry performance monitoring.

    Creates a custom transaction with child spans so you can verify
    Sentry's tracing/profiling is capturing performance data.
    """
    with sentry_sdk.start_transaction(
        op="test",
        name="debug-sentry-performance-test",
    ):
        with sentry_sdk.start_span(op="computation", description="fibonacci_calculation"):
            # Simulate some CPU-bound work
            total = sum(math.sqrt(i) * math.log(i + 1) for i in range(1, iterations * 1000))

        with sentry_sdk.start_span(op="io", description="simulated_db_query"):
            # Simulated I/O wait
            import asyncio

            await asyncio.sleep(0.1)

    return {
        "status": "performance_test_complete",
        "iterations": iterations,
        "computed_checksum": round(total, 2),
        "note": "Check Sentry Performance tab for the transaction.",
    }
