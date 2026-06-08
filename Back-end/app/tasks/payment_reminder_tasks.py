# ============================================================
# PaySentinelIQ — Payment Reminder Celery Tasks
# Daily checks for upcoming boleto due dates and user-configured
# reminder frequencies. Sends notifications via the dispatch system.
# ============================================================

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from celery import shared_task
from sqlalchemy import select, and_

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=300,
    name="check_payment_reminders",
)
def check_payment_reminders(self: Any) -> dict[str, Any]:
    """
    Daily task that scans all pending payment schedules and sends
    reminders based on each user's configured reminder preferences.

    Should be scheduled to run once per day (e.g., Celery Beat cron: 0 8 * * *).

    For each user with pending payments, checks:
      - every_2_days: notify if due within 48 hours
      - weekly: notify every 7 days before due date
      - monthly: notify every 30 days before due date
      - on_due_date: notify on the exact due date

    Deduplication: only sends one notification per (schedule, frequency_type)
    per day, tracked via notified_at timestamp.
    """
    logger.info("Starting payment reminder check...")

    try:
        from app.shared.database import AsyncSessionLocal
        from app.shared.orm_models import PaymentScheduleModel, UserSettingsModel

        now = datetime.now(timezone.utc)
        notifications_sent = 0
        schedules_checked = 0

        async def _run():
            nonlocal notifications_sent, schedules_checked
            async with AsyncSessionLocal() as session:
                # Fetch all pending payment schedules
                result = await session.execute(
                    select(PaymentScheduleModel).where(
                        PaymentScheduleModel.status == "pending"
                    )
                )
                schedules = list(result.scalars().all())

                for schedule in schedules:
                    schedules_checked += 1
                    days_until_due = (schedule.due_date.replace(tzinfo=timezone.utc) - now).days

                    # Mark as overdue if past due date
                    if days_until_due < 0:
                        schedule.status = "overdue"
                        session.add(schedule)
                        continue

                    # Skip if already notified today
                    if schedule.notified_at and schedule.notified_at.date() == now.date():
                        continue

                    # Get user's reminder preferences
                    user_settings_result = await session.execute(
                        select(UserSettingsModel).where(
                            UserSettingsModel.user_id == schedule.user_id
                        )
                    )
                    user_settings = user_settings_result.scalar_one_or_none()

                    prefs = {"on_due_date": True}  # default
                    if user_settings and user_settings.reminder_preferences:
                        prefs = user_settings.reminder_preferences

                    should_notify = False
                    reason = ""

                    if prefs.get("on_due_date") and days_until_due == 0:
                        should_notify = True
                        reason = "Vence hoje"
                    elif prefs.get("every_2_days") and days_until_due <= 2 and days_until_due > 0:
                        should_notify = True
                        reason = f"Vence em {days_until_due} dia(s)"
                    elif prefs.get("weekly") and days_until_due <= 7 and days_until_due % 7 == 0 and days_until_due > 0:
                        should_notify = True
                        reason = f"Vence em {days_until_due} dia(s) (lembrete semanal)"
                    elif prefs.get("monthly") and days_until_due <= 30 and days_until_due % 30 == 0 and days_until_due > 0:
                        should_notify = True
                        reason = f"Vence em {days_until_due} dia(s) (lembrete mensal)"

                    if should_notify:
                        # Build notification payload
                        title = f"Pagamento pendente — {reason}"
                        message = (
                            f"Boleto de {schedule.beneficiary or 'beneficiário desconhecido'} "
                            f"no valor de R$ {schedule.amount:,.2f} "
                            f"vence em {schedule.due_date.strftime('%d/%m/%Y')}."
                        )

                        # Create in-app notification via service
                        from app.notifications.services import NotificationService
                        svc = NotificationService(session)
                        await svc.create_notification(
                            user_id=schedule.user_id,
                            tenant_id=schedule.tenant_id,
                            type="payment",
                            title=title,
                            message=message,
                            severity="warning" if days_until_due <= 2 else "normal",
                            action_url="/payroll",
                            metadata={
                                "schedule_id": str(schedule.id),
                                "due_date": schedule.due_date.isoformat(),
                                "amount": schedule.amount,
                                "beneficiary": schedule.beneficiary,
                                "days_until_due": days_until_due,
                            },
                        )

                        # Mark as notified
                        schedule.notified_at = now
                        session.add(schedule)
                        notifications_sent += 1

                        logger.info(
                            "Payment reminder sent to user %s: %s — %s",
                            schedule.user_id, schedule.beneficiary, reason,
                        )

                await session.commit()

        import asyncio
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_run())
        finally:
            loop.close()

        return {
            "status": "completed",
            "schedules_checked": schedules_checked,
            "notifications_sent": notifications_sent,
            "timestamp": now.isoformat(),
        }

    except Exception as exc:
        logger.error("Payment reminder check failed: %s", exc)
        raise self.retry(exc=exc) from exc
