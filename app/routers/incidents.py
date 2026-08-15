"""
Incidents router - real DB-backed CRUD against the incidents table.
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
from app.models.alert import AlertSeverity
from app.models.incident import Incident, IncidentStatus
from app.models.tenant_base import apply_tenant_context
from app.severity_mapping import to_canonical_severity

router = APIRouter()


class CreateIncidentRequest(BaseModel):
    """Request to open an incident"""
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    affected_services: Optional[list] = None
    impact_level: Optional[str] = None
    affected_users: Optional[int] = None


def _serialize(incident: Incident) -> dict:
    return {
        "id": str(incident.id),
        "title": incident.title,
        "description": incident.description,
        "severity": incident.severity.value,
        "canonical_severity": to_canonical_severity(incident.severity).value,
        "status": incident.status.value,
        "affected_services": incident.affected_services,
        "impact_level": incident.impact_level,
        "affected_users": incident.affected_users,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
        "resolution_notes": incident.resolution_notes,
        "created_at": incident.created_at.isoformat(),
    }


async def _get_incident_or_404(db: AsyncSession, incident_id: str) -> Incident:
    try:
        incident_uuid = uuid.UUID(incident_id)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")

    incident = await db.get(Incident, incident_uuid)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found")
    return incident


@router.post("/create")
async def create_incident(request: CreateIncidentRequest, db: AsyncSession = Depends(get_db)):
    """Open a new incident"""
    try:
        logger.info(f"Creating incident: {request.title}")

        incident = Incident(
            title=request.title,
            description=request.description,
            severity=request.severity,
            status=IncidentStatus.OPEN,
            affected_services=request.affected_services,
            impact_level=request.impact_level,
            affected_users=request.affected_users,
        )
        apply_tenant_context(incident)

        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident created: {incident.id}")
        return _serialize(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{incident_id}/resolve")
async def resolve_incident(incident_id: str, resolution_notes: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """Resolve an incident"""
    try:
        incident = await _get_incident_or_404(db, incident_id)

        incident.status = IncidentStatus.RESOLVED
        incident.resolution_notes = resolution_notes
        incident.resolved_at = datetime.utcnow()

        await db.commit()
        await db.refresh(incident)

        return _serialize(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get incident details"""
    try:
        incident = await _get_incident_or_404(db, incident_id)
        return _serialize(incident)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_incidents(
    status: Optional[IncidentStatus] = None,
    severity: Optional[AlertSeverity] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List incidents, real filters applied against the database"""
    try:
        query = select(Incident)
        if status is not None:
            query = query.where(Incident.status == status)
        if severity is not None:
            query = query.where(Incident.severity == severity)

        query = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        incidents = result.scalars().all()

        return {
            "total": len(incidents),
            "incidents": [_serialize(i) for i in incidents],
            "filters": {"status": status.value if status else None, "severity": severity.value if severity else None},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
