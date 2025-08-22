"""Notification manager for Telegram bot."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from src.core.logging import get_logger
from src.core.config import TelegramConfig
from ..utils.constants import NotificationType

logger = get_logger(__name__)


class NotificationManager:
    """Manages notifications and alerts for the Telegram bot."""

    def __init__(self, config: TelegramConfig):
        """Initialize the notification manager.
        
        Args:
            config: Telegram bot configuration.
        """
        self.config = config
        self.chat_ids: List[int] = []
        self.notification_preferences: Dict[str, Dict] = {}
        self.notification_queue: List[Dict] = []
        self.running = False

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
        logger.info("Notification manager started")

        # Start notification processing loop
        asyncio.create_task(self._process_notifications())

    async def stop(self):
        """Stop the notification manager."""
        self.running = False
        logger.info("Notification manager stopped")

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
        """Process notifications in the queue."""
        while self.running:
            try:
                # Process all notifications in the queue
                while self.notification_queue and self.running:
                    notification = self.notification_queue.pop(0)
                    await self._send_notification_to_all_chats(notification)

                # Sleep to avoid high CPU usage
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                await asyncio.sleep(5)  # Sleep longer on error

    async def _send_notification_to_all_chats(self, notification: Dict):
        """Send a notification to all registered chat IDs.
        
        Args:
            notification: The notification to send.
        """
        message = notification["message"]
        kwargs = notification.get("kwargs", {})

        for chat_id in self.chat_ids:
            try:
                # Import here to avoid circular imports
                from ..core.trading_bot import TradingBot
                bot = TradingBot.get_instance()
                if bot:
                    await bot.send_message(chat_id, message, **kwargs)
                else:
                    logger.error("Bot instance not available for sending notification")
            except Exception as e:
                logger.error(f"Error sending notification to chat {chat_id}: {e}")

    async def send_notification(
        self,
        message: str,
        notification_type: str = "info",
        priority: str = "medium",
        **kwargs,
    ):
        """Send a notification to all registered chat IDs.
        
        Args:
            message: The message to send.
            notification_type: The type of notification.
            priority: The priority of the notification.
            **kwargs: Additional arguments to pass to send_message.
        """
        try:
            notification = {
                "message": message,
                "type": notification_type,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc),
                "kwargs": kwargs,
            }

            # Check if notification type is enabled
            if not self._is_notification_enabled(notification_type):
                logger.debug(f"Notification type {notification_type} is disabled")
                return

            # Add to queue for processing
            self.notification_queue.append(notification)
            logger.debug(f"Notification queued: {notification_type} - {priority}")

        except Exception as e:
            logger.error(f"Error queuing notification: {e}")

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