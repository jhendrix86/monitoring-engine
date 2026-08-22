"""
Notification client - sends alerts to notification-engine
"""

import httpx
from typing import Optional, List
from enum import Enum
from loguru import logger

from app.config import settings


class NotificationChannel(str, Enum):
    """Notification channels supported by notification-engine"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    DISCORD = "discord"


async def send_alert_notification(
    alert_id: str,
    alert_title: str,
    alert_message: Optional[str],
    severity: str,
    recipient: str = "admin@company.com",
    channels: Optional[List[NotificationChannel]] = None,
) -> Optional[dict]:
    """
    Send an alert notification via notification-engine
    
    Args:
        alert_id: The ID of the alert
        alert_title: The alert title
        alert_message: Optional alert message/description
        severity: Alert severity (critical, warning, info)
        recipient: Email or other recipient identifier
        channels: List of notification channels (defaults to email)
    
    Returns:
        Notification response dict if successful, None otherwise
    """
    if channels is None:
        channels = [NotificationChannel.EMAIL]
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{settings.notification_engine_url}/notifications/send"
            
            payload = {
                "recipient": recipient,
                "recipient_type": "email",
                "channels": [c.value for c in channels],
                "subject": f"[{severity.upper()}] {alert_title}",
                "message": alert_message or alert_title,
                "data": {
                    "alert_id": alert_id,
                    "severity": severity,
                    "source": "monitoring-engine"
                },
                "alert_id": alert_id
            }
            
            logger.info(f"Sending notification to {url} for alert {alert_id}")
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Notification sent successfully: {result.get('id')}")
            return result
            
    except httpx.HTTPError as e:
        logger.error(f"Failed to send notification for alert {alert_id}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error sending notification for alert {alert_id}: {e}")
        return None