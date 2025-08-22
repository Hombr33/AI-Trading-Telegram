"""Callback handler for Telegram bot."""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.commands.handler import CommandHandler

logger = get_logger(__name__)


class CallbackHandler:
    """Callback handler for Telegram bot."""

    def __init__(self, command_handler: CommandHandler):
        """Initialize callback handler.
        
        Args:
            command_handler: The command handler to use.
        """
        self.command_handler = command_handler

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries.
        
        Args:
            update: The update object.
            context: The context object.
        """
        await self.command_handler.handle_callback(update, context)

    def get_handler(self) -> CallbackQueryHandler:
        """Get the callback query handler.
        
        Returns:
            The callback query handler.
        """
        return CallbackQueryHandler(self.handle_callback)