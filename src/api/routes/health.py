"""
Health check API routes.
"""

from datetime import datetime, timezone

import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from ...core.config import config

logger = structlog.get_logger(__name__)
router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: str
    version: str
    environment: str


class DetailedHealthResponse(BaseModel):
    """Detailed health check response."""

    status: str
    timestamp: str
    version: str
    environment: str
    components: dict
    uptime: str


@router.get("/", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        environment=config.environment,
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check endpoint."""
    # Check other components
    components = {"api": "healthy", "logging": "healthy"}

    # Calculate uptime from health monitor
    try:
        from ...core.health_monitor import health_monitor

        current_health = health_monitor.get_current_health()
        uptime_seconds = current_health.uptime_seconds

        # Format uptime as HH:MM:SS
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        seconds = int(uptime_seconds % 60)
        uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    except Exception:
        uptime = "0:00:00"  # Fallback if health monitor not available

    return DetailedHealthResponse(
        status=(
            "healthy"
            if all(v == "healthy" for v in components.values())
            else "degraded"
        ),
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        environment=config.environment,
        components=components,
        uptime=uptime,
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive"}
