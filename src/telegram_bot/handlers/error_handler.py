"""Error handler for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger

logger = get_logger(__name__)


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors from the Telegram bot."""
    try:
        logger.error(f"Telegram bot error: {context.error}")

        if update and hasattr(update, "effective_chat"):
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🚨 An error occurred. Please try again.",
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    except Exception as e:
        logger.error(f"Error in error handler: {e}")


def setup_error_handler():
    """Setup error handler for the Telegram bot."""
    return handle_error
