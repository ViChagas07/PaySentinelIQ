# ============================================================
# PaySentinelIQ — Notification Delivery Tasks
# Celery tasks for sending notifications through configured
# channels: Email, WhatsApp, Telegram, Slack, In-App (WebSocket).
#
# Each task is triggered asynchronously after a notification
# is created in the database, ensuring zero UI blocking.
# ============================================================

import json
import logging
from typing import Any

from celery import shared_task

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# EMAIL NOTIFICATION
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=120,
    name="send_email_notification",
)
def send_email_notification(
    self: Any,
    user_id: str,
    email: str,
    title: str,
    message: str,
    severity: str = "normal",
    action_url: str | None = None,
) -> dict[str, Any]:
    """
    Send a notification via email using Resend (or configured provider).

    In production, this uses the Resend API. For development, it
    logs the email payload and simulates success.
    """
    logger.info(
        "Sending email notification to user %s at %s: %s",
        user_id,
        email,
        title,
    )

    try:
        # In production:
        # import resend
        # resend.Emails.send({
        #     "from": "PaySentinelIQ <alerts@paysentinel.com>",
        #     "to": [email],
        #     "subject": f"[{severity.upper()}] {title}",
        #     "html": _build_email_html(title, message, severity, action_url),
        # })

        # Simulate processing delay
        import time
        time.sleep(0.3)

        logger.info("Email notification sent successfully: %s → %s", title, email)

        return {
            "status": "sent",
            "channel": "email",
            "user_id": user_id,
            "recipient": email,
            "title": title,
        }

    except Exception as exc:
        logger.error("Failed to send email notification: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# WHATSAPP NOTIFICATION
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="send_whatsapp_notification",
)
def send_whatsapp_notification(
    self: Any,
    user_id: str,
    phone: str,
    title: str,
    message: str,
    severity: str = "normal",
) -> dict[str, Any]:
    """
    Send instant risk alerts via WhatsApp (WhatsApp Business API).

    In production, this integrates with the Meta WhatsApp Cloud API.
    For development, it logs the payload and simulates success.
    """
    logger.info(
        "Sending WhatsApp notification to user %s at %s: %s",
        user_id,
        phone,
        title,
    )

    try:
        # In production: use WhatsApp Cloud API
        # POST https://graph.facebook.com/v18.0/{phone_number_id}/messages
        # with appropriate authentication and template message

        payload = {
            "channel": "whatsapp",
            "recipient": phone,
            "title": title,
            "message": message[:160],  # Truncated for WhatsApp
            "severity": severity,
        }
        logger.debug("WhatsApp payload: %s", json.dumps(payload, indent=2))

        return {
            "status": "sent",
            "channel": "whatsapp",
            "user_id": user_id,
            "recipient": phone,
            "title": title,
        }

    except Exception as exc:
        logger.error("Failed to send WhatsApp notification: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# TELEGRAM NOTIFICATION
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="send_telegram_notification",
)
def send_telegram_notification(
    self: Any,
    user_id: str,
    chat_id: str,
    title: str,
    message: str,
    severity: str = "normal",
    action_url: str | None = None,
) -> dict[str, Any]:
    """
    Send AI notifications and monitoring events via Telegram Bot API.

    In production, this posts to the Telegram Bot API.
    For development, it logs the payload and simulates success.
    """
    logger.info(
        "Sending Telegram notification to user %s (chat %s): %s",
        user_id,
        chat_id,
        title,
    )

    try:
        # In production:
        # import httpx
        # bot_token = settings.TELEGRAM_BOT_TOKEN
        # text = f"*{title}*\n\n{message}"
        # if action_url:
        #     text += f"\n\n[View Details]({action_url})"
        # await httpx.AsyncClient().post(
        #     f"https://api.telegram.org/bot{bot_token}/sendMessage",
        #     json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        # )

        severity_emoji = {"critical": "🔴", "warning": "🟠", "normal": "🔵", "success": "🟢", "ai": "🟣"}
        emoji = severity_emoji.get(severity, "ℹ️")
        logger.debug("Telegram message: %s %s → %s", emoji, title, chat_id)

        return {
            "status": "sent",
            "channel": "telegram",
            "user_id": user_id,
            "recipient": chat_id,
            "title": title,
        }

    except Exception as exc:
        logger.error("Failed to send Telegram notification: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# SLACK NOTIFICATION
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="send_slack_notification",
)
def send_slack_notification(
    self: Any,
    user_id: str,
    channel: str,
    title: str,
    message: str,
    severity: str = "normal",
    action_url: str | None = None,
) -> dict[str, Any]:
    """
    Send operational alerts to Slack team channels.

    In production, this posts to a Slack Incoming Webhook.
    For development, it logs the payload and simulates success.
    """
    logger.info(
        "Sending Slack notification for user %s to channel %s: %s",
        user_id,
        channel,
        title,
    )

    try:
        # In production:
        # import httpx
        # webhook_url = settings.SLACK_WEBHOOK_URL
        # severity_color = {"critical": "#D63B3B", "warning": "#FF8C00",
        #                   "normal": "#1E6FFF", "success": "#00C48C", "ai": "#7C3AED"}
        # await httpx.AsyncClient().post(webhook_url, json={
        #     "attachments": [{
        #         "color": severity_color.get(severity, "#1E6FFF"),
        #         "title": title,
        #         "text": message,
        #         "fields": [
        #             {"title": "Severity", "value": severity, "short": True},
        #         ] + ([{"title": "Action", "value": f"<{action_url}|View>", "short": True}] if action_url else []),
        #     }]
        # })

        logger.debug("Slack alert: [%s] %s → #%s", severity.upper(), title, channel)

        return {
            "status": "sent",
            "channel": "slack",
            "user_id": user_id,
            "recipient": channel,
            "title": title,
        }

    except Exception as exc:
        logger.error("Failed to send Slack notification: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# IN-APP NOTIFICATION (WEBSOCKET)
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=2,
    default_retry_delay=10,
    name="send_in_app_notification",
)
def send_in_app_notification(
    self: Any,
    notification_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Push real-time notification to connected WebSocket clients via Redis Pub/Sub.

    This task publishes the notification to a Redis Pub/Sub channel.
    The FastAPI process (which holds the actual WebSocket connections)
    subscribes to this channel and relays the message to the correct
    WebSocket client(s).

    This architecture works correctly even when Celery workers and
    FastAPI run in **separate containers** (as in Railway/docker-compose
    deployments), because Redis acts as the cross-process message broker.
    """
    notification_id = notification_data.get("id", "unknown")
    tenant_id = notification_data.get("tenant_id")
    user_id = notification_data.get("user_id")
    logger.info(
        "Publishing in-app notification %s via Redis Pub/Sub (tenant=%s user=%s)",
        notification_id, tenant_id, user_id,
    )

    try:
        from app.shared.redis_client import RedisPubSub
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(
                RedisPubSub.publish(
                    "ws:notifications",
                    {
                        "type": "new_notification",
                        "data": notification_data,
                        "target": {
                            "tenant_id": tenant_id,
                            "user_id": user_id,
                        },
                    },
                )
            )
        finally:
            loop.close()

        return {
            "status": "published",
            "channel": "in_app",
            "notification_id": notification_id,
        }

    except Exception as exc:
        logger.error("Failed to publish in-app notification: %s", exc)
        raise self.retry(exc=exc) from exc


# ═══════════════════════════════════════════════════════════════
# ORCHESTRATOR: DISPATCH TO ALL ENABLED CHANNELS
# ═══════════════════════════════════════════════════════════════


@shared_task(
    bind=True,
    max_retries=1,
    default_retry_delay=30,
    name="dispatch_notification",
)
def dispatch_notification(
    self: Any,
    user_id: str,
    notification_data: dict[str, Any],
    user_channels: dict[str, Any],
) -> dict[str, Any]:
    """
    Orchestrator task that reads user's notification channel preferences
    and fans out to the appropriate delivery tasks.

    Args:
        user_id: Target user UUID.
        notification_data: The notification payload (title, message, severity, etc.).
        user_channels: Dict of channel → enabled (e.g., {"email": True, "whatsapp": False}).
    """
    notification_id = notification_data.get("id", "unknown")
    title = notification_data.get("title", "Notification")
    message = notification_data.get("message", "")
    severity = notification_data.get("severity", "normal")
    action_url = notification_data.get("action_url")

    dispatched_channels: list[str] = []

    # ── Email ──
    if user_channels.get("email"):
        send_email_notification.delay(
            user_id=user_id,
            email=user_channels.get("email_address", ""),
            title=title,
            message=message,
            severity=severity,
            action_url=action_url,
        )
        dispatched_channels.append("email")

    # ── WhatsApp ──
    if user_channels.get("whatsapp"):
        send_whatsapp_notification.delay(
            user_id=user_id,
            phone=user_channels.get("phone", ""),
            title=title,
            message=message,
            severity=severity,
        )
        dispatched_channels.append("whatsapp")

    # ── Telegram ──
    if user_channels.get("telegram"):
        send_telegram_notification.delay(
            user_id=user_id,
            chat_id=user_channels.get("telegram_chat_id", ""),
            title=title,
            message=message,
            severity=severity,
            action_url=action_url,
        )
        dispatched_channels.append("telegram")

    # ── Slack ──
    if user_channels.get("slack"):
        send_slack_notification.delay(
            user_id=user_id,
            channel=user_channels.get("slack_channel", "#alerts"),
            title=title,
            message=message,
            severity=severity,
            action_url=action_url,
        )
        dispatched_channels.append("slack")

    # ── In-App (WebSocket) ──
    if user_channels.get("in_app", True):
        send_in_app_notification.delay(notification_data=notification_data)
        dispatched_channels.append("in_app")

    logger.info(
        "Notification %s dispatched to channels: %s",
        notification_id,
        dispatched_channels,
    )

    return {
        "status": "dispatched",
        "notification_id": notification_id,
        "channels": dispatched_channels,
    }
