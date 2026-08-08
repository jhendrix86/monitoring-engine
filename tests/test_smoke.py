"""
Monitoring Engine smoke tests
"""
import pytest


@pytest.mark.asyncio
async def test_performance_metric_import():
    """Verify performance metric models import without error"""
    from app.models.performance_metric import PerformanceMetric, MetricType
    assert PerformanceMetric is not None
    assert MetricType.CPU == "cpu"
    assert MetricType.MEMORY == "memory"


@pytest.mark.asyncio
async def test_app_instantiation():
    """Verify FastAPI app instantiates without error"""
    from app.main import app
    assert app is not None
    assert app.title == "Monitoring Engine"
