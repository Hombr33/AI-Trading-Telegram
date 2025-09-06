"""Command handler for Telegram bot."""

from typing import Callable, Dict

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.services.symbol_service import SymbolService

from ..handlers.admin_commands import AdminCommandHandlers
from ..handlers.multi_user_handlers import MultiUserHandlers
from .analysis import AnalysisCommandHandler
from .auto_trading import AutoTradingCommandHandler
from .symbol import SymbolCommandHandler
from .system import SystemCommandHandler
from .trading import TradingCommandHandler

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
        self.admin_handler = AdminCommandHandlers()
        self.multi_user_handler = MultiUserHandlers()

        # Initialize symbol handler with service
        from src.database.session import SessionLocal

        SymbolService(SessionLocal())
        self.symbol_handler = SymbolCommandHandler()

        # Initialize callback router
        from ..handlers.callback_handler import CallbackRouter

        self.callback_router = CallbackRouter()

        # Combine commands from all handlers
        self.commands = {}
        self.commands.update(self.system_handler.commands)
        self.commands.update(self.trading_handler.commands)
        self.commands.update(self.analysis_handler.commands)
        self.commands.update(self.auto_trading_handler.commands)
        self.commands.update(self.symbol_handler.commands)

        # Add admin commands
        admin_commands = {
            "admin": self.admin_menu_command,
            "users": self.admin_handler.users_command,
            "add_admin": self.admin_handler.add_admin_command,
            "remove_admin": self.admin_handler.remove_admin_command,
            "set_subscription": self.admin_handler.set_subscription_command,
            "server_config": self.admin_handler.server_config_command,
            "restart": self.admin_handler.restart_command,
            "logs": self.admin_handler.logs_command,
            "close_all": self.admin_handler.close_all_command,
        }

        # Add multi-user commands
        multi_user_commands = {
            "search_users": self.multi_user_handler.search_users_command,
            "bulk_ops": self.multi_user_handler.bulk_operations_command,
            "isolate_user": self.multi_user_handler.user_isolation_command,
            "user_details": self.multi_user_handler.user_details_command,
            "system_monitor": self.multi_user_handler.system_monitor_command,
        }

        self.commands.update(admin_commands)
        self.commands.update(multi_user_commands)

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

    async def positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /positions command."""
        await self.trading_handler.positions_command(update, context)

    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command."""
        await self.trading_handler.signals_command(update, context)

    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command."""
        await self.trading_handler.orders_command(update, context)

    async def performance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /performance command."""
        await self.analysis_handler.performance_command(update, context)

    async def risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command."""
        await self.analysis_handler.risk_command(update, context)

    async def settings_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
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

    async def admin_menu_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /admin command - show admin menu."""
        from ..handlers.user_commands import UserCommandHandlers

        user_handler = UserCommandHandlers()

        # Check if user is admin
        telegram_id = update.effective_user.id
        if not await user_handler.user_manager.is_admin(telegram_id):
            await update.message.reply_text("❌ Admin privileges required.")
            return

        admin_menu = (
            "👑 **ADMIN CONTROL PANEL** 👑\n\n"
            "**User Management:**\n"
            "👥 `/users` - View all registered users\n"
            "👑 `/add_admin` - Add new administrator\n"
            "👤 `/remove_admin` - Remove administrator\n"
            "💎 `/set_subscription` - Manage user subscriptions\n\n"
            "**System Management:**\n"
            "⚙️ `/server_config` - Server configuration\n"
            "🔄 `/restart` - Restart system\n"
            "📋 `/logs` - View system logs\n"
            "🚨 `/close_all` - Emergency close all positions\n\n"
            "**Quick Actions:**\n"
            "📊 `/status` - System status\n"
            "🖥️ `/monitor` - Resource monitoring\n"
            "⚙️ `/settings` - Bot settings"
        )

        from ..utils.keyboards import create_keyboard

        keyboard = create_keyboard(
            [
                [("👥 Users", "users"), ("👑 Add Admin", "add_admin")],
                [
                    ("💎 Subscriptions", "set_subscription"),
                    ("⚙️ Config", "server_config"),
                ],
                [("📋 Logs", "logs"), ("🔄 Restart", "restart")],
                [("📊 Status", "status"), ("🖥️ Monitor", "monitor")],
            ]
        )

        await update.message.reply_text(
            admin_menu, reply_markup=keyboard, parse_mode="Markdown"
        )

    # Additional user command methods
    async def my_id_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myid command."""
        from ..handlers.user_commands import UserCommandHandlers

        user_handler = UserCommandHandlers()
        await user_handler.my_id_command(update, context)

    async def subscription_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /subscription command."""
        from ..handlers.user_commands import UserCommandHandlers

        user_handler = UserCommandHandlers()
        await user_handler.subscription_command(update, context)

    async def connections_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /connections command."""
        from ..handlers.user_commands import UserCommandHandlers

        user_handler = UserCommandHandlers()
        await user_handler.connections_command(update, context)

    async def symbols_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /symbols command."""
        from ..handlers.user_commands import UserCommandHandlers

        user_handler = UserCommandHandlers()
        await user_handler.symbols_command(update, context)

    # Multi-user command methods
    async def search_users_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /search_users command."""
        await self.multi_user_handler.search_users_command(update, context)

    async def bulk_operations_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /bulk_ops command."""
        await self.multi_user_handler.bulk_operations_command(update, context)

    async def user_details_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /user_details command."""
        await self.multi_user_handler.user_details_command(update, context)

    async def system_monitor_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /system_monitor command."""
        await self.multi_user_handler.system_monitor_command(update, context)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages."""
        # Forward to message handler
        from ..handlers.message_handler import handle_message

        await handle_message(update, context)
