# ============================================================
# PaySentinelIQ — Rate Limiting ASGI Middleware
# Enforces per-route-group rate limits via Redis sliding window
# ============================================================

import logging
import re
import time
from typing import Any

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.shared.exceptions import RateLimitExceededError
from app.shared.rate_limiter import RateLimiter
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)


# ── Route-group classifiers ──────────────────────────────────────────
_LOGIN_PATHS = re.compile(r"^/api/auth/(login|google)$")
_HEALTH_PATHS = re.compile(
    r"^/(health|metrics|robots\.txt|sitemap\.xml|/?)$",
)
_API_PATHS = re.compile(r"^/api/")

# Endpoints that MUST always bypass rate limiting (e.g. health checks
# used by the platform orchestrator).
_BYPASS_PATHS = _HEALTH_PATHS


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that enforces per-route-group rate limits.

    Route groups
    ------------
    * ``login`` — ``POST /api/auth/login`` and ``POST /api/auth/google``.
      Applies the stricter ``RATE_LIMIT_LOGIN_MAX`` limit (default 5/60s).
      Identifier: client IP.

    * ``api``  — All other ``/api/*`` paths.
      Applies ``RATE_LIMIT_PER_USER`` (default 100/60s).
      Identifier: JWT ``sub`` claim when present, otherwise client IP.

    * (bypass) — ``/health``, ``/metrics``, ``/``, etc.  No limit.

    Response headers
    ----------------
    Every non-bypassed response receives:

    * ``X-RateLimit-Limit``     — max requests per window
    * ``X-RateLimit-Remaining`` — requests left in the current window
    * ``X-RateLimit-Reset``     — unix timestamp when the window resets

    When the limit is exceeded the client receives a **429** response with
    a ``Retry-After`` header and the same ``X-RateLimit-*`` headers.
    """

    def __init__(self, app: Any, redis_client: Any = None) -> None:
        super().__init__(app)
        self._limiter = RateLimiter(redis_client)

    # ------------------------------------------------------------------
    # Starlette dispatch
    # ------------------------------------------------------------------

    async def dispatch(self, request: Request, call_next: Any) -> Response:  # type: ignore[override]
        path = request.url.path
        method = request.method

        # ── 1. Bypass paths ────────────────────────────────────
        if _BYPASS_PATHS.match(path):
            return await call_next(request)

        # ── 2. Classify route group & pick identifier ──────────
        settings = get_settings()

        if _LOGIN_PATHS.match(path) and method == "POST":
            route_group = "login"
            identifier = self._get_ip(request)
            max_requests = settings.RATE_LIMIT_LOGIN_MAX
        elif _API_PATHS.match(path):
            route_group = "api"
            identifier = await self._resolve_identifier(request)
            max_requests = settings.RATE_LIMIT_PER_USER
        else:
            # Static / unknown paths — apply general limit by IP
            route_group = "api"
            identifier = self._get_ip(request)
            max_requests = settings.RATE_LIMIT_PER_USER

        window_seconds = settings.RATE_LIMIT_WINDOW

        # ── 3. Check & record ──────────────────────────────────
        try:
            result = await self._limiter.check(
                identifier=identifier,
                route_group=route_group,
                max_requests=max_requests,
                window_seconds=window_seconds,
            )
        except RateLimitExceededError as exc:
            retry_after = exc.details.get("retry_after_seconds", 60)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please try again later.",
                    "details": {"retry_after_seconds": retry_after},
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(
                        int(time.time() + window_seconds),
                    ),
                },
            )

        # ── 4. Forward request & annotate response ─────────────
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(result["limit"])
        response.headers["X-RateLimit-Remaining"] = str(result["remaining"])
        response.headers["X-RateLimit-Reset"] = str(result["reset"])
        return response

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_ip(request: Request) -> str:
        """Extract the client IP from forwarded headers or the socket."""
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client is not None:
            return request.client.host
        return "unknown"

    @staticmethod
    async def _resolve_identifier(request: Request) -> str:
        """
        Return the user ID from the JWT, or the client IP as a fallback.

        The JWT is read from the ``Authorization: Bearer <token>`` header
        and decoded with the same secret / algorithm used by the auth
        service.  If the token is missing, expired, or otherwise invalid
        we fall back to the IP address — the request will be rejected
        later by the route's own auth dependency if it needs
        authentication.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return RateLimitMiddleware._get_ip(request)

        token = auth_header[7:]
        try:
            settings = get_settings()
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY.get_secret_value(),
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id: str | None = payload.get("sub")
            if user_id is not None:
                return user_id
        except (JWTError, Exception):
            pass

        return RateLimitMiddleware._get_ip(request)
