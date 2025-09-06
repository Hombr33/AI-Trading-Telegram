"""Message handler for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler as TelegramMessageHandler
from telegram.ext import filters

from src.core.logging import get_logger
from src.telegram_bot.notifications.manager import NotificationManager

logger = get_logger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages from users (reply keyboard buttons)."""
    try:
        message_text = update.message.text
        logger.info(f"Message received: {message_text}")

        # Import command handlers
        from ..commands.handler import CommandHandler

        command_handler = CommandHandler()

        # Map reply keyboard buttons to commands
        button_map = {
            "📊 Status": command_handler.system_handler.status_command,
            "💰 Account": command_handler.trading_handler.account_command,
            "📈 Positions": command_handler.trading_handler.positions_command,
            "📋 Orders": command_handler.trading_handler.orders_command,
            "🎯 Signals": command_handler.trading_handler.signals_command,
            "⚠️ Risk": command_handler.analysis_handler.risk_command,
            "📊 Performance": command_handler.analysis_handler.performance_command,
            "🖥️ Monitor": command_handler.system_handler.monitor_command,
            "⚙️ Settings": command_handler.system_handler.settings_command,
            "❓ Help": command_handler.system_handler.help_command,
            "📈 Open Positions": command_handler.trading_handler.positions_command,
            "📋 Pending Orders": command_handler.trading_handler.orders_command,
            "💰 Account Info": command_handler.trading_handler.account_command,
            "🎯 Trading Signals": command_handler.trading_handler.signals_command,
            "📊 Performance Stats": command_handler.analysis_handler.performance_command,
            "⚠️ Risk Metrics": command_handler.analysis_handler.risk_command,
            "📝 Trading Journal": command_handler.analysis_handler.journal_command,
            "📊 System Status": command_handler.system_handler.status_command,
            "🖥️ Resource Monitor": command_handler.system_handler.monitor_command,
            "⚙️ Bot Settings": command_handler.system_handler.settings_command,
            "🔙 Main Menu": command_handler.system_handler.start_command,
        }

        # Execute mapped command if button press detected
        if message_text in button_map:
            await button_map[message_text](update, context)
        else:
            # Handle as regular message
            await update.message.reply_text(
                "💬 **Message Received!**\n\n"
                f"You said: *{message_text}*\n\n"
                "🎮 Use the keyboard buttons below for quick actions,\n"
                "or type /help to see all commands!",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error handling message: {e}")


def setup_message_handler(notification_manager: NotificationManager):
    """Setup message handler for the Telegram bot."""
    return handle_message
