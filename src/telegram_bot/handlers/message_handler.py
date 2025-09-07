"""Message handler for Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes

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
            "🖥️ Monitor": command_handler.system_handler.status_command,
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
            "🖥️ Resource Monitor": command_handler.system_handler.status_command,
            "⚙️ Bot Settings": command_handler.system_handler.settings_command,
            "🔙 Main Menu": command_handler.system_handler.start_command,
        }

        # Check if user is waiting for custom symbol input
        if context.user_data.get("waiting_for_custom_symbol", False):
            await handle_custom_symbol_input(update, context)
            return

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


async def handle_custom_symbol_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle custom symbol input from user."""
    try:
        symbol = update.message.text.strip().upper()
        telegram_id = update.effective_user.id

        # Validate symbol format
        if not is_valid_symbol(symbol):
            await update.message.reply_text(
                "❌ **Invalid Symbol Format**\n\n"
                "Please use uppercase letters only, no spaces or special characters.\n\n"
                "Examples: `EURUSD`, `BTCUSDT`, `XAUUSD`\n\n"
                "Try again:",
                parse_mode="Markdown",
            )
            return

        # Import user command handlers to add the symbol
        from .user_commands import UserCommandHandlers

        user_handlers = UserCommandHandlers()

        # Add the custom symbol to user's trading pairs
        success = await user_handlers._add_custom_symbol(telegram_id, symbol)

        if success:
            # Clear the waiting state
            context.user_data["waiting_for_custom_symbol"] = False

            await update.message.reply_text(
                f"✅ **Symbol Added Successfully!**\n\n"
                f"`{symbol}` has been added to your trading pairs.\n\n"
                "You can now receive signals for this symbol.\n\n"
                "Use /settings → Trading to manage your pairs.",
                parse_mode="Markdown",
            )
        else:
            await update.message.reply_text(
                f"❌ **Failed to Add Symbol**\n\n"
                f"Could not add `{symbol}` to your trading pairs.\n\n"
                "The symbol might already exist or there was an error.\n\n"
                "Try again or contact support.",
                parse_mode="Markdown",
            )

    except Exception as e:
        logger.error(f"Error handling custom symbol input: {e}")
        await update.message.reply_text(
            "❌ Error processing your symbol. Please try again."
        )


def is_valid_symbol(symbol: str) -> bool:
    """Validate symbol format."""
    if not symbol or len(symbol) < 3 or len(symbol) > 12:
        return False

    # Check if symbol contains only letters and numbers
    return symbol.isalnum()


def setup_message_handler(notification_manager: NotificationManager):
    """Setup message handler for the Telegram bot."""
    return handle_message
