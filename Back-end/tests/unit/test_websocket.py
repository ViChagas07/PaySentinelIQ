# ============================================================
# PaySentinelIQ — WebSocket Unit Tests
#
# Tests:
# - ConnectionManager (multi-tenant connect/disconnect/broadcast)
# - User and tenant isolation
# - JWT authentication helper
# - Redis Pub/Sub integration
# ============================================================

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.websocket.router import (
    ConnectionManager,
    authenticate_websocket,
    ws_manager,
)


# ═══════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def manager() -> ConnectionManager:
    """Fresh ConnectionManager for each test."""
    return ConnectionManager()


@pytest.fixture
def mock_ws() -> AsyncMock:
    """Mock WebSocket that simulates accept/send/close."""
    ws = AsyncMock()
    ws.send_text = AsyncMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    ws.receive_text = AsyncMock()
    ws.query_params = {}
    return ws


@pytest.fixture
def mock_auth_service() -> None:
    """Patch AuthService.verify_access_token for unit tests."""
    with patch("app.websocket.router.AuthService") as mock:
        mock.verify_access_token.return_value = {
            "sub": "user-123",
            "tenant_id": "tenant-abc",
            "role": "fraud_analyst",
            "type": "access",
        }
        yield mock


# ═══════════════════════════════════════════════════════════════
# CONNECTION MANAGER — CONNECT / DISCONNECT
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_connect_registers_websocket(manager: ConnectionManager, mock_ws: AsyncMock) -> None:
    """A WebSocket should be registered under the correct channel/tenant/user."""
    await manager.connect("notifications", mock_ws, "user-123", "tenant-abc")

    assert "user-123" in manager._connections["notifications"]["tenant-abc"]
    assert mock_ws in manager._connections["notifications"]["tenant-abc"]["user-123"]
    mock_ws.accept.assert_awaited_once()


@pytest.mark.asyncio
async def test_connect_rejects_unknown_channel(manager: ConnectionManager, mock_ws: AsyncMock) -> None:
    """An unknown channel should close the connection with code 4004."""
    await manager.connect("unknown_channel", mock_ws, "user-123", "tenant-abc")

    # The order is: accept() first, then close(4004) if channel unknown.
    # accept() is called first so the client can receive the close frame.
    mock_ws.accept.assert_awaited_once()
    mock_ws.close.assert_awaited_once_with(code=4004, reason="Unknown channel: unknown_channel")


@pytest.mark.asyncio
async def test_disconnect_removes_websocket(manager: ConnectionManager, mock_ws: AsyncMock) -> None:
    """After disconnect, the WebSocket should no longer be in the registry."""
    await manager.connect("notifications", mock_ws, "user-123", "tenant-abc")
    assert mock_ws in manager._connections["notifications"]["tenant-abc"]["user-123"]

    await manager.disconnect("notifications", mock_ws, "user-123", "tenant-abc")

    # The entire tenant-abc dict should be cleaned up (no more users)
    assert "tenant-abc" not in manager._connections["notifications"]


@pytest.mark.asyncio
async def test_disconnect_cleans_up_empty_branches(manager: ConnectionManager, mock_ws: AsyncMock) -> None:
    """After removing the last user's connection, tenant dict should also be cleaned."""
    await manager.connect("notifications", mock_ws, "user-123", "tenant-abc")
    await manager.disconnect("notifications", mock_ws, "user-123", "tenant-abc")

    assert "tenant-abc" not in manager._connections["notifications"]


@pytest.mark.asyncio
async def test_multiple_tabs_same_user(manager: ConnectionManager) -> None:
    """Multiple WebSocket connections from the same user should all be tracked."""
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await manager.connect("notifications", ws1, "user-123", "tenant-abc")
    await manager.connect("notifications", ws2, "user-123", "tenant-abc")

    assert ws1 in manager._connections["notifications"]["tenant-abc"]["user-123"]
    assert ws2 in manager._connections["notifications"]["tenant-abc"]["user-123"]


