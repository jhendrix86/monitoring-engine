"""
Monitoring Engine - Main Application
System monitoring and alerting system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager, suppress
from loguru import logger
from datetime import datetime
import asyncio
import os

from app import database as database_module
from app.config import settings
from app.database import init_db
from app.health_poller import poll_all_services
from app.self_metrics import collect_self_metrics
from app.drift_monitor import run_drift_check
from app.routers import health, performance, alerts, logs, incidents
from app.middleware.tenant import tenant_middleware

_polling_task: asyncio.Task | None = None
_metrics_task: asyncio.Task | None = None
_drift_task: asyncio.Task | None = None


async def _health_polling_loop():
    """
    Background loop: real health polling of every registered engine on
    settings.health_check_interval, persisting a HealthCheck row per
    service each pass. A failed iteration (e.g. every engine down) is
    logged and skipped, never crashes the loop - this is the fleet's own
    monitoring, so it has to keep running even when everything it watches
    is unhealthy.
    """
    while True:
        try:
            async with database_module.AsyncSessionLocal() as session:
                await poll_all_services(session)
        except Exception as exc:
            logger.error(f"Health polling loop iteration failed: {exc}")
        await asyncio.sleep(settings.health_check_interval)


async def _metrics_collection_loop():
    """Background loop: real psutil self-metrics on settings.metrics_collection_interval."""
    while True:
        try:
            async with database_module.AsyncSessionLocal() as session:
                for metric in collect_self_metrics():
                    session.add(metric)
                await session.commit()
        except Exception as exc:
            logger.error(f"Metrics collection loop iteration failed: {exc}")
        await asyncio.sleep(settings.metrics_collection_interval)


async def _drift_monitoring_loop():
    """
    Background loop: run recorded metrics through the DriftMonitor operator
    on settings.drift_check_interval, opening a `performance_drift` alert
    when a metric has moved past threshold vs its baseline window. Same
    keep-running-through-failure contract as the loops above - a bad pass
    is logged and skipped, thin/flat data is an honest no-op.
    """
    while True:
        try:
            async with database_module.AsyncSessionLocal() as session:
                await run_drift_check(session)
        except Exception as exc:
            logger.error(f"Drift monitoring loop iteration failed: {exc}")
        await asyncio.sleep(settings.drift_check_interval)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global _polling_task, _metrics_task, _drift_task
    logger.info("Starting Monitoring Engine...")

    # Initialize database
    await init_db()

    if settings.enable_background_loops:
        _polling_task = asyncio.create_task(_health_polling_loop())
        _metrics_task = asyncio.create_task(_metrics_collection_loop())
        _drift_task = asyncio.create_task(_drift_monitoring_loop())
        logger.info(
            f"Started background health polling (interval={settings.health_check_interval}s), "
            f"self-metrics collection (interval={settings.metrics_collection_interval}s), "
            f"and drift monitoring (interval={settings.drift_check_interval}s)"
        )

    logger.info("Monitoring Engine started successfully")
    yield

    for task in (_polling_task, _metrics_task, _drift_task):
        if task is not None:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

    logger.info("Shutting down Monitoring Engine...")


# Create FastAPI application
app = FastAPI(
    title="Monitoring Engine",
    description="System monitoring and alerting system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan,
    # SECURITY_REVIEW.md finding: /docs, /redoc, /openapi.json were reachable
    # unauthenticated on every engine (dynamic-pentest-confirmed) - a full
    # interactive API browser plus every unauth write path. Disabled unless
    # DEBUG=true.
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)

# Configure CORS
def _cors_allowed_origins() -> list:
    # SECURITY_REVIEW.md #1 - no wildcard with credentials. Set
    # ALLOWED_ORIGINS (comma-separated) when a browser client exists.
    import os
    return [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add tenant middleware for multi-tenancy support
app.middleware("http")(tenant_middleware)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(performance.router, prefix="/performance", tags=["performance"])
app.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(incidents.router, prefix="/incidents", tags=["incidents"])


@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "Monitoring Engine",
        "version": "1.0.0",
        "status": "operational",
        "description": "System monitoring and alerting system",
        "features": [
            "System health checks",
            "Performance tracking",
            "Uptime monitoring",
            "Alert management",
            "Log aggregation",
            "Infrastructure monitoring",
            "Custom metrics",
            "Monitoring dashboard"
        ],
        "endpoints": {
            "health": "/health",
            "performance": "/performance",
            "alerts": "/alerts",
            "logs": "/logs",
            "incidents": "/incidents"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("Health check performed")
    return {
        "status": "healthy",
        "service": "monitoring-engine",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8043,
        reload=True
    )
