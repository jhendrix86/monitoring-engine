"""
Notification client - sends alerts to notification-engine

notification-engine keeps its own local `alerts` table in a separate
database - there is no cross-service foreign key. Wiring a monitoring-engine
alert to a real notification therefore means two real calls, not one: first
mirror the alert into notification-engine's own table via `POST
/alerts/create` (source="monitoring-engine") to get a real, resolvable id on
that side, then send a real notification linked to *that* id via `POST
/notifications/send`. Sending monitoring-engine's own alert id directly to
`/notifications/send` was tried first and confirmed broken against the real
running containers: notification-engine's `_resolve_alert` looks the id up
in its own `alerts` table and 404s, since that table has never heard of it -
every notification silently failed even though alert creation "succeeded".
"""

from typing import Optional, List
from enum import Enum

import httpx
from loguru import logger

from app.config import settings
from app.models.alert import AlertSeverity


class NotificationChannel(str, Enum):
    """Notification channels supported by notification-engine"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DISCORD = "discord"


# monitoring-engine's AlertSeverity (4 levels) -> notification-engine's
# AlertPriority (5 levels, different vocabulary - no shared severity_mapping
# module exists on notification-engine's side yet, a separate real gap).
# Direct name mapping: INFO/WARNING are exact matches; ERROR -> HIGH since
# there's no "error" tier on the other side and HIGH is the closest level
# above WARNING; CRITICAL -> CRITICAL. Priority's DEBUG tier has no reachable
# source here - AlertSeverity has nothing below INFO.
_TO_NOTIFICATION_PRIORITY = {
    AlertSeverity.INFO: "info",
    AlertSeverity.WARNING: "warning",
    AlertSeverity.ERROR: "high",
    AlertSeverity.CRITICAL: "critical",
}


async def send_alert_notification(
    alert_id: str,
    alert_title: str,
    alert_message: Optional[str],
    severity: str,
    recipient: Optional[str] = None,
    channels: Optional[List[NotificationChannel]] = None,
) -> Optional[dict]:
    """
    Mirror the alert into notification-engine and send a real notification
    for it. Never raises - a delivery failure here must not fail the alert
    creation that triggered it.

    `recipient` defaults to `settings.alert_notification_recipient`, which is
    empty until explicitly configured - an honest no-op (matching this
    fleet's "unconfigured = quiet skip" convention, see notification-engine's
    own delivery clients' `configured` gates) rather than a hardcoded
    real-looking address that would silently swallow every real send.
    """
    recipient = recipient or settings.alert_notification_recipient
    if not recipient:
        logger.debug(f"Alert notification skipped for {alert_id}: no recipient configured")
        return None

    if channels is None:
        channels = [NotificationChannel.EMAIL]

    priority = _TO_NOTIFICATION_PRIORITY.get(AlertSeverity(severity), "info")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            create_resp = await client.post(
                f"{settings.notification_engine_url}/alerts/create",
                json={
                    "source": "monitoring-engine",
                    "alert_type": "monitoring_alert",
                    "priority": priority,
                    "title": alert_title,
                    "description": alert_message or alert_title,
                    "metadata": {"monitoring_engine_alert_id": alert_id},
                },
            )
            create_resp.raise_for_status()
            remote_alert_id = create_resp.json()["id"]

            send_resp = await client.post(
                f"{settings.notification_engine_url}/notifications/send",
                json={
                    "recipient": recipient,
                    "recipient_type": "email",
                    "channels": [c.value for c in channels],
                    "subject": f"[{severity.upper()}] {alert_title}",
                    "message": alert_message or alert_title,
                    "data": {
                        "alert_id": alert_id,
                        "severity": severity,
                        "source": "monitoring-engine",
                    },
                    "alert_id": remote_alert_id,
                },
            )
            send_resp.raise_for_status()

            result = send_resp.json()
            logger.info(f"Notification sent for alert {alert_id}: {result.get('id')}")
            return result

    except httpx.HTTPError as e:
        logger.error(f"Failed to send notification for alert {alert_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending notification for alert {alert_id}: {e}")
        return None
