# ============================================================
# PaySentinelIQ — Redis Client
# Async Redis connection with pub/sub and cache helpers
# ============================================================

import json
from collections.abc import AsyncGenerator
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from app.shared.settings import get_settings

settings = get_settings()

redis_pool: Optional[Redis] = None


async def get_redis() -> Redis:
    """Dependency injection for Redis connection."""
    global redis_pool
    if redis_pool is None:
        redis_pool = aioredis.from_url(
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
    async def get(key: str) -> Optional[Any]:
        client = await get_redis()
        value = await client.get(key)
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return None

    @staticmethod
    async def set(key: str, value: Any, ttl: Optional[int] = None) -> None:
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
        cursor = 0
        while True:
            cursor, keys = await client.scan(cursor, match=pattern, count=100)
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
        return await client.publish(full_channel, payload)

    @staticmethod
    async def subscribe(channel: str) -> PubSub:
        client = await get_redis()
        full_channel = f"{RedisPubSub.CHANNEL_PREFIX}:{channel}"
        pubsub = client.pubsub()
        await pubsub.subscribe(full_channel)
        return pubsub

    @staticmethod
    async def listen(pubsub: PubSub) -> AsyncGenerator[dict[str, Any], None]:
        """Async generator yielding decoded messages from a subscription."""
        async for msg in pubsub.listen():
            if msg["type"] == "message":
                try:
                    data = json.loads(msg["data"])
                    yield data
                except (json.JSONDecodeError, TypeError):
                    raw = msg["data"]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    yield {"raw": raw}
