"""Symbol management commands for Telegram bot."""

from typing import Any, Dict, List, Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.database.session import SessionLocal
from src.services.symbol_service import SymbolService
from src.telegram_bot.commands.base import BaseCommandHandler
from src.telegram_bot.utils.keyboards import create_keyboard

logger = get_logger(__name__)


class SymbolCommandHandler(BaseCommandHandler):
    """Handler for symbol management commands."""

    def __init__(self):
        """Initialize the handler."""
        super().__init__()
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register symbol commands."""
        self.commands = {
            "symbol": self.symbol_command,
            "addsymbol": self.add_symbol_command,
            "delsymbol": self.delete_symbol_command,
            "listsymbols": self.list_symbols_command,
        }

    def _register_callbacks(self):
        """Register symbol callbacks."""
        self.callbacks = {
            "refresh_symbols": self.list_symbols_command,
            "symbols": self.list_symbols_command,
            "confirm_delete": self.confirm_delete_callback,
        }

    async def symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /symbol command."""
        keyboard = create_keyboard(
            [
                [("List Symbols", "refresh_symbols")],
                [("Add Symbol", "add_symbol"), ("Delete Symbol", "delete_symbol")],
                [("Back to Menu", "menu")],
            ]
        )

        await update.message.reply_text(
            "🔄 Symbol Management\n\n"
            "Here you can manage symbol mappings for different brokers.\n\n"
            "Available commands:\n"
            "/addsymbol <standard> <broker> <broker_name> [description] - Add a new symbol mapping\n"
            "/delsymbol <standard> - Delete a symbol mapping\n"
            "/listsymbols - List all symbol mappings\n",
            reply_markup=keyboard,
        )

    async def add_symbol_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /addsymbol command."""
        try:
            args = context.args
            if len(args) < 3:
                await update.message.reply_text(
                    "❌ Usage: /addsymbol <standard> <broker> <broker_name> [description]\n"
                    "Example: /addsymbol EURUSD EURUSDm MT5 'MetaTrader 5 symbol'"
                )
                return

            standard = args[0].upper()
            broker = args[1]
            broker_name = args[2]
            description = " ".join(args[3:]) if len(args) > 3 else None

            session = SessionLocal()
            try:
                service = SymbolService(session)

                # Check if mapping already exists
                existing = service.get_mapping(standard, broker_name)
                if existing:
                    await update.message.reply_text(
                        f"❌ Mapping already exists for {standard} on {broker_name}:\n"
                        f"Broker Symbol: {existing.broker_symbol}\n"
                        f"Description: {existing.description or 'N/A'}"
                    )
                    return

                # Create new mapping
                mapping = service.create_mapping(
                    standard, broker, broker_name, description
                )

                await update.message.reply_text(
                    f"✅ Added new symbol mapping:\n"
                    f"Standard: {mapping.standard_symbol}\n"
                    f"Broker: {mapping.broker_symbol}\n"
                    f"Broker Name: {mapping.broker_name}\n"
                    f"Description: {mapping.description or 'N/A'}"
                )
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error in add_symbol_command: {e}")
            await update.message.reply_text(
                "❌ Failed to add symbol mapping. Please try again."
            )

    async def delete_symbol_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /delsymbol command."""
        try:
            if len(context.args) < 2:
                await update.message.reply_text(
                    "❌ Usage: /delsymbol <standard> <broker_name>\n"
                    "Example: /delsymbol EURUSD MT5"
                )
                return

            standard = context.args[0].upper()
            broker_name = context.args[1]

            session = SessionLocal()
            try:
                service = SymbolService(session)
                mapping = service.get_mapping(standard, broker_name)

                if not mapping:
                    await update.message.reply_text(
                        f"❌ No mapping found for {standard} on {broker_name}"
                    )
                    return

                keyboard = create_keyboard(
                    [
                        [
                            (
                                f"Delete {standard}",
                                f"confirm_delete:{standard}:{broker_name}",
                            )
                        ],
                        [("Cancel", "refresh_symbols")],
                    ]
                )

                await update.message.reply_text(
                    f"🗑️ Delete symbol mapping?\n\n"
                    f"Standard: {mapping.standard_symbol}\n"
                    f"Broker: {mapping.broker_symbol}\n"
                    f"Broker Name: {mapping.broker_name}\n"
                    f"Description: {mapping.description or 'N/A'}\n\n"
                    f"Are you sure you want to delete this mapping?",
                    reply_markup=keyboard,
                )
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error in delete_symbol_command: {e}")
            await update.message.reply_text(
                "❌ Failed to process delete command. Please try again."
            )

    async def list_symbols_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /listsymbols command."""
        try:
            session = SessionLocal()
            try:
                service = SymbolService(session)
                mappings = service.get_all_mappings()

                if not mappings:
                    message = (
                        "📊 **Symbol Mappings**\n\n"
                        "No symbol mappings configured.\n\n"
                        "Use /addsymbol to add a new mapping."
                    )
                    keyboard = create_keyboard(
                        [[("Add Symbol", "add_symbol")], [("Back to Menu", "start")]]
                    )
                else:
                    message = "📊 **Symbol Mappings**\n\n"
                    for mapping in mappings:
                        message += (
                            f"**{mapping.standard_symbol}** → {mapping.broker_symbol}\n"
                            f"Broker: {mapping.broker_name}\n"
                        )
                        if mapping.description:
                            message += f"Description: {mapping.description}\n"
                        message += "\n"

                    keyboard = create_keyboard(
                        [[("Refresh", "refresh_symbols")], [("Back to Menu", "start")]]
                    )

                if update.callback_query:
                    await self.edit_message(update, context, message, keyboard)
                else:
                    await self.send_message(update, context, message, keyboard)
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error in list_symbols_command: {e}")
            error_message = (
                "❌ **Error Loading Symbols**\n\n"
                "Failed to retrieve symbol mappings. Please try again."
            )
            keyboard = create_keyboard([[("Back to Menu", "start")]])

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def confirm_delete_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle symbol deletion confirmation."""
        try:
            query = update.callback_query
            data = query.data.split(":")
            if len(data) != 3:
                await query.answer("Invalid callback data")
                return

            standard = data[1].upper()
            broker_name = data[2]

            session = SessionLocal()
            try:
                service = SymbolService(session)
                success = service.delete_mapping(standard, broker_name)

                if success:
                    await query.edit_message_text(
                        f"✅ Deleted symbol mapping for {standard} on {broker_name}",
                        reply_markup=create_keyboard(
                            [[("Back to Symbols", "refresh_symbols")]]
                        ),
                    )
                else:
                    await query.edit_message_text(
                        f"❌ Failed to delete mapping for {standard} on {broker_name}",
                        reply_markup=create_keyboard(
                            [
                                [
                                    (
                                        "Try Again",
                                        f"confirm_delete:{standard}:{broker_name}",
                                    )
                                ],
                                [("Back to Symbols", "refresh_symbols")],
                            ]
                        ),
                    )
            finally:
                session.close()

        except Exception as e:
            logger.error(f"Error in confirm_delete_callback: {e}")
            await update.callback_query.answer(
                "❌ Failed to delete symbol mapping. Please try again."
            )
