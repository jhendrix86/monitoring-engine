"""
Performance metric models
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base
from app.models.tenant_base import TenantBase


class MetricType(str, enum.Enum):
    """Metric type enumeration"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    CUSTOM = "custom"


class PerformanceMetric(TenantBase, Base):
    """Performance metric model"""
    __tablename__ = "performance_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    metric_type = Column(Enum(MetricType), nullable=False)
    metric_name = Column(String(100), nullable=False)
    
    # Value
    value = Column(Integer, nullable=False)
    unit = Column(String(50), nullable=True)
    
    # Context
    service_name = Column(String(100), nullable=True)
    hostname = Column(String(255), nullable=True)
    
    # Timestamps
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Metadata
    extra_metadata = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<PerformanceMetric {self.metric_name} - {self.value}>"
