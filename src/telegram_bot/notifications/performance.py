"""Performance notifications for Telegram bot."""

from typing import Dict, Any
from datetime import datetime, timezone

from src.core.logging import get_logger
from .manager import NotificationManager

logger = get_logger(__name__)


class PerformanceNotifications:
    """Performance notifications for Telegram bot."""

    def __init__(self, notification_manager: NotificationManager):
        """Initialize performance notifications.
        
        Args:
            notification_manager: The notification manager to use.
        """
        self.notification_manager = notification_manager

    async def send_daily_summary(self, performance_data: Dict[str, Any]):
        """Send daily performance summary notification.
        
        Args:
            performance_data: The performance data to send.
        """
        try:
            profit = performance_data.get("profit", 0)
            win_rate = performance_data.get("win_rate", 0)
            trades = performance_data.get("trades", 0)
            best_trade = performance_data.get("best_trade", {})
            worst_trade = performance_data.get("worst_trade", {})

            # Determine emoji based on profit
            profit_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"

            message = (
                f"📊 **DAILY PERFORMANCE SUMMARY** 📊\n\n"
                f"{profit_emoji} **Profit/Loss**: ${profit:.2f}\n"
                f"📈 **Win Rate**: {win_rate * 100:.1f}%\n"
                f"🔄 **Total Trades**: {trades}\n\n"
            )

            if best_trade:
                message += (
                    f"🏆 **Best Trade**:\n"
                    f"  Symbol: {best_trade.get('symbol', 'N/A')}\n"
                    f"  Profit: ${best_trade.get('profit', 0):.2f}\n"
                    f"  Type: {best_trade.get('type', 'N/A')}\n\n"
                )

            if worst_trade:
                message += (
                    f"📉 **Worst Trade**:\n"
                    f"  Symbol: {worst_trade.get('symbol', 'N/A')}\n"
                    f"  Loss: ${abs(worst_trade.get('profit', 0)):.2f}\n"
                    f"  Type: {worst_trade.get('type', 'N/A')}\n\n"
                )

            message += (
                f"⏰ **Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
                f"Use /performance for detailed performance metrics\n"
                f"Use /journal to view trading journal"
            )

            await self.notification_manager.send_notification(
                message, notification_type="performance", priority="medium", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending daily summary notification: {e}")

    async def send_weekly_summary(self, performance_data: Dict[str, Any]):
        """Send weekly performance summary notification.
        
        Args:
            performance_data: The performance data to send.
        """
        try:
            profit = performance_data.get("profit", 0)
            win_rate = performance_data.get("win_rate", 0)
            trades = performance_data.get("trades", 0)
            best_day = performance_data.get("best_day", {})
            worst_day = performance_data.get("worst_day", {})
            top_symbols = performance_data.get("top_symbols", [])

            # Determine emoji based on profit
            profit_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"

            message = (
                f"📊 **WEEKLY PERFORMANCE SUMMARY** 📊\n\n"
                f"{profit_emoji} **Profit/Loss**: ${profit:.2f}\n"
                f"📈 **Win Rate**: {win_rate * 100:.1f}%\n"
                f"🔄 **Total Trades**: {trades}\n\n"
            )

            if best_day:
                message += (
                    f"🏆 **Best Day**:\n"
                    f"  Date: {best_day.get('date', 'N/A')}\n"
                    f"  Profit: ${best_day.get('profit', 0):.2f}\n"
                    f"  Trades: {best_day.get('trades', 0)}\n\n"
                )

            if worst_day:
                message += (
                    f"📉 **Worst Day**:\n"
                    f"  Date: {worst_day.get('date', 'N/A')}\n"
                    f"  Loss: ${abs(worst_day.get('profit', 0)):.2f}\n"
                    f"  Trades: {worst_day.get('trades', 0)}\n\n"
                )

            if top_symbols:
                message += f"🔝 **Top Performing Symbols**:\n"
                for symbol in top_symbols[:3]:  # Show top 3
                    message += f"  {symbol.get('symbol', 'N/A')}: ${symbol.get('profit', 0):.2f}\n"
                message += "\n"

            message += (
                f"⏰ **Week Ending**: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}\n\n"
                f"Use /performance for detailed performance metrics\n"
                f"Use /journal to view trading journal"
            )

            await self.notification_manager.send_notification(
                message, notification_type="performance", priority="medium", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending weekly summary notification: {e}")

    async def send_monthly_summary(self, performance_data: Dict[str, Any]):
        """Send monthly performance summary notification.
        
        Args:
            performance_data: The performance data to send.
        """
        try:
            profit = performance_data.get("profit", 0)
            win_rate = performance_data.get("win_rate", 0)
            trades = performance_data.get("trades", 0)
            best_week = performance_data.get("best_week", {})
            worst_week = performance_data.get("worst_week", {})
            top_symbols = performance_data.get("top_symbols", [])
            drawdown = performance_data.get("max_drawdown", 0)

            # Determine emoji based on profit
            profit_emoji = "🟢" if profit > 0 else "🔴" if profit < 0 else "⚪"

            message = (
                f"📊 **MONTHLY PERFORMANCE SUMMARY** 📊\n\n"
                f"{profit_emoji} **Profit/Loss**: ${profit:.2f}\n"
                f"📈 **Win Rate**: {win_rate * 100:.1f}%\n"
                f"🔄 **Total Trades**: {trades}\n"
                f"📉 **Max Drawdown**: {drawdown * 100:.1f}%\n\n"
            )

            if best_week:
                message += (
                    f"🏆 **Best Week**:\n"
                    f"  Week Ending: {best_week.get('date', 'N/A')}\n"
                    f"  Profit: ${best_week.get('profit', 0):.2f}\n"
                    f"  Trades: {best_week.get('trades', 0)}\n\n"
                )

            if worst_week:
                message += (
                    f"📉 **Worst Week**:\n"
                    f"  Week Ending: {worst_week.get('date', 'N/A')}\n"
                    f"  Loss: ${abs(worst_week.get('profit', 0)):.2f}\n"
                    f"  Trades: {worst_week.get('trades', 0)}\n\n"
                )

            if top_symbols:
                message += f"🔝 **Top Performing Symbols**:\n"
                for symbol in top_symbols[:3]:  # Show top 3
                    message += f"  {symbol.get('symbol', 'N/A')}: ${symbol.get('profit', 0):.2f}\n"
                message += "\n"

            message += (
                f"⏰ **Month**: {datetime.now(timezone.utc).strftime('%B %Y')}\n\n"
                f"Use /performance for detailed performance metrics\n"
                f"Use /journal to view trading journal"
            )

            await self.notification_manager.send_notification(
                message, notification_type="performance", priority="high", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending monthly summary notification: {e}")

    async def send_milestone_notification(self, milestone_type: str, value: float):
        """Send milestone notification.
        
        Args:
            milestone_type: The type of milestone (profit, trades, etc.).
            value: The milestone value.
        """
        try:
            if milestone_type == "profit":
                emoji = "💰"
                title = "PROFIT MILESTONE"
                message = f"Total profit has reached ${value:.2f}!"
            elif milestone_type == "trades":
                emoji = "🔄"
                title = "TRADES MILESTONE"
                message = f"Total number of trades has reached {int(value)}!"
            elif milestone_type == "win_streak":
                emoji = "🔥"
                title = "WIN STREAK MILESTONE"
                message = f"Current win streak has reached {int(value)} trades!"
            else:
                emoji = "🏆"
                title = "MILESTONE REACHED"
                message = f"A new milestone has been reached: {milestone_type} - {value}"

            notification_message = (
                f"{emoji} **{title}** {emoji}\n\n"
                f"🎉 **Congratulations!** 🎉\n\n"
                f"📝 **Achievement**: {message}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Use /performance to view detailed performance metrics"
            )

            await self.notification_manager.send_notification(
                notification_message, notification_type="performance", priority="medium", parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending milestone notification: {e}")