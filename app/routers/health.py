"""
Health router - real HTTP-based polling (app/health_poller.py) persisted
to the health_checks table, not the hardcoded mock this used to return.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from loguru import logger

from app.database import get_db
from app.health_poller import poll_one_service
from app.models.health_check import HealthCheck, HealthStatus
from app.service_registry import SERVICE_PORTS

router = APIRouter()


async def _latest_check_per_service(db: AsyncSession) -> dict[str, HealthCheck]:
    """
    Most recent HealthCheck row per service_name. Deduped in Python
    rather than a DB-side DISTINCT ON, since that's Postgres-only and
    this needs to run identically against the SQLite test database too.
    """
    result = await db.execute(select(HealthCheck).order_by(HealthCheck.checked_at.desc()))
    latest: dict[str, HealthCheck] = {}
    for check in result.scalars():
        latest.setdefault(check.service_name, check)
    return latest


@router.get("/system")
async def get_system_health(db: AsyncSession = Depends(get_db)):
    """Aggregate overall system health from the latest persisted check per service."""
    try:
        latest = await _latest_check_per_service(db)

        if not latest:
            return {
                "overall_status": "unknown",
                "services": {},
                "timestamp": datetime.utcnow().isoformat(),
                "note": "No health checks recorded yet - the background polling loop hasn't completed a pass.",
            }

        statuses = {check.status for check in latest.values()}
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = "unhealthy"
        elif HealthStatus.DEGRADED in statuses or HealthStatus.UNKNOWN in statuses:
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "overall_status": overall_status,
            "services": {
                name: {"status": check.status.value, "response_time_ms": check.response_time_ms, "checked_at": check.checked_at.isoformat()}
                for name, check in latest.items()
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_service_health(db: AsyncSession = Depends(get_db)):
    """List the latest persisted health check for every service that's been polled."""
    try:
        latest = await _latest_check_per_service(db)
        services = [
            {
                "service_name": check.service_name,
                "service_type": check.service_type,
                "status": check.status.value,
                "response_time_ms": check.response_time_ms,
                "error_message": check.error_message,
                "checked_at": check.checked_at.isoformat(),
            }
            for check in latest.values()
        ]
        return {"total": len(services), "services": services}

    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_id}")
async def get_service_health_detail(service_id: str, db: AsyncSession = Depends(get_db)):
    """Poll one registered service live, right now, and persist + return the fresh result."""
    if service_id not in SERVICE_PORTS:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service_id}' - not in the fleet's service registry")

    try:
        check = await poll_one_service(db, service_id)
        return {
            "service_name": check.service_name,
            "service_type": check.service_type,
            "status": check.status.value,
            "response_time_ms": check.response_time_ms,
            "error_message": check.error_message,
            "details": check.details,
            "last_check": check.checked_at.isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get service health for {service_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
