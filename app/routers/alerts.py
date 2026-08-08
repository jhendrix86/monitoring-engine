"""
Alerts router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateAlertRequest(BaseModel):
    """Request to create an alert"""
    alert_type: str
    severity: str
    title: str
    message: Optional[str] = None
    threshold: Optional[int] = None
    current_value: Optional[int] = None
    service_name: Optional[str] = None


@router.post("/create")
async def create_alert(
    request: CreateAlertRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create an alert"""
    try:
        logger.info(f"Creating alert: {request.title}")

        # In production, this would save to database
        # For now, return a mock response
        alert = {
            "id": "alert_123",
            "alert_type": request.alert_type,
            "severity": request.severity,
            "status": "open",
            "title": request.title,
            "message": request.message,
            "service_name": request.service_name,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Alert created: {alert['id']}")
        return alert

    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledged_by: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Acknowledge an alert"""
    try:
        logger.info(f"Acknowledging alert {alert_id}")

        # In production, this would update database
        # For now, return a mock response
        alert = {
            "id": alert_id,
            "status": "acknowledged",
            "acknowledged_by": acknowledged_by,
            "acknowledged_at": datetime.utcnow().isoformat()
        }

        return alert

    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an alert"""
    try:
        logger.info(f"Resolving alert {alert_id}")

        # In production, this would update database
        # For now, return a mock response
        alert = {
            "id": alert_id,
            "status": "resolved",
            "resolution_notes": resolution_notes,
            "resolved_at": datetime.utcnow().isoformat()
        }

        return alert

    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_alerts(
    severity: Optional[str] = None,
    status: Optional[str] = None,
    service_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List alerts"""
    try:
        logger.info("Listing alerts")

        # In production, this would query from database with filters
        # For now, return a mock response
        alerts = [
            {"id": "alert_001", "alert_type": "high_cpu", "severity": "warning", "status": "open"},
            {"id": "alert_002", "alert_type": "service_down", "severity": "critical", "status": "acknowledged"},
        ]

        return {
            "total": len(alerts),
            "alerts": alerts,
            "filters": {"severity": severity, "status": status, "service_name": service_name},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
