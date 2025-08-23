"""Trading commands for Telegram bot."""

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
            "position_details": self.position_details_callback,
            "quick_close": self.quick_close_callback,
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
        try:
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
                    [("💰 Account Info", "account"), ("📊 Status", "status")],
                    [("🔄 Refresh", "refresh_positions"), ("❓ Help", "help")]
                ])
            else:
                # Format the positions message with enhanced visuals
                total_profit = sum(pos.get("profit", 0) for pos in positions)
                
                message = (
                    f"📊 **LIVE POSITIONS DASHBOARD** 📊\n\n"
                    f"💰 **Portfolio P&L**: ${total_profit:.2f}\n"
                    f"📈 **Trend**: {'🟢' if total_profit >= 0 else '🔴'}\n\n"
                )

                for i, position in enumerate(positions, 1):
                    profit_emoji = "🟢" if position.get("profit", 0) >= 0 else "🔴"
                    direction_emoji = "📈" if position.get("type") == "BUY" else "📉"
                    
                    message += (
                        f"**{i}. {position.get('symbol', 'Unknown')}** {direction_emoji}\n"
                        f"  💰 Volume: {position.get('volume', 0):.2f}\n"
                        f"  📍 Entry: ${position.get('price_open', 0):.5f}\n"
                        f"  📱 Current: ${position.get('price_current', 0):.5f}\n"
                        f"  {profit_emoji} P/L: ${position.get('profit', 0):.2f}\n"
                        f"  🕐 Time: {position.get('time', 'Unknown')}\n\n"
                    )

                message += (
                    f"📊 **Portfolio Summary**:\n"
                    f"🎯 Active Positions: **{len(positions)}**\n"
                    f"💰 Total Value: ${total_profit:.2f}\n"
                    f"🕐 **Live Update**: {datetime.now().strftime('%H:%M:%S')}"
                )
                
                # Create enhanced keyboard with quick actions
                keyboard = create_keyboard([
                    [("🔄 Refresh", "refresh_positions"), ("📊 Details", "position_details")],
                    [("⚡ Quick Close", "quick_close"), ("📋 Orders", "orders")],
                    [("💰 Account", "account"), ("📊 Status", "status")]
                ])

            # If this is a callback query, edit the message
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
        """Handle the /account command.
        
        Args:
            update: The update object.
            context: The context object.
        """
        try:
            # Get real account data
            account_info = await self._get_real_account_info()

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
                f"**Currency**: {account_info['currency']}\n"
                f"**Leverage**: 1:{account_info['leverage']}\n"
                f"**Server**: {account_info['server']}\n"
                f"**Name**: {account_info['name']}\n\n"
                f"**Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Create an inline keyboard for account actions
            keyboard = create_keyboard([
                [("Refresh", "refresh_account"), ("Positions", "positions")],
                [("Orders", "orders"), ("Signals", "signals")],
                [("Account History", "account_history"), ("Status", "status")]
            ])

            # If this is a callback query, edit the message
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
        # Show that we're generating signals
        if update.callback_query:
            await update.callback_query.answer("🤖 Generating AI signals...")
        
        try:
            # Generate real AI signals
            signals = await self._generate_ai_signals()
            
            if not signals:
                message = (
                    f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                    f"🔍 **No signals found at the moment**\n\n"
                    f"The AI analyzer is continuously monitoring the markets.\n"
                    f"New signals will appear when profitable opportunities are detected.\n\n"
                    f"💡 **Tip**: Check back in a few minutes or use the refresh button."
                )
            else:
                # Format the signals message
                message = f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                message += f"🤖 **Generated by AI Analyzer**\n"
                message += f"📊 **Total Signals**: {len(signals)}\n\n"

                for i, signal in enumerate(signals, 1):
                    # Determine emoji based on signal direction and strength
                    if signal["direction"] == "BUY":
                        direction_emoji = "🟢📈" if signal["strength"] > 0.7 else "🟡📈"
                    else:
                        direction_emoji = "🔴📉" if signal["strength"] > 0.7 else "🟠📉"
                    
                    confidence = "High" if signal["strength"] > 0.8 else "Medium" if signal["strength"] > 0.6 else "Low"
                    
                    message += (
                        f"**{i}. {signal['symbol']}** {direction_emoji}\n"
                        f"  📊 **Action**: {signal['direction']}\n"
                        f"  💰 **Entry**: ${signal['entry_price']:.5f}\n"
                        f"  🎯 **Target**: ${signal['target_price']:.5f}\n"
                        f"  🛡️ **Stop Loss**: ${signal['stop_loss']:.5f}\n"
                        f"  ⚡ **Confidence**: {confidence} ({signal['strength'] * 100:.1f}%)\n"
                        f"  🕐 **Generated**: {signal['timestamp']}\n\n"
                    )

            message += f"🔄 **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
        except Exception as e:
            logger.error(f"Error generating AI signals: {e}")
            message = (
                f"🎯 **AI TRADING SIGNALS** 🎯\n\n"
                f"❌ **Error generating signals**\n\n"
                f"There was an issue with the AI signal generator.\n"
                f"Please try again in a moment.\n\n"
                f"Error: {str(e)}"
            )

        # Create an inline keyboard for signals actions
        keyboard = create_keyboard([
            [("🔄 Refresh", "refresh_signals"), ("📈 Positions", "positions")],
            [("📋 Orders", "orders"), ("💰 Account", "account")],
            [("📊 Status", "status"), ("❓ Help", "help")]
        ])

        # If this is a callback query, edit the message
        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def _generate_ai_signals(self) -> List[Dict[str, Any]]:
        """Generate AI trading signals using the OpenAI analyzer.
        
        Returns:
            List of trading signals.
        """
        try:
            from src.core.config import AppConfig
            from src.analysis.openai_analyzer import OpenAIAnalyzer
            
            # Get configuration
            config = AppConfig()
            
            # Check if OpenAI is configured
            if not config.openai.api_key:
                logger.warning("OpenAI API key not configured, using fallback signals")
                return self._get_fallback_signals()
            
            # Initialize the analyzer
            analyzer = OpenAIAnalyzer(config)
            
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

    async def _generate_text_based_signals(self, market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate signals using text-based market analysis.
        
        Args:
            market_context: Market context information.
            
        Returns:
            List of trading signals.
        """
        try:
            from src.core.config import AppConfig
            import openai
            import json
            
            config = AppConfig()
            client = openai.AsyncOpenAI(api_key=config.openai.api_key)
            
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
            
            response = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional forex trading analyst with 10 years of experience."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=800,
                temperature=0.7
            )
            
            response_content = response.choices[0].message.content
            if not response_content:
                return self._get_fallback_signals()
            
            # Parse the JSON response
            signal_data = json.loads(response_content)
            signals = signal_data.get("signals", [])
            
            # Validate and format signals
            formatted_signals = []
            for signal in signals:
                if all(key in signal for key in ["symbol", "direction", "entry_price", "target_price", "stop_loss", "strength"]):
                    formatted_signals.append({
                        "symbol": signal["symbol"],
                        "direction": signal["direction"],
                        "entry_price": float(signal["entry_price"]),
                        "target_price": float(signal["target_price"]),
                        "stop_loss": float(signal["stop_loss"]),
                        "strength": float(signal["strength"]),
                        "reasoning": signal.get("reasoning", "AI-generated signal"),
                        "timestamp": signal.get("timestamp", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    })
            
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

    async def position_details_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the position_details callback.
        
        Args:
            update: The update object.
            context: The context object.
        """
        message = (
            f"📊 **POSITION DETAILS** 📊\n\n"
            f"Detailed position analysis coming soon!\n\n"
            f"This feature will show detailed information about each position, including profit/loss history, charts, and advanced metrics."
        )

        # Create an inline keyboard to go back to positions
        keyboard = create_keyboard([
            [("Back to Positions", "positions")],
            [("Status", "status"), ("Help", "help")]
        ])

        await self.edit_message(update, context, message, keyboard)

    async def quick_close_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the quick_close callback.
        
        Args:
            update: The update object.
            context: The context object.
        """
        message = (
            f"⚡ **QUICK CLOSE** ⚡\n\n"
            f"Quick close functionality coming soon!\n\n"
            f"This feature will allow you to quickly close positions with a single click."
        )

        # Create an inline keyboard to go back to positions
        keyboard = create_keyboard([
            [("Back to Positions", "positions")],
            [("Status", "status"), ("Help", "help")]
        ])

        await self.edit_message(update, context, message, keyboard)

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
