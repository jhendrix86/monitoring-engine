"""
Incidents router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateIncidentRequest(BaseModel):
    """Request to open an incident"""
    title: str
    description: Optional[str] = None
    severity: str
    affected_services: Optional[list] = None
    impact_level: Optional[str] = None
    affected_users: Optional[int] = None


@router.post("/create")
async def create_incident(
    request: CreateIncidentRequest,
    db: AsyncSession = Depends(get_db)
):
    """Open a new incident"""
    try:
        logger.info(f"Creating incident: {request.title}")

        # In production, this would save to database
        # For now, return a mock response
        incident = {
            "id": "incident_123",
            "title": request.title,
            "description": request.description,
            "severity": request.severity,
            "status": "open",
            "affected_services": request.affected_services,
            "impact_level": request.impact_level,
            "affected_users": request.affected_users,
            "created_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Incident created: {incident['id']}")
        return incident

    except Exception as e:
        logger.error(f"Failed to create incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: str,
    resolution_notes: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Resolve an incident"""
    try:
        logger.info(f"Resolving incident {incident_id}")

        # In production, this would update database
        # For now, return a mock response
        incident = {
            "id": incident_id,
            "status": "resolved",
            "resolution_notes": resolution_notes,
            "resolved_at": datetime.utcnow().isoformat()
        }

        return incident

    except Exception as e:
        logger.error(f"Failed to resolve incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{incident_id}")
async def get_incident(incident_id: str, db: AsyncSession = Depends(get_db)):
    """Get incident details"""
    try:
        logger.info(f"Getting incident details for {incident_id}")

        # In production, this would query from database
        # For now, return a mock response
        incident = {
            "id": incident_id,
            "title": "Elevated error rate on sales-engine",
            "severity": "high",
            "status": "investigating",
            "affected_services": ["sales-engine"],
            "created_at": datetime.utcnow().isoformat()
        }

        return incident

    except Exception as e:
        logger.error(f"Failed to get incident: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_incidents(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List incidents"""
    try:
        logger.info("Listing incidents")

        # In production, this would query from database with filters
        # For now, return a mock response
        incidents = [
            {"id": "incident_001", "title": "Elevated error rate on sales-engine", "severity": "high", "status": "investigating"},
            {"id": "incident_002", "title": "Delayed email delivery", "severity": "medium", "status": "resolved"},
        ]

        return {
            "total": len(incidents),
            "incidents": incidents,
            "filters": {"status": status, "severity": severity},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list incidents: {e}")
        raise HTTPException(status_code=500, detail=str(e))
