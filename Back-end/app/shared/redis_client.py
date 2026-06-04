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
        redis_pool = aioredis.from_url(  # type: ignore[no-untyped-call]
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=50,
        )
    return redis_pool


async def close_redis() -> None:
    """Close Redis connection pool on shutdown."""
    global redis_pool
    if redis_pool:
        await redis_pool.close()
        redis_pool = None


class RedisCache:
    """Async Redis cache helper."""

    @staticmethod
    async def get(key: str) -> Any | None:
        client = await get_redis()
        value = await client.get(key)
        if value is not None:
            try:
                return json.loads(cast(str, value))
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int | None = None) -> None:
        client = await get_redis()
        ttl = ttl or settings.REDIS_CACHE_TTL
        data = json.dumps(value, default=str)
        await client.setex(key, ttl, data)

    @staticmethod
    async def delete(key: str) -> None:
        client = await get_redis()
        await client.delete(key)

    @staticmethod
    async def delete_pattern(pattern: str) -> None:
        client = await get_redis()
        cursor: int = 0
        while True:
            result = await cast(Any, client).scan(
                cursor, match=pattern, count=100
            )
            cursor, keys = cast(tuple[int, list[str]], result)
            if keys:
                await client.delete(*keys)
            if cursor == 0:
                break


class RedisPubSub:
    """Async Redis Pub/Sub bridge for event-driven architecture."""

    CHANNEL_PREFIX = "psi:events"

    @staticmethod
    async def publish(channel: str, message: dict[str, Any]) -> int:
        client = await get_redis()
        full_channel = f"{RedisPubSub.CHANNEL_PREFIX}:{channel}"
        payload = json.dumps(message, default=str)
        return cast(int, await cast(Any, client).publish(full_channel, payload))

    @staticmethod
    async def subscribe(channel: str) -> PubSub:
        client = await get_redis()
        full_channel = f"{RedisPubSub.CHANNEL_PREFIX}:{channel}"
        pubsub = cast(Any, client).pubsub()
        await pubsub.subscribe(full_channel)
        return cast(PubSub, pubsub)

    @staticmethod
    async def listen(pubsub: PubSub) -> AsyncGenerator[dict[str, Any], None]:
        """Async generator yielding decoded messages from a subscription."""
        async for msg in cast(Any, pubsub).listen():
            if msg.get("type") == "message":
                raw_data = msg.get("data")
                try:
                    data = json.loads(cast(str, raw_data))
                    yield cast(dict[str, Any], data)
                except (json.JSONDecodeError, TypeError):
                    if isinstance(raw_data, bytes):
                        raw_data = raw_data.decode("utf-8", errors="replace")
                    yield {"raw": raw_data}
