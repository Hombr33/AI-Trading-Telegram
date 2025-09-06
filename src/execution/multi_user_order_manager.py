"""
Multi-User Order Manager for enhanced user-specific order routing and management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import json

from ..core.logging import get_logger
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import OrderManagerError, UserIsolationError, TradingBotException
from ..core.workflow import Component, ComponentStatus
from ..common.interfaces import IOrderManager, OrderType, OrderSide
from ..models.orders import Order
from ..models.trades import Trade
from ..bridge.ea_bridge import EABridge
from ..execution.multi_user_position_manager import MultiUserPositionManager
from ..services.user_manager import UserManager
from ..services.config_manager import ConfigManager

logger = get_logger(__name__)


class MultiUserOrderManager(IOrderManager):
    """Enhanced order manager with user-specific routing and isolation."""

    def __init__(
        self,
        ea_bridge: EABridge,
        position_manager: MultiUserPositionManager,
        user_manager: UserManager,
        config_manager: ConfigManager,
    ):
        self.ea_bridge = ea_bridge
        self.position_manager = position_manager
        self.user_manager = user_manager
        self.config_manager = config_manager

        # User-specific order tracking
        self._user_orders = defaultdict(dict)  # telegram_id -> {order_id: Order}
        self._user_order_history = defaultdict(list)  # telegram_id -> [Order]
        self._pending_orders = defaultdict(
            dict
        )  # telegram_id -> {order_id: pending_order}

        # Order routing and execution
        self._order_queues = defaultdict(asyncio.Queue)  # telegram_id -> Queue
        self._execution_workers = {}  # telegram_id -> task
        self._user_locks = defaultdict(asyncio.Lock)  # telegram_id -> lock

        # Statistics and monitoring
        self._running = False
        self._stats = {
            "total_orders": 0,
            "pending_orders": 0,
            "executed_orders": 0,
            "failed_orders": 0,
            "last_update": None,
        }

    @with_error_handling("multi_user_order_manager_start", notify_telegram=True)
    async def start(self):
        """Start the multi-user order manager."""
        if self._running:
            return

        self._running = True
        logger.info("Multi-user order manager started")

        # Start order processing workers for active users
        await self._initialize_execution_workers()

    async def stop(self):
        """Stop the multi-user order manager."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping multi-user order manager...")

        # Cancel all execution workers
        for telegram_id, task in self._execution_workers.items():
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._execution_workers.values(), return_exceptions=True)
        self._execution_workers.clear()

        logger.info("Multi-user order manager stopped")

    async def _initialize_execution_workers(self):
        """Initialize order execution workers for active users."""
        try:
            # Get users with active EA connections
            active_users = await self._get_users_with_ea_connections()

            for telegram_id in active_users:
                if telegram_id not in self._execution_workers:
                    task = asyncio.create_task(self._process_user_orders(telegram_id))
                    self._execution_workers[telegram_id] = task
                    logger.info(
                        f"Started order execution worker for user {telegram_id}"
                    )

        except Exception as e:
            logger.error(f"Failed to initialize execution workers: {e}")

    async def _get_users_with_ea_connections(self) -> List[int]:
        """Get users that have active EA connections."""
        try:
            # Query database for users with active platform connections
            # This is a simplified version - in production you'd query the actual database
            return []  # Placeholder
        except Exception as e:
            logger.error(f"Failed to get users with EA connections: {e}")
            return []

    async def _process_user_orders(self, telegram_id: int):
        """Process orders for specific user."""
        while self._running:
            try:
                # Get order from user's queue
                order_data = await self._order_queues[telegram_id].get()

                if not self._running:
                    break

                # Process the order
                await self._execute_user_order(telegram_id, order_data)

                self._order_queues[telegram_id].task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing order for user {telegram_id}: {e}")
                await asyncio.sleep(1)

    async def _execute_user_order(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute order for specific user."""
        try:
            order_id = order_data.get("order_id")
            if not order_id:
                return {"success": False, "error": "Missing order_id"}

            # Validate user authorization
            if not await self._validate_user_order_access(telegram_id, order_data):
                return {"success": False, "error": "User not authorized"}

            # Pre-execution validation
            validation_result = await self._validate_order_pre_execution(
                telegram_id, order_data
            )
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["reason"]}

            # Execute order via EA bridge
            execution_result = await self.ea_bridge.send_order_with_risk_check(
                telegram_id, order_data
            )

            # Update statistics
            async with self._user_locks[telegram_id]:
                if execution_result and execution_result.get("success"):
                    self._stats["executed_orders"] += 1
                else:
                    self._stats["failed_orders"] += 1

            # Post-execution processing
            if execution_result and execution_result.get("success"):
                await self._handle_successful_execution(
                    telegram_id, order_data, execution_result
                )
            else:
                await self._handle_failed_execution(
                    telegram_id, order_data, execution_result
                )

            return execution_result or {"success": False, "error": "Execution failed"}

        except Exception as e:
            logger.error(f"Failed to execute order for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _validate_user_order_access(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> bool:
        """Validate user has access to execute this order."""
        try:
            # Check if user is authorized
            if not await self.user_manager.is_user_authorized(telegram_id):
                return False

            # Check if user has active EA connection
            connection = await self.ea_bridge.get_user_ea_connection(telegram_id)
            if not connection:
                return False

            # Additional validation based on order type and user permissions
            order_type = order_data.get("type", "").upper()
            if order_type in ["BUY", "SELL"]:
                # Check trading permissions
                user_config = await self.config_manager.get_user_config(
                    telegram_id, "trading"
                )
                if not user_config or not user_config.get(
                    "auto_trading_enabled", False
                ):
                    return False

            return True

        except Exception as e:
            logger.error(f"Order access validation failed for user {telegram_id}: {e}")
            return False

    async def _validate_order_pre_execution(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate order before execution."""
        try:
            # Basic validation
            required_fields = ["symbol", "type", "entry_zone"]
            for field in required_fields:
                if field not in order_data:
                    return {
                        "valid": False,
                        "reason": f"Missing required field: {field}",
                    }

            # Validate order type
            order_type = order_data.get("type", "").upper()
            if order_type not in ["BUY", "SELL"]:
                return {"valid": False, "reason": f"Invalid order type: {order_type}"}

            # Check symbol permissions
            symbol = order_data.get("symbol", "")
            if not await self._validate_symbol_access(telegram_id, symbol):
                return {"valid": False, "reason": f"Symbol not authorized: {symbol}"}

            # Check position limits
            current_positions = await self.position_manager.get_user_positions(
                telegram_id
            )
            max_positions = await self._get_user_max_positions(telegram_id)
            if len(current_positions) >= max_positions:
                return {
                    "valid": False,
                    "reason": f"Maximum positions ({max_positions}) reached",
                }

            return {"valid": True, "reason": "Order validated"}

        except Exception as e:
            logger.error(f"Order validation failed for user {telegram_id}: {e}")
            return {"valid": False, "reason": f"Validation error: {str(e)}"}

    async def _validate_symbol_access(self, telegram_id: int, symbol: str) -> bool:
        """Validate user has access to trade specific symbol."""
        try:
            # Get user's symbol subscriptions
            subscriptions = await self.user_manager.get_user_subscriptions(telegram_id)
            symbol_names = [sub["symbol"] for sub in subscriptions]

            # Check if symbol is in user's subscriptions or if user has wildcard access
            return symbol in symbol_names or "*" in symbol_names

        except Exception as e:
            logger.error(f"Symbol access validation failed for user {telegram_id}: {e}")
            return False

    async def _get_user_max_positions(self, telegram_id: int) -> int:
        """Get maximum positions allowed for user."""
        try:
            user_config = await self.config_manager.get_user_config(telegram_id, "risk")
            return user_config.get("max_open_positions", 5) if user_config else 5
        except Exception:
            return 5  # Default

    async def _handle_successful_execution(
        self,
        telegram_id: int,
        order_data: Dict[str, Any],
        execution_result: Dict[str, Any],
    ):
        """Handle successful order execution."""
        try:
            # Create order record
            order = Order(
                order_id=order_data.get("order_id"),
                user_id=telegram_id,
                symbol=order_data.get("symbol"),
                order_type=order_data.get("type"),
                volume=execution_result.get("volume", 0),
                price=execution_result.get("price", 0),
                status="executed",
                created_at=datetime.utcnow(),
                executed_at=datetime.utcnow(),
            )

            # Store in user-specific tracking
            async with self._user_locks[telegram_id]:
                self._user_orders[telegram_id][order.order_id] = order
                self._user_order_history[telegram_id].append(order)

            # Update position tracking
            await self.position_manager.force_refresh_user_positions(telegram_id)

            logger.info(
                f"Order {order.order_id} executed successfully for user {telegram_id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to handle successful execution for user {telegram_id}: {e}"
            )

    async def _handle_failed_execution(
        self,
        telegram_id: int,
        order_data: Dict[str, Any],
        execution_result: Optional[Dict[str, Any]],
    ):
        """Handle failed order execution."""
        try:
            # Create failed order record
            order = Order(
                order_id=order_data.get("order_id"),
                user_id=telegram_id,
                symbol=order_data.get("symbol"),
                order_type=order_data.get("type"),
                volume=0,
                price=0,
                status="failed",
                created_at=datetime.utcnow(),
                error_message=(
                    execution_result.get("error")
                    if execution_result
                    else "Unknown error"
                ),
            )

            # Store in user-specific tracking
            async with self._user_locks[telegram_id]:
                self._user_orders[telegram_id][order.order_id] = order
                self._user_order_history[telegram_id].append(order)

            logger.warning(
                f"Order {order.order_id} failed for user {telegram_id}: {order.error_message}"
            )

        except Exception as e:
            logger.error(
                f"Failed to handle failed execution for user {telegram_id}: {e}"
            )

    # Public Interface Methods

    async def submit_order(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit order for specific user."""
        try:
            # Generate order ID if not provided
            if "order_id" not in order_data:
                order_data["order_id"] = (
                    f"order_{telegram_id}_{int(datetime.utcnow().timestamp())}"
                )

            # Initialize user tracking if needed
            if telegram_id not in self._execution_workers:
                await self._initialize_user_worker(telegram_id)

            # Add to user's order queue
            await self._order_queues[telegram_id].put(order_data)

            # Update statistics
            async with self._user_locks[telegram_id]:
                self._pending_orders[telegram_id][order_data["order_id"]] = order_data
                self._stats["total_orders"] += 1
                self._stats["pending_orders"] += 1

            return {
                "success": True,
                "order_id": order_data["order_id"],
                "message": "Order submitted for execution",
            }

        except Exception as e:
            logger.error(f"Failed to submit order for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def _initialize_user_worker(self, telegram_id: int):
        """Initialize order execution worker for user."""
        try:
            if telegram_id not in self._execution_workers:
                task = asyncio.create_task(self._process_user_orders(telegram_id))
                self._execution_workers[telegram_id] = task

                # Initialize data structures
                if telegram_id not in self._user_orders:
                    self._user_orders[telegram_id] = {}
                    self._user_order_history[telegram_id] = []
                    self._pending_orders[telegram_id] = {}

                logger.info(
                    f"Initialized order execution worker for user {telegram_id}"
                )

        except Exception as e:
            logger.error(f"Failed to initialize worker for user {telegram_id}: {e}")

    async def cancel_order(self, telegram_id: int, order_id: str) -> Dict[str, Any]:
        """Cancel pending order for user."""
        try:
            async with self._user_locks[telegram_id]:
                if order_id in self._pending_orders[telegram_id]:
                    # Remove from pending orders
                    del self._pending_orders[telegram_id][order_id]
                    self._stats["pending_orders"] -= 1

                    return {"success": True, "message": f"Order {order_id} cancelled"}
                else:
                    return {
                        "success": False,
                        "error": f"Order {order_id} not found or already executed",
                    }

        except Exception as e:
            logger.error(
                f"Failed to cancel order {order_id} for user {telegram_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def get_user_orders(
        self, telegram_id: int, status: Optional[str] = None
    ) -> List[Order]:
        """Get orders for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                orders = list(self._user_orders[telegram_id].values())

                if status:
                    orders = [order for order in orders if order.status == status]

                return orders

        except Exception as e:
            logger.error(f"Failed to get orders for user {telegram_id}: {e}")
            return []

    async def get_user_pending_orders(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get pending orders for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                return list(self._pending_orders[telegram_id].values())

        except Exception as e:
            logger.error(f"Failed to get pending orders for user {telegram_id}: {e}")
            return []

    async def get_user_order_history(
        self, telegram_id: int, limit: int = 100
    ) -> List[Order]:
        """Get order history for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                history = self._user_order_history[telegram_id]
                return history[-limit:] if limit > 0 else history

        except Exception as e:
            logger.error(f"Failed to get order history for user {telegram_id}: {e}")
            return []

    async def get_order_status(
        self, telegram_id: int, order_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get status of specific order."""
        try:
            async with self._user_locks[telegram_id]:
                # Check pending orders
                if order_id in self._pending_orders[telegram_id]:
                    return {
                        "order_id": order_id,
                        "status": "pending",
                        "submitted_at": datetime.utcnow().isoformat(),
                    }

                # Check executed orders
                if order_id in self._user_orders[telegram_id]:
                    order = self._user_orders[telegram_id][order_id]
                    return {
                        "order_id": order.order_id,
                        "status": order.status,
                        "symbol": order.symbol,
                        "order_type": order.order_type,
                        "volume": order.volume,
                        "price": order.price,
                        "executed_at": (
                            order.executed_at.isoformat() if order.executed_at else None
                        ),
                        "error_message": getattr(order, "error_message", None),
                    }

                return None

        except Exception as e:
            logger.error(f"Failed to get order status for user {telegram_id}: {e}")
            return None

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics."""
        try:
            return {
                "is_running": self._running,
                "total_orders": self._stats["total_orders"],
                "pending_orders": self._stats["pending_orders"],
                "executed_orders": self._stats["executed_orders"],
                "failed_orders": self._stats["failed_orders"],
                "active_workers": len(self._execution_workers),
                "last_update": self._stats["last_update"],
            }
        except Exception as e:
            logger.error(f"Failed to get manager stats: {e}")
            return {"error": str(e)}

    async def get_all_users_orders(self) -> Dict[str, List[Order]]:
        """Get orders for all users (admin function)."""
        try:
            result = {}
            for telegram_id in self._user_orders.keys():
                result[str(telegram_id)] = await self.get_user_orders(telegram_id)
            return result
        except Exception as e:
            logger.error(f"Failed to get all users orders: {e}")
            return {}

    async def emergency_cancel_all_user_orders(
        self, telegram_id: int
    ) -> Dict[str, Any]:
        """Emergency cancel all pending orders for user."""
        try:
            async with self._user_locks[telegram_id]:
                pending_count = len(self._pending_orders[telegram_id])
                self._pending_orders[telegram_id].clear()
                self._stats["pending_orders"] -= pending_count

                return {
                    "success": True,
                    "cancelled": pending_count,
                    "message": f"Emergency cancelled {pending_count} pending orders",
                }

        except Exception as e:
            logger.error(f"Emergency cancel failed for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    # Abstract Interface Implementation Methods

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
        """Place an order (interface implementation)."""
        try:
            # This is a simplified implementation - in practice you'd need telegram_id from kwargs or context
            telegram_id = kwargs.get("telegram_id")
            if not telegram_id:
                return {
                    "success": False,
                    "error": "telegram_id required for multi-user order placement",
                }

            # Convert to our internal format
            order_data = {
                "symbol": symbol,
                "type": "BUY" if side == OrderSide.BUY else "SELL",
                "entry_zone": [price] if price else [kwargs.get("entry_price", 0)],
                "sl": stop_loss,
                "tp": [take_profit] if take_profit else [],
                "volume": volume,
            }

            return await self.submit_order(telegram_id, order_data)

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_order(self, platform: str, order_id: str, symbol: str) -> bool:
        """Cancel an existing order (interface implementation)."""
        try:
            # This is a simplified implementation - in practice you'd need telegram_id from context
            # For now, search across all users
            for telegram_id in self._user_orders.keys():
                result = await self.cancel_order(telegram_id, order_id)
                if result["success"]:
                    return True
            return False

        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    async def get_order(
        self, platform: str, order_id: str, symbol: str
    ) -> Dict[str, Any]:
        """Get information about a specific order (interface implementation)."""
        try:
            # Search across all users
            for telegram_id in self._user_orders.keys():
                order = await self.get_order_status(telegram_id, order_id)
                if order:
                    return order
            return {"error": f"Order {order_id} not found"}

        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return {"error": str(e)}

    async def get_open_orders(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open orders (interface implementation)."""
        try:
            all_orders = []
            for telegram_id in self._user_orders.keys():
                user_orders = await self.get_user_pending_orders(telegram_id)
                all_orders.extend(user_orders)
            return all_orders

        except Exception as e:
            logger.error(f"Failed to get open orders: {e}")
            return []

    async def get_positions(
        self, platform: str = None, symbol: str = None
    ) -> List[Dict[str, Any]]:
        """Get all open positions (interface implementation)."""
        try:
            # Delegate to position manager
            positions = await self.position_manager.get_positions()

            # Convert Position objects to dictionaries
            result = []
            for pos in positions:
                pos_dict = {
                    "ticket": pos.mt_ticket,
                    "symbol": (
                        getattr(pos, "instrument", {}).symbol
                        if hasattr(pos, "instrument")
                        else "Unknown"
                    ),
                    "type": pos.direction,
                    "volume": pos.volume,
                    "open_price": pos.open_price,
                    "current_price": pos.current_price,
                    "stop_loss": pos.stop_loss,
                    "take_profit": pos.take_profit,
                    "profit": pos.unrealized_pnl,
                    "open_time": pos.open_time,
                }
                result.append(pos_dict)

            return result

        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
