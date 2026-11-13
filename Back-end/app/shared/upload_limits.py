# ============================================================
# PaySentinelIQ — Upload request body limit
# Counts bytes actually received for upload paths, independent
# of client-provided Content-Length, before multipart parsing.
# ============================================================

from __future__ import annotations

from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

UPLOAD_PATHS = frozenset(
    {
        "/api/documents/analyze",
        "/api/verifications/upload",
    }
)


class UploadBodyLimitMiddleware:
    """Path-scoped ASGI middleware that bounds actual body bytes received.

    The body is buffered only up to the configured cap and replayed to the
    inner application, so FastAPI's multipart parser never sees more than the
    allowed body. This does not replace proxy/ingress limits.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in UPLOAD_PATHS
        ):
            await self.app(scope, receive, send)
            return

        # Reject early when a truthful Content-Length already exceeds the cap.
        # A missing or understated header is still caught by the byte count.
        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    declared_length = int(value)
                except ValueError:
                    break
                if declared_length > self.max_bytes:
                    response = JSONResponse(
                        status_code=413,
                        content={
                            "detail": "Request body exceeds the allowed size"
                        },
                    )
                    await response(scope, receive, send)
                    return
                break

        buffered: list[Message] = []
        total_bytes = 0

        while True:
            message = await receive()
            if message.get("type") != "http.request":
                buffered.append(message)
                break

            body = message.get("body", b"")
            total_bytes += len(body)
            if total_bytes > self.max_bytes:
                response = JSONResponse(
                    status_code=413,
                    content={"detail": "Request body exceeds the allowed size"},
                )
                await response(scope, receive, send)
                return

            buffered.append(message)
            if not message.get("more_body", False):
                break

        replay = iter(buffered)

        async def replay_receive() -> Message:
            try:
                return next(replay)
            except StopIteration:
                return await receive()

        await self.app(scope, replay_receive, send)
