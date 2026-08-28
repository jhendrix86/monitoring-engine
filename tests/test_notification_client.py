"""
send_alert_notification() wires real alerts to notification-engine's real
delivery pipeline. NOTIFICATION_ENGINE_URL existed as config with zero real
call sites for a while; the first real wiring attempt sent monitoring-engine's
own alert id straight to notification-engine's /notifications/send, which
404s for real (confirmed against the live containers) since notification-engine
resolves alert_id against its own, separate alerts table. This suite covers
the fixed two-call version: mirror via /alerts/create first, then send.
"""

import json

import respx
from httpx import Response

import app.config as config_module
from app.services.notification_client import send_alert_notification


async def test_send_alert_notification_is_a_real_honest_noop_when_unconfigured(monkeypatch):
    monkeypatch.setattr(config_module.settings, "alert_notification_recipient", "")

    with respx.mock:
        # No routes registered at all - any real HTTP call would raise
        # respx.NotMockedError. If the function stays quiet, this passes.
        result = await send_alert_notification(
            alert_id="11111111-1111-1111-1111-111111111111",
            alert_title="CPU above 90%",
            alert_message="CPU at 95%",
            severity="critical",
        )
        assert result is None


async def test_send_alert_notification_mirrors_then_sends_for_real(monkeypatch):
    monkeypatch.setattr(config_module.settings, "alert_notification_recipient", "ops@example.com")
    monkeypatch.setattr(config_module.settings, "notification_engine_url", "http://notification-engine:8037")

    with respx.mock:
        create_route = respx.post("http://notification-engine:8037/alerts/create").mock(
            return_value=Response(200, json={"id": "22222222-2222-2222-2222-222222222222"})
        )
        send_route = respx.post("http://notification-engine:8037/notifications/send").mock(
            return_value=Response(200, json={"id": "n1", "status": "sent"})
        )

        result = await send_alert_notification(
            alert_id="11111111-1111-1111-1111-111111111111",
            alert_title="CPU above 90%",
            alert_message="CPU at 95%",
            severity="critical",
        )

        assert result == {"id": "n1", "status": "sent"}

        assert create_route.called
        create_payload = json.loads(create_route.calls[0].request.content)
        assert create_payload["source"] == "monitoring-engine"
        assert create_payload["priority"] == "critical"
        assert create_payload["title"] == "CPU above 90%"
        assert create_payload["metadata"]["monitoring_engine_alert_id"] == "11111111-1111-1111-1111-111111111111"

        assert send_route.called
        send_payload = json.loads(send_route.calls[0].request.content)
        assert send_payload["recipient"] == "ops@example.com"
        assert send_payload["channels"] == ["email"]
        # Must use notification-engine's OWN id from /alerts/create, not
        # monitoring-engine's - this is the exact bug that made every real
        # send 404 before the fix.
        assert send_payload["alert_id"] == "22222222-2222-2222-2222-222222222222"
        assert "[CRITICAL]" in send_payload["subject"]


async def test_send_alert_notification_mirror_failure_is_non_fatal(monkeypatch):
    """A real, unreachable/erroring notification-engine must not raise - the
    caller (alert creation) has already succeeded and must not be undone."""
    monkeypatch.setattr(config_module.settings, "alert_notification_recipient", "ops@example.com")
    monkeypatch.setattr(config_module.settings, "notification_engine_url", "http://notification-engine:8037")

    with respx.mock:
        respx.post("http://notification-engine:8037/alerts/create").mock(
            return_value=Response(500, json={"detail": "boom"})
        )

        result = await send_alert_notification(
            alert_id="11111111-1111-1111-1111-111111111111",
            alert_title="CPU above 90%",
            alert_message="CPU at 95%",
            severity="critical",
        )
        assert result is None


async def test_severity_mapping_covers_every_alertseverity_value():
    """Every AlertSeverity must map to a real notification-engine AlertPriority
    string - a missing entry would KeyError the first time that severity's
    alert was ever created, not at import time."""
    from app.models.alert import AlertSeverity
    from app.services.notification_client import _TO_NOTIFICATION_PRIORITY

    for severity in AlertSeverity:
        assert severity in _TO_NOTIFICATION_PRIORITY
        assert _TO_NOTIFICATION_PRIORITY[severity] in {"critical", "high", "warning", "info", "debug"}
