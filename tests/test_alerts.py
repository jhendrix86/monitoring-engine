"""alerts.py is now real: every endpoint reads/writes the alerts table."""


async def _create_alert(client, **overrides):
    payload = {"alert_type": "high_cpu", "severity": "warning", "title": "CPU above 90%"}
    payload.update(overrides)
    r = await client.post("/alerts/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_alert_persists_a_real_row(client):
    body = await _create_alert(client)
    assert body["title"] == "CPU above 90%"
    assert body["status"] == "open"
    assert body["id"]  # a real generated UUID, not "alert_123"


async def test_create_alert_requires_declared_fields(client):
    r = await client.post("/alerts/create", json={"alert_type": "x"})
    assert r.status_code == 422


async def test_create_alert_rejects_invalid_severity(client):
    r = await client.post(
        "/alerts/create",
        json={"alert_type": "x", "severity": "sort of bad", "title": "t"},
    )
    assert r.status_code == 422


async def test_acknowledge_alert_updates_the_real_row(client):
    created = await _create_alert(client)
    r = await client.post(f"/alerts/{created['id']}/acknowledge", params={"acknowledged_by": "ops-bot"})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "acknowledged"
    assert body["acknowledged_by"] == "ops-bot"


async def test_acknowledge_unknown_alert_is_a_real_404(client):
    r = await client.post("/alerts/00000000-0000-0000-0000-000000000000/acknowledge")
    assert r.status_code == 404


async def test_resolve_alert_updates_the_real_row(client):
    created = await _create_alert(client)
    r = await client.post(f"/alerts/{created['id']}/resolve", params={"resolution_notes": "Scaled up"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


async def test_list_alerts_reflects_real_created_rows(client):
    await _create_alert(client, title="one")
    await _create_alert(client, title="two")

    r = await client.get("/alerts/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {a["title"] for a in body["alerts"]} == {"one", "two"}


async def test_list_alerts_filters_by_severity_for_real(client):
    await _create_alert(client, severity="critical", title="crit-one")
    await _create_alert(client, severity="warning", title="warn-one")

    r = await client.get("/alerts/", params={"severity": "critical"})
    body = r.json()
    assert body["total"] == 1
    assert body["alerts"][0]["title"] == "crit-one"
