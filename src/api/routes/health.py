"""
Health check API routes.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

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
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=config.environment
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check endpoint."""
    # Check other components
    components = {
        "api": "healthy",
        "logging": "healthy"
    }
    
    # Calculate uptime (placeholder)
    uptime = "0:00:00"  # Implement actual uptime calculation
    
    return DetailedHealthResponse(
        status="healthy" if all(v == "healthy" for v in components.values()) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=config.environment,
        components=components,
        uptime=uptime
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive"}