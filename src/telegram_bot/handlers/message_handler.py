"""Message handler for Telegram bot."""

from telegram import Update
from telegram.ext import MessageHandler as TelegramMessageHandler, ContextTypes, filters

from src.core.logging import get_logger
from src.telegram_bot.commands.handler import CommandHandler

logger = get_logger(__name__)


class MessageHandler:
    """Message handler for Telegram bot."""

    def __init__(self, command_handler: CommandHandler):
        """Initialize message handler.
        
        Args:
            command_handler: The command handler to use.
        """
        self.command_handler = command_handler

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages.
        
        Args:
            update: The update object.
            context: The context object.
        """
        await self.command_handler.message_handler(update, context)

    def get_handler(self) -> TelegramMessageHandler:
        """Get the message handler.
        
        Returns:
            The message handler.
        """
        return TelegramMessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)