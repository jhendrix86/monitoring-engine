"""logs.py is now real: ingestion persists, listing/search query the database."""

from datetime import datetime

import pytest


async def test_create_log_entry_persists_a_real_row(client):
    r = await client.post("/logs/", json={
        "level": "error", "service_name": "kg-service", "message": "Connection timeout",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["message"] == "Connection timeout"
    assert body["level"] == "error"
    assert body["id"]  # a real generated UUID, not "log_123"


async def test_create_log_entry_requires_declared_fields(client):
    r = await client.post("/logs/", json={"level": "error"})
    assert r.status_code == 422


async def test_create_log_entry_rejects_invalid_level(client):
    r = await client.post("/logs/", json={"level": "not-a-real-level", "message": "x"})
    assert r.status_code == 422


async def test_list_log_entries_defaults_to_a_1_hour_window(client):
    r = await client.get("/logs/")
    assert r.status_code == 200
    body = r.json()
    start = datetime.fromisoformat(body["period"]["start_date"])
    end = datetime.fromisoformat(body["period"]["end_date"])
    assert (end - start).total_seconds() == pytest.approx(3600, abs=1)


async def test_list_log_entries_reflects_real_created_rows(client):
    await client.post("/logs/", json={"level": "info", "message": "one"})
    await client.post("/logs/", json={"level": "error", "message": "two"})

    r = await client.get("/logs/")
    body = r.json()
    assert body["total"] == 2
    assert {e["message"] for e in body["entries"]} == {"one", "two"}


async def test_list_log_entries_filters_by_level_for_real(client):
    await client.post("/logs/", json={"level": "info", "message": "one"})
    await client.post("/logs/", json={"level": "error", "message": "two"})

    r = await client.get("/logs/", params={"level": "error"})
    body = r.json()
    assert body["total"] == 1
    assert body["entries"][0]["message"] == "two"


async def test_search_log_entries_finds_real_persisted_matches(client):
    await client.post("/logs/", json={"level": "error", "message": "Connection timeout on kg-service"})
    await client.post("/logs/", json={"level": "info", "message": "unrelated"})

    r = await client.get("/logs/search", params={"query": "timeout"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"] == "timeout"
    assert body["total"] == 1
    assert "timeout" in body["entries"][0]["message"]


async def test_search_log_entries_requires_query(client):
    r = await client.get("/logs/search")
    assert r.status_code == 422
