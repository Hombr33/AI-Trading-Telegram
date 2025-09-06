"""
Trading data service for Telegram bot - provides real trading data.
"""

from typing import Any, Dict, List, Optional

from src.core.config import AppConfig
from src.core.logging import get_logger
from src.database.session import SessionLocal
from src.execution.platforms.forex.mt5_executor import MT5Executor
from src.models.orders import Order
from src.models.positions import Position
from src.models.signals import Signal

logger = get_logger(__name__)


class TradingDataService:
    """Service for providing real trading data to Telegram bot."""

    def __init__(self):
        self.config = AppConfig()
        self.mt5_executor: Optional[MT5Executor] = None
        self._initialize_mt5()

    def _initialize_mt5(self):
        """Initialize MT5 executor if available."""
        try:
            if hasattr(self.config, "mt5"):
                self.mt5_executor = MT5Executor(self.config.mt5)
                logger.info("MT5 executor initialized for trading data service")
            else:
                logger.warning("MT5 configuration not available")
        except Exception as e:
            logger.error(f"Failed to initialize MT5 executor: {e}")
            self.mt5_executor = None

    async def get_positions(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get real positions from MT5 or database.

        Args:
            user_id: Optional user ID to filter positions

        Returns:
            List of position dictionaries
        """
        try:
            # Try MT5 first for real-time data
            if self.mt5_executor and self.mt5_executor.connected:
                positions = await self.mt5_executor.get_positions()
                if positions:
                    return [
                        {
                            "symbol": pos.symbol,
                            "type": "BUY" if pos.type == 0 else "SELL",
                            "volume": pos.volume,
                            "price_open": pos.price_open,
                            "price_current": pos.price_current,
                            "profit": pos.profit,
                            "time": str(pos.time),
                            "ticket": pos.ticket,
                            "stop_loss": pos.sl,
                            "take_profit": pos.tp,
                            "swap": pos.swap,
                            "commission": pos.commission,
                        }
                        for pos in positions
                    ]

            # Fallback to database
            return await self._get_positions_from_db(user_id)

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return await self._get_positions_from_db(user_id)

    async def get_orders(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get real pending orders from MT5 or database.

        Args:
            user_id: Optional user ID to filter orders

        Returns:
            List of order dictionaries
        """
        try:
            # Try MT5 first for real-time data
            if self.mt5_executor and self.mt5_executor.connected:
                orders = await self.mt5_executor.get_orders()
                if orders:
                    return [
                        {
                            "symbol": order.symbol,
                            "type": "BUY" if order.type in [2, 4] else "SELL",
                            "volume": order.volume_current,
                            "price_open": order.price_open,
                            "time": str(order.time_setup),
                            "ticket": order.ticket,
                            "stop_loss": order.sl,
                            "take_profit": order.tp,
                        }
                        for order in orders
                    ]

            # Fallback to database
            return await self._get_orders_from_db(user_id)

        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return await self._get_orders_from_db(user_id)

    async def get_account_info(self) -> Dict[str, Any]:
        """Get real account information from MT5 or database.

        Returns:
            Account information dictionary
        """
        try:
            # Try MT5 first for real-time data
            if self.mt5_executor and self.mt5_executor.connected:
                account_info = await self.mt5_executor.get_account_info()
                if account_info:
                    positions = await self.get_positions()
                    orders = await self.get_orders()

                    return {
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "margin": account_info.margin,
                        "free_margin": account_info.margin_free,
                        "margin_level": account_info.margin_level,
                        "profit_loss": account_info.profit,
                        "open_positions": len(positions),
                        "pending_orders": len(orders),
                        "currency": account_info.currency,
                        "leverage": account_info.leverage,
                        "server": account_info.server,
                        "name": account_info.name,
                        "total_profit": account_info.profit,
                    }

            # Fallback to database
            return await self._get_account_info_from_db()

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return await self._get_account_info_from_db()

    async def get_signals(
        self, limit: int = 50, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get trading signals from database.

        Args:
            limit: Maximum number of signals to return
            user_id: Optional user ID to filter signals

        Returns:
            List of signal dictionaries
        """
        try:
            session = SessionLocal()
            query = session.query(Signal).filter(Signal.status == "ACTIVE")

            if user_id:
                # Filter signals based on user preferences and subscriptions
                try:
                    from ...services.config_manager import ConfigManager

                    config_manager = ConfigManager()

                    # Get user signal preferences
                    signal_prefs = await config_manager.get_user_config(
                        user_id, "signal_preferences"
                    )

                    if signal_prefs:
                        # Filter by subscribed symbols
                        subscribed_symbols = signal_prefs.get("subscribed_symbols", [])
                        if subscribed_symbols:
                            query = query.filter(Signal.symbol.in_(subscribed_symbols))

                        # Filter by minimum confidence
                        min_confidence = signal_prefs.get("min_confidence", 0)
                        if min_confidence > 0:
                            query = query.filter(Signal.confidence >= min_confidence)

                        # Filter by signal types
                        allowed_biases = signal_prefs.get(
                            "allowed_biases", ["BULLISH", "BEARISH"]
                        )
                        if allowed_biases:
                            query = query.filter(Signal.bias.in_(allowed_biases))

                except Exception as e:
                    logger.error(f"Error applying user-specific signal filtering: {e}")
                    # Continue with unfiltered query if filtering fails

            signals = query.order_by(Signal.created_at.desc()).limit(limit).all()

            return [
                {
                    "id": signal.id,
                    "signal_id": signal.signal_id,
                    "symbol": signal.symbol,
                    "bias": signal.bias,
                    "confidence": signal.confidence,
                    "setups": signal.setups,
                    "status": signal.status,
                    "created_at": (
                        signal.created_at.isoformat() if signal.created_at else None
                    ),
                    "expires_at": (
                        signal.expires_at.isoformat() if signal.expires_at else None
                    ),
                }
                for signal in signals
            ]
        except Exception as e:
            logger.error(f"Error getting signals: {e}")
            return []
        finally:
            session.close()

    async def _get_positions_from_db(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get positions from database as fallback."""
        try:
            session = SessionLocal()
            query = session.query(Position).filter(Position.is_active)

            if user_id:
                query = query.filter(Position.user_id == user_id)

            positions = query.all()

            return [
                {
                    "symbol": pos.instrument.symbol if pos.instrument else "Unknown",
                    "type": pos.direction,
                    "volume": pos.volume,
                    "price_open": pos.open_price,
                    "price_current": pos.current_price,
                    "profit": pos.unrealized_pnl,
                    "time": pos.open_time,
                    "ticket": pos.mt_ticket or str(pos.id),
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                    "swap": pos.swap,
                    "commission": pos.commission,
                }
                for pos in positions
            ]
        except Exception as e:
            logger.error(f"Error getting positions from database: {e}")
            return []
        finally:
            session.close()

    async def _get_orders_from_db(
        self, user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get orders from database as fallback."""
        try:
            session = SessionLocal()
            query = session.query(Order).filter(
                Order.status.in_(["PENDING", "PARTIAL"])
            )

            if user_id:
                query = query.filter(Order.user_id == user_id)

            orders = query.all()

            return [
                {
                    "symbol": (
                        order.instrument.symbol if order.instrument else "Unknown"
                    ),
                    "type": order.order_type,
                    "volume": order.volume,
                    "price_open": order.price,
                    "time": order.created_at.isoformat() if order.created_at else None,
                    "ticket": order.mt_ticket or str(order.id),
                    "stop_loss": order.stop_loss,
                    "take_profit": order.take_profit,
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error getting orders from database: {e}")
            return []
        finally:
            session.close()

    async def _get_account_info_from_db(self) -> Dict[str, Any]:
        """Get account info from database as fallback."""
        try:
            # This would typically come from a user account model
            # For now, return basic structure
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "profit_loss": 0.0,
                "open_positions": 0,
                "pending_orders": 0,
                "currency": "USD",
                "leverage": 100,
                "server": "Database",
                "name": "Database Account",
                "total_profit": 0.0,
            }
        except Exception as e:
            logger.error(f"Error getting account info from database: {e}")
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "profit_loss": 0.0,
                "open_positions": 0,
                "pending_orders": 0,
                "currency": "USD",
                "leverage": 100,
                "server": "Fallback",
                "name": "Fallback Account",
                "total_profit": 0.0,
            }

    def is_mt5_available(self) -> bool:
        """Check if MT5 is available and connected."""
        return self.mt5_executor is not None and self.mt5_executor.connected

    async def close(self):
        """Close the service and cleanup resources."""
        if self.mt5_executor:
            try:
                await self.mt5_executor.disconnect()
            except Exception as e:
                logger.error(f"Error disconnecting MT5 executor: {e}")
