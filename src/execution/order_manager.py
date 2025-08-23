"""
Order Manager for handling order lifecycle and signal execution.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timezone
from uuid import uuid4

from ..core.logging import (
    get_logger,
    log_error_with_context,
    log_trade_event,
    log_system_event,
    log_operation_timing
)
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import OrderValidationError, RiskManagementError
from ..core.config import TradingConfig
from ..execution.mt5_executor import MT5Executor
from ..models.orders import Order
from ..models.instruments import Instrument
from ..models.signals import Signal

logger = get_logger(__name__)


class OrderManager:
    """Manages order lifecycle and signal execution."""

    def __init__(self, mt5_executor: MT5Executor, config: TradingConfig):
        self.mt5_executor = mt5_executor
        self.config = config
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []

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
