"""
Main FastAPI application for the AI Trading Bot system.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from prometheus_client import make_asgi_app
import structlog

from .database.connection import get_database_connection, close_database_connection
from .api.routes import bridge, health, metrics, v1
from .core.config import get_settings
from .core.security import verify_bridge_token
from .core.logging import setup_logging


# Setup logging
setup_logging()
logger = structlog.get_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting AI Trading Bot application")
    
    # Initialize database
    try:
        db_conn = get_database_connection()
        db_conn.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Trading Bot application")
    close_database_connection()


# Create FastAPI app
app = FastAPI(
    title="AI Trading Bot API",
    description="Advanced AI-powered trading bot with MT4/MT5 integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Dependency for bridge token verification
async def verify_bridge_auth(request: Request):
    """Verify bridge authentication token."""
    settings = get_settings()
    token = request.headers.get("Authorization")
    
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization format")
    
    token_value = token[7:]  # Remove "Bearer " prefix
    
    if not verify_bridge_token(token_value):
        raise HTTPException(status_code=401, detail="Invalid bridge token")
    
    return token_value


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        exc_info=True,
    )
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(
    health.router,
    prefix="/healthz",
    tags=["health"],
)

app.include_router(
    metrics.router,
    prefix="/metrics",
    tags=["metrics"],
)

app.include_router(
    bridge.router,
    prefix="/bridge",
    tags=["bridge"],
    dependencies=[Depends(verify_bridge_auth)],
)

app.include_router(
    v1.router,
    prefix="/v1",
    tags=["api"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Trading Bot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/healthz",
        "metrics": "/metrics",
    }


@app.get("/readyz")
async def ready():
    """Readiness check endpoint."""
    try:
        # Check database connection
        db_conn = get_database_connection()
        with db_conn.get_session() as session:
            session.execute("SELECT 1")
        
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not ready")


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.app:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.app.debug,
        log_level=settings.logging.level.lower(),
    )