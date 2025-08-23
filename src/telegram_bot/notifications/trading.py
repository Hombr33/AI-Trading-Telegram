"""Trading notifications for Telegram bot."""

from typing import Dict, Any
from datetime import datetime, timezone

from src.core.logging import get_logger
from .manager import NotificationManager
from ..utils.constants import NotificationPriority

logger = get_logger(__name__)


class TradingNotifications:
    """Trading notifications for Telegram bot."""

    def __init__(self, notification_manager: NotificationManager):
        """Initialize trading notifications.
        
        Args:
            notification_manager: The notification manager to use.
        """
        self.notification_manager = notification_manager

    async def send_signal_notification(self, signal_data: Dict[str, Any]):
        """Send trading signal notification.
        
        Args:
            signal_data: The signal data to send.
        """
        try:
            symbol = signal_data.get("symbol", "UNKNOWN")
            direction = signal_data.get("direction", "NEUTRAL")
            strength = signal_data.get("strength", 0)
            entry_price = signal_data.get("entry_price", 0)
            target_price = signal_data.get("target_price", 0)
            stop_loss = signal_data.get("stop_loss", 0)

            # Determine emoji based on direction
            direction_emoji = "📈" if direction.upper() == "BUY" else "📉" if direction.upper() == "SELL" else "📊"
            
            message = (
                f"🚨 **NEW TRADING SIGNAL** 🚨\n\n"
                f"{direction_emoji} **Symbol**: {symbol}\n"
                f"🎯 **Direction**: {direction}\n"
                f"💯 **Strength**: {strength * 100:.1f}%\n"
                f"📊 **Entry**: ${entry_price:.5f}\n"
                f"🎯 **Target**: ${target_price:.5f}\n"
                f"⚠️ **Stop Loss**: ${stop_loss:.5f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Use /positions to check current positions\n"
                f"Use /risk to monitor risk levels"
            )

            await self.notification_manager.send_notification(
                message, 
                notification_type="signal", 
                priority=NotificationPriority.HIGH, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")

    async def send_position_notification(self, position_data: Dict[str, Any], action: str):
        """Send position update notification.
        
        Args:
            position_data: The position data to send.
            action: The action that occurred (opened, closed, modified).
        """
        try:
            symbol = position_data.get("symbol", "UNKNOWN")
            direction = position_data.get("type", "UNKNOWN")
            volume = position_data.get("volume", 0)
            price = position_data.get("price_open", 0)
            pnl = position_data.get("profit", 0)

            if action == "opened":
                emoji = "✅"
                action_text = "OPENED"
            elif action == "closed":
                emoji = "🔒"
                action_text = "CLOSED"
            elif action == "modified":
                emoji = "🔄"
                action_text = "MODIFIED"
            else:
                emoji = "📊"
                action_text = action.upper()

            # Determine emoji based on direction
            direction_emoji = "📈" if direction.upper() == "BUY" else "📉" if direction.upper() == "SELL" else "📊"
            
            # Determine emoji based on profit
            profit_emoji = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"

            message = (
                f"{emoji} **POSITION {action_text}** {emoji}\n\n"
                f"{direction_emoji} **Symbol**: {symbol}\n"
                f"📈 **Direction**: {direction}\n"
                f"📊 **Volume**: {volume}\n"
                f"💰 **Price**: ${price:.5f}\n"
                f"{profit_emoji} **P&L**: ${abs(pnl):.2f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            await self.notification_manager.send_notification(
                message, 
                notification_type="position", 
                priority=NotificationPriority.MEDIUM, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending position notification: {e}")

    async def send_order_notification(self, order_data: Dict[str, Any], action: str):
        """Send order update notification.
        
        Args:
            order_data: The order data to send.
            action: The action that occurred (placed, cancelled, filled).
        """
        try:
            symbol = order_data.get("symbol", "UNKNOWN")
            order_type = order_data.get("type", "UNKNOWN")
            volume = order_data.get("volume", 0)
            price = order_data.get("price", 0)

            if action == "placed":
                emoji = "📝"
                action_text = "PLACED"
            elif action == "cancelled":
                emoji = "❌"
                action_text = "CANCELLED"
            elif action == "filled":
                emoji = "✅"
                action_text = "FILLED"
            else:
                emoji = "📊"
                action_text = action.upper()

            message = (
                f"{emoji} **ORDER {action_text}** {emoji}\n\n"
                f"📊 **Symbol**: {symbol}\n"
                f"📈 **Type**: {order_type}\n"
                f"📊 **Volume**: {volume}\n"
                f"💰 **Price**: ${price:.5f}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )

            await self.notification_manager.send_notification(
                message, 
                notification_type="order", 
                priority=NotificationPriority.MEDIUM, 
                parse_mode="Markdown"
            )

        except Exception as e:
            logger.error(f"Error sending order notification: {e}")