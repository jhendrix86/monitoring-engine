"""incidents.py is 100% mock - see tests/test_health.py's module docstring."""


async def test_create_incident_returns_submitted_fields(client):
    r = await client.post("/incidents/create", json={
        "title": "Elevated error rate on sales-engine", "severity": "high", "affected_services": ["sales-engine"],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Elevated error rate on sales-engine"
    assert body["status"] == "open"


async def test_create_incident_requires_declared_fields(client):
    r = await client.post("/incidents/create", json={"title": "x"})
    assert r.status_code == 422


async def test_resolve_incident(client):
    r = await client.post("/incidents/incident_123/resolve", params={"resolution_notes": "Rolled back deploy"})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


async def test_get_incident(client):
    r = await client.get("/incidents/incident_123")
    assert r.status_code == 200
    assert r.json()["id"] == "incident_123"


async def test_list_incidents(client):
    r = await client.get("/incidents/")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["incidents"])


async def test_list_incidents_echoes_filters(client):
    r = await client.get("/incidents/", params={"status": "investigating", "severity": "high"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"status": "investigating", "severity": "high"}
