"""
Multi-user service orchestrator for the trading system.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from .user_manager import UserManager
from .config_manager import ConfigManager
from ..bridge.ea_bridge import EABridge
from ..bridge.crypto_bridge import CryptoBridge
from ..bridge.signal_distributor import SignalDistributor
from ..telegram_bot.core.trading_bot import TradingBot

logger = logging.getLogger(__name__)


class MultiUserService:
    """Orchestrates multi-user trading operations."""

    def __init__(self, telegram_bot_token: str):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.ea_bridge = EABridge()
        self.crypto_bridge = CryptoBridge()
        self.signal_distributor = SignalDistributor()
        # Use existing Telegram bot instance
        self.telegram_bot = None
        
        self._running = False
        self._tasks = []

    async def start(self) -> None:
        """Start the multi-user service."""
        if self._running:
            return

        logger.info("Starting multi-user trading service...")
        
        # Multi-user service doesn't manage its own bot instance
        # It uses the existing bot from the main application
        
        self._running = True
        logger.info("Multi-user trading service started")

    async def stop(self) -> None:
        """Stop the multi-user service."""
        if not self._running:
            return

        logger.info("Stopping multi-user trading service...")
        self._running = False
        
        logger.info("Multi-user trading service stopped")

    async def process_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and distribute trading signal to users."""
        try:
            logger.info(f"Processing signal for {signal_data.get('symbol', 'Unknown')}")
            
            # Validate signal format
            if not self._validate_signal_format(signal_data):
                logger.error("Invalid signal format")
                return {"success": False, "error": "Invalid signal format"}

            # Distribute signal via Telegram
            distribution_result = await self.telegram_bot.send_signal_to_users(signal_data)
            
            # Execute trades for users with auto-trading enabled
            execution_results = await self._execute_signal_trades(signal_data, distribution_result["distributed"])
            
            return {
                "success": True,
                "distributed_to": distribution_result["distributed"],
                "skipped": distribution_result["skipped"],
                "execution_results": execution_results
            }

        except Exception as e:
            logger.error(f"Failed to process signal: {e}")
            return {"success": False, "error": str(e)}

    async def _execute_signal_trades(self, signal_data: Dict[str, Any], user_ids: List[int]) -> Dict[str, Any]:
        """Execute trades for users with auto-trading enabled."""
        execution_results = {"successful": [], "failed": []}
        
        for telegram_id in user_ids:
            try:
                # Get user's trading configuration
                trading_config = await self.config_manager.get_user_config(telegram_id, "trading")
                
                if not trading_config or not trading_config.get("auto_execution_enabled", False):
                    continue

                # Check if user has platform connections
                connections = await self.user_manager.get_user_platform_connections(telegram_id)
                
                for connection in connections:
                    platform_type = connection["platform_type"]
                    
                    if platform_type == "mt5":
                        success = await self._execute_mt5_trade(telegram_id, signal_data, trading_config)
                    elif platform_type == "crypto":
                        success = await self._execute_crypto_trade(telegram_id, signal_data, trading_config)
                    else:
                        continue
                    
                    if success:
                        execution_results["successful"].append({
                            "telegram_id": telegram_id,
                            "platform": platform_type
                        })
                        break
                else:
                    execution_results["failed"].append({
                        "telegram_id": telegram_id,
                        "reason": "No active platform connections"
                    })

            except Exception as e:
                logger.error(f"Failed to execute trade for user {telegram_id}: {e}")
                execution_results["failed"].append({
                    "telegram_id": telegram_id,
                    "reason": str(e)
                })

        return execution_results

    async def _execute_mt5_trade(self, telegram_id: int, signal_data: Dict[str, Any], 
                                trading_config: Dict[str, Any]) -> bool:
        """Execute MT5 trade for user."""
        try:
            # Get first setup from signal
            setups = signal_data.get("setups", [])
            if not setups:
                return False

            setup = setups[0]
            
            # Prepare order data
            order_data = {
                "symbol": signal_data.get("symbol"),
                "type": setup.get("type"),  # BUY or SELL
                "entry_zone": setup.get("entry_zone"),
                "sl": setup.get("sl"),
                "tp": setup.get("tp", []),
                "confidence": signal_data.get("confidence", 0),
                "notes": setup.get("notes", "")
            }

            # Send order to EA
            result = await self.ea_bridge.send_order_to_ea(telegram_id, order_data)
            
            if result:
                # Send confirmation to user
                await self.telegram_bot.send_position_update(telegram_id, {
                    "type": "entry",
                    "symbol": order_data["symbol"],
                    "entry_price": result.get("entry_price"),
                    "position_type": order_data["type"],
                    "volume": result.get("volume"),
                    "sl": order_data["sl"],
                    "tp": order_data["tp"]
                })
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to execute MT5 trade for user {telegram_id}: {e}")
            return False

    async def _execute_crypto_trade(self, telegram_id: int, signal_data: Dict[str, Any], 
                                  trading_config: Dict[str, Any]) -> bool:
        """Execute crypto trade for user."""
        try:
            # Get first setup from signal
            setups = signal_data.get("setups", [])
            if not setups:
                return False

            setup = setups[0]
            
            # Prepare order data for crypto exchange
            order_data = {
                "symbol": signal_data.get("symbol").replace("/", ""),  # Remove slash for exchange format
                "side": "Buy" if setup.get("type") == "BUY" else "Sell",
                "orderType": "Market",  # Start with market orders for simplicity
                "quantity": self._calculate_crypto_quantity(telegram_id, signal_data, trading_config)
            }

            # Place order on crypto exchange
            result = await self.crypto_bridge.place_crypto_order(telegram_id, order_data)
            
            if result:
                # Send confirmation to user
                await self.telegram_bot.send_position_update(telegram_id, {
                    "type": "entry",
                    "symbol": signal_data.get("symbol"),
                    "entry_price": result.get("price"),
                    "position_type": setup.get("type"),
                    "volume": order_data["quantity"],
                    "sl": setup.get("sl"),
                    "tp": setup.get("tp")
                })
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to execute crypto trade for user {telegram_id}: {e}")
            return False

    def _calculate_crypto_quantity(self, telegram_id: int, signal_data: Dict[str, Any], 
                                 trading_config: Dict[str, Any]) -> float:
        """Calculate crypto trade quantity based on risk management."""
        # This is a simplified calculation - in production, you'd want more sophisticated position sizing
        risk_per_trade = trading_config.get("risk_per_trade_pct", 2.0) / 100
        default_quantity = 0.01  # Default small quantity
        
        # TODO: Implement proper position sizing based on account balance and risk
        return default_quantity

    async def _monitor_positions(self) -> None:
        """Monitor positions across all users."""
        while self._running:
            try:
                # Get all active users
                admin_users = await self.user_manager.get_all_users(self.user_manager.initial_admin_id)
                
                if admin_users:
                    active_users = [
                        user for user in admin_users 
                        if user["subscription_status"] == "active"
                    ]
                    
                    for user in active_users:
                        telegram_id = user["telegram_id"]
                        
                        # Check MT5 positions
                        await self._check_mt5_positions(telegram_id)
                        
                        # Check crypto positions
                        await self._check_crypto_positions(telegram_id)

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in position monitoring: {e}")
                await asyncio.sleep(60)

    async def _check_mt5_positions(self, telegram_id: int) -> None:
        """Check MT5 positions for user."""
        try:
            positions = await self.ea_bridge.get_positions_from_ea(telegram_id)
            
            if positions:
                # TODO: Implement position monitoring logic
                # - Check for stop loss hits
                # - Check for take profit hits
                # - Update trailing stops
                # - Send notifications for significant changes
                pass

        except Exception as e:
            logger.error(f"Error checking MT5 positions for user {telegram_id}: {e}")

    async def _check_crypto_positions(self, telegram_id: int) -> None:
        """Check crypto positions for user."""
        try:
            positions = await self.crypto_bridge.get_crypto_positions(telegram_id)
            
            if positions:
                # TODO: Implement crypto position monitoring logic
                pass

        except Exception as e:
            logger.error(f"Error checking crypto positions for user {telegram_id}: {e}")

    async def _health_check_loop(self) -> None:
        """Perform periodic health checks."""
        while self._running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                await asyncio.sleep(300)

    async def _perform_health_check(self) -> None:
        """Perform system health check."""
        try:
            # Check database connectivity
            # Check Telegram bot status
            # Check EA connections
            # Check crypto exchange connections
            # Send alerts if issues detected
            
            logger.debug("Health check completed")

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            await self.telegram_bot.send_admin_alert(f"Health check failed: {e}")

    def _validate_signal_format(self, signal_data: Dict[str, Any]) -> bool:
        """Validate signal data format."""
        required_fields = ["symbol", "bias", "setups", "confidence"]
        
        for field in required_fields:
            if field not in signal_data:
                return False

        setups = signal_data.get("setups", [])
        if not setups or not isinstance(setups, list):
            return False

        for setup in setups:
            if not isinstance(setup, dict):
                return False
            
            setup_required = ["type", "entry_zone", "sl"]
            for field in setup_required:
                if field not in setup:
                    return False

        return True

    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        try:
            bot_stats = await self.telegram_bot.get_bot_stats()
            
            return {
                "service_status": "running" if self._running else "stopped",
                "bot_stats": bot_stats,
                "active_tasks": len(self._tasks),
                "last_health_check": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {
                "service_status": "error",
                "error": str(e)
            }
