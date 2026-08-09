"""health.py is 100% mock - every endpoint documents "In production, this
would... For now, return a mock response" and never touches the database."""


async def test_get_system_health(client):
    r = await client.get("/health/system")
    assert r.status_code == 200
    body = r.json()
    assert body["overall_status"] == "healthy"
    assert "monitoring-engine" in body["services"]


async def test_get_service_health(client):
    r = await client.get("/health/services")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == len(body["services"])


async def test_get_service_health_detail(client):
    r = await client.get("/health/pricing-intelligence")
    assert r.status_code == 200
    assert r.json()["service_name"] == "pricing-intelligence"
