"""
drift_monitor.run_drift_check is real: it aggregates recorded
performance_metrics / health_checks over a current vs baseline window,
runs the pair through the empire-operators DriftMonitor, and opens a real
`performance_drift` Alert row only when a metric has actually moved past
threshold. Flat or absent data is an honest no-op, and it won't stack a
second alert while one is still open.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.drift_monitor import DRIFT_ALERT_TYPE, run_drift_check
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.health_check import HealthCheck, HealthStatus
from app.models.performance_metric import MetricType, PerformanceMetric

NOW = datetime.utcnow()
IN_CURRENT_WINDOW = NOW - timedelta(minutes=10)   # < 1h ago
IN_BASELINE_WINDOW = NOW - timedelta(hours=5)     # between 1h and 24h ago


def _cpu(value: float, when: datetime) -> PerformanceMetric:
    return PerformanceMetric(
        metric_type=MetricType.CPU,
        metric_name="cpu_usage",
        value=value,
        unit="percent",
        service_name="monitoring-engine",
        collected_at=when,
    )


async def _open_drift_alerts(db) -> int:
    return await db.scalar(
        select(func.count(Alert.id)).where(
            Alert.alert_type == DRIFT_ALERT_TYPE, Alert.status == AlertStatus.OPEN
        )
    )


async def test_no_recorded_data_is_a_noop(db_session):
    result = await run_drift_check(db_session)
    assert result is None
    assert await _open_drift_alerts(db_session) == 0


async def test_flat_metrics_do_not_open_an_alert(db_session):
    for v in (49.0, 51.0):
        db_session.add(_cpu(v, IN_BASELINE_WINDOW))
    for v in (50.0, 52.0):
        db_session.add(_cpu(v, IN_CURRENT_WINDOW))
    await db_session.commit()

    result = await run_drift_check(db_session)
    assert result is None
    assert await _open_drift_alerts(db_session) == 0


async def test_synthetic_drift_opens_one_real_alert(db_session):
    # baseline avg CPU 40, current avg CPU 80 -> 100% deviation, past the
    # operator's 20% threshold.
    for v in (38.0, 42.0):
        db_session.add(_cpu(v, IN_BASELINE_WINDOW))
    for v in (78.0, 82.0):
        db_session.add(_cpu(v, IN_CURRENT_WINDOW))
    await db_session.commit()

    alert = await run_drift_check(db_session)

    assert alert is not None
    assert alert.alert_type == DRIFT_ALERT_TYPE
    assert alert.severity == AlertSeverity.WARNING
    assert alert.status == AlertStatus.OPEN
    assert alert.extra_metadata["drift_deviations"] == {"avg_cpu_usage": 100.0}
    assert alert.extra_metadata["current_metrics"]["avg_cpu_usage"] == 80.0
    assert alert.extra_metadata["baseline_metrics"]["avg_cpu_usage"] == 40.0
    assert await _open_drift_alerts(db_session) == 1


async def test_drift_alert_is_not_stacked_while_one_is_open(db_session):
    for v in (38.0, 42.0):
        db_session.add(_cpu(v, IN_BASELINE_WINDOW))
    for v in (78.0, 82.0):
        db_session.add(_cpu(v, IN_CURRENT_WINDOW))
    await db_session.commit()

    first = await run_drift_check(db_session)
    second = await run_drift_check(db_session)

    assert first is not None
    assert second is None
    assert await _open_drift_alerts(db_session) == 1


async def test_resolving_the_alert_lets_a_new_one_open(db_session):
    for v in (38.0, 42.0):
        db_session.add(_cpu(v, IN_BASELINE_WINDOW))
    for v in (78.0, 82.0):
        db_session.add(_cpu(v, IN_CURRENT_WINDOW))
    await db_session.commit()

    first = await run_drift_check(db_session)
    first.status = AlertStatus.RESOLVED
    await db_session.commit()

    second = await run_drift_check(db_session)
    assert second is not None
    assert second.id != first.id


async def test_metric_with_data_on_only_one_side_is_ignored(db_session):
    # CPU only in the current window, memory only in the baseline window:
    # no metric has data on both sides, so there's nothing to compare.
    db_session.add(_cpu(90.0, IN_CURRENT_WINDOW))
    db_session.add(
        PerformanceMetric(
            metric_type=MetricType.MEMORY,
            metric_name="memory_usage",
            value=10.0,
            unit="percent",
            collected_at=IN_BASELINE_WINDOW,
        )
    )
    await db_session.commit()

    result = await run_drift_check(db_session)
    assert result is None
    assert await _open_drift_alerts(db_session) == 0


async def test_response_time_drift_from_health_checks(db_session):
    for ms in (95, 105):
        db_session.add(
            HealthCheck(
                service_name="content-engine",
                service_type="engine",
                status=HealthStatus.HEALTHY,
                response_time_ms=ms,
                checked_at=IN_BASELINE_WINDOW,
            )
        )
    for ms in (290, 310):
        db_session.add(
            HealthCheck(
                service_name="content-engine",
                service_type="engine",
                status=HealthStatus.HEALTHY,
                response_time_ms=ms,
                checked_at=IN_CURRENT_WINDOW,
            )
        )
    await db_session.commit()

    alert = await run_drift_check(db_session)
    assert alert is not None
    assert "avg_response_time_ms" in alert.extra_metadata["drift_deviations"]
