#!/usr/bin/env python3
"""
Order Execution Script for AI Trading Bot.
Executes trading signals and manages positions.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bridge.order_bridge import OrderBridge
from common.interfaces import IOrderManager, IPositionManager
from core.config import BridgeConfig, TradingConfig
from core.logging import get_logger
from execution.mt5_executor import MT5Executor
from execution.order_manager import OrderManager
from execution.position_manager import PositionManager
from execution.trailing_manager import TrailingConfig, TrailingManager

logger = get_logger(__name__)


class OrderExecutionScript:
    """Main order execution script."""

    def __init__(self):
        self.config = TradingConfig()
        self.bridge_config = BridgeConfig()
        self.mt5_executor = None
        self.order_manager: IOrderManager = None
        self.position_manager: IPositionManager = None
        self.trailing_manager = None
        self.order_bridge = None

    async def initialize(self):
        """Initialize all components."""
        try:
            logger.info("Initializing order execution system...")

            # Initialize MT5 executor
            self.mt5_executor = MT5Executor(self.config)
            await self.mt5_executor.connect()

            # Initialize managers
            self.order_manager = OrderManager(self.mt5_executor, self.config)
            self.position_manager = PositionManager(self.mt5_executor, self.config)

            # Initialize trailing manager
            trailing_config = TrailingConfig(
                enabled=True, start_points=250, stop_points=200, step_points=50
            )
            self.trailing_manager = TrailingManager(self.mt5_executor, trailing_config)

            # Initialize order bridge
            self.order_bridge = OrderBridge(self.bridge_config)
            await self.order_bridge.connect()

            logger.info("Order execution system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize order execution system: {e}")
            return False

    async def start_managers(self):
        """Start all background managers."""
        try:
            # Start position manager
            asyncio.create_task(self.position_manager.start())
            logger.info("Position manager started")

            # Start trailing manager
            asyncio.create_task(self.trailing_manager.start())
            logger.info("Trailing manager started")

        except Exception as e:
            logger.error(f"Failed to start managers: {e}")

    async def execute_signal(self, signal_data: dict):
        """Execute a trading signal."""
        try:
            logger.info(f"Executing signal: {signal_data}")

            # Create signal object (simplified)
            signal = type("Signal", (), signal_data)()

            # Create instrument object (simplified)
            instrument = type("Instrument", (), {"symbol": signal_data["symbol"]})()

            # Execute signal
            result = await self.order_manager.execute_signal(signal, instrument)

            if result["success"]:
                logger.info(f"Signal executed successfully: {result}")

                # Send confirmation via bridge
                await self.order_bridge.send_signal(signal)

                return result
            else:
                logger.error(f"Signal execution failed: {result}")
                return result

        except Exception as e:
            logger.error(f"Error executing signal: {e}")
            return {"success": False, "error": str(e)}

    async def get_positions(self):
        """Get current positions."""
        try:
            positions = await self.mt5_executor.get_positions()
            logger.info(f"Current positions: {len(positions)}")
            return positions
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    async def get_orders(self):
        """Get current orders."""
        try:
            orders = await self.mt5_executor.get_orders()
            logger.info(f"Current orders: {len(orders)}")
            return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    async def close_position(self, ticket: int, volume: float = None):
        """Close a position."""
        try:
            result = await self.position_manager.close_position(ticket, volume)
            if result["success"]:
                logger.info(f"Position {ticket} closed successfully")
            else:
                logger.error(f"Failed to close position {ticket}: {result['error']}")
            return result
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return {"success": False, "error": str(e)}

    async def modify_position(self, ticket: int, sl: float = None, tp: float = None):
        """Modify position stop loss or take profit."""
        try:
            result = await self.position_manager.modify_position(ticket, sl, tp)
            if result["success"]:
                logger.info(f"Position {ticket} modified successfully")
            else:
                logger.error(f"Failed to modify position {ticket}: {result['error']}")
            return result
        except Exception as e:
            logger.error(f"Error modifying position: {e}")
            return {"success": False, "error": str(e)}

    async def get_trailing_stats(self):
        """Get trailing manager statistics."""
        try:
            stats = self.trailing_manager.get_trailing_stats()
            logger.info(f"Trailing stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error getting trailing stats: {e}")
            return {}

    async def run_interactive(self):
        """Run interactive mode for manual order execution."""
        print("\n=== AI Trading Bot - Order Execution ===")
        print("Commands:")
        print("  signal <symbol> <bias> <entry> <sl> <tp> - Execute signal")
        print("  positions - Show current positions")
        print("  orders - Show current orders")
        print("  close <ticket> [volume] - Close position")
        print("  modify <ticket> <sl> <tp> - Modify position")
        print("  trailing - Show trailing stats")
        print("  quit - Exit")
        print()

        while True:
            try:
                command = input("> ").strip().split()
                if not command:
                    continue

                cmd = command[0].lower()

                if cmd == "quit":
                    break
                elif cmd == "signal" and len(command) >= 6:
                    # signal XAUUSD BEARISH 3343.0 3348.0 3336.0
                    symbol = command[1]
                    bias = command[2]
                    entry = float(command[3])
                    sl = float(command[4])
                    tp = float(command[5])

                    signal_data = {
                        "symbol": symbol,
                        "bias": bias,
                        "setups": [
                            {
                                "type": "SELL" if bias == "BEARISH" else "BUY",
                                "entry_zone": [entry - 1, entry + 1],
                                "entry_style": "limit",
                                "sl": sl,
                                "tp": [tp],
                                "confidence": 80,
                                "notes": "Manual execution",
                            }
                        ],
                    }

                    result = await self.execute_signal(signal_data)
                    print(f"Signal execution: {result}")

                elif cmd == "positions":
                    positions = await self.get_positions()
                    for pos in positions:
                        print(
                            f"Ticket: {pos['ticket']}, Symbol: {pos['symbol']}, "
                            f"Type: {pos['type']}, Volume: {pos['volume']}, "
                            f"P&L: {pos['profit']}"
                        )

                elif cmd == "orders":
                    orders = await self.get_orders()
                    for order in orders:
                        print(
                            f"Ticket: {order['ticket']}, Symbol: {order['symbol']}, "
                            f"Type: {order['type']}, Volume: {order['volume']}"
                        )

                elif cmd == "close" and len(command) >= 2:
                    ticket = int(command[1])
                    volume = float(command[2]) if len(command) > 2 else None
                    result = await self.close_position(ticket, volume)
                    print(f"Close result: {result}")

                elif cmd == "modify" and len(command) >= 4:
                    ticket = int(command[1])
                    sl = float(command[2]) if command[2] != "null" else None
                    tp = float(command[3]) if command[3] != "null" else None
                    result = await self.modify_position(ticket, sl, tp)
                    print(f"Modify result: {result}")

                elif cmd == "trailing":
                    stats = await self.get_trailing_stats()
                    print(f"Trailing stats: {stats}")

                else:
                    print("Invalid command. Type 'help' for available commands.")

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Command error: {e}")
                print(f"Error: {e}")

    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.trailing_manager:
                await self.trailing_manager.stop()

            if self.position_manager:
                await self.position_manager.stop()

            if self.order_bridge:
                await self.order_bridge.disconnect()

            if self.mt5_executor:
                await self.mt5_executor.disconnect()

            logger.info("Cleanup completed")

        except Exception as e:
            logger.error(f"Cleanup error: {e}")


async def main():
    """Main function."""
    script = OrderExecutionScript()

    try:
        # Initialize
        if not await script.initialize():
            logger.error("Failed to initialize. Exiting.")
            return

        # Start managers
        await script.start_managers()

        # Run interactive mode
        await script.run_interactive()

    except Exception as e:
        logger.error(f"Main error: {e}")
    finally:
        await script.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
