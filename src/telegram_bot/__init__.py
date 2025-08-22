"""
Telegram module for bot integration and user communication.
"""

# Import from new modular structure
from .main import TelegramBot
from .notifications.manager import NotificationManager
from .commands.handler import CommandHandler

__all__ = ["TelegramBot", "NotificationManager", "CommandHandler"]
