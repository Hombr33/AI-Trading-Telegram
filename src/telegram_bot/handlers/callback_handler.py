"""Callback handler for Telegram bot."""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.notifications.manager import NotificationManager

logger = get_logger(__name__)


class CallbackRouter:
    """Routes callbacks to appropriate handlers."""
    
    def __init__(self):
        """Initialize callback router."""
        self.handlers = {}
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup callback handlers."""
        # Import handlers
        from .system_callbacks import SystemCallbackHandler
        from .trading_callbacks import TradingCallbackHandler
        from ..commands.system import SystemCommandHandler
        from ..commands.trading import TradingCommandHandler
        
        # Initialize command handlers
        system_handler = SystemCommandHandler()
        trading_handler = TradingCommandHandler()
        
        # Initialize callback handlers
        self.system_callbacks = SystemCallbackHandler(system_handler)
        self.trading_callbacks = TradingCallbackHandler(trading_handler)
        
        # Initialize admin callback handler
        from .admin_commands import AdminCommandHandlers
        self.admin_callbacks = AdminCommandHandlers()
        
        # Define callback routing
        self.system_callback_keys = {
            "start", "help", "status", "settings", "about", 
            "docs", "support", "rate", "updates", "quick_actions",
            "risk_settings", "notification_settings", 
            "theme_settings", "sound_settings", "trading_guide",
            "risk_guide", "ta_guide", "setup_guide", "email_support",
            "live_chat", "faq", "rate_5", "rate_4", "leave_review",
            "feedback", "changelog", "update_alerts", "roadmap",
            "monitor", "system_monitor", "health_monitor"
        }
        
        # Admin callback keys
        self.admin_callback_keys = {
            "users", "add_admin", "remove_admin", "set_subscription",
            "server_config", "restart", "logs", "close_all",
            "logs_system", "logs_trading", "logs_error", "logs_refresh",
            "server_config_edit", "server_config_add", "server_config_refresh",
            "confirm_restart", "cancel_restart", "confirm_close_all", "cancel_close_all"
        }
        
        self.trading_callback_keys = {
            "positions", "refresh_positions", "position_details", "quick_close",
            "orders", "refresh_orders", "account", "refresh_account", 
            "account_history", "export_history", "symbols", "refresh_symbols",
            "signals", "refresh_signals", "live_dashboard", "webapp",
            "webapp_open", "webapp_mobile", "webapp_desktop", "add_symbol", 
            "delete_symbol"
        }
    
    async def route_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Route callback to appropriate handler."""
        query = update.callback_query
        callback_data = query.data
        
        try:
            # Handle signal callbacks with pattern matching
            if callback_data.startswith("signal_"):
                await self.trading_callbacks.handle_callback(update, context)
            elif callback_data in self.system_callback_keys:
                await self.system_callbacks.handle_callback(update, context)
            elif callback_data in self.trading_callback_keys:
                await self.trading_callbacks.handle_callback(update, context)
            elif callback_data in self.admin_callback_keys:
                await self.admin_callbacks.handle_admin_callback(update, context)
            else:
                logger.warning(f"Unknown callback data: {callback_data}")
                await query.answer("Unknown callback")
                await query.edit_message_text(
                    f"❌ **Unknown Command**\n\n"
                    f"Callback '{callback_data}' not recognized.\n"
                    f"Use /help to see available commands.",
                    parse_mode="Markdown"
                )
                
        except Exception as e:
            logger.error(f"Error routing callback {callback_data}: {e}")
            await query.answer("Error processing request")
            try:
                await query.edit_message_text(
                    f"❌ Error Processing Request\n\n"
                    f"Something went wrong. Please try again or use /help.",
                    parse_mode=None  # Remove markdown to avoid parsing errors
                )
            except:
                pass


# Global callback router instance
callback_router = CallbackRouter()


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    try:
        query = update.callback_query
        await query.answer("⚡ Processing...")
        
        data = query.data
        logger.info(f"Callback query received: {data}")
        
        # Create fresh router instance to ensure latest configuration
        router = CallbackRouter()
        
        # Route callback to appropriate handler
        await router.route_callback(update, context)
            
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")
        try:
            await query.edit_message_text(
                f"❌ **Error Processing Request**\n\n"
                f"Something went wrong. Please try again or use /help.",
                parse_mode="Markdown"
            )
        except:
            pass


def setup_callback_handler(notification_manager: NotificationManager):
    """Setup callback handler for the Telegram bot."""
    return handle_callback_query
