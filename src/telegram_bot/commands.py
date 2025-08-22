"""Command Handler for Telegram bot commands and queries."""

import asyncio
import logging
import os
import sys
import psutil
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone, timedelta

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from .notifications import NotificationManager

logger = get_logger(__name__)


class CommandHandler:
    """Handles Telegram bot commands and queries."""

    def __init__(self, notification_manager: NotificationManager):
        self.notification_manager = notification_manager
        self.mock_data = self._setup_mock_data()

    async def start_command(self, update, context):
        """Handle /start command."""
        welcome_text = (
            "🤖 *Welcome to AI Trading Bot!*\n\n"
            "I'm your smart trading assistant, ready to help you monitor and manage your trading activities.\n\n"
            "*Quick Actions:*\n"
            "📊 /status - System Status\n"
            "📈 /positions - Open Positions\n"
            "💼 /account - Account Info\n"
            "🎯 /signals - Trading Signals\n"
            "⚠️ /risk - Risk Metrics\n"
            "⚙️ /settings - Bot Settings\n\n"
            "Type /help for detailed information about all features."
        )
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("📈 Positions", callback_data="positions")
            ],
            [
                InlineKeyboardButton("💼 Account", callback_data="account"),
                InlineKeyboardButton("📋 Orders", callback_data="orders")
            ],
            [
                InlineKeyboardButton("🎯 Signals", callback_data="signals"),
                InlineKeyboardButton("⚠️ Risk", callback_data="risk")
            ],
            [
                InlineKeyboardButton("🖥️ Monitor", callback_data="monitor"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def help_command(self, update, context):
        """Handle /help command."""
        help_text = (
            "📚 *AI Trading Bot Help*\n\n"
            "*Trading Commands:*\n"
            "📈 /positions - View and manage your open positions\n"
            "📋 /orders - View pending orders\n"
            "🎯 /signals - Check latest AI-generated trading signals\n"
            "📊 /performance - View your trading performance\n\n"
            "*Account Commands:*\n"
            "💼 /account - View account information and balance\n"
            "📝 /journal - View trading journal entries\n\n"
            "*Monitoring Commands:*\n"
            "🔄 /status - Check all system components\n"
            "⚠️ /risk - Monitor risk metrics and exposure\n"
            "🖥️ /monitor - View system resource usage\n\n"
            "*Settings & Info:*\n"
            "⚙️ /settings - Configure bot preferences\n"
            "ℹ️ /about - Information about the bot\n\n"
            "*Tips:*\n"
            "• Use the inline buttons for quick navigation\n"
            "• Enable notifications for real-time alerts\n"
            "• Check /risk regularly to monitor exposure\n\n"
            "Need more help? Visit our [Documentation](https://github.com/oyi77/telegram-ai-trade/docs)"
        )
        
        # Add quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("📈 Open Positions", callback_data="positions"),
                InlineKeyboardButton("🎯 Latest Signals", callback_data="signals")
            ],
            [
                InlineKeyboardButton("💼 Account", callback_data="account"),
                InlineKeyboardButton("⚠️ Risk", callback_data="risk")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
                InlineKeyboardButton("📊 Status", callback_data="status")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            help_text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

    async def status_command(self, update, context):
        """Handle /status command."""
        status = self.mock_data["system_status"]
        
        def get_status_emoji(status):
            return "✅" if status == "Online" else "❌" if status == "Offline" else "⚠️"
        
        status_text = (
            "�️ *System Status Dashboard*\n\n"
            f"{get_status_emoji(status['bot_status'])} *Trading Bot:* {status['bot_status']}\n"
            f"{get_status_emoji(status['mt5_connection'])} *MT5 Connection:* {status['mt5_connection']}\n"
            f"{get_status_emoji(status['ai_analyzer'])} *AI Analyzer:* {status['ai_analyzer']}\n"
            f"{get_status_emoji(status['risk_manager'])} *Risk Manager:* {status['risk_manager']}\n\n"
            f"🕒 *Last Updated:* {status['last_update']}\n\n"
            "Select an action below to manage your trading:"
        )
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_status"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("📈 View Positions", callback_data="positions"),
                InlineKeyboardButton("⚠️ Risk Metrics", callback_data="risk")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            status_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def positions_command(self, update, context):
        """Handle /positions command."""
        if not self.mock_data["positions"]:
            no_positions_text = (
                "📊 *Positions Overview*\n\n"
                "No open positions at the moment.\n\n"
                "Use /signals to check for new trading opportunities!"
            )
            keyboard = [
                [
                    InlineKeyboardButton("🎯 View Signals", callback_data="signals"),
                    InlineKeyboardButton("📊 Performance", callback_data="performance")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                no_positions_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return

        # Calculate total P/L
        total_pl = sum(pos['profit'] for pos in self.mock_data["positions"])
        
        positions_text = (
            "� *Open Positions Overview*\n\n"
            f"Total P/L: {'🟢' if total_pl >= 0 else '🔴'} ${abs(total_pl):.2f}\n"
            f"Active Positions: {len(self.mock_data['positions'])}\n\n"
        )
        
        for pos in self.mock_data["positions"]:
            profit_emoji = "🟢" if pos['profit'] >= 0 else "🔴"
            direction_emoji = "📈" if pos['type'] == "BUY" else "📉"
            
            positions_text += (
                f"{direction_emoji} *{pos['symbol']}* ({pos['type']})\n"
                f"💰 Volume: {pos['volume']}\n"
                f"📍 Entry: ${pos['price_open']:.5f}\n"
                f"📱 Current: ${pos['price_current']:.5f}\n"
                f"{profit_emoji} P/L: ${abs(pos['profit']):.2f}\n"
                f"⏱️ Opened: {pos['time']}\n"
                f"➖➖➖➖➖➖➖➖➖➖\n\n"
            )
        
        # Add action buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_positions"),
                InlineKeyboardButton("📊 Charts", callback_data="charts")
            ],
            [
                InlineKeyboardButton("⚠️ Risk Analysis", callback_data="risk"),
                InlineKeyboardButton("📈 Performance", callback_data="performance")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            positions_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def signals_command(self, update, context):
        """Handle /signals command."""
        # Mock some example signals - in real implementation, get from signal service
        signals = self.mock_data.get("signals", [])
        
        if not signals:
            signals_text = (
                "🎯 *Trading Signals*\n\n"
                "No active signals at the moment.\n\n"
                "The AI analyzer continuously monitors the markets and will "
                "notify you when new opportunities arise.\n\n"
                "*Signal Types:*\n"
                "🟢 Strong Buy\n"
                "🟡 Potential Buy\n"
                "🔴 Strong Sell\n"
                "🟠 Potential Sell"
            )
        else:
            signals_text = "🎯 *Latest Trading Signals*\n\n"
            
            for signal in signals:
                # Add appropriate emoji based on signal type and strength
                direction_emoji = "🟢" if signal["direction"] == "BUY" else "🔴"
                strength_emoji = "💪" if signal["strength"] > 0.7 else "⚡"
                
                signals_text += (
                    f"{direction_emoji} *{signal['symbol']}*\n"
                    f"{strength_emoji} Signal Strength: {signal['strength']*100:.1f}%\n"
                    f"📊 Entry Zone: ${signal['entry_price']:.5f}\n"
                    f"🎯 Target: ${signal['target_price']:.5f}\n"
                    f"⚠️ Stop Loss: ${signal['stop_loss']:.5f}\n"
                    f"⏰ Time: {signal['timestamp']}\n"
                    f"➖➖➖➖➖➖➖➖➖➖\n\n"
                )
        
        # Add interactive buttons
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_signals"),
                InlineKeyboardButton("📊 Analysis", callback_data="analysis")
            ],
            [
                InlineKeyboardButton("⚙️ Signal Settings", callback_data="signal_settings"),
                InlineKeyboardButton("📈 Market Overview", callback_data="market_overview")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            signals_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def risk_command(self, update, context):
        """Handle /risk command."""
        risk = self.mock_data["risk_metrics"]
        perf = self.mock_data["performance"]
        
        def get_risk_indicator(value, threshold):
            if value <= threshold * 0.5:
                return "🟢"  # Safe
            elif value <= threshold * 0.8:
                return "🟡"  # Warning
            else:
                return "🔴"  # Danger
        
        risk_text = (
            "⚠️ *Risk Management Dashboard*\n\n"
            "*Account Health:*\n"
            f"{get_risk_indicator(risk['margin_used_pct'], 70)} Margin Used: {risk['margin_used_pct']}%\n"
            f"{get_risk_indicator(risk['daily_drawdown'], 5)} Daily Drawdown: {risk['daily_drawdown']}%\n"
            f"{get_risk_indicator(risk['exposure_level'], 80)} Total Exposure: {risk['exposure_level']}%\n\n"
            
            "*Position Risk:*\n"
            f"📊 Open Positions: {risk['open_positions']}\n"
            f"💰 Total Position Value: ${risk['total_position_value']:,.2f}\n"
            f"📉 Max Drawdown: {risk['max_drawdown']}%\n\n"
            
            "*Performance Metrics:*\n"
            f"📈 Win Rate: {perf['win_rate']}%\n"
            f"⚖️ Risk/Reward: {perf['risk_reward_ratio']:.2f}\n"
            f"💵 Profit Factor: {perf['profit_factor']:.2f}\n\n"
            
            "*Risk Limits Status:*\n"
            "✅ Daily Loss Limit: Active\n"
            "✅ Position Size Limit: Active\n"
            "✅ Drawdown Protection: Active"
            f"Win Rate: {perf['win_rate']}%\n"
            f"Profit Factor: {perf['profit_factor']}\n"
            f"Current Drawdown: {risk['current_drawdown']}%\n"
            f"Max Drawdown: {perf['max_drawdown']}%\n"
            f"Sharpe Ratio: {perf['sharpe_ratio']}\n"
        )
        await update.message.reply_text(risk_text)

    async def settings_command(self, update, context):
        """Handle /settings command."""
        settings_text = (
            "⚙️ Bot Settings\n\n"
            "Use these commands to configure:\n\n"
            "• /risk_limit - Set risk per trade\n"
            "• /drawdown_limit - Set max drawdown\n"
            "• /notifications - Configure alerts\n"
            "• /timezone - Set your timezone\n"
        )
        await update.message.reply_text(settings_text)

    async def handle_callback(self, update, context):
        """Handle callback queries from inline buttons."""
        query = update.callback_query
        try:
            # Show the user we're processing their action
            await query.answer("Processing...")
            
            if query.data == "refresh_status":
                await self.status_command(update, context)
            elif query.data == "settings":
                await self.settings_command(update, context)
            elif query.data == "positions":
                await self.positions_command(update, context)
            elif query.data == "risk":
                await self.risk_command(update, context)
            elif query.data == "help":
                await self.help_command(update, context)
            elif query.data == "signals":
                await self.signals_command(update, context)
            elif query.data == "refresh_positions":
                await self.positions_command(update, context)
            elif query.data == "refresh_signals":
                await self.signals_command(update, context)
            elif query.data == "performance":
                await self.performance_command(update, context)
            elif query.data == "status":
                await self.status_command(update, context)
            elif query.data == "orders":
                await self.orders_command(update, context)
            elif query.data == "account":
                await self.account_command(update, context)
            elif query.data == "refresh_account":
                await self.account_command(update, context)
            elif query.data == "account_history":
                # For now, just show a message that this feature is coming soon
                await query.edit_message_text(
                    "📊 *Account History*\n\nThis feature is coming soon in the next update.",
                    parse_mode='Markdown'
                )
            elif query.data == "monitor":
                await self.monitor_command(update, context)
            elif query.data == "refresh_monitor":
                await self.monitor_command(update, context)
            elif query.data.startswith("risk_"):
                value = query.data.split("_")[1]
                await query.edit_message_text(f"Risk limit set to {value}%")
            elif query.data.startswith("drawdown_"):
                value = query.data.split("_")[1]
                await query.edit_message_text(f"Max drawdown limit set to {value}%")
            elif query.data.startswith("notify_"):
                option = query.data.split("_")[1]
                await query.edit_message_text(f"Notifications {option} configured")
            else:
                logger.warning(f"Unknown callback data: {query.data}")
                await query.edit_message_text("Sorry, this action is not available.")
                
        except Exception as e:
            logger.error(f"Error handling callback query: {e}")
            await query.edit_message_text("Sorry, an error occurred while processing your request.")

    def _setup_mock_data(self) -> Dict:
        """Setup mock data for demonstration purposes."""
        return {
            "system_status": {
                "bot_status": "🟢 RUNNING",
                "mt5_connection": "🟢 CONNECTED",
                "ai_analyzer": "🟢 ACTIVE",
                "risk_manager": "🟢 ACTIVE",
                "last_update": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
            },
            "positions": [
                {
                    "ticket": 12345,
                    "symbol": "XAUUSD",
                    "type": "BUY",
                    "volume": 0.1,
                    "price_open": 2345.50,
                    "price_current": 2350.25,
                    "profit": 47.50,
                    "swap": -2.50,
                    "time": "2024-01-15 10:30:00",
                },
                {
                    "ticket": 12346,
                    "symbol": "EURUSD",
                    "type": "SELL",
                    "volume": 0.05,
                    "price_open": 1.0850,
                    "price_current": 1.0830,
                    "profit": 10.00,
                    "swap": -1.25,
                    "time": "2024-01-15 11:15:00",
                },
            ],
            "orders": [
                {
                    "ticket": 12347,
                    "symbol": "GBPUSD",
                    "type": "BUY_LIMIT",
                    "volume": 0.1,
                    "price": 1.2650,
                    "sl": 1.2600,
                    "tp": 1.2750,
                    "time": "2024-01-15 12:00:00",
                }
            ],
            "performance": {
                "total_trades": 45,
                "winning_trades": 28,
                "losing_trades": 17,
                "win_rate": 62.2,
                "total_pnl": 1250.75,
                "max_drawdown": 3.2,
                "sharpe_ratio": 1.85,
                "profit_factor": 2.1,
            },
            "risk_metrics": {
                "current_drawdown": 1.8,
                "max_daily_drawdown": 4.5,
                "open_risk": 2.1,
                "correlation_exposure": 0.35,
                "position_count": 2,
                "daily_pnl": 125.50,
                "risk_per_trade": 2.0,
            },
            "settings": {
                "notifications": {
                    "signals": "✅ Enabled",
                    "positions": "✅ Enabled",
                    "risk": "✅ Enabled",
                    "performance": "✅ Enabled",
                    "system": "✅ Enabled",
                },
                "risk_limits": {
                    "max_risk_per_trade": "2.0%",
                    "max_daily_drawdown": "6.0%",
                    "max_open_positions": "10",
                    "max_correlation": "70%",
                },
                "trading_hours": {
                    "london_session": "07:00-16:00 UTC",
                    "new_york_session": "12:00-21:00 UTC",
                    "asian_session": "23:00-08:00 UTC",
                },
            },
            "journal": [
                {
                    "date": "2024-01-15",
                    "trades": [
                        {
                            "time": "10:30:00",
                            "symbol": "XAUUSD",
                            "action": "BUY",
                            "volume": 0.1,
                            "price": 2345.50,
                            "sl": 2340.00,
                            "tp": 2355.00,
                            "status": "OPEN",
                            "pnl": 47.50,
                        },
                        {
                            "time": "11:15:00",
                            "symbol": "EURUSD",
                            "action": "SELL",
                            "volume": 0.05,
                            "price": 1.0850,
                            "sl": 1.0880,
                            "tp": 1.0800,
                            "status": "OPEN",
                            "pnl": 10.00,
                        },
                    ],
                    "daily_pnl": 57.50,
                    "trades_count": 2,
                }
            ],
        }

    async def get_system_status(self) -> str:
        """Get system status information."""
        try:
            status = self.mock_data["system_status"]

            message = (
                "📊 **SYSTEM STATUS** 📊\n\n"
                f"🤖 **Bot Status**: {status['bot_status']}\n"
                f"🔗 **MT5 Connection**: {status['mt5_connection']}\n"
                f"🧠 **AI Analyzer**: {status['ai_analyzer']}\n"
                f"🛡️ **Risk Manager**: {status['risk_manager']}\n\n"
                f"⏰ **Last Update**: {status['last_update']}\n\n"
                "🟢 All systems operational"
            )

            return message

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return "❌ Failed to get system status"

    async def get_positions(self) -> str:
        """Get current open positions."""
        try:
            positions = self.mock_data["positions"]

            if not positions:
                return "📊 **OPEN POSITIONS** 📊\n\nNo open positions at the moment."

            message = "📊 **OPEN POSITIONS** 📊\n\n"

            total_pnl = 0
            for pos in positions:
                pnl = pos["profit"]
                total_pnl += pnl
                pnl_emoji = "🟢" if pnl >= 0 else "🔴"

                message += (
                    f"📈 **{pos['symbol']}** ({pos['type']})\n"
                    f"🎫 Ticket: {pos['ticket']}\n"
                    f"📊 Volume: {pos['volume']}\n"
                    f"💰 Open Price: {pos['price_open']}\n"
                    f"📊 Current Price: {pos['price_current']}\n"
                    f"{pnl_emoji} P&L: ${pnl:.2f}\n"
                    f"⏰ Time: {pos['time']}\n\n"
                )

            message += f"💵 **Total P&L**: ${total_pnl:.2f}"

            return message

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return "❌ Failed to get positions"

    async def get_orders(self) -> str:
        """Get pending orders."""
        try:
            orders = self.mock_data["orders"]

            if not orders:
                return "📋 **PENDING ORDERS** 📋\n\nNo pending orders at the moment."

            message = "📋 **PENDING ORDERS** 📋\n\n"

            for order in orders:
                message += (
                    f"📈 **{order['symbol']}** ({order['type']})\n"
                    f"🎫 Ticket: {order['ticket']}\n"
                    f"📊 Volume: {order['volume']}\n"
                    f"💰 Price: {order['price']}\n"
                    f"🛑 Stop Loss: {order['sl']}\n"
                    f"🎯 Take Profit: {order['tp']}\n"
                    f"⏰ Time: {order['time']}\n\n"
                )

            return message

        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return "❌ Failed to get orders"

    async def get_performance(self) -> str:
        """Get trading performance metrics."""
        try:
            perf = self.mock_data["performance"]

            message = (
                "📈 **TRADING PERFORMANCE** 📈\n\n"
                f"📊 **Total Trades**: {perf['total_trades']}\n"
                f"✅ **Winning Trades**: {perf['winning_trades']}\n"
                f"❌ **Losing Trades**: {perf['losing_trades']}\n"
                f"🎯 **Win Rate**: {perf['win_rate']}%\n\n"
                f"💰 **Total P&L**: ${perf['total_pnl']:.2f}\n"
                f"📉 **Max Drawdown**: {perf['max_drawdown']}%\n"
                f"📊 **Sharpe Ratio**: {perf['sharpe_ratio']:.2f}\n"
                f"📈 **Profit Factor**: {perf['profit_factor']:.2f}\n\n"
                f"⏰ **Last Updated**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            return message

        except Exception as e:
            logger.error(f"Error getting performance: {e}")
            return "❌ Failed to get performance data"

    async def get_risk_metrics(self) -> str:
        """Get risk metrics and alerts."""
        try:
            risk = self.mock_data["risk_metrics"]

            # Determine risk level
            if risk["current_drawdown"] > 4.0:
                risk_level = "🔴 HIGH"
            elif risk["current_drawdown"] > 2.0:
                risk_level = "🟡 MEDIUM"
            else:
                risk_level = "🟢 LOW"

            message = (
                "🛡️ **RISK METRICS** 🛡️\n\n"
                f"⚠️ **Risk Level**: {risk_level}\n\n"
                f"📉 **Current Drawdown**: {risk['current_drawdown']}%\n"
                f"📊 **Max Daily Drawdown**: {risk['max_daily_drawdown']}%\n"
                f"💰 **Open Risk**: {risk['open_risk']}%\n"
                f"🔗 **Correlation Exposure**: {risk['correlation_exposure']:.1%}\n\n"
                f"📊 **Position Count**: {risk['position_count']}\n"
                f"💵 **Daily P&L**: ${risk['daily_pnl']:.2f}\n"
                f"🎯 **Risk Per Trade**: {risk['risk_per_trade']}%\n\n"
                f"⏰ **Last Updated**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            return message

        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return "❌ Failed to get risk metrics"

    async def get_settings(self) -> str:
        """Get bot settings and configuration."""
        try:
            settings = self.mock_data["settings"]

            message = "⚙️ **BOT SETTINGS** ⚙️\n\n"

            # Notifications
            message += "🔔 **Notifications**\n"
            for notif_type, status in settings["notifications"].items():
                message += f"• {notif_type.title()}: {status}\n"

            message += "\n🛡️ **Risk Limits**\n"
            for limit_type, value in settings["risk_limits"].items():
                message += f"• {limit_type.replace('_', ' ').title()}: {value}\n"

            message += "\n🕐 **Trading Hours**\n"
            for session, hours in settings["trading_hours"].items():
                message += f"• {session.replace('_', ' ').title()}: {hours}\n"

            message += f"\n⏰ **Last Updated**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"

            return message

        except Exception as e:
            logger.error(f"Error getting settings: {e}")
            return "❌ Failed to get settings"

    async def get_trading_journal(self) -> str:
        """Get trading journal entries."""
        try:
            journal = self.mock_data["journal"]

            if not journal:
                return "📖 **TRADING JOURNAL** 📖\n\nNo journal entries available."

            message = "📖 **TRADING JOURNAL** 📖\n\n"

            for entry in journal:
                message += f"📅 **{entry['date']}**\n"
                message += f"📊 Trades: {entry['trades_count']}\n"
                message += f"💵 Daily P&L: ${entry['daily_pnl']:.2f}\n\n"

                for trade in entry["trades"]:
                    status_emoji = "🟢" if trade["status"] == "OPEN" else "🔒"
                    pnl_emoji = "🟢" if trade["pnl"] >= 0 else "🔴"

                    message += (
                        f"{status_emoji} **{trade['symbol']}** ({trade['action']})\n"
                        f"⏰ Time: {trade['time']}\n"
                        f"📊 Volume: {trade['volume']}\n"
                        f"💰 Price: {trade['price']}\n"
                        f"🛑 SL: {trade['sl']}\n"
                        f"🎯 TP: {trade['tp']}\n"
                        f"{pnl_emoji} P&L: ${trade['pnl']:.2f}\n\n"
                    )

            return message

        except Exception as e:
            logger.error(f"Error getting trading journal: {e}")
            return "❌ Failed to get trading journal"

    async def get_recent_signals(self, limit: int = 5) -> str:
        """Get recent trading signals."""
        try:
            # Mock recent signals
            signals = [
                {
                    "time": "14:30:00",
                    "symbol": "XAUUSD",
                    "bias": "BULLISH",
                    "confidence": 85,
                    "entry_zone": "2340-2345",
                    "sl": "2335",
                    "tp1": "2355",
                    "tp2": "2370",
                },
                {
                    "time": "13:15:00",
                    "symbol": "EURUSD",
                    "bias": "BEARISH",
                    "confidence": 72,
                    "entry_zone": "1.0880-1.0890",
                    "sl": "1.0910",
                    "tp1": "1.0850",
                    "tp2": "1.0820",
                },
            ]

            if not signals:
                return "📡 **RECENT SIGNALS** 📡\n\nNo recent signals available."

            message = "📡 **RECENT SIGNALS** 📡\n\n"

            for signal in signals[:limit]:
                confidence_emoji = "🟢" if signal["confidence"] >= 80 else "🟡"

                message += (
                    f"{confidence_emoji} **{signal['symbol']}** ({signal['bias']})\n"
                    f"⏰ Time: {signal['time']}\n"
                    f"💯 Confidence: {signal['confidence']}%\n"
                    f"🎯 Entry Zone: {signal['entry_zone']}\n"
                    f"🛑 Stop Loss: {signal['sl']}\n"
                    f"🎯 TP1: {signal['tp1']}\n"
                    f"🎯 TP2: {signal['tp2']}\n\n"
                )

            return message

        except Exception as e:
            logger.error(f"Error getting recent signals: {e}")
            return "❌ Failed to get recent signals"

    async def get_market_analysis(self) -> str:
        """Get current market analysis."""
        try:
            # Mock market analysis
            analysis = {
                "overall_bias": "BULLISH",
                "key_levels": {
                    "XAUUSD": {"support": "2340", "resistance": "2370"},
                    "EURUSD": {"support": "1.0820", "resistance": "1.0890"},
                    "GBPUSD": {"support": "1.2600", "resistance": "1.2750"},
                },
                "volatility": "MEDIUM",
                "session": "LONDON",
            }

            message = (
                "📊 **MARKET ANALYSIS** 📊\n\n"
                f"🎯 **Overall Bias**: {analysis['overall_bias']}\n"
                f"📈 **Volatility**: {analysis['volatility']}\n"
                f"🕐 **Active Session**: {analysis['session']}\n\n"
                "🔑 **Key Levels**\n"
            )

            for symbol, levels in analysis["key_levels"].items():
                message += (
                    f"• **{symbol}**\n"
                    f"  📉 Support: {levels['support']}\n"
                    f"  📈 Resistance: {levels['resistance']}\n\n"
                )

            message += f"⏰ **Analysis Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"

            return message

        except Exception as e:
            logger.error(f"Error getting market analysis: {e}")
            return "❌ Failed to get market analysis"
            
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle general text messages."""
        try:
            message = update.message.text.lower()

            if "hello" in message or "hi" in message:
                await update.message.reply_text(
                    "👋 Hello! How can I help you today? Use /help to see available commands."
                )
            elif "how are you" in message:
                await update.message.reply_text(
                    "🤖 I'm running perfectly! Ready to help with your trading needs."
                )
            elif "thank" in message:
                await update.message.reply_text(
                    "🙏 You're welcome! Is there anything else you need?"
                )
            else:
                await update.message.reply_text(
                    "💬 I didn't understand that. Use /help to see available commands or ask me something specific about trading."
                )

        except Exception as e:
            logger.error(f"Error in message handler: {e}")
            await update.message.reply_text(
                "❌ Sorry, something went wrong. Please try again."
            )
            
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors."""
        try:
            logger.error(f"Update {update} caused error {context.error}")

            if update and update.effective_message:
                await update.effective_message.reply_text(
                    "❌ Sorry, something went wrong. Please try again or contact support."
                )

        except Exception as e:
            logger.error(f"Error in error handler: {e}")
            
    async def performance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /performance command."""
        try:
            performance = await self.get_performance()
            await update.message.reply_text(performance, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in performance command: {e}")
            await update.message.reply_text(
                "❌ Failed to get performance data. Please try again."
            )
            
    async def journal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /journal command."""
        try:
            journal = await self.get_trading_journal()
            await update.message.reply_text(journal, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in journal command: {e}")
            await update.message.reply_text(
                "❌ Failed to get trading journal. Please try again."
            )
            
    async def orders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /orders command."""
        try:
            orders = await self.get_orders()
            await update.message.reply_text(orders, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in orders command: {e}")
            await update.message.reply_text(
                "❌ Failed to get orders. Please try again."
            )
            
    async def account_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /account command to show account information."""
        try:
            # Get account info from MT5 executor
            account_info = await self._get_account_info()
            
            if not account_info:
                await update.message.reply_text(
                    "⚠️ Unable to retrieve account information. Please check connection to trading terminal.",
                    parse_mode='Markdown'
                )
                return
            
            # Format account information
            account_text = (
                f"💼 *Account Information*\n\n"
                f"*Login:* `{account_info.get('login', 'N/A')}`\n"
                f"*Name:* {account_info.get('name', 'N/A')}\n"
                f"*Server:* {account_info.get('server', 'N/A')}\n"
                f"*Company:* {account_info.get('company', 'N/A')}\n\n"
                f"*Balance:* ${account_info.get('balance', 0):.2f}\n"
                f"*Equity:* ${account_info.get('equity', 0):.2f}\n"
                f"*Margin:* ${account_info.get('margin', 0):.2f}\n"
                f"*Free Margin:* ${account_info.get('free_margin', 0):.2f}\n"
                f"*Margin Level:* {account_info.get('margin_level', 0):.2f}%\n"
                f"*Leverage:* 1:{account_info.get('leverage', 0)}\n"
            )
            
            # Create inline keyboard for account actions
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_account"),
                    InlineKeyboardButton("📈 Positions", callback_data="positions")
                ],
                [
                    InlineKeyboardButton("📋 Orders", callback_data="orders"),
                    InlineKeyboardButton("⚠️ Risk", callback_data="risk")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                account_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in account_command: {e}")
            await update.message.reply_text(
                "⚠️ An error occurred while retrieving account information.",
                parse_mode='Markdown'
            )
    
    async def _get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information from MT5 executor."""
        # For now, return mock data
        return {
            'login': 12345678,
            'name': 'Demo Account',
            'server': 'Demo Server',
            'company': 'Demo Broker',
            'balance': 10000.0,
            'equity': 10250.0,
            'margin': 500.0,
            'free_margin': 9750.0,
            'margin_level': 2050.0,
            'leverage': 100,
            'currency': 'USD'
        }
        
    async def monitor_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /monitor command to show system resource usage."""
        try:
            # Get system resource information
            system_info = self._get_system_info()
            
            # Format system information
            monitor_text = (
                f"🖥️ *System Monitoring*\n\n"
                f"*CPU Usage:* {system_info['cpu_percent']}%\n"
                f"*Memory Usage:* {system_info['memory_percent']}%\n"
                f"*Available Memory:* {system_info['available_memory']} MB\n"
                f"*Disk Usage:* {system_info['disk_percent']}%\n"
                f"*Free Disk Space:* {system_info['free_disk']} GB\n\n"
                f"*System Uptime:* {system_info['uptime']}\n"
                f"*Bot Uptime:* {system_info['bot_uptime']}\n"
                f"*Python Version:* {system_info['python_version']}\n"
            )
            
            # Create inline keyboard for monitoring actions
            keyboard = [
                [
                    InlineKeyboardButton("🔄 Refresh", callback_data="refresh_monitor"),
                    InlineKeyboardButton("📊 Status", callback_data="status")
                ],
                [
                    InlineKeyboardButton("💼 Account", callback_data="account"),
                    InlineKeyboardButton("⚙️ Settings", callback_data="settings")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                monitor_text,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error in monitor_command: {e}")
            await update.message.reply_text(
                "⚠️ An error occurred while retrieving system information.",
                parse_mode='Markdown'
            )
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system resource information."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_memory = round(memory.available / (1024 * 1024), 2)  # MB
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            free_disk = round(disk.free / (1024 * 1024 * 1024), 2)  # GB
            
            # Get system uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            uptime_str = f"{uptime.days} days, {uptime.seconds // 3600} hours, {(uptime.seconds % 3600) // 60} minutes"
            
            # Get bot uptime (mock for now)
            bot_uptime = "2 hours, 15 minutes"
            
            # Get Python version
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'available_memory': available_memory,
                'disk_percent': disk_percent,
                'free_disk': free_disk,
                'uptime': uptime_str,
                'bot_uptime': bot_uptime,
                'python_version': python_version
            }
            
        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            return {
                'cpu_percent': 'N/A',
                'memory_percent': 'N/A',
                'available_memory': 'N/A',
                'disk_percent': 'N/A',
                'free_disk': 'N/A',
                'uptime': 'N/A',
                'bot_uptime': 'N/A',
                'python_version': 'N/A'
            }
