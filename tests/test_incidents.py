"""
incidents.py is now real: every endpoint reads/writes the incidents
table. Incident.severity was also fixed this session from an unvalidated
free-text string to the real AlertSeverity enum (info/warning/error/
critical) - "high"/"medium" are no longer accepted, matching alerts.py's
severity vocabulary.
"""


async def _create_incident(client, **overrides):
    payload = {
        "title": "Elevated error rate on sales-engine",
        "severity": "critical",
        "affected_services": ["sales-engine"],
    }
    payload.update(overrides)
    r = await client.post("/incidents/create", json=payload)
    assert r.status_code == 200
    return r.json()


async def test_create_incident_persists_a_real_row(client):
    body = await _create_incident(client)
    assert body["title"] == "Elevated error rate on sales-engine"
    assert body["status"] == "open"
    assert body["id"]  # a real generated UUID, not "incident_123"


async def test_create_incident_requires_declared_fields(client):
    r = await client.post("/incidents/create", json={"title": "x"})
    assert r.status_code == 422


async def test_create_incident_rejects_invalid_severity(client):
    r = await client.post("/incidents/create", json={"title": "x", "severity": "high"})
    assert r.status_code == 422


async def test_resolve_incident_updates_the_real_row(client):
    created = await _create_incident(client)
    r = await client.post(f"/incidents/{created['id']}/resolve", params={"resolution_notes": "Rolled back deploy"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


async def test_resolve_unknown_incident_is_a_real_404(client):
    r = await client.post("/incidents/00000000-0000-0000-0000-000000000000/resolve")
    assert r.status_code == 404


async def test_get_incident_returns_the_real_row(client):
    created = await _create_incident(client)
    r = await client.get(f"/incidents/{created['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


async def test_get_unknown_incident_is_a_real_404(client):
    r = await client.get("/incidents/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404


async def test_list_incidents_reflects_real_created_rows(client):
    await _create_incident(client, title="one")
    await _create_incident(client, title="two")

    r = await client.get("/incidents/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    assert {i["title"] for i in body["incidents"]} == {"one", "two"}


async def test_list_incidents_filters_by_status_and_severity_for_real(client):
    await _create_incident(client, severity="critical", title="crit-one")
    await _create_incident(client, severity="warning", title="warn-one")

    r = await client.get("/incidents/", params={"severity": "critical"})
    body = r.json()
    assert body["total"] == 1
    assert body["incidents"][0]["title"] == "crit-one"
