"""
Multi-user service orchestrator for the trading system.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..bridge.crypto_bridge import CryptoBridge
from ..bridge.ea_bridge import EABridge
from ..bridge.signal_distributor import SignalDistributor
from ..execution.multi_user_order_manager import MultiUserOrderManager
from ..execution.multi_user_position_manager import MultiUserPositionManager
from ..telegram_bot.core.trading_bot import TradingBot
from .config_manager import ConfigManager
from .user_manager import UserManager

logger = logging.getLogger(__name__)


class MultiUserService:
    """Orchestrates multi-user trading operations with enhanced signal distribution."""

    def __init__(self, telegram_bot_token: str):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.ea_bridge = EABridge()
        self.crypto_bridge = CryptoBridge()
        self.signal_distributor = SignalDistributor()

        # Enhanced multi-user components
        self.position_manager = MultiUserPositionManager(
            self.ea_bridge, self.user_manager, self.config_manager
        )
        self.order_manager = MultiUserOrderManager(
            self.ea_bridge,
            self.position_manager,
            self.user_manager,
            self.config_manager,
        )

        # Use existing Telegram bot instance
        self.telegram_bot = None
        self.notification_manager = None

        self._running = False
        self._tasks = []

        # Signal distribution queues
        self._immediate_queue = asyncio.Queue()
        self._delayed_queue = asyncio.Queue()
        self._batch_queue = []

        # Signal processing state
        self._processing_signals = False
        self._batch_processing_task = None
        self._delayed_processing_task = None

        # Statistics
        self._signal_stats = {
            "total_processed": 0,
            "total_distributed": 0,
            "total_skipped": 0,
            "immediate_sent": 0,
            "delayed_sent": 0,
            "batch_sent": 0,
            "auto_trades_executed": 0,
            "last_signal_time": None,
        }

    async def start(self) -> None:
        """Start the multi-user service with signal distribution."""
        if self._running:
            return

        logger.info("Starting multi-user trading service...")

        # Multi-user service doesn't manage its own bot instance
        # It uses the existing bot from the main application

        # Initialize notification manager if bot is available
        if self.telegram_bot:
            self.notification_manager = self.telegram_bot.notification_manager

        # Start signal distribution tasks
        self._tasks.append(asyncio.create_task(self._process_immediate_signals()))
        self._tasks.append(asyncio.create_task(self._process_delayed_signals()))
        self._batch_processing_task = asyncio.create_task(self._process_batch_signals())

        # Start monitoring tasks
        self._tasks.append(asyncio.create_task(self._monitor_positions()))
        self._tasks.append(asyncio.create_task(self._health_check_loop()))

        # Start enhanced multi-user components
        await self.position_manager.start()
        await self.order_manager.start()

        self._running = True
        logger.info("Multi-user trading service started with signal distribution")

    async def stop(self) -> None:
        """Stop the multi-user service and signal distribution."""
        if not self._running:
            return

        logger.info("Stopping multi-user trading service...")
        self._running = False

        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self._tasks, return_exceptions=True)

        # Process remaining signals
        await self._flush_signal_queues()

        logger.info("Multi-user trading service stopped")

    async def process_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and distribute trading signal to users with enhanced distribution system."""
        try:
            symbol = signal_data.get("symbol", "Unknown")
            logger.info(f"Processing signal for {symbol}")

            # Validate signal format
            if not self._validate_signal_format(signal_data):
                logger.error("Invalid signal format")
                return {"success": False, "error": "Invalid signal format"}

            # Enrich signal with metadata
            signal_data = await self._enrich_signal_data(signal_data)

            # Get subscribed users and categorize distribution
            distribution_plan = await self._create_distribution_plan(signal_data)

            if not distribution_plan["total_users"]:
                logger.info(f"No users subscribed to {symbol}")
                return {
                    "success": True,
                    "distributed_to": [],
                    "skipped": [],
                    "execution_results": {"successful": [], "failed": []},
                }

            # Queue signals for distribution
            await self._queue_signals_for_distribution(signal_data, distribution_plan)

            # Execute trades for users with auto-trading enabled
            execution_results = await self._execute_signal_trades(
                signal_data, distribution_plan["immediate"]
            )

            # Update statistics
            self._update_signal_stats(distribution_plan)

            return {
                "success": True,
                "distributed_to": distribution_plan["immediate"]
                + distribution_plan["delayed"]
                + distribution_plan["batch"],
                "skipped": distribution_plan["skipped"],
                "execution_results": execution_results,
                "distribution_plan": distribution_plan,
            }

        except Exception as e:
            logger.error(f"Failed to process signal: {e}")
            return {"success": False, "error": str(e)}

    def set_telegram_bot(self, telegram_bot: TradingBot) -> None:
        """Set the Telegram bot instance for notifications."""
        self.telegram_bot = telegram_bot
        if telegram_bot and hasattr(telegram_bot, "notification_manager"):
            self.notification_manager = telegram_bot.notification_manager
        logger.info("Telegram bot instance set for multi-user service")

    async def send_signal_to_users(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy method for backward compatibility - redirects to process_signal."""
        return await self.process_signal(signal_data)

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
        """Get comprehensive service statistics including signal distribution."""
        try:
            bot_stats = {}
            if self.telegram_bot:
                try:
                    bot_stats = await self.telegram_bot.get_bot_stats()
                except Exception:
                    bot_stats = {"error": "Bot stats unavailable"}

            # Get queue sizes
            queue_stats = {
                "immediate_queue_size": self._immediate_queue.qsize(),
                "delayed_queue_size": self._delayed_queue.qsize(),
                "batch_queue_size": len(self._batch_queue),
            }

            return {
                "service_status": "running" if self._running else "stopped",
                "bot_stats": bot_stats,
                "active_tasks": len(self._tasks),
                "signal_stats": self._signal_stats.copy(),
                "queue_stats": queue_stats,
                "last_health_check": datetime.now(timezone.utc).isoformat(),
                "uptime": "Enhanced multi-user service with signal distribution",
            }

        except Exception as e:
            logger.error(f"Failed to get service stats: {e}")
            return {"service_status": "error", "error": str(e)}

    async def get_signal_distribution_stats(self) -> Dict[str, Any]:
        """Get detailed signal distribution statistics."""
        try:
            return {
                "total_processed": self._signal_stats["total_processed"],
                "total_distributed": self._signal_stats["total_distributed"],
                "total_skipped": self._signal_stats["total_skipped"],
                "distribution_breakdown": {
                    "immediate": self._signal_stats["immediate_sent"],
                    "delayed": self._signal_stats["delayed_sent"],
                    "batch": self._signal_stats["batch_sent"],
                },
                "auto_trades_executed": self._signal_stats["auto_trades_executed"],
                "last_signal_time": self._signal_stats["last_signal_time"],
                "queue_status": {
                    "immediate": self._immediate_queue.qsize(),
                    "delayed": self._delayed_queue.qsize(),
                    "batch": len(self._batch_queue),
                },
                "distribution_efficiency": self._calculate_distribution_efficiency(),
            }

        except Exception as e:
            logger.error(f"Failed to get signal distribution stats: {e}")
            return {"error": str(e)}

    def _calculate_distribution_efficiency(self) -> float:
        """Calculate signal distribution efficiency."""
        try:
            total_processed = self._signal_stats["total_processed"]
            if total_processed == 0:
                return 0.0

            total_distributed = self._signal_stats["total_distributed"]
            return (total_distributed / total_processed) * 100

        except Exception:
            return 0.0

    async def force_process_batch_signals(self) -> Dict[str, Any]:
        """Force process all pending batch signals."""
        try:
            if not self._batch_queue:
                return {"success": True, "message": "No batch signals to process"}

            processed_count = 0
            user_signals = defaultdict(list)

            for signal_item in self._batch_queue:
                user_signals[signal_item["telegram_id"]].append(signal_item)

            for telegram_id, signals in user_signals.items():
                try:
                    await self._send_batch_notification(telegram_id, signals)
                    processed_count += len(signals)
                except Exception as e:
                    logger.error(f"Error processing batch for {telegram_id}: {e}")

            self._batch_queue.clear()
            self._signal_stats["batch_sent"] += processed_count

            return {
                "success": True,
                "processed": processed_count,
                "users_notified": len(user_signals),
            }

        except Exception as e:
            logger.error(f"Error force processing batch signals: {e}")
            return {"success": False, "error": str(e)}

    async def _enrich_signal_data(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich signal data with additional metadata."""
        try:
            # Add processing timestamp
            signal_data["processed_at"] = datetime.now(timezone.utc).isoformat()
            signal_data["signal_id"] = signal_data.get(
                "signal_id", f"sig_{int(datetime.now(timezone.utc).timestamp())}"
            )

            # Add risk metrics
            setups = signal_data.get("setups", [])
            if setups:
                setup = setups[0]
                entry_zone = setup.get("entry_zone", [])
                sl = setup.get("sl", 0)
                tp = setup.get("tp", [])

                if entry_zone and sl and tp:
                    # Calculate risk-reward ratio
                    entry_price = (
                        sum(entry_zone) / len(entry_zone)
                        if len(entry_zone) == 2
                        else entry_zone[0]
                    )
                    risk = abs(entry_price - sl)
                    reward = abs(tp[0] - entry_price) if tp else 0
                    rr_ratio = reward / risk if risk > 0 else 0

                    signal_data["risk_metrics"] = {
                        "risk_amount": risk,
                        "reward_amount": reward,
                        "risk_reward_ratio": rr_ratio,
                        "recommended_position_size": self._calculate_position_size(
                            risk, signal_data
                        ),
                    }

            return signal_data

        except Exception as e:
            logger.error(f"Error enriching signal data: {e}")
            return signal_data

    async def _create_distribution_plan(
        self, signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a distribution plan for the signal."""
        try:
            symbol = signal_data.get("symbol")
            confidence = signal_data.get("confidence", 0)

            # Get all subscribed users
            subscribers = await self.signal_distributor.get_subscribed_users(
                symbol, confidence
            )

            if not subscribers:
                return {
                    "total_users": 0,
                    "immediate": [],
                    "delayed": [],
                    "batch": [],
                    "skipped": [],
                }

            immediate = []
            delayed = []
            batch = []
            skipped = []

            for subscriber in subscribers:
                telegram_id = subscriber["telegram_id"]

                # Check if signal should be distributed
                user_config = await self.config_manager.get_all_user_configs(
                    telegram_id
                )
                should_distribute = (
                    await self.signal_distributor.should_distribute_signal(
                        signal_data, user_config
                    )
                )

                if not should_distribute:
                    skipped.append(telegram_id)
                    continue

                # Categorize based on user preferences
                preferences = await self.signal_distributor.get_user_signal_preferences(
                    telegram_id
                )
                signal_confidence = signal_data.get("confidence", 0)

                if signal_confidence >= preferences.get("immediate_threshold", 80):
                    immediate.append(telegram_id)
                elif signal_confidence >= preferences.get("delayed_threshold", 60):
                    delayed.append(telegram_id)
                elif signal_confidence >= preferences.get("batch_threshold", 40):
                    batch.append(telegram_id)
                else:
                    skipped.append(telegram_id)

            return {
                "total_users": len(subscribers),
                "immediate": immediate,
                "delayed": delayed,
                "batch": batch,
                "skipped": skipped,
                "symbol": symbol,
                "confidence": confidence,
            }

        except Exception as e:
            logger.error(f"Error creating distribution plan: {e}")
            return {
                "total_users": 0,
                "immediate": [],
                "delayed": [],
                "batch": [],
                "skipped": [],
            }

    async def _queue_signals_for_distribution(
        self, signal_data: Dict[str, Any], distribution_plan: Dict[str, Any]
    ) -> None:
        """Queue signals for distribution based on the plan."""
        try:
            # Immediate signals
            for telegram_id in distribution_plan["immediate"]:
                await self._immediate_queue.put(
                    {
                        "signal_data": signal_data,
                        "telegram_id": telegram_id,
                        "distribution_type": "immediate",
                    }
                )

            # Delayed signals
            for telegram_id in distribution_plan["delayed"]:
                delay_minutes = await self._get_user_delay_preference(telegram_id)
                delayed_time = datetime.now(timezone.utc) + timedelta(
                    minutes=delay_minutes
                )

                await self._delayed_queue.put(
                    {
                        "signal_data": signal_data,
                        "telegram_id": telegram_id,
                        "distribution_type": "delayed",
                        "deliver_at": delayed_time,
                    }
                )

            # Batch signals
            for telegram_id in distribution_plan["batch"]:
                self._batch_queue.append(
                    {
                        "signal_data": signal_data,
                        "telegram_id": telegram_id,
                        "distribution_type": "batch",
                        "queued_at": datetime.now(timezone.utc),
                    }
                )

            logger.info(
                f"Queued signal for {len(distribution_plan['immediate'])} immediate, "
                f"{len(distribution_plan['delayed'])} delayed, "
                f"{len(distribution_plan['batch'])} batch recipients"
            )

        except Exception as e:
            logger.error(f"Error queuing signals: {e}")

    async def _get_user_delay_preference(self, telegram_id: int) -> int:
        """Get user's delay preference for signals."""
        try:
            preferences = await self.signal_distributor.get_user_signal_preferences(
                telegram_id
            )
            return preferences.get("delay_minutes", 5)
        except Exception:
            return 5  # Default 5 minutes

    def _calculate_position_size(
        self, risk_amount: float, signal_data: Dict[str, Any]
    ) -> float:
        """Calculate recommended position size based on risk."""
        try:
            # Get signal setups for position sizing calculation
            setups = signal_data.get("setups", [])
            if not setups:
                logger.warning("No setups found in signal data for position sizing")
                return 0.01  # Default fallback

            # Use the first setup for calculation
            setup = setups[0]
            entry_zone = setup.get("entry_zone", [0, 0])
            stop_loss = setup.get("sl", 0)

            # Calculate average entry price from entry zone
            if isinstance(entry_zone, list) and len(entry_zone) >= 2:
                avg_entry_price = (entry_zone[0] + entry_zone[1]) / 2
            else:
                avg_entry_price = float(entry_zone) if entry_zone else 0

            # Calculate position size based on risk amount and stop loss distance
            if stop_loss and avg_entry_price > 0:
                stop_loss_distance = abs(avg_entry_price - stop_loss)

                if stop_loss_distance > 0:
                    # Position size = Risk amount / Stop loss distance
                    position_size = risk_amount / stop_loss_distance

                    # Apply reasonable limits
                    min_position = 0.01
                    max_position = 10.0
                    position_size = max(min_position, min(position_size, max_position))

                    # Round to 2 decimal places for standard lots
                    position_size = round(position_size, 2)

                    logger.info(
                        f"Calculated position size: {position_size} "
                        f"(risk: {risk_amount:.2f}, SL distance: {stop_loss_distance:.5f})"
                    )

                    return position_size

            # Fallback calculation based on risk-reward ratio
            risk_metrics = signal_data.get("risk_metrics", {})
            rr_ratio = risk_metrics.get("risk_reward_ratio", 1.5)
            base_position = 0.01

            if rr_ratio >= 2.0:
                return base_position * 1.2  # Increase position for better RR
            elif rr_ratio >= 1.5:
                return base_position
            else:
                return base_position * 0.8  # Reduce position for poor RR

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.01

    async def _process_immediate_signals(self) -> None:
        """Process immediate signal distribution."""
        while self._running:
            try:
                # Get signal from queue
                signal_item = await self._immediate_queue.get()

                if not self._running:
                    break

                await self._distribute_signal_to_user(
                    signal_item["signal_data"],
                    signal_item["telegram_id"],
                    signal_item["distribution_type"],
                )

                self._signal_stats["immediate_sent"] += 1
                self._immediate_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing immediate signal: {e}")
                await asyncio.sleep(1)

    async def _process_delayed_signals(self) -> None:
        """Process delayed signal distribution."""
        delayed_signals = []

        while self._running:
            try:
                # Get signal from queue
                signal_item = await self._delayed_queue.get()

                if not self._running:
                    break

                # Add to delayed processing list
                delayed_signals.append(signal_item)
                self._delayed_queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing delayed signal: {e}")
                await asyncio.sleep(1)

        # Process any remaining delayed signals
        for signal_item in delayed_signals:
            try:
                await self._distribute_signal_to_user(
                    signal_item["signal_data"],
                    signal_item["telegram_id"],
                    signal_item["distribution_type"],
                )
                self._signal_stats["delayed_sent"] += 1
            except Exception as e:
                logger.error(f"Error distributing delayed signal: {e}")

    async def _process_batch_signals(self) -> None:
        """Process batch signal distribution."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Process every 5 minutes

                if not self._batch_queue:
                    continue

                # Group signals by user
                user_signals = defaultdict(list)
                for signal_item in self._batch_queue:
                    user_signals[signal_item["telegram_id"]].append(signal_item)

                # Send batch notifications
                for telegram_id, signals in user_signals.items():
                    try:
                        await self._send_batch_notification(telegram_id, signals)
                        self._signal_stats["batch_sent"] += len(signals)
                    except Exception as e:
                        logger.error(
                            f"Error sending batch notification to {telegram_id}: {e}"
                        )

                # Clear processed signals
                self._batch_queue.clear()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processing: {e}")

    async def _distribute_signal_to_user(
        self, signal_data: Dict[str, Any], telegram_id: int, distribution_type: str
    ) -> None:
        """Distribute signal to a specific user."""
        try:
            # Format signal message
            message = await self.signal_distributor.format_signal_message(
                signal_data, telegram_id
            )

            # Send via notification manager if available
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    message,
                    notification_type="signal",
                    chat_ids=[telegram_id],
                    parse_mode="Markdown",
                )
            elif self.telegram_bot:
                # Fallback to direct bot sending
                await self.telegram_bot.send_message(
                    telegram_id, message, parse_mode="Markdown"
                )
            else:
                logger.error("No notification system available")

            logger.info(
                f"Signal distributed to user {telegram_id} ({distribution_type})"
            )

        except Exception as e:
            logger.error(f"Error distributing signal to user {telegram_id}: {e}")
            raise

    async def _send_batch_notification(
        self, telegram_id: int, signals: List[Dict[str, Any]]
    ) -> None:
        """Send batch notification with multiple signals."""
        try:
            if not signals:
                return

            # Create batch message
            message = "📊 **Signal Batch Update** 📊\n\n"
            message += f"You have {len(signals)} new signals:\n\n"

            for i, signal_item in enumerate(signals, 1):
                signal_data = signal_item["signal_data"]
                symbol = signal_data.get("symbol", "Unknown")
                confidence = signal_data.get("confidence", 0)
                bias = signal_data.get("bias", "Unknown")

                message += f"{i}. **{symbol}** - {bias} ({confidence}%)\n"

            message += f"\n⏰ Batch delivered at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"

            # Send batch notification
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    message,
                    notification_type="signal",
                    chat_ids=[telegram_id],
                    parse_mode="Markdown",
                )
            elif self.telegram_bot:
                await self.telegram_bot.send_message(
                    telegram_id, message, parse_mode="Markdown"
                )

            logger.info(
                f"Batch notification sent to user {telegram_id} with {len(signals)} signals"
            )

        except Exception as e:
            logger.error(f"Error sending batch notification to {telegram_id}: {e}")
            raise

    async def _flush_signal_queues(self) -> None:
        """Flush all signal queues on shutdown."""
        try:
            logger.info("Flushing signal queues...")

            # Process remaining immediate signals
            while not self._immediate_queue.empty():
                try:
                    signal_item = self._immediate_queue.get_nowait()
                    await self._distribute_signal_to_user(
                        signal_item["signal_data"],
                        signal_item["telegram_id"],
                        signal_item["distribution_type"],
                    )
                    self._immediate_queue.task_done()
                except Exception as e:
                    logger.error(f"Error flushing immediate signal: {e}")

            # Process remaining delayed signals
            while not self._delayed_queue.empty():
                try:
                    signal_item = self._delayed_queue.get_nowait()
                    await self._distribute_signal_to_user(
                        signal_item["signal_data"],
                        signal_item["telegram_id"],
                        signal_item["distribution_type"],
                    )
                    self._delayed_queue.task_done()
                except Exception as e:
                    logger.error(f"Error flushing delayed signal: {e}")

            # Process remaining batch signals
            if self._batch_queue:
                user_signals = defaultdict(list)
                for signal_item in self._batch_queue:
                    user_signals[signal_item["telegram_id"]].append(signal_item)

                for telegram_id, signals in user_signals.items():
                    try:
                        await self._send_batch_notification(telegram_id, signals)
                    except Exception as e:
                        logger.error(
                            f"Error flushing batch signals for {telegram_id}: {e}"
                        )

                self._batch_queue.clear()

            logger.info("Signal queues flushed")

        except Exception as e:
            logger.error(f"Error flushing signal queues: {e}")

    def _update_signal_stats(self, distribution_plan: Dict[str, Any]) -> None:
        """Update signal processing statistics."""
        try:
            self._signal_stats["total_processed"] += 1
            self._signal_stats["total_distributed"] += (
                len(distribution_plan["immediate"])
                + len(distribution_plan["delayed"])
                + len(distribution_plan["batch"])
            )
            self._signal_stats["total_skipped"] += len(distribution_plan["skipped"])
            self._signal_stats["last_signal_time"] = datetime.now(
                timezone.utc
            ).isoformat()

        except Exception as e:
            logger.error(f"Error updating signal stats: {e}")

    async def _execute_signal_trades(
        self, signal_data: Dict[str, Any], user_ids: List[int]
    ) -> Dict[str, Any]:
        """Execute trades for users with auto-trading enabled."""
        execution_results = {"successful": [], "failed": []}

        for telegram_id in user_ids:
            try:
                # Get user's trading configuration
                trading_config = await self.config_manager.get_user_config(
                    telegram_id, "trading"
                )

                if not trading_config or not trading_config.get(
                    "auto_execution_enabled", False
                ):
                    continue

                # Check if user has platform connections
                connections = await self.user_manager.get_user_platform_connections(
                    telegram_id
                )

                for connection in connections:
                    platform_type = connection["platform_type"]

                    if platform_type == "mt5":
                        success = await self._execute_mt5_trade(
                            telegram_id, signal_data, trading_config
                        )
                    elif platform_type == "crypto":
                        success = await self._execute_crypto_trade(
                            telegram_id, signal_data, trading_config
                        )
                    else:
                        continue

                    if success:
                        execution_results["successful"].append(
                            {"telegram_id": telegram_id, "platform": platform_type}
                        )
                        self._signal_stats["auto_trades_executed"] += 1
                        break
                else:
                    execution_results["failed"].append(
                        {
                            "telegram_id": telegram_id,
                            "reason": "No active platform connections",
                        }
                    )

            except Exception as e:
                logger.error(f"Failed to execute trade for user {telegram_id}: {e}")
                execution_results["failed"].append(
                    {"telegram_id": telegram_id, "reason": str(e)}
                )

        return execution_results

    async def _execute_mt5_trade(
        self,
        telegram_id: int,
        signal_data: Dict[str, Any],
        trading_config: Dict[str, Any],
    ) -> bool:
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
                "notes": setup.get("notes", ""),
            }

            # Send order to EA
            result = await self.ea_bridge.send_order_to_ea(telegram_id, order_data)

            if result:
                # Send confirmation to user
                await self.telegram_bot.send_position_update(
                    telegram_id,
                    {
                        "type": "entry",
                        "symbol": order_data["symbol"],
                        "entry_price": result.get("entry_price"),
                        "position_type": order_data["type"],
                        "volume": result.get("volume"),
                        "sl": order_data["sl"],
                        "tp": order_data["tp"],
                    },
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to execute MT5 trade for user {telegram_id}: {e}")
            return False

    async def _execute_crypto_trade(
        self,
        telegram_id: int,
        signal_data: Dict[str, Any],
        trading_config: Dict[str, Any],
    ) -> bool:
        """Execute crypto trade for user."""
        try:
            # Get first setup from signal
            setups = signal_data.get("setups", [])
            if not setups:
                return False

            setup = setups[0]

            # Prepare order data for crypto exchange
            order_data = {
                "symbol": signal_data.get("symbol").replace(
                    "/", ""
                ),  # Remove slash for exchange format
                "side": "Buy" if setup.get("type") == "BUY" else "Sell",
                "orderType": "Market",  # Start with market orders for simplicity
                "quantity": self._calculate_crypto_quantity(
                    telegram_id, signal_data, trading_config
                ),
            }

            # Place order on crypto exchange
            result = await self.crypto_bridge.place_crypto_order(
                telegram_id, order_data
            )

            if result:
                # Send confirmation to user
                await self.telegram_bot.send_position_update(
                    telegram_id,
                    {
                        "type": "entry",
                        "symbol": signal_data.get("symbol"),
                        "entry_price": result.get("price"),
                        "position_type": setup.get("type"),
                        "volume": order_data["quantity"],
                        "sl": setup.get("sl"),
                        "tp": setup.get("tp"),
                    },
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to execute crypto trade for user {telegram_id}: {e}")
            return False

    def _calculate_crypto_quantity(
        self,
        telegram_id: int,
        signal_data: Dict[str, Any],
        trading_config: Dict[str, Any],
    ) -> float:
        """Calculate crypto trade quantity based on risk management."""
        try:
            # Get risk parameters from trading config
            risk_per_trade_pct = trading_config.get("risk_per_trade_pct", 2.0)
            max_position_size = trading_config.get("max_position_size", 10.0)
            min_position_size = trading_config.get("min_position_size", 0.01)

            # Get account balance (this would come from the exchange API in production)
            # For now, we'll use a default balance or get it from user config
            account_balance = trading_config.get("account_balance", 1000.0)

            # Calculate risk amount in USD
            risk_amount = account_balance * (risk_per_trade_pct / 100)

            # Get signal data for position sizing
            setups = signal_data.get("setups", [])
            if not setups:
                logger.warning(f"No setups found in signal data for user {telegram_id}")
                return min_position_size

            # Use the first setup for calculation
            setup = setups[0]
            entry_price = setup.get("entry_zone", [0, 0])
            stop_loss = setup.get("sl", 0)

            # Calculate entry price (use middle of entry zone)
            if isinstance(entry_price, list) and len(entry_price) >= 2:
                avg_entry_price = (entry_price[0] + entry_price[1]) / 2
            else:
                avg_entry_price = float(entry_price) if entry_price else 0

            # Calculate stop loss distance
            if stop_loss and avg_entry_price > 0:
                stop_loss_distance = abs(avg_entry_price - stop_loss)

                # Calculate position size based on risk
                # Position size = Risk amount / Stop loss distance
                if stop_loss_distance > 0:
                    position_size = risk_amount / stop_loss_distance

                    # Apply position size limits
                    position_size = max(
                        min_position_size, min(position_size, max_position_size)
                    )

                    # Round to appropriate decimal places (crypto typically 4-8 decimals)
                    position_size = round(position_size, 6)

                    logger.info(
                        f"Calculated position size for user {telegram_id}: "
                        f"{position_size} (risk: {risk_amount:.2f}, SL distance: {stop_loss_distance:.6f})"
                    )

                    return position_size

            # Fallback to default if calculation fails
            logger.warning(
                f"Position sizing calculation failed for user {telegram_id}, using default"
            )
            return min_position_size

        except Exception as e:
            logger.error(f"Error calculating position size for user {telegram_id}: {e}")
            return trading_config.get("min_position_size", 0.01)

    async def _monitor_positions(self) -> None:
        """Monitor positions across all users."""
        while self._running:
            try:
                # Get all active users
                admin_users = await self.user_manager.get_all_users(
                    self.user_manager.initial_admin_id
                )

                if admin_users:
                    active_users = [
                        user
                        for user in admin_users
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
                for position in positions:
                    await self._monitor_position(telegram_id, position, "mt5")

        except Exception as e:
            logger.error(f"Error checking MT5 positions for user {telegram_id}: {e}")

    async def _check_crypto_positions(self, telegram_id: int) -> None:
        """Check crypto positions for user."""
        try:
            positions = await self.crypto_bridge.get_crypto_positions(telegram_id)

            if positions:
                for position in positions:
                    await self._monitor_position(telegram_id, position, "crypto")

        except Exception as e:
            logger.error(f"Error checking crypto positions for user {telegram_id}: {e}")

    async def _monitor_position(
        self, telegram_id: int, position: Dict[str, Any], platform: str
    ) -> None:
        """Monitor individual position for various events."""
        try:
            # Get position details
            symbol = position.get("symbol")
            ticket = position.get("ticket")
            current_price = position.get("price_current", position.get("current_price"))
            position.get("price_open", position.get("open_price"))
            profit = position.get("profit", position.get("pnl", 0))
            position_type = position.get("type", position.get("side"))
            volume = position.get("volume")

            # Get user risk preferences
            risk_config = await self.config_manager.get_user_config(
                telegram_id, "risk_management"
            )
            if not risk_config:
                risk_config = {}

            # Check for significant profit/loss changes
            await self._check_profit_loss_alerts(telegram_id, position, risk_config)

            # Check for stop loss hits
            await self._check_stop_loss_hit(telegram_id, position, platform)

            # Check for take profit hits
            await self._check_take_profit_hit(telegram_id, position, platform)

            # Update trailing stops if enabled
            await self._update_trailing_stops(
                telegram_id, position, platform, risk_config
            )

            # Check for margin/drawdown alerts
            await self._check_risk_alerts(telegram_id, position, risk_config)

            # Log position status
            logger.debug(
                f"Monitored position {ticket} for user {telegram_id}: "
                f"{symbol} {position_type} {volume} @ {current_price} P&L: {profit}"
            )

        except Exception as e:
            logger.error(f"Error monitoring position for user {telegram_id}: {e}")

    async def _check_profit_loss_alerts(
        self, telegram_id: int, position: Dict[str, Any], risk_config: Dict[str, Any]
    ) -> None:
        """Check for significant profit/loss changes and send alerts."""
        try:
            profit = position.get("profit", position.get("pnl", 0))
            symbol = position.get("symbol")
            ticket = position.get("ticket")

            # Get alert thresholds
            profit_alert_threshold = risk_config.get(
                "profit_alert_threshold", 50.0
            )  # $50 profit
            loss_alert_threshold = risk_config.get(
                "loss_alert_threshold", -25.0
            )  # $25 loss

            # Check for significant profit
            if profit >= profit_alert_threshold:
                message = "💰 **Profit Alert** 💰\n\n"
                message += f"📈 Position: {symbol} (#{ticket})\n"
                message += f"💵 Current P&L: ${profit:.2f}\n"
                message += "✅ Consider taking partial profits or adjusting stop loss"

                await self._send_position_alert(telegram_id, message)

            # Check for significant loss
            elif profit <= loss_alert_threshold:
                message = "⚠️ **Loss Alert** ⚠️\n\n"
                message += f"📉 Position: {symbol} (#{ticket})\n"
                message += f"💸 Current P&L: ${profit:.2f}\n"
                message += "🛑 Consider reviewing position or risk management"

                await self._send_position_alert(telegram_id, message)

        except Exception as e:
            logger.error(f"Error checking profit/loss alerts: {e}")

    async def _check_stop_loss_hit(
        self, telegram_id: int, position: Dict[str, Any], platform: str
    ) -> None:
        """Check if stop loss has been hit."""
        try:
            current_price = position.get("price_current", position.get("current_price"))
            stop_loss = position.get("sl", position.get("stop_loss"))
            position_type = position.get("type", position.get("side"))
            symbol = position.get("symbol")
            ticket = position.get("ticket")

            if not stop_loss or not current_price:
                return

            # Check if SL is hit based on position type
            sl_hit = False
            if position_type in ["BUY", "Buy", 0] and current_price <= stop_loss:
                sl_hit = True
            elif position_type in ["SELL", "Sell", 1] and current_price >= stop_loss:
                sl_hit = True

            if sl_hit:
                message = "🛑 **Stop Loss Hit** 🛑\n\n"
                message += f"📍 Position: {symbol} (#{ticket})\n"
                message += f"💰 Stop Loss: {stop_loss}\n"
                message += f"📊 Current Price: {current_price}\n"
                message += (
                    f"⏰ Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )

                await self._send_position_alert(telegram_id, message)

        except Exception as e:
            logger.error(f"Error checking stop loss: {e}")

    async def _check_take_profit_hit(
        self, telegram_id: int, position: Dict[str, Any], platform: str
    ) -> None:
        """Check if take profit has been hit."""
        try:
            current_price = position.get("price_current", position.get("current_price"))
            take_profit = position.get("tp", position.get("take_profit"))
            position_type = position.get("type", position.get("side"))
            symbol = position.get("symbol")
            ticket = position.get("ticket")

            if not take_profit or not current_price:
                return

            # Check if TP is hit based on position type
            tp_hit = False
            if position_type in ["BUY", "Buy", 0] and current_price >= take_profit:
                tp_hit = True
            elif position_type in ["SELL", "Sell", 1] and current_price <= take_profit:
                tp_hit = True

            if tp_hit:
                message = "🎯 **Take Profit Hit** 🎯\n\n"
                message += f"📍 Position: {symbol} (#{ticket})\n"
                message += f"💰 Take Profit: {take_profit}\n"
                message += f"📊 Current Price: {current_price}\n"
                message += (
                    f"⏰ Time: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
                )

                await self._send_position_alert(telegram_id, message)

        except Exception as e:
            logger.error(f"Error checking take profit: {e}")

    async def _update_trailing_stops(
        self,
        telegram_id: int,
        position: Dict[str, Any],
        platform: str,
        risk_config: Dict[str, Any],
    ) -> None:
        """Update trailing stops if enabled."""
        try:
            # Check if trailing stops are enabled
            trailing_enabled = risk_config.get("trailing_stop_enabled", False)
            if not trailing_enabled:
                return

            current_price = position.get("price_current", position.get("current_price"))
            open_price = position.get("price_open", position.get("open_price"))
            current_sl = position.get("sl", position.get("stop_loss"))
            position_type = position.get("type", position.get("side"))
            symbol = position.get("symbol")
            ticket = position.get("ticket")

            if not current_price or not open_price:
                return

            # Get trailing stop distance (in pips or percentage)
            trailing_distance = risk_config.get(
                "trailing_stop_distance", 20
            )  # 20 pips default
            trailing_type = risk_config.get(
                "trailing_stop_type", "pips"
            )  # 'pips' or 'percentage'

            # Calculate new stop loss
            new_sl = None

            if position_type in ["BUY", "Buy", 0]:
                # For buy positions, trail stop loss upward
                if trailing_type == "pips":
                    potential_sl = current_price - (
                        trailing_distance * 0.0001
                    )  # Assuming 4-digit quotes
                else:  # percentage
                    potential_sl = current_price * (1 - trailing_distance / 100)

                # Only update if new SL is higher than current SL
                if not current_sl or potential_sl > current_sl:
                    new_sl = potential_sl

            elif position_type in ["SELL", "Sell", 1]:
                # For sell positions, trail stop loss downward
                if trailing_type == "pips":
                    potential_sl = current_price + (trailing_distance * 0.0001)
                else:  # percentage
                    potential_sl = current_price * (1 + trailing_distance / 100)

                # Only update if new SL is lower than current SL
                if not current_sl or potential_sl < current_sl:
                    new_sl = potential_sl

            # Update stop loss if needed
            if (
                new_sl and abs(new_sl - (current_sl or 0)) > 0.00001
            ):  # Avoid tiny updates
                try:
                    if platform == "mt5":
                        await self.ea_bridge.modify_position(
                            telegram_id, ticket, sl=new_sl
                        )
                    elif platform == "crypto":
                        await self.crypto_bridge.modify_position(
                            telegram_id, ticket, stop_loss=new_sl
                        )

                    # Send notification
                    message = "📈 **Trailing Stop Updated** 📈\n\n"
                    message += f"📍 Position: {symbol} (#{ticket})\n"
                    message += f"🔄 Old SL: {current_sl:.5f}\n"
                    message += f"🆕 New SL: {new_sl:.5f}\n"
                    message += f"📊 Current Price: {current_price:.5f}"

                    await self._send_position_alert(telegram_id, message)

                except Exception as e:
                    logger.error(f"Failed to update trailing stop for {ticket}: {e}")

        except Exception as e:
            logger.error(f"Error updating trailing stops: {e}")

    async def _check_risk_alerts(
        self, telegram_id: int, position: Dict[str, Any], risk_config: Dict[str, Any]
    ) -> None:
        """Check for risk management alerts."""
        try:
            # Get account information
            account_info = {}
            if hasattr(self, "ea_bridge"):
                try:
                    account_info = (
                        await self.ea_bridge.get_account_info(telegram_id) or {}
                    )
                except Exception:
                    pass

            # Check drawdown alerts
            max_drawdown_pct = risk_config.get(
                "max_drawdown_percent", 10.0
            )  # 10% max drawdown
            balance = account_info.get("balance", 0)
            equity = account_info.get("equity", 0)

            if balance > 0 and equity > 0:
                current_drawdown = ((balance - equity) / balance) * 100

                if current_drawdown >= max_drawdown_pct:
                    message = "🚨 **Drawdown Alert** 🚨\n\n"
                    message += f"📉 Current Drawdown: {current_drawdown:.2f}%\n"
                    message += f"⚠️ Maximum Allowed: {max_drawdown_pct:.2f}%\n"
                    message += f"💰 Balance: ${balance:.2f}\n"
                    message += f"💎 Equity: ${equity:.2f}\n"
                    message += "🛑 Consider reducing position sizes or stopping trading"

                    await self._send_position_alert(telegram_id, message)

            # Check margin level alerts
            margin_level = account_info.get("margin_level", 0)
            min_margin_level = risk_config.get(
                "min_margin_level", 200.0
            )  # 200% minimum

            if margin_level > 0 and margin_level < min_margin_level:
                message = "⚠️ **Margin Alert** ⚠️\n\n"
                message += f"📊 Current Margin Level: {margin_level:.2f}%\n"
                message += f"🎯 Minimum Required: {min_margin_level:.2f}%\n"
                message += "🚨 Risk of margin call - consider closing positions"

                await self._send_position_alert(telegram_id, message)

        except Exception as e:
            logger.error(f"Error checking risk alerts: {e}")

    async def _send_position_alert(self, telegram_id: int, message: str) -> None:
        """Send position alert to user."""
        try:
            if self.notification_manager:
                await self.notification_manager.send_notification(
                    message,
                    notification_type="position_alert",
                    chat_ids=[telegram_id],
                    parse_mode="Markdown",
                )
            elif self.telegram_bot:
                await self.telegram_bot.send_message(
                    telegram_id, message, parse_mode="Markdown"
                )
            else:
                logger.warning(
                    f"Cannot send position alert to {telegram_id}: No notification system available"
                )

        except Exception as e:
            logger.error(f"Failed to send position alert to {telegram_id}: {e}")

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
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {"status": "unknown", "error": None},
            "telegram_bot": {"status": "unknown", "error": None},
            "ea_bridge": {"status": "unknown", "error": None, "connected_users": 0},
            "crypto_bridge": {
                "status": "unknown",
                "error": None,
                "connected_exchanges": 0,
            },
            "signal_queues": {"status": "unknown", "sizes": {}},
            "memory_usage": {"status": "unknown", "usage_mb": 0},
            "overall_status": "unknown",
        }

        try:
            # Check database connectivity
            await self._check_database_health(health_status)

            # Check Telegram bot status
            await self._check_telegram_bot_health(health_status)

            # Check EA connections
            await self._check_ea_bridge_health(health_status)

            # Check crypto exchange connections
            await self._check_crypto_bridge_health(health_status)

            # Check signal queue health
            await self._check_signal_queue_health(health_status)

            # Check memory usage
            await self._check_memory_usage(health_status)

            # Determine overall status
            self._calculate_overall_health_status(health_status)

            # Log health status
            overall_status = health_status["overall_status"]
            if overall_status == "healthy":
                logger.debug("Health check completed - all systems healthy")
            elif overall_status == "warning":
                logger.warning(
                    f"Health check completed with warnings: {self._get_health_issues(health_status)}"
                )
            else:
                logger.error(
                    f"Health check completed with critical issues: {self._get_health_issues(health_status)}"
                )

            # Send alerts for critical issues
            if overall_status == "critical":
                await self._send_health_alert(health_status)

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["overall_status"] = "critical"
            health_status["health_check_error"] = str(e)

            if self.telegram_bot:
                try:
                    await self.telegram_bot.send_notification(
                        f"Health check system failure: {e}", "critical"
                    )
                except Exception as alert_error:
                    logger.error(f"Failed to send health check alert: {alert_error}")

    async def _check_database_health(self, health_status: Dict[str, Any]) -> None:
        """Check database connectivity and health."""
        try:
            from ..database.session import SessionLocal

            # Test database connection
            session = SessionLocal()
            try:
                # Simple query to test connection
                from sqlalchemy import text

                result = session.execute(text("SELECT 1"))
                result.fetchone()

                health_status["database"]["status"] = "healthy"
                logger.debug("Database health check: HEALTHY")

            except Exception as e:
                health_status["database"]["status"] = "critical"
                health_status["database"]["error"] = str(e)
                logger.error(f"Database health check: CRITICAL - {e}")
            finally:
                session.close()

        except Exception as e:
            health_status["database"]["status"] = "critical"
            health_status["database"][
                "error"
            ] = f"Database import/initialization failed: {e}"
            logger.error(f"Database health check failed: {e}")

    async def _check_telegram_bot_health(self, health_status: Dict[str, Any]) -> None:
        """Check Telegram bot status."""
        try:
            if self.telegram_bot:
                # Check if bot is running and responsive
                try:
                    # Test bot connection with getMe
                    if (
                        hasattr(self.telegram_bot, "application")
                        and self.telegram_bot.application
                    ):
                        bot_info = await self.telegram_bot.application.bot.get_me()
                        if bot_info:
                            health_status["telegram_bot"]["status"] = "healthy"
                            health_status["telegram_bot"][
                                "bot_username"
                            ] = bot_info.username
                            logger.debug(
                                f"Telegram bot health check: HEALTHY - {bot_info.username}"
                            )
                        else:
                            health_status["telegram_bot"]["status"] = "warning"
                            health_status["telegram_bot"][
                                "error"
                            ] = "Bot info unavailable"
                    else:
                        health_status["telegram_bot"]["status"] = "warning"
                        health_status["telegram_bot"][
                            "error"
                        ] = "Bot application not initialized"

                except Exception as e:
                    health_status["telegram_bot"]["status"] = "critical"
                    health_status["telegram_bot"]["error"] = str(e)
                    logger.error(f"Telegram bot health check: CRITICAL - {e}")
            else:
                health_status["telegram_bot"]["status"] = "critical"
                health_status["telegram_bot"][
                    "error"
                ] = "Telegram bot instance not available"
                logger.error("Telegram bot health check: CRITICAL - No bot instance")

        except Exception as e:
            health_status["telegram_bot"]["status"] = "critical"
            health_status["telegram_bot"]["error"] = f"Health check failed: {e}"
            logger.error(f"Telegram bot health check failed: {e}")

    async def _check_ea_bridge_health(self, health_status: Dict[str, Any]) -> None:
        """Check EA bridge connections."""
        try:
            if self.ea_bridge:
                # Get connection status for all users
                try:
                    connection_health = (
                        await self.ea_bridge.get_all_user_connections_health()
                    )

                    if connection_health:
                        connected_users = len(
                            [
                                conn
                                for conn in connection_health.values()
                                if isinstance(conn, dict) and conn.get("connected")
                            ]
                        )
                        total_users = len(connection_health)

                        health_status["ea_bridge"]["connected_users"] = connected_users
                        health_status["ea_bridge"]["total_users"] = total_users

                        if connected_users == total_users and total_users > 0:
                            health_status["ea_bridge"]["status"] = "healthy"
                        elif connected_users > 0:
                            health_status["ea_bridge"]["status"] = "warning"
                            health_status["ea_bridge"][
                                "error"
                            ] = f"Only {connected_users}/{total_users} EA connections active"
                        else:
                            health_status["ea_bridge"]["status"] = "warning"
                            health_status["ea_bridge"][
                                "error"
                            ] = "No active EA connections"

                        logger.debug(
                            f"EA bridge health check: {connected_users}/{total_users} connections active"
                        )
                    else:
                        health_status["ea_bridge"]["status"] = "warning"
                        health_status["ea_bridge"][
                            "error"
                        ] = "No EA connection data available"

                except Exception as e:
                    health_status["ea_bridge"]["status"] = "warning"
                    health_status["ea_bridge"]["error"] = str(e)
                    logger.warning(f"EA bridge health check failed: {e}")
            else:
                health_status["ea_bridge"]["status"] = "warning"
                health_status["ea_bridge"]["error"] = "EA bridge not initialized"

        except Exception as e:
            health_status["ea_bridge"]["status"] = "warning"
            health_status["ea_bridge"]["error"] = f"Health check failed: {e}"
            logger.warning(f"EA bridge health check failed: {e}")

    async def _check_crypto_bridge_health(self, health_status: Dict[str, Any]) -> None:
        """Check crypto exchange connections."""
        try:
            if self.crypto_bridge:
                # Check exchange connections
                try:
                    # This would check exchange API connectivity
                    # For now, we'll just verify the bridge is available
                    health_status["crypto_bridge"]["status"] = "healthy"
                    health_status["crypto_bridge"][
                        "connected_exchanges"
                    ] = 1  # Placeholder
                    logger.debug("Crypto bridge health check: HEALTHY")

                except Exception as e:
                    health_status["crypto_bridge"]["status"] = "warning"
                    health_status["crypto_bridge"]["error"] = str(e)
                    logger.warning(f"Crypto bridge health check: WARNING - {e}")
            else:
                health_status["crypto_bridge"]["status"] = "warning"
                health_status["crypto_bridge"][
                    "error"
                ] = "Crypto bridge not initialized"

        except Exception as e:
            health_status["crypto_bridge"]["status"] = "warning"
            health_status["crypto_bridge"]["error"] = f"Health check failed: {e}"
            logger.warning(f"Crypto bridge health check failed: {e}")

    async def _check_signal_queue_health(self, health_status: Dict[str, Any]) -> None:
        """Check signal queue health."""
        try:
            queue_sizes = {
                "immediate": self._immediate_queue.qsize(),
                "delayed": self._delayed_queue.qsize(),
                "batch": len(self._batch_queue),
            }

            health_status["signal_queues"]["sizes"] = queue_sizes

            # Check for queue overflow
            max_queue_size = 1000  # Configurable threshold
            total_queued = sum(queue_sizes.values())

            if total_queued > max_queue_size:
                health_status["signal_queues"]["status"] = "warning"
                health_status["signal_queues"][
                    "error"
                ] = f"High queue size: {total_queued} items"
                logger.warning(
                    f"Signal queue health: WARNING - {total_queued} items queued"
                )
            else:
                health_status["signal_queues"]["status"] = "healthy"
                logger.debug(
                    f"Signal queue health: HEALTHY - {total_queued} items queued"
                )

        except Exception as e:
            health_status["signal_queues"]["status"] = "warning"
            health_status["signal_queues"]["error"] = f"Health check failed: {e}"
            logger.warning(f"Signal queue health check failed: {e}")

    async def _check_memory_usage(self, health_status: Dict[str, Any]) -> None:
        """Check memory usage."""
        try:
            import os

            import psutil

            # Get current process memory usage
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_usage_mb = memory_info.rss / 1024 / 1024  # Convert to MB

            health_status["memory_usage"]["usage_mb"] = round(memory_usage_mb, 2)

            # Check memory thresholds
            warning_threshold = 500  # 500 MB
            critical_threshold = 1000  # 1 GB

            if memory_usage_mb > critical_threshold:
                health_status["memory_usage"]["status"] = "critical"
                health_status["memory_usage"][
                    "error"
                ] = f"High memory usage: {memory_usage_mb:.2f} MB"
                logger.error(
                    f"Memory usage health: CRITICAL - {memory_usage_mb:.2f} MB"
                )
            elif memory_usage_mb > warning_threshold:
                health_status["memory_usage"]["status"] = "warning"
                health_status["memory_usage"][
                    "error"
                ] = f"Elevated memory usage: {memory_usage_mb:.2f} MB"
                logger.warning(
                    f"Memory usage health: WARNING - {memory_usage_mb:.2f} MB"
                )
            else:
                health_status["memory_usage"]["status"] = "healthy"
                logger.debug(f"Memory usage health: HEALTHY - {memory_usage_mb:.2f} MB")

        except ImportError:
            health_status["memory_usage"]["status"] = "unknown"
            health_status["memory_usage"]["error"] = "psutil not available"
        except Exception as e:
            health_status["memory_usage"]["status"] = "unknown"
            health_status["memory_usage"]["error"] = f"Health check failed: {e}"
            logger.warning(f"Memory usage health check failed: {e}")

    def _calculate_overall_health_status(self, health_status: Dict[str, Any]) -> None:
        """Calculate overall system health status."""
        try:
            critical_count = 0
            warning_count = 0
            healthy_count = 0

            # Count status types
            for component in [
                "database",
                "telegram_bot",
                "ea_bridge",
                "crypto_bridge",
                "signal_queues",
                "memory_usage",
            ]:
                status = health_status.get(component, {}).get("status", "unknown")
                if status == "critical":
                    critical_count += 1
                elif status == "warning":
                    warning_count += 1
                elif status == "healthy":
                    healthy_count += 1

            # Determine overall status
            if critical_count > 0:
                # Database or Telegram bot critical = overall critical
                db_status = health_status.get("database", {}).get("status")
                bot_status = health_status.get("telegram_bot", {}).get("status")

                if db_status == "critical" or bot_status == "critical":
                    health_status["overall_status"] = "critical"
                else:
                    health_status["overall_status"] = (
                        "warning"  # Other components critical but core is ok
                    )
            elif warning_count > 0:
                health_status["overall_status"] = "warning"
            else:
                health_status["overall_status"] = "healthy"

        except Exception as e:
            logger.error(f"Failed to calculate overall health status: {e}")
            health_status["overall_status"] = "unknown"

    def _get_health_issues(self, health_status: Dict[str, Any]) -> List[str]:
        """Get list of health issues."""
        issues = []

        for component in [
            "database",
            "telegram_bot",
            "ea_bridge",
            "crypto_bridge",
            "signal_queues",
            "memory_usage",
        ]:
            component_data = health_status.get(component, {})
            status = component_data.get("status")
            error = component_data.get("error")

            if status in ["critical", "warning"] and error:
                issues.append(f"{component}: {error}")

        return issues

    async def _send_health_alert(self, health_status: Dict[str, Any]) -> None:
        """Send health alert to administrators."""
        try:
            issues = self._get_health_issues(health_status)
            overall_status = health_status["overall_status"]

            if not issues:
                return

            message = "🚨 **System Health Alert** 🚨\n\n"
            message += f"📊 Overall Status: {overall_status.upper()}\n"
            message += f"⏰ Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
            message += "❌ **Issues Detected:**\n"

            for issue in issues[:5]:  # Limit to first 5 issues
                message += f"• {issue}\n"

            if len(issues) > 5:
                message += f"• ... and {len(issues) - 5} more issues\n"

            message += "\n🔧 Administrator intervention may be required."

            # Send to administrators
            if self.telegram_bot:
                try:
                    await self.telegram_bot.send_notification(message, "critical")
                except Exception as e:
                    logger.error(f"Failed to send health alert: {e}")

        except Exception as e:
            logger.error(f"Failed to prepare health alert: {e}")

    # Enhanced Multi-User Methods

    async def initialize_user_trading_session(self, telegram_id: int) -> Dict[str, Any]:
        """Initialize complete trading session for user."""
        try:
            # Initialize EA bridge session
            ea_session = await self.ea_bridge.initialize_user_session(telegram_id)

            # Initialize position tracking
            position_tracking = await self.position_manager.initialize_user_tracking(
                telegram_id
            )

            # Get user risk metrics
            risk_metrics = await self.position_manager.get_user_risk_metrics(
                telegram_id
            )

            return {
                "success": True,
                "ea_session": ea_session,
                "position_tracking": position_tracking,
                "risk_metrics": risk_metrics,
                "message": f"Trading session initialized for user {telegram_id}",
            }

        except Exception as e:
            logger.error(
                f"Failed to initialize trading session for user {telegram_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    async def submit_user_order(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Submit order for specific user with enhanced validation."""
        try:
            # Enhanced order submission with user-specific routing
            result = await self.order_manager.submit_order(telegram_id, order_data)

            if result["success"]:
                logger.info(
                    f"Order submitted for user {telegram_id}: {result.get('order_id')}"
                )
            else:
                logger.warning(
                    f"Order submission failed for user {telegram_id}: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to submit order for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_trading_status(self, telegram_id: int) -> Dict[str, Any]:
        """Get comprehensive trading status for user."""
        try:
            # Get user positions
            positions = await self.position_manager.get_user_positions(telegram_id)

            # Get user risk metrics
            risk_metrics = await self.position_manager.get_user_risk_metrics(
                telegram_id
            )

            # Get pending orders
            pending_orders = await self.order_manager.get_user_pending_orders(
                telegram_id
            )

            # Get recent order history
            order_history = await self.order_manager.get_user_order_history(
                telegram_id, limit=10
            )

            # Get EA connection status
            ea_connection = await self.ea_bridge.get_user_ea_connection(telegram_id)

            return {
                "telegram_id": telegram_id,
                "positions": [self._position_to_dict(pos) for pos in positions],
                "risk_metrics": risk_metrics,
                "pending_orders": pending_orders,
                "recent_orders": [
                    self._order_to_dict(order) for order in order_history
                ],
                "ea_connection": bool(ea_connection),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get trading status for user {telegram_id}: {e}")
            return {"error": str(e)}

    def _position_to_dict(self, position) -> Dict[str, Any]:
        """Convert position object to dictionary."""
        return {
            "ticket": position.mt_ticket,
            "symbol": (
                getattr(position, "instrument", {}).symbol
                if hasattr(position, "instrument")
                else "Unknown"
            ),
            "type": position.direction,
            "volume": position.volume,
            "open_price": position.open_price,
            "current_price": position.current_price,
            "stop_loss": position.stop_loss,
            "take_profit": position.take_profit,
            "pnl": position.unrealized_pnl,
            "open_time": position.open_time,
        }

    def _order_to_dict(self, order) -> Dict[str, Any]:
        """Convert order object to dictionary."""
        return {
            "order_id": order.order_id,
            "symbol": order.symbol,
            "type": order.order_type,
            "volume": order.volume,
            "price": order.price,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "executed_at": order.executed_at.isoformat() if order.executed_at else None,
            "error_message": getattr(order, "error_message", None),
        }

    async def modify_user_position(
        self,
        telegram_id: int,
        ticket: int,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Modify position for specific user."""
        try:
            result = await self.position_manager.modify_user_position(
                telegram_id, ticket, sl, tp
            )

            if result["success"]:
                logger.info(f"Position {ticket} modified for user {telegram_id}")
            else:
                logger.warning(
                    f"Position modification failed for user {telegram_id}: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to modify position for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def close_user_position(
        self, telegram_id: int, ticket: int, volume: Optional[float] = None
    ) -> Dict[str, Any]:
        """Close position for specific user."""
        try:
            result = await self.position_manager.close_user_position(
                telegram_id, ticket, volume
            )

            if result["success"]:
                logger.info(f"Position {ticket} closed for user {telegram_id}")
            else:
                logger.warning(
                    f"Position close failed for user {telegram_id}: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to close position for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_user_order(
        self, telegram_id: int, order_id: str
    ) -> Dict[str, Any]:
        """Cancel order for specific user."""
        try:
            result = await self.order_manager.cancel_order(telegram_id, order_id)

            if result["success"]:
                logger.info(f"Order {order_id} cancelled for user {telegram_id}")
            else:
                logger.warning(
                    f"Order cancellation failed for user {telegram_id}: {result.get('error')}"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to cancel order for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_user_risk_metrics(self, telegram_id: int) -> Dict[str, Any]:
        """Get risk metrics for specific user."""
        try:
            return await self.position_manager.get_user_risk_metrics(telegram_id)
        except Exception as e:
            logger.error(f"Failed to get risk metrics for user {telegram_id}: {e}")
            return {}

    async def emergency_user_stop(self, telegram_id: int) -> Dict[str, Any]:
        """Emergency stop all trading for user."""
        try:
            # Cancel all pending orders
            cancel_result = await self.order_manager.emergency_cancel_all_user_orders(
                telegram_id
            )

            # Close all positions
            close_result = (
                await self.position_manager.emergency_close_all_user_positions(
                    telegram_id
                )
            )

            # Cleanup user session
            await self.ea_bridge.cleanup_user_session(telegram_id)

            return {
                "success": True,
                "cancelled_orders": cancel_result.get("cancelled", 0),
                "closed_positions": close_result.get("closed", 0),
                "message": f"Emergency stop completed for user {telegram_id}",
            }

        except Exception as e:
            logger.error(f"Emergency stop failed for user {telegram_id}: {e}")
            return {"success": False, "error": str(e)}

    async def get_all_users_trading_status(
        self, admin_telegram_id: int
    ) -> Dict[str, Any]:
        """Get trading status for all users (admin only)."""
        try:
            if not await self.user_manager.is_admin(admin_telegram_id):
                return {"error": "Admin access required"}

            # Get all users
            all_users = await self.user_manager.get_all_users(admin_telegram_id)
            if not all_users:
                return {"error": "Failed to get users"}

            users_status = {}
            for user in all_users:
                telegram_id = user["telegram_id"]
                user_status = await self.get_user_trading_status(telegram_id)
                users_status[str(telegram_id)] = user_status

            return {
                "total_users": len(all_users),
                "users_status": users_status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get all users trading status: {e}")
            return {"error": str(e)}

    async def get_enhanced_service_stats(self) -> Dict[str, Any]:
        """Get enhanced service statistics including multi-user components."""
        try:
            base_stats = await self.get_service_stats()

            # Add multi-user component stats
            position_stats = self.position_manager.get_manager_stats()
            order_stats = self.order_manager.get_manager_stats()
            ea_bridge_stats = self.ea_bridge.get_all_user_connections_health()

            return {
                **base_stats,
                "position_manager": position_stats,
                "order_manager": order_stats,
                "ea_bridge": ea_bridge_stats,
                "enhanced_features": {
                    "user_isolation": True,
                    "risk_management": True,
                    "position_tracking": True,
                    "order_routing": True,
                },
            }

        except Exception as e:
            logger.error(f"Failed to get enhanced service stats: {e}")
            return {"error": str(e)}
