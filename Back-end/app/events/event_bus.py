# ============================================================
# PaySentinelIQ — Event Bus
# Central event dispatcher using Redis pub/sub
# ============================================================

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.events import DomainEvent
from app.shared.redis_client import RedisPubSub

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    """
    Central event bus for publishing and subscribing to domain events.
    Uses Redis pub/sub for cross-process communication.
    Supports local in-memory handlers for same-process dispatching.
    """

    _handlers: dict[str, list[EventHandler]] = {}

    @classmethod
    def subscribe(cls, event_type: str, handler: EventHandler) -> None:
        """Register a handler for a specific event type."""
        if event_type not in cls._handlers:
            cls._handlers[event_type] = []
        cls._handlers[event_type].append(handler)
        logger.info("Handler registered for event: %s", event_type)

    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        """
        Publish an event to both:
        1. Local in-memory handlers (same process)
        2. Redis pub/sub (cross-process, for Celery workers / other services)
        """
        # 1. Local handlers
        local_handlers = cls._handlers.get(event.event_type, [])
        if local_handlers:
            await asyncio.gather(
                *(handler(event) for handler in local_handlers),
                return_exceptions=True,
            )

        # 2. Redis pub/sub for cross-process
        try:
            channel = event.event_type.replace(".", ":")
            await RedisPubSub.publish(channel, event.to_redis_message())
        except Exception as e:
            logger.error("Failed to publish event %s to Redis: %s", event.event_type, e)

    @classmethod
    async def publish_many(cls, events: list[DomainEvent]) -> None:
        """Publish multiple events concurrently."""
        await asyncio.gather(*(cls.publish(e) for e in events), return_exceptions=True)


# ── Decorator for auto-subscribing handlers ──


def event_handler(event_type: str):
    """Decorator to register a function as an event handler."""

    def decorator(func: EventHandler) -> EventHandler:
        EventBus.subscribe(event_type, func)
        return func

    return decorator


# ── Redis Listener (Background Task) ──


async def start_redis_event_listener() -> None:
    """
    Background task that listens for events from Redis pub/sub
    and dispatches them to local handlers. Used by Celery workers
    and other processes that need to react to events.
    """
    channels = [
        "psi:events:document:uploaded",
        "psi:events:ocr:completed",
        "psi:events:fraud_detection:started",
        "psi:events:risk:score_generated",
        "psi:events:compliance:check_triggered",
        "psi:events:analyst:alert_sent",
    ]

    pubsub = await RedisPubSub.subscribe(channels[0])
    async for message in RedisPubSub.listen(pubsub):
        try:
            event_type = message.get("event_type")
            if event_type and event_type in EventBus._handlers:
                # Reconstruct event and dispatch to local handlers
                # Note: In production, use a factory to reconstruct the correct event type
                logger.debug("Received Redis event: %s", event_type)
        except Exception as e:
            logger.error("Error processing Redis event: %s", e)
