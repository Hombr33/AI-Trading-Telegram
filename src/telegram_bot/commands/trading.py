"""Trading commands for Telegram bot."""

import json
from typing import Dict, Any, List, Optional
import os
from datetime import datetime

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import (
    create_keyboard,
    create_progress_keyboard,
    create_confirmation_keyboard,
    create_paginated_keyboard,
    get_trading_menu_keyboard,
)
from src.telegram_bot.utils.visual_effects import VisualEffects
from src.database.session import SessionLocal
from src.services.symbol_service import SymbolService
from src.telegram_bot.services.trading_data_service import TradingDataService

# Lazy import to avoid circular imports - moved to method level
from .base import BaseCommandHandler
from src.analysis.openai_analyzer import OpenAIAnalyzer
from src.core.config import AppConfig

logger = get_logger(__name__)

# Initialize OpenAIAnalyzer
config = AppConfig()
analyzer = OpenAIAnalyzer(
    api_key=config.openai.api_key if hasattr(config, "openai") else None
)


class TradingCommandHandler(BaseCommandHandler):
    """Trading command handler for Telegram bot."""

    def __init__(self):
        super().__init__()
        self.trading_data_service = TradingDataService()
        self._register_commands()
        self._register_callbacks()

    def _register_commands(self):
        """Register trading commands."""
        self.commands = {
            "symbols": self.symbols_command,
            "addsymbol": self.add_symbol_command,
            "delsymbol": self.delete_symbol_command,
            "positions": self.positions_command,
            "orders": self.orders_command,
            "account": self.account_command,
            "signals": self.signals_command,
        }

    def _register_callbacks(self):
        """Register trading callbacks."""
        self.callbacks = {
            "positions": self.positions_command,
            "refresh_positions": self.positions_command,
            "position_details": self.positions_command,
            "quick_close": self.positions_command,
            "orders": self.orders_command,
            "refresh_orders": self.orders_command,
            "account": self.account_command,
            "refresh_account": self.account_command,
            "account_history": self.account_command,
            "signals": self.signals_command,
            "refresh_signals": self.signals_command,
            "symbols": self.symbols_command,
            "refresh_symbols": self.symbols_command,
        }

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

    async def add_symbol_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
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

    async def delete_symbol_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
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

            existing = service.get_mapping(standard_symbol, broker_name)
            if existing:
                service.delete_mapping(standard_symbol, broker_name)
                await update.message.reply_text(
                    f"Deleted mapping: {standard_symbol} for {broker_name}"
                )
            else:
                await update.message.reply_text(
                    f"Mapping not found: {standard_symbol} for {broker_name}"
                )
        except Exception as e:
            logger.error(f"Error deleting symbol mapping: {str(e)}")
            await update.message.reply_text(f"Error deleting symbol mapping: {str(e)}")
        finally:
            session.close()

    async def positions_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /positions command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Show loading animation
            if update.callback_query:
                chat_id = update.callback_query.message.chat_id
            else:
                chat_id = update.effective_chat.id

            await VisualEffects.send_typing_effect(
                context.bot, chat_id, "Loading positions data"
            )

            # Get real positions data using the MT5 bridge service
            telegram_id = update.effective_user.id

            # Lazy import to avoid circular imports
            try:
                from src.bridge.mt5_bridge_service import get_mt5_bridge_service

                bridge_service = await get_mt5_bridge_service()
                positions = await bridge_service.get_positions_for_telegram(telegram_id)
            except ImportError:
                # Fallback to trading data service if bridge not available
                positions = await self.trading_data_service.get_positions()

            if not positions:
                message = (
                    f"📈 **POSITIONS** 📈\n\n"
                    f"No open positions at the moment.\n\n"
                    f"Use /signals to view trading signals\n"
                    f"Use /account to view account information"
                )

                keyboard = create_keyboard(
                    [
                        [
                            ("🔄 Refresh", "refresh_positions"),
                            ("🔍 Signals", "signals"),
                        ],
                        [("💰 Account", "account"), ("📋 Orders", "orders")],
                        [("📊 Status", "status"), ("🏠 Menu", "start")],
                    ]
                )
            else:
                # Format the positions message
                cards_message = ""
                total_profit = 0.0

                for pos in positions:
                    # Calculate profit percentage
                    profit = pos.get("profit", 0.0)
                    profit_pct = (
                        (profit / 10000) * 100 if profit != 0 else 0
                    )  # Assuming 10k account

                    # Format volume
                    volume = pos.get("volume", 0.0)

                    # Get price history (simplified)
                    price_history = "📈" if profit > 0 else "📉" if profit < 0 else "➡️"

                    # Create position card
                    card = (
                        f"🎯 **{pos.get('symbol', 'Unknown')}** ({pos.get('type', 'Unknown')})\n"
                        f"┌────────────────────────┐\n"
                        f"│ Volume: {volume} │ P&L: {VisualEffects.format_currency(profit)} │\n"
                        f"│ Entry: ${pos.get('price_open', 0):.5f} │ Current: ${pos.get('price_current', 0):.5f} │\n"
                        f"│ SL: ${pos.get('stop_loss', 0):.5f} │ TP: ${pos.get('take_profit', 0):.5f} │\n"
                        f"│ Ticket: {pos.get('ticket', 'N/A')} │ {price_history} │\n"
                        f"└────────────────────────┘\n"
                    )

                    cards_message += card + "\n"
                    total_profit += profit

                # Add portfolio summary
                portfolio_change = (total_profit / 10000) * 100  # Assuming 10k account
                message = (
                    f"📊 **LIVE POSITIONS DASHBOARD** 📊\n\n"
                    f"{cards_message}"
                    f"💼 **PORTFOLIO SUMMARY**\n"
                    f"┌────────────────────────┐\n"
                    f"│ Total P&L: {VisualEffects.format_currency(total_profit)} │\n"
                    f"│ Portfolio: {VisualEffects.format_percentage(portfolio_change)} │\n"
                    f"│ Positions: {len(positions)} active │\n"
                    f"└────────────────────────┘\n\n"
                    f"🕐 **Last Update**: {datetime.now().strftime('%H:%M:%S')}"
                )

                keyboard = create_keyboard(
                    [
                        [
                            ("🔄 Refresh", "refresh_positions"),
                            ("📊 Details", "position_details"),
                        ],
                        [("⚡ Quick Close", "quick_close"), ("📋 Orders", "orders")],
                        [("💰 Account", "account"), ("🌐 WebApp", "webapp")],
                        [("📊 Live Dashboard", "live_dashboard"), ("🏠 Menu", "start")],
                    ]
                )

            # Send or edit message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in positions command: {e}")
            error_message = (
                f"❌ **Error Loading Positions**\n\n"
                f"There was an issue loading position data.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_positions"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /orders command.

        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real orders data using the MT5 bridge service
            telegram_id = update.effective_user.id

            # Lazy import to avoid circular imports
            try:
                from src.bridge.mt5_bridge_service import get_mt5_bridge_service

                bridge_service = await get_mt5_bridge_service()
                orders = await bridge_service.get_orders_for_telegram(telegram_id)
            except ImportError:
                # Fallback to trading data service if bridge not available
                orders = await self.trading_data_service.get_orders()

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
                        f"  Price: ${order['price_open']:.5f}\n"
                        f"  Volume: {order['volume']}\n"
                        f"  Time: {order['time']}\n"
                        f"  Ticket: {order['ticket']}\n\n"
                    )

                message += f"**Total Orders**: {len(orders)}\n**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Create an inline keyboard for orders actions
            keyboard = create_keyboard(
                [
                    [("Refresh", "refresh_orders"), ("Positions", "positions")],
                    [("Account", "account"), ("Signals", "signals")],
                    [("Status", "status"), ("Help", "help")],
                ]
            )

            # If this is a callback query, edit the message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            error_message = (
                f"❌ **Error Loading Orders**\n\n"
                f"There was an issue loading order data.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_orders"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /account command."""
        try:
            # Show loading animation
            if update.callback_query:
                chat_id = update.callback_query.message.chat_id
            else:
                chat_id = update.effective_chat.id

            await VisualEffects.send_typing_effect(
                context.bot, chat_id, "Loading account data"
            )

            # Get real account data using the MT5 bridge service
            telegram_id = update.effective_user.id

            # Lazy import to avoid circular imports
            try:
                from src.bridge.mt5_bridge_service import get_mt5_bridge_service

                bridge_service = await get_mt5_bridge_service()
                account_info = await bridge_service.get_account_info_for_telegram(
                    telegram_id
                )
            except ImportError:
                # Fallback to trading data service if bridge not available
                account_info = await self.trading_data_service.get_account_info()

            # Calculate key metrics
            balance = account_info["balance"]
            equity = account_info["equity"]
            margin_level = account_info["margin_level"]
            profit_loss = account_info["profit_loss"]

            # Create account status indicator
            margin_status = (
                "🟢 Safe"
                if margin_level > 300
                else "🟡 Caution" if margin_level > 100 else "🔴 Danger"
            )
            equity_change = ((equity - balance) / balance) * 100

            # Format account info with VisualEffects
            message = (
                f"💰 **ACCOUNT DASHBOARD** 💰\n\n"
                f"┌─── 💼 BALANCE INFO ───┐\n"
                f"│ Balance: {VisualEffects.format_currency(balance)} │\n"
                f"│ Equity: {VisualEffects.format_currency(equity)} │\n"
                f"│ P&L: {VisualEffects.format_currency(profit_loss)} │\n"
                f"│ Change: {VisualEffects.format_percentage(equity_change)} │\n"
                f"└────────────────────────┘\n\n"
                f"┌─── 📊 MARGIN INFO ───┐\n"
                f"│ Used: {VisualEffects.format_currency(account_info['margin'])} │\n"
                f"│ Free: {VisualEffects.format_currency(account_info['free_margin'])} │\n"
                f"│ Level: {margin_level:.1f}% {margin_status} │\n"
                f"└───────────────────────┘\n\n"
                f"📊 **PORTFOLIO STATUS**\n"
                f"🎯 Open Positions: {account_info['open_positions']}\n"
                f"📋 Pending Orders: {account_info['pending_orders']}\n"
                f"🏦 Server: {account_info['server']}\n"
                f"💳 Currency: {account_info['currency']}\n"
                f"⚖️ Leverage: 1:{account_info['leverage']}\n\n"
                f"👤 **Account**: {account_info['name']}\n"
                f"🕐 **Updated**: {datetime.now().strftime('%H:%M:%S')}"
            )

            # Create enhanced keyboard
            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "refresh_account"), ("📈 Positions", "positions")],
                    [("📋 Orders", "orders"), ("📜 History", "account_history")],
                    [("🎯 Signals", "signals"), ("🌐 WebApp", "webapp")],
                    [("📊 Status", "status"), ("🏠 Menu", "start")],
                ]
            )

            # Send or edit message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in account command: {e}")
            error_message = (
                f"❌ **Error Loading Account**\n\n"
                f"There was an issue loading account data.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_account"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)

    async def signals_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /signals command."""
        try:
            # Show loading animation
            if update.callback_query:
                chat_id = update.callback_query.message.chat_id
            else:
                chat_id = update.effective_chat.id

            await VisualEffects.send_typing_effect(
                context.bot, chat_id, "Loading trading signals"
            )

            # Get real signals data using the MT5 bridge service
            telegram_id = update.effective_user.id

            # Lazy import to avoid circular imports
            try:
                from src.bridge.mt5_bridge_service import get_mt5_bridge_service

                bridge_service = await get_mt5_bridge_service()
                signals = await bridge_service.get_signals_for_telegram(
                    telegram_id, limit=10
                )
            except ImportError:
                # Fallback to trading data service if bridge not available
                signals = await self.trading_data_service.get_signals(limit=10)

            if not signals:
                message = (
                    f"🎯 **TRADING SIGNALS** 🎯\n\n"
                    f"No active trading signals at the moment.\n\n"
                    f"Signals are generated by AI analysis and appear here when available.\n"
                    f"Check back later for new opportunities."
                )

                keyboard = create_keyboard(
                    [
                        [("🔄 Refresh", "refresh_signals"), ("📊 Status", "status")],
                        [("📈 Positions", "positions"), ("💰 Account", "account")],
                        [("🏠 Menu", "start"), ("❓ Help", "help")],
                    ]
                )
            else:
                # Format the signals message
                message = f"🎯 **TRADING SIGNALS** 🎯\n\n"

                for signal in signals:
                    # Determine emoji based on bias
                    bias_emoji = (
                        "📈"
                        if signal["bias"] == "BULLISH"
                        else "📉" if signal["bias"] == "BEARISH" else "➡️"
                    )

                    # Format confidence
                    confidence = signal.get("confidence", 0)
                    confidence_emoji = (
                        "🟢" if confidence >= 80 else "🟡" if confidence >= 60 else "🔴"
                    )

                    # Format setups
                    setups = signal.get("setups", [])
                    setup_count = len(setups) if isinstance(setups, list) else 0

                    message += (
                        f"{bias_emoji} **{signal['symbol']}** ({signal['bias']})\n"
                        f"  Confidence: {confidence_emoji} {confidence}%\n"
                        f"  Setups: {setup_count} available\n"
                        f"  Status: {signal['status']}\n"
                        f"  Created: {signal['created_at'][:10] if signal['created_at'] else 'Unknown'}\n\n"
                    )

                message += f"**Total Signals**: {len(signals)}\n**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

                # Create signals keyboard
                keyboard = create_keyboard(
                    [
                        [("🔄 Refresh", "refresh_signals"), ("📊 Status", "status")],
                        [("📈 Positions", "positions"), ("💰 Account", "account")],
                        [("📋 Orders", "orders"), ("🏠 Menu", "start")],
                    ]
                )

            # Send or edit message
            if update.callback_query:
                await self.edit_message(update, context, message, keyboard)
            else:
                await self.send_message(update, context, message, keyboard)

        except Exception as e:
            logger.error(f"Error in signals command: {e}")
            error_message = (
                f"❌ **Error Loading Signals**\n\n"
                f"There was an issue loading trading signals.\n"
                f"Please try again in a moment."
            )
            keyboard = create_keyboard(
                [[("🔄 Retry", "refresh_signals"), ("📊 Status", "status")]]
            )

            if update.callback_query:
                await self.edit_message(update, context, error_message, keyboard)
            else:
                await self.send_message(update, context, error_message, keyboard)
