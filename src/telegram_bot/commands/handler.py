"""Command handler for Telegram bot."""

from typing import Dict, Any, Callable

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from .system import SystemCommandHandler
from .trading import TradingCommandHandler
from .analysis import AnalysisCommandHandler
from .auto_trading import AutoTradingCommandHandler

logger = get_logger(__name__)


class CommandHandler:
    """Command handler for Telegram bot."""

    def __init__(self):
        """Initialize command handler."""
        self.system_handler = SystemCommandHandler()
        self.trading_handler = TradingCommandHandler()
        self.analysis_handler = AnalysisCommandHandler()
        self.auto_trading_handler = AutoTradingCommandHandler()
        
        # Combine commands from all handlers
        self.commands = {}
        self.commands.update(self.system_handler.commands)
        self.commands.update(self.trading_handler.commands)
        self.commands.update(self.analysis_handler.commands)
        self.commands.update(self.auto_trading_handler.commands)
        
        # Setup mock data
        self._setup_mock_data()

    def _setup_mock_data(self):
        """Setup mock data for testing."""
        # This is a placeholder for setting up mock data
        # The actual mock data is now handled in the utils/mock_data.py module
        pass

    def get_command_handlers(self) -> Dict[str, Callable]:
        """Get command handlers.
        
        Returns:
            Dict mapping command names to handler functions.
        """
        return self.commands

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries.
        
        Args:
            update: The update object.
            context: The context object.
        """
        query = update.callback_query
        callback_data = query.data

        # Determine which handler should handle the callback
        if callback_data in self.system_handler.callbacks:
            await self.system_handler.handle_callback(update, context)
        elif callback_data in self.trading_handler.callbacks:
            await self.trading_handler.handle_callback(update, context)
        elif callback_data in self.analysis_handler.callbacks:
            await self.analysis_handler.handle_callback(update, context)
        elif callback_data in self.auto_trading_handler.callbacks:
            await self.auto_trading_handler.handle_callback(update, context)
        else:
            logger.warning(f"Unknown callback data: {callback_data}")
            await self.system_handler.answer_callback_query(update, context)
            await self.system_handler.edit_message(
                update, context, 
                f"Unknown callback: {callback_data}\n\nPlease try again or use /help to see available commands."
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors.
        
        Args:
            update: The update object.
            context: The context object.
        """
        await self.system_handler.error_handler(update, context)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # This is a placeholder for message handling
        # For now, just forward to the system handler
        await self.system_handler.message_handler(update, context)