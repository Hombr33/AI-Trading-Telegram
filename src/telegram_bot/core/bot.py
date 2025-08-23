"""Base Telegram bot implementation."""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from telegram import Update
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

logger = get_logger(__name__)


class BaseTelegramBot:
    """Base class for Telegram bot implementation."""

    def __init__(self, config: TelegramConfig):
        """Initialize the base Telegram bot.
        
        Args:
            config: Telegram bot configuration.
        """
        self.config = config
        self.application: Optional[Application] = None
        self.running = False

    async def initialize(self):
        """Initialize the Telegram bot application."""
        try:
            # Create application
            self.application = (
                Application.builder().token(self.config.bot_token).build()
            )
            logger.info("Telegram bot application initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot application: {e}")
            return False

    def register_handler(self, handler_type, *args, **kwargs):
        """Register a handler with the application.
        
        Args:
            handler_type: The type of handler to register.
            *args: Arguments to pass to the handler.
            **kwargs: Keyword arguments to pass to the handler.
        """
        if not self.application:
            logger.error("Cannot register handler: Application not initialized")
            return False

        try:
            self.application.add_handler(handler_type(*args, **kwargs))
            return True
        except Exception as e:
            logger.error(f"Failed to register handler: {e}")
            return False

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
            return True

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False

    async def stop(self):
        """Stop the Telegram bot."""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()

            self.running = False
            logger.info("Telegram bot stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")
            return False

    async def send_message(self, chat_id: int, message: str, **kwargs):
        """Send a message to a specific chat.
        
        Args:
            chat_id: The chat ID to send the message to.
            message: The message to send.
            **kwargs: Additional arguments to pass to send_message.
            
        Returns:
            bool: True if the message was sent successfully, False otherwise.
        """
        try:
            # If application is running, use it
            if self.application and self.running:
                await self.application.bot.send_message(chat_id, message, **kwargs)
                return True
            
            # Otherwise, create a simple bot instance for sending messages
            from telegram import Bot
            bot = Bot(token=self.config.bot_token)
            
            # Initialize the bot for one-time use
            async with bot:
                await bot.send_message(chat_id, message, **kwargs)
            
            return True

        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def is_running(self) -> bool:
        """Check if bot is running.
        
        Returns:
            bool: True if the bot is running, False otherwise.
        """
        return self.running

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()