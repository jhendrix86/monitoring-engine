"""
Verifies tenant context assignment for monitoring-engine endpoints.
Tests that apply_tenant_context() correctly assigns tenant_id on create.
Note: Automatic query filtering is not yet implemented - this test validates
create-time tenant assignment only.
"""

from sqlalchemy import select

# Use fixed UUIDs that match what we create in conftest
TENANT_A = "3e2a7c54-a950-48f3-9eb9-d1eb6b2d1be2"
TENANT_B = "00000000-0000-0000-0000-000000000001"


async def test_apply_tenant_context_on_alert_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on alert creation."""
    from app.models.alert import Alert
    import uuid
    
    # Create alert for tenant A
    result = await client.post(
        "/alerts/",
        json={
            "name": "Test Alert",
            "severity": "high",
            "source": "test-service",
            "message": "Test alert message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    alert_id = result.json()["id"]
    
    # Verify tenant_id was correctly assigned
    alert = await db_session.get(Alert, uuid.UUID(alert_id))
    assert alert is not None
    assert str(alert.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_incident_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on incident creation."""
    from app.models.incident import Incident
    import uuid
    
    # Create alert for tenant A
    alert_result = await client.post(
        "/alerts/",
        json={
            "name": "Test Alert",
            "severity": "high",
            "source": "test-service",
            "message": "Test alert message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert alert_result.status_code == 200
    alert_id = alert_result.json()["id"]
    
    # Create incident for tenant A
    incident_result = await client.post(
        "/incidents/",
        json={
            "title": "Test Incident",
            "severity": "critical",
            "alert_id": alert_id
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert incident_result.status_code == 200
    incident_id = incident_result.json()["id"]
    
    # Verify incident tenant_id was correctly assigned
    incident = await db_session.get(Incident, uuid.UUID(incident_id))
    assert incident is not None
    assert str(incident.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_log_entry_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on log entry creation."""
    from app.models.log_entry import LogEntry
    import uuid
    
    # Create log entry for tenant A
    result = await client.post(
        "/logs/",
        json={
            "level": "info",
            "source": "test-service",
            "message": "Test log message"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    
    # Verify log entry tenant_id was correctly assigned
    result = await db_session.execute(select(LogEntry).order_by(LogEntry.created_at.desc()))
    log_entry = result.scalars().first()
    assert log_entry is not None
    assert str(log_entry.tenant_id) == TENANT_A


async def test_apply_tenant_context_on_performance_metric_create(client, db_session):
    """Verify that apply_tenant_context assigns tenant_id on performance metric creation."""
    from app.models.performance_metric import PerformanceMetric
    import uuid
    
    # Create performance metric for tenant A
    result = await client.post(
        "/performance/metrics",
        json={
            "metric_type": "cpu_usage",
            "value": 75.5,
            "source": "test-service"
        },
        headers={"X-Tenant-ID": TENANT_A}
    )
    assert result.status_code == 200
    
    # Verify performance metric tenant_id was correctly assigned
    result = await db_session.execute(select(PerformanceMetric).order_by(PerformanceMetric.created_at.desc()))
    metric = result.scalars().first()
    assert metric is not None
    assert str(metric.tenant_id) == TENANT_A
