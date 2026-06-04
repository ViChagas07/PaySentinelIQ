# ============================================================
# PaySentinelIQ — WebSocket Module
# Connection manager, Redis bridge, channel routing
# ============================================================

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class ConnectionManager:
    """
    Manages WebSocket connections across channels.
    Bridges Redis pub/sub messages to connected WebSocket clients.
    """

    def __init__(self):
        # channel_name -> set of WebSocket connections
        self._connections: dict[str, set[WebSocket]] = {
            "alerts": set(),
            "verification": set(),
            "analytics": set(),
            "notifications": set(),
        }

    async def connect(self, channel: str, websocket: WebSocket) -> None:
        await websocket.accept()
        if channel in self._connections:
            self._connections[channel].add(websocket)
        logger.info(
            "WebSocket connected to channel: %s (total: %d)",
            channel,
            len(self._connections.get(channel, set())),
        )

    async def disconnect(self, channel: str, websocket: WebSocket) -> None:
        if channel in self._connections:
            self._connections[channel].discard(websocket)
        logger.info("WebSocket disconnected from channel: %s", channel)

    async def broadcast(self, channel: str, message: dict[str, Any]) -> None:
        """Send a message to all clients subscribed to a channel."""
        if channel not in self._connections:
            return

        dead_connections: set[WebSocket] = set()
        payload = json.dumps(message, default=str)

        for connection in self._connections[channel]:
            try:
                await connection.send_text(payload)
            except Exception:
                dead_connections.add(connection)

        # Clean up dead connections
        self._connections[channel] -= dead_connections

    async def broadcast_to_all(self, message: dict[str, Any]) -> None:
        """Broadcast to all channels."""
        for channel in self._connections:
            await self.broadcast(channel, message)

    def get_connection_counts(self) -> dict[str, int]:
        return {ch: len(conns) for ch, conns in self._connections.items()}


# Singleton manager
ws_manager = ConnectionManager()


# ── WebSocket Endpoints ──


@router.websocket("/alerts")
async def ws_alerts(websocket: WebSocket):
    """
    Live fraud alerts channel.
    Pushes new fraud alerts to connected analysts in real-time.
    """
    await ws_manager.connect("alerts", websocket)
    try:
        # Send initial connection confirmation
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "channel": "alerts",
                    "message": "Connected to fraud alerts stream",
                }
            )
        )

        # Keep connection alive, listen for client messages
        while True:
            data = await websocket.receive_text()
            # Clients can send ping/heartbeat
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect("alerts", websocket)
    except Exception as e:
        logger.error("WebSocket error on alerts channel: %s", e)
        await ws_manager.disconnect("alerts", websocket)


@router.websocket("/verification")
async def ws_verification(websocket: WebSocket):
    """
    Verification progress channel.
    Streams real-time OCR and AI analysis progress for active documents.
    """
    await ws_manager.connect("verification", websocket)
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "channel": "verification",
                    "message": "Connected to verification progress stream",
                }
            )
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect("verification", websocket)
    except Exception as e:
        logger.error("WebSocket error on verification channel: %s", e)
        await ws_manager.disconnect("verification", websocket)


@router.websocket("/analytics")
async def ws_analytics(websocket: WebSocket):
    """
    Analytics channel.
    Pushes dashboard metric updates and risk score changes in real-time.
    """
    await ws_manager.connect("analytics", websocket)
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "channel": "analytics",
                    "message": "Connected to analytics stream",
                    "metrics": {
                        "payrolls_processed": 12487,
                        "fraud_alerts": 23,
                        "verification_rate": 98.4,
                    },
                }
            )
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect("analytics", websocket)
    except Exception as e:
        logger.error("WebSocket error on analytics channel: %s", e)
        await ws_manager.disconnect("analytics", websocket)


@router.websocket("/notifications")
async def ws_notifications(websocket: WebSocket):
    """
    Notification channel.
    Pushes user-specific notifications in real-time.
    """
    await ws_manager.connect("notifications", websocket)
    try:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "connected",
                    "channel": "notifications",
                    "message": "Connected to notification stream",
                }
            )
        )

        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

    except WebSocketDisconnect:
        await ws_manager.disconnect("notifications", websocket)
    except Exception as e:
        logger.error("WebSocket error on notifications channel: %s", e)
        await ws_manager.disconnect("notifications", websocket)


# ── Helper: push events from Celery tasks ──


async def push_fraud_alert(alert_data: dict[str, Any]) -> None:
    """Called by Celery tasks to push fraud alerts to connected analysts."""
    await ws_manager.broadcast(
        "alerts",
        {
            "type": "fraud_alert",
            "data": alert_data,
        },
    )


async def push_verification_progress(document_id: str, status: str, progress: float) -> None:
    """Called by Celery tasks to stream verification progress."""
    await ws_manager.broadcast(
        "verification",
        {
            "type": "verification_progress",
            "document_id": document_id,
            "status": status,
            "progress": progress,
        },
    )


async def push_dashboard_update(metrics: dict[str, Any]) -> None:
    """Called by Celery tasks to update dashboard metrics."""
    await ws_manager.broadcast(
        "analytics",
        {
            "type": "dashboard_update",
            "metrics": metrics,
        },
    )
