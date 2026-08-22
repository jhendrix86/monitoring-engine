"""
Alerts router - real DB-backed CRUD against the alerts table.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.alert import Alert, AlertSeverity, AlertStatus
from app.models.tenant_base import apply_tenant_context
from app.severity_mapping import to_canonical_severity
from app.services.notification_client import send_alert_notification

router = APIRouter()


class CreateAlertRequest(BaseModel):
    """Request to create an alert"""
    alert_type: str
    severity: AlertSeverity
    title: str
    message: Optional[str] = None
    threshold: Optional[int] = None
    current_value: Optional[int] = None
    service_name: Optional[str] = None


def _serialize(alert: Alert) -> dict:
    return {
        "id": str(alert.id),
        "alert_type": alert.alert_type,
        "severity": alert.severity.value,
        "canonical_severity": to_canonical_severity(alert.severity).value,
        "status": alert.status.value,
        "title": alert.title,
        "message": alert.message,
        "threshold": alert.threshold,
        "current_value": alert.current_value,
        "service_name": alert.service_name,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "acknowledged_by": alert.acknowledged_by,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "resolution_notes": alert.resolution_notes,
        "created_at": alert.created_at.isoformat(),
    }


async def _get_alert_or_404(db: AsyncSession, alert_id: str) -> Alert:
    try:
        alert_uuid = uuid.UUID(alert_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")

    alert = await db.get(Alert, alert_uuid)
    if alert is None:
        raise HTTPException(status_code=404, detail=f"Alert '{alert_id}' not found")
    return alert


@router.post("/create")
async def create_alert(request: CreateAlertRequest, db: AsyncSession = Depends(get_db)):
    """Create an alert"""
    try:
        logger.info(f"Creating alert: {request.title}")

        alert = Alert(
            alert_type=request.alert_type,
            severity=request.severity,
            status=AlertStatus.OPEN,
            title=request.title,
            message=request.message,
            threshold=request.threshold,
            current_value=request.current_value,
            service_name=request.service_name,
        )
        apply_tenant_context(alert)

        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        logger.info(f"Alert created: {alert.id}")
        
        # Send notification to notification-engine
        try:
            await send_alert_notification(
                alert_id=str(alert.id),
                alert_title=alert.title,
                alert_message=alert.message,
                severity=alert.severity.value,
            )
        except Exception as e:
            logger.warning(f"Notification failed for alert {alert.id}: {e}")
            # Don't fail the alert creation if notification fails
        
        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, acknowledged_by: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Acknowledge an alert"""
    try:
        alert = await _get_alert_or_404(db, alert_id)

        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_by = acknowledged_by
        alert.acknowledged_at = datetime.utcnow()

        await db.commit()
        await db.refresh(alert)

        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to acknowledge alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolution_notes: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Resolve an alert"""
    try:
        alert = await _get_alert_or_404(db, alert_id)

        alert.status = AlertStatus.RESOLVED
        alert.resolution_notes = resolution_notes
        alert.resolved_at = datetime.utcnow()

        await db.commit()
        await db.refresh(alert)

        return _serialize(alert)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_alerts(
    severity: Optional[AlertSeverity] = None,
    status: Optional[AlertStatus] = None,
    service_name: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List alerts, real filters applied against the database"""
    try:
        query = select(Alert)
        if severity is not None:
            query = query.where(Alert.severity == severity)
        if status is not None:
            query = query.where(Alert.status == status)
        if service_name is not None:
            query = query.where(Alert.service_name == service_name)

        query = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        alerts = result.scalars().all()

        return {
            "total": len(alerts),
            "alerts": [_serialize(a) for a in alerts],
            "filters": {
                "severity": severity.value if severity else None,
                "status": status.value if status else None,
                "service_name": service_name,
            },
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))
