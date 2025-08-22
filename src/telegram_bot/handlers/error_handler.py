"""Error handler for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.commands.handler import CommandHandler

logger = get_logger(__name__)


class ErrorHandler:
    """Error handler for Telegram bot."""

    def __init__(self, command_handler: CommandHandler):
        """Initialize error handler.
        
        Args:
            command_handler: The command handler to use.
        """
        self.command_handler = command_handler

    async def handle_error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors.
        
        Args:
            update: The update object.
            context: The context object.
        """
        await self.command_handler.error_handler(update, context)