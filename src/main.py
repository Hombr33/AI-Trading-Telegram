"""
AI Trading Bot - Main Application
Main FastAPI application with Socket.IO, Telegram bot, and trading execution.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import socketio
from socketio import AsyncServer

from src.core.config import config
from src.core.logging import (
    get_logger,
    log_system_event,
    print_banner,
    print_status_table,
    log_error_with_context,
)
from .core.workflow import workflow_manager, performance_monitor
from .core.health_monitor import health_monitor
from .core.error_handler import ErrorContext
from .bridge.socketio_bridge import SocketIOBridge
from .execution.platform_manager import PlatformManager
from .execution.order_manager import OrderManager
from .execution.position_manager import PositionManager
from .execution.trailing_manager import TrailingManager
from .telegram_bot.core.trading_bot import TradingBot
from .services.signal_generation_service import SignalGenerationService
from .services.auto_trading_service import AutoTradingService

# Import MT5/AioMQL only on Windows
import sys
if sys.platform == "win32":
    try:
        from .execution.aiomql_executor import AioMQLExecutor
    except ImportError:
        AioMQLExecutor = None
        logger.warning("AioMQL executor not available on Windows")
else:
    AioMQLExecutor = None

# Import API routes
from src.api.routes import health, v1, bridge, trading

# Get logger
logger = get_logger(__name__)

# Global instances for API routes
telegram_bot: TradingBot = None
socketio_bridge: SocketIOBridge = None
platform_manager: PlatformManager = None
order_manager: OrderManager = None
position_manager: PositionManager = None
trailing_manager: TrailingManager = None
signal_generation_service: SignalGenerationService = None
auto_trading_service: AutoTradingService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global telegram_bot, socketio_bridge, platform_manager, order_manager, position_manager, trailing_manager, signal_generation_service, auto_trading_service

    # Print startup banner
    print_banner(
        "AI Trading Bot Starting",
        "Initializing components and establishing connections...",
        "cyan",
    )

    try:
        # Initialize Platform Manager (supports MT5 + Crypto exchanges)
        logger.info("Initializing platform manager...")
        platform_manager = PlatformManager(config)
        
        # Connect to all configured platforms
        logger.info("Connecting to trading platforms...")
        connection_results = await platform_manager.connect_all()
        
        connected_platforms = [name for name, success in connection_results.items() if success]
        failed_platforms = [name for name, success in connection_results.items() if not success]
        
        if connected_platforms:
            logger.info(f"Connected to platforms: {', '.join(connected_platforms)}")
        if failed_platforms:
            logger.warning(f"Failed to connect to platforms: {', '.join(failed_platforms)}")
        
        if not connected_platforms:
            logger.warning("No platforms connected, continuing with mock mode")

        # Initialize managers with platform manager
        logger.info("Initializing trading managers...")
        order_manager = OrderManager(platform_manager, config.trading)
        position_manager = PositionManager(platform_manager, config.trading)
        trailing_manager = TrailingManager(platform_manager, config.trading)

        # Initialize Socket.IO bridge
        logger.info("Initializing Socket.IO bridge...")
        socketio_bridge = SocketIOBridge(config.bridge)

        # Initialize Telegram bot
        logger.info("Initializing Telegram bot...")
        telegram_bot = TradingBot(config.telegram)
        
        # Setup Telegram bot (initialize application and handlers)
        logger.info("Setting up Telegram bot...")
        if not await telegram_bot.setup():
            logger.error("Failed to setup Telegram bot")
            raise RuntimeError("Telegram bot setup failed")

        # Set global instances for API routes
        bridge.set_global_instances(order_manager, telegram_bot)
        trading.order_manager = order_manager
        trading.position_manager = position_manager
        trading.telegram_bot = telegram_bot

        # Initialize auto trading services
        logger.info("Initializing auto trading services...")
        signal_generation_service = SignalGenerationService(config, telegram_bot)
        auto_trading_service = AutoTradingService(config, platform_manager, telegram_bot)

        # Start health monitoring
        logger.info("Starting health monitoring...")
        await health_monitor.start_monitoring()

        # Start all components in parallel
        logger.info("Starting all components in sequence...")

        # 1. Start FastAPI first (happens automatically with the lifespan context)
        logger.info("FastAPI application initialized")

        # 2. Start Socket.IO bridge
        await socketio_bridge.connect()
        logger.info("Socket.IO bridge connected successfully")

        # 3. Start managers as background tasks with error handling
        logger.info("Starting trading managers...")
        position_task = asyncio.create_task(position_manager.start())
        trailing_task = asyncio.create_task(trailing_manager.start())
        
        # 4. Start MT5 connection in background (non-blocking)
        async def connect_mt5_background():
            """Connect to MT5 in the background without blocking startup."""
            try:
                logger.info("Connecting to MT5 in background...")
                if await mt5_executor.connect():
                    logger.info("MT5 connected successfully")
                else:
                    logger.warning("Failed to connect to MT5, continuing with mock mode")
            except Exception as e:
                logger.error(f"Error connecting to MT5: {e}, continuing with mock mode")
        
        # 4. Start Telegram bot (needed for auto services)
        logger.info("Starting Telegram bot...")
        await telegram_bot.start()
        
        # 5. Start auto trading services if enabled
        if config.auto_trading.enabled:
            logger.info("Starting auto trading services...")
            if config.auto_trading.auto_signal_generation:
                logger.info("Starting signal generation service...")
                await signal_generation_service.start()
            
            logger.info("Starting auto trading execution service...")
            await auto_trading_service.start()
        else:
            logger.info("Auto trading is disabled in configuration")

        # Record startup success
        log_system_event(
            "main", "startup", "AI Trading Bot application started successfully"
        )

        # Print status table
        status_data = {
            "MT5 Executor": {
                "status": "connecting",
                "details": "Connecting in background",
            },
            "Socket.IO Bridge": {
                "status": "connected",
                "details": "Ready for EA connections",
            },
            "Position Manager": {
                "status": "running",
                "details": "Background task active",
            },
            "Trailing Manager": {
                "status": "running",
                "details": "Background task active",
            },
            "Telegram Bot": {"status": "running", "details": "Ready for commands"},
        }
        print_status_table(status_data)

        yield

    except Exception as e:
        log_error_with_context(e, {"component": "startup", "action": "initialization"})
        raise
    finally:
        # Enhanced shutdown sequence
        logger.info("Shutting down AI Trading Bot...")

        try:
            # Stop health monitoring
            await health_monitor.stop_monitoring()

            # Stop auto trading services first
            if auto_trading_service:
                logger.info("Stopping auto trading service...")
                await auto_trading_service.stop()
            
            if signal_generation_service:
                logger.info("Stopping signal generation service...")
                await signal_generation_service.stop()

            # Stop managers in reverse order
            if 'trailing_manager' in locals():
                await trailing_manager.stop()
            if 'position_manager' in locals():
                await position_manager.stop()

            # Stop Telegram bot gracefully
            if 'telegram_bot' in locals():
                logger.info("Stopping Telegram bot...")
                await telegram_bot.stop()
                logger.info("Telegram bot stopped (any polling cancellation messages are normal)")

            # Disconnect Socket.IO bridge
            if 'socketio_bridge' in locals():
                await socketio_bridge.disconnect()

            # Disconnect all trading platforms
            if platform_manager:
                await platform_manager.disconnect_all()

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
            "platform_manager": (
                len(platform_manager.get_platform_status()["connected_platforms"]) > 0
                if platform_manager else False
            ),
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
            "auto_trading": auto_trading_service.is_running if auto_trading_service else False,
            "signal_generation": signal_generation_service.is_running if signal_generation_service else False,
        },
    }


# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with comprehensive monitoring."""
    try:
        # Get health monitor status
        health_summary = health_monitor.get_health_summary()
        
        # Get performance metrics
        performance_summary = performance_monitor.get_performance_summary()
        
        # Component-specific health checks
        components = {}
        
        # Check platform connections
        if platform_manager:
            try:
                platform_status = platform_manager.get_platform_status()
                components["platforms"] = {
                    "connected_platforms": platform_status["connected_platforms"],
                    "total_platforms": platform_status["total_platforms"],
                    "primary_platform": platform_status["primary_platform"],
                    "healthy": platform_status["connected_platforms"] > 0,
                    "details": platform_status["platforms"]
                }
            except Exception as e:
                components["platforms"] = {
                    "status": "error",
                    "healthy": False,
                    "error": str(e),
                }

        # Check Socket.IO bridge
        if socketio_bridge:
            bridge_status = socketio_bridge.get_status()
            components["bridge"] = {
                "status": "connected" if bridge_status["connected"] else "disconnected",
                "healthy": bridge_status["connected"],
                "fallback_enabled": bridge_status.get("fallback_enabled", False)
            }

        # Check Telegram bot
        if telegram_bot:
            components["telegram"] = {
                "status": "running" if telegram_bot.is_running else "stopped",
                "healthy": telegram_bot.is_running,
            }

        # Check managers
        if position_manager:
            components["position_manager"] = {
                "status": "running" if position_manager.is_running else "stopped",
                "healthy": position_manager.is_running,
            }

        if trailing_manager:
            components["trailing_manager"] = {
                "status": "running" if trailing_manager.is_running else "stopped",
                "healthy": trailing_manager.is_running,
            }

        # Calculate overall health
        healthy_components = sum(1 for comp in components.values() if comp.get("healthy", False))
        total_components = len(components)
        health_percentage = (healthy_components / total_components * 100) if total_components > 0 else 0
        
        overall_status = "healthy"
        if health_percentage < 50:
            overall_status = "critical"
        elif health_percentage < 80:
            overall_status = "warning"

        return {
            "status": overall_status,
            "health_percentage": health_percentage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": "1.0.0",
            "uptime_seconds": performance_summary.get("uptime_seconds", 0),
            "components": components,
            "system_health": health_summary,
            "performance": performance_summary
        }
        
    except Exception as e:
        log_error_with_context(e, {"operation": "health_check"})
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }


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
