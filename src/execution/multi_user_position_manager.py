"""
Multi-User Position Manager for enhanced user-specific position tracking.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import threading

from ..core.logging import get_logger
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import (
    PositionManagerError,
    UserIsolationError,
    TradingBotException,
)
from ..core.workflow import Component, ComponentStatus
from ..core.config import TradingConfig
from ..common.interfaces import IPositionManager
from ..models.positions import Position
from ..models.trades import Trade
from ..bridge.ea_bridge import EABridge
from ..services.user_manager import UserManager
from ..services.config_manager import ConfigManager

logger = get_logger(__name__)


class MultiUserPositionManager(IPositionManager):
    """Enhanced position manager with user-specific tracking and isolation."""

    def __init__(
        self, ea_bridge: EABridge, user_manager: UserManager, config: TradingConfig
    ):
        self.ea_bridge = ea_bridge
        self.user_manager = user_manager
        self.config = config

        # User-specific position tracking
        self._user_positions = defaultdict(dict)  # telegram_id -> {ticket: Position}
        self._user_position_history = defaultdict(list)  # telegram_id -> [Position]
        self._user_risk_metrics = defaultdict(dict)  # telegram_id -> risk_metrics

        # Monitoring and control
        self._running = False
        self._monitoring_tasks = {}  # telegram_id -> task
        self._user_locks = defaultdict(asyncio.Lock)  # telegram_id -> lock
        self._global_lock = asyncio.Lock()

        # Statistics and health
        self._stats = {
            "total_users": 0,
            "active_users": 0,
            "total_positions": 0,
            "last_update": None,
        }

    @with_error_handling("multi_user_position_manager_start", notify_telegram=True)
    async def start(self):
        """Start the multi-user position manager."""
        if self._running:
            return

        self._running = True
        logger.info("Multi-user position manager started")

        # Start background monitoring
        asyncio.create_task(self._global_monitoring_loop())

    async def stop(self):
        """Stop the multi-user position manager."""
        if not self._running:
            return

        self._running = False
        logger.info("Stopping multi-user position manager...")

        # Cancel all monitoring tasks
        for telegram_id, task in self._monitoring_tasks.items():
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._monitoring_tasks.values(), return_exceptions=True)
        self._monitoring_tasks.clear()

        logger.info("Multi-user position manager stopped")

    async def _global_monitoring_loop(self):
        """Global monitoring loop for all users."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute

                # Get all active users
                active_users = await self._get_active_users()

                # Update stats
                async with self._global_lock:
                    self._stats.update(
                        {
                            "total_users": len(active_users),
                            "active_users": len(
                                [u for u in active_users if u in self._user_positions]
                            ),
                            "total_positions": sum(
                                len(positions)
                                for positions in self._user_positions.values()
                            ),
                            "last_update": datetime.utcnow(),
                        }
                    )

                # Clean up inactive users
                await self._cleanup_inactive_users(active_users)

            except Exception as e:
                logger.error(f"Error in global monitoring loop: {e}")
                await asyncio.sleep(120)  # Wait longer on error

    async def _get_active_users(self) -> List[int]:
        """Get list of active users with EA connections."""
        try:
            # This would typically query the database for users with active EA connections
            # For now, return users that have positions or recent activity
            active_users = []
            for telegram_id in list(self._user_positions.keys()):
                if self._user_positions[telegram_id]:  # Has positions
                    active_users.append(telegram_id)
                elif telegram_id in self._monitoring_tasks:  # Has monitoring task
                    active_users.append(telegram_id)

            return active_users

        except Exception as e:
            logger.error(f"Failed to get active users: {e}")
            return []

    async def _cleanup_inactive_users(self, active_users: List[int]):
        """Clean up data for inactive users."""
        try:
            current_users = set(self._user_positions.keys()) | set(
                self._monitoring_tasks.keys()
            )
            inactive_users = current_users - set(active_users)

            for telegram_id in inactive_users:
                await self._cleanup_user_data(telegram_id)

        except Exception as e:
            logger.error(f"Failed to cleanup inactive users: {e}")

    async def _cleanup_user_data(self, telegram_id: int):
        """Clean up data for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                # Cancel monitoring task
                if telegram_id in self._monitoring_tasks:
                    task = self._monitoring_tasks[telegram_id]
                    if not task.done():
                        task.cancel()
                    del self._monitoring_tasks[telegram_id]

                # Clear user data
                self._user_positions.pop(telegram_id, None)
                self._user_position_history.pop(telegram_id, None)
                self._user_risk_metrics.pop(telegram_id, None)

                logger.info(f"Cleaned up data for inactive user {telegram_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup user data for {telegram_id}: {e}")

    async def initialize_user_tracking(self, telegram_id: int) -> bool:
        """Initialize position tracking for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                if telegram_id in self._monitoring_tasks:
                    return True  # Already tracking

                # Start user-specific monitoring
                task = asyncio.create_task(self._monitor_user_positions(telegram_id))
                self._monitoring_tasks[telegram_id] = task

                # Initialize user data structures
                if telegram_id not in self._user_positions:
                    self._user_positions[telegram_id] = {}
                    self._user_position_history[telegram_id] = []
                    self._user_risk_metrics[telegram_id] = (
                        self._get_default_risk_metrics()
                    )

                logger.info(f"Initialized position tracking for user {telegram_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to initialize tracking for user {telegram_id}: {e}")
            return False

    async def _monitor_user_positions(self, telegram_id: int):
        """Monitor positions for specific user."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds

                # Check if user is still active
                if telegram_id not in self._monitoring_tasks:
                    break

                # Update positions from EA bridge
                await self._update_user_positions(telegram_id)

                # Check risk limits
                await self._check_user_risk_limits(telegram_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring positions for user {telegram_id}: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _update_user_positions(self, telegram_id: int):
        """Update positions for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                # Get positions from EA bridge
                positions_data = await self.ea_bridge.get_user_positions(telegram_id)

                if positions_data is None:
                    return  # No positions or error

                current_positions = {}
                for pos_data in positions_data:
                    ticket = pos_data.get("ticket")
                    if ticket:
                        current_positions[ticket] = pos_data

                # Update existing positions and add new ones
                user_positions = self._user_positions[telegram_id]
                for ticket, pos_data in current_positions.items():
                    if ticket in user_positions:
                        # Update existing position
                        await self._update_position(telegram_id, ticket, pos_data)
                    else:
                        # Add new position
                        await self._add_position(telegram_id, pos_data)

                # Check for closed positions
                closed_tickets = set(user_positions.keys()) - set(
                    current_positions.keys()
                )
                for ticket in closed_tickets:
                    await self._remove_position(telegram_id, ticket)

                # Update risk metrics
                await self._update_user_risk_metrics(telegram_id)

        except Exception as e:
            logger.error(f"Failed to update positions for user {telegram_id}: {e}")

    async def _add_position(self, telegram_id: int, position_data: Dict[str, Any]):
        """Add a new position for user."""
        try:
            ticket = position_data.get("ticket")
            if not ticket:
                return

            # Create position object
            position = Position(
                position_id=f"pos_{telegram_id}_{ticket}",
                trade_id=0,  # Will be updated when trade is created
                instrument_id=0,  # Will be updated when instrument is found
                user_id=telegram_id,
                direction=position_data.get("type", "BUY"),
                volume=position_data.get("volume", 0),
                open_price=position_data.get("price_open", 0),
                current_price=position_data.get(
                    "price_current", position_data.get("price_open", 0)
                ),
                stop_loss=position_data.get("sl"),
                take_profit=position_data.get("tp"),
                open_time=datetime.fromtimestamp(
                    position_data.get("time", datetime.utcnow().timestamp()),
                    tz=datetime.utcnow().tzinfo,
                ).isoformat(),
                unrealized_pnl=position_data.get("profit", 0),
                swap=position_data.get("swap", 0),
                commission=0.0,
                is_active=True,
                mt_ticket=str(ticket),
            )

            self._user_positions[telegram_id][ticket] = position
            logger.info(f"Added position {ticket} for user {telegram_id}")

        except Exception as e:
            logger.error(f"Failed to add position for user {telegram_id}: {e}")

    async def _update_position(
        self, telegram_id: int, ticket: int, position_data: Dict[str, Any]
    ):
        """Update existing position for user."""
        try:
            if ticket not in self._user_positions[telegram_id]:
                return

            position = self._user_positions[telegram_id][ticket]
            position.current_price = position_data.get(
                "price_current", position.current_price
            )
            position.unrealized_pnl = position_data.get(
                "profit", position.unrealized_pnl
            )
            position.stop_loss = position_data.get("sl", position.stop_loss)
            position.take_profit = position_data.get("tp", position.take_profit)

        except Exception as e:
            logger.error(
                f"Failed to update position {ticket} for user {telegram_id}: {e}"
            )

    async def _remove_position(self, telegram_id: int, ticket: int):
        """Remove closed position for user."""
        try:
            if ticket in self._user_positions[telegram_id]:
                position = self._user_positions[telegram_id][ticket]
                position.is_active = False

                # Move to history
                self._user_position_history[telegram_id].append(position)
                del self._user_positions[telegram_id][ticket]

                logger.info(
                    f"Position {ticket} closed and moved to history for user {telegram_id}"
                )

        except Exception as e:
            logger.error(
                f"Failed to remove position {ticket} for user {telegram_id}: {e}"
            )

    async def _update_user_risk_metrics(self, telegram_id: int):
        """Update risk metrics for specific user."""
        try:
            positions = self._user_positions[telegram_id]
            if not positions:
                self._user_risk_metrics[telegram_id] = self._get_default_risk_metrics()
                return

            total_exposure = 0.0
            total_pnl = 0.0
            position_count = len(positions)
            long_positions = 0
            short_positions = 0

            for position in positions.values():
                exposure = position.volume * (
                    position.current_price or position.open_price
                )
                total_exposure += exposure
                total_pnl += position.unrealized_pnl or 0

                if position.direction == "BUY":
                    long_positions += 1
                elif position.direction == "SELL":
                    short_positions += 1

            # Calculate drawdown
            drawdown_pct = 0.0
            if total_exposure > 0 and total_pnl < 0:
                drawdown_pct = abs(total_pnl) / total_exposure * 100

            self._user_risk_metrics[telegram_id] = {
                "total_exposure": total_exposure,
                "total_pnl": total_pnl,
                "position_count": position_count,
                "long_positions": long_positions,
                "short_positions": short_positions,
                "drawdown_pct": drawdown_pct,
                "last_update": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Failed to update risk metrics for user {telegram_id}: {e}")

    def _get_default_risk_metrics(self) -> Dict[str, Any]:
        """Get default risk metrics structure."""
        return {
            "total_exposure": 0.0,
            "total_pnl": 0.0,
            "position_count": 0,
            "long_positions": 0,
            "short_positions": 0,
            "drawdown_pct": 0.0,
            "last_update": datetime.utcnow(),
        }

    async def _check_user_risk_limits(self, telegram_id: int):
        """Check risk limits for specific user."""
        try:
            risk_metrics = self._user_risk_metrics.get(
                telegram_id, self._get_default_risk_metrics()
            )

            # Get user risk configuration
            user_config = await self.config_manager.get_user_config(telegram_id, "risk")
            if not user_config:
                return  # No risk limits configured

            alerts = []

            # Check position count limit
            max_positions = user_config.get("max_open_positions", 5)
            if risk_metrics["position_count"] >= max_positions:
                alerts.append(f"Maximum positions ({max_positions}) reached")

            # Check drawdown limit
            max_drawdown = user_config.get("max_daily_drawdown_pct", 5.0)
            if risk_metrics["drawdown_pct"] >= max_drawdown:
                alerts.append(f"Daily drawdown limit ({max_drawdown}%) reached")

            # Check exposure limit
            max_exposure = user_config.get("max_exposure", 10000)
            if risk_metrics["total_exposure"] >= max_exposure:
                alerts.append(f"Maximum exposure ({max_exposure}) reached")

            if alerts:
                logger.warning(
                    f"Risk alerts for user {telegram_id}: {', '.join(alerts)}"
                )
                # Here you could send notifications or trigger risk management actions

        except Exception as e:
            logger.error(f"Failed to check risk limits for user {telegram_id}: {e}")

    # Public Interface Methods

    async def get_user_positions(self, telegram_id: int) -> List[Position]:
        """Get all positions for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                return list(self._user_positions[telegram_id].values())
        except Exception as e:
            logger.error(f"Failed to get positions for user {telegram_id}: {e}")
            return []

    async def get_user_position(
        self, telegram_id: int, ticket: int
    ) -> Optional[Position]:
        """Get specific position for user."""
        try:
            async with self._user_locks[telegram_id]:
                return self._user_positions[telegram_id].get(ticket)
        except Exception as e:
            logger.error(f"Failed to get position {ticket} for user {telegram_id}: {e}")
            return None

    async def get_user_risk_metrics(self, telegram_id: int) -> Dict[str, Any]:
        """Get risk metrics for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                return self._user_risk_metrics.get(
                    telegram_id, self._get_default_risk_metrics()
                )
        except Exception as e:
            logger.error(f"Failed to get risk metrics for user {telegram_id}: {e}")
            return self._get_default_risk_metrics()

    async def get_user_position_history(self, telegram_id: int) -> List[Position]:
        """Get position history for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                return self._user_position_history[telegram_id].copy()
        except Exception as e:
            logger.error(f"Failed to get position history for user {telegram_id}: {e}")
            return []

    async def modify_user_position(
        self,
        telegram_id: int,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Modify position for specific user."""
        try:
            # First modify in EA
            success = await self.ea_bridge.modify_position_in_ea(
                telegram_id, ticket, sl, tp
            )

            if success:
                # Update local position
                async with self._user_locks[telegram_id]:
                    if ticket in self._user_positions[telegram_id]:
                        position = self._user_positions[telegram_id][ticket]
                        if sl is not None:
                            position.stop_loss = sl
                        if tp is not None:
                            position.take_profit = tp

                return {"success": True, "message": f"Position {ticket} modified"}
            else:
                return {"success": False, "error": "Failed to modify position in EA"}

        except Exception as e:
            logger.error(
                f"Failed to modify position {ticket} for user {telegram_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def close_user_position(
        self, telegram_id: int, ticket: int, volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Close position for specific user."""
        try:
            # First close in EA
            success = await self.ea_bridge.close_position_in_ea(
                telegram_id, ticket, volume
            )

            if success:
                # Update local tracking
                async with self._user_locks[telegram_id]:
                    if ticket in self._user_positions[telegram_id]:
                        position = self._user_positions[telegram_id][ticket]
                        if volume and volume < position.volume:
                            # Partial close
                            position.volume -= volume
                        else:
                            # Full close
                            await self._remove_position(telegram_id, ticket)

                return {"success": True, "message": f"Position {ticket} closed"}
            else:
                return {"success": False, "error": "Failed to close position in EA"}

        except Exception as e:
            logger.error(
                f"Failed to close position {ticket} for user {telegram_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def get_all_users_positions(self) -> Dict[str, List[Position]]:
        """Get positions for all users (admin function)."""
        try:
            async with self._global_lock:
                result = {}
                for telegram_id, positions in self._user_positions.items():
                    result[str(telegram_id)] = list(positions.values())
                return result
        except Exception as e:
            logger.error(f"Failed to get all users positions: {e}")
            return {}

    async def get_all_users_risk_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get risk metrics for all users (admin function)."""
        try:
            async with self._global_lock:
                result = {}
                for telegram_id, metrics in self._user_risk_metrics.items():
                    result[str(telegram_id)] = metrics.copy()
                return result
        except Exception as e:
            logger.error(f"Failed to get all users risk metrics: {e}")
            return {}

    def get_manager_stats(self) -> Dict[str, Any]:
        """Get comprehensive manager statistics."""
        try:
            # Note: This method is synchronous, so we don't use async locks
            # In a production environment, consider making this async or using thread locks
            return {
                "is_running": self._running,
                "total_users": self._stats["total_users"],
                "active_users": self._stats["active_users"],
                "total_positions": self._stats["total_positions"],
                "active_monitoring_tasks": len(self._monitoring_tasks),
                "last_update": self._stats["last_update"],
            }
        except Exception as e:
            logger.error(f"Failed to get manager stats: {e}")
            return {"error": str(e)}

    async def force_refresh_user_positions(self, telegram_id: int) -> bool:
        """Force refresh positions for specific user."""
        try:
            await self._update_user_positions(telegram_id)
            return True
        except Exception as e:
            logger.error(
                f"Failed to force refresh positions for user {telegram_id}: {e}"
            )
            return False

    # Abstract Interface Implementation Methods

    async def get_positions(self) -> List[Position]:
        """Get all active positions across all users (interface implementation)."""
        try:
            all_positions = []
            for telegram_id in list(self._user_positions.keys()):
                user_positions = await self.get_user_positions(telegram_id)
                all_positions.extend(user_positions)
            return all_positions
        except Exception as e:
            logger.error(f"Failed to get all positions: {e}")
            return []

    async def modify_position(
        self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict[str, Any]:
        """Modify position by ticket (interface implementation)."""
        try:
            # Find which user owns this position
            for telegram_id, positions in self._user_positions.items():
                if ticket in positions:
                    return await self.modify_user_position(telegram_id, ticket, sl, tp)

            return {"success": False, "error": f"Position {ticket} not found"}
        except Exception as e:
            logger.error(f"Failed to modify position {ticket}: {e}")
            return {"success": False, "error": str(e)}

    def get_position(self, ticket: int) -> Optional[Position]:
        """Get position by ticket (interface implementation)."""
        try:
            # Search across all users
            for positions in self._user_positions.values():
                if ticket in positions:
                    return positions[ticket]
            return None
        except Exception as e:
            logger.error(f"Failed to get position {ticket}: {e}")
            return None

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get positions by symbol across all users (interface implementation)."""
        try:
            matching_positions = []
            for positions in self._user_positions.values():
                for position in positions.values():
                    # Check if position has the symbol (this depends on your Position model)
                    if (
                        hasattr(position, "instrument")
                        and position.instrument
                        and position.instrument.symbol == symbol
                    ):
                        matching_positions.append(position)
                    elif hasattr(position, "symbol") and position.symbol == symbol:
                        matching_positions.append(position)
            return matching_positions
        except Exception as e:
            logger.error(f"Failed to get positions by symbol {symbol}: {e}")
            return []

    async def emergency_close_all_user_positions(
        self, telegram_id: int
    ) -> Dict[str, Any]:
        """Emergency close all positions for specific user."""
        try:
            async with self._user_locks[telegram_id]:
                positions = self._user_positions.get(telegram_id, {})
                if not positions:
                    return {"success": True, "message": "No positions to close"}

                closed_count = 0
                failed_count = 0

                for ticket in list(positions.keys()):
                    result = await self.close_user_position(telegram_id, ticket)
                    if result["success"]:
                        closed_count += 1
                    else:
                        failed_count += 1

                return {
                    "success": failed_count == 0,
                    "closed": closed_count,
                    "failed": failed_count,
                    "message": f"Emergency close completed: {closed_count} closed, {failed_count} failed",
                }

        except Exception as e:
            logger.error(f"Emergency close failed for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}
