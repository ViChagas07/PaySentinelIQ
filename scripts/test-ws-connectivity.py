#!/usr/bin/env python3
"""
PaySentinelIQ — WebSocket Connectivity Test Script

Usage:
    # Quick test (no auth — should receive 4001):
    python scripts/test-ws-connectivity.py

    # Test with a JWT token:
    export WS_TOKEN=<your-jwt>
    python scripts/test-ws-connectivity.py --token $WS_TOKEN

    # Test with custom URL:
    python scripts/test-ws-connectivity.py --url wss://paysentineliq-production.up.railway.app/ws/notifications

    # Verbose output:
    python scripts/test-ws-connectivity.py -v
"""

import argparse
import asyncio
import json
import os
import sys
import time

# Use the websockets library (install with: pip install websockets)
try:
    import websockets
except ImportError:
    print("❌ Missing dependency: websockets")
    print("   Install with: pip install websockets")
    sys.exit(1)


async def test_connection(url: str, token: str | None, verbose: bool) -> int:
    """
    Test WebSocket connectivity.

    Returns 0 on success, 1 on failure.
    """
    ws_url = f"{url}?token={token}" if token else url
    passed = 0
    failed = 0

    def log(msg: str, ok: bool | None = None) -> None:
        prefix = ""
        if ok is True:
            prefix = "✅"
            nonlocal passed
            passed += 1
        elif ok is False:
            prefix = "❌"
            nonlocal failed
            failed += 1
        else:
            prefix = "  ℹ️"
        print(f"  {prefix} {msg}" if prefix else f"  {msg}")

    # ── Test 1: Connection handshake ──────────────────────────
    print("\n" + "=" * 60)
    print("📡 WebSocket Connectivity Test")
    print("=" * 60)
    print(f"\nURL: {ws_url[:80]}{'...' if len(ws_url) > 80 else ''}")
    if verbose:
        print(f"Token present: {'✅' if token else '❌'}")

    try:
        print("\n--- Test 1: Connection Handshake ---")
        async with websockets.connect(ws_url, ping_interval=None, close_timeout=5) as ws:
            log(f"Connected to {url}", ok=True)

            # ── Test 2: Connected message ─────────────────────
            print("\n--- Test 2: Connected Message ---")
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
                data = json.loads(msg)
                if data.get("type") == "connected":
                    log(f"Received connected message: channel={data.get('channel')}", ok=True)
                    if verbose:
                        print(f"  Full message: {json.dumps(data, indent=2)}")
                else:
                    log(f"Unexpected message type: {data.get('type')}", ok=False)
            except asyncio.TimeoutError:
                log("Timeout waiting for connected message", ok=False)

            # ── Test 3: Ping/Pong ──────────────────────────────
            print("\n--- Test 3: Ping/Pong Heartbeat ---")
            try:
                await ws.send("ping")
                pong = await asyncio.wait_for(ws.recv(), timeout=5)
                pong_data = json.loads(pong)
                if pong_data.get("type") == "pong":
                    log("Ping → Pong roundtrip successful", ok=True)
                else:
                    log(f"Expected pong, got: {pong_data.get('type')}", ok=False)
            except asyncio.TimeoutError:
                log("Timeout waiting for pong response", ok=False)

            # ── Test 4: Connection stability ──────────────────
            print("\n--- Test 4: Connection Stability (3s) ---")
            try:
                await asyncio.wait_for(
                    asyncio.sleep(3),
                    timeout=10,
                )
                log("Connection stable for 3 seconds", ok=True)
            except asyncio.TimeoutError:
                log("Connection dropped during stability test", ok=False)

            # ── Test 5: Graceful close ─────────────────────────
            print("\n--- Test 5: Graceful Close ---")
            await ws.close(code=1000, reason="Test complete")
            log("Connection closed gracefully", ok=True)

    except websockets.exceptions.InvalidStatusCode as e:
        if e.status_code == 401 or e.status_code == 400:
            log(f"Expected auth failure: HTTP {e.status_code}", ok=not token)
            if token:
                log(f"Auth failed despite token being present — check token validity", ok=False)
        else:
            log(f"Unexpected HTTP status: {e.status_code}", ok=False)
            if verbose:
                print(f"  Error details: {e}")
    except websockets.exceptions.ConnectionClosed as e:
        if e.code == 4001:
            log(f"Connection rejected with code 4001 (auth required)", ok=not token)
            if token:
                log(f"Auth failed despite token being present — check token validity", ok=False)
        else:
            log(f"Connection closed unexpectedly: code={e.code} reason={e.reason}", ok=False)
    except (OSError, websockets.exceptions.WebSocketException) as e:
        log(f"Connection error: {e}", ok=False)
        if verbose:
            print(f"  Error details: {type(e).__name__}: {e}")

    # ── Summary ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PaySentinelIQ WebSocket Connectivity Test",
    )
    parser.add_argument(
        "--url",
        default="wss://paysentineliq-production.up.railway.app/ws/notifications",
        help="WebSocket URL to test (default: production)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="JWT access token for authenticated tests (default: $WS_TOKEN)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output with full message details",
    )
    args = parser.parse_args()

    token = args.token or os.environ.get("WS_TOKEN")
    url = args.url

    if not token:
        print("\n⚠️  No token provided. Testing WITHOUT authentication.")
        print("   Expected: Connection rejected with code 4001.")
        print("   To test with auth: --token <jwt> or export WS_TOKEN=<jwt>\n")

    result = asyncio.run(test_connection(url, token, args.verbose))
    sys.exit(result)


if __name__ == "__main__":
    main()
