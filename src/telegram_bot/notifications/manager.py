"""Notification manager for Telegram bot."""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

from src.core.logging import get_logger
from src.core.config import TelegramConfig
from src.core.exceptions import TelegramBotError
from ..utils.constants import NotificationType, NotificationPriority, NotificationStatus

logger = get_logger(__name__)


@dataclass
class Notification:
    """Notification data structure."""

    id: str
    message: str
    notification_type: str
    priority: NotificationPriority
    chat_ids: List[int]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    max_attempts: int = 3
    status: NotificationStatus = NotificationStatus.PENDING
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class NotificationManager:
    """Manages notifications and alerts for the Telegram bot with enhanced reliability."""

    def __init__(self, config: TelegramConfig):
        """Initialize the notification manager.

        Args:
            config: Telegram bot configuration.
        """
        self.config = config
        self.chat_ids: List[int] = []
        self.notification_preferences: Dict[str, Dict] = {}
        self.notification_queue: List[Notification] = []
        self.failed_notifications: List[Notification] = []
        self.delivery_stats = {"total_sent": 0, "total_failed": 0, "total_retries": 0}
        self.running = False
        self._processing_task = None
        self._retry_task = None

        # Load chat IDs from config
        if self.config.chat_id:
            self.chat_ids.append(self.config.chat_id)

        # Setup default notification preferences
        self._setup_default_preferences()

    def _setup_default_preferences(self):
        """Setup default notification preferences."""
        self.notification_preferences = {
            "signals": {"enabled": True, "priority": "high"},
            "positions": {"enabled": True, "priority": "medium"},
            "risk": {"enabled": True, "priority": "high"},
            "performance": {"enabled": True, "priority": "medium"},
            "system": {"enabled": True, "priority": "low"},
            "errors": {"enabled": True, "priority": "high"},
        }

    async def start(self):
        """Start the notification manager."""
        self.running = True
        logger.info("Enhanced notification manager started")

        # Start notification processing loops
        self._processing_task = asyncio.create_task(self._process_notifications())
        self._retry_task = asyncio.create_task(self._retry_failed_notifications())

    async def stop(self):
        """Stop the notification manager."""
        self.running = False
        logger.info("Enhanced notification manager stopping")

        # Cancel tasks
        if self._processing_task:
            self._processing_task.cancel()
        if self._retry_task:
            self._retry_task.cancel()

        # Process remaining notifications
        await self._flush_queue()
        logger.info("Enhanced notification manager stopped")

    async def add_chat_id(self, chat_id: int):
        """Add a chat ID for notifications.

        Args:
            chat_id: The chat ID to add.
        """
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
            logger.info(f"Added chat ID: {chat_id}")

    async def remove_chat_id(self, chat_id: int):
        """Remove a chat ID from notifications.

        Args:
            chat_id: The chat ID to remove.
        """
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            logger.info(f"Removed chat ID: {chat_id}")

    def _is_notification_enabled(self, notification_type: str) -> bool:
        """Check if a notification type is enabled.

        Args:
            notification_type: The notification type to check.

        Returns:
            bool: True if the notification type is enabled, False otherwise.
        """
        # Map notification type to preference key
        if notification_type in ["signal", "signals"]:
            pref_key = "signals"
        elif notification_type in ["position", "positions"]:
            pref_key = "positions"
        elif notification_type in ["risk"]:
            pref_key = "risk"
        elif notification_type in ["performance"]:
            pref_key = "performance"
        elif notification_type in ["system", "status"]:
            pref_key = "system"
        elif notification_type in ["error", "errors"]:
            pref_key = "errors"
        else:
            # Default to enabled for unknown types
            return True

        # Check if preference exists and is enabled
        return self.notification_preferences.get(pref_key, {}).get("enabled", True)

    async def _process_notifications(self):
        """Process notifications in the queue with enhanced reliability."""
        while self.running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    success = await self._send_notification(notification)

                    if (
                        not success
                        and notification.attempts < notification.max_attempts
                    ):
                        self.failed_notifications.append(notification)
                else:
                    await asyncio.sleep(0.5)  # No notifications to process

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                await asyncio.sleep(5)  # Sleep longer on error

    async def _retry_failed_notifications(self):
        """Retry failed notifications."""
        while self.running:
            try:
                await asyncio.sleep(30)  # Retry every 30 seconds

                if self.failed_notifications:
                    # Process oldest failed notifications first
                    notification = self.failed_notifications.pop(0)

                    # Check if we should still retry (max 1 hour)
                    age_seconds = (
                        datetime.now(timezone.utc) - notification.created_at
                    ).total_seconds()
                    if age_seconds > 3600:
                        logger.warning(
                            f"Dropping expired notification: {notification.id}"
                        )
                        continue

                    notification.status = NotificationStatus.RETRYING
                    self.delivery_stats["total_retries"] += 1

                    success = await self._send_notification(notification)
                    if (
                        not success
                        and notification.attempts < notification.max_attempts
                    ):
                        self.failed_notifications.append(
                            notification
                        )  # Re-queue for retry

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error retrying notifications: {e}")

    async def _flush_queue(self):
        """Process remaining notifications in queue."""
        logger.info(f"Flushing {len(self.notification_queue)} pending notifications")

        for notification in self.notification_queue[:]:
            await self._send_notification(notification)

        self.notification_queue.clear()

    async def send_notification(
        self,
        message: str,
        notification_type: str = "info",
        priority: Optional[NotificationPriority] = None,
        chat_ids: Optional[List[int]] = None,
        **kwargs,
    ):
        """Send a notification with enhanced reliability.

        Args:
            message: The message to send.
            notification_type: The type of notification.
            priority: The priority of the notification (defaults to MEDIUM).
            chat_ids: Specific chat IDs to send to (defaults to all registered).
            **kwargs: Additional arguments to pass to send_message.
        """
        try:
            # Set default priority based on notification type
            if priority is None:
                if notification_type in ["error", "risk"]:
                    priority = NotificationPriority.HIGH
                elif notification_type in ["signal", "position"]:
                    priority = NotificationPriority.MEDIUM
                else:
                    priority = NotificationPriority.LOW

            # Use default chat IDs if none provided
            if chat_ids is None:
                chat_ids = self.chat_ids.copy()

            if not chat_ids:
                logger.warning("No chat IDs configured for notification")
                return False

            # Check if notification type is enabled
            if not self._is_notification_enabled(notification_type):
                logger.debug(f"Notification type {notification_type} is disabled")
                return True

            # Create notification
            notification = Notification(
                id=f"{notification_type}_{int(time.time() * 1000)}",
                message=message,
                notification_type=notification_type,
                priority=priority,
                chat_ids=chat_ids,
                metadata=kwargs,
            )

            # Send immediately if critical, otherwise queue
            if priority == NotificationPriority.CRITICAL:
                return await self._send_notification(notification)
            else:
                self._add_to_queue(notification)
                return True

        except Exception as e:
            logger.error(f"Error queuing notification: {e}")
            return False

    def _add_to_queue(self, notification: Notification):
        """Add notification to queue with priority sorting."""
        # Insert based on priority (higher priority first)
        inserted = False
        for i, queued_notification in enumerate(self.notification_queue):
            if notification.priority.value > queued_notification.priority.value:
                self.notification_queue.insert(i, notification)
                inserted = True
                break

        if not inserted:
            self.notification_queue.append(notification)

        logger.debug(
            f"Queued notification {notification.id} (queue size: {len(self.notification_queue)})"
        )

    async def _send_notification(self, notification: Notification) -> bool:
        """Send individual notification with error handling."""
        notification.attempts += 1

        try:
            start_time = time.time()

            for chat_id in notification.chat_ids:
                try:
                    # Import here to avoid circular imports
                    from ..core.trading_bot import TradingBot

                    bot = TradingBot.get_instance()
                    if bot:
                        await bot.send_message(
                            chat_id, notification.message, **notification.metadata
                        )
                    else:
                        raise TelegramBotError("Bot instance not available")

                except Exception as e:
                    logger.error(f"Failed to send notification to chat {chat_id}: {e}")
                    notification.last_error = str(e)
                    raise TelegramBotError(f"Failed to send to chat {chat_id}: {e}")

            # Record successful delivery
            notification.status = NotificationStatus.SENT
            self.delivery_stats["total_sent"] += 1

            duration_ms = (time.time() - start_time) * 1000
            logger.debug(
                f"Notification sent successfully: {notification.id} ({duration_ms:.1f}ms)"
            )

            return True

        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            self.delivery_stats["total_failed"] += 1

            logger.error(
                f"Failed to send notification {notification.id} (attempt {notification.attempts}): {e}"
            )
            return False

    async def send_startup_notification(self):
        """Send a notification when the bot starts up."""
        message = (
            "🤖 *AI Trading Bot Started*\n\n"
            "The trading bot has been started and is now operational.\n\n"
            "Use /status to check the current system status.\n"
            "Use /help to see available commands."
        )

        await self.send_notification(
            message, notification_type="system", parse_mode="Markdown"
        )

    async def send_signal_notification(self, signal_data: Dict[str, Any]):
        """Send signal notification."""
        try:
            symbol = signal_data.get("symbol", "Unknown")
            bias = signal_data.get("bias", "Unknown")
            confidence = signal_data.get("confidence", 0)

            message = (
                f"📊 *Trading Signal*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Bias: `{bias}`\n"
                f"Confidence: `{confidence}%`\n"
                f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            await self.send_notification(
                message, notification_type="signal", parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")

    async def send_position_notification(
        self, position_data: Dict[str, Any], action: str
    ):
        """Send position notification."""
        try:
            symbol = position_data.get("symbol", "Unknown")
            position_type = position_data.get("type", "Unknown")
            volume = position_data.get("volume", 0)
            profit = position_data.get("profit", 0)

            action_emoji = {
                "opened": "🟢",
                "closed": "🔴",
                "modified": "🔄",
                "snapshot": "📊",
            }.get(action, "📍")

            message = (
                f"{action_emoji} *Position {action.title()}*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Type: `{position_type}`\n"
                f"Volume: `{volume}`\n"
                f"Profit: `${profit:.2f}`\n"
                f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            await self.send_notification(
                message, notification_type="position", parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending position notification: {e}")

    async def send_order_notification(self, order_data: Dict[str, Any]):
        """Send order notification."""
        try:
            symbol = order_data.get("symbol", "Unknown")
            order_type = order_data.get("order_type", "Unknown")
            volume = order_data.get("volume", 0)
            status = order_data.get("status", "Unknown")

            status_emoji = {"EXECUTED": "✅", "FAILED": "❌", "PENDING": "⏳"}.get(
                status, "📋"
            )

            message = (
                f"{status_emoji} *Order {status}*\n\n"
                f"Symbol: `{symbol}`\n"
                f"Type: `{order_type}`\n"
                f"Volume: `{volume}`\n"
                f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            await self.send_notification(
                message, notification_type="order", parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Error sending order notification: {e}")

    async def send_risk_alert(
        self, alert_type: str, message: str, data: Dict[str, Any] = None
    ):
        """Send risk alert notification."""
        try:
            alert_emoji = {
                "drawdown": "🚨",
                "margin": "⚠️",
                "exposure": "📊",
                "loss": "🔻",
            }.get(alert_type, "🚨")

            notification_message = (
                f"{alert_emoji} *Risk Alert: {alert_type.title()}*\n\n"
                f"{message}\n\n"
                f"Time: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            )

            if data:
                notification_message += f"\nDetails: `{data}`"

            await self.send_notification(
                notification_message,
                notification_type="risk",
                priority=NotificationPriority.HIGH,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")

    async def send_critical_alert(
        self, message: str, error: Optional[Exception] = None
    ):
        """Send critical alert notification."""
        try:
            error_detail = f"\nError: {str(error)}" if error else ""
            critical_message = f"🚨 *CRITICAL ALERT*\n\n{message}{error_detail}"

            await self.send_notification(
                critical_message,
                notification_type="critical",
                priority=NotificationPriority.CRITICAL,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error sending critical alert: {e}")

    async def send_trade_notification(
        self, symbol: str, action: str, details: Dict[str, Any]
    ):
        """Send standardized trade notification."""
        try:
            message = self._format_trade_message(symbol, action, details)

            await self.send_notification(
                message,
                notification_type="trade",
                priority=NotificationPriority.HIGH,
                parse_mode="Markdown",
            )
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")

    def _format_trade_message(
        self, symbol: str, action: str, details: Dict[str, Any]
    ) -> str:
        """Format trade message with emojis and formatting."""
        action_emojis = {
            "order_placed": "📝",
            "order_filled": "✅",
            "order_cancelled": "❌",
            "position_opened": "🟢",
            "position_closed": "🔴",
            "position_modified": "🔄",
        }

        emoji = action_emojis.get(action, "📊")

        message = f"{emoji} *{action.replace('_', ' ').title()}*\n\n"
        message += f"Symbol: `{symbol}`\n"

        for key, value in details.items():
            if key in ["volume", "price", "profit", "sl", "tp"]:
                message += f"{key.replace('_', ' ').title()}: `{value}`\n"

        message += f"\nTime: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"

        return message

    def get_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics."""
        return {
            "delivery_stats": self.delivery_stats,
            "queue_size": len(self.notification_queue),
            "failed_count": len(self.failed_notifications),
            "chat_ids_count": len(self.chat_ids),
            "is_running": self.running,
            "enabled_types": [
                ntype
                for ntype, prefs in self.notification_preferences.items()
                if prefs["enabled"]
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def update_preferences(
        self, notification_type: str, enabled: bool, priority: str = "medium"
    ):
        """Update notification preferences."""
        if notification_type in self.notification_preferences:
            self.notification_preferences[notification_type]["enabled"] = enabled
            self.notification_preferences[notification_type]["priority"] = priority
            logger.info(
                f"Updated preferences for {notification_type}: enabled={enabled}, priority={priority}"
            )
        else:
            self.notification_preferences[notification_type] = {
                "enabled": enabled,
                "priority": priority,
            }
            logger.info(
                f"Added preferences for {notification_type}: enabled={enabled}, priority={priority}"
            )
