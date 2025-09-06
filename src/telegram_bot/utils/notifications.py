"""Utility functions for easy access to notification features."""

from typing import Dict, Any, Optional
from ..notifications.manager import NotificationManager
from ..utils.constants import NotificationPriority


# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None


def set_notification_manager(manager: NotificationManager):
    """Set the global notification manager instance."""
    global _notification_manager
    _notification_manager = manager


def get_notification_manager() -> Optional[NotificationManager]:
    """Get the global notification manager instance."""
    return _notification_manager


async def send_critical_alert(message: str, error: Optional[Exception] = None):
    """Send critical alert notification."""
    if _notification_manager:
        await _notification_manager.send_critical_alert(message, error)


async def send_trade_notification(symbol: str, action: str, details: Dict[str, Any]):
    """Send standardized trade notification."""
    if _notification_manager:
        await _notification_manager.send_trade_notification(symbol, action, details)


async def send_quick_notification(
    message: str,
    notification_type: str = "info",
    priority: NotificationPriority = NotificationPriority.MEDIUM,
):
    """Send a quick notification with minimal setup."""
    if _notification_manager:
        await _notification_manager.send_notification(
            message,
            notification_type=notification_type,
            priority=priority,
            parse_mode="Markdown",
        )


async def send_system_alert(message: str):
    """Send system alert notification."""
    await send_quick_notification(
        f"🔧 *System Alert*\n\n{message}",
        notification_type="system",
        priority=NotificationPriority.HIGH,
    )


async def send_error_alert(message: str, error: Optional[Exception] = None):
    """Send error alert notification."""
    error_detail = f"\nError: {str(error)}" if error else ""
    await send_quick_notification(
        f"❌ *Error Alert*\n\n{message}{error_detail}",
        notification_type="error",
        priority=NotificationPriority.HIGH,
    )


def get_notification_stats() -> Dict[str, Any]:
    """Get notification statistics."""
    if _notification_manager:
        return _notification_manager.get_stats()
    return {}
