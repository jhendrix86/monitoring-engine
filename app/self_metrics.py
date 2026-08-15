"""
Real self-performance metrics via psutil - this engine's own host, not a
fabricated summary. Other engines report their own metrics by POSTing to
/performance/record; this module is what monitoring-engine records about
itself, since nothing else does that for it.
"""

import os
import socket

import psutil

from app.models.performance_metric import MetricType, PerformanceMetric

HOSTNAME = socket.gethostname()
SERVICE_NAME = "monitoring-engine"


def collect_self_metrics() -> list[PerformanceMetric]:
    """Real psutil readings for this process's host: CPU, memory, disk (all percent)."""
    cpu_percent = psutil.cpu_percent(interval=None)
    memory_percent = psutil.virtual_memory().percent
    disk_percent = psutil.disk_usage(os.sep).percent

    return [
        PerformanceMetric(
            metric_type=MetricType.CPU,
            metric_name="cpu_usage",
            value=cpu_percent,
            unit="percent",
            service_name=SERVICE_NAME,
            hostname=HOSTNAME,
        ),
        PerformanceMetric(
            metric_type=MetricType.MEMORY,
            metric_name="memory_usage",
            value=memory_percent,
            unit="percent",
            service_name=SERVICE_NAME,
            hostname=HOSTNAME,
        ),
        PerformanceMetric(
            metric_type=MetricType.DISK,
            metric_name="disk_usage",
            value=disk_percent,
            unit="percent",
            service_name=SERVICE_NAME,
            hostname=HOSTNAME,
        ),
    ]
