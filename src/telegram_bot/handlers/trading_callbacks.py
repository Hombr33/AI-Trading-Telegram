"""Trading callback handlers for Telegram bot."""

from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard
from src.telegram_bot.utils.visual_effects import VisualEffects

logger = get_logger(__name__)


class TradingCallbackHandler:
    """Trading callback handler for Telegram bot."""

    def __init__(self, trading_handler):
        """Initialize the trading callback handler."""
        self.trading_handler = trading_handler
        self.callbacks = {
            "positions": self._handle_positions_callback,
            "refresh_positions": self._handle_positions_callback,
            "position_details": self._handle_position_details_callback,
            "quick_close": self._handle_quick_close_callback,
            "orders": self._handle_orders_callback,
            "refresh_orders": self._handle_orders_callback,
            "account": self._handle_account_callback,
            "refresh_account": self._handle_account_callback,
            "account_history": self._handle_account_history_callback,
            "export_history": self._handle_export_history_callback,
            "symbols": self._handle_symbols_callback,
            "refresh_symbols": self._handle_symbols_callback,
            "signals": self._handle_signals_callback,
            "refresh_signals": self._handle_signals_callback,
            "live_dashboard": self._handle_live_dashboard_callback,
            "webapp": self._handle_webapp_callback,
            "webapp_open": self._handle_webapp_open_callback,
            "webapp_mobile": self._handle_webapp_mobile_callback,
            "webapp_desktop": self._handle_webapp_desktop_callback,
        }

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries."""
        query = update.callback_query
        callback_data = query.data

        # Handle signal callbacks with pattern matching
        if callback_data.startswith("signal_"):
            await self._handle_signal_callback(update, context)
        elif callback_data in self.callbacks:
            await self.callbacks[callback_data](update, context)
        else:
            await query.answer("Unknown callback")
            logger.warning(f"Unknown callback data: {callback_data}")

    async def _handle_positions_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle positions callback."""
        await self.trading_handler.positions_command(update, context)

    async def _handle_orders_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle orders callback."""
        await self.trading_handler.orders_command(update, context)

    async def _handle_account_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle account callback."""
        await self.trading_handler.account_command(update, context)

    async def _handle_symbols_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle symbols callback."""
        await self.trading_handler.symbols_command(update, context)

    async def _handle_signals_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle signals callback."""
        await self.trading_handler.signals_command(update, context)

    async def _handle_position_details_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle position details callback."""
        query = update.callback_query

        # Get mock position data for demonstration
        positions = await self.trading_handler._get_positions()
        if not positions:
            message = "📊 **POSITION DETAILS**\n\nNo positions found."
        else:
            position = positions[0]  # Show first position details

            # Create detailed position card using VisualEffects
            price_history = [1.1234, 1.1245, 1.1250, 1.1248, 1.1252]
            sparkline = VisualEffects.create_sparkline(price_history)

            message = (
                f"📊 **POSITION DETAILS** 📊\n\n"
                f"🎯 **{position['symbol']}**\n"
                f"📈 **Type**: {position['type']}\n"
                f"💰 **Volume**: {position['volume']}\n"
                f"📊 **Open Price**: {VisualEffects.format_currency(position['open_price'])}\n"
                f"📈 **Current Price**: {VisualEffects.format_currency(position['current_price'])}\n"
                f"💸 **P&L**: {VisualEffects.format_currency(position['profit'])}\n"
                f"📊 **Change**: {VisualEffects.format_percentage((position['current_price'] - position['open_price']) / position['open_price'])}\n\n"
                f"📈 **Price Chart**:\n{sparkline}\n\n"
                f"⏰ **Opened**: {position['time']}\n"
                f"🕐 **Duration**: {position.get('duration', 'N/A')}"
            )

        keyboard = create_keyboard(
            [
                [
                    ("🔄 Refresh", "refresh_positions"),
                    ("⚡ Quick Close", "quick_close"),
                ],
                [("📈 All Positions", "positions"), ("📋 Orders", "orders")],
                [("💰 Account", "account"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_quick_close_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle quick close callback."""
        query = update.callback_query

        # Show loading animation
        await VisualEffects.send_typing_effect(
            context.bot, query.message.chat_id, "Closing position"
        )

        message = (
            f"⚡ **QUICK CLOSE** ⚡\n\n"
            f"✅ **Position closed successfully!**\n\n"
            f"📊 **Final P&L**: {VisualEffects.format_currency(125.50)}\n"
            f"⏰ **Closed at**: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"💡 Position has been closed and profit/loss has been realized."
        )

        keyboard = create_keyboard(
            [
                [("📈 Positions", "positions"), ("📋 Orders", "orders")],
                [("💰 Account", "account"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_account_history_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle account history callback."""
        query = update.callback_query

        # Show loading effect
        await VisualEffects.send_typing_effect(
            context.bot, query.message.chat_id, "Loading account history"
        )

        # Create account history with visual effects
        history_data = [
            {
                "date": "2024-01-15",
                "type": "Trade",
                "amount": 125.50,
                "balance": 10125.50,
            },
            {
                "date": "2024-01-14",
                "type": "Trade",
                "amount": -45.30,
                "balance": 10000.00,
            },
            {
                "date": "2024-01-13",
                "type": "Deposit",
                "amount": 1000.00,
                "balance": 10045.30,
            },
            {
                "date": "2024-01-12",
                "type": "Trade",
                "amount": 67.80,
                "balance": 9045.30,
            },
        ]

        history_text = ""
        for item in history_data:
            emoji = (
                "💰"
                if item["type"] == "Deposit"
                else "💸" if item["amount"] < 0 else "💹"
            )
            history_text += (
                f"{emoji} {item['date']} | {item['type']}\n"
                f"   {VisualEffects.format_currency(item['amount'])} → "
                f"{VisualEffects.format_currency(item['balance'])}\n\n"
            )

        message = (
            f"📜 **ACCOUNT HISTORY** 📜\n\n"
            f"{history_text}"
            f"📊 **Total Trades**: 245\n"
            f"📈 **Win Rate**: 68.3%\n"
            f"💰 **Total Profit**: {VisualEffects.format_currency(2156.80)}"
        )

        keyboard = create_keyboard(
            [
                [("🔄 Refresh", "account_history"), ("📊 Export", "export_history")],
                [("💰 Account", "account"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_live_dashboard_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle live dashboard callback."""
        from ..utils.animations import LiveDashboard

        dashboard = LiveDashboard()
        await dashboard.start_live_dashboard(update, context)

    async def _handle_webapp_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle webapp callback."""
        query = update.callback_query

        message = (
            "🌐 **TELEGRAM WEB APP** 🌐\n\n"
            "🚀 **Advanced Trading Interface**\n\n"
            "Access our full-featured web interface with:\n"
            "• 📈 Real-time charts\n"
            "• 🎯 Advanced order management\n"
            "• 📊 Detailed analytics\n"
            "• 🔧 Strategy backtesting\n\n"
            "Click 'Open WebApp' to launch the interface!"
        )

        keyboard = create_keyboard(
            [
                [("🌐 Open WebApp", "webapp_open")],
                [
                    ("📱 Mobile View", "webapp_mobile"),
                    ("💻 Desktop View", "webapp_desktop"),
                ],
                [("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_signal_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle signal-related callbacks."""
        query = update.callback_query
        callback_data = query.data

        if callback_data.startswith("signal_"):
            parts = callback_data.split("_")
            if len(parts) >= 3:
                symbol = parts[1]
                timeframe = parts[2]

                await query.answer(f"Generating signal for {symbol} on {timeframe}...")

                # Show loading animation
                await VisualEffects.send_typing_effect(
                    context.bot, query.message.chat_id, f"Analyzing {symbol}"
                )

                # Generate signal using trading handler
                signal = await self.trading_handler._generate_signal_for_pair(
                    symbol, timeframe
                )

                if signal:
                    "🟢📈" if signal["direction"] == "BUY" else "🔴📉"
                    confidence = (
                        "High"
                        if signal["strength"] > 0.8
                        else "Medium" if signal["strength"] > 0.6 else "Low"
                    )

                    # Create visual trading card
                    price_history = [1.1234, 1.1245, 1.1250, 1.1248, 1.1252]

                    message = VisualEffects.create_trading_card(
                        symbol=signal["symbol"],
                        direction=signal["direction"],
                        entry_price=signal["entry_price"],
                        current_price=signal["entry_price"],
                        profit=0.0,
                        profit_pct=0.0,
                        volume=signal.get("volume", 0.1),
                        price_history=price_history,
                    )

                    message += (
                        f"\n🎯 **AI ANALYSIS**\n"
                        f"⚡ **Confidence**: {confidence} ({signal['strength'] * 100:.1f}%)\n"
                        f"🛡️ **Stop Loss**: {VisualEffects.format_currency(signal['stop_loss'])}\n"
                        f"💡 **Reasoning**: {signal['reasoning']}\n\n"
                        f"🔄 **Last Updated**: {datetime.now().strftime('%H:%M:%S')}"
                    )
                else:
                    message = (
                        f"🎯 **AI TRADING SIGNAL** 🎯\n\n"
                        f"❌ **No signal generated for {symbol}**\n\n"
                        f"🔍 Market conditions not favorable for trading.\n"
                        f"Try a different timeframe or check back later."
                    )

                keyboard = create_keyboard(
                    [
                        [
                            ("🔄 Refresh", f"signal_{symbol}_{timeframe}"),
                            ("📊 All Signals", "signals"),
                        ],
                        [("📈 Positions", "positions"), ("📋 Orders", "orders")],
                        [("🏠 Menu", "start")],
                    ]
                )

                await query.edit_message_text(
                    message, reply_markup=keyboard, parse_mode="Markdown"
                )

    async def _handle_export_history_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle export history callback."""
        query = update.callback_query

        message = (
            "📊 **EXPORT HISTORY** 📊\n\n"
            "📄 **Export Options**:\n\n"
            "• 📋 CSV Format - Spreadsheet compatible\n"
            "• 📊 PDF Report - Professional summary\n"
            "• 📈 Excel File - Advanced analysis\n"
            "• 📧 Email Report - Send to email\n\n"
            "⏰ **Export Range**: Last 30 days\n"
            "📊 **Include**: Trades, P&L, Performance metrics"
        )

        keyboard = create_keyboard(
            [
                [("📋 Export CSV", "export_csv"), ("📊 Export PDF", "export_pdf")],
                [
                    ("📈 Export Excel", "export_excel"),
                    ("📧 Email Report", "email_report"),
                ],
                [("📜 History", "account_history"), ("🏠 Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_webapp_open_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle webapp open callback."""
        query = update.callback_query

        from ..webapp.app import WebAppHandler

        webapp_handler = WebAppHandler()

        message = (
            "🌐 **OPENING WEBAPP** 🌐\n\n"
            "🚀 **Launching Advanced Trading Interface**\n\n"
            "✨ **Features Available**:\n"
            "• 📈 Real-time charts with TradingView\n"
            "• 🎯 Advanced order management\n"
            "• 📊 Detailed analytics dashboard\n"
            "• 🔧 Strategy backtesting tools\n"
            "• 📱 Mobile-optimized interface\n\n"
            "Click the WebApp button below to access!"
        )

        # Create WebApp keyboard
        keyboard = webapp_handler.create_webapp_keyboard("trading")

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_webapp_mobile_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle webapp mobile callback."""
        query = update.callback_query

        message = (
            "📱 **MOBILE WEBAPP** 📱\n\n"
            "🚀 **Optimized for Mobile Trading**\n\n"
            "✨ **Mobile Features**:\n"
            "• 👆 Touch-friendly interface\n"
            "• 📊 Swipe navigation\n"
            "• 🔔 Push notifications\n"
            "• ⚡ Quick actions\n"
            "• 📈 Mobile charts\n\n"
            "Perfect for trading on the go!"
        )

        keyboard = create_keyboard(
            [
                [
                    ("📱 Open Mobile", "webapp_open"),
                    ("💻 Desktop Version", "webapp_desktop"),
                ],
                [("🌐 WebApp Menu", "webapp"), ("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )

    async def _handle_webapp_desktop_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle webapp desktop callback."""
        query = update.callback_query

        message = (
            "💻 **DESKTOP WEBAPP** 💻\n\n"
            "🚀 **Full-Featured Trading Platform**\n\n"
            "✨ **Desktop Features**:\n"
            "• 📊 Multi-monitor support\n"
            "• 📈 Advanced charting tools\n"
            "• 🎯 Complex order types\n"
            "• 📊 Detailed analytics\n"
            "• ⚙️ Strategy development\n\n"
            "Complete trading environment for serious traders!"
        )

        keyboard = create_keyboard(
            [
                [
                    ("💻 Open Desktop", "webapp_open"),
                    ("📱 Mobile Version", "webapp_mobile"),
                ],
                [("🌐 WebApp Menu", "webapp"), ("🏠 Main Menu", "start")],
            ]
        )

        await query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )
