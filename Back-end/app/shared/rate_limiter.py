# ============================================================
# PaySentinelIQ — Redis-based Rate Limiter
# Sliding window counter using Redis sorted sets
# Fail-open: if Redis is down, requests are allowed through
# ============================================================

import logging
import time
from typing import Any

from app.shared.exceptions import RateLimitExceededError
from app.shared.settings import get_settings

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Sliding window rate limiter backed by Redis sorted sets.

    How it works (per identifier + route_group):
      1. Prune timestamp entries older than the window.
      2. Count the remaining entries (current request volume).
      3. Add the current timestamp to the set.
      4. If count > limit → raise RateLimitExceededError.
      5. Return limit/remaining/reset info for response headers.

    The sorted set is bounded by the window size so memory is O(max_requests).
    """

    def __init__(self, redis_client: Any = None) -> None:
        self._redis = redis_client

    # ------------------------------------------------------------------
    # Internal: get Redis client (lazy — import inside method to avoid
    # circular dependencies at module level)
    # ------------------------------------------------------------------
    async def _get_redis(self) -> Any:
        if self._redis is None:
            from app.shared.redis_client import get_redis

            self._redis = await get_redis()
        return self._redis

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def check(
        self,
        identifier: str,
        route_group: str = "api",
        max_requests: int | None = None,
        window_seconds: int | None = None,
    ) -> dict[str, int]:
        """
        Check (and record) a request against the rate limit.

        Parameters
        ----------
        identifier : str
            Unique identifier for the client — typically ``user_id`` for
            authenticated requests or the client IP for anonymous ones.
        route_group : str
            Logical group used as a Redis key segment (e.g. ``"login"``,
            ``"api"``).  Different groups can have different limits.
        max_requests : int | None
            Maximum number of requests allowed within the window.  Falls
            back to ``settings.RATE_LIMIT_PER_USER`` (or ``LOGIN_MAX``
            depending on the caller).
        window_seconds : int | None
            Width of the sliding window in seconds.  Falls back to
            ``settings.RATE_LIMIT_WINDOW``.

        Returns
        -------
        dict
            ``{"limit": …, "remaining": …, "reset": …, "retry_after": …}``

        Raises
        ------
        RateLimitExceededError
            When the caller has exceeded the allowed number of requests.
        """
        settings = get_settings()
        max_requests = max_requests or settings.RATE_LIMIT_PER_USER
        window_seconds = window_seconds or settings.RATE_LIMIT_WINDOW

        key = f"rl:{route_group}:{identifier}"
        now = time.time()
        window_start = now - window_seconds

        try:
            redis = await self._get_redis()

            # ── Atomic pipeline ──────────────────────────────────
            pipe = redis.pipeline()

            # 1. Remove timestamps outside the current window
            pipe.zremrangebyscore(key, 0, window_start)  # (void)

            # 2. Count how many timestamps remain inside the window
            pipe.zcard(key)  # → int

            # 3. Insert the current timestamp
            pipe.zadd(key, {str(now): now})  # (void)

            # 4. Set TTL so the key auto-expires (window + 1s buffer)
            pipe.expire(key, window_seconds + 1)  # (void)

            results = await pipe.execute()

            request_count: int = results[1]  # zcard result

            reset_at = int(now + window_seconds)
            retry_after = max(1, int(window_start + window_seconds - now))
            remaining = max(0, max_requests - request_count)

            if request_count > max_requests:
                raise RateLimitExceededError(retry_after=retry_after)

            return {
                "limit": max_requests,
                "remaining": remaining,
                "reset": reset_at,
                "retry_after": retry_after,
            }

        except RateLimitExceededError:
            raise  # re-raise — the middleware will turn this into a 429
        except Exception as exc:
            # Fail open: if Redis is unreachable we log the warning and let
            # the request through.  A production deployment should alert on
            # this.
            logger.warning(
                "Rate limiter check failed (allowing request): %s", exc,
            )
            return {
                "limit": max_requests,
                "remaining": 1,
                "reset": int(now + window_seconds),
                "retry_after": 0,
            }
