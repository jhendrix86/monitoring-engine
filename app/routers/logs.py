"""
Logs router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db

router = APIRouter()


class CreateLogEntryRequest(BaseModel):
    """Request to record a log entry"""
    level: str
    service_name: Optional[str] = None
    message: str
    context: Optional[dict] = None


@router.post("/")
async def create_log_entry(
    request: CreateLogEntryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Record a log entry"""
    try:
        logger.info(f"Recording log entry from {request.service_name}")

        # In production, this would save to database
        # For now, return a mock response
        entry = {
            "id": "log_123",
            "level": request.level,
            "service_name": request.service_name,
            "message": request.message,
            "context": request.context,
            "timestamp": datetime.utcnow().isoformat()
        }

        return entry

    except Exception as e:
        logger.error(f"Failed to record log entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_log_entries(
    level: Optional[str] = None,
    service_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List log entries"""
    try:
        logger.info("Listing log entries")

        if not start_date:
            start_date = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        if not end_date:
            end_date = datetime.utcnow().isoformat()

        # In production, this would query from database with filters
        # For now, return a mock response
        entries = [
            {"id": "log_001", "level": "info", "service_name": "sales-engine", "message": "Lead created"},
            {"id": "log_002", "level": "error", "service_name": "kg-service", "message": "Connection timeout"},
        ]

        return {
            "total": len(entries),
            "entries": entries,
            "period": {"start_date": start_date, "end_date": end_date},
            "filters": {"level": level, "service_name": service_name},
            "pagination": {"limit": limit, "offset": offset}
        }

    except Exception as e:
        logger.error(f"Failed to list log entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_log_entries(
    query: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Full-text search across log entries"""
    try:
        logger.info(f"Searching log entries for: {query}")

        # In production, this would run a full-text query against the database
        # For now, return a mock response
        entries = [
            {"id": "log_001", "level": "error", "service_name": "kg-service", "message": f"Match for '{query}'"},
        ]

        return {"query": query, "total": len(entries), "entries": entries}

    except Exception as e:
        logger.error(f"Failed to search log entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
