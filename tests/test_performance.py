"""performance.py is 100% mock - see tests/test_health.py's module docstring."""

from datetime import datetime

import pytest


async def test_record_metric_returns_submitted_fields(client):
    r = await client.post("/performance/record", json={
        "metric_type": "cpu", "metric_name": "cpu_usage", "value": 45, "unit": "percent",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["metric_name"] == "cpu_usage"
    assert body["value"] == 45


async def test_record_metric_requires_declared_fields(client):
    r = await client.post("/performance/record", json={"metric_type": "cpu"})
    assert r.status_code == 422


async def test_list_metrics_defaults_to_a_1_hour_window(client):
    r = await client.get("/performance/")
    assert r.status_code == 200
    body = r.json()
    start = datetime.fromisoformat(body["period"]["start_date"])
    end = datetime.fromisoformat(body["period"]["end_date"])
    assert (end - start).total_seconds() == pytest.approx(3600, abs=1)


async def test_list_metrics_echoes_filters(client):
    r = await client.get("/performance/", params={"metric_type": "cpu", "service_name": "kg-service"})
    assert r.status_code == 200
    assert r.json()["filters"] == {"metric_type": "cpu", "service_name": "kg-service"}


async def test_get_performance_summary(client):
    r = await client.get("/performance/summary")
    assert r.status_code == 200
    assert "summary" in r.json()
