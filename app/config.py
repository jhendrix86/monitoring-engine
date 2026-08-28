"""
Configuration management for Monitoring Engine
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://localhost/monitoring")
    
    # Redis
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Prometheus
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "")
    
    # Monitoring intervals
    health_check_interval: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))  # seconds
    metrics_collection_interval: int = int(os.getenv("METRICS_COLLECTION_INTERVAL", "30"))  # seconds

    # Set to false to disable the background health-polling and
    # self-metrics loops - used by the test suite so it doesn't spend
    # every test run polling 13 nonexistent ports on localhost.
    enable_background_loops: bool = os.getenv("ENABLE_BACKGROUND_LOOPS", "true").lower() == "true"
    
    # Alert thresholds
    cpu_warning_threshold: float = float(os.getenv("CPU_WARNING_THRESHOLD", "80.0"))
    cpu_critical_threshold: float = float(os.getenv("CPU_CRITICAL_THRESHOLD", "90.0"))
    memory_warning_threshold: float = float(os.getenv("MEMORY_WARNING_THRESHOLD", "80.0"))
    memory_critical_threshold: float = float(os.getenv("MEMORY_CRITICAL_THRESHOLD", "90.0"))
    
    # Application
    app_name: str = "Monitoring Engine"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Integration
    notification_engine_url: str = os.getenv("NOTIFICATION_ENGINE_URL", "http://localhost:8037")

    # Recipient for real alert notifications sent to notification-engine.
    # Empty by default (honest no-op, not a fabricated success) until
    # someone actually configures it - matches the fleet's established
    # "unconfigured = quiet, honest skip" convention (see
    # notification-engine's own delivery clients' `configured` gates).
    alert_notification_recipient: str = os.getenv("ALERT_NOTIFICATION_RECIPIENT", "")

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # tolerate env vars owned by other libs (e.g. unkey-auth's UNKEY_*)


settings = Settings()
