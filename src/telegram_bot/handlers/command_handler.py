"""Command handler for Telegram bot."""

from typing import Dict, Any, List, Callable

from telegram import Update
from telegram.ext import CommandHandler as TelegramCommandHandler, ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.notifications.manager import NotificationManager

logger = get_logger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text(
        "🤖 Welcome to AI Trading Bot!\n\n"
        "Use /help to see available commands."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_text = (
        "🤖 *AI Trading Bot Commands*\n\n"
        "📊 *Trading*\n"
        "/positions - View open positions\n"
        "/orders - View pending orders\n"
        "/performance - Trading performance\n"
        "/risk - Risk metrics\n\n"
        "⚙️ *System*\n"
        "/status - System status\n"
        "/settings - Bot settings\n"
        "/help - This help message"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    status_text = (
        "📊 *System Status*\n\n"
        "🟢 Bot: Running\n"
        "🟢 MT5: Connected\n"
        "🟢 Bridge: Active\n"
        "🟢 Notifications: Enabled"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")


def setup_command_handlers(notification_manager: NotificationManager) -> Dict[str, Callable]:
    """Setup command handlers for the Telegram bot."""
    return {
        "start": start_command,
        "help": help_command,
        "status": status_command,
    }