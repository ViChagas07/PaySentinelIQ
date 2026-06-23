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


def event_handler(event_type: str) -> Callable[[EventHandler], EventHandler]:
    """Decorator to register a function as an event handler."""

    def decorator(func: EventHandler) -> EventHandler:
        EventBus.subscribe(event_type, func)
        return func

    return decorator


# ── Redis Listener (Background Task) ──


async def start_redis_event_listener() -> None:
    """
    Background task that listens for domain events from Redis pub/sub
    and dispatches them to local in-process handlers.

    Subscribes to ALL known domain event channels — not just the first one.
    """
    channels = [
        "psi:events:document:uploaded",
        "psi:events:ocr:completed",
        "psi:events:fraud_detection:started",
        "psi:events:risk:score_generated",
        "psi:events:compliance:check_triggered",
        "psi:events:analyst:alert_sent",
    ]

    if not channels:
        logger.warning("No domain event channels configured — Redis listener not started")
        return

    logger.info("Starting domain event Redis listener on %d channels", len(channels))

    try:
        client = await RedisPubSub._get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(*channels)
        logger.info("Subscribed to channels: %s", channels)
    except Exception as exc:
        logger.error("Failed to subscribe to Redis channels: %s", exc)
        return

    try:
        async for raw_msg in pubsub.listen():
            msg_type = raw_msg.get("type")
            if msg_type != "message":
                continue

            data = raw_msg.get("data")
            if data is None:
                continue

            try:
                import json
                message = json.loads(data) if isinstance(data, str) else data
            except (json.JSONDecodeError, TypeError):
                continue

            try:
                event_type = message.get("event_type")
                if event_type and event_type in EventBus._handlers:
                    logger.debug("Dispatching Redis event: %s", event_type)
                    # Dispatch to all local handlers for this event type
                    from app.events import DomainEvent
                    event = DomainEvent(
                        event_type=event_type,
                        data=message.get("data", {}),
                    )
                    await asyncio.gather(
                        *(handler(event) for handler in EventBus._handlers[event_type]),
                        return_exceptions=True,
                    )
            except Exception as e:
                logger.error("Error dispatching Redis event: %s", e)
    except asyncio.CancelledError:
        logger.info("Domain event Redis listener cancelled (shutting down)")
    except Exception as exc:
        logger.error("Domain event Redis listener error: %s", exc)
    finally:
        logger.info("Domain event Redis listener stopped")
