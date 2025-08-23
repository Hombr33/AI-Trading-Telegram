"""Symbol management commands for Telegram bot."""

from typing import Dict, Any, List, Optional
from telegram import Update
from telegram.ext import ContextTypes
from src.core.logging import get_logger
from src.services.symbol_service import SymbolService
from src.telegram_bot.utils.keyboards import create_keyboard
from src.telegram_bot.commands.base import BaseCommandHandler

logger = get_logger(__name__)

class SymbolCommandHandler(BaseCommandHandler):
    """Handler for symbol management commands."""

    def __init__(self, symbol_service: SymbolService):
        """Initialize the handler.
        
        Args:
            symbol_service: The symbol service.
        """
        super().__init__()
        self.symbol_service = symbol_service

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
            "delete_symbol": self.delete_symbol_callback,
            "confirm_delete": self.confirm_delete_callback,
        }

    async def symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /symbol command."""
        keyboard = create_keyboard([
            [("List Symbols", "refresh_symbols")],
            [("Add Symbol", "add_symbol"), ("Delete Symbol", "delete_symbol")],
            [("Back to Menu", "menu")]
        ])

        await update.message.reply_text(
            "🔄 Symbol Management\n\n"
            "Here you can manage symbol mappings for different brokers.\n\n"
            "Available commands:\n"
            "/addsymbol <standard> <broker> <broker_name> [description] - Add a new symbol mapping\n"
            "/delsymbol <standard> - Delete a symbol mapping\n"
            "/listsymbols - List all symbol mappings\n",
            reply_markup=keyboard
        )

    async def add_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /addsymbol command."""
        try:
            args = context.args
            if len(args) < 3:
                await update.message.reply_text(
                    "❌ Usage: /addsymbol <standard> <broker> <broker_name> [description]\n"
                    "Example: /addsymbol EURUSD EURUSDm Exness 'Exness MetaTrader 5'"
                )
                return

            standard = args[0].upper()
            broker = args[1]
            broker_name = args[2]
            description = " ".join(args[3:]) if len(args) > 3 else None

            # Check if mapping already exists
            existing = await self.symbol_service.get_mapping(standard)
            if existing:
                await update.message.reply_text(
                    f"❌ Mapping already exists for {standard}:\n"
                    f"Broker: {existing.broker_symbol}\n"
                    f"Broker Name: {existing.broker_name}"
                )
                return

            # Create new mapping
            mapping = await self.symbol_service.create_mapping(
                standard,
                broker,
                broker_name,
                description
            )

            await update.message.reply_text(
                f"✅ Added new symbol mapping:\n"
                f"Standard: {mapping.standard_symbol}\n"
                f"Broker: {mapping.broker_symbol}\n"
                f"Broker Name: {mapping.broker_name}\n"
                f"Description: {mapping.description or 'N/A'}"
            )

        except Exception as e:
            logger.error(f"Error in add_symbol_command: {e}")
            await update.message.reply_text(
                "❌ Failed to add symbol mapping. Please try again."
            )

    async def delete_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /delsymbol command."""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ Usage: /delsymbol <standard>\n"
                    "Example: /delsymbol EURUSD"
                )
                return

            standard = context.args[0].upper()
            mapping = await self.symbol_service.get_mapping(standard)
            
            if not mapping:
                await update.message.reply_text(f"❌ No mapping found for {standard}")
                return

            keyboard = create_keyboard([
                [(f"Delete {standard}", f"confirm_delete:{standard}")],
                [("Cancel", "refresh_symbols")]
            ])

            await update.message.reply_text(
                f"🗑️ Delete symbol mapping?\n\n"
                f"Standard: {mapping.standard_symbol}\n"
                f"Broker: {mapping.broker_symbol}\n"
                f"Broker Name: {mapping.broker_name}\n"
                f"Description: {mapping.description or 'N/A'}\n\n"
                f"Are you sure you want to delete this mapping?",
                reply_markup=keyboard
            )

        except Exception as e:
            logger.error(f"Error in delete_symbol_command: {e}")
            await update.message.reply_text(
                "❌ Failed to process delete command. Please try again."
            )

    async def list_symbols_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /listsymbols command."""
        try:
            mappings = await self.symbol_service.get_all_mappings()
            
            if not mappings:
                await update.message.reply_text(
                    "📊 No symbol mappings found.\n"
                    "Use /addsymbol to add a new mapping."
                )
                return

            message = "📊 Symbol Mappings:\n\n"
            for mapping in mappings:
                message += (
                    f"Standard: {mapping.standard_symbol}\n"
                    f"Broker: {mapping.broker_symbol}\n"
                    f"Broker Name: {mapping.broker_name}\n"
                )
                if mapping.description:
                    message += f"Description: {mapping.description}\n"
                message += "----------------------\n"

            keyboard = create_keyboard([
                [("Add Symbol", "add_symbol"), ("Delete Symbol", "delete_symbol")],
                [("Refresh", "refresh_symbols"), ("Back to Menu", "menu")]
            ])

            await update.message.reply_text(message, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Error in list_symbols_command: {e}")
            await update.message.reply_text(
                "❌ Failed to retrieve symbol mappings. Please try again."
            )

    async def confirm_delete_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle symbol deletion confirmation."""
        try:
            query = update.callback_query
            data = query.data.split(":")
            if len(data) != 2:
                await query.answer("Invalid callback data")
                return

            standard = data[1].upper()
            success = await self.symbol_service.delete_mapping(standard)

            if success:
                await query.edit_message_text(
                    f"✅ Deleted symbol mapping for {standard}",
                    reply_markup=create_keyboard([
                        [("Back to Symbols", "refresh_symbols")]
                    ])
                )
            else:
                await query.edit_message_text(
                    f"❌ Failed to delete mapping for {standard}",
                    reply_markup=create_keyboard([
                        [("Try Again", f"delete_symbol:{standard}")],
                        [("Back to Symbols", "refresh_symbols")]
                    ])
                )

        except Exception as e:
            logger.error(f"Error in confirm_delete_callback: {e}")
            await update.callback_query.answer(
                "❌ Failed to delete symbol mapping. Please try again."
            )
