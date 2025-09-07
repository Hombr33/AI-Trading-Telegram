"""
AI Trading Bot - Main Application
Main FastAPI application with Socket.IO, Telegram bot, and trading execution.
"""

import asyncio
import os
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from socketio import AsyncServer

from src.core.config import config
from src.core.logging import (
    get_logger,
    log_error_with_context,
    log_system_event,
    print_banner,
    print_status_table,
)

logger = get_logger(__name__)

from .bridge.mt5_bridge_service import MT5BridgeService, shutdown_mt5_bridge_service
from .bridge.socketio_bridge import SocketIOBridge
from .common.interfaces import IPlatformManager, ISignalGenerationService
from .core.health_monitor import health_monitor
from .core.workflow import performance_monitor
from .execution.order_manager import OrderManager
from .execution.platform_manager import PlatformManager
from .execution.position_manager import PositionManager
from .execution.trailing_manager import TrailingManager
from .services.auto_trading_service import AutoTradingService
from .services.config_manager import ConfigManager
from .services.multi_user_service import MultiUserService
from .services.signal_generation_service import SignalGenerationService
from .services.user_manager import UserManager
from .telegram_bot.core.trading_bot import TradingBot

if sys.platform == "win32":
    try:
        from .execution.platforms.forex.aiomql_executor import AioMQLExecutor
        from .execution.platforms.forex.mt5_executor import MT5Executor
    except ImportError:
        AioMQLExecutor = None
        logger.warning("AioMQL executor not available on Windows")
else:
    AioMQLExecutor = None

# Import admin dashboard
from src.admin_dashboard.router import router as admin_router
from src.admin_dashboard.router import (
    set_multi_user_service as set_admin_multi_user_service,
)

# Import API routes
from src.api.routes import bridge, ea, health, multi_user, trading, v1

# Get logger
logger = get_logger(__name__)


# Remove conflicting signal handlers - let uvicorn handle shutdown gracefully

# Global instances for API routes
telegram_bot: TradingBot = None
start_time: datetime = None
socketio_bridge: SocketIOBridge = None
platform_manager: IPlatformManager = None
order_manager: OrderManager = None
position_manager: PositionManager = None
trailing_manager: TrailingManager = None
signal_generation_service: ISignalGenerationService = None
auto_trading_service: AutoTradingService = None
multi_user_service: MultiUserService = None
mt5_bridge_service: MT5BridgeService = None
user_manager: UserManager = None
config_manager: ConfigManager = None


# Global shutdown flag
shutdown_event = asyncio.Event()

# Global list to track background tasks
background_tasks = []

# Global flag for immediate shutdown
force_shutdown = False