# ═══════════════════════════════════════════════════════════════
# CONNECTION MANAGER — TENANT ISOLATION
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_broadcast_respects_tenant_isolation(manager: ConnectionManager) -> None:
    """A broadcast to tenant-abc should NOT reach tenant-xyz."""
    ws_abc = AsyncMock()
    ws_xyz = AsyncMock()
    await manager.connect("notifications", ws_abc, "user-1", "tenant-abc")
    await manager.connect("notifications", ws_xyz, "user-2", "tenant-xyz")

    await manager.broadcast(
        "notifications",
        {"type": "test", "message": "hello"},
        tenant_id="tenant-abc",
    )

    ws_abc.send_text.assert_awaited_once()
    ws_xyz.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_to_user_isolation(manager: ConnectionManager) -> None:
    """send_to_user should only reach the specified user, not other users in same tenant."""
    ws_user1 = AsyncMock()
    ws_user2 = AsyncMock()
    await manager.connect("notifications", ws_user1, "user-1", "tenant-abc")
    await manager.connect("notifications", ws_user2, "user-2", "tenant-abc")

    await manager.send_to_user("notifications", "tenant-abc", "user-1", {"type": "private"})

    ws_user1.send_text.assert_awaited_once()
    ws_user2.send_text.assert_not_awaited()


@pytest.mark.asyncio
async def test_broadcast_without_target_reaches_all(manager: ConnectionManager) -> None:
    """A broadcast without tenant_id/user_id should reach all connections."""
    ws_a = AsyncMock()
    ws_b = AsyncMock()
    await manager.connect("notifications", ws_a, "user-1", "tenant-abc")
    await manager.connect("notifications", ws_b, "user-2", "tenant-xyz")

    await manager.broadcast("notifications", {"type": "global"})

    ws_a.send_text.assert_awaited_once()
    ws_b.send_text.assert_awaited_once()


# ═══════════════════════════════════════════════════════════════
# CONNECTION MANAGER — DEAD CONNECTION CLEANUP
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_dead_connection_cleaned_on_broadcast(manager: ConnectionManager) -> None:
    """If send_text raises an exception, the dead connection should be removed."""
    ws_alive = AsyncMock()
    ws_dead = AsyncMock()
    ws_dead.send_text = AsyncMock(side_effect=Exception("Connection lost"))

    await manager.connect("notifications", ws_alive, "user-1", "tenant-abc")
    await manager.connect("notifications", ws_dead, "user-2", "tenant-abc")

    await manager.broadcast("notifications", {"type": "test"})

    # Dead connection should be removed
    assert ws_dead not in manager._connections["notifications"]["tenant-abc"].get("user-2", set())
    # Alive connection should still be there
    assert ws_alive in manager._connections["notifications"]["tenant-abc"]["user-1"]


# ═══════════════════════════════════════════════════════════════
# CONNECTION COUNTS
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_connection_counts(manager: ConnectionManager) -> None:
    """get_connection_counts should return an accurate snapshot."""
    ws1 = AsyncMock()
    ws2 = AsyncMock()
    await manager.connect("notifications", ws1, "user-1", "tenant-abc")
    await manager.connect("notifications", ws2, "user-2", "tenant-abc")

    counts = manager.get_connection_counts()
    assert counts["notifications"]["tenant-abc"]["user-1"] == 1
    assert counts["notifications"]["tenant-abc"]["user-2"] == 1


# ═══════════════════════════════════════════════════════════════
# JWT AUTHENTICATION
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_authenticate_websocket_no_token(mock_ws: AsyncMock) -> None:
    """Without a token, authenticate_websocket should raise AuthenticationError."""
    mock_ws.query_params = {}

    from app.shared.exceptions import AuthenticationError

    with pytest.raises(AuthenticationError, match="Authentication required"):
        await authenticate_websocket(mock_ws)


