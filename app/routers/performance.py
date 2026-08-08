"""
Performance metrics router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class RecordMetricRequest(BaseModel):
    """Request to record a performance metric"""
    metric_type: str
    metric_name: str
    value: int
    unit: Optional[str] = None
    service_name: Optional[str] = None
    hostname: Optional[str] = None


@router.post("/record")
async def record_metric(
    request: RecordMetricRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record a performance metric"""
    try:
        logger.info(f"Recording metric: {request.metric_name}")

        # In production, this would save to database
        # For now, return a mock response
        metric = {
            "id": "metric_123",
            "metric_type": request.metric_type,
            "metric_name": request.metric_name,
            "value": request.value,
            "unit": request.unit,
            "service_name": request.service_name,
            "hostname": request.hostname,
            "collected_at": datetime.utcnow().isoformat()
        }

        return metric

    except Exception as e:
        logger.error(f"Failed to record metric: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_metrics(
    metric_type: Optional[str] = None,
    service_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List performance metrics"""
    try:
        logger.info("Listing performance metrics")

        if not start_date:
            start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()

        # In production, this would query from database with filters
        # For now, return a mock response
        metrics = [
            {"id": "metric_001", "metric_type": "cpu", "metric_name": "cpu_usage", "value": 45, "unit": "percent"},
            {"id": "metric_002", "metric_type": "memory", "metric_name": "memory_usage", "value": 62, "unit": "percent"},
        ]

        return {
            "total": len(metrics),
            "metrics": metrics,
            "period": {"start_date": start_date, "end_date": end_date},
            "filters": {"metric_type": metric_type, "service_name": service_name},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_performance_summary(db: AsyncSession = Depends(get_db)):
    """Get an aggregate performance summary across services"""
    try:
        logger.info("Getting performance summary")

        # In production, this would aggregate from database
        # For now, return a mock response
        summary = {
            "avg_cpu_usage": 42.3,
            "avg_memory_usage": 58.1,
            "avg_response_time_ms": 120,
            "services_reporting": 13
        }

        return {"timestamp": datetime.utcnow().isoformat(), "summary": summary}

    except Exception as e:
        logger.error(f"Failed to get performance summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
