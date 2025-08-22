"""System notifications for Telegram bot."""

from typing import Dict, Any
from datetime import datetime, timezone

from src.core.logging import get_logger
from .manager import NotificationManager

logger = get_logger(__name__)


class SystemNotifications:
    """System notifications for Telegram bot."""

    def __init__(self, notification_manager: NotificationManager):
        """Initialize system notifications.
        
        Args:
            notification_manager: The notification manager to use.
        """
        self.notification_manager = notification_manager

    async def send_startup_notification(self, system_info: Dict[str, Any] = None):
        """Send startup notification.
        
        Args:
            system_info: System information to include in the notification.
        """
        try:
            message = (
                f"🚀 **SYSTEM STARTED** 🚀\n\n"
                f"The AI Trading Bot has been started successfully.\n\n"
            )

            if system_info:
                message += "**System Information**:\n"
                for key, value in system_info.items():
                    message += f"📊 **{key.title()}**: {value}\n"
                message += "\n"

            message += (
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Use /help to see available commands\n"
                f"Use /status to check system status"
            )

            await self.notification_manager.send_notification(
                message, notification_type="info", priority="medium", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")

    async def send_shutdown_notification(self, reason: str = None):
        """Send shutdown notification.
        
        Args:
            reason: The reason for shutdown.
        """
        try:
            message = (
                f"🛑 **SYSTEM SHUTDOWN** 🛑\n\n"
                f"The AI Trading Bot is shutting down.\n\n"
            )

            if reason:
                message += f"📝 **Reason**: {reason}\n\n"

            message += f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            await self.notification_manager.send_notification(
                message, notification_type="info", priority="high", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending shutdown notification: {e}")

    async def send_error_notification(self, error_message: str, error_type: str = None, details: Dict[str, Any] = None):
        """Send error notification.
        
        Args:
            error_message: The error message.
            error_type: The type of error.
            details: Additional details about the error.
        """
        try:
            message = (
                f"❌ **SYSTEM ERROR** ❌\n\n"
            )

            if error_type:
                message += f"📝 **Type**: {error_type}\n"

            message += f"📝 **Error**: {error_message}\n\n"

            if details:
                message += "**Details**:\n"
                for key, value in details.items():
                    message += f"📊 **{key.title()}**: {value}\n"
                message += "\n"

            message += f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            await self.notification_manager.send_notification(
                message, notification_type="error", priority="high", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")

    async def send_warning_notification(self, warning_message: str, warning_type: str = None, details: Dict[str, Any] = None):
        """Send warning notification.
        
        Args:
            warning_message: The warning message.
            warning_type: The type of warning.
            details: Additional details about the warning.
        """
        try:
            message = (
                f"⚠️ **SYSTEM WARNING** ⚠️\n\n"
            )

            if warning_type:
                message += f"📝 **Type**: {warning_type}\n"

            message += f"📝 **Warning**: {warning_message}\n\n"

            if details:
                message += "**Details**:\n"
                for key, value in details.items():
                    message += f"📊 **{key.title()}**: {value}\n"
                message += "\n"

            message += f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            await self.notification_manager.send_notification(
                message, notification_type="warning", priority="medium", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending warning notification: {e}")

    async def send_info_notification(self, info_message: str, info_type: str = None, details: Dict[str, Any] = None):
        """Send info notification.
        
        Args:
            info_message: The info message.
            info_type: The type of info.
            details: Additional details about the info.
        """
        try:
            message = (
                f"ℹ️ **SYSTEM INFO** ℹ️\n\n"
            )

            if info_type:
                message += f"📝 **Type**: {info_type}\n"

            message += f"📝 **Info**: {info_message}\n\n"

            if details:
                message += "**Details**:\n"
                for key, value in details.items():
                    message += f"📊 **{key.title()}**: {value}\n"
                message += "\n"

            message += f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            await self.notification_manager.send_notification(
                message, notification_type="info", priority="low", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending info notification: {e}")