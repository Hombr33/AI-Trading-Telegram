"""Animation utilities for Telegram bot."""

import asyncio
from datetime import datetime
from typing import Any, Dict, List

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger

from .keyboards import create_animated_loading_keyboard, create_quick_actions_keyboard

logger = get_logger(__name__)


class LiveDashboard:
    """Live animated dashboard for Telegram bot."""

    def __init__(self):
        self.running = False
        self.update_interval = 3.0  # seconds

    async def start_live_dashboard(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Start live dashboard with animations."""
        self.running = True

        # Initial loading animation
        await self._show_loading_animation(update, context)

        # Start live updates
        while self.running:
            await self._update_dashboard(update, context)
            await asyncio.sleep(self.update_interval)

    async def stop_live_dashboard(self):
        """Stop live dashboard."""
        self.running = False

    async def _show_loading_animation(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Show loading animation."""
        loading_steps = [
            "🔍 Scanning markets...",
            "📊 Analyzing positions...",
            "🎯 Loading signals...",
            "⚠️ Checking risk metrics...",
            "✅ Dashboard ready!",
        ]

        for i, step in enumerate(loading_steps):
            keyboard = create_animated_loading_keyboard(i)

            if i == 0:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=f"⚡ **LIVE DASHBOARD LOADING** ⚡\n\n{step}",
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=update.callback_query.message.message_id,
                    text=f"⚡ **LIVE DASHBOARD LOADING** ⚡\n\n{step}",
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )

            await asyncio.sleep(0.8)

    async def _update_dashboard(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Update dashboard with live data."""
        try:
            # Import services for real data
            from ..services.system_data_service import SystemDataService
            from ..services.trading_data_service import TradingDataService

            # Initialize services
            trading_service = TradingDataService()
            system_service = SystemDataService()

            # Get live data
            positions = await trading_service.get_positions()
            account = await trading_service.get_account_info()
            status = await system_service.get_system_status()

            total_profit = (
                sum(pos.get("profit", 0) for pos in positions) if positions else 0
            )
            profit_emoji = (
                "🟢" if total_profit > 0 else "🔴" if total_profit < 0 else "⚪"
            )

            # Create animated dashboard
            timestamp = datetime.now().strftime("%H:%M:%S")

            message = (
                f"⚡ **LIVE TRADING DASHBOARD** ⚡\n\n"
                f"💰 **Account**: ${account.get('balance', 0):.2f}\n"
                f"{profit_emoji} **P&L**: ${total_profit:.2f}\n"
                f"📊 **Positions**: {len(positions)}\n"
                f"🔄 **Status**: {status.get('status', 'Unknown')}\n\n"
                f"📈 **Market Pulse**: {'🟢 Bullish' if total_profit > 0 else '🔴 Bearish' if total_profit < 0 else '🟡 Neutral'}\n"
                f"⚠️ **Risk Level**: {'🟢 Low' if len(positions) < 3 else '🟡 Medium' if len(positions) < 5 else '🔴 High'}\n\n"
                f"🕐 **Live Update**: {timestamp}\n"
                f"🔄 *Auto-refreshing...*"
            )

            keyboard = create_keyboard(
                [
                    [
                        ("⏸️ Pause", "pause_dashboard"),
                        ("🔄 Force Refresh", "refresh_dashboard"),
                    ],
                    [("📊 Positions", "positions"), ("💰 Account", "account")],
                    [("🎯 Signals", "signals"), ("⚠️ Risk", "risk")],
                    [("❌ Close Dashboard", "close_dashboard")],
                ]
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=update.callback_query.message.message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.debug(f"Error updating dashboard: {e}")
                # Stop if message was deleted or other error
                self.running = False

        except Exception as e:
            logger.error(f"Error updating dashboard with real data: {e}")
            # Fallback to basic dashboard
            message = (
                f"⚡ **LIVE TRADING DASHBOARD** ⚡\n\n"
                f"❌ **Data Loading Error**\n\n"
                f"Please try refreshing or check system status.\n\n"
                f"🕐 **Last Update**: {datetime.now().strftime('%H:%M:%S')}"
            )

            keyboard = create_keyboard(
                [
                    [("🔄 Refresh", "refresh_dashboard"), ("📊 Status", "status")],
                    [("🏠 Menu", "start")],
                ]
            )

            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=update.callback_query.message.message_id,
                    text=message,
                    reply_markup=keyboard,
                    parse_mode="Markdown",
                )
            except Exception as edit_error:
                logger.debug(f"Error updating dashboard fallback: {edit_error}")
                self.running = False


def create_market_heatmap_keyboard(markets: List[Dict[str, Any]]) -> str:
    """Create a text-based market heatmap."""
    heatmap = "📊 **MARKET HEATMAP** 📊\n\n"

    for market in markets[:5]:  # Show top 5 markets
        change = market.get("change_pct", 0)
        if change > 2:
            emoji = "🟢🔥"
        elif change > 0:
            emoji = "🟢"
        elif change > -2:
            emoji = "🟡"
        elif change > -5:
            emoji = "🔴"
        else:
            emoji = "🔴💥"

        # Create mini progress bar
        abs_change = abs(change)
        bars = int(abs_change / 2) if abs_change < 10 else 5
        bar = "█" * min(bars, 5)

        heatmap += f"{emoji} **{market['symbol']}**: {change:+.2f}% {bar}\n"

    return heatmap


def create_price_alert_keyboard(symbol: str, current_price: float) -> Dict[str, Any]:
    """Create price alert configuration keyboard."""
    message = (
        f"🔔 **PRICE ALERT SETUP** 🔔\n\n"
        f"📊 **{symbol}**\n"
        f"💰 Current Price: ${current_price:.5f}\n\n"
        f"⚠️ Set alert thresholds:\n"
        f"📈 Above: ${current_price * 1.02:.5f} (+2%)\n"
        f"📉 Below: ${current_price * 0.98:.5f} (-2%)"
    )

    keyboard_buttons = [
        [
            ("🔔 Enable Alert", f"alert_enable_{symbol}"),
            ("❌ Disable", f"alert_disable_{symbol}"),
        ],
        [
            ("📈 Set High Alert", f"alert_high_{symbol}"),
            ("📉 Set Low Alert", f"alert_low_{symbol}"),
        ],
        [
            ("⚙️ Custom Range", f"alert_custom_{symbol}"),
            ("🔄 Current Alerts", f"alert_list_{symbol}"),
        ],
    ]

    return {"message": message, "keyboard": keyboard_buttons}