@pytest.mark.asyncio
@patch("app.websocket.router.AuthService.verify_access_token")
async def test_authenticate_websocket_valid_token(
    mock_verify: MagicMock,
    mock_ws: AsyncMock,
) -> None:
    """With a valid token, the payload should be returned."""
    mock_ws.query_params = {"token": "valid-jwt-token"}
    mock_verify.return_value = {
        "sub": "user-123",
        "tenant_id": "tenant-abc",
        "role": "fraud_analyst",
        "type": "access",
    }

    payload = await authenticate_websocket(mock_ws)

    assert payload["sub"] == "user-123"
    assert payload["tenant_id"] == "tenant-abc"
    assert payload["role"] == "fraud_analyst"
    mock_verify.assert_called_once_with("valid-jwt-token")


@pytest.mark.asyncio
@patch("app.websocket.router.AuthService.verify_access_token")
async def test_authenticate_websocket_invalid_token(
    mock_verify: MagicMock,
    mock_ws: AsyncMock,
) -> None:
    """An invalid token should raise AuthenticationError."""
    mock_ws.query_params = {"token": "bad-token"}
    from app.shared.exceptions import AuthenticationError

    mock_verify.side_effect = AuthenticationError("Invalid token")

    with pytest.raises(AuthenticationError):
        await authenticate_websocket(mock_ws)


# ═══════════════════════════════════════════════════════════════
# END-TO-END: AUTH + CONNECTION FLOW
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
@patch("app.websocket.router.AuthService.verify_access_token")
async def test_ws_endpoint_rejects_unauthenticated(
    mock_verify: MagicMock,
    manager: ConnectionManager,
    mock_ws: AsyncMock,
) -> None:
    """The endpoint should close with code 4001 when no token is provided."""
    from app.websocket.router import _ws_endpoint

    mock_ws.query_params = {}

    await _ws_endpoint("notifications", mock_ws)

    mock_ws.close.assert_awaited_once_with(code=4001, reason="Authentication required. Pass ?token=<JWT> in the WebSocket URL.")
    mock_ws.accept.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.websocket.router.AuthService.verify_access_token")
async def test_ws_endpoint_accepts_authenticated(
    mock_verify: MagicMock,
    manager: ConnectionManager,
    mock_ws: AsyncMock,
) -> None:
    """The endpoint should accept the connection when a valid token is provided."""
    from app.websocket.router import _ws_endpoint

    mock_ws.query_params = {"token": "valid-jwt"}
    mock_ws.receive_text = AsyncMock(return_value="ping")
    mock_verify.return_value = {
        "sub": "user-123",
        "tenant_id": "tenant-abc",
        "role": "fraud_analyst",
        "type": "access",
    }

    # We call _ws_endpoint but it will loop forever on receive_text.
    # We use a side effect to raise WebSocketDisconnect after first message.
    import fastapi
    mock_ws.receive_text.side_effect = [
        "ping",
        fastapi.WebSocketDisconnect(),
    ]

    await _ws_endpoint("notifications", mock_ws)

    # Should have accepted and sent connected + pong
    assert mock_ws.accept.await_count == 1
    assert mock_ws.send_text.await_count >= 2  # connected + pong


# ═══════════════════════════════════════════════════════════════
# REDIS PUB/SUB INTEGRATION
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
@patch("app.websocket.router.RedisPubSub.publish")
async def test_publish_via_redis(mock_publish: AsyncMock) -> None:
    """publish_via_redis should publish to the correct Redis channel."""
    from app.websocket.router import publish_via_redis

    await publish_via_redis(
        notification_data={"id": "notif-1", "title": "Test"},
        tenant_id="tenant-abc",
        user_id="user-123",
    )

    mock_publish.assert_awaited_once()
    args, _ = mock_publish.call_args
    channel, message = args

    assert channel == "ws:notifications"
    assert message["type"] == "new_notification"
    assert message["data"]["id"] == "notif-1"
    assert message["target"]["tenant_id"] == "tenant-abc"
    assert message["target"]["user_id"] == "user-123"
