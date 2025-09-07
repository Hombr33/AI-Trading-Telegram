"""
Automatic trading execution service.
Executes trades automatically when auto trading is enabled.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.common.interfaces import IAutoTradingService, IOrderManager, IPlatformManager
from src.core.config import config
from src.core.logging import get_logger, log_system_event, log_trade_event

logger = get_logger(__name__)


class AutoTradingService(IAutoTradingService):
    """Service for automatic trade execution.

    Implements the IAutoTradingService interface to provide automatic trade execution
    based on signals. Uses dependency injection for platform and order management.
    """

    def __init__(self, config, platform_manager: IPlatformManager, telegram_bot=None):
        """
        Initialize the auto trading service.

        Args:
            config: Application configuration
            platform_manager: Trading platform manager implementing IPlatformManager
            telegram_bot: Optional telegram bot for notifications
        """
        self.config = config
        self.platform_manager = platform_manager
        self.telegram_bot = telegram_bot
        self.running = False
        self.task: Optional[asyncio.Task] = None
        self.order_manager: Optional[IOrderManager] = None
        self.trades_today = 0
        self.daily_reset_time = 0
        self.pending_signals: List[Dict[str, Any]] = []
        self.active_trades: Dict[str, Dict[str, Any]] = {}

    def set_order_manager(self, order_manager: IOrderManager) -> None:
        """Set the order manager instance.

        Args:
            order_manager: Order manager implementing IOrderManager interface
        """
        self.order_manager = order_manager
        logger.info("Order manager set for auto trading service")

    async def start(self) -> None:
        """Start the auto trading service."""
        if self.running:
            logger.warning("Auto trading service is already running")
            return

        if not config.auto_trading.enabled:
            logger.info("Auto trading is disabled in config")
            return

        if not self.order_manager:
            logger.error("Cannot start auto trading service: Order manager not set")
            return

        self.running = True
        self.task = asyncio.create_task(self._trading_loop())
        log_system_event(
            "auto_trading_service", "started", "Auto trading service started"
        )
        logger.info("Auto trading service started")

    async def stop(self) -> None:
        """Stop the auto trading service."""
        if not self.running:
            logger.warning("Auto trading service is not running")
            return

        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        log_system_event(
            "auto_trading_service", "stopped", "Auto trading service stopped"
        )
        logger.info("Auto trading service stopped")

    def set_platform_manager(self, platform_manager: IPlatformManager):
        """Set the platform manager."""
        self.platform_manager = platform_manager

    def set_order_manager(self, order_manager: IOrderManager):
        """Set the order manager."""
        self.order_manager = order_manager

    async def _trading_loop(self):
        """Main auto trading loop."""
        while self.running:
            try:
                # Check if auto trading is enabled
                if not config.auto_trading.enabled:
                    await asyncio.sleep(60)  # Check every minute
                    continue

                # Reset daily counter at midnight
                current_time = time.time()
                if current_time - self.daily_reset_time > 86400:  # 24 hours
                    self.trades_today = 0
                    self.daily_reset_time = current_time

                # Check daily trade limit
                if self.trades_today >= config.auto_trading.max_trades_per_day:
                    logger.info(
                        f"Daily trade limit reached: {self.trades_today}/{config.auto_trading.max_trades_per_day}"
                    )
                    await asyncio.sleep(300)  # Wait 5 minutes before checking again
                    continue

                # Process pending signals if signal generation is disabled but trading is enabled
                await self._process_pending_signals()

                # If signal generation is enabled, get signals from signal service
                if config.auto_trading.auto_signal_generation:
                    await self._process_automatic_signals()

                # Manage existing trades
                await self._manage_active_trades()

                # Sleep before next iteration
                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in auto trading loop: {e}")
                await asyncio.sleep(60)

    async def _process_pending_signals(self):
        """Process any pending manual signals."""
        if not self.pending_signals:
            return

        for signal in self.pending_signals.copy():
            try:
                success = await self._execute_signal(signal)
                if success:
                    self.pending_signals.remove(signal)
            except Exception as e:
                logger.error(f"Error processing pending signal: {e}")

    async def _process_automatic_signals(self):
        """Process signals from the signal generation service."""
        try:
            # Check if signal generation service is available
            if hasattr(self, "signal_service") and self.signal_service:
                # Get latest signals from the service
                signals = await self.signal_service.get_latest_signals()

                for signal in signals:
                    if signal.get("auto_execute", False):
                        await self._execute_signal(signal)
            else:
                # Fallback: check for signals in database with retry logic
                await self._process_database_signals_with_retry()

        except Exception as e:
            logger.error(f"Error processing automatic signals: {e}")

    async def _process_database_signals_with_retry(self, max_retries: int = 3):
        """Process database signals with retry logic for SQLite I/O errors."""
        import asyncio

        from sqlalchemy import desc
        from sqlalchemy.exc import DisconnectionError, OperationalError

        try:
            from src.database.session import get_db_session_with_retry
            from src.models import Signal

            # Use the retry-enabled session manager
            with get_db_session_with_retry(max_retries=max_retries) as db:
                # Get latest active signals
                latest_signals = (
                    db.query(Signal)
                    .filter(Signal.is_active == True)
                    .order_by(desc(Signal.created_at))
                    .limit(5)
                    .all()
                )

                for signal in latest_signals:
                    signal_data = {
                        "symbol": signal.symbol,
                        "bias": signal.bias,
                        "setups": signal.setups or [],
                        "confidence": signal.confidence,
                        "auto_execute": True,
                    }
                    await self._execute_signal(signal_data)

                logger.info(
                    f"Successfully processed {len(latest_signals)} database signals"
                )

        except (OperationalError, DisconnectionError) as e:
            error_msg = str(e).lower()
            if "disk i/o error" in error_msg or "database is locked" in error_msg:
                logger.error(f"SQLite I/O error after {max_retries} attempts: {e}")

                # Attempt database recovery
                try:
                    from src.database.health_check import recover_database_from_io_error

                    recovery_success = await recover_database_from_io_error()
                    if recovery_success:
                        logger.info(
                            "Database recovery successful, retrying signal processing"
                        )
                        # Retry once after recovery
                        return await self._process_database_signals_with_retry(
                            max_retries=1
                        )
                except Exception as recovery_error:
                    logger.error(f"Database recovery failed: {recovery_error}")

                # Log system event for monitoring
                log_system_event(
                    "auto_trading_service",
                    "database_io_error",
                    f"SQLite I/O error after {max_retries} attempts: {e}",
                )
            else:
                # Re-raise non-I/O related database errors
                logger.error(f"Database error in signal processing: {e}")
                raise

        except Exception as e:
            logger.error(f"Unexpected error processing database signals: {e}")
            raise

    async def _execute_signal(self, signal: Dict[str, Any]) -> bool:
        """Execute a trading signal."""
        try:
            if not self.platform_manager:
                logger.warning("Platform manager not available for auto trading")
                return False

            symbol = signal.get("symbol")
            action = signal.get("action")

            if action not in ["buy", "sell"]:
                logger.info(f"Skipping signal with action: {action}")
                return True  # Consider it processed

            # Check if we already have a position in this symbol
            if symbol in self.active_trades:
                logger.info(f"Already have active trade for {symbol}")
                return True

            # Calculate position size based on risk management
            position_size = await self._calculate_position_size(signal)
            if not position_size or position_size <= 0:
                logger.warning(f"Invalid position size calculated for {symbol}")
                return False

            # Create order
            order = {
                "symbol": symbol,
                "side": action,
                "type": "market",  # Use market orders for auto trading
                "quantity": position_size,
                "stop_loss": signal.get("stop_loss"),
                "take_profit": signal.get("take_profit"),
                "comment": f"Auto trade - Signal confidence: {signal.get('confidence', 'N/A')}",
            }

            # Execute the order
            result = await self.platform_manager.place_order(order)

            if result.get("success"):
                # Track the trade
                trade_info = {
                    "order_id": result.get("order_id"),
                    "symbol": symbol,
                    "action": action,
                    "quantity": position_size,
                    "entry_price": signal.get("entry_price"),
                    "stop_loss": signal.get("stop_loss"),
                    "take_profit": signal.get("take_profit"),
                    "platform": result.get("platform"),
                    "timestamp": datetime.now().isoformat(),
                    "signal": signal,
                }

                self.active_trades[symbol] = trade_info
                self.trades_today += 1

                # Log the trade
                log_trade_event(
                    "auto_trade_executed",
                    symbol,
                    action,
                    position_size,
                    signal.get("entry_price"),
                    {
                        "platform": result.get("platform"),
                        "confidence": signal.get("confidence"),
                        "auto_trade": True,
                    },
                )

                # Send notification
                await self._send_trade_notification(trade_info, "opened")

                logger.info(
                    f"Auto trade executed: {action} {position_size} {symbol} @ {signal.get('entry_price')}"
                )
                return True
            else:
                logger.error(
                    f"Failed to execute auto trade for {symbol}: {result.get('error')}"
                )
                return False

        except Exception as e:
            logger.error(f"Error executing signal for {signal.get('symbol')}: {e}")
            return False

    async def _calculate_position_size(self, signal: Dict[str, Any]) -> Optional[float]:
        """Calculate position size based on risk management."""
        try:
            if not self.platform_manager:
                return None

            symbol = signal.get("symbol")
            platform_name = self.platform_manager.get_platform_for_symbol(symbol)

            if not platform_name:
                logger.warning(f"No platform found for {symbol}")
                return None

            executor = self.platform_manager.get_executor(platform_name)
            if not executor:
                return None

            # Get account info
            account_info = await executor.get_account_info()
            if not account_info:
                logger.warning(f"No account info available for {platform_name}")
                return None

            # Calculate position size based on risk percentage
            # AccountInfo.balance is a Dict[str, float], get USD balance
            account_balance = account_info.balance.get(
                "USD", 10000.0
            )  # Default to $10k if no USD balance
            risk_amount = account_balance * (
                config.auto_trading.risk_per_trade_percent / 100
            )

            entry_price = signal.get("entry_price", 0)
            stop_loss = signal.get("stop_loss", 0)

            if not entry_price or not stop_loss:
                logger.warning(f"Invalid entry price or stop loss for {symbol}")
                return None

            # Calculate risk per unit
            risk_per_unit = abs(entry_price - stop_loss)
            if risk_per_unit <= 0:
                logger.warning(f"Invalid risk per unit for {symbol}")
                return None

            # Calculate position size
            position_size = risk_amount / risk_per_unit

            # Apply minimum and maximum limits
            min_size = 0.001  # Minimum position size
            max_size = account_balance * 0.1  # Maximum 10% of account per trade

            position_size = max(min_size, min(position_size, max_size))

            # Round to appropriate decimal places
            if "USD" in symbol or "EUR" in symbol or "GBP" in symbol:
                # Forex - round to 2 decimal places
                position_size = round(position_size, 2)
            else:
                # Crypto - round to 6 decimal places
                position_size = round(position_size, 6)

            logger.info(
                f"Calculated position size for {symbol}: {position_size} (risk: {config.auto_trading.risk_per_trade_percent}%)"
            )
            return position_size

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return None

    async def _manage_active_trades(self):
        """Manage existing active trades."""
        if not self.active_trades:
            return

        for symbol, trade_info in list(self.active_trades.items()):
            try:
                # Check if trade is still open
                is_open = await self._is_trade_open(trade_info)

                if not is_open:
                    # Trade has been closed
                    await self._handle_trade_closure(symbol, trade_info)
                    continue

                # Check for trailing stop or other management rules
                await self._apply_trade_management(symbol, trade_info)

            except Exception as e:
                logger.error(f"Error managing trade for {symbol}: {e}")

    async def _is_trade_open(self, trade_info: Dict[str, Any]) -> bool:
        """Check if a trade is still open."""
        try:
            if not self.platform_manager:
                return False

            platform_name = trade_info.get("platform")
            if not platform_name:
                return False

            executor = self.platform_manager.get_executor(platform_name)
            if not executor:
                return False

            # Get current positions
            positions = await executor.get_positions()

            # Check if our trade is still in positions
            order_id = trade_info.get("order_id")
            symbol = trade_info.get("symbol")

            for position in positions:
                if (
                    position.get("order_id") == order_id
                    or position.get("symbol") == symbol
                ):
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking if trade is open: {e}")
            return False

    async def _handle_trade_closure(self, symbol: str, trade_info: Dict[str, Any]):
        """Handle trade closure."""
        try:
            logger.info(f"Trade closed for {symbol}")

            # Remove from active trades
            del self.active_trades[symbol]

            # Send notification
            await self._send_trade_notification(trade_info, "closed")

            # Log closure
            log_trade_event(
                "auto_trade_closed",
                symbol,
                trade_info.get("action"),
                trade_info.get("quantity"),
                0,  # Exit price would need to be fetched
                {"platform": trade_info.get("platform"), "auto_trade": True},
            )

        except Exception as e:
            logger.error(f"Error handling trade closure for {symbol}: {e}")

    async def _apply_trade_management(self, symbol: str, trade_info: Dict[str, Any]):
        """Apply trade management rules (trailing stops, etc.)."""
        try:
            if not self.platform_manager:
                return

            # Get position manager for trade management
            position_manager = self.platform_manager.get_position_manager()
            if not position_manager:
                return

            # Get current positions for the symbol
            positions = await position_manager.get_positions()
            symbol_positions = [p for p in positions if p.get("symbol") == symbol]

            for position in symbol_positions:
                # Apply trailing stop if profit target reached
                current_price = position.get("current_price", 0)
                open_price = position.get("open_price", 0)
                stop_loss = position.get("stop_loss", 0)
                take_profit = position.get("take_profit", 0)

                if current_price and open_price and stop_loss:
                    # Check if we should move to breakeven (1R profit)
                    if position.get("direction") == "BUY":
                        profit_1r = open_price + (open_price - stop_loss)
                        if current_price >= profit_1r and stop_loss < open_price:
                            # Move stop loss to breakeven
                            await position_manager.modify_position(
                                position.get("id"), stop_loss=open_price
                            )
                            logger.info(f"Moved {symbol} stop loss to breakeven")

                    elif position.get("direction") == "SELL":
                        profit_1r = open_price - (stop_loss - open_price)
                        if current_price <= profit_1r and stop_loss > open_price:
                            # Move stop loss to breakeven
                            await position_manager.modify_position(
                                position.get("id"), stop_loss=open_price
                            )
                            logger.info(f"Moved {symbol} stop loss to breakeven")

                    # Apply trailing stop (simplified implementation)
                    if take_profit and current_price:
                        if position.get("direction") == "BUY":
                            # Trail stop loss up as price moves up
                            new_stop = (
                                current_price - (current_price - open_price) * 0.5
                            )
                            if new_stop > stop_loss:
                                await position_manager.modify_position(
                                    position.get("id"), stop_loss=new_stop
                                )
                                logger.info(
                                    f"Applied trailing stop for {symbol}: {new_stop}"
                                )

                        elif position.get("direction") == "SELL":
                            # Trail stop loss down as price moves down
                            new_stop = (
                                current_price + (open_price - current_price) * 0.5
                            )
                            if new_stop < stop_loss:
                                await position_manager.modify_position(
                                    position.get("id"), stop_loss=new_stop
                                )
                                logger.info(
                                    f"Applied trailing stop for {symbol}: {new_stop}"
                                )

        except Exception as e:
            logger.error(f"Error applying trade management for {symbol}: {e}")

    async def _send_trade_notification(
        self, trade_info: Dict[str, Any], event_type: str
    ):
        """Send trade notification via Telegram."""
        try:
            await send_trade_notification(trade_info, event_type)
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")

    def add_signal(self, signal: Dict[str, Any]) -> bool:
        """Add a trading signal to the pending queue.

        Args:
            signal: Trading signal dictionary with symbol, side, entry_price, etc.

        Returns:
            bool: True if signal was added, False otherwise
        """
        if not self.running:
            logger.warning("Auto trading service is not running, signal ignored")
            return False

        # Validate signal format
        required_fields = ["symbol", "side", "entry_price"]
        if not all(field in signal for field in required_fields):
            logger.error(
                f"Invalid signal format, missing required fields: {required_fields}"
            )
            return False

        # Add signal to pending queue
        self.pending_signals.append(signal)
        logger.info(
            f"Added signal to auto trading queue: {signal['symbol']} {signal['side']} {signal['entry_price']}"
        )
        return True

    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "running": self.running,
            "enabled": config.auto_trading.enabled,
            "trades_today": self.trades_today,
            "max_trades_per_day": config.auto_trading.max_trades_per_day,
            "active_trades": len(self.active_trades),
            "pending_signals": len(self.pending_signals),
            "risk_per_trade": config.auto_trading.risk_per_trade_percent,
            "active_symbols": list(self.active_trades.keys()),
        }


"""Global service instance for automatic trading.

This will be initialized in main.py and provides access to the AutoTradingService
throughout the application.
"""
auto_trading_service = None
