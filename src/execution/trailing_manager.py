"""
Trailing Stop and Take Profit Manager for automated position management.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..core.logging import get_logger

# MT5Executor will be injected via platform manager

logger = get_logger(__name__)


@dataclass
class TrailingConfig:
    """Configuration for trailing stop management."""

    enabled: bool = True
    start_points: int = 250  # Start trailing after 250 points profit
    stop_points: int = 200  # Initial trailing stop distance
    step_points: int = 50  # Trailing step size
    activation_condition: str = "after_tp1"  # When to activate trailing


@dataclass
class PositionState:
    """Current state of a position for trailing management."""

    ticket: int
    symbol: str
    direction: str  # "BUY" or "SELL"
    volume: float
    open_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    profit: float
    partial_tp_hit: bool = False
    trailing_activated: bool = False
    breakeven_moved: bool = False


class TrailingManager:
    """Manages trailing stops and take profit for open positions."""

    def __init__(self, platform_manager, config: TrailingConfig):
        # Get MT5 executor from platform manager
        self.mt5_executor = (
            platform_manager.platforms.get("mt5")
            if hasattr(platform_manager, "platforms")
            else None
        )
        self.config = config
        self.active_positions: Dict[int, PositionState] = {}
        self.running = False

    async def start(self):
        """Start the trailing manager."""
        self.running = True
        logger.info("Trailing manager started")

        while self.running:
            try:
                await self._update_positions()
                await self._process_trailing()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Trailing manager error: {e}")
                await asyncio.sleep(5)  # Wait longer on error

    async def stop(self):
        """Stop the trailing manager."""
        self.running = False
        logger.info("Trailing manager stopped")

    async def add_position(self, position: Dict):
        """Add a new position for trailing management."""
        pos_state = PositionState(
            ticket=position["ticket"],
            symbol=position["symbol"],
            direction=position["type"],
            volume=position["volume"],
            open_price=position["price_open"],
            current_price=position["price_open"],  # Will be updated
            stop_loss=position["sl"],
            take_profit=position["tp"],
            profit=position["profit"],
        )

        self.active_positions[position["ticket"]] = pos_state
        logger.info(f"Added position {position['ticket']} for trailing management")

    async def remove_position(self, ticket: int):
        """Remove a position from trailing management."""
        if ticket in self.active_positions:
            del self.active_positions[ticket]
            logger.info(f"Removed position {ticket} from trailing management")

    async def _update_positions(self):
        """Update current position states from MT5."""
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

            for position in positions:
                ticket = position["ticket"]

                if ticket in self.active_positions:
                    # Update existing position
                    pos_state = self.active_positions[ticket]
                    pos_state.current_price = position[
                        "price_open"
                    ]  # Use current market price
                    pos_state.profit = position["profit"]
                    pos_state.stop_loss = position["sl"]
                    pos_state.take_profit = position["tp"]
                else:
                    # Add new position
                    await self.add_position(position)

        except Exception as e:
            logger.error(f"Error updating positions: {e}")

    async def _process_trailing(self):
        """Process trailing logic for all active positions."""
        for ticket, pos_state in list(self.active_positions.items()):
            try:
                await self._process_position_trailing(pos_state)
            except Exception as e:
                logger.error(f"Error processing trailing for position {ticket}: {e}")

    async def _process_position_trailing(self, pos_state: PositionState):
        """Process trailing logic for a single position."""
        # Calculate current profit in points
        if pos_state.direction == "BUY":
            profit_points = (
                pos_state.current_price - pos_state.open_price
            ) * 10000  # Convert to points
        else:
            profit_points = (pos_state.open_price - pos_state.current_price) * 10000

        # Check if we should move to breakeven (at 1R profit)
        if not pos_state.breakeven_moved and profit_points >= 100:  # 1R = 100 points
            await self._move_to_breakeven(pos_state)

        # Check if we should take partial profit (at 1.5R)
        if not pos_state.partial_tp_hit and profit_points >= 150:  # 1.5R = 150 points
            await self._take_partial_profit(pos_state)

        # Check if we should activate trailing (after TP1 or at 2R)
        if not pos_state.trailing_activated:
            if (
                pos_state.partial_tp_hit and profit_points >= 200
            ) or profit_points >= 200:
                await self._activate_trailing(pos_state)

        # Update trailing stop if active
        if pos_state.trailing_activated:
            await self._update_trailing_stop(pos_state)

    async def _move_to_breakeven(self, pos_state: PositionState):
        """Move stop loss to breakeven."""
        try:
            result = await self.mt5_executor.modify_order(
                pos_state.ticket, sl=pos_state.open_price
            )

            if result["success"]:
                pos_state.breakeven_moved = True
                pos_state.stop_loss = pos_state.open_price
                logger.info(f"Position {pos_state.ticket} moved to breakeven")
            else:
                logger.error(
                    f"Failed to move position {pos_state.ticket} to breakeven: {result['error']}"
                )

        except Exception as e:
            logger.error(f"Error moving position {pos_state.ticket} to breakeven: {e}")

    async def _take_partial_profit(self, pos_state: PositionState):
        """Take partial profit (50% of position)."""
        try:
            partial_volume = pos_state.volume * 0.5

            result = await self.mt5_executor.close_position(
                pos_state.ticket, volume=partial_volume
            )

            if result["success"]:
                pos_state.partial_tp_hit = True
                pos_state.volume = partial_volume
                logger.info(f"Partial profit taken for position {pos_state.ticket}")
            else:
                logger.error(
                    f"Failed to take partial profit for position {pos_state.ticket}: {result['error']}"
                )

        except Exception as e:
            logger.error(
                f"Error taking partial profit for position {pos_state.ticket}: {e}"
            )

    async def _activate_trailing(self, pos_state: PositionState):
        """Activate trailing stop for a position."""
        try:
            # Calculate initial trailing stop
            if pos_state.direction == "BUY":
                trailing_stop = pos_state.current_price - (
                    self.config.stop_points / 10000
                )
            else:
                trailing_stop = pos_state.current_price + (
                    self.config.stop_points / 10000
                )

            result = await self.mt5_executor.modify_order(
                pos_state.ticket, sl=trailing_stop
            )

            if result["success"]:
                pos_state.trailing_activated = True
                pos_state.stop_loss = trailing_stop
                logger.info(
                    f"Trailing activated for position {pos_state.ticket} at {trailing_stop}"
                )
            else:
                logger.error(
                    f"Failed to activate trailing for position {pos_state.ticket}: {result['error']}"
                )

        except Exception as e:
            logger.error(
                f"Error activating trailing for position {pos_state.ticket}: {e}"
            )

    async def _update_trailing_stop(self, pos_state: PositionState):
        """Update trailing stop based on price movement."""
        try:
            if pos_state.direction == "BUY":
                # For long positions, trail up
                new_stop = pos_state.current_price - (self.config.stop_points / 10000)

                if new_stop > pos_state.stop_loss + (self.config.step_points / 10000):
                    # Only move stop if it's significantly higher
                    result = await self.mt5_executor.modify_order(
                        pos_state.ticket, sl=new_stop
                    )

                    if result["success"]:
                        pos_state.stop_loss = new_stop
                        logger.info(
                            f"Trailing stop updated for position {pos_state.ticket} to {new_stop}"
                        )

            else:
                # For short positions, trail down
                new_stop = pos_state.current_price + (self.config.stop_points / 10000)

                if new_stop < pos_state.stop_loss - (self.config.step_points / 10000):
                    # Only move stop if it's significantly lower
                    result = await self.mt5_executor.modify_order(
                        pos_state.ticket, sl=new_stop
                    )

                    if result["success"]:
                        pos_state.stop_loss = new_stop
                        logger.info(
                            f"Trailing stop updated for position {pos_state.ticket} to {new_stop}"
                        )

        except Exception as e:
            logger.error(
                f"Error updating trailing stop for position {pos_state.ticket}: {e}"
            )

    def get_position_status(self, ticket: int) -> Optional[PositionState]:
        """Get current status of a position."""
        return self.active_positions.get(ticket)

    def get_all_positions(self) -> List[PositionState]:
        """Get all active positions being managed."""
        return list(self.active_positions.values())

    def get_trailing_stats(self) -> Dict:
        """Get statistics about trailing management."""
        total_positions = len(self.active_positions)
        trailing_active = sum(
            1 for pos in self.active_positions.values() if pos.trailing_activated
        )
        breakeven_moved = sum(
            1 for pos in self.active_positions.values() if pos.breakeven_moved
        )
        partial_tp_hit = sum(
            1 for pos in self.active_positions.values() if pos.partial_tp_hit
        )

        return {
            "total_positions": total_positions,
            "trailing_active": trailing_active,
            "breakeven_moved": breakeven_moved,
            "partial_tp_hit": partial_tp_hit,
            "running": self.running,
        }

    def get_config(self) -> Dict[str, Any]:
        """Get trailing manager configuration."""
        return {
            "enabled": self.config.trailing_stop["enabled"],
            "start_points": self.config.trailing_stop["start_points"],
            "stop_points": self.config.trailing_stop["stop_points"],
            "step_points": self.config.trailing_stop["step_points"],
        }

    @property
    def is_running(self) -> bool:
        """Check if the trailing manager is running."""
        return self.running
