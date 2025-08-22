"""
AI Trading Bot - Main Application
Main FastAPI application with Socket.IO, Telegram bot, and trading execution.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio
from socketio import AsyncServer

from .core.config import config
from .core.logging import (
    get_logger,
    log_system_event,
    print_banner,
    print_status_table,
    log_error_with_context,
)
from .bridge.socketio_bridge import SocketIOBridge
from .execution.mt5_executor import MT5Executor
from .execution.order_manager import OrderManager
from .execution.position_manager import PositionManager
from .execution.trailing_manager import TrailingManager
from .telegram_bot.bot import TelegramBot

# Import API routes
from .api.routes import health, v1, bridge, trading

# Get logger
logger = get_logger(__name__)

# Global instances for API routes
telegram_bot: TelegramBot = None
socketio_bridge: SocketIOBridge = None
mt5_executor: MT5Executor = None
order_manager: OrderManager = None
position_manager: PositionManager = None
trailing_manager: TrailingManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global telegram_bot, socketio_bridge, mt5_executor, order_manager, position_manager, trailing_manager

    # Print startup banner
    print_banner(
        "AI Trading Bot Starting",
        "Initializing components and establishing connections...",
        "cyan",
    )

    try:
        # Initialize MT5 executor
        logger.info("Initializing MT5 executor...")
        mt5_executor = MT5Executor(config.trading)

        # Connect to MT5
        logger.info("Connecting to MT5...")
        if not await mt5_executor.connect():
            logger.warning("Failed to connect to MT5, continuing with mock mode")

        # Initialize managers
        logger.info("Initializing trading managers...")
        order_manager = OrderManager(mt5_executor, config.trading)
        position_manager = PositionManager(mt5_executor, config.trading)
        trailing_manager = TrailingManager(mt5_executor, config.trading)

        # Initialize Socket.IO bridge
        logger.info("Initializing Socket.IO bridge...")
        socketio_bridge = SocketIOBridge(config.bridge)

        # Initialize Telegram bot
        logger.info("Initializing Telegram bot...")
        telegram_bot = TelegramBot(config.telegram)

        # Set global instances for API routes
        bridge.set_global_instances(order_manager, telegram_bot)
        trading.order_manager = order_manager
        trading.position_manager = position_manager
        trading.telegram_bot = telegram_bot

        # Start all components
        logger.info("Starting all components...")

        # Start Socket.IO bridge
        await socketio_bridge.connect()

        # Start Telegram bot
        logger.info("Starting Telegram bot...")
        await telegram_bot.start()

        # Start managers as background tasks
        asyncio.create_task(position_manager.start())
        asyncio.create_task(trailing_manager.start())

        log_system_event(
            "main", "startup", "AI Trading Bot application started successfully"
        )

        # Print status table
        status_data = {
            "MT5 Executor": {
                "status": "initialized",
                "details": "Ready for connection",
            },
            "Socket.IO Bridge": {
                "status": "connecting",
                "details": "Establishing connection",
            },
            "Position Manager": {
                "status": "starting",
                "details": "Background task started",
            },
            "Trailing Manager": {
                "status": "starting",
                "details": "Background task started",
            },
            "Telegram Bot": {"status": "starting", "details": "Initializing bot"},
        }
        print_status_table(status_data)

        yield

    except Exception as e:
        log_error_with_context(e, {"component": "startup", "action": "initialization"})
        raise
    finally:
        # Shutdown sequence
        logger.info("Shutting down AI Trading Bot...")

        try:
            # Stop managers
            if position_manager:
                await position_manager.stop()
            if trailing_manager:
                await trailing_manager.stop()

            # Stop Telegram bot
            if telegram_bot:
                await telegram_bot.stop()

            # Disconnect Socket.IO bridge
            if socketio_bridge:
                await socketio_bridge.disconnect()

            # Shutdown MT5 executor
            if mt5_executor:
                await mt5_executor.disconnect()

            log_system_event(
                "main", "shutdown", "AI Trading Bot application shut down successfully"
            )

        except Exception as e:
            log_error_with_context(e, {"component": "shutdown", "action": "cleanup"})


# Create FastAPI app
app = FastAPI(
    title="AI Trading Bot",
    description="Institutional-grade AI-powered automated trading bot",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],  # Restrict to localhost only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = AsyncServer(async_mode="asgi", cors_allowed_origins="*")
socketio_app = socketio.ASGIApp(sio, app)


# Socket.IO event handlers
@sio.event
async def connect(sid, environ, auth):
    """Handle Socket.IO client connection."""
    logger.info(f"Client connected: {sid}")
    if socketio_bridge:
        await socketio_bridge.handle_client_connect(sid, environ, auth)


@sio.event
async def disconnect(sid):
    """Handle Socket.IO client disconnection."""
    logger.info(f"Client disconnected: {sid}")
    if socketio_bridge:
        await socketio_bridge.handle_client_disconnect(sid)


@sio.event
async def order(sid, data):
    """Handle order events from EA."""
    logger.info(f"Order event from {sid}: {data}")
    if socketio_bridge:
        await socketio_bridge.handle_order_event(sid, data)


@sio.event
async def signal(sid, data):
    """Handle signal events from EA."""
    logger.info(f"Signal event from {sid}: {data}")
    if socketio_bridge:
        await socketio_bridge.handle_signal_event(sid, data)


@sio.event
async def position_update(sid, data):
    """Handle position update events from EA."""
    logger.info(f"Position update from {sid}: {data}")
    if socketio_bridge:
        await socketio_bridge.handle_position_update(sid, data)


@sio.event
async def risk_alert(sid, data):
    """Handle risk alert events from EA."""
    logger.info(f"Risk alert from {sid}: {data}")
    if socketio_bridge:
        await socketio_bridge.handle_risk_alert(sid, data)


# Include API routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(v1.router, prefix="/api/v1", tags=["api"])
app.include_router(bridge.router, prefix="/api/v1/bridge", tags=["bridge"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with application info."""
    return {
        "name": "AI Trading Bot",
        "version": "1.0.0",
        "description": "Institutional-grade AI-powered automated trading bot",
        "status": "running",
        "components": {
            "mt5_executor": mt5_executor.is_connected if mt5_executor else False,
            "socketio_bridge": (
                socketio_bridge.get_status()
                if socketio_bridge
                else {"connected": False}
            ),
            "position_manager": (
                position_manager.is_running if position_manager else False
            ),
            "trailing_manager": (
                trailing_manager.is_running if trailing_manager else False
            ),
            "telegram_bot": telegram_bot.is_running if telegram_bot else False,
        },
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health_status = {
        "status": "healthy",
        "timestamp": "2025-08-22T00:00:00Z",
        "version": "1.0.0",
        "components": {},
    }

    # Check MT5 connection
    if mt5_executor:
        try:
            connected = mt5_executor.is_connected
            health_status["components"]["mt5"] = {
                "status": "connected" if connected else "disconnected",
                "healthy": connected,
            }
        except Exception as e:
            health_status["components"]["mt5"] = {
                "status": "error",
                "healthy": False,
                "error": str(e),
            }

    # Check Socket.IO bridge
    if socketio_bridge:
        bridge_status = socketio_bridge.get_status()
        health_status["components"]["bridge"] = {
            "status": "connected" if bridge_status["connected"] else "disconnected",
            "healthy": bridge_status["connected"],
        }

    # Check Telegram bot
    if telegram_bot:
        health_status["components"]["telegram"] = {
            "status": "running" if telegram_bot.is_running else "stopped",
            "healthy": telegram_bot.is_running,
        }

    # Check managers
    if position_manager:
        health_status["components"]["position_manager"] = {
            "running": "running" if position_manager.is_running else "stopped",
            "healthy": position_manager.is_running,
        }

    if trailing_manager:
        health_status["components"]["trailing_manager"] = {
            "running": "running" if trailing_manager.is_running else "stopped",
            "healthy": trailing_manager.is_running,
        }

    # Overall health
    all_healthy = all(
        comp.get("healthy", True) for comp in health_status["components"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "unhealthy"

    return health_status


# Status endpoint
@app.get("/status")
async def get_status():
    """Get detailed system status."""
    status = {
        "status": "running",
        "timestamp": "2025-08-22T00:00:00Z",
        "version": "1.0.0",
        "environment": config.environment,
        "components": {},
    }

    # MT5 status
    if mt5_executor:
        try:
            connected = mt5_executor.is_connected
            status["components"]["mt5"] = {
                "connected": connected,
                "account_info": (
                    await mt5_executor.get_account_info() if connected else None
                ),
            }
        except Exception as e:
            status["components"]["mt5"] = {"connected": False, "error": str(e)}

    # Socket.IO bridge status
    if socketio_bridge:
        status["components"]["bridge"] = socketio_bridge.get_status()

    # Telegram bot status
    if telegram_bot:
        status["components"]["telegram"] = {
            "running": telegram_bot.is_running,
            "chat_id": config.telegram.chat_id,
        }

    # Manager statuses
    if position_manager:
        status["components"]["position_manager"] = {
            "running": position_manager.is_running,
            "active_positions": len(await position_manager.get_positions()),
        }

    if trailing_manager:
        status["components"]["trailing_manager"] = {
            "running": trailing_manager.is_running,
            "config": trailing_manager.get_config(),
        }

    return status


# Configuration endpoint
@app.get("/config")
async def get_config():
    """Get application configuration (non-sensitive)."""
    return {
        "environment": config.environment,
        "app": {
            "name": config.app.name,
            "version": config.app.version,
            "debug": config.app.debug,
        },
        "database": {
            "url": (
                str(config.database.url).replace(config.database.password, "***")
                if config.database.password
                else str(config.database.url)
            )
        },
        "trading": {
            "risk_management": config.trading.risk_management,
            "position_sizing": config.trading.position_sizing,
            "trailing_stop": config.trading.trailing_stop,
            "take_profit": config.trading.take_profit,
        },
        "telegram": {
            "enabled": bool(config.telegram.bot_token),
            "chat_id": config.telegram.chat_id,
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app", host="0.0.0.0", port=8000, reload=True, log_level="info"
    )
