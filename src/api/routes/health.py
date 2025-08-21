"""
Health check API routes.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel
import structlog

from ...database.session import get_db_session
from ...core.config import get_settings

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
    settings = get_settings()
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app.version,
        environment=settings.app.environment
    )


@router.get("/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check():
    """Detailed health check endpoint."""
    settings = get_settings()
    
    # Check database connection
    db_status = "healthy"
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
    except Exception as e:
        db_status = "unhealthy"
        logger.error("Database health check failed", error=str(e))
    
    # Check other components
    components = {
        "database": db_status,
        "api": "healthy",
        "logging": "healthy"
    }
    
    # Calculate uptime (placeholder)
    uptime = "0:00:00"  # Implement actual uptime calculation
    
    return DetailedHealthResponse(
        status="healthy" if all(v == "healthy" for v in components.values()) else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.app.version,
        environment=settings.app.environment,
        components=components,
        uptime=uptime
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    try:
        # Check database connection
        with get_db_session() as db:
            db.execute("SELECT 1")
        
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not_ready", "error": str(e)}


@router.get("/live")
async def liveness_check():
    """Liveness check endpoint."""
    return {"status": "alive"}