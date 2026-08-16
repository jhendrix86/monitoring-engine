"""
Verifies tenant isolation for monitoring-engine endpoints.
Tests that automatic query filtering actually isolates data between tenants.
"""

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def _create_alert(client, tenant_id, name):
    resp = await client.post(
        "/alerts/create",
        json={
            "alert_type": "test",
            "severity": "critical",
            "title": name,
            "message": "Test alert message",
            "service_name": "test-service"
        },
        headers={"X-Tenant-ID": tenant_id},
    )
    assert resp.status_code == 200
    return resp.json()["id"]


async def test_tenant_cannot_read_another_tenants_alert(client):
    alert_id = await _create_alert(client, TENANT_A, "Tenant A's Alert")

    # Verify tenant A can see the alert in the list
    a_listing = await client.get("/alerts/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 1

    # Verify tenant B cannot see the alert
    b_listing = await client.get("/alerts/", headers={"X-Tenant-ID": TENANT_B})
    assert b_listing.status_code == 200
    assert b_listing.json()["total"] == 0


async def test_list_alerts_is_scoped_per_tenant(client):
    await _create_alert(client, TENANT_A, "A's Alert 1")
    await _create_alert(client, TENANT_A, "A's Alert 2")
    
    # Verify tenant A sees their alerts
    a_listing = await client.get("/alerts/", headers={"X-Tenant-ID": TENANT_A})
    assert a_listing.status_code == 200
    assert a_listing.json()["total"] == 2


async def test_no_tenant_header_sees_everything(client):
    """Fail-open posture: no X-Tenant-ID means no filtering is applied."""
    await _create_alert(client, TENANT_A, "A's Alert")
    
    # Verify no-tenant header sees the alert
    unscoped = await client.get("/alerts/")
    assert unscoped.status_code == 200
    assert unscoped.json()["total"] == 1


async def test_tenant_cannot_modify_another_tenants_alert(client):
    alert_id = await _create_alert(client, TENANT_A, "Tenant A's Alert")

    # Try to resolve as tenant B
    resolve_response = await client.post(
        f"/alerts/{alert_id}/resolve",
        headers={"X-Tenant-ID": TENANT_B}
    )
    assert resolve_response.status_code == 404


async def test_incident_creation_respects_tenant_scoping(client):
    """Incident creation should be tenant-scoped."""
    # Create incident for tenant A
    incident_resp = await client.post(
        "/incidents/create",
        json={
            "title": "Test Incident",
            "severity": "critical",
            "affected_services": ["test-service"]
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert incident_resp.status_code == 200
    incident_id = incident_resp.json()["id"]

    # Tenant A can see the incident
    a_incident = await client.get(f"/incidents/{incident_id}", headers={"X-Tenant-ID": TENANT_A})
    assert a_incident.status_code == 200

    # Tenant B cannot see the incident
    b_incident = await client.get(f"/incidents/{incident_id}", headers={"X-Tenant-ID": TENANT_B})
    assert b_incident.status_code == 404


async def test_log_entry_respects_tenant_scoping(client):
    """Log entries should be tenant-scoped."""
    # Create log entry for tenant A
    log_resp = await client.post(
        "/logs/",
        json={
            "level": "info",
            "source": "test-service",
            "message": "Test log message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert log_resp.status_code == 200

    # List logs for tenant A
    a_logs = await client.get("/logs/", headers={"X-Tenant-ID": TENANT_A})
    assert a_logs.status_code == 200
    assert a_logs.json()["total"] == 1

    # List logs for tenant B
    b_logs = await client.get("/logs/", headers={"X-Tenant-ID": TENANT_B})
    assert b_logs.status_code == 200
    assert b_logs.json()["total"] == 0
