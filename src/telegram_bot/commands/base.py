"""Base command handler for Telegram bot."""

import asyncio
from typing import Optional, Union

from telegram import (
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard

logger = get_logger(__name__)


class BaseCommandHandler:
    """Base command handler for Telegram bot."""

    def __init__(self):
        """Initialize base command handler."""
        self.commands = {}
        self.callbacks = {}
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register commands.

        This method should be overridden by subclasses.
        """
        pass

    def _register_callbacks(self):
        """Register callbacks.

        This method should be overridden by subclasses.
        """
        pass

    async def send_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        reply_keyboard: Optional[
            Union[ReplyKeyboardMarkup, ReplyKeyboardRemove]
        ] = None,
        parse_mode: str = "Markdown",
    ):
        """Send a message to the user.

        Args:
            update: The update object.
            context: The context object.
            text: The text to send.
            keyboard: The inline keyboard to attach to the message.
            reply_keyboard: The reply keyboard to show.
            parse_mode: The parse mode to use.
        """
        try:
            # Use reply keyboard if provided, otherwise use inline keyboard
            reply_markup = reply_keyboard if reply_keyboard is not None else keyboard

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode,
            )

            # If we have both keyboards, send inline keyboard in separate message
            if reply_keyboard is not None and keyboard is not None:
                await asyncio.sleep(0.1)  # Small delay for better UX
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="🎯 **Quick Actions Dashboard**",
                    reply_markup=keyboard,
                    parse_mode=parse_mode,
                )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            # Try without parse mode if it fails
            try:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"Error: {e}\n\nOriginal message: {text}",
                    reply_markup=keyboard,
                    parse_mode=None,
                )
            except Exception as e2:
                logger.error(f"Error sending error message: {e2}")

    async def edit_message(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        parse_mode: str = "Markdown",
    ):
        """Edit a message.

        Args:
            update: The update object.
            context: The context object.
            text: The text to send.
            keyboard: The keyboard to attach to the message.
            parse_mode: The parse mode to use.
        """
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=update.callback_query.message.message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode,
            )
        except Exception as e:
            error_msg = str(e)
            if "Message is not modified" in error_msg:
                # Message content is the same, just answer the callback query
                logger.debug("Message content unchanged, answering callback query")
                await update.callback_query.answer()
                return
            else:
                logger.error(f"Error editing message: {e}")
                # Try without parse mode if it fails
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=update.callback_query.message.message_id,
                        text=f"Error: {e}\n\nOriginal message: {text}",
                        reply_markup=keyboard,
                        parse_mode=None,
                    )
                except Exception as e2:
                    logger.error(f"Error sending error message: {e2}")

    async def answer_callback_query(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        text: str = None,
        show_alert: bool = False,
    ):
        """Answer a callback query.

        Args:
            update: The update object.
            context: The context object.
            text: The text to send.
            show_alert: Whether to show an alert.
        """
        try:
            await context.bot.answer_callback_query(
                callback_query_id=update.callback_query.id,
                text=text,
                show_alert=show_alert,
            )
        except Exception as e:
            logger.error(f"Error answering callback query: {e}")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries.

        Args:
            update: The update object.
            context: The context object.
        """
        query = update.callback_query
        callback_data = query.data

        # Answer the callback query to stop the loading animation
        await self.answer_callback_query(update, context)

        # Find and execute the appropriate callback handler
        if callback_data in self.callbacks:
            await self.callbacks[callback_data](update, context)
        else:
            logger.warning(f"Unknown callback data: {callback_data}")
            await self.edit_message(
                update,
                context,
                f"Unknown callback: {callback_data}\n\nPlease try again or use /help to see available commands.",
                create_keyboard([[("Help", "help")]]),
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors.

        Args:
            update: The update object.
            context: The context object.
        """
        logger.error(f"Update {update} caused error {context.error}")

        try:
            # Send a message to the user
            if update and update.effective_chat:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"❌ **ERROR**\n\nAn error occurred while processing your request.\n\nError: {context.error}",
                    parse_mode="Markdown",
                )
        except Exception as e:
            logger.error(f"Error sending error message: {e}")

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages.

        Args:
            update: The update object.
            context: The context object.
        """
        # This is a placeholder for message handling
        # Subclasses should override this method if needed
        pass
