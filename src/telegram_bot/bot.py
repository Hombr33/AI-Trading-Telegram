"""
Telegram Bot for AI Trading Bot monitoring and alerts.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler as TGCommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from src.core.logging import get_logger
from src.core.config import TelegramConfig
from .notifications import NotificationManager
from .commands import CommandHandler

logger = get_logger(__name__)


class TelegramBot:
    """Main Telegram bot for trading bot monitoring and alerts."""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.application: Optional[Application] = None
        self.notification_manager: Optional[NotificationManager] = None
        self.command_handler: Optional[CommandHandler] = None
        self.running = False

        # Initialize bot
        self._setup_bot()

    def _setup_bot(self):
        """Setup the Telegram bot."""
        try:
            # Create application
            self.application = (
                Application.builder().token(self.config.bot_token).build()
            )

            # Setup notification manager and command handler
            self.notification_manager = NotificationManager(self.config)
            self.command_handler = CommandHandler(self.notification_manager)

            # Register command handlers
            self.application.add_handler(TGCommandHandler("start", self.command_handler.start_command))
            self.application.add_handler(TGCommandHandler("help", self.command_handler.help_command))
            self.application.add_handler(TGCommandHandler("status", self.command_handler.status_command))
            self.application.add_handler(TGCommandHandler("positions", self.command_handler.positions_command))
            self.application.add_handler(TGCommandHandler("signals", self.command_handler.signals_command))
            self.application.add_handler(TGCommandHandler("risk", self.command_handler.risk_command))
            self.application.add_handler(TGCommandHandler("settings", self.command_handler.settings_command))
            
            # Register callback query handler
            self.application.add_handler(CallbackQueryHandler(self.command_handler.handle_callback))

            # Setup command handler
            self.command_handler = CommandHandler(self.notification_manager)

            # Register handlers
            self._register_handlers()

            logger.info("Telegram bot setup completed")

        except Exception as e:
            logger.error(f"Failed to setup Telegram bot: {e}")
            raise

    def _register_handlers(self):
        """Register bot command and message handlers."""
        if not self.application:
            return

        # Command handlers
        self.application.add_handler(TGCommandHandler("start", self._start_command))
        self.application.add_handler(TGCommandHandler("help", self._help_command))
        self.application.add_handler(TGCommandHandler("status", self._status_command))
        self.application.add_handler(
            TGCommandHandler("positions", self._positions_command)
        )
        self.application.add_handler(TGCommandHandler("orders", self._orders_command))
        self.application.add_handler(
            TGCommandHandler("performance", self._performance_command)
        )
        self.application.add_handler(TGCommandHandler("risk", self._risk_command))
        self.application.add_handler(
            TGCommandHandler("settings", self._settings_command)
        )
        self.application.add_handler(TGCommandHandler("journal", self._journal_command))

        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self._button_callback))

        # Message handler for general messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._message_handler)
        )

        # Error handler
        self.application.add_error_handler(self._error_handler)

    async def start(self):
        """Start the Telegram bot."""
        try:
            if not self.application:
                raise RuntimeError("Bot application not initialized")

            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()

            self.running = True
            logger.info("Telegram bot started successfully")

            # Send startup notification
            await self.notification_manager.send_startup_notification()

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            raise

    async def stop(self):
        """Stop the Telegram bot."""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()

            self.running = False
            logger.info("Telegram bot stopped")

        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")

    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        try:
            user = update.effective_user
            welcome_message = (
                f"🚀 Welcome to AI Trading Bot, {user.first_name}!\n\n"
                "I'm your personal trading assistant. Here's what I can do:\n\n"
                "📊 **Monitoring & Alerts**\n"
                "• Real-time trading signals\n"
                "• Position updates and P&L\n"
                "• Risk alerts and warnings\n\n"
                "📈 **Trading Commands**\n"
                "• Check positions and orders\n"
                "• View performance metrics\n"
                "• Monitor risk levels\n\n"
                "⚙️ **Settings**\n"
                "• Customize notifications\n"
                "• Set risk preferences\n"
                "• Configure alerts\n\n"
                "Use /help to see all available commands."
            )

            keyboard = [
                [InlineKeyboardButton("📊 Status", callback_data="status")],
                [InlineKeyboardButton("📈 Positions", callback_data="positions")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")],
                [InlineKeyboardButton("❓ Help", callback_data="help")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(welcome_message, reply_markup=reply_markup)

        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )

    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        try:
            help_message = (
                "🤖 **AI Trading Bot Commands**\n\n"
                "📊 **Status & Monitoring**\n"
                "/status - Bot and system status\n"
                "/positions - Current open positions\n"
                "/orders - Pending orders\n"
                "/performance - Trading performance\n"
                "/risk - Risk metrics and alerts\n\n"
                "📈 **Trading Operations**\n"
                "/journal - Trading journal\n"
                "/signals - Recent trading signals\n"
                "/analysis - Market analysis\n\n"
                "⚙️ **Configuration**\n"
                "/settings - Bot settings\n"
                "/notifications - Notification preferences\n"
                "/risk_limits - Risk management settings\n\n"
                "❓ **Support**\n"
                "/help - This help message\n"
                "/contact - Support contact\n\n"
                "💡 **Tips**\n"
                "• Use inline buttons for quick access\n"
                "• Set up notifications for important events\n"
                "• Monitor risk levels regularly"
            )

            await update.message.reply_text(help_message)

        except Exception as e:
            logger.error(f"Error in help command: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )

    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        try:
            status = await self.command_handler.get_system_status()
            await update.message.reply_text(status)

        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await update.message.reply_text(
                "❌ Failed to get system status. Please try again."
            )

    async def _positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /positions command."""
        try:
            positions = await self.command_handler.get_positions()
            await update.message.reply_text(positions)

        except Exception as e:
            logger.error(f"Error in positions command: {e}")
            await update.message.reply_text(
                "❌ Failed to get positions. Please try again."
            )

    async def _orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command."""
        try:
            orders = await self.command_handler.get_orders()
            await update.message.reply_text(orders)

        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            await update.message.reply_text(
                "❌ Failed to get orders. Please try again."
            )

    async def _performance_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /performance command."""
        try:
            performance = await self.command_handler.get_performance()
            await update.message.reply_text(performance)

        except Exception as e:
            logger.error(f"Error in performance command: {e}")
            await update.message.reply_text(
                "❌ Failed to get performance data. Please try again."
            )

    async def _risk_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /risk command."""
        try:
            risk = await self.command_handler.get_risk_metrics()
            await update.message.reply_text(risk)

        except Exception as e:
            logger.error(f"Error in risk command: {e}")
            await update.message.reply_text(
                "❌ Failed to get risk metrics. Please try again."
            )

    async def _settings_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /settings command."""
        try:
            settings = await self.command_handler.get_settings()
            await update.message.reply_text(settings)

        except Exception as e:
            logger.error(f"Error in settings command: {e}")
            await update.message.reply_text(
                "❌ Failed to get settings. Please try again."
            )

    async def _journal_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /journal command."""
        try:
            journal = await self.command_handler.get_trading_journal()
            await update.message.reply_text(journal)

        except Exception as e:
            logger.error(f"Error in journal command: {e}")
            await update.message.reply_text(
                "❌ Failed to get trading journal. Please try again."
            )

    async def _button_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle inline button callbacks."""
        try:
            query = update.callback_query
            await query.answer()

            data = query.data

            if data == "status":
                status = await self.command_handler.get_system_status()
                await query.edit_message_text(status)
            elif data == "positions":
                positions = await self.command_handler.get_positions()
                await query.edit_message_text(positions)
            elif data == "settings":
                settings = await self.command_handler.get_settings()
                await query.edit_message_text(settings)
            elif data == "help":
                await self._help_command(update, context)

        except Exception as e:
            logger.error(f"Error in button callback: {e}")
            await query.edit_message_text(
                "❌ Sorry, something went wrong. Please try again."
            )

    async def _message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle general text messages."""
        try:
            message = update.message.text.lower()

            if "hello" in message or "hi" in message:
                await update.message.reply_text(
                    "👋 Hello! How can I help you today? Use /help to see available commands."
                )
            elif "how are you" in message:
                await update.message.reply_text(
                    "🤖 I'm running perfectly! Ready to help with your trading needs."
                )
            elif "thank" in message:
                await update.message.reply_text(
                    "🙏 You're welcome! Is there anything else you need?"
                )
            else:
                await update.message.reply_text(
                    "💬 I didn't understand that. Use /help to see available commands or ask me something specific about trading."
                )

        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )

    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors."""
        try:
            logger.error(f"Update {update} caused error {context.error}")

            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Sorry, something went wrong. Please try again or contact support."
                )

        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    async def send_message(self, chat_id: int, message: str, **kwargs):
        """Send a message to a specific chat."""
        try:
            if not self.application:
                logger.error("Bot application not initialized")
                return False

            await self.application.bot.send_message(chat_id, message, **kwargs)
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    async def send_notification(self, message: str, notification_type: str = "info"):
        """Send a notification to all users."""
        try:
            if not self.notification_manager:
                logger.error("Notification manager not initialized")
                return False

            await self.notification_manager.send_notification(
                message, notification_type
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False

    def is_running(self) -> bool:
        """Check if bot is running."""
        return self.running

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
