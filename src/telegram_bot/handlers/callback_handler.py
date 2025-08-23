"""Callback handler for Telegram bot."""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.notifications.manager import NotificationManager

logger = get_logger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback queries from inline keyboards."""
    try:
        query = update.callback_query
        await query.answer("⚡ Processing...")
        
        data = query.data
        logger.info(f"Callback query received: {data}")
        
        # Import command handlers
        from ..commands.handler import CommandHandler
        command_handler = CommandHandler()
        
        # Handle special live dashboard
        if data == "live_dashboard":
            from ..utils.animations import LiveDashboard
            dashboard = LiveDashboard()
            await dashboard.start_live_dashboard(update, context)
            return
        
        # Handle other callbacks through command handler
        await command_handler.handle_callback(update, context)
            
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