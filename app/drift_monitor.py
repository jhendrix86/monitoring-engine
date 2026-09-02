"""
Real metric-drift detection for the fleet.

`/performance/summary` reports current averages; nothing compared them
against a historical baseline, so a slow regression (an engine getting
steadily slower, memory creeping up) never raised anything until it
tripped a hard CPU/memory threshold. This closes that gap: on an
interval, aggregate the same recorded metrics over a recent window and a
trailing baseline window, run the pair through the `DriftMonitor`
reasoning operator (the fleet-shared `empire-operators` package), and
open a real `performance_drift` alert when a metric has moved past the
operator's threshold.

Same background-loop shape as `health_poller` / `self_metrics` (the loop
itself lives in `app.main` next to the other two). Never raises out of a
pass - drift monitoring has to keep running even when the data it reads
is thin or absent, so a bad pass is logged and skipped, and flat/empty
data is an honest no-op, never a fabricated alert.
"""

from datetime import datetime, timedelta

from empire_operators import DriftMonitor
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.health_check import HealthCheck
from app.models.performance_metric import MetricType, PerformanceMetric
from app.models.tenant_base import apply_tenant_context
from app.services.notification_client import send_alert_notification

DRIFT_ALERT_TYPE = "performance_drift"


async def _avg_metrics(db: AsyncSession, since: datetime, until: datetime) -> dict:
    """
    Real averages over [since, until): CPU + memory from performance_metrics,
    response time from health_checks. A metric with no rows in the window is
    left out of the returned dict entirely (not reported as 0) so the
    DriftMonitor operator only ever compares keys that have real data on
    both sides.
    """
    def _window(column):
        return (column >= since) & (column < until)

    avg_cpu = await db.scalar(
        select(func.avg(PerformanceMetric.value)).where(
            PerformanceMetric.metric_type == MetricType.CPU,
            _window(PerformanceMetric.collected_at),
        )
    )
    avg_memory = await db.scalar(
        select(func.avg(PerformanceMetric.value)).where(
            PerformanceMetric.metric_type == MetricType.MEMORY,
            _window(PerformanceMetric.collected_at),
        )
    )
    avg_response_time = await db.scalar(
        select(func.avg(HealthCheck.response_time_ms)).where(_window(HealthCheck.checked_at))
    )

    metrics = {}
    if avg_cpu is not None:
        metrics["avg_cpu_usage"] = round(avg_cpu, 1)
    if avg_memory is not None:
        metrics["avg_memory_usage"] = round(avg_memory, 1)
    if avg_response_time is not None:
        metrics["avg_response_time_ms"] = round(avg_response_time, 1)
    return metrics


def _describe(deviations: dict, current: dict, baseline: dict) -> str:
    parts = []
    for key, pct in deviations.items():
        parts.append(
            f"{key}: baseline {baseline.get(key)} -> current {current.get(key)} ({pct}% change)"
        )
    return "Metric drift past threshold - " + "; ".join(parts)


async def run_drift_check(db: AsyncSession) -> Alert | None:
    """
    One drift-detection pass. Returns the Alert it opened, or None when
    there's nothing to report (not enough recorded data, metrics flat, or a
    drift alert is already open).
    """
    now = datetime.utcnow()
    current_start = now - timedelta(hours=settings.drift_current_window_hours)
    baseline_start = now - timedelta(hours=settings.drift_baseline_window_hours)

    if baseline_start >= current_start:
        logger.warning(
            "Drift windows misconfigured (baseline window <= current window) - skipping pass"
        )
        return None

    current = await _avg_metrics(db, current_start, now)
    baseline = await _avg_metrics(db, baseline_start, current_start)

    shared = current.keys() & baseline.keys()
    if not shared:
        logger.debug("Drift check: no metric has data in both windows yet - honest no-op")
        return None

    state = DriftMonitor().execute(
        {
            "current_metrics": {k: current[k] for k in shared},
            "baseline_metrics": {k: baseline[k] for k in shared},
        }
    )
    deviations = state.get("drift_deviations", {})
    if not state.get("flags", {}).get("drift_detected"):
        logger.debug(f"Drift check: metrics within {DriftMonitor.DRIFT_THRESHOLD_PCT}% of baseline")
        return None

    existing = await db.scalar(
        select(Alert.id).where(
            Alert.alert_type == DRIFT_ALERT_TYPE, Alert.status == AlertStatus.OPEN
        )
    )
    if existing is not None:
        logger.info(
            f"Drift detected ({deviations}) but an OPEN {DRIFT_ALERT_TYPE} alert already "
            f"exists ({existing}) - not stacking another"
        )
        return None

    alert = Alert(
        alert_type=DRIFT_ALERT_TYPE,
        severity=AlertSeverity.WARNING,
        status=AlertStatus.OPEN,
        title=f"Performance drift on {', '.join(sorted(deviations))}",
        message=_describe(deviations, current, baseline),
        service_name="monitoring-engine",
        extra_metadata={
            "drift_deviations": deviations,
            "current_metrics": {k: current[k] for k in shared},
            "baseline_metrics": {k: baseline[k] for k in shared},
            "threshold_pct": DriftMonitor.DRIFT_THRESHOLD_PCT,
            "current_window_hours": settings.drift_current_window_hours,
            "baseline_window_hours": settings.drift_baseline_window_hours,
        },
    )
    apply_tenant_context(alert)
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.warning(f"Opened {DRIFT_ALERT_TYPE} alert {alert.id}: {deviations}")

    try:
        await send_alert_notification(
            alert_id=str(alert.id),
            alert_title=alert.title,
            alert_message=alert.message,
            severity=alert.severity.value,
        )
    except Exception as exc:  # notification failure must not fail the pass
        logger.warning(f"Notification failed for drift alert {alert.id}: {exc}")

    return alert
