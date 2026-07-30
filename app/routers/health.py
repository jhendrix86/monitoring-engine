"""
Health router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

from app.database import get_db
from app.models.health_check import HealthCheck, HealthStatus

router = APIRouter()


@router.get("/system")
async def get_system_health(
    db: AsyncSession = Depends(get_db)
):
    """Get overall system health"""
    try:
        logger.info("Getting system health")
        
        # In production, this would aggregate all service health
        # For now, return a mock response
        health = {
            "overall_status": "healthy",
            "services": {
                "pricing-intelligence": {"status": "healthy", "uptime": "99.9%"},
                "funnel-automation": {"status": "healthy", "uptime": "99.8%"},
                "global-state-manager": {"status": "healthy", "uptime": "99.9%"},
                "governance-engine": {"status": "healthy", "uptime": "99.9%"},
                "knowledge-graph": {"status": "healthy", "uptime": "99.7%"},
                "revenue-operations": {"status": "healthy", "uptime": "99.9%"},
                "notification-engine": {"status": "healthy", "uptime": "99.8%"},
                "customer-support": {"status": "healthy", "uptime": "99.9%"},
                "marketing-automation": {"status": "healthy", "uptime": "99.7%"},
                "content-engine": {"status": "healthy", "uptime": "99.8%"},
                "sales-engine": {"status": "healthy", "uptime": "99.9%"},
                "analytics-engine": {"status": "healthy", "uptime": "99.8%"},
                "monitoring-engine": {"status": "healthy", "uptime": "100.0%"}
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return health
        
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services")
async def get_service_health(
    db: AsyncSession = Depends(get_db)
):
    """Get all service health"""
    try:
        logger.info("Getting service health")
        
        # In production, this would query from database
        # For now, return a mock response
        services = [
            {
                "service_name": "pricing-intelligence",
                "service_type": "pricing",
                "status": "healthy",
                "response_time_ms": 45,
                "checked_at": datetime.utcnow().isoformat()
            },
            {
                "service_name": "funnel-automation",
                "service_type": "funnel",
                "status": "healthy",
                "response_time_ms": 32,
                "checked_at": datetime.utcnow().isoformat()
            }
        ]
        
        return {
            "total": len(services),
            "services": services
        }
        
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{service_id}")
async def get_service_health_detail(
    service_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific service health"""
    try:
        logger.info(f"Getting health for service {service_id}")
        
        # In production, this would query from database
        # For now, return a mock response
        service = {
            "service_name": service_id,
            "service_type": "pricing",
            "status": "healthy",
            "response_time_ms": 45,
            "uptime_percentage": 99.9,
            "last_check": datetime.utcnow().isoformat(),
            "details": {
                "cpu_usage": 45.2,
                "memory_usage": 62.1,
                "disk_usage": 34.5
            }
        }
        
        return service
        
    except Exception as e:
        logger.error(f"Failed to get service health: {e}")
        raise HTTPException(status_code=500, detail=str(e))
