"""alerts.py is 100% mock - see tests/test_health.py's module docstring."""


async def test_create_alert_returns_submitted_fields(client):
    r = await client.post("/alerts/create", json={
        "alert_type": "high_cpu", "severity": "warning", "title": "CPU above 90%",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "CPU above 90%"
    assert body["status"] == "open"


async def test_create_alert_requires_declared_fields(client):
    r = await client.post("/alerts/create", json={"alert_type": "x"})
    assert r.status_code == 422


async def test_acknowledge_alert(client):
    r = await client.post("/alerts/alert_123/acknowledge", params={"acknowledged_by": "ops-bot"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_by"] == "ops-bot"


async def test_resolve_alert(client):
    r = await client.post("/alerts/alert_123/resolve", params={"resolution_notes": "Scaled up"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


async def test_list_alerts(client):
    r = await client.get("/alerts/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["alerts"])


async def test_list_alerts_echoes_filters(client):
    r = await client.get("/alerts/", params={"severity": "critical", "status": "open"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"severity": "critical", "status": "open", "service_name": None}
