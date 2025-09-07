"""
Telegram module for bot integration and user communication.
"""

from .commands.handler import CommandHandler

# Import from new modular structure
from .main import TelegramBot
from .notifications.manager import NotificationManager

__all__ = ["TelegramBot", "NotificationManager", "CommandHandler"]
