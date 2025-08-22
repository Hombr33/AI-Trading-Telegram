"""Message handler for Telegram bot."""

from telegram import Update
from telegram.ext import MessageHandler as TelegramMessageHandler, ContextTypes, filters

from src.core.logging import get_logger
from src.telegram_bot.notifications.manager import NotificationManager

logger = get_logger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users."""
    try:
        message_text = update.message.text
        logger.info(f"Message received: {message_text}")
        
        await update.message.reply_text(
            "I received your message. Use /help to see available commands."
        )
        
    except Exception as e:
        logger.error(f"Error handling message: {e}")


def setup_message_handler(notification_manager: NotificationManager):
    """Setup message handler for the Telegram bot."""
    return handle_message