async def monitor_shutdown_request():
    """Monitor for shutdown requests from system manager."""
    from src.core.system_manager import system_manager

    try:
        while True:
            # Check for shutdown request every second
            if await system_manager.wait_for_shutdown(timeout=1.0):
                logger.info("Shutdown requested by system manager")
                # Set the global shutdown event to trigger FastAPI shutdown
                shutdown_event.set()
                break
    except asyncio.CancelledError:
        logger.info("Shutdown monitor cancelled")
    except Exception as e:
        logger.error(f"Error in shutdown monitor: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals with immediate force shutdown."""
    global force_shutdown
    print(f"\n🛑 Received signal {signum}. Force shutting down...")
    force_shutdown = True
    shutdown_event.set()

    # Force exit after a very short delay
    import threading

    def force_exit():
        import time

        time.sleep(1)  # Wait only 1 second
        print("⚠️ Force exiting...")
        os._exit(1)

    # Start force exit timer in background
    exit_thread = threading.Thread(target=force_exit, daemon=True)
    exit_thread.start()


async def shutdown_handler(sig, loop):
    """Graceful shutdown handler for signals."""
    logger.info(f"Received exit signal {sig.name}...")
    shutdown_event.set()

    # Cancel all running tasks except current one
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    logger.info(f"Cancelling {len(tasks)} outstanding tasks")

    for task in tasks:
        task.cancel()

    # Wait for tasks to complete cancellation
    if tasks:
        try:
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=2.0,  # Reduced timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Some tasks did not complete cancellation in time")

    loop.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global telegram_bot, start_time, socketio_bridge, platform_manager, order_manager, position_manager, trailing_manager, signal_generation_service, auto_trading_service, multi_user_service, mt5_bridge_service, user_manager, config_manager

    # Set up signal handlers for proper Ctrl+C handling
    import signal

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Record startup time
    start_time = datetime.now(timezone.utc)

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

        connected_platforms = [
            name for name, success in connection_results.items() if success
        ]
        failed_platforms = [
            name for name, success in connection_results.items() if not success
        ]

        if connected_platforms:
            logger.info(f"Connected to platforms: {', '.join(connected_platforms)}")
        if failed_platforms:
            logger.warning(
                f"Failed to connect to platforms: {', '.join(failed_platforms)}"
            )

        if not connected_platforms:
            logger.warning("No platforms connected, continuing with mock mode")

        # Initialize managers with platform manager
        logger.info("Initializing trading managers...")
        order_manager = OrderManager(platform_manager, config.trading)
        position_manager = PositionManager(platform_manager, config.trading)

        # Initialize user and config managers
        logger.info("Initializing user and config managers...")
        user_manager = UserManager()
        config_manager = ConfigManager()

        # Initialize trailing manager with proper TrailingConfig
        from .execution.trailing_manager import TrailingConfig

        trailing_config = TrailingConfig()
        trailing_manager = TrailingManager(platform_manager, trailing_config)

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

        # Start Telegram bot polling
        logger.info("Starting Telegram bot polling...")
        bot_started = await telegram_bot.start()
        if not bot_started:
            logger.warning("Telegram bot failed to start - continuing in API-only mode")
            logger.warning("The system will run without Telegram notifications")
        # Don't raise error - continue in API-only mode
        # Set global instances for API routes
        bridge.set_global_instances(order_manager, telegram_bot)

        # Set global instances for EA routes
        from src.api.routes.ea import set_ea_globals

        set_ea_globals(user_manager, config_manager, order_manager, telegram_bot)

        # Initialize multi-user service
        logger.info("Initializing multi-user service...")
        multi_user_service = MultiUserService(config.telegram.bot_token)

        # Set telegram bot instance for multi-user service
        multi_user_service.set_telegram_bot(telegram_bot)

        # Set multi-user service for API routes
        multi_user.set_multi_user_service(multi_user_service)

        # Set multi-user service for admin dashboard
        set_admin_multi_user_service(multi_user_service)

        # Initialize auto trading services
        logger.info("Initializing auto trading services...")
        signal_generation_service = SignalGenerationService(config, telegram_bot)
        auto_trading_service = AutoTradingService(
            config, platform_manager, telegram_bot
        )

        # Set order manager for auto trading service
        auto_trading_service.order_manager = order_manager

        # Start health monitoring
        logger.info("Starting health monitoring...")
        await health_monitor.start_monitoring()

        # Start all components in parallel
        logger.info("Starting all components in sequence...")

        # 1. Start FastAPI first (happens automatically with the lifespan context)
        logger.info("FastAPI application initialized")

        # Start shutdown monitor task
        shutdown_monitor_task = asyncio.create_task(
            monitor_shutdown_request(), name="shutdown_monitor"
        )

        # 2. Start Socket.IO bridge
        await socketio_bridge.connect()
        logger.info("Socket.IO bridge connected successfully")

        # 2.5. Initialize MT5 Bridge Service
        logger.info("Initializing MT5 Bridge Service...")
        mt5_bridge_service = MT5BridgeService()
        await mt5_bridge_service.start()
        logger.info("MT5 Bridge Service started successfully")

        # 3. Start managers as background tasks with error handling
        logger.info("Starting trading managers...")
        position_task = asyncio.create_task(position_manager.start())
        trailing_task = asyncio.create_task(trailing_manager.start())

        # Track background tasks for proper shutdown
        background_tasks.extend([position_task, trailing_task])

        # 4. Start MT5 connection in background (non-blocking)
        async def connect_mt5_background():
            """Connect to MT5 in the background without blocking startup."""
            try:
                logger.info("Connecting to MT5 in background...")
                # Get MT5 executor from platform manager
                mt5_executor = (
                    platform_manager.get_executor("mt5") if platform_manager else None
                )
                if mt5_executor and hasattr(mt5_executor, "connect"):
                    if await mt5_executor.connect():
                        logger.info("MT5 connected successfully")
                    else:
                        logger.warning(
                            "Failed to connect to MT5, continuing with mock mode"
                        )
                        logger.debug(
                            "MT5 connection details: Login=%s, Server=%s",
                            config.mt5.login,
                            config.mt5.server,
                        )
                else:
                    logger.warning(
                        "MT5 executor not available, continuing with mock mode"
                    )
            except Exception as e:
                logger.error(f"Error connecting to MT5: {e}, continuing with mock mode")
                logger.debug("MT5 connection exception details", exc_info=True)

        # Start MT5 connection task and track it
        mt5_task = asyncio.create_task(connect_mt5_background())
        background_tasks.append(mt5_task)

        # 4. Start multi-user service (includes Telegram bot)
        logger.info("Starting multi-user service...")
        await multi_user_service.start()

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
            "MT5 Bridge Service": {
                "status": "running",
                "details": "Unified MT5 integration active",
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

        # Wait for shutdown event with timeout to prevent hanging
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=None)
        except asyncio.CancelledError:
            logger.info("Lifespan cancelled")
        except asyncio.TimeoutError:
            logger.info("Shutdown event timeout")

        # Check for force shutdown
        if force_shutdown:
            logger.info("Force shutdown requested, exiting immediately")
            # Still need to yield to satisfy the context manager
            yield
            return

        yield

    except Exception as e:
        log_error_with_context(e, {"component": "startup", "action": "initialization"})
        raise
    finally:
        # Enhanced shutdown sequence
        from src.core.system_manager import system_manager

        is_restart = system_manager.is_restart_requested()
        shutdown_reason = "restart" if is_restart else "shutdown"

        logger.info(f"Shutting down AI Trading Bot... (reason: {shutdown_reason})")

        try:
            # Cancel all background tasks first
            logger.info("Cancelling background tasks...")
            for task in background_tasks:
                if not task.done():
                    task.cancel()

            # Wait for tasks to complete cancellation with very short timeout
            if background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*background_tasks, return_exceptions=True),
                        timeout=1.0,  # Very short timeout for immediate shutdown
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        "Background tasks did not cancel in time - forcing shutdown"
                    )
                except Exception as e:
                    logger.error(f"Error cancelling background tasks: {e}")

            # If force shutdown, skip all other cleanup
            if force_shutdown:
                logger.info("Force shutdown - skipping detailed cleanup")
                return

            # Cancel shutdown monitor task
            if "shutdown_monitor_task" in locals():
                shutdown_monitor_task.cancel()
                try:
                    await shutdown_monitor_task
                except asyncio.CancelledError:
                    pass

            # Stop health monitoring
            await health_monitor.stop_monitoring()

            # Stop background managers first to prevent errors during shutdown
            logger.info("Stopping background managers...")
            try:
                if position_manager:
                    await position_manager.stop()
                if trailing_manager:
                    trailing_manager.running = False
            except Exception as e:
                logger.error(f"Error stopping managers: {e}")

            # Stop MT5 Bridge Service first
            logger.info("Stopping MT5 Bridge Service...")
            try:
                await shutdown_mt5_bridge_service()
                logger.info("MT5 Bridge Service stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping MT5 Bridge Service: {e}")

            # Stop services in reverse order
            logger.info("Stopping auto trading service...")
            try:
                await auto_trading_service.stop()
            except Exception as e:
                logger.error(f"Error stopping auto trading service: {e}")

            logger.info("Stopping signal generation service...")
            try:
                await signal_generation_service.stop()
            except Exception as e:
                logger.error(f"Error stopping signal generation service: {e}")

            # Stop multi-user service (includes Telegram bot)
            if multi_user_service:
                logger.info("Stopping multi-user service...")
                try:
                    await multi_user_service.stop()
                    logger.info("Multi-user service stopped successfully")
                except Exception as e:
                    logger.error(f"Error stopping multi-user service: {e}")

            # Stop legacy Telegram bot if still running
            if telegram_bot:
                logger.info("Stopping legacy Telegram bot...")
                try:
                    # Use a shorter timeout to prevent hanging
                    await asyncio.wait_for(telegram_bot.stop(), timeout=2.0)
                    logger.info("Legacy Telegram bot stopped successfully")
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    logger.info("Legacy Telegram bot shutdown completed")
                except Exception as e:
                    logger.warning(f"Error stopping legacy Telegram bot: {e}")
                    telegram_bot.running = False

            # Disconnect Socket.IO bridge
            if "socketio_bridge" in locals():
                await socketio_bridge.disconnect()

            # Disconnect all trading platforms
            if platform_manager:
                await platform_manager.disconnect_all()

            log_system_event(
                "main",
                shutdown_reason,
                f"AI Trading Bot application {shutdown_reason} completed successfully",
            )

        except Exception as e:
            log_error_with_context(
                e, {"component": shutdown_reason, "action": "cleanup"}
            )


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
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],  # Restrict to localhost only
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
app.include_router(multi_user.router, prefix="/api/v1/multi-user", tags=["multi-user"])
app.include_router(ea.router, prefix="/api/v1/ea", tags=["ea"])
app.include_router(admin_router, tags=["admin-dashboard"])

