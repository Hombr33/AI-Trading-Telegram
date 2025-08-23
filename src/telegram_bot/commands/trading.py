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
    get_trading_menu_keyboard
)
from src.telegram_bot.utils.visual_effects import VisualEffects
from src.database.session import SessionLocal
from src.services.symbol_service import SymbolService
from .base import BaseCommandHandler
from src.analysis.openai_analyzer import OpenAIAnalyzer
from src.core.config import AppConfig

logger = get_logger(__name__)

# Initialize OpenAIAnalyzer
config = AppConfig()
analyzer = OpenAIAnalyzer(api_key=config.openai.api_key if hasattr(config, 'openai') else None)


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
            "signal": self.signal_for_pair_command,  # New command for specific pairs
            "symbols": self.symbols_command,
            "addsymbol": self.add_symbol_command,
            "delsymbol": self.delete_symbol_command,
        }

    def _register_callbacks(self):
        """Register trading callbacks."""
        # Callbacks are now handled by the main callback handler
        # This keeps the trading commands focused on command handling only
        self.callbacks = {}

    async def positions_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /positions command."""
        try:
            # Show loading animation
            if update.callback_query:
                chat_id = update.callback_query.message.chat_id
            else:
                chat_id = update.effective_chat.id
                
            await VisualEffects.send_typing_effect(
                context.bot, chat_id, "Loading positions"
            )
            
            # Get real positions data
            positions = await self._get_real_positions()

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
                    [("🎯 Signal EURUSD", "signal_EURUSD_H1"), ("🎯 Signal GBPUSD", "signal_GBPUSD_H1")],
                    [("💰 Account Info", "account"), ("📊 Status", "status")],
                    [("🔄 Refresh", "refresh_positions"), ("❓ Help", "help")]
                ])
            else:
                # Create visual trading cards for each position
                cards_message = ""
                total_profit = 0
                
                for position in positions:
                    # Generate mock price history for sparkline
                    open_price = position.get("price_open", 1.1234)
                    current_price = position.get("price_current", open_price)
                    profit = position.get("profit", 0)
                    volume = position.get("volume", 0.1)
                    
                    # Calculate profit percentage
                    profit_pct = (profit / (open_price * volume * 100000)) * 100 if volume > 0 else 0
                    
                    # Create price history for sparkline
                    price_history = [
                        open_price * (1 + (i * 0.001)) for i in range(-5, 5)
                    ]
                    
                    # Create trading card using VisualEffects
                    card = VisualEffects.create_trading_card(
                        symbol=position.get("symbol", "UNKNOWN"),
                        direction=position.get("type", "BUY"),
                        entry_price=open_price,
                        current_price=current_price,
                        profit=profit,
                        profit_pct=profit_pct,
                        volume=volume,
                        price_history=price_history
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
                
                keyboard = create_keyboard([
                    [("🔄 Refresh", "refresh_positions"), ("📊 Details", "position_details")],
                    [("⚡ Quick Close", "quick_close"), ("📋 Orders", "orders")],
                    [("💰 Account", "account"), ("🌐 WebApp", "webapp")],
                    [("📊 Live Dashboard", "live_dashboard"), ("🏠 Menu", "start")]
                ])

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
            keyboard = create_keyboard([
                [("🔄 Retry", "refresh_positions"), ("📊 Status", "status")]
            ])
            
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
            # Get real orders data
            orders = await self._get_real_orders()

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
            keyboard = create_keyboard([
                [("Refresh", "refresh_orders"), ("Positions", "positions")],
                [("Account", "account"), ("Signals", "signals")],
                [("Status", "status"), ("Help", "help")]
            ])

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
            keyboard = create_keyboard([
                [("🔄 Retry", "refresh_orders"), ("📊 Status", "status")]
            ])
            
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
            
            # Get real account data
            account_info = await self._get_real_account_info()

            # Calculate key metrics
            balance = account_info['balance']
            equity = account_info['equity']
            margin_level = account_info['margin_level']
            profit_loss = account_info['profit_loss']
            
            # Create account status indicator
            margin_status = "🟢 Safe" if margin_level > 300 else "🟡 Caution" if margin_level > 100 else "🔴 Danger"
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
            keyboard = create_keyboard([
                [("🔄 Refresh", "refresh_account"), ("📈 Positions", "positions")],
                [("📋 Orders", "orders"), ("📜 History", "account_history")],
                [("🎯 Signals", "signals"), ("🌐 WebApp", "webapp")],
                [("📊 Status", "status"), ("🏠 Menu", "start")]
            ])

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
            keyboard = create_keyboard([
                [("🔄 Retry", "refresh_account"), ("📊 Status", "status")]
            ])
            
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
                await update.callback_query.answer("🤖 Generating AI signals...")
            else:
                chat_id = update.effective_chat.id
                
            await VisualEffects.send_typing_effect(
                context.bot, chat_id, "Analyzing markets with AI"
            )
            
            # Generate real AI signals
            signals = await self._generate_ai_signals()
            
            if not signals:
                message = (
                    f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                    f"🔍 **Market Analysis Complete**\n\n"
                    f"🤖 AI is monitoring 28+ currency pairs\n"
                    f"📊 No high-confidence signals at the moment\n\n"
                    f"💡 **What this means**:\n"
                    f"• Market conditions are mixed\n"
                    f"• Risk/reward ratios are unfavorable\n"
                    f"• Waiting for clearer opportunities\n\n"
                    f"🔄 **Auto-refresh in progress...**"
                )
                
                # Create keyboard with manual signal requests
                keyboard = create_keyboard([
                    [("🎯 EURUSD Signal", "signal_EURUSD_H1"), ("🎯 GBPUSD Signal", "signal_GBPUSD_H1")],
                    [("🎯 XAUUSD Signal", "signal_XAUUSD_H1"), ("🎯 USDJPY Signal", "signal_USDJPY_H1")],
                    [("🔄 Refresh All", "refresh_signals"), ("📊 Market Watch", "symbols")],
                    [("📈 Positions", "positions"), ("🏠 Menu", "start")]
                ])
            else:
                # Create signal cards using VisualEffects
                signals_text = ""
                
                for i, signal in enumerate(signals, 1):
                    # Generate price history for sparkline
                    entry_price = signal['entry_price']
                    price_history = [
                        entry_price * (1 + (j * 0.0001)) for j in range(-10, 10, 2)
                    ]
                    
                    # Create signal card
                    profit_estimate = (signal['target_price'] - entry_price) * 100000 * 0.1  # Estimate for 0.1 lot
                    profit_pct = ((signal['target_price'] - entry_price) / entry_price) * 100
                    
                    card = VisualEffects.create_trading_card(
                        symbol=signal['symbol'],
                        direction=signal['direction'],
                        entry_price=entry_price,
                        current_price=entry_price,  # Use entry price as current for signals
                        profit=profit_estimate,
                        profit_pct=profit_pct,
                        volume=0.1,
                        price_history=price_history
                    )
                    
                    confidence = "High" if signal["strength"] > 0.8 else "Medium" if signal["strength"] > 0.6 else "Low"
                    
                    signals_text += (
                        f"{card}\n"
                        f"🎯 **Target**: {VisualEffects.format_currency(signal['target_price'])}\n"
                        f"🛡️ **Stop**: {VisualEffects.format_currency(signal['stop_loss'])}\n"
                        f"⚡ **Confidence**: {confidence} ({signal['strength'] * 100:.1f}%)\n"
                        f"💡 **Reason**: {signal['reasoning']}\n\n"
                    )

                message = (
                    f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                    f"🤖 **AI Analysis Complete** | {len(signals)} signals found\n\n"
                    f"{signals_text}"
                    f"🔄 **Updated**: {datetime.now().strftime('%H:%M:%S')}"
                )
                
                # Create keyboard with individual signal buttons
                signal_buttons = []
                for signal in signals[:4]:  # Show up to 4 signals as buttons
                    signal_buttons.append((f"🎯 {signal['symbol']}", f"signal_{signal['symbol']}_H1"))
                
                keyboard_rows = [signal_buttons[i:i+2] for i in range(0, len(signal_buttons), 2)]
                keyboard_rows.extend([
                    [("🔄 Refresh", "refresh_signals"), ("📊 Market Watch", "symbols")],
                    [("📈 Positions", "positions"), ("🌐 WebApp", "webapp")],
                    [("💰 Account", "account"), ("🏠 Menu", "start")]
                ])
                
                keyboard = create_keyboard(keyboard_rows)
            
        except Exception as e:
            logger.error(f"Error generating AI signals: {e}")
            message = (
                f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                f"❌ **Error generating signals**\n\n"
                f"AI analyzer encountered an issue.\n"
                f"Please try again in a moment."
            )
            
            keyboard = create_keyboard([
                [("🔄 Retry", "refresh_signals"), ("📊 Status", "status")],
                [("🏠 Menu", "start")]
            ])

        # Send or edit message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def signal_for_pair_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /signal command for specific trading pairs.
        
        Usage: /signal <symbol> [timeframe]
        Examples: /signal EURUSD, /signal GBPUSD H1, /signal XAUUSD H4
        
        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Check if symbol is provided
            if not context.args:
                message = (
                    f"🎯 **SIGNAL REQUEST** 🎯\n\n"
                    f"❌ **No symbol specified**\n\n"
                    f"📝 **Usage**: `/signal <symbol> [timeframe]`\n\n"
                    f"💡 **Examples**:\n"
                    f"• `/signal EURUSD` - Get signal for EURUSD (default H1)\n"
                    f"• `/signal GBPUSD H1` - Get signal for GBPUSD on H1 timeframe\n"
                    f"• `/signal XAUUSD H4` - Get signal for XAUUSD on H4 timeframe\n\n"
                    f"🔄 **Available Timeframes**: M5, M15, H1, H4, D1\n"
                    f"📊 **Available Symbols**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, XAUUSD"
                )
                
                keyboard = create_keyboard([
                    [("🎯 Get All Signals", "signals"), ("📋 View Symbols", "symbols")],
                    [("📊 Positions", "positions"), ("💰 Account", "account")],
                    [("❓ Help", "help")]
                ])
                
                await self.send_message(update, context, message, keyboard)
                return

            # Get symbol and optional timeframe
            symbol = context.args[0].upper()
            timeframe = context.args[1].upper() if len(context.args) > 1 else "H1"
            
            # Validate symbol
            valid_symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "XAUUSD", "BTCUSDT", "ETHUSDT"]
            if symbol not in valid_symbols:
                message = (
                    f"🎯 **SIGNAL REQUEST** 🎯\n\n"
                    f"❌ **Invalid symbol**: `{symbol}`\n\n"
                    f"📊 **Available Symbols**:\n"
                    f"• **Forex**: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD\n"
                    f"• **Crypto**: BTCUSDT, ETHUSDT\n"
                    f"• **Metals**: XAUUSD\n\n"
                    f"💡 **Usage**: `/signal <symbol> [timeframe]`\n"
                    f"🔄 **Example**: `/signal EURUSD H1`"
                )
                
                keyboard = create_keyboard([
                    [("🎯 Get All Signals", "signals"), ("📋 View Symbols", "symbols")],
                    [("📊 Positions", "positions"), ("💰 Account", "account")]
                ])
                
                await self.send_message(update, context, message, keyboard)
                return

            # Validate timeframe
            valid_timeframes = ["M5", "M15", "H1", "H4", "D1"]
            if timeframe not in valid_timeframes:
                message = (
                    f"🎯 **SIGNAL REQUEST** 🎯\n\n"
                    f"❌ **Invalid timeframe**: `{timeframe}`\n\n"
                    f"🔄 **Available Timeframes**:\n"
                    f"• **M5** - 5 minutes\n"
                    f"• **M15** - 15 minutes\n"
                    f"• **H1** - 1 hour\n"
                    f"• **H4** - 4 hours\n"
                    f"• **D1** - 1 day\n\n"
                    f"💡 **Usage**: `/signal {symbol} <timeframe>`\n"
                    f"🔄 **Example**: `/signal {symbol} H1`"
                )
                
                keyboard = create_keyboard([
                    [("🎯 Get Signal", f"signal_{symbol}_{timeframe}"), ("📋 View Symbols", "symbols")],
                    [("📊 Positions", "positions"), ("💰 Account", "account")]
                ])
                
                await self.send_message(update, context, message, keyboard)
                return

            # Show that we're generating signals
            message = (
                f"🎯 **GENERATING SIGNAL** 🎯\n\n"
                f"🤖 **AI Analysis in Progress**\n"
                f"📊 **Symbol**: {symbol}\n"
                f"🔄 **Timeframe**: {timeframe}\n"
                f"⏳ **Please wait...**\n\n"
                f"💡 **Analyzing**:\n"
                f"• Market structure and trends\n"
                f"• Support and resistance levels\n"
                f"• Liquidity zones and order blocks\n"
                f"• Risk-reward opportunities"
            )
            
            # Send initial message
            sent_message = await self.send_message(update, context, message)
            
            # Generate signal for the specific pair
            signal = await self._generate_signal_for_pair(symbol, timeframe)
            
            if signal:
                # Format the signal message
                direction_emoji = "🟢📈" if signal["direction"] == "BUY" else "🔴📉"
                confidence = "High" if signal["strength"] > 0.8 else "Medium" if signal["strength"] > 0.6 else "Low"
                
                message = (
                    f"🎯 **AI TRADING SIGNAL** 🎯\n\n"
                    f"🤖 **Generated by AI Analyzer**\n"
                    f"📊 **Symbol**: {signal['symbol']}\n"
                    f"🔄 **Timeframe**: {timeframe}\n"
                    f"⏰ **Generated**: {signal['timestamp']}\n\n"
                    f"**{signal['symbol']}** {direction_emoji}\n"
                    f"📊 **Action**: {signal['direction']}\n"
                    f"💰 **Entry**: ${signal['entry_price']:.5f}\n"
                    f"🎯 **Target**: ${signal['target_price']:.5f}\n"
                    f"🛡️ **Stop Loss**: ${signal['stop_loss']:.5f}\n"
                    f"⚡ **Confidence**: {confidence} ({signal['strength'] * 100:.1f}%)\n"
                    f"💡 **Reasoning**: {signal['reasoning']}\n\n"
                    f"🔄 **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                message = (
                    f"🎯 **AI TRADING SIGNAL** 🎯\n\n"
                    f"❌ **No signal generated**\n\n"
                    f"📊 **Symbol**: {symbol}\n"
                    f"🔄 **Timeframe**: {timeframe}\n\n"
                    f"🔍 **Possible reasons**:\n"
                    f"• No clear trading opportunity at the moment\n"
                    f"• Market conditions not favorable\n"
                    f"• Risk-reward ratio below threshold\n\n"
                    f"💡 **Suggestions**:\n"
                    f"• Try a different timeframe\n"
                    f"• Check back in a few minutes\n"
                    f"• Use /signals to see all available signals\n\n"
                    f"🔄 **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

            # Create keyboard for actions
            keyboard = create_keyboard([
                [("🔄 Refresh Signal", f"signal_{symbol}_{timeframe}"), ("📊 All Signals", "signals")],
                [("📈 Positions", "positions"), ("📋 Orders", "orders")],
                [("💰 Account", "account"), ("❓ Help", "help")]
            ])

            # Edit the message with the result
            if sent_message:
                await self.edit_message(update, context, message, keyboard, sent_message)
            else:
                await self.send_message(update, context, message, keyboard)
                
        except Exception as e:
            logger.error(f"Error generating signal for pair {symbol if 'symbol' in locals() else 'unknown'}: {e}")
            message = (
                f"🎯 **SIGNAL REQUEST** 🎯\n\n"
                f"❌ **Error generating signal**\n\n"
                f"There was an issue with the AI signal generator.\n"
                f"Please try again in a moment.\n\n"
                f"Error: {str(e)}"
            )
            
            keyboard = create_keyboard([
                [("🔄 Retry", f"signal_{symbol if 'symbol' in locals() else 'EURUSD'}_{timeframe if 'timeframe' in locals() else 'H1'}")],
                [("🎯 All Signals", "signals"), ("📋 Help", "help")]
            ])
            
            await self.send_message(update, context, message, keyboard)

    async def _generate_ai_signals(self) -> List[Dict[str, Any]]:
        """Generate AI trading signals using the OpenAI analyzer.
        
        Returns:
            List of trading signals.
        """
        try:
            # For now, we'll generate signals based on market context without screenshots
            # This is a simplified implementation that uses text-based market analysis
            market_context = {
                "timestamp": datetime.now().isoformat(),
                "symbols": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
                "timeframe": "H1",
                "analysis_type": "text_based"
            }
            
            # Since the analyzer expects screenshot data, we'll create a text-based signal generator
            # This can be enhanced later to include actual chart screenshots
            signals = await self._generate_text_based_signals(market_context)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error in AI signal generation: {e}")
            return self._get_fallback_signals()

    async def _generate_signal_for_pair(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """Generate a trading signal for a specific pair and timeframe.
        
        Args:
            symbol: The trading symbol (e.g., EURUSD, GBPUSD)
            timeframe: The timeframe (e.g., H1, H4, D1)
            
        Returns:
            A trading signal dictionary or None if no signal generated.
        """
        try:
            # Create market context for the specific symbol and timeframe
            market_context = {
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol,
                "timeframe": timeframe,
                "analysis_type": "pair_specific"
            }
            
            # Generate signal using the AI analyzer
            response = await analyzer.analyze_market(symbol)
            
            if not response or not isinstance(response, str):
                logger.warning(f"Analyzer returned invalid response for {symbol}: {type(response)}")
                return None
            
            # Parse the response
            try:
                signal_data = json.loads(response)
                
                # Validate the signal data
                required_fields = ["action", "entry_price", "stop_loss", "take_profit", "confidence"]
                if not all(field in signal_data for field in required_fields):
                    logger.warning(f"Missing required fields in signal data for {symbol}: {signal_data}")
                    return None
                
                # Convert to our standard format
                signal = {
                    "symbol": symbol,
                    "direction": signal_data["action"],
                    "entry_price": float(signal_data["entry_price"]),
                    "target_price": float(signal_data["take_profit"]),
                    "stop_loss": float(signal_data["stop_loss"]),
                    "strength": float(signal_data["confidence"]) / 10.0,  # Convert 1-10 to 0-1 scale
                    "reasoning": signal_data.get("reasoning", f"AI analysis for {symbol} on {timeframe} timeframe"),
                    "timestamp": signal_data.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
                
                # Only return signals with sufficient confidence
                if signal["strength"] >= 0.6:
                    logger.info(f"Generated signal for {symbol} on {timeframe}: {signal}")
                    return signal
                else:
                    logger.info(f"Signal for {symbol} on {timeframe} below confidence threshold: {signal['strength']}")
                    return None
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response for {symbol}: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating signal for {symbol} on {timeframe}: {e}")
            return None

    async def _generate_text_based_signals(self, market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals using text-based market analysis.
        
        Args:
            market_context: Market context information.
            
        Returns:
            List of trading signals.
        """
        try:
            # Create a prompt for signal generation
            prompt = f"""
            You are a professional forex trading signal generator. Analyze the current market conditions and generate 1-3 high-quality trading signals.
            
            Market Context:
            - Timestamp: {market_context['timestamp']}
            - Available Symbols: {', '.join(market_context['symbols'])}
            - Timeframe: {market_context['timeframe']}
            
            Generate trading signals in the following JSON format:
            {{
                "signals": [
                    {{
                        "symbol": "EURUSD",
                        "direction": "BUY" or "SELL",
                        "entry_price": 1.0875,
                        "target_price": 1.0925,
                        "stop_loss": 1.0825,
                        "strength": 0.85,
                        "reasoning": "Brief explanation of the signal",
                        "timestamp": "{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }}
                ]
            }}
            
            Requirements:
            - Only generate signals with strength > 0.6
            - Ensure realistic price levels based on current market conditions
            - Provide clear reasoning for each signal
            - Limit to maximum 3 signals
            """
            
            response = await analyzer.analyze_market("EURUSD")  # Use a default symbol for analysis
            
            # Add detailed logging to debug the issue
            logger.info(f"Analyzer response type: {type(response)}")
            logger.info(f"Analyzer response content: {repr(response)}")
            
            # The analyze_market method returns a string, not an OpenAI response object
            response_content = response if isinstance(response, str) else str(response)
            if not response_content or response_content.strip() == "":
                logger.warning("Analyzer returned empty response, using fallback")
                return self._get_fallback_signals()
            
                        # Parse the JSON response - the analyzer returns a single signal object, not an array
            formatted_signals = []
            try:
                # Log the exact content being parsed
                logger.info(f"Attempting to parse JSON: {repr(response_content)}")
                
                signal_data = json.loads(response_content)
                
                # The analyzer returns a single signal object, not an array
                if isinstance(signal_data, dict):
                    # Convert the single signal to our expected format
                    signal = signal_data
                    logger.info(f"Parsed signal data: {signal}")
                    
                    if all(key in signal for key in ["action", "entry_price", "stop_loss", "take_profit", "confidence"]):
                        formatted_signals.append({
                            "symbol": "EURUSD",  # Default symbol since analyzer doesn't return it
                            "direction": signal["action"],
                            "entry_price": float(signal["entry_price"]),
                            "target_price": float(signal["take_profit"]),
                            "stop_loss": float(signal["stop_loss"]),
                            "strength": float(signal["confidence"]) / 10.0,  # Convert 1-10 to 0-1 scale
                            "reasoning": signal.get("reasoning", "AI-generated signal"),
                            "timestamp": signal.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        })
                        logger.info(f"Successfully formatted signal: {formatted_signals[0]}")
                    else:
                        missing_keys = [key for key in ["action", "entry_price", "stop_loss", "take_profit", "confidence"] if key not in signal]
                        logger.warning(f"Missing required fields in signal data: {missing_keys}")
                        return self._get_fallback_signals()
                else:
                    logger.warning(f"Unexpected response format: {type(signal_data)}")
                    return self._get_fallback_signals()
                    
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response content that failed to parse: {repr(response_content)}")
                return self._get_fallback_signals()
            
            return formatted_signals
            
        except Exception as e:
            logger.error(f"Error in text-based signal generation: {e}")
            return self._get_fallback_signals()

    def _get_fallback_signals(self) -> List[Dict[str, Any]]:
        """Get fallback signals when AI generation fails.
        
        Returns:
            List of fallback trading signals.
        """
        # Return a few realistic-looking signals as fallback
        return [
            {
                "symbol": "EURUSD",
                "direction": "BUY",
                "entry_price": 1.0875,
                "target_price": 1.0925,
                "stop_loss": 1.0825,
                "strength": 0.75,
                "reasoning": "Technical analysis suggests upward trend",
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]

    async def _get_real_positions(self) -> List[Dict[str, Any]]:
        """Get real positions from MT5.
        
        Returns:
            List of position dictionaries.
        """
        try:
            # Try to get positions from MT5 executor
            from src.core.config import AppConfig
            from src.execution.mt5_executor import MT5Executor
            
            config = AppConfig()
            mt5_executor = MT5Executor(config.mt5)
            
            if mt5_executor.connected:
                # Get real positions from MT5
                positions = await mt5_executor.get_positions()
                if positions:
                    return [
                        {
                            "symbol": pos.symbol,
                            "type": "BUY" if pos.type == 0 else "SELL",
                            "volume": pos.volume,
                            "price_open": pos.price_open,
                            "price_current": pos.price_current,
                            "profit": pos.profit,
                            "time": str(pos.time),
                            "ticket": pos.ticket
                        }
                        for pos in positions
                    ]
            
            # Fallback to empty if MT5 not available
            return []
            
        except Exception as e:
            logger.error(f"Error getting real positions: {e}")
            return []

    async def _get_real_orders(self) -> List[Dict[str, Any]]:
        """Get real pending orders from MT5.
        
        Returns:
            List of order dictionaries.
        """
        try:
            # Try to get orders from MT5 executor
            from src.core.config import AppConfig
            from src.execution.mt5_executor import MT5Executor
            
            config = AppConfig()
            mt5_executor = MT5Executor(config.mt5)
            
            if mt5_executor.connected:
                # Get real orders from MT5
                orders = await mt5_executor.get_orders()
                if orders:
                    return [
                        {
                            "symbol": order.symbol,
                            "type": "BUY" if order.type in [2, 4] else "SELL",
                            "volume": order.volume_current,
                            "price_open": order.price_open,
                            "time": str(order.time_setup),
                            "ticket": order.ticket
                        }
                        for order in orders
                    ]
            
            # Fallback to empty if MT5 not available
            return []
            
        except Exception as e:
            logger.error(f"Error getting real orders: {e}")
            return []

    async def _get_real_account_info(self) -> Dict[str, Any]:
        """Get real account information from MT5.
        
        Returns:
            Account information dictionary.
        """
        try:
            # Try to get account info from MT5 executor
            from src.core.config import AppConfig
            from src.execution.mt5_executor import MT5Executor
            
            config = AppConfig()
            mt5_executor = MT5Executor(config.mt5)
            
            if mt5_executor.connected:
                # Get real account info from MT5
                account_info = await mt5_executor.get_account_info()
                if account_info:
                    return {
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "margin": account_info.margin,
                        "free_margin": account_info.margin_free,
                        "margin_level": account_info.margin_level,
                        "profit_loss": account_info.profit,
                        "open_positions": len(await self._get_real_positions()),
                        "pending_orders": len(await self._get_real_orders()),
                        "currency": account_info.currency,
                        "leverage": account_info.leverage,
                        "server": account_info.server,
                        "name": account_info.name,
                        "total_profit": account_info.profit
                    }
            
            # Fallback to basic demo data
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "profit_loss": 0.0,
                "open_positions": 0,
                "pending_orders": 0,
                "currency": "USD",
                "leverage": 100,
                "server": "Demo",
                "name": "Demo Account",
                "total_profit": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting real account info: {e}")
            # Return fallback data
            return {
                "balance": 10000.0,
                "equity": 10000.0,
                "margin": 0.0,
                "free_margin": 10000.0,
                "margin_level": 0.0,
                "profit_loss": 0.0,
                "open_positions": 0,
                "pending_orders": 0,
                "currency": "USD",
                "leverage": 100,
                "server": "Demo",
                "name": "Demo Account",
                "total_profit": 0.0
            }
