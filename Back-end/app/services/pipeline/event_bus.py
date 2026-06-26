# ============================================================
# PaySentinelIQ — Pipeline Event Bus
# ============================================================
# Publish/subscribe event system for pipeline lifecycle.
# Stages publish events. Consumers subscribe.
# Zero coupling: publishers don't know about subscribers.
# ============================================================

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PipelineEventType(str, Enum):
    # Pipeline lifecycle
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_FINISHED = "pipeline_finished"
    PIPELINE_FAILED = "pipeline_failed"
    PIPELINE_PARTIAL = "pipeline_partial"
    # Stage lifecycle
    STAGE_STARTED = "stage_started"
    STAGE_FINISHED = "stage_finished"
    STAGE_FAILED = "stage_failed"
    # Evidence
    EVIDENCE_CREATED = "evidence_created"
    # AI
    CREW_STARTED = "crew_started"
    CREW_FINISHED = "crew_finished"
    # Scoring
    FUSION_STARTED = "fusion_started"
    FUSION_FINISHED = "fusion_finished"


@dataclass
class PipelineEvent:
    """Immutable event published during pipeline execution."""
    event_type: PipelineEventType
    document_id: str = ""
    correlation_id: str = ""
    stage_name: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# Type alias for subscribers
EventHandler = Callable[[PipelineEvent], None]


class PipelineEventBus:
    """Simple pub/sub event bus for pipeline observability.

    Usage:
        bus = PipelineEventBus()
        bus.subscribe(lambda event: log.info("Event: %s", event.event_type))
        bus.publish(PipelineEvent(PipelineEventType.STAGE_STARTED, stage_name="Ingest"))
    """

    def __init__(self):
        self._subscribers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        """Register an event handler. Called for every event."""
        self._subscribers.append(handler)

    def unsubscribe(self, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        if handler in self._subscribers:
            self._subscribers.remove(handler)

    def publish(self, event: PipelineEvent) -> None:
        """Publish an event to all subscribers. Failures are logged, not propagated."""
        for handler in self._subscribers:
            try:
                handler(event)
            except Exception as e:
                logger.warning("Event handler failed for %s: %s", event.event_type.value, e)

    def clear(self) -> None:
        """Remove all subscribers. Useful for testing."""
        self._subscribers.clear()

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


# ── Built-in subscribers ──


def create_logging_subscriber() -> EventHandler:
    """Creates a subscriber that logs all events at DEBUG level."""
    def _log_event(event: PipelineEvent) -> None:
        logger.debug("[EVENT] %s | doc=%s stage=%s data=%s",
                      event.event_type.value, event.document_id[:8],
                      event.stage_name, str(event.data)[:200])
    return _log_event


def create_metrics_subscriber(metrics_registry: Any = None) -> EventHandler:
    """Creates a subscriber that records metrics for each event type."""
    def _record_metric(event: PipelineEvent) -> None:
        # Placeholder for Prometheus metrics integration
        pass
    return _record_metric
