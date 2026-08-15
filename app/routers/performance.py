"""
Performance metrics router - real DB-backed CRUD against
performance_metrics, and a real aggregate summary (no fabricated
constants).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.health_check import HealthCheck
from app.models.performance_metric import MetricType, PerformanceMetric
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class RecordMetricRequest(BaseModel):
    """Request to record a performance metric"""
    metric_type: MetricType
    metric_name: str
    value: float
    unit: Optional[str] = None
    service_name: Optional[str] = None
    hostname: Optional[str] = None


def _serialize(metric: PerformanceMetric) -> dict:
    return {
        "id": str(metric.id),
        "metric_type": metric.metric_type.value,
        "metric_name": metric.metric_name,
        "value": metric.value,
        "unit": metric.unit,
        "service_name": metric.service_name,
        "hostname": metric.hostname,
        "collected_at": metric.collected_at.isoformat(),
    }


@router.post("/record")
async def record_metric(request: RecordMetricRequest, db: AsyncSession = Depends(get_db)):
    """Record a performance metric"""
    try:
        logger.info(f"Recording metric: {request.metric_name}")

        metric = PerformanceMetric(
            metric_type=request.metric_type,
            metric_name=request.metric_name,
            value=request.value,
            unit=request.unit,
            service_name=request.service_name,
            hostname=request.hostname,
        )
        apply_tenant_context(metric)

        db.add(metric)
        await db.commit()
        await db.refresh(metric)

        return _serialize(metric)

    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_metrics(
    metric_type: Optional[MetricType] = None,
    service_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List performance metrics, real filters applied against the database"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(hours=1)
        if not end_date:
            end_date = datetime.utcnow()

        query = select(PerformanceMetric).where(
            PerformanceMetric.collected_at >= start_date, PerformanceMetric.collected_at <= end_date
        )
        if metric_type is not None:
            query = query.where(PerformanceMetric.metric_type == metric_type)
        if service_name is not None:
            query = query.where(PerformanceMetric.service_name == service_name)

        query = query.order_by(PerformanceMetric.collected_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        metrics = result.scalars().all()

        return {
            "total": len(metrics),
            "metrics": [_serialize(m) for m in metrics],
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "filters": {"metric_type": metric_type.value if metric_type else None, "service_name": service_name},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary(db: AsyncSession = Depends(get_db)):
    """Real aggregate performance summary, computed from the last hour of recorded data."""
    try:
        window_start = datetime.utcnow() - timedelta(hours=1)

        avg_cpu = await db.scalar(
            select(func.avg(PerformanceMetric.value)).where(
                PerformanceMetric.metric_type == MetricType.CPU, PerformanceMetric.collected_at >= window_start
            )
        )
        avg_memory = await db.scalar(
            select(func.avg(PerformanceMetric.value)).where(
                PerformanceMetric.metric_type == MetricType.MEMORY, PerformanceMetric.collected_at >= window_start
            )
        )
        avg_response_time = await db.scalar(
            select(func.avg(HealthCheck.response_time_ms)).where(HealthCheck.checked_at >= window_start)
        )
        services_reporting = await db.scalar(
            select(func.count(func.distinct(HealthCheck.service_name))).where(HealthCheck.checked_at >= window_start)
        )

        summary = {
            "avg_cpu_usage": round(avg_cpu, 1) if avg_cpu is not None else None,
            "avg_memory_usage": round(avg_memory, 1) if avg_memory is not None else None,
            "avg_response_time_ms": round(avg_response_time, 1) if avg_response_time is not None else None,
            "services_reporting": services_reporting or 0,
        }

        return {"timestamp": datetime.utcnow().isoformat(), "window": "last_1h", "summary": summary}

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
