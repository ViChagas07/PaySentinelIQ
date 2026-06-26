# ============================================================
# PaySentinelIQ — Rate Limiting (Fase 4)
# ============================================================

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimiter:
    """In-memory sliding window rate limiter per key."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets[key]
        # Remove expired entries
        cutoff = now - self._window
        self._buckets[key] = [t for t in bucket if t > cutoff]
        if len(self._buckets[key]) >= self._max:
            return False
        self._buckets[key].append(now)
        return True

    def remaining(self, key: str) -> int:
        now = time.monotonic()
        bucket = self._buckets[key]
        cutoff = now - self._window
        active = sum(1 for t in bucket if t > cutoff)
        return max(0, self._max - active)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_per_ip: int = 100, max_per_user: int = 30, window: int = 60):
        super().__init__(app)
        self._ip_limiter = RateLimiter(max_per_ip, window)
        self._user_limiter = RateLimiter(max_per_user, window)

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        # Skip health/static paths
        if request.url.path.startswith(("/health", "/ready", "/live", "/static")):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        if not self._ip_limiter.is_allowed(ip):
            raise HTTPException(status_code=429, detail="Too many requests")

        return await call_next(request)
