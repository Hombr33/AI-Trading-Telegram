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
        await query.answer()
        
        data = query.data
        logger.info(f"Callback query received: {data}")
        
        if data == "refresh_status":
            await query.edit_message_text("🔄 Status refreshed")
        else:
            await query.edit_message_text(f"Command received: {data}")
            
    except Exception as e:
        logger.error(f"Error handling callback query: {e}")


def setup_callback_handler(notification_manager: NotificationManager):
    """Setup callback handler for the Telegram bot."""
    return handle_callback_query