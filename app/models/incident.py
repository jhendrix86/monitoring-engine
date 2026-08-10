"""
Incident models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class IncidentStatus(str, enum.Enum):
    """Incident status enumeration"""
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVING = "resolving"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Incident(TenantBase, Base):
    """Incident model"""
    __tablename__ = "incidents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Incident details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False)
    status = Column(Enum(IncidentStatus), default=IncidentStatus.OPEN)
    
    # Affected services
    affected_services = Column(JSON, nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Impact
    impact_level = Column(String(20), nullable=True)
    affected_users = Column(Integer, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Incident {self.title} - {self.status}>"
