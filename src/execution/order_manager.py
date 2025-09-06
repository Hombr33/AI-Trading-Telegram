"""
Order Manager for handling order lifecycle and signal execution.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timezone
from uuid import uuid4

from ..core.logging import (
    get_logger,
    log_error_with_context,
    log_trade_event,
    log_system_event,
    log_operation_timing,
)
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import OrderValidationError, RiskManagementError
from ..core.config import TradingConfig
from ..common.interfaces import IOrderManager, OrderType, OrderSide

# MT5Executor will be injected via platform manager
from ..models.orders import Order
from ..models.instruments import Instrument
from ..models.signals import Signal

logger = get_logger(__name__)


class OrderManager(IOrderManager):
    """Manages order lifecycle and signal execution.

    Implements the IOrderManager interface to provide standardized order management
    functionality across different trading platforms.
    """

    def __init__(self, platform_manager, config: TradingConfig):
        self.platform_manager = platform_manager
        # Get MT5 executor from platform manager
        self.mt5_executor = (
            platform_manager.platforms.get("mt5")
            if hasattr(platform_manager, "platforms")
            else None
        )
        self.config = config
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

    async def place_order(
        self,
        platform: str,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        volume: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Place an order on the specified platform."""
        try:
            # Create order object
            order_id = f"order_{uuid4().hex[:8]}"

            # Map interface order type and side to internal representation
            internal_order_type = self._map_order_type(order_type, side)

            order = {
                "order_id": order_id,
                "symbol": symbol,
                "type": internal_order_type,
                "volume": volume,
                "price": price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "platform": platform,
                **kwargs,
            }

            # Create Order object from dictionary
            order_obj = Order(
                order_id=order_id,
                symbol=symbol,
                order_type=internal_order_type,
                volume=volume,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                status="PENDING",
            )

            # Use existing order placement logic
            result = await self._place_order(order_obj)

            if result["success"]:
                # Store the order in active orders
                self.active_orders[order_id] = order_obj
                self.order_history.append(order_obj)

            return result
        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_order(self, platform: str, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        try:
            if order_id not in self.active_orders:
                return False

            order = self.active_orders[order_id]

            # Use existing cancel logic
            result = await self.mt5_executor.close_position(
                int(order.get("mt_ticket", 0))
            )

            if result["success"]:
                del self.active_orders[order_id]
                return True
            return False
        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return False

    async def get_order(
        self, platform: str, order_id: str, symbol: str
    ) -> Dict[str, Any]:
        """Get information about a specific order."""
        try:
            if order_id not in self.active_orders:
                return {"success": False, "error": "Order not found"}

            return {"success": True, "order": self.active_orders[order_id]}
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return {"success": False, "error": str(e)}

    async def get_open_orders(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open orders, optionally filtered by platform and symbol."""
        try:
            orders = list(self.active_orders.values())

            # Apply filters if provided
            if platform:
                orders = [
                    order for order in orders if order.get("platform") == platform
                ]
            if symbol:
                orders = [order for order in orders if order.get("symbol") == symbol]

            return orders
        except Exception as e:
            logger.error(f"Error getting open orders: {e}")
            return []

    async def get_positions(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by platform and symbol."""
        try:
            # For positions, we need to query the executor
            if platform and platform != "mt5":
                # Currently only MT5 is supported
                return []

            positions = await self.mt5_executor.get_positions(symbol)

            # Convert to standard format
            result = []
            for pos in positions:
                result.append(
                    {
                        "symbol": pos.get("symbol"),
                        "volume": pos.get("volume"),
                        "open_price": pos.get("price_open"),
                        "current_price": pos.get("price_current"),
                        "profit": pos.get("profit"),
                        "platform": "mt5",
                        "ticket": pos.get("ticket"),
                        "type": "BUY" if pos.get("type") == 0 else "SELL",
                    }
                )

            return result
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def _map_order_type(self, order_type: OrderType, side: OrderSide) -> str:
        """Map interface order types to internal representation."""
        if order_type == OrderType.MARKET:
            return "BUY" if side == OrderSide.BUY else "SELL"
        elif order_type == OrderType.LIMIT:
            return "BUYLIMIT" if side == OrderSide.BUY else "SELLLIMIT"
        elif order_type == OrderType.STOP:
            return "BUYSTOP" if side == OrderSide.BUY else "SELLSTOP"
        else:
            return "BUY" if side == OrderSide.BUY else "SELL"

    async def execute_signal(
        self, signal_data: Union[Signal, Dict], instrument: Optional[Instrument] = None
    ) -> Dict:
        """Execute a trading signal by placing orders."""
        try:
            # Handle both Signal objects and dict inputs
            if isinstance(signal_data, dict):
                # Create a mock signal object from dict
                signal = type(
                    "MockSignal",
                    (),
                    {
                        "symbol": signal_data.get("symbol"),
                        "bias": signal_data.get("bias"),
                        "setups": signal_data.get("setups", []),
                        "id": signal_data.get("id", "mock_signal"),
                    },
                )()
            else:
                signal = signal_data

            logger.info(f"Executing signal for {signal.symbol}: {signal.bias}")

            # Validate signal
            if not self._validate_signal(signal):
                return {"success": False, "error": "Invalid signal parameters"}

            # Calculate position size
            position_size = await self._calculate_position_size(signal, instrument)
            if not position_size:
                return {"success": False, "error": "Failed to calculate position size"}

            # Create mock instrument if none provided
            if instrument is None:
                instrument = type(
                    "MockInstrument",
                    (),
                    {
                        "id": 1,
                        "symbol": signal.symbol,
                        "name": signal.symbol,
                        "type": "FOREX",
                        "digits": 5,
                        "point": 0.00001,
                        "spread": 2,
                        "trade_mode": 4,
                    },
                )()

            # Create and place orders
            orders = []
            for setup in signal.setups:
                order = await self._create_order_from_setup(
                    setup, signal, instrument, position_size
                )
                if order:
                    orders.append(order)

            if not orders:
                return {"success": False, "error": "Failed to create orders"}

            # Place orders in MT5
            execution_results = []
            for order in orders:
                result = await self._place_order(order)
                execution_results.append(result)

                if result["success"]:
                    self.active_orders[order.order_id] = order
                    self.order_history.append(order)
                    logger.info(f"Order placed successfully: {order.order_id}")
                else:
                    logger.error(
                        f"Order placement failed: {order.order_id}: {result['error']}"
                    )

            return {
                "success": True,
                "orders": execution_results,
                "signal_id": signal.id,
                "position_size": position_size,
            }

        except Exception as e:
            logger.error(f"Signal execution error: {e}")
            return {"success": False, "error": str(e)}

    async def modify_order(
        self, order_id: str, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict:
        """Modify an existing order."""
        try:
            if order_id not in self.active_orders:
                return {"success": False, "error": "Order not found"}

            order = self.active_orders[order_id]

            # Update order parameters
            if sl is not None:
                order.stop_loss = sl
            if tp is not None:
                order.take_profit = tp

            # Modify in MT5
            result = await self.mt5_executor.modify_order(
                int(order.mt_ticket), sl=order.stop_loss, tp=order.take_profit
            )

            if result["success"]:
                logger.info(f"Order {order_id} modified successfully")
                return {"success": True, "order": order}
            else:
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Order modification error: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_order(self, order_id: str) -> Dict:
        """Cancel a pending order."""
        try:
            if order_id not in self.active_orders:
                return {"success": False, "error": "Order not found"}

            order = self.active_orders[order_id]

            # Cancel in MT5
            result = await self.mt5_executor.close_position(int(order.mt_ticket))

            if result["success"]:
                del self.active_orders[order_id]
                logger.info(f"Order {order_id} cancelled successfully")
                return {"success": True}
            else:
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Order cancellation error: {e}")
            return {"success": False, "error": str(e)}

    async def close_position(
        self, position_id: str, volume: Optional[float] = None
    ) -> Dict:
        """Close a position or partial close."""
        try:
            # Find order by position ID
            order = None
            for active_order in self.active_orders.values():
                if active_order.mt_ticket == position_id:
                    order = active_order
                    break

            if not order:
                return {"success": False, "error": "Position not found"}

            # Close in MT5
            result = await self.mt5_executor.close_position(
                int(position_id), volume=volume
            )

            if result["success"]:
                if volume and volume < order.volume:
                    # Partial close
                    order.volume -= volume
                    logger.info(f"Partial close of position {position_id}")
                else:
                    # Full close
                    del self.active_orders[order.order_id]
                    logger.info(f"Position {position_id} closed successfully")

                return {"success": True}
            else:
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Position close error: {e}")
            return {"success": False, "error": str(e)}

    async def get_orders(self) -> List[Order]:
        """Get all pending orders."""
        return list(self.active_orders.values())

    def _validate_signal(self, signal: Signal) -> bool:
        """Validate trading signal parameters."""
        if not signal.symbol or not signal.bias:
            return False

        if not signal.setups or len(signal.setups) == 0:
            return False

        for setup in signal.setups:
            # Handle both object and dict setups
            if hasattr(setup, "entry_zone"):
                entry_zone = setup.entry_zone
                sl = setup.sl
                tp = setup.tp
                confidence = setup.confidence
            else:
                # Handle dict setup
                entry_zone = setup.get("entry_zone")
                sl = setup.get("sl")
                tp = setup.get("tp")
                confidence = setup.get("confidence", 0)

            if not entry_zone or len(entry_zone) != 2:
                return False

            if not sl or not tp:
                return False

            if confidence < 60:  # Minimum confidence threshold
                return False

        return True

    async def _calculate_position_size(
        self, signal: Signal, instrument: Instrument
    ) -> Optional[float]:
        """Calculate position size based on risk management rules."""
        try:
            # Get account balance
            account_info = self.mt5_executor.account_info
            if not account_info:
                logger.error("No account info available")
                return None

            balance = account_info.balance
            risk_per_trade = self.config.risk_management["max_risk_per_trade_pct"] / 100

            # Calculate risk amount
            risk_amount = balance * risk_per_trade

            # For now, use a simple calculation
            # In production, this should consider stop loss distance and pip value
            position_size = 0.01  # Minimum lot size

            # Ensure within limits
            min_size = self.config.position_sizing["min_position_size"]
            max_size = self.config.position_sizing["max_position_size"]

            position_size = max(min_size, min(position_size, max_size))

            return position_size

        except Exception as e:
            logger.error(f"Position size calculation error: {e}")
            return None

    async def _create_order_from_setup(
        self, setup: Dict, signal: Signal, instrument: Instrument, position_size: float
    ) -> Optional[Order]:
        """Create an order from a signal setup."""
        try:
            order_id = f"order_{uuid4().hex[:8]}"

            # Determine order type based on entry style (default to market if not specified)
            entry_style = setup.get("entry_style", "market")
            if entry_style == "limit":
                if setup["type"] == "BUY":
                    order_type = "BUYLIMIT"
                else:
                    order_type = "SELLLIMIT"
            elif entry_style == "stop":
                if setup["type"] == "BUY":
                    order_type = "BUYSTOP"
                else:
                    order_type = "SELLSTOP"
            else:  # market
                order_type = "BUY" if setup["type"] == "BUY" else "SELL"

            # Calculate entry price (middle of entry zone)
            entry_price = (setup["entry_zone"][0] + setup["entry_zone"][1]) / 2

            # Get magic number from config or use default
            magic_number = getattr(self.config, "execution", {}).get(
                "magic_number", 1001
            )

            # Create order object without SQLAlchemy relationship issues
            order = type(
                "MockOrder",
                (),
                {
                    "order_id": order_id,
                    "signal_id": getattr(signal, "id", "mock_signal"),
                    "instrument_id": getattr(instrument, "id", 1),
                    "action": "OPEN",
                    "order_type": order_type,
                    "volume": position_size,
                    "price": entry_price if order_type not in ["BUY", "SELL"] else None,
                    "stop_loss": setup["sl"],
                    "take_profit": (
                        setup["tp"][0] if setup["tp"] else None
                    ),  # Use first TP level
                    "magic_number": magic_number,
                    "comment": f"AI_SIGNAL_{getattr(signal, 'id', 'mock')}_{setup['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    "status": "PENDING",
                    "instrument": instrument,  # Set the instrument directly
                    "signal": signal,  # Set the signal directly
                },
            )()

            return order

        except Exception as e:
            logger.error(f"Order creation error: {e}")
            return None

    async def _place_order(self, order: Order) -> Dict:
        """Place an order in MT5."""
        try:
            result = await self.mt5_executor.place_order(order)

            if result["success"]:
                order.mt_ticket = str(result["order"])
                order.status = "FILLED"
                return result
            else:
                order.status = "REJECTED"
                return result

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            order.status = "REJECTED"
            return {"success": False, "error": str(e)}

    def get_active_orders(self) -> List[Order]:
        """Get all active orders."""
        return list(self.active_orders.values())

    def get_order_history(self) -> List[Order]:
        """Get order history."""
        return self.order_history.copy()

    def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self.active_orders.get(order_id)

    def get_orders_by_symbol(self, symbol: str) -> List[Order]:
        """Get orders by symbol."""
        return [
            order
            for order in self.active_orders.values()
            if order.instrument.symbol == symbol
        ]

    def get_order_stats(self) -> Dict:
        """Get order statistics."""
        total_orders = len(self.order_history)
        active_orders = len(self.active_orders)
        filled_orders = sum(
            1 for order in self.order_history if order.status == "FILLED"
        )
        rejected_orders = sum(
            1 for order in self.order_history if order.status == "REJECTED"
        )

        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "filled_orders": filled_orders,
            "rejected_orders": rejected_orders,
            "success_rate": (
                (filled_orders / total_orders * 100) if total_orders > 0 else 0
            ),
        }

    async def cancel_order(self, platform: str, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                # Use MT5 executor to cancel the order
                if platform.lower() == "mt5" and self.mt5_executor:
                    result = await self.mt5_executor.cancel_order(order_id, symbol)
                    if result:
                        order.status = "CANCELLED"
                        del self.active_orders[order_id]
                        log_trade_event(
                            "order_cancelled",
                            {
                                "order_id": order_id,
                                "symbol": symbol,
                                "platform": platform,
                            },
                        )
                        return True
                else:
                    # Mock cancellation for other platforms
                    order.status = "CANCELLED"
                    del self.active_orders[order_id]
                    return True
            return False
        except Exception as e:
            log_error_with_context(e, {"order_id": order_id, "platform": platform})
            return False

    async def get_order(
        self, platform: str, order_id: str, symbol: str
    ) -> Dict[str, Any]:
        """Get information about a specific order."""
        try:
            if order_id in self.active_orders:
                order = self.active_orders[order_id]
                return {
                    "order_id": order.order_id,
                    "symbol": order.symbol,
                    "type": order.order_type,
                    "volume": order.volume,
                    "price": order.price,
                    "stop_loss": order.stop_loss,
                    "take_profit": order.take_profit,
                    "status": order.status,
                    "platform": platform,
                }

            # Check order history
            for order in self.order_history:
                if order.order_id == order_id:
                    return {
                        "order_id": order.order_id,
                        "symbol": order.symbol,
                        "type": order.order_type,
                        "volume": order.volume,
                        "price": order.price,
                        "stop_loss": order.stop_loss,
                        "take_profit": order.take_profit,
                        "status": order.status,
                        "platform": platform,
                    }

            return {}
        except Exception as e:
            log_error_with_context(e, {"order_id": order_id, "platform": platform})
            return {}

    async def get_open_orders(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open orders, optionally filtered by platform and symbol."""
        try:
            open_orders = []
            for order_id, order in self.active_orders.items():
                if order.status in ["PENDING", "PARTIAL"]:
                    if symbol and order.symbol != symbol:
                        continue
                    open_orders.append(
                        {
                            "order_id": order.order_id,
                            "symbol": order.symbol,
                            "type": order.order_type,
                            "volume": order.volume,
                            "price": order.price,
                            "stop_loss": order.stop_loss,
                            "take_profit": order.take_profit,
                            "status": order.status,
                            "platform": platform or "mt5",
                        }
                    )
            return open_orders
        except Exception as e:
            log_error_with_context(e, {"platform": platform, "symbol": symbol})
            return []

    async def get_positions(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open positions, optionally filtered by platform and symbol."""
        try:
            if platform and platform.lower() == "mt5" and self.mt5_executor:
                # Get positions from MT5
                positions = await self.mt5_executor.get_positions(symbol)
                return positions if positions else []
            else:
                # Mock positions for other platforms or when MT5 not available
                mock_positions = []
                for order_id, order in self.active_orders.items():
                    if order.status == "FILLED":
                        if symbol and order.symbol != symbol:
                            continue
                        mock_positions.append(
                            {
                                "position_id": order_id,
                                "symbol": order.symbol,
                                "volume": order.volume,
                                "price": order.price,
                                "profit": 0.0,
                                "platform": platform or "mt5",
                            }
                        )
                return mock_positions
        except Exception as e:
            log_error_with_context(e, {"platform": platform, "symbol": symbol})
            return []
