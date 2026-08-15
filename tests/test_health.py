"""
health.py is now real: /system and /services read persisted HealthCheck
rows from the database (real SQL, deduped to the latest per service);
/{service_id} does a real, live HTTP poll via app/health_poller.py and
persists the result before returning it.
"""

from app.models.health_check import HealthCheck, HealthStatus


async def test_system_health_with_no_checks_yet_reports_unknown(client):
    r = await client.get("/health/system")
    assert r.status_code == 200
    body = r.json()
    assert body["overall_status"] == "unknown"
    assert body["services"] == {}


async def test_system_health_aggregates_real_persisted_checks(client, db_session):
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.HEALTHY))
    db_session.add(HealthCheck(service_name="sales-engine", service_type="engine", status=HealthStatus.HEALTHY))
    await db_session.commit()

    r = await client.get("/health/system")
    body = r.json()
    assert body["overall_status"] == "healthy"
    assert set(body["services"].keys()) == {"content-engine", "sales-engine"}


async def test_system_health_is_unhealthy_if_any_service_is_unhealthy(client, db_session):
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.HEALTHY))
    db_session.add(HealthCheck(service_name="sales-engine", service_type="engine", status=HealthStatus.UNHEALTHY))
    await db_session.commit()

    r = await client.get("/health/system")
    assert r.json()["overall_status"] == "unhealthy"


async def test_system_health_uses_only_the_latest_check_per_service(client, db_session):
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.UNHEALTHY))
    await db_session.commit()
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.HEALTHY))
    await db_session.commit()

    r = await client.get("/health/system")
    body = r.json()
    assert body["overall_status"] == "healthy"
    assert body["services"]["content-engine"]["status"] == "healthy"


async def test_get_service_health_lists_latest_persisted_checks(client, db_session):
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.HEALTHY, response_time_ms=12))
    await db_session.commit()

    r = await client.get("/health/services")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["services"][0]["service_name"] == "content-engine"
    assert body["services"][0]["response_time_ms"] == 12


async def test_get_service_health_detail_rejects_unknown_service(client):
    r = await client.get("/health/not-a-real-service")
    assert r.status_code == 404


async def test_get_service_health_detail_really_polls_and_honestly_fails_when_unreachable(client, db_session):
    # No real content-engine is running in the test environment - this is
    # a real HTTP attempt, not a stub, so an honest UNHEALTHY/error result
    # (not a fabricated "healthy") is the correct, expected outcome.
    r = await client.get("/health/content-engine")
    assert r.status_code == 200
    body = r.json()
    assert body["service_name"] == "content-engine"
    assert body["status"] == "unhealthy"
    assert body["error_message"] is not None

    # And it was actually persisted, not just returned.
    from sqlalchemy import select

    result = await db_session.execute(select(HealthCheck).where(HealthCheck.service_name == "content-engine"))
    assert result.scalars().first() is not None
