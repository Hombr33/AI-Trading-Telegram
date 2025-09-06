"""Trading bot implementation for Telegram."""

from typing import Optional

from telegram.ext import CallbackQueryHandler
from telegram.ext import CommandHandler as TGCommandHandler
from telegram.ext import MessageHandler, filters

from src.core.config import TelegramConfig
from src.core.logging import get_logger

from ..notifications.manager import NotificationManager
from .bot import BaseTelegramBot

logger = get_logger(__name__)


class TradingBot(BaseTelegramBot):
    """Trading bot implementation for Telegram."""

    _instance: Optional["TradingBot"] = None
    _initialized: bool = False

    def __init__(self, config: TelegramConfig):
        """Initialize the trading bot.

        Args:
            config: Telegram bot configuration.
        """
        super().__init__(config)
        self.notification_manager: Optional[NotificationManager] = None
        self.command_handlers = {}
        self.callback_handlers = {}

        # Set as singleton instance
        TradingBot._instance = self

    @classmethod
    def get_instance(cls) -> Optional["TradingBot"]:
        """Get the singleton instance of TradingBot.

        Returns:
            The TradingBot instance if it exists, None otherwise.
        """
        return cls._instance

    @classmethod
    def create_instance(cls, config: TelegramConfig) -> "TradingBot":
        """Create or get the singleton instance of TradingBot.

        Args:
            config: Telegram bot configuration.

        Returns:
            The TradingBot instance.
        """
        if cls._instance is None:
            cls._instance = cls(config)
        return cls._instance

    async def setup(self):
        """Set up the trading bot."""
        # Initialize the base application
        if not await self.initialize():
            return False

        # Setup notification manager
        self.notification_manager = NotificationManager(self.config)

        # Import handlers here to avoid circular imports
        from ..handlers.callback_handler import setup_callback_handler
        from ..handlers.command_handler import setup_command_handlers
        from ..handlers.error_handler import setup_error_handler
        from ..handlers.message_handler import setup_message_handler

        # Register command handlers
        command_handlers = setup_command_handlers(self.notification_manager)
        for command, handler in command_handlers.items():
            self.application.add_handler(TGCommandHandler(command, handler))
            self.command_handlers[command] = handler

        # Register callback query handler
        callback_handler = setup_callback_handler(self.notification_manager)
        self.application.add_handler(CallbackQueryHandler(callback_handler))

        # Register message handler
        message_handler = setup_message_handler(self.notification_manager)

        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        # Register error handler
        error_handler = setup_error_handler()
        self.application.add_error_handler(error_handler)

        logger.info("Trading bot setup completed")
        return True

    async def start(self):
        """Start the trading bot."""
        result = await super().start()
        if result and self.notification_manager:
            # Send startup notification
            await self.notification_manager.send_startup_notification()
        return result

    async def send_notification(self, message: str, notification_type: str = "info"):
        """Send a notification to all users.

        Args:
            message: The message to send.
            notification_type: The type of notification.

        Returns:
            bool: True if the notification was sent successfully, False otherwise.
        """
        try:
            if not self.notification_manager:
                logger.error("Notification manager not initialized")
                return False

            await self.notification_manager.send_notification(
                message, notification_type
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
