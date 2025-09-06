"""Auto trading commands for Telegram bot."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger
from src.telegram_bot.utils.keyboards import create_keyboard

from .base import BaseCommandHandler

logger = get_logger(__name__)


class AutoTradingCommandHandler(BaseCommandHandler):
    """Auto trading command handler for Telegram bot."""

    def _register_commands(self):
        """Register auto trading commands."""
        self.commands = {
            "auto_trading": self.auto_trading_command,
            "auto_signals": self.auto_signals_command,
        }

    def _register_callbacks(self):
        """Register auto trading callbacks."""
        self.callbacks = {
            "toggle_auto_trading": self.toggle_auto_trading,
            "toggle_auto_signals": self.toggle_auto_signals,
            "auto_trading": self.auto_trading_command,
            "auto_signals": self.auto_signals_command,
            "view_auto_settings": self.view_auto_settings,
            "edit_auto_pairs": self.edit_auto_pairs,
        }

    async def auto_trading_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /auto_trading command."""
        from src.core.config import config

        status = "🟢 ENABLED" if config.auto_trading.enabled else "🔴 DISABLED"

        message = (
            f"🤖 **Auto Trading Status**: {status}\n\n"
            f"**Configuration:**\n"
            f"• Max Trades/Day: {config.auto_trading.max_trades_per_day}\n"
            f"• Risk Per Trade: {config.auto_trading.risk_per_trade_percent}%\n"
            f"• Signal Generation: {'🟢 ON' if config.auto_trading.auto_signal_generation else '🔴 OFF'}\n"
            f"• Signal Interval: {config.auto_trading.signal_interval_minutes}min\n\n"
            f"**Trading Pairs:**\n"
            f"• Forex: {', '.join(config.auto_trading.forex_pairs)}\n"
            f"• Crypto: {', '.join(config.auto_trading.crypto_pairs)}\n\n"
            f"💡 Toggle auto trading to start/stop automatic signal generation and trading."
        )

        keyboard = create_keyboard(
            [
                [("🔄 Toggle Auto Trading", "toggle_auto_trading")],
                [
                    ("⚙️ Auto Signals", "auto_signals"),
                    ("📋 View Settings", "view_auto_settings"),
                ],
                [("✏️ Edit Pairs", "edit_auto_pairs"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def auto_signals_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle the /auto_signals command."""
        from src.core.config import config

        status = (
            "🟢 ENABLED"
            if config.auto_trading.auto_signal_generation
            else "🔴 DISABLED"
        )

        message = (
            f"📡 **Auto Signal Generation**: {status}\n\n"
            f"**Configuration:**\n"
            f"• Interval: Every {config.auto_trading.signal_interval_minutes} minutes\n"
            f"• Auto Trading: {'🟢 ON' if config.auto_trading.enabled else '🔴 OFF'}\n\n"
            f"**Signal Analysis:**\n"
            f"• AI-powered market analysis\n"
            f"• Technical indicator fusion\n"
            f"• Risk-adjusted position sizing\n"
            f"• Multi-timeframe confirmation\n\n"
            f"**Active Pairs:**\n"
            f"• Forex: {len(config.auto_trading.forex_pairs)} pairs\n"
            f"• Crypto: {len(config.auto_trading.crypto_pairs)} pairs\n\n"
            f"💡 Auto signals work independently or with auto trading."
        )

        keyboard = create_keyboard(
            [
                [("🔄 Toggle Auto Signals", "toggle_auto_signals")],
                [
                    ("🤖 Auto Trading", "auto_trading"),
                    ("📋 View Settings", "view_auto_settings"),
                ],
                [("✏️ Edit Pairs", "edit_auto_pairs"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        if update.callback_query:
            await self.edit_message(update, context, message, keyboard)
        else:
            await self.send_message(update, context, message, keyboard)

    async def toggle_auto_trading(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Toggle auto trading on/off."""
        from src.core.config import config

        # Toggle the setting
        config.auto_trading.enabled = not config.auto_trading.enabled

        status = "🟢 ENABLED" if config.auto_trading.enabled else "🔴 DISABLED"
        action = "enabled" if config.auto_trading.enabled else "disabled"

        # Start/stop the auto trading service
        if config.auto_trading.enabled:
            await self._start_auto_trading_service()
        else:
            await self._stop_auto_trading_service()

        message = (
            f"🤖 **Auto Trading {action.upper()}!**\n\n"
            f"Status: {status}\n\n"
            f"{'🚀 Auto trading is now active. The system will:' if config.auto_trading.enabled else '🛑 Auto trading stopped. Manual control resumed.'}\n"
            f"{'• Generate signals automatically' if config.auto_trading.enabled else ''}\n"
            f"{'• Execute trades based on AI analysis' if config.auto_trading.enabled else ''}\n"
            f"{'• Manage risk per your settings' if config.auto_trading.enabled else ''}\n\n"
            f"Use /auto_trading to view detailed settings."
        )

        keyboard = create_keyboard(
            [
                [("⚙️ Auto Trading Settings", "auto_trading")],
                [("📡 Auto Signals", "auto_signals"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await self.edit_message(update, context, message, keyboard)

    async def toggle_auto_signals(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Toggle auto signal generation on/off."""
        from src.core.config import config

        # Toggle the setting
        config.auto_trading.auto_signal_generation = (
            not config.auto_trading.auto_signal_generation
        )

        status = (
            "🟢 ENABLED"
            if config.auto_trading.auto_signal_generation
            else "🔴 DISABLED"
        )
        action = "enabled" if config.auto_trading.auto_signal_generation else "disabled"

        # Start/stop the signal generation service
        if config.auto_trading.auto_signal_generation:
            await self._start_signal_generation_service()
        else:
            await self._stop_signal_generation_service()

        message = (
            f"📡 **Auto Signal Generation {action.upper()}!**\n\n"
            f"Status: {status}\n\n"
            f"{'🔍 Signal generation is now active. The system will:' if config.auto_trading.auto_signal_generation else '🔇 Signal generation stopped.'}\n"
            f"{'• Analyze market conditions every ' + str(config.auto_trading.signal_interval_minutes) + ' minutes' if config.auto_trading.auto_signal_generation else ''}\n"
            f"{'• Send AI-powered trading signals' if config.auto_trading.auto_signal_generation else ''}\n"
            f"{'• Suggest optimal entry/exit points' if config.auto_trading.auto_signal_generation else ''}\n\n"
            f"Use /auto_signals to view detailed settings."
        )

        keyboard = create_keyboard(
            [
                [("📡 Auto Signals Settings", "auto_signals")],
                [("🤖 Auto Trading", "auto_trading"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await self.edit_message(update, context, message, keyboard)

    async def view_auto_settings(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """View detailed auto trading settings."""
        from src.core.config import config

        message = (
            f"⚙️ **Auto Trading Configuration**\n\n"
            f"**Status:**\n"
            f"• Auto Trading: {'🟢 ON' if config.auto_trading.enabled else '🔴 OFF'}\n"
            f"• Auto Signals: {'🟢 ON' if config.auto_trading.auto_signal_generation else '🔴 OFF'}\n\n"
            f"**Trading Settings:**\n"
            f"• Max Trades/Day: {config.auto_trading.max_trades_per_day}\n"
            f"• Risk Per Trade: {config.auto_trading.risk_per_trade_percent}%\n"
            f"• Signal Interval: {config.auto_trading.signal_interval_minutes} minutes\n\n"
            f"**Active Trading Pairs:**\n"
            f"• **Forex**: {', '.join(config.auto_trading.forex_pairs)}\n"
            f"• **Crypto**: {', '.join(config.auto_trading.crypto_pairs)}\n\n"
            f"**Environment Variables:**\n"
            f"• AUTO_TRADING_ENABLED\n"
            f"• AUTO_SIGNAL_GENERATION\n"
            f"• SIGNAL_INTERVAL_MINUTES\n"
            f"• MAX_TRADES_PER_DAY"
        )

        keyboard = create_keyboard(
            [
                [
                    ("🤖 Auto Trading", "auto_trading"),
                    ("📡 Auto Signals", "auto_signals"),
                ],
                [("✏️ Edit Pairs", "edit_auto_pairs"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await self.edit_message(update, context, message, keyboard)

    async def edit_auto_pairs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit auto trading pairs."""
        from src.core.config import config

        message = (
            f"✏️ **Edit Trading Pairs**\n\n"
            f"**Current Configuration:**\n\n"
            f"**Forex Pairs:**\n"
            f"{chr(10).join([f'• {pair}' for pair in config.auto_trading.forex_pairs])}\n\n"
            f"**Crypto Pairs:**\n"
            f"{chr(10).join([f'• {pair}' for pair in config.auto_trading.crypto_pairs])}\n\n"
            f"💡 **To modify pairs:**\n"
            f"1. Edit your `.env` file\n"
            f"2. Set `AUTO_FOREX_PAIRS=EURUSD,GBPUSD,USDJPY`\n"
            f"3. Set `AUTO_CRYPTO_PAIRS=BTCUSDT,ETHUSDT,ADAUSDT`\n"
            f"4. Restart the application\n\n"
            f"🔄 Changes require application restart."
        )

        keyboard = create_keyboard(
            [
                [
                    ("🤖 Auto Trading", "auto_trading"),
                    ("📡 Auto Signals", "auto_signals"),
                ],
                [("📋 View Settings", "view_auto_settings"), ("📊 Status", "status")],
                [("🏠 Main Menu", "start")],
            ]
        )

        await self.edit_message(update, context, message, keyboard)

    async def _start_auto_trading_service(self):
        """Start the auto trading background service."""
        # This service is managed by the main application
        logger.info("Auto trading service is managed by main application")

    async def _stop_auto_trading_service(self):
        """Stop the auto trading background service."""
        # This service is managed by the main application
        logger.info("Auto trading service is managed by main application")

    async def _start_signal_generation_service(self):
        """Start the signal generation background service."""
        # This service is managed by the main application
        logger.info("Signal generation service is managed by main application")

    async def _stop_signal_generation_service(self):
        """Stop the signal generation background service."""
        # This service is managed by the main application
        logger.info("Signal generation service is managed by main application")
