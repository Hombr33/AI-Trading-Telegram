"""Trading commands for Telegram bot."""

from typing import Dict, Any, List, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import (
    create_keyboard, 
    create_progress_keyboard, 
    create_confirmation_keyboard,
    create_paginated_keyboard,
    get_trading_menu_keyboard
)
from src.telegram_bot.utils.visual_effects import VisualEffects
from src.telegram_bot.utils.mock_data import (
    get_positions, get_orders, get_account_info, get_recent_signals
)
from src.database.session import SessionLocal
from src.services.symbol_service import SymbolService
from .base import BaseCommandHandler

logger = get_logger(__name__)


class TradingCommandHandler(BaseCommandHandler):
    """Trading command handler for Telegram bot."""

    async def symbols_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /symbols command."""
        try:
            session = SessionLocal()
            service = SymbolService(session)
            
            broker_name = context.args[0] if context.args else None
            mappings = service.get_all_mappings(broker_name)
            
            if not mappings:
                response = "No symbol mappings found."
                if broker_name:
                    response += f" for broker {broker_name}"
                await update.message.reply_text(response)
                return

            response = "Symbol Mappings:\n"
            for mapping in mappings:
                response += f"{mapping.standard_symbol} -> {mapping.broker_symbol} ({mapping.broker_name})\n"
            
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error listing symbols: {str(e)}")
            await update.message.reply_text(f"Error listing symbols: {str(e)}")
        finally:
            session.close()

    async def add_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /addsymbol command."""
        if len(context.args) != 3:
            await update.message.reply_text(
                "Usage: /addsymbol <standard_symbol> <broker_symbol> <broker_name>"
            )
            return

        standard_symbol, broker_symbol, broker_name = context.args
        
        try:
            session = SessionLocal()
            service = SymbolService(session)
            
            existing = service.get_mapping(standard_symbol, broker_name)
            if existing:
                service.update_mapping(standard_symbol, broker_symbol, broker_name)
                await update.message.reply_text(
                    f"Updated mapping: {standard_symbol} -> {broker_symbol} for {broker_name}"
                )
            else:
                service.create_mapping(standard_symbol, broker_symbol, broker_name)
                await update.message.reply_text(
                    f"Added mapping: {standard_symbol} -> {broker_symbol} for {broker_name}"
                )
        except Exception as e:
            logger.error(f"Error adding symbol mapping: {str(e)}")
            await update.message.reply_text(f"Error adding symbol mapping: {str(e)}")
        finally:
            session.close()

    async def delete_symbol_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /delsymbol command."""
        if len(context.args) != 2:
            await update.message.reply_text(
                "Usage: /delsymbol <standard_symbol> <broker_name>"
            )
            return

        standard_symbol, broker_name = context.args
        
        try:
            session = SessionLocal()
            service = SymbolService(session)
            
            if service.delete_mapping(standard_symbol, broker_name):
                await update.message.reply_text(
                    f"Deleted mapping for {standard_symbol} ({broker_name})"
                )
            else:
                await update.message.reply_text(
                    f"No mapping found for {standard_symbol} ({broker_name})"
                )
        except Exception as e:
            logger.error(f"Error deleting symbol mapping: {str(e)}")
            await update.message.reply_text(f"Error deleting symbol mapping: {str(e)}")
        finally:
            session.close()

    def _register_commands(self):
        """Register trading commands."""
        self.commands = {
            "positions": self.positions_command,
            "orders": self.orders_command,
            "account": self.account_command,
            "signals": self.signals_command,
            "symbols": self.symbols_command,
            "addsymbol": self.add_symbol_command,
            "delsymbol": self.delete_symbol_command,
        }

    def _register_callbacks(self):
        """Register trading callbacks."""
        self.callbacks = {
            "positions": self.positions_command,
            "refresh_positions": self.positions_command,
            "orders": self.orders_command,
            "refresh_orders": self.orders_command,
            "account": self.account_command,
            "refresh_account": self.account_command,
            "account_history": self.account_history_callback,
            "symbols": self.symbols_command,
            "addsymbol": self.add_symbol_command,
            "delsymbol": self.delete_symbol_command,
            "signals": self.signals_command,
            "refresh_signals": self.signals_command,
            "refresh_symbols": self.symbols_command,
        }

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /positions command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get positions data
        positions = get_positions()

        if not positions:
            message = (
                f"📊 **LIVE POSITIONS DASHBOARD** 📊\n\n"
                f"🎯 **No Active Positions**\n\n"
                f"💡 **Quick Actions**:\n"
                f"🎯 Check AI signals for opportunities\n"
                f"📋 Review pending orders\n"
                f"💰 Monitor account balance\n\n"
                f"⚡ *Ready to trade when you are!*"
            )
            keyboard = create_keyboard([
                [("🎯 Get Signals", "signals"), ("📋 View Orders", "orders")],
                [("💰 Account Info", "account"), ("📊 Market Pulse", "market_pulse")],
                [("🔄 Refresh", "refresh_positions"), ("❓ Help", "help")]
            ])
        else:
            # Show typing effect for better UX
            await VisualEffects.send_typing_effect(update, context, 1.0)
            
            # Format the positions message with enhanced visuals
            total_profit = sum(pos["profit"] for pos in positions)
            profit_trend = VisualEffects.create_profit_trend([0, total_profit])
            
            message = (
                f"📊 **LIVE POSITIONS DASHBOARD** 📊\n\n"
                f"💰 **Portfolio P&L**: {VisualEffects.format_currency(total_profit)}\n"
                f"📈 **Trend**: {profit_trend}\n\n"
            )

            for i, position in enumerate(positions, 1):
                # Use visual effects for trading card
                card = VisualEffects.create_trading_card(position)
                message += card + "\n\n"

            message += (
                f"📊 **Portfolio Summary**:\n"
                f"🎯 Active Positions: **{len(positions)}**\n"
                f"💰 Total Value: {VisualEffects.format_currency(total_profit)}\n"
                f"🕐 **Live Update**: {datetime.now().strftime('%H:%M:%S')}"
            )
            
            # Create enhanced keyboard with quick actions
            keyboard = create_keyboard([
                [("🔄 Refresh", "refresh_positions"), ("📊 Details", "position_details")],
                [("⚡ Quick Close", "quick_close"), ("🎯 Add Position", "add_position")],
                [("💰 Account", "account"), ("⚠️ Risk Check", "risk")],
                [("📋 Orders", "orders"), ("📊 Performance", "performance")]
            ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /orders command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get orders data
        orders = get_orders()

        if not orders:
            message = (
                f"📝 **ORDERS** 📝\n\n"
                f"No pending orders at the moment.\n\n"
                f"Use /signals to view trading signals\n"
                f"Use /positions to view open positions"
            )
        else:
            # Format the orders message
            message = f"📝 **ORDERS** 📝\n\n"

            for order in orders:
                # Determine emoji based on order type
                type_emoji = "📈" if order["type"] == "BUY" else "📉"

                message += (
                    f"{type_emoji} **{order['symbol']}** ({order['type']})\n"
                    f"  Price: ${order['price']:.5f}\n"
                    f"  Volume: {order['volume']}\n"
                    f"  Type: {order['order_type']}\n"
                    f"  Status: {order['status']}\n\n"
                )

            message += f"**Total Orders**: {len(orders)}\n**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Create an inline keyboard for orders actions
        keyboard = create_keyboard([
            [("Refresh", "refresh_orders"), ("Positions", "positions")],
            [("Account", "account"), ("Signals", "signals")],
            [("Status", "status"), ("Risk", "risk")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /account command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get account data
        account_info = get_account_info()

        # Format the account message
        message = (
            f"💰 **ACCOUNT INFORMATION** 💰\n\n"
            f"**Balance**: ${account_info['balance']:.2f}\n"
            f"**Equity**: ${account_info['equity']:.2f}\n"
            f"**Margin**: ${account_info['margin']:.2f}\n"
            f"**Free Margin**: ${account_info['free_margin']:.2f}\n"
            f"**Margin Level**: {account_info['margin_level']:.2f}%\n\n"
            f"**Profit/Loss**: ${account_info['profit_loss']:.2f}\n"
            f"**Open Positions**: {account_info['open_positions']}\n"
            f"**Pending Orders**: {account_info['pending_orders']}\n\n"
            f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        # Create an inline keyboard for account actions
        keyboard = create_keyboard([
            [("Refresh", "refresh_account"), ("Positions", "positions")],
            [("Orders", "orders"), ("Risk", "risk")],
            [("Account History", "account_history"), ("Status", "status")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def account_history_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the account_history callback.
        
        Args:
            update: The update object.
            context: The context object.
        """
        message = (
            f"📜 **ACCOUNT HISTORY** 📜\n\n"
            f"Account history feature coming soon!\n\n"
            f"This feature will show your account history, including deposits, withdrawals, and closed positions."
        )

        # Create an inline keyboard to go back to account
        keyboard = create_keyboard([
            [("Back to Account", "account")],
            [("Status", "status"), ("Help", "help")]
        ])

        await self.edit_message(update, context, message, keyboard)

    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /signals command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        # Get signals data
        signals = get_recent_signals()

        if not signals:
            message = (
                f"🚨 **TRADING SIGNALS** 🚨\n\n"
                f"No recent trading signals.\n\n"
                f"Use /positions to view open positions\n"
                f"Use /orders to view pending orders"
            )
        else:
            # Format the signals message
            message = f"🚨 **TRADING SIGNALS** 🚨\n\n"

            for signal in signals:
                # Determine emoji based on signal direction
                direction_emoji = "📈" if signal["direction"] == "BUY" else "📉"

                message += (
                    f"{direction_emoji} **{signal['symbol']}** ({signal['direction']})\n"
                    f"  Entry: ${signal['entry_price']:.5f}\n"
                    f"  Target: ${signal['target_price']:.5f}\n"
                    f"  Stop Loss: ${signal['stop_loss']:.5f}\n"
                    f"  Strength: {signal['strength'] * 100:.1f}%\n"
                    f"  Time: {signal['timestamp']}\n\n"
                )

            message += f"**Total Signals**: {len(signals)}\n**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Create an inline keyboard for signals actions
        keyboard = create_keyboard([
            [("Refresh", "refresh_signals"), ("Positions", "positions")],
            [("Orders", "orders"), ("Account", "account")],
            [("Status", "status"), ("Risk", "risk")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)