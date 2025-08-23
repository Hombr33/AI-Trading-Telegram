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
        self.polling_task: Optional[asyncio.Task] = None

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
                # Store the polling task so we can cancel it later
                self.polling_task = asyncio.create_task(
                    self.application.updater.start_polling(
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=True
                    )
                )
            except (NetworkError, TimedOut) as e:
                logger.warning(f"Network error during bot startup, retrying: {e}")
                await asyncio.sleep(2)
                self.polling_task = asyncio.create_task(
                    self.application.updater.start_polling(
                        allowed_updates=Update.ALL_TYPES,
                        drop_pending_updates=True
                    )
                )

            self.running = True
            logger.info("Telegram bot started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            return False

    async def stop(self):
        """Stop the Telegram bot using the proper shutdown sequence.
        
        This follows the recommended python-telegram-bot shutdown pattern:
        1. Stop the updater first
        2. Stop the application
        3. Shutdown the application
        4. Cancel the polling task gracefully
        """
        try:
            if not self.application:
                logger.info("Telegram bot application not initialized, nothing to stop")
                self.running = False
                return True

            logger.info("Starting Telegram bot shutdown sequence...")
            
            # Step 1: Stop the updater first (this stops polling)
            if self.application.updater and self.application.updater.running:
                try:
                    logger.info("Stopping Telegram bot updater...")
                    await self.application.updater.stop()
                    logger.info("Updater stopped successfully")
                except Exception as e:
                    logger.warning(f"Error stopping updater: {e}")
            
            # Step 2: Stop the application (this stops the updater if not already stopped)
            try:
                logger.info("Stopping Telegram bot application...")
                await self.application.stop()
                logger.info("Application stopped successfully")
            except Exception as e:
                logger.warning(f"Error stopping application: {e}")
            
            # Step 3: Shutdown the application
            try:
                logger.info("Shutting down Telegram bot application...")
                await self.application.shutdown()
                logger.info("Application shutdown completed")
            except Exception as e:
                logger.warning(f"Error during application shutdown: {e}")
            
            # Step 4: Cancel the polling task gracefully
            if self.polling_task and not self.polling_task.done():
                logger.info("Cancelling polling task...")
                try:
                    # Cancel the task
                    self.polling_task.cancel()
                    
                    # Wait for the task to complete cancellation
                    try:
                        await asyncio.wait_for(self.polling_task, timeout=5.0)
                    except asyncio.TimeoutError:
                        logger.warning("Polling task cancellation timed out")
                    except asyncio.CancelledError:
                        logger.info("Polling task cancelled successfully")
                    except Exception as e:
                        logger.warning(f"Unexpected error during polling task cancellation: {e}")
                    finally:
                        if not self.polling_task.done():
                            logger.error("Polling task did not complete cancellation")
                except Exception as e:
                    logger.warning(f"Error cancelling polling task: {e}")
            
            # Step 5: Final cleanup
            self.polling_task = None
            self.application = None
            self.running = False
            
            logger.info("Telegram bot shutdown completed successfully")
            return True

        except Exception as e:
            logger.error(f"Critical error during Telegram bot shutdown: {e}")
            # Force cleanup even on error
            self.polling_task = None
            self.application = None
            self.running = False
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