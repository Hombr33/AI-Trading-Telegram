"""Risk notifications for Telegram bot."""

from typing import Dict, Any
from datetime import datetime, timezone

from src.core.logging import get_logger
from .manager import NotificationManager
from ..utils.constants import NotificationPriority

logger = get_logger(__name__)


class RiskNotifications:
    """Risk notifications for Telegram bot."""

    def __init__(self, notification_manager: NotificationManager):
        """Initialize risk notifications.

        Args:
            notification_manager: The notification manager to use.
        """
        self.notification_manager = notification_manager

    async def send_risk_alert(
        self, alert_type: str, message: str, data: Dict[str, Any] = None
    ):
        """Send risk alert notification.

        Args:
            alert_type: The type of risk alert.
            message: The alert message.
            data: Additional data to include in the alert.
        """
        try:
            if alert_type == "drawdown":
                emoji = "⚠️"
                title = "DRAWDOWN ALERT"
            elif alert_type == "correlation":
                emoji = "🔗"
                title = "CORRELATION ALERT"
            elif alert_type == "exposure":
                emoji = "📊"
                title = "EXPOSURE ALERT"
            elif alert_type == "emergency":
                emoji = "🚨"
                title = "EMERGENCY ALERT"
            else:
                emoji = "⚠️"
                title = "RISK ALERT"

            alert_message = (
                f"{emoji} **{title}** {emoji}\n\n" f"📝 **Message**: {message}\n\n"
            )

            if data:
                for key, value in data.items():
                    alert_message += f"📊 **{key.title()}**: {value}\n"

            alert_message += f"\n⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"

            # Determine priority based on alert type
            if alert_type == "emergency":
                priority = NotificationPriority.CRITICAL
            elif alert_type in ["drawdown", "exposure"]:
                priority = NotificationPriority.HIGH
            else:
                priority = NotificationPriority.MEDIUM

            await self.notification_manager.send_notification(
                alert_message,
                notification_type="risk",
                priority=priority,
                parse_mode="Markdown",
            )

        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")

    async def send_drawdown_alert(self, current_drawdown: float, max_allowed: float):
        """Send drawdown alert notification.

        Args:
            current_drawdown: The current drawdown percentage.
            max_allowed: The maximum allowed drawdown percentage.
        """
        message = f"Account drawdown has reached {current_drawdown:.2f}% (max allowed: {max_allowed:.2f}%)"
        data = {
            "current_drawdown": f"{current_drawdown:.2f}%",
            "max_allowed": f"{max_allowed:.2f}%",
            "status": "WARNING" if current_drawdown < max_allowed else "CRITICAL",
        }
        await self.send_risk_alert("drawdown", message, data)

    async def send_exposure_alert(self, current_exposure: float, max_allowed: float):
        """Send exposure alert notification.

        Args:
            current_exposure: The current exposure percentage.
            max_allowed: The maximum allowed exposure percentage.
        """
        message = f"Account exposure has reached {current_exposure:.2f}% (max allowed: {max_allowed:.2f}%)"
        data = {
            "current_exposure": f"{current_exposure:.2f}%",
            "max_allowed": f"{max_allowed:.2f}%",
            "status": "WARNING" if current_exposure < max_allowed else "CRITICAL",
        }
        await self.send_risk_alert("exposure", message, data)

    async def send_correlation_alert(self, correlation_level: float, symbols: str):
        """Send correlation alert notification.

        Args:
            correlation_level: The correlation level between positions.
            symbols: The symbols that are correlated.
        """
        message = f"High correlation detected between positions: {symbols}"
        data = {
            "correlation_level": f"{correlation_level:.2f}",
            "symbols": symbols,
            "status": "WARNING",
        }
        await self.send_risk_alert("correlation", message, data)

    async def send_emergency_stop_alert(self, reason: str):
        """Send emergency stop alert notification.

        Args:
            reason: The reason for the emergency stop.
        """
        message = f"EMERGENCY STOP TRIGGERED: {reason}"
        data = {
            "reason": reason,
            "action": "All positions closed and trading stopped",
            "status": "CRITICAL",
        }
        await self.send_risk_alert("emergency", message, data)
