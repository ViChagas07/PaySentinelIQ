# ============================================================
# PaySentinelIQ — Redis Client
# Async Redis connection with pub/sub and cache helpers
# ============================================================

import json
from collections.abc import AsyncGenerator
from typing import Any, cast

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.shared.settings import get_settings

settings = get_settings()

redis_pool: Redis | None = None


async def get_redis() -> Redis:
    """Dependency injection for Redis connection."""

    global redis_pool

    if redis_pool is None:
        redis_pool = cast(
            Redis,
            aioredis.from_url(  # type: ignore[no-untyped-call]
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=50,
            ),
        )

    return redis_pool


async def close_redis() -> None:
    """Close Redis connection pool on shutdown."""

    global redis_pool

    if redis_pool is not None:
        await redis_pool.aclose()
        redis_pool = None


class RedisCache:
    """Async Redis cache helper."""

    @staticmethod
    async def get(key: str) -> Any | None:
        client = await get_redis()

        value = await client.get(key)

        if value is None:
            return None

        try:
            return json.loads(cast(str, value))
        except (json.JSONDecodeError, TypeError):
            return value

    @staticmethod
    async def set(
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:

        client = await get_redis()

        ttl = ttl or settings.REDIS_CACHE_TTL

        data = json.dumps(
            value,
            default=str,
        )

        await client.setex(
            key,
            ttl,
            data,
        )

    @staticmethod
    async def delete(
        key: str,
    ) -> None:

        client = await get_redis()

        await client.delete(key)

    @staticmethod
    async def delete_pattern(
        pattern: str,
    ) -> None:

        client = await get_redis()

        cursor = 0

        while True:
            scan_result = cast(
                tuple[int, list[str]],
                await client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100,
                ),
            )

            cursor, keys = scan_result

            if keys:
                await client.delete(*keys)

            if cursor == 0:
                break


class RedisPubSub:
    """Async Redis Pub/Sub bridge."""

    CHANNEL_PREFIX = "psi:events"

    @staticmethod
    async def publish(
        channel: str,
        message: dict[str, Any],
    ) -> int:

        client = await get_redis()

        full_channel = f"{RedisPubSub.CHANNEL_PREFIX}:{channel}"

        payload = json.dumps(
            message,
            default=str,
        )

        published = cast(
            int,
            await client.publish(
                full_channel,
                payload,
            ),
        )

        return published

    @staticmethod
    async def subscribe(
        channel: str,
    ) -> PubSub:

        client = await get_redis()

        full_channel = f"{RedisPubSub.CHANNEL_PREFIX}:{channel}"

        pubsub = client.pubsub()

        await pubsub.subscribe(
            full_channel,
        )

        return pubsub

    @staticmethod
    async def listen(
        pubsub: PubSub,
    ) -> AsyncGenerator[
        dict[str, Any],
        None,
    ]:

        async for raw_msg in pubsub.listen():
            msg = cast(
                dict[str, Any],
                raw_msg,
            )

            if msg.get("type") != "message":
                continue

            data = msg.get("data")

            if data is None:
                continue

            try:
                parsed = cast(
                    dict[str, Any],
                    json.loads(cast(str, data)),
                )

                yield parsed

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                if isinstance(
                    data,
                    bytes,
                ):
                    data = data.decode(
                        "utf-8",
                        errors="replace",
                    )

                yield {"raw": str(data)}
