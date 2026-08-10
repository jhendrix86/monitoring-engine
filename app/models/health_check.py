"""
Health check models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class HealthStatus(str, enum.Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck(TenantBase, Base):
    """Health check model"""
    __tablename__ = "health_checks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Service details
    service_name = Column(String(100), nullable=False)
    service_type = Column(String(50), nullable=False)
    service_url = Column(String(255), nullable=True)
    
    # Health status
    status = Column(Enum(HealthStatus), default=HealthStatus.UNKNOWN)
    
    # Response time
    response_time_ms = Column(Integer, nullable=True)
    
    # Details
    details = Column(JSON, nullable=True)
    error_message = Column(String(500), nullable=True)
    
    # Timestamps
    checked_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<HealthCheck {self.service_name} - {self.status}>"
