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
            # Create application with better network configuration
            builder = Application.builder().token(self.config.bot_token)
            
            # Set connection and read timeouts for better network handling
            builder = builder.read_timeout(10).write_timeout(10).connect_timeout(10)
            
            # Build the application
            self.application = builder.build()
            
            # Add error handler for network issues
            async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
                """Handle errors in the bot."""
                import traceback
                logger.error(f"Exception while handling an update: {context.error}")
                
                # Handle specific network errors gracefully
                from telegram.error import NetworkError, TimedOut, BadRequest
                if isinstance(context.error, (NetworkError, TimedOut)):
                    logger.warning("Network error occurred, will retry automatically")
                elif isinstance(context.error, BadRequest):
                    logger.warning(f"Bad request error: {context.error}")
                else:
                    logger.error(f"Unexpected error: {traceback.format_exc()}")
            
            self.application.add_error_handler(error_handler)
            
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
            
            # Configure better error handling for network issues
            from telegram.error import NetworkError, TimedOut
            from telegram.ext import ApplicationBuilder
            
            # Start polling with network error handling
            try:
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    pool_timeout=2
                )
            except (NetworkError, TimedOut) as e:
                logger.warning(f"Network error during bot startup, retrying: {e}")
                await asyncio.sleep(2)
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True,
                    read_timeout=15,
                    write_timeout=15,
                    connect_timeout=15,
                    pool_timeout=3
                )

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
                try:
                    # Stop the application which includes stopping polling
                    await asyncio.wait_for(self.application.stop(), timeout=5.0)
                    
                    # Final cleanup
                    await asyncio.wait_for(self.application.shutdown(), timeout=5.0)
                    
                except asyncio.TimeoutError:
                    logger.warning("Telegram bot stop timed out, forcing shutdown")
                except Exception as e:
                    logger.warning(f"Non-critical error during bot shutdown: {e}")

            self.running = False
            logger.info("Telegram bot stopped")
            return True

        except Exception as e:
            logger.error(f"Critical error stopping Telegram bot: {e}")
            # Don't prevent application shutdown
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