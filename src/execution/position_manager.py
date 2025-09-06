"""
Position Manager for monitoring and managing open positions.
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone

from ..core.logging import (
    get_logger,
    log_error_with_context,
    log_system_event,
    log_trade_event,
    log_operation_timing,
)
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import MT5ExecutionError, RiskManagementError
from ..core.workflow import Component, ComponentStatus
from ..core.config import TradingConfig
from ..common.interfaces import IPositionManager

# MT5Executor will be injected via platform manager
from ..models.positions import Position
from ..models.trades import Trade

logger = get_logger(__name__)


class PositionManager(IPositionManager):
    """Manages position monitoring and management.

    Implements the IPositionManager interface to provide standardized position management
    functionality across different trading platforms.
    """

    def __init__(self, platform_manager, config: TradingConfig):
        # Get MT5 executor from platform manager
        self.mt5_executor = (
            platform_manager.platforms.get("mt5")
            if hasattr(platform_manager, "platforms")
            else None
        )
        self.config = config
        self.active_positions: Dict[int, Position] = {}
        self.position_history: List[Position] = []
        self.running = False
        self.sync_failures = 0
        self.last_sync_time = 0

    @with_error_handling("position_manager_start", notify_telegram=True)
    async def start(self):
        """Start the position manager with enhanced monitoring."""
        self.running = True
        log_system_event("position_manager", "starting", "Position manager starting up")

        # Start monitoring loop as a background task
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

        log_system_event(
            "position_manager", "started", "Position manager started successfully"
        )

    async def _monitoring_loop(self):
        """Enhanced monitoring loop with error recovery."""
        while self.running:
            try:
                start_time = time.time()

                # Update positions with timeout
                async with ErrorContext(
                    "position_update", {"sync_failures": self.sync_failures}
                ) as ctx:
                    await asyncio.wait_for(self._update_positions(), timeout=30.0)
                    self.sync_failures = 0  # Reset on success
                    self.last_sync_time = time.time()

                # Check risk limits
                async with ErrorContext("risk_check") as ctx:
                    await self._check_risk_limits()

                # Log performance
                loop_time = time.time() - start_time
                log_operation_timing("position_manager_loop", start_time, time.time())

                await asyncio.sleep(5)  # Check every 5 seconds

            except asyncio.TimeoutError:
                self.sync_failures += 1
                logger.warning(
                    f"Position sync timeout (failures: {self.sync_failures})"
                )

                if self.sync_failures >= self.max_sync_failures:
                    log_system_event(
                        "position_manager",
                        "sync_failure_limit",
                        "Maximum sync failures reached, restarting MT5 connection",
                    )
                    # Could trigger MT5 reconnection here
                    self.sync_failures = 0

                await asyncio.sleep(10)  # Wait longer on timeout

            except Exception as e:
                log_error_with_context(
                    e,
                    {
                        "component": "position_manager",
                        "operation": "monitoring_loop",
                        "sync_failures": self.sync_failures,
                    },
                )
                await asyncio.sleep(10)  # Wait longer on error

    async def stop(self):
        """Stop the position manager."""
        self.running = False
        logger.info("Position manager stopped")

    async def _update_positions(self):
        """Update position information from MT5."""
        try:
            # Check if MT5 executor is available and connected
            if not self.mt5_executor or not hasattr(self.mt5_executor, "get_positions"):
                return  # Silently skip if executor not available

            # Additional safety check for connection
            if (
                hasattr(self.mt5_executor, "connected")
                and not self.mt5_executor.connected
            ):
                return  # Skip if not connected

            positions = await self.mt5_executor.get_positions()

            # Update existing positions
            for position_data in positions:
                ticket = position_data["ticket"]

                if ticket in self.active_positions:
                    # Update existing position
                    pos = self.active_positions[ticket]
                    pos.current_price = position_data[
                        "price_open"
                    ]  # Current market price
                    pos.unrealized_pnl = position_data["profit"]
                    pos.stop_loss = position_data["sl"]
                    pos.take_profit = position_data["tp"]
                else:
                    # Add new position
                    await self._add_position(position_data)

            # Check for closed positions
            closed_tickets = []
            for ticket in self.active_positions:
                if not any(pos["ticket"] == ticket for pos in positions):
                    closed_tickets.append(ticket)

            for ticket in closed_tickets:
                await self._remove_position(ticket)

        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    async def _add_position(self, position_data: Dict):
        """Add a new position."""
        try:
            # Create position object
            position = Position(
                position_id=f"pos_{position_data['ticket']}",
                trade_id=0,  # Will be updated when trade is created
                instrument_id=0,  # Will be updated when instrument is found
                user_id=None,
                direction=position_data["type"],
                volume=position_data["volume"],
                open_price=position_data["price_open"],
                current_price=position_data["price_open"],
                stop_loss=position_data["sl"],
                take_profit=position_data["tp"],
                open_time=datetime.fromtimestamp(
                    position_data["time"], tz=timezone.utc
                ).isoformat(),
                unrealized_pnl=position_data["profit"],
                swap=position_data["swap"],
                commission=0.0,  # Will be updated from MT5
                is_active=True,
                mt_ticket=str(position_data["ticket"]),
            )

            self.active_positions[position_data["ticket"]] = position
            logger.info(
                f"Added new position: {position_data['ticket']} {position_data['symbol']}"
            )

        except Exception as e:
            logger.error(f"Error adding position: {e}")

    async def _remove_position(self, ticket: int):
        """Remove a closed position."""
        try:
            if ticket in self.active_positions:
                position = self.active_positions[ticket]
                position.is_active = False

                # Move to history
                self.position_history.append(position)
                del self.active_positions[ticket]

                logger.info(f"Position {ticket} closed and moved to history")

        except Exception as e:
            logger.error(f"Error removing position: {e}")

    async def _check_risk_limits(self):
        """Check if any positions violate risk limits."""
        try:
            total_exposure = 0.0
            total_pnl = 0.0

            for position in self.active_positions.values():
                # Calculate exposure (simplified)
                exposure = position.volume * position.current_price
                total_exposure += exposure
                total_pnl += position.unrealized_pnl or 0

            # Check daily drawdown limit
            if total_pnl < 0:
                drawdown_pct = abs(total_pnl) / (total_exposure + abs(total_pnl)) * 100

                if (
                    drawdown_pct
                    >= self.config.risk_management["max_daily_drawdown_pct"]
                ):
                    logger.warning(f"Daily drawdown limit reached: {drawdown_pct:.2f}%")
                    await self._handle_risk_limit_breach("daily_drawdown", drawdown_pct)

            # Check position count limit
            if (
                len(self.active_positions)
                >= self.config.risk_management["max_open_positions"]
            ):
                logger.warning(
                    f"Maximum open positions reached: {len(self.active_positions)}"
                )
                await self._handle_risk_limit_breach(
                    "max_positions", len(self.active_positions)
                )

        except Exception as e:
            logger.error(f"Error checking risk limits: {e}")

    async def _handle_risk_limit_breach(self, breach_type: str, value: float):
        """Handle risk limit breaches."""
        try:
            logger.warning(f"Risk limit breach detected: {breach_type} = {value}")

            if breach_type == "daily_drawdown":
                # Close all positions if drawdown is too high
                if value >= self.config.risk_management["max_daily_drawdown_pct"]:
                    logger.critical(
                        "Emergency stop: Closing all positions due to excessive drawdown"
                    )
                    await self._emergency_close_all()

            elif breach_type == "max_positions":
                # Close oldest positions to reduce count
                await self._reduce_position_count()

        except Exception as e:
            logger.error(f"Error handling risk limit breach: {e}")

    async def _emergency_close_all(self):
        """Emergency close all positions."""
        try:
            logger.critical("Emergency closing all positions")

            for ticket in list(self.active_positions.keys()):
                result = await self.mt5_executor.close_position(ticket)

                if result["success"]:
                    logger.info(f"Emergency closed position {ticket}")
                else:
                    logger.error(
                        f"Failed to emergency close position {ticket}: {result['error']}"
                    )

        except Exception as e:
            logger.error(f"Error during emergency close: {e}")

    async def _reduce_position_count(self):
        """Reduce position count by closing oldest positions."""
        try:
            target_count = (
                self.config.risk_management["max_open_positions"] - 2
            )  # Leave room for new positions

            if len(self.active_positions) <= target_count:
                return

            # Sort positions by open time (oldest first)
            sorted_positions = sorted(
                self.active_positions.values(), key=lambda x: x.open_time
            )

            positions_to_close = len(self.active_positions) - target_count

            for i in range(positions_to_close):
                position = sorted_positions[i]
                ticket = int(position.mt_ticket)

                result = await self.mt5_executor.close_position(ticket)

                if result["success"]:
                    logger.info(f"Closed position {ticket} to reduce count")
                else:
                    logger.error(
                        f"Failed to close position {ticket}: {result['error']}"
                    )

        except Exception as e:
            logger.error(f"Error reducing position count: {e}")

    async def modify_position(
        self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None
    ) -> Dict:
        """Modify position stop loss or take profit."""
        try:
            if ticket not in self.active_positions:
                return {"success": False, "error": "Position not found"}

            result = await self.mt5_executor.modify_order(ticket, sl=sl, tp=tp)

            if result["success"]:
                position = self.active_positions[ticket]
                if sl is not None:
                    position.stop_loss = sl
                if tp is not None:
                    position.take_profit = tp

                logger.info(f"Position {ticket} modified successfully")
                return {"success": True, "position": position}
            else:
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Position modification error: {e}")
            return {"success": False, "error": str(e)}

    async def close_position(self, ticket: int, volume: Optional[float] = None) -> Dict:
        """Close a position or partial close."""
        try:
            if ticket not in self.active_positions:
                return {"success": False, "error": "Position not found"}

            result = await self.mt5_executor.close_position(ticket, volume=volume)

            if result["success"]:
                if volume and volume < self.active_positions[ticket].volume:
                    # Partial close
                    self.active_positions[ticket].volume -= volume
                    logger.info(f"Partial close of position {ticket}")
                else:
                    # Full close
                    await self._remove_position(ticket)

                return {"success": True}
            else:
                return {"success": False, "error": result["error"]}

        except Exception as e:
            logger.error(f"Position close error: {e}")
            return {"success": False, "error": str(e)}

    def get_position(self, ticket: int) -> Optional[Position]:
        """Get position by ticket."""
        return self.active_positions.get(ticket)

    def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get positions by symbol."""
        return [
            pos
            for pos in self.active_positions.values()
            if hasattr(pos, "instrument") and pos.instrument.symbol == symbol
        ]

    async def get_positions(self) -> List[Position]:
        """Get all active positions."""
        return list(self.active_positions.values())

    def get_position_history(self) -> List[Position]:
        """Get position history."""
        return self.position_history.copy()

    def get_position_stats(self) -> Dict:
        """Get position statistics."""
        total_positions = len(self.active_positions)
        total_volume = sum(pos.volume for pos in self.active_positions.values())
        total_pnl = sum(
            pos.unrealized_pnl or 0 for pos in self.active_positions.values()
        )

        # Count by direction
        long_positions = sum(
            1 for pos in self.active_positions.values() if pos.direction == "BUY"
        )
        short_positions = sum(
            1 for pos in self.active_positions.values() if pos.direction == "SELL"
        )

        return {
            "total_positions": total_positions,
            "total_volume": total_volume,
            "total_pnl": total_pnl,
            "long_positions": long_positions,
            "short_positions": short_positions,
            "average_pnl": total_pnl / total_positions if total_positions > 0 else 0,
        }

    def get_risk_metrics(self) -> Dict:
        """Get current risk metrics."""
        total_exposure = 0.0
        total_pnl = 0.0

        for position in self.active_positions.values():
            # Simplified exposure calculation
            exposure = position.volume * (position.current_price or position.open_price)
            total_exposure += exposure
            total_pnl += position.unrealized_pnl or 0

        if total_exposure > 0:
            drawdown_pct = abs(min(total_pnl, 0)) / total_exposure * 100
        else:
            drawdown_pct = 0

        return {
            "total_exposure": total_exposure,
            "total_pnl": total_pnl,
            "drawdown_pct": drawdown_pct,
            "position_count": len(self.active_positions),
            "risk_per_trade_pct": self.config.risk_management["risk_per_trade_pct"],
            "max_daily_drawdown_pct": self.config.risk_management[
                "max_daily_drawdown_pct"
            ],
        }

    @property
    def is_running(self) -> bool:
        """Check if the position manager is running."""
        return self.running