# Mount static files for admin dashboard

admin_static_path = os.path.join(os.path.dirname(__file__), "admin_dashboard", "static")
if os.path.exists(admin_static_path):
    app.mount(
        "/admin/static", StaticFiles(directory=admin_static_path), name="admin-static"
    )


# API info endpoint
@app.get("/api")
async def api_info():
    """API information endpoint."""
    return {
        "name": "AI Trading Bot",
        "version": "1.0.0",
        "description": "Institutional-grade AI-powered automated trading bot",
        "status": "running",
        "components": {
            "platform_manager": (
                len(platform_manager.get_platform_status()["connected_platforms"]) > 0
                if platform_manager
                else False
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
            "auto_trading": (
                auto_trading_service.is_running if auto_trading_service else False
            ),
            "signal_generation": (
                signal_generation_service.is_running
                if signal_generation_service
                else False
            ),
        },
    }


# Status endpoint
@app.get("/status")
async def get_status():
    """Get detailed system status."""
    try:
        # Basic system info
        uptime = (
            datetime.now(timezone.utc) - start_time
            if "start_time" in globals()
            else None
        )

        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime": str(uptime) if uptime else "Unknown",
            "environment": config.environment,
            "healthy": True,
            "components": {
                "platform_manager": platform_manager is not None,
                "position_manager": position_manager is not None
                and getattr(position_manager, "is_running", False),
                "trailing_manager": trailing_manager is not None
                and getattr(trailing_manager, "is_running", False),
                "telegram_bot": telegram_bot is not None
                and getattr(telegram_bot, "is_running", False),
                "socketio_bridge": socketio_bridge is not None,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
            "healthy": False,
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
                    "details": platform_status["platforms"],
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
                "fallback_enabled": bridge_status.get("fallback_enabled", False),
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
        healthy_components = sum(
            1 for comp in components.values() if comp.get("healthy", False)
        )
        total_components = len(components)
        health_percentage = (
            (healthy_components / total_components * 100) if total_components > 0 else 0
        )

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
            "performance": performance_summary,
        }

    except Exception as e:
        log_error_with_context(e, {"operation": "health_check"})
        return {
            "status": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }


# Root endpoint - Simple dashboard
@app.get("/")
async def dashboard():
    """Main dashboard showing system status."""
    try:
        status_data = await get_status()

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Trading Bot Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
                .status-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .status-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #007bff; }}
                .status-healthy {{ border-left-color: #28a745; }}
                .status-warning {{ border-left-color: #ffc107; }}
                .status-error {{ border-left-color: #dc3545; }}
                .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
                .metric-label {{ font-weight: bold; }}
                .metric-value {{ color: #666; }}
                .timestamp {{ text-align: center; color: #888; font-size: 0.9em; }}
                .api-links {{ text-align: center; margin-top: 30px; }}
                .api-links a {{ margin: 0 15px; color: #007bff; text-decoration: none; }}
                .api-links a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🤖 AI Trading Bot Dashboard</h1>
                    <p>Real-time system monitoring and status</p>
                </div>

                <div class="status-grid">
                    <div class="status-card status-{'healthy' if status_data.get('healthy', False) else 'error'}">
                        <h3>System Status</h3>
                        <div class="metric">
                            <span class="metric-label">Status:</span>
                            <span class="metric-value">{'🟢 Healthy' if status_data.get('healthy', False) else '🔴 Error'}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Uptime:</span>
                            <span class="metric-value">{status_data.get('uptime', 'Unknown')}</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Environment:</span>
                            <span class="metric-value">{status_data.get('environment', 'Unknown')}</span>
                        </div>
                    </div>

                    <div class="status-card">
                        <h3>Platform Connections</h3>
                        <div class="metric">
                            <span class="metric-label">MT5 Executor:</span>
                            <span class="metric-value">🔄 Connecting</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Socket.IO Bridge:</span>
                            <span class="metric-value">🟢 Connected</span>
                        </div>
                    </div>

                    <div class="status-card">
                        <h3>Trading Managers</h3>
                        <div class="metric">
                            <span class="metric-label">Position Manager:</span>
                            <span class="metric-value">🟢 Running</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Trailing Manager:</span>
                            <span class="metric-value">🟢 Running</span>
                        </div>
                    </div>

                    <div class="status-card">
                        <h3>Communication</h3>
                        <div class="metric">
                            <span class="metric-label">Telegram Bot:</span>
                            <span class="metric-value">🟢 Ready</span>
                        </div>
                        <div class="metric">
                            <span class="metric-label">Web API:</span>
                            <span class="metric-value">🟢 Online</span>
                        </div>
                    </div>
                </div>

                <div class="api-links">
                    <h3>API Endpoints</h3>
                    <a href="/status">System Status</a>
                    <a href="/health">Health Check</a>
                    <a href="/config">Configuration</a>
                    <a href="/docs">API Documentation</a>
                </div>

                <div class="timestamp">
                    Last updated: {status_data.get('timestamp', 'Unknown')}
                </div>
            </div>
        </body>
        </html>
        """

        return HTMLResponse(content=html_content)

    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Dashboard Error</h1><p>Error loading dashboard: {str(e)}</p>"
        )


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
