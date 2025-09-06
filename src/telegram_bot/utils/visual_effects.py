"""Visual effects and animations for Telegram bot."""

import asyncio
from typing import List

from telegram import Update
from telegram.ext import ContextTypes

from src.core.logging import get_logger

logger = get_logger(__name__)


class VisualEffects:
    """Visual effects and animations for enhanced user experience."""

    @staticmethod
    def create_progress_bar(
        current: int,
        total: int,
        length: int = 10,
        filled_char: str = "█",
        empty_char: str = "░",
    ) -> str:
        """Create a visual progress bar."""
        filled_length = int(length * current / total) if total > 0 else 0
        return filled_char * filled_length + empty_char * (length - filled_length)

    @staticmethod
    def create_sparkline(values: List[float], length: int = 8) -> str:
        """Create a sparkline chart from values."""
        if not values:
            return "▁" * length

        min_val, max_val = min(values), max(values)
        if min_val == max_val:
            return "▄" * length

        chars = "▁▂▃▄▅▆▇█"

        sparkline = ""
        for i in range(min(length, len(values))):
            normalized = (values[i] - min_val) / (max_val - min_val)
            char_index = int(normalized * (len(chars) - 1))
            sparkline += chars[char_index]

        # Pad if needed
        while len(sparkline) < length:
            sparkline += "▁"

        return sparkline

    @staticmethod
    def format_currency(amount: float, symbol: str = "$") -> str:
        """Format currency with appropriate colors."""
        if amount > 0:
            return f"🟢 {symbol}{amount:,.2f}"
        elif amount < 0:
            return f"🔴 {symbol}{abs(amount):,.2f}"
        else:
            return f"⚪ {symbol}{amount:.2f}"

    @staticmethod
    def format_percentage(pct: float) -> str:
        """Format percentage with colors and emojis."""
        if pct > 5:
            return f"🚀 +{pct:.2f}%"
        elif pct > 0:
            return f"🟢 +{pct:.2f}%"
        elif pct > -5:
            return f"🔴 {pct:.2f}%"
        else:
            return f"💥 {pct:.2f}%"

    @staticmethod
    def create_trading_card(
        symbol: str,
        direction: str,
        entry_price: float,
        current_price: float,
        profit: float,
        profit_pct: float,
        volume: float,
        price_history: List[float],
    ) -> str:
        """Create a visual trading card for a position."""
        type_emoji = "📈" if direction == "BUY" else "📉"

        # Create mini chart
        chart = VisualEffects.create_sparkline(price_history)

        card = (
            f"┌─ {type_emoji} **{symbol}** ─┐\n"
            f"│ {chart} │\n"
            f"│ Entry: ${entry_price:.5f} │\n"
            f"│ Current: ${current_price:.5f} │\n"
            f"│ Volume: {volume} │\n"
            f"│ P&L: {VisualEffects.format_currency(profit)} │\n"
            f"│ Change: {VisualEffects.format_percentage(profit_pct)} │\n"
            f"└─────────────────────┘"
        )

        return card

    @staticmethod
    def create_status_indicator(status: str) -> str:
        """Create animated status indicator."""
        indicators = {
            "connected": "🟢 ●",
            "connecting": "🟡 ◐",
            "disconnected": "🔴 ○",
            "error": "❌ ✖",
            "loading": "🔄 ◑",
            "success": "✅ ✓",
            "warning": "⚠️ ⚠",
        }
        return indicators.get(status, "❓ ?")

    @staticmethod
    async def send_typing_effect(
        update: Update, context: ContextTypes.DEFAULT_TYPE, duration: float = 2.0
    ):
        """Send typing indicator for enhanced UX."""
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, action="typing"
            )
            await asyncio.sleep(duration)
        except Exception as e:
            logger.debug(f"Typing effect error: {e}")

    @staticmethod
    def create_loading_dots(step: int) -> str:
        """Create animated loading dots."""
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        return dots[step % len(dots)]

    @staticmethod
    def create_profit_trend(profit_history: List[float]) -> str:
        """Create profit trend indicator."""
        if len(profit_history) < 2:
            return "📊"

        current = profit_history[-1]
        previous = profit_history[-2]

        if current > previous:
            return "📈🚀" if current > previous * 1.1 else "📈"
        elif current < previous:
            return "📉💥" if current < previous * 0.9 else "📉"
        else:
            return "📊"
