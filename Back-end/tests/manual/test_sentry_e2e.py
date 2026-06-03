#!/usr/bin/env python3
# ============================================================
# PaySentinelIQ — Sentry End-to-End Verification Script
#
# Tests that Sentry SDK initializes correctly and can send
# events to the configured Sentry project.
#
# Usage:
#   cd Back-end
#   python tests/manual/test_sentry_e2e.py
#
# Prerequisites:
#   - .env file with SENTRY_DSN configured
#   - sentry-sdk installed (pip install sentry-sdk[fastapi])
# ============================================================

import os
import sys
import time
from pathlib import Path

# Ensure the Back-end directory is on sys.path so we can import app modules
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Set environment to load .env from Back-end/
os.chdir(BACKEND_DIR)


def print_header(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def test_sentry_initialization() -> bool:
    """
    Test 1: Verify that init_sentry() correctly initializes the SDK
    when SENTRY_DSN is configured in .env.
    """
    print_header("TEST 1: Sentry SDK Initialization")

    from app.shared.sentry import init_sentry
    from app.shared.settings import get_settings

    settings = get_settings()
    print(f"  SENTRY_DSN configured : {bool(settings.SENTRY_DSN)}")
    print(f"  ENVIRONMENT           : {settings.ENVIRONMENT}")
    print(f"  APP_NAME              : {settings.APP_NAME}")
    print(f"  APP_VERSION           : {settings.APP_VERSION}")

    if not settings.SENTRY_DSN:
        print("  [FAIL] SENTRY_DSN is not set in .env — cannot proceed.")
        return False

    # Mask DSN for safe logging
    dsn = settings.SENTRY_DSN
    masked = dsn[:35] + "..." if len(dsn) > 35 else dsn
    print(f"  DSN (masked)          : {masked}")

    # Initialize Sentry
    init_sentry()

    import sentry_sdk
    client = sentry_sdk.get_client()
    is_active = client is not None and client.is_active()

    if is_active:
        print("  [PASS] PASS: Sentry SDK initialized and client is ACTIVE.")
        return True
    else:
        print("  [FAIL] FAIL: Sentry client is NOT active after init_sentry().")
        return False


def test_capture_message() -> bool:
    """
    Test 2: Send a test message to Sentry and verify we get an event_id back.
    """
    print_header("TEST 2: Capture Custom Message")

    import sentry_sdk

    event_id = sentry_sdk.capture_message(
        "[PaySentinelIQ E2E Test] Sentry integration verification — "
        "if you see this in the dashboard, Sentry is working correctly.",
        level="info",
        extras={
            "test": "sentry_e2e",
            "timestamp": time.time(),
        },
    )

    if event_id:
        print(f"  [PASS] PASS: Message sent — event_id = {event_id}")
        return True
    else:
        print("  [FAIL] FAIL: capture_message returned None — transport may be disabled.")
        return False


def test_capture_exception() -> bool:
    """
    Test 3: Capture a handled exception and verify it's sent.
    """
    print_header("TEST 3: Capture Handled Exception")

    import sentry_sdk

    try:
        raise ValueError("E2E test: deliberate ValueError for Sentry verification")
    except ValueError as exc:
        event_id = sentry_sdk.capture_exception(
            exc,
            extras={
                "test": "sentry_e2e_exception",
                "timestamp": time.time(),
            },
        )

    if event_id:
        print(f"  [PASS] PASS: Exception captured — event_id = {event_id}")
        return True
    else:
        print("  [FAIL] FAIL: capture_exception returned None.")
        return False


def test_transaction_span() -> bool:
    """
    Test 4: Create a transaction with a child span for performance monitoring.
    """
    print_header("TEST 4: Performance Transaction + Span")

    import sentry_sdk

    with sentry_sdk.start_transaction(
        op="test",
        name="sentry-e2e-transaction-test",
    ) as transaction:
        with sentry_sdk.start_span(op="computation", description="e2e_fibonacci"):
            # Simulate some work
            result = sum(i * i for i in range(1000))

        with sentry_sdk.start_span(op="io", description="e2e_simulated_io"):
            time.sleep(0.05)

    print(f"  Transaction completed : name={transaction.name}")
    print(f"  Computed result       : {result}")
    print("  [PASS] PASS: Transaction and spans created (check Performance tab).")
    return True


def test_flush_and_shutdown() -> bool:
    """
    Test 5: Flush events to Sentry and shut down the SDK cleanly.
    """
    print_header("TEST 5: Flush & Shutdown")

    import sentry_sdk

    # Flush ensures all pending events are sent before we exit
    # timeout=5 means wait up to 5 seconds for events to be delivered
    flushed = sentry_sdk.flush(timeout=5)

    if flushed:
        print("  [PASS] PASS: All events flushed successfully to Sentry.")
    else:
        print("  [WARN] WARNING: Flush did not complete within timeout — some events may be pending.")

    # Shutdown the SDK (disables transport, prevents further events)
    # This also triggers a final flush internally
    client = sentry_sdk.get_client()
    if client:
        client.close(timeout=2)
        print("  [PASS] PASS: Sentry SDK client closed cleanly.")

    return True


def main() -> int:
    print_header("PaySentinelIQ — Sentry E2E Verification")
    print(f"  Back-end directory : {BACKEND_DIR}")
    print(f"  Python version     : {sys.version}")

    results = {}

    # Test 1: Initialization (MUST pass for subsequent tests)
    results["initialization"] = test_sentry_initialization()
    if not results["initialization"]:
        print("\n" + "!" * 60)
        print("  Sentry initialization FAILED — aborting remaining tests.")
        print("  Make sure SENTRY_DSN is set correctly in Back-end/.env")
        print("!" * 60)
        return 1

    # Test 2-4: Core functionality
    results["capture_message"] = test_capture_message()
    results["capture_exception"] = test_capture_exception()
    results["transaction"] = test_transaction_span()

    # Test 5: Cleanup
    results["flush"] = test_flush_and_shutdown()

    # ── Summary ──
    print_header("RESULTS SUMMARY")
    all_passed = True
    for name, passed in results.items():
        status = "[PASS] PASS" if passed else "[FAIL] FAIL"
        if not passed:
            all_passed = False
        print(f"  {status} : {name}")

    print()
    if all_passed:
        print("  *** ALL TESTS PASSED! ***")
        print("  Check your Sentry dashboard (Issues & Performance tabs)")
        print("  within a few seconds to verify the events arrived.")
        return 0
    else:
        print("  [FAIL] SOME TESTS FAILED — check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
