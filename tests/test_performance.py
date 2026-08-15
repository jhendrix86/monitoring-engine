"""
performance.py is now real: recording/listing hit performance_metrics
for real, and /summary computes real averages from the last hour of
recorded data (no fabricated constants).
"""

from datetime import datetime

import pytest

from app.models.health_check import HealthCheck, HealthStatus


async def test_record_metric_persists_a_real_row(client):
    r = await client.post("/performance/record", json={
        "metric_type": "cpu", "metric_name": "cpu_usage", "value": 45.5, "unit": "percent",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["metric_name"] == "cpu_usage"
    assert body["value"] == 45.5
    assert body["id"]  # a real generated UUID, not "metric_123"


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


async def test_list_metrics_reflects_real_recorded_rows(client):
    await client.post("/performance/record", json={"metric_type": "cpu", "metric_name": "cpu_usage", "value": 10})
    await client.post("/performance/record", json={"metric_type": "memory", "metric_name": "memory_usage", "value": 20})

    r = await client.get("/performance/", params={"metric_type": "cpu"})
    body = r.json()
    assert body["total"] == 1
    assert body["metrics"][0]["metric_name"] == "cpu_usage"


async def test_get_performance_summary_computes_real_averages(client):
    await client.post("/performance/record", json={"metric_type": "cpu", "metric_name": "cpu_usage", "value": 40})
    await client.post("/performance/record", json={"metric_type": "cpu", "metric_name": "cpu_usage", "value": 60})
    await client.post("/performance/record", json={"metric_type": "memory", "metric_name": "memory_usage", "value": 50})

    r = await client.get("/performance/summary")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["avg_cpu_usage"] == 50.0
    assert summary["avg_memory_usage"] == 50.0


async def test_get_performance_summary_with_no_data_is_honest_not_fabricated(client):
    r = await client.get("/performance/summary")
    assert r.status_code == 200
    summary = r.json()["summary"]
    assert summary["avg_cpu_usage"] is None
    assert summary["avg_response_time_ms"] is None
    assert summary["services_reporting"] == 0


async def test_get_performance_summary_counts_services_reporting_from_health_checks(client, db_session):
    db_session.add(HealthCheck(service_name="content-engine", service_type="engine", status=HealthStatus.HEALTHY, response_time_ms=20))
    db_session.add(HealthCheck(service_name="sales-engine", service_type="engine", status=HealthStatus.HEALTHY, response_time_ms=40))
    await db_session.commit()

    r = await client.get("/performance/summary")
    summary = r.json()["summary"]
    assert summary["services_reporting"] == 2
    assert summary["avg_response_time_ms"] == 30.0
