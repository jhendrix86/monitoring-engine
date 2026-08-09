"""logs.py is 100% mock - see tests/test_health.py's module docstring."""

from datetime import datetime

import pytest


async def test_create_log_entry_returns_submitted_fields(client):
    r = await client.post("/logs/", json={
        "level": "error", "service_name": "kg-service", "message": "Connection timeout",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Connection timeout"
    assert body["level"] == "error"


async def test_create_log_entry_requires_declared_fields(client):
    r = await client.post("/logs/", json={"level": "error"})
    assert r.status_code == 422


async def test_list_log_entries_defaults_to_a_1_hour_window(client):
    r = await client.get("/logs/")
    assert r.status_code == 200
    body = r.json()
    start = datetime.fromisoformat(body["period"]["start_date"])
    end = datetime.fromisoformat(body["period"]["end_date"])
    assert (end - start).total_seconds() == pytest.approx(3600, abs=1)


async def test_search_log_entries_echoes_query(client):
    r = await client.get("/logs/search", params={"query": "timeout"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "timeout"
    assert "timeout" in body["entries"][0]["message"]


async def test_search_log_entries_requires_query(client):
    r = await client.get("/logs/search")
    assert r.status_code == 422
