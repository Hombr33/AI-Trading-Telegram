"""
Telegram Bot for AI Trading Bot monitoring and alerts.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application,
        CommandHandler as TGCommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        filters,
        ContextTypes,
    )
except ImportError:
    # Try alternative imports for different python-telegram-bot versions
    from telegram.bot import Update
    from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
    from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
    from telegram.ext.application import Application
    from telegram.ext.commandhandler import CommandHandler as TGCommandHandler
    from telegram.ext.callbackqueryhandler import CallbackQueryHandler
    from telegram.ext.messagehandler import MessageHandler
    from telegram.ext.filters import filters
    from telegram.ext.contexttypes import ContextTypes

from src.core.logging import get_logger
from src.core.config import TelegramConfig
from .notifications import NotificationManager
from .commands import CommandHandler
from .handlers.conversation_handlers import setup_conversation_handlers

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

        # Register conversation handlers first (they have higher priority)
        conversation_handlers = setup_conversation_handlers()
        for conv_handler in conversation_handlers:
            self.application.add_handler(conv_handler)

        # Command handlers - use command_handler methods
        self.application.add_handler(TGCommandHandler("start", self.command_handler.start_command))
        self.application.add_handler(TGCommandHandler("help", self.command_handler.help_command))
        self.application.add_handler(TGCommandHandler("status", self.command_handler.status_command))
        self.application.add_handler(TGCommandHandler("positions", self.command_handler.positions_command))
        self.application.add_handler(TGCommandHandler("signals", self.command_handler.signals_command))
        self.application.add_handler(TGCommandHandler("orders", self.command_handler.orders_command))
        self.application.add_handler(TGCommandHandler("performance", self.command_handler.performance_command))
        self.application.add_handler(TGCommandHandler("risk", self.command_handler.risk_command))
        self.application.add_handler(TGCommandHandler("settings", self.command_handler.settings_command))
        self.application.add_handler(TGCommandHandler("journal", self.command_handler.journal_command))

        # Additional user commands
        self.application.add_handler(TGCommandHandler("myid", self.command_handler.my_id_command))
        self.application.add_handler(TGCommandHandler("subscription", self.command_handler.subscription_command))
        self.application.add_handler(TGCommandHandler("connections", self.command_handler.connections_command))
        self.application.add_handler(TGCommandHandler("symbols", self.command_handler.symbols_command))

        # Admin commands
        self.application.add_handler(TGCommandHandler("users", self.command_handler.users_command))
        self.application.add_handler(TGCommandHandler("server_config", self.command_handler.server_config_command))
        self.application.add_handler(TGCommandHandler("restart", self.command_handler.restart_command))
        self.application.add_handler(TGCommandHandler("logs", self.command_handler.logs_command))
        self.application.add_handler(TGCommandHandler("close_all", self.command_handler.close_all_command))

        # Multi-user commands
        self.application.add_handler(TGCommandHandler("search_users", self.command_handler.search_users_command))
        self.application.add_handler(TGCommandHandler("bulk_ops", self.command_handler.bulk_operations_command))
        self.application.add_handler(TGCommandHandler("user_details", self.command_handler.user_details_command))
        self.application.add_handler(TGCommandHandler("system_monitor", self.command_handler.system_monitor_command))

        # Callback query handler for inline buttons
        self.application.add_handler(CallbackQueryHandler(self.command_handler.handle_callback))

        # Message handler for general messages
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.command_handler.message_handler)
        )

        # Error handler
        self.application.add_error_handler(self.command_handler.error_handler)

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

    # Removed _handle_callback method as we're using command_handler.handle_callback instead

    async def stop(self):
        """Stop the Telegram bot."""
        try:
            if self.application and self.running:
                logger.info("Stopping Telegram bot polling...")
                
                # First stop the updater (this stops polling gracefully)
                if self.application.updater and self.application.updater.running:
                    try:
                        await self.application.updater.stop()
                        logger.info("Telegram updater stopped")
                    except Exception as e:
                        logger.warning(f"Error stopping updater: {e}")
                
                # Then stop the application
                try:
                    await self.application.stop()
                    logger.info("Telegram application stopped")
                except Exception as e:
                    logger.warning(f"Error stopping application: {e}")
                
                # Finally shutdown the application
                try:
                    await self.application.shutdown()
                    logger.info("Telegram application shutdown complete")
                except Exception as e:
                    logger.warning(f"Error during application shutdown: {e}")

            self.running = False
            logger.info("Telegram bot stopped")

        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
            self.running = False


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
