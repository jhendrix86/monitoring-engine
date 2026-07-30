"""
Monitoring Engine - Main Application
System monitoring and alerting system for the Autonomous Company OS
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os

from app.config import settings
from app.database import init_db
from app.routers import health, performance, alerts, logs, incidents


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting Monitoring Engine...")
    
    # Initialize database
    await init_db()
    
    logger.info("Monitoring Engine started successfully")
    yield
    
    logger.info("Shutting down Monitoring Engine...")


# Create FastAPI application
app = FastAPI(
    title="Monitoring Engine",
    description="System monitoring and alerting system for the Autonomous Company OS",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {
        "status": "healthy",
        "service": "monitoring-engine",
        "timestamp": logger.info("Health check performed")
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8043,
        reload=True
    )
