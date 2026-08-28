"""
Alert models
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Enum, ForeignKey, Text, JSON, Uuid
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class AlertSeverity(str, enum.Enum):
    """Alert severity enumeration"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(str, enum.Enum):
    """Alert status enumeration"""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class Alert(TenantBase, Base):
    """Alert model"""
    __tablename__ = "alerts"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Alert details
    alert_type = Column(String(100), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    status = Column(Enum(AlertStatus), default=AlertStatus.OPEN)
    
    # Message
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=True)
    
    # Thresholds
    threshold = Column(Integer, nullable=True)
    current_value = Column(Integer, nullable=True)
    
    # Service
    service_name = Column(String(100), nullable=True)
    
    # Resolution
    acknowledged_at = Column(DateTime, nullable=True)
    acknowledged_by = Column(String(255), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Alert {self.alert_type} - {self.severity} - {self.status}>"
