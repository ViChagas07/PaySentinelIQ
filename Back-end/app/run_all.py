# ============================================================
# PaySentinelIQ — Unified Entrypoint (API + Workers + Scheduler)
# ============================================================
# Single-process runner for Koyeb free tier (1 service limit).
# Starts:
#   - FastAPI app (uvicorn)
#   - Audit worker consumer
#   - Notification worker consumer
#   - Email worker consumer
#   - Bill due-soon scheduler
# ============================================================

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn

from app.main import create_app
from app.messaging.application.bill_scheduler import BillDueSoonScheduler
from app.messaging.application.handlers import (
    AuditEventHandler,
    EmailEventHandler,
    NotificationEventHandler,
)
from app.messaging.infrastructure.factory import close_event_publisher, get_event_publisher
from app.messaging.infrastructure.rabbitmq_consumer import RabbitMQEventConsumer
from app.messaging.infrastructure.rabbitmq_topology import (
    AUDIT_QUEUE,
    EMAIL_QUEUE,
    NOTIFICATIONS_QUEUE,
)
from app.shared.settings import get_settings

settings = get_settings()

# ── Logging ──────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

# ── Global state ─────────────────────────────────────────────
_consumers: list[RabbitMQEventConsumer] = []
_scheduler_task: asyncio.Task | None = None
_app: uvicorn.Server | None = None


# ── Lifecycle ────────────────────────────────────────────────
async def start_consumers() -> None:
    """Start all RabbitMQ consumers."""
    global _consumers

    publisher = get_event_publisher()

    handlers_and_queues = [
        (AuditEventHandler(), AUDIT_QUEUE, "audit"),
        (NotificationEventHandler(publisher=publisher), NOTIFICATIONS_QUEUE, "notifications"),
        (EmailEventHandler(), EMAIL_QUEUE, "email"),
    ]

    for handler, queue_name, name in handlers_and_queues:
        consumer = RabbitMQEventConsumer(
            queue_name,
            handler,
            consumer_name=f"{name}-worker",
        )
        _consumers.append(consumer)
        await consumer.start()
        logger.info("Started %s consumer on %s", name, queue_name)


async def stop_consumers() -> None:
    """Gracefully stop all consumers."""
    global _consumers

    for consumer in _consumers:
        try:
            await consumer.stop()
            logger.info("Stopped consumer %s", consumer.consumer_name)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error stopping consumer %s: %s", consumer.consumer_name, exc)

    _consumers.clear()
    await close_event_publisher()


async def run_scheduler() -> None:
    """Run the bill due-soon scheduler loop."""
    scheduler = BillDueSoonScheduler()

    while True:
        try:
            stats = await scheduler.run_once()
            logger.info(
                "Scheduler run: checked=%d, due_soon=%d, overdue=%d",
                stats["schedules_checked"],
                stats["due_soon_events"],
                stats["overdue_events"],
            )
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Scheduler error: %s", exc)

        settings = get_settings()
        await asyncio.sleep(settings.BILL_SCHEDULER_INTERVAL_SECONDS)


async def run_all() -> None:
    """Main entrypoint: starts API + consumers + scheduler."""
    global _app, _scheduler_task

    # 1. Create FastAPI app
    app = create_app()

    # 2. Start consumers (if RabbitMQ enabled)
    if settings.RABBITMQ_ENABLED:
        await start_consumers()
        logger.info("All RabbitMQ consumers started")
    else:
        logger.warning("RABBITMQ_ENABLED=false — consumers not started")

    # 3. Start scheduler (if enabled)
    if settings.BILL_SCHEDULER_ENABLED:
        _scheduler_task = asyncio.create_task(run_scheduler())
        logger.info("Bill scheduler started")
    else:
        logger.info("BILL_SCHEDULER_ENABLED=false — scheduler not started")

    # 4. Run uvicorn
    config = uvicorn.Config(
        app,
        host=settings.HOST,
        port=settings.PORT,
        loop="asyncio",
        log_level=settings.LOG_LEVEL.lower(),
        # Disable uvicorn's own signal handlers — we handle them
        lifespan="off",
    )
    global _app
    _app = uvicorn.Server(config)

    # 5. Setup signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except (NotImplementedError, RuntimeError):  # pragma: no cover (Windows)
            pass

    # 6. Run server + wait for stop
    server_task = asyncio.create_task(_app.serve())

    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down...")
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

        if _scheduler_task:
            _scheduler_task.cancel()
            try:
                await _scheduler_task
            except asyncio.CancelledError:
                pass

        await stop_consumers()
        logger.info("Shutdown complete")


# ── Entrypoint ───────────────────────────────────────────────

if __name__ == "__main__":
    if settings.RABBITMQ_ENABLED:
        logger.info("Starting PaySentinelIQ (API + Workers + Scheduler)")
    else:
        logger.info("Starting PaySentinelIQ (API only — RABBITMQ_ENABLED=false)")

    asyncio.run(run_all())