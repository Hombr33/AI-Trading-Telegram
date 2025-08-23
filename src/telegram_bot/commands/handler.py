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

    def __init__(self, notification_manager=None):
        """Initialize command handler."""
        self.notification_manager = notification_manager
        self.system_handler = SystemCommandHandler()
        self.trading_handler = TradingCommandHandler()
        self.analysis_handler = AnalysisCommandHandler()
        self.auto_trading_handler = AutoTradingCommandHandler()
        
        # Initialize callback router
        from ..handlers.callback_handler import CallbackRouter
        self.callback_router = CallbackRouter()
        
        # Combine commands from all handlers
        self.commands = {}
        self.commands.update(self.system_handler.commands)
        self.commands.update(self.trading_handler.commands)
        self.commands.update(self.analysis_handler.commands)
        self.commands.update(self.auto_trading_handler.commands)

    def get_command_handlers(self) -> Dict[str, Callable]:
        """Get command handlers."""
        return self.commands

    # Direct command methods expected by bot.py
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await self.system_handler.start_command(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command.""" 
        await self.system_handler.help_command(update, context)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        await self.system_handler.status_command(update, context)

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /positions command."""
        await self.trading_handler.positions_command(update, context)

    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        await self.trading_handler.signals_command(update, context)

    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command."""
        await self.trading_handler.orders_command(update, context)

    async def performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /performance command."""
        await self.analysis_handler.performance_command(update, context)

    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command."""
        await self.analysis_handler.risk_command(update, context)

    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /settings command."""
        await self.system_handler.settings_command(update, context)

    async def journal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /journal command."""
        await self.analysis_handler.journal_command(update, context)

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        await self.callback_router.route_callback(update, context)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors."""
        await self.system_handler.error_handler(update, context)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages."""
        # Forward to message handler
        from ..handlers.message_handler import handle_message
        await handle_message(update, context)
