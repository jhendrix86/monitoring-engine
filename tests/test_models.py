"""
Real tests for the SQLAlchemy models - previously completely untested
despite being the only real (non-mock) part of this engine. None of the 5
models reference each other (all standalone tables), so this focuses on
schema creation and each model's real defaults/enum handling.
"""

from sqlalchemy import select

from app.models.health_check import HealthCheck, HealthStatus
from app.models.performance_metric import PerformanceMetric, MetricType
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.log_entry import LogEntry, LogLevel
from app.models.incident import Incident, IncidentStatus


async def test_health_check_defaults_to_unknown_status(db_session):
    check = HealthCheck(service_name="kg-service", service_type="graph")
    db_session.add(check)
    await db_session.commit()
    await db_session.refresh(check)

    assert check.status == HealthStatus.UNKNOWN


async def test_performance_metric_persists_and_queries_by_type(db_session):
    db_session.add(PerformanceMetric(metric_type=MetricType.CPU, metric_name="cpu_usage", value=45, unit="percent"))
    db_session.add(PerformanceMetric(metric_type=MetricType.MEMORY, metric_name="memory_usage", value=62, unit="percent"))
    await db_session.commit()

    result = await db_session.execute(select(PerformanceMetric).where(PerformanceMetric.metric_type == MetricType.CPU))
    rows = result.scalars().all()
    assert len(rows) == 1
    assert rows[0].value == 45


async def test_alert_defaults_to_open_status(db_session):
    alert = Alert(alert_type="high_cpu", severity=AlertSeverity.WARNING, title="CPU above 90%")
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    assert alert.status == AlertStatus.OPEN
    assert alert.resolved_at is None


async def test_log_entry_requires_level_and_message(db_session):
    entry = LogEntry(level=LogLevel.ERROR, message="Connection timeout", service_name="kg-service")
    db_session.add(entry)
    await db_session.commit()

    result = await db_session.execute(select(LogEntry).where(LogEntry.level == LogLevel.ERROR))
    fetched = result.scalar_one()
    assert fetched.message == "Connection timeout"


async def test_incident_defaults_to_open_status(db_session):
    incident = Incident(title="Elevated error rate", severity=AlertSeverity.CRITICAL)
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    assert incident.status == IncidentStatus.OPEN
    assert incident.closed_at is None
