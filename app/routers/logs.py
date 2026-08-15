"""
Logs router - real DB-backed ingestion and querying against log_entries.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.log_entry import LogEntry, LogLevel
from app.models.tenant_base import apply_tenant_context

router = APIRouter()


class CreateLogEntryRequest(BaseModel):
    """Request to record a log entry"""
    level: LogLevel
    service_name: Optional[str] = None
    message: str
    context: Optional[dict] = None


def _serialize(entry: LogEntry) -> dict:
    return {
        "id": str(entry.id),
        "level": entry.level.value,
        "service_name": entry.service_name,
        "message": entry.message,
        "context": entry.context,
        "timestamp": entry.timestamp.isoformat(),
    }


@router.post("/")
async def create_log_entry(request: CreateLogEntryRequest, db: AsyncSession = Depends(get_db)):
    """Record a log entry"""
    try:
        logger.info(f"Recording log entry from {request.service_name}")

        entry = LogEntry(
            level=request.level,
            service_name=request.service_name,
            message=request.message,
            context=request.context,
        )
        apply_tenant_context(entry)

        db.add(entry)
        await db.commit()
        await db.refresh(entry)

        return _serialize(entry)

    except Exception as e:
        logger.error(f"Failed to record log entry: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_log_entries(
    level: Optional[LogLevel] = None,
    service_name: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List log entries, real filters applied against the database"""
    try:
        if not start_date:
            start_date = datetime.utcnow() - timedelta(hours=1)
        if not end_date:
            end_date = datetime.utcnow()

        query = select(LogEntry).where(LogEntry.timestamp >= start_date, LogEntry.timestamp <= end_date)
        if level is not None:
            query = query.where(LogEntry.level == level)
        if service_name is not None:
            query = query.where(LogEntry.service_name == service_name)

        query = query.order_by(LogEntry.timestamp.desc()).offset(offset).limit(limit)

        result = await db.execute(query)
        entries = result.scalars().all()

        return {
            "total": len(entries),
            "entries": [_serialize(e) for e in entries],
            "period": {"start_date": start_date.isoformat(), "end_date": end_date.isoformat()},
            "filters": {"level": level.value if level else None, "service_name": service_name},
            "pagination": {"limit": limit, "offset": offset},
        }

    except Exception as e:
        logger.error(f"Failed to list log entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_log_entries(query: str, limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Real substring search of log messages, case-insensitive"""
    try:
        logger.info(f"Searching log entries for: {query}")

        db_query = (
            select(LogEntry)
            .where(LogEntry.message.ilike(f"%{query}%"))
            .order_by(LogEntry.timestamp.desc())
            .limit(limit)
        )
        result = await db.execute(db_query)
        entries = result.scalars().all()

        return {"query": query, "total": len(entries), "entries": [_serialize(e) for e in entries]}

    except Exception as e:
        logger.error(f"Failed to search log entries: {e}")
        raise HTTPException(status_code=500, detail=str(e))
