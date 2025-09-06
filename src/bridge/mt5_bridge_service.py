"""
MT5 Bridge Service - Unified service for MT5 EA communication and data flow.
Integrates EA Bridge, Socket.IO Bridge, and Trading Data Service.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from src.bridge.ea_bridge import EABridge
from src.bridge.socketio_bridge import SocketIOBridge
from src.core.config import AppConfig, BridgeConfig
from src.core.logging import get_logger
from src.services.signal_generation_service import SignalGenerationService
from src.telegram_bot.services.trading_data_service import TradingDataService

logger = get_logger(__name__)


class MT5BridgeService:
    """Unified MT5 Bridge service for EA communication and data flow."""

    def __init__(self):
        self.config = AppConfig()
        self.bridge_config = BridgeConfig()

        # Initialize components
        self.ea_bridge = EABridge()
        self.socketio_bridge = SocketIOBridge(self.bridge_config)
        self.trading_data_service = TradingDataService()
        self.signal_service: Optional[SignalGenerationService] = None

        # State management
        self.is_running = False
        self.callbacks: Dict[str, List[Callable]] = {}

        # Setup event handlers
        self._setup_event_handlers()

    def _setup_event_handlers(self):
        """Setup event handlers for bridge communication."""
        # Register for Socket.IO events
        asyncio.create_task(
            self.socketio_bridge.on_event("order", self._handle_order_event)
        )
        asyncio.create_task(
            self.socketio_bridge.on_event("signal", self._handle_signal_event)
        )
        asyncio.create_task(
            self.socketio_bridge.on_event(
                "position_update", self._handle_position_update
            )
        )
        asyncio.create_task(
            self.socketio_bridge.on_event("risk_alert", self._handle_risk_alert)
        )

    async def start(self):
        """Start the MT5 bridge service."""
        try:
            logger.info("Starting MT5 Bridge Service...")

            # Connect Socket.IO bridge
            await self.socketio_bridge.connect()

            # Initialize signal service if available
            try:
                # Get config and telegram_bot from global instances
                from src.core.config import config
                from src.main import telegram_bot

                self.signal_service = SignalGenerationService(config, telegram_bot)
                logger.info("Signal generation service initialized")
            except Exception as e:
                logger.warning(f"Signal service not available: {e}")
                self.signal_service = None

            self.is_running = True
            logger.info("MT5 Bridge Service started successfully")

        except Exception as e:
            logger.error(f"Failed to start MT5 Bridge Service: {e}")
            raise

    async def stop(self):
        """Stop the MT5 bridge service."""
        try:
            logger.info("Stopping MT5 Bridge Service...")

            self.is_running = False

            # Disconnect components
            await self.socketio_bridge.disconnect()
            await self.trading_data_service.close()

            logger.info("MT5 Bridge Service stopped")

        except Exception as e:
            logger.error(f"Error stopping MT5 Bridge Service: {e}")

    # Telegram Bot Integration Methods

    async def get_positions_for_telegram(
        self, telegram_id: int
    ) -> List[Dict[str, Any]]:
        """Get positions for Telegram bot display."""
        try:
            # Try EA Bridge first for user-specific data
            positions = await self.ea_bridge.get_positions_from_ea(telegram_id)
            if positions:
                logger.info(
                    f"Retrieved {len(positions)} positions from EA for user {telegram_id}"
                )
                return positions

            # Fallback to trading data service
            positions = await self.trading_data_service.get_positions()
            logger.info(
                f"Retrieved {len(positions)} positions from trading data service"
            )
            return positions

        except Exception as e:
            logger.error(f"Error getting positions for Telegram: {e}")
            return []

    async def get_orders_for_telegram(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get orders for Telegram bot display."""
        try:
            # Use trading data service (EA Bridge doesn't have get_orders method)
            orders = await self.trading_data_service.get_orders()
            logger.info(f"Retrieved {len(orders)} orders from trading data service")
            return orders

        except Exception as e:
            logger.error(f"Error getting orders for Telegram: {e}")
            return []

    async def get_account_info_for_telegram(self, telegram_id: int) -> Dict[str, Any]:
        """Get account info for Telegram bot display."""
        try:
            # Try EA Bridge first for user-specific data
            account_info = await self.ea_bridge.get_account_info_from_ea(telegram_id)
            if account_info:
                logger.info(f"Retrieved account info from EA for user {telegram_id}")
                return account_info

            # Fallback to trading data service
            account_info = await self.trading_data_service.get_account_info()
            logger.info("Retrieved account info from trading data service")
            return account_info

        except Exception as e:
            logger.error(f"Error getting account info for Telegram: {e}")
            return await self.trading_data_service._get_account_info_from_db()

    async def get_signals_for_telegram(
        self, telegram_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get signals for Telegram bot display."""
        try:
            signals = await self.trading_data_service.get_signals(limit=limit)
            logger.info(f"Retrieved {len(signals)} signals for Telegram")
            return signals

        except Exception as e:
            logger.error(f"Error getting signals for Telegram: {e}")
            return []

    # Trading Operations

    async def send_order_to_ea(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send trading order to EA via bridge."""
        try:
            # Try EA Bridge first
            result = await self.ea_bridge.send_order_to_ea(telegram_id, order_data)
            if result:
                logger.info(f"Order sent via EA Bridge for user {telegram_id}")
                return result

            # Try Socket.IO Bridge as fallback
            socketio_result = await self.socketio_bridge.send_order(order_data)
            if socketio_result.get("success"):
                logger.info(f"Order sent via Socket.IO Bridge for user {telegram_id}")
                return socketio_result

            logger.warning(f"Failed to send order for user {telegram_id}")
            return None

        except Exception as e:
            logger.error(f"Error sending order to EA: {e}")
            return None

    async def send_signal_to_ea(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send trading signal to EA via bridge."""
        try:
            # Send via Socket.IO Bridge (signals are broadcast, not user-specific)
            result = await self.socketio_bridge.send_signal(signal_data)
            logger.info(
                f"Signal sent via Socket.IO Bridge: {signal_data.get('signal_id')}"
            )
            return result

        except Exception as e:
            logger.error(f"Error sending signal to EA: {e}")
            return {"success": False, "error": str(e)}

    async def modify_position(
        self,
        telegram_id: int,
        position_ticket: int,
        new_sl: float = None,
        new_tp: float = None,
    ) -> bool:
        """Modify position in EA."""
        try:
            success = await self.ea_bridge.modify_position_in_ea(
                telegram_id, position_ticket, new_sl, new_tp
            )
            if success:
                logger.info(
                    f"Position {position_ticket} modified for user {telegram_id}"
                )
            return success

        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return False

    async def close_position(
        self, telegram_id: int, position_ticket: int, volume: float = None
    ) -> bool:
        """Close position in EA."""
        try:
            success = await self.ea_bridge.close_position_in_ea(
                telegram_id, position_ticket, volume
            )
            if success:
                logger.info(f"Position {position_ticket} closed for user {telegram_id}")
            return success

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    # Event Handlers

    async def _handle_order_event(self, data: Dict[str, Any]):
        """Handle order events from EA."""
        logger.info(f"Order event received: {data}")
        await self._trigger_callbacks("order", data)

    async def _handle_signal_event(self, data: Dict[str, Any]):
        """Handle signal events from EA."""
        logger.info(f"Signal event received: {data}")
        await self._trigger_callbacks("signal", data)

    async def _handle_position_update(self, data: Dict[str, Any]):
        """Handle position update events from EA."""
        logger.info(f"Position update received: {data}")
        await self._trigger_callbacks("position_update", data)

    async def _handle_risk_alert(self, data: Dict[str, Any]):
        """Handle risk alert events from EA."""
        logger.info(f"Risk alert received: {data}")
        await self._trigger_callbacks("risk_alert", data)

    # Callback Management

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for specific events."""
        if event not in self.callbacks:
            self.callbacks[event] = []
        self.callbacks[event].append(callback)
        logger.info(f"Callback registered for event: {event}")

    async def _trigger_callbacks(self, event: str, data: Dict[str, Any]):
        """Trigger all callbacks for a specific event."""
        if event in self.callbacks:
            for callback in self.callbacks[event]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"Error in callback for event {event}: {e}")

    # Status and Health

    def get_status(self) -> Dict[str, Any]:
        """Get overall bridge service status."""
        return {
            "is_running": self.is_running,
            "socketio_status": self.socketio_bridge.get_status(),
            "trading_data_available": self.trading_data_service.is_mt5_available(),
            "signal_service_available": self.signal_service is not None,
            "registered_callbacks": list(self.callbacks.keys()),
        }

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        status = {
            "bridge_service": "healthy" if self.is_running else "stopped",
            "socketio_bridge": (
                "connected" if self.socketio_bridge.connected else "disconnected"
            ),
            "mt5_connection": (
                "available"
                if self.trading_data_service.is_mt5_available()
                else "unavailable"
            ),
            "signal_service": "available" if self.signal_service else "unavailable",
            "timestamp": datetime.now().isoformat(),
        }

        # Test EA Bridge connectivity (if user-specific testing is possible)
        try:
            # This would need a test user ID in production
            test_endpoint = await self.ea_bridge.get_server_endpoint()
            status["ea_endpoint"] = test_endpoint
        except Exception as e:
            status["ea_endpoint_error"] = str(e)

        return status


# Global instance for use across the application
mt5_bridge_service: Optional[MT5BridgeService] = None


async def get_mt5_bridge_service() -> MT5BridgeService:
    """Get or create the global MT5 bridge service instance."""
    global mt5_bridge_service

    if mt5_bridge_service is None:
        mt5_bridge_service = MT5BridgeService()
        await mt5_bridge_service.start()

    return mt5_bridge_service


async def shutdown_mt5_bridge_service():
    """Shutdown the global MT5 bridge service instance."""
    global mt5_bridge_service

    if mt5_bridge_service:
        await mt5_bridge_service.stop()
        mt5_bridge_service = None
