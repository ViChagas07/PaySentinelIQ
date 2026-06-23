# ============================================================
# PaySentinelIQ — WebSocket Module
# Connection manager, JWT auth, Redis bridge, multi-tenant routing
# ============================================================

import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.services import AuthService
from app.shared.exceptions import AuthenticationError
from app.shared.redis_client import RedisPubSub
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ═══════════════════════════════════════════════════════════════
# CONNECTION MANAGER (Multi-Tenant Aware)
# ═══════════════════════════════════════════════════════════════


class ConnectionManager:
    """
    Manages WebSocket connections across channels, tenants, and users.

    Three-level hierarchy::

        channel
        └── tenant_id
            └── user_id
                └── set[WebSocket]   (multiple tabs / windows)

    This guarantees:
    - Tenant A never receives Tenant B's data.
    - User X never receives User Y's notifications.
    - Multiple browser tabs for the same user all receive updates.

    Cross‑process broadcasts are relayed via Redis Pub/Sub so that
    Celery workers (or other API workers) can push messages to the
    correct process.
    """

    def __init__(self) -> None:
        # channel -> tenant_id -> user_id -> set[WebSocket]
        self._connections: dict[str, dict[str, dict[str, set[WebSocket]]]] = {
            "alerts": {},
            "verification": {},
            "analytics": {},
            "notifications": {},
        }

    # ------------------------------------------------------------------
    # Connect / Disconnect
    # ------------------------------------------------------------------

    async def connect(
        self,
        channel: str,
        websocket: WebSocket,
        user_id: str,
        tenant_id: str,
    ) -> None:
        """Accept the WebSocket and register it under (channel, tenant, user)."""
        await websocket.accept()

        if channel not in self._connections:
            logger.warning("Unknown channel '%s' — rejecting connection", channel)
            await websocket.close(code=4004, reason=f"Unknown channel: {channel}")
            return

        if tenant_id not in self._connections[channel]:
            self._connections[channel][tenant_id] = {}

        if user_id not in self._connections[channel][tenant_id]:
            self._connections[channel][tenant_id][user_id] = set()

        self._connections[channel][tenant_id][user_id].add(websocket)

        total = sum(
            len(conns)
            for t_conns in self._connections[channel].values()
            for conns in t_conns.values()
        )
        logger.info(
            "WS connected  channel=%s tenant=%s user=%s (total=%d)",
            channel, tenant_id, user_id, total,
        )

    async def disconnect(
        self,
        channel: str,
        websocket: WebSocket,
        user_id: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Remove a WebSocket from the registry.  Cleans up empty branches."""
        if channel not in self._connections:
            return

        tenants_to_scan = [tenant_id] if tenant_id else list(self._connections[channel])
        for tid in tenants_to_scan:
            if tid not in self._connections[channel]:
                continue
            users_to_scan = [user_id] if user_id else list(self._connections[channel][tid])
            for uid in users_to_scan:
                if uid not in self._connections[channel][tid]:
                    continue
                self._connections[channel][tid][uid].discard(websocket)
                if not self._connections[channel][tid][uid]:
                    del self._connections[channel][tid][uid]
            if not self._connections[channel][tid]:
                del self._connections[channel][tid]

        logger.info(
            "WS disconnected channel=%s tenant=%s user=%s",
            channel, tenant_id or "*", user_id or "*",
        )

    # ------------------------------------------------------------------
    # Send helpers
    # ------------------------------------------------------------------

    async def send_to_user(
        self,
        channel: str,
        tenant_id: str,
        user_id: str,
        message: dict[str, Any],
    ) -> None:
        """Send a message to a specific user's connections (all tabs/windows)."""
        payload = json.dumps(message, default=str)
        user_connections = (
            self._connections.get(channel, {})
            .get(tenant_id, {})
            .get(user_id, set())
        )
        dead: set[WebSocket] = set()
        for ws in user_connections:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        # Clean up dead connections for this user
        if dead and channel in self._connections and tenant_id in self._connections[channel] and user_id in self._connections[channel][tenant_id]:
            self._connections[channel][tenant_id][user_id] -= dead

    async def send_to_tenant(
        self,
        channel: str,
        tenant_id: str,
        message: dict[str, Any],
    ) -> None:
        """Send a message to all users within a tenant on a channel."""
        payload = json.dumps(message, default=str)
        tenant_connections = self._connections.get(channel, {}).get(tenant_id, {})
        dead: set[WebSocket] = set()
        for user_conns in tenant_connections.values():
            for ws in user_conns:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.add(ws)
        # Clean up dead connections across all users in this tenant
        for uid in list(tenant_connections.keys()):
            self._connections[channel][tenant_id][uid] -= dead
            if not self._connections[channel][tenant_id][uid]:
                del self._connections[channel][tenant_id][uid]

    async def broadcast(
        self,
        channel: str,
        message: dict[str, Any],
        tenant_id: str | None = None,
        user_id: str | None = None,
    ) -> None:
        """
        Send a message to connections with optional targeting.

        Targeting logic (first match wins):
        - user_id + tenant_id → send_to_user
        - tenant_id only       → send_to_tenant
        - neither              → ALL connections on the channel
        """
        if channel not in self._connections:
            return

        if user_id and tenant_id:
            await self.send_to_user(channel, tenant_id, user_id, message)
        elif tenant_id:
            await self.send_to_tenant(channel, tenant_id, message)
        else:
            payload = json.dumps(message, default=str)
            dead: set[WebSocket] = set()
            for tenant_conns in self._connections[channel].values():
                for user_conns in tenant_conns.values():
                    for ws in user_conns:
                        try:
                            await ws.send_text(payload)
                        except Exception:
                            dead.add(ws)
            # Clean up dead connections across the entire channel
            for tid in list(self._connections[channel].keys()):
                for uid in list(self._connections[channel][tid].keys()):
                    self._connections[channel][tid][uid] -= dead
                    if not self._connections[channel][tid][uid]:
                        del self._connections[channel][tid][uid]
                if not self._connections[channel][tid]:
                    del self._connections[channel][tid]

    def get_connection_counts(self) -> dict[str, dict[str, dict[str, int]]]:
        """Return a diagnostic snapshot of all connections."""
        return {
            ch: {
                tid: {
                    uid: len(conns)
                    for uid, conns in u_dict.items()
                }
                for tid, u_dict in t_dict.items()
            }
            for ch, t_dict in self._connections.items()
        }


# Singleton manager
ws_manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════
# AUTHENTICATION HELPER
# ═══════════════════════════════════════════════════════════════


async def authenticate_websocket(websocket: WebSocket) -> dict[str, Any]:
    """
    Extract JWT from query param, validate, and return the token payload.

    The client **must** pass the token as a query parameter::

        wss://host/ws/notifications?token=JWT_HERE

    Raises ``AuthenticationError`` (which the caller should catch and
    close the socket with code 4001) if the token is missing or invalid.
    """
    token = websocket.query_params.get("token")
    if not token:
        raise AuthenticationError(
            "Authentication required. Pass ?token=<JWT> in the WebSocket URL."
        )
    return AuthService.verify_access_token(token)


# ═══════════════════════════════════════════════════════════════
# WEBSOCKET ENDPOINTS
# ═══════════════════════════════════════════════════════════════


async def _ws_endpoint(channel: str, websocket: WebSocket) -> None:
    """
    Generic WebSocket handler shared by all channels.

    Steps:
    1. Authenticate the client via JWT query parameter.
    2. Register the connection in the manager (scoped to user + tenant).
    3. Send a ``connected`` confirmation.
    4. Loop: read "ping" → reply "pong"; any other data is ignored.
    5. On disconnect: unregister.
    """
    # ── 1. Authenticate ────────────────────────────────────────
    try:
        payload = await authenticate_websocket(websocket)
    except AuthenticationError as exc:
        logger.warning("WS auth failed on %s: %s", channel, exc)
        await websocket.close(code=4001, reason=str(exc))
        return
    except Exception as exc:
        logger.error("WS auth error on %s: %s", channel, exc)
        await websocket.close(code=4001, reason="Authentication error")
        return

    user_id: str = str(payload["sub"])
    tenant_id: str = str(payload["tenant_id"])

    # ── 2. Register ────────────────────────────────────────────
    await ws_manager.connect(channel, websocket, user_id, tenant_id)

    try:
        # ── 3. Send connected confirmation ─────────────────────
        await websocket.send_text(
            json.dumps({
                "type": "connected",
                "channel": channel,
                "user_id": user_id,
                "message": f"Connected to {channel} stream",
            })
        )

        # ── 4. Message loop ────────────────────────────────────
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect(channel, websocket, user_id, tenant_id)
    except Exception as e:
        logger.error("WS error on channel %s: %s", channel, e)
        await ws_manager.disconnect(channel, websocket, user_id, tenant_id)


@router.websocket("/alerts")
async def ws_alerts(websocket: WebSocket) -> None:
    """Live fraud alerts channel (authenticated, tenant-scoped)."""
    await _ws_endpoint("alerts", websocket)


@router.websocket("/verification")
async def ws_verification(websocket: WebSocket) -> None:
    """Verification progress channel (authenticated, tenant-scoped)."""
    await _ws_endpoint("verification", websocket)


@router.websocket("/analytics")
async def ws_analytics(websocket: WebSocket) -> None:
    """Analytics channel (authenticated, tenant-scoped)."""
    await _ws_endpoint("analytics", websocket)


@router.websocket("/notifications")
async def ws_notifications(websocket: WebSocket) -> None:
    """Notification channel (authenticated, user-scoped)."""
    await _ws_endpoint("notifications", websocket)


# ═══════════════════════════════════════════════════════════════
# REDIS PUB/SUB — CROSS-PROCESS BRIDGE
# ═══════════════════════════════════════════════════════════════

_WS_REDIS_CHANNEL = "ws:notifications"
_redis_listener_task: asyncio.Task[None] | None = None


async def start_ws_redis_listener() -> None:
    """
    Background task: subscribe to Redis Pub/Sub for WebSocket
    notification events published by Celery workers.

    This is the bridge that allows Celery (running in a separate
    container) to push notifications to WebSocket clients connected
    to *this* FastAPI process.

    Expected message format from Redis::

        {
            "type": "new_notification",
            "data": { ... },
            "target": {
                "tenant_id": "...",
                "user_id": "..."       // optional — if omitted, sent to tenant
            }
        }
    """
    global _redis_listener_task
    logger.info("Starting WebSocket Redis listener on channel: %s", _WS_REDIS_CHANNEL)

    try:
        pubsub = await RedisPubSub.subscribe(_WS_REDIS_CHANNEL)
        logger.info("WebSocket Redis listener subscribed to %s", _WS_REDIS_CHANNEL)
    except Exception as exc:
        logger.error("Failed to subscribe to Redis channel %s: %s", _WS_REDIS_CHANNEL, exc)
        return

    try:
        async for message in RedisPubSub.listen(pubsub):
            try:
                target = message.get("target", {})
                tenant_id = target.get("tenant_id")
                user_id = target.get("user_id")

                await ws_manager.broadcast(
                    "notifications",
                    message,
                    tenant_id=tenant_id,
                    user_id=user_id,
                )
            except Exception as exc:
                logger.error("Error processing WS Redis message: %s", exc)
    except asyncio.CancelledError:
        logger.info("WebSocket Redis listener cancelled (shutting down)")
    except Exception as exc:
        logger.error("WebSocket Redis listener error: %s", exc)
    finally:
        logger.info("WebSocket Redis listener stopped")


async def stop_ws_redis_listener() -> None:
    """Cancel the WebSocket Redis listener background task."""
    global _redis_listener_task
    if _redis_listener_task is not None:
        _redis_listener_task.cancel()
        try:
            await _redis_listener_task
        except asyncio.CancelledError:
            pass
        _redis_listener_task = None
        logger.info("WebSocket Redis listener stopped")


# ═══════════════════════════════════════════════════════════════
# PUSH HELPERS — called from Celery tasks via Redis Pub/Sub
# ═══════════════════════════════════════════════════════════════


async def push_fraud_alert(
    alert_data: dict[str, Any],
    tenant_id: str | None = None,
) -> None:
    """
    Push fraud alert to the alerts channel.
    If ``tenant_id`` is provided, only clients from that tenant receive it.
    """
    await ws_manager.broadcast(
        "alerts",
        {
            "type": "fraud_alert",
            "data": alert_data,
        },
        tenant_id=tenant_id,
    )


async def push_verification_progress(
    document_id: str,
    status: str,
    progress: float,
    tenant_id: str | None = None,
) -> None:
    """Stream verification progress to the verification channel."""
    await ws_manager.broadcast(
        "verification",
        {
            "type": "verification_progress",
            "document_id": document_id,
            "status": status,
            "progress": progress,
        },
        tenant_id=tenant_id,
    )


async def push_dashboard_update(
    metrics: dict[str, Any],
    tenant_id: str | None = None,
) -> None:
    """Update dashboard metrics on the analytics channel."""
    await ws_manager.broadcast(
        "analytics",
        {
            "type": "dashboard_update",
            "metrics": metrics,
        },
        tenant_id=tenant_id,
    )


async def push_notification(
    notification_data: dict[str, Any],
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Push a real-time notification to connected clients.

    Targeting:
    - If ``user_id`` + ``tenant_id`` → send only to that user.
    - If ``tenant_id`` only         → send to all users in that tenant.
    - If neither                    → broadcast to ALL tenants (use with care).
    """
    message = {
        "type": "new_notification",
        "data": notification_data,
    }
    await ws_manager.broadcast(
        "notifications",
        message,
        tenant_id=tenant_id,
        user_id=user_id,
    )


async def publish_via_redis(
    notification_data: dict[str, Any],
    tenant_id: str | None = None,
    user_id: str | None = None,
) -> None:
    """
    Publish a notification event to Redis Pub/Sub so that **all**
    FastAPI workers (or a Celery worker acting as producer) can
    relay it to their locally-connected WebSocket clients.

    This is the function that Celery tasks should call instead of
    importing ``push_notification`` directly (which only works
    in-process).
    """
    message = {
        "type": "new_notification",
        "data": notification_data,
        "target": {
            "tenant_id": tenant_id,
            "user_id": user_id,
        },
    }
    try:
        published = await RedisPubSub.publish(_WS_REDIS_CHANNEL, message)
        logger.debug(
            "Published WS notification to Redis (subscribers=%d): %s",
            published,
            notification_data.get("id", "unknown"),
        )
    except Exception as exc:
        logger.error("Failed to publish WS notification to Redis: %s", exc)
