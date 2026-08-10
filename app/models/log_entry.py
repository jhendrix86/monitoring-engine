"""
Log entry models
"""

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class LogLevel(str, enum.Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogEntry(TenantBase, Base):
    """Log entry model"""
    __tablename__ = "log_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Log details
    level = Column(Enum(LogLevel), nullable=False)
    service_name = Column(String(100), nullable=True)
    
    # Message
    message = Column(Text, nullable=False)
    
    # Context
    context = Column(JSON, nullable=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<LogEntry {self.level} - {self.service_name}>"
