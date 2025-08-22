"""
Notification Manager for Telegram bot alerts and notifications.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from enum import Enum

from src.core.logging import get_logger
from src.core.config import TelegramConfig

logger = get_logger(__name__)


class NotificationType(Enum):
    """Notification types."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SIGNAL = "signal"
    POSITION = "position"
    RISK = "risk"
    PERFORMANCE = "performance"


class NotificationManager:
    """Manages notifications and alerts for the Telegram bot."""
    
    def __init__(self, config: TelegramConfig):
        self.config = config
        self.chat_ids: List[int] = []
        self.notification_preferences: Dict[str, Dict] = {}
        self.notification_queue: List[Dict] = []
        self.running = False
        
        # Load chat IDs from config
        if self.config.chat_id:
            self.chat_ids.append(self.config.chat_id)
        
        # Setup default notification preferences
        self._setup_default_preferences()
    
    def _setup_default_preferences(self):
        """Setup default notification preferences."""
        self.notification_preferences = {
            "signals": {"enabled": True, "priority": "high"},
            "positions": {"enabled": True, "priority": "medium"},
            "risk": {"enabled": True, "priority": "high"},
            "performance": {"enabled": True, "priority": "medium"},
            "system": {"enabled": True, "priority": "low"},
            "errors": {"enabled": True, "priority": "high"}
        }
    
    async def start(self):
        """Start the notification manager."""
        self.running = True
        logger.info("Notification manager started")
        
        # Start notification processing loop
        asyncio.create_task(self._process_notifications())
    
    async def stop(self):
        """Stop the notification manager."""
        self.running = False
        logger.info("Notification manager stopped")
    
    async def add_chat_id(self, chat_id: int):
        """Add a chat ID for notifications."""
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)
            logger.info(f"Added chat ID: {chat_id}")
    
    async def remove_chat_id(self, chat_id: int):
        """Remove a chat ID from notifications."""
        if chat_id in self.chat_ids:
            self.chat_ids.remove(chat_id)
            logger.info(f"Removed chat ID: {chat_id}")
    
    async def send_notification(self, message: str, notification_type: str = "info", 
                              priority: str = "medium", **kwargs):
        """Send a notification to all registered chat IDs."""
        try:
            notification = {
                "message": message,
                "type": notification_type,
                "priority": priority,
                "timestamp": datetime.now(timezone.utc),
                "kwargs": kwargs
            }
            
            # Check if notification type is enabled
            if not self._is_notification_enabled(notification_type):
                logger.debug(f"Notification type {notification_type} is disabled")
                return
            
            # Add to queue for processing
            self.notification_queue.append(notification)
            logger.debug(f"Notification queued: {notification_type} - {priority}")
            
        except Exception as e:
            logger.error(f"Error queuing notification: {e}")
    
    async def send_signal_notification(self, signal_data: Dict):
        """Send trading signal notification."""
        try:
            symbol = signal_data.get("symbol", "UNKNOWN")
            bias = signal_data.get("bias", "NEUTRAL")
            confidence = signal_data.get("confidence", 0)
            
            message = (
                f"🚨 **AI TRADING SIGNAL** 🚨\n\n"
                f"📊 **Symbol**: {symbol}\n"
                f"🎯 **Bias**: {bias}\n"
                f"💯 **Confidence**: {confidence}%\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Use /positions to check current positions\n"
                f"Use /risk to monitor risk levels"
            )
            
            await self.send_notification(
                message, 
                notification_type="signal", 
                priority="high"
            )
            
        except Exception as e:
            logger.error(f"Error sending signal notification: {e}")
    
    async def send_position_notification(self, position_data: Dict, action: str):
        """Send position update notification."""
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
            
            message = (
                f"{emoji} **POSITION {action_text}** {emoji}\n\n"
                f"📊 **Symbol**: {symbol}\n"
                f"📈 **Direction**: {direction}\n"
                f"📊 **Volume**: {volume}\n"
                f"💰 **Price**: {price}\n"
                f"💵 **P&L**: {pnl}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )
            
            await self.send_notification(
                message, 
                notification_type="position", 
                priority="medium"
            )
            
        except Exception as e:
            logger.error(f"Error sending position notification: {e}")
    
    async def send_risk_alert(self, alert_type: str, message: str, data: Dict = None):
        """Send risk alert notification."""
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
                f"{emoji} **{title}** {emoji}\n\n"
                f"📝 **Message**: {message}\n\n"
            )
            
            if data:
                for key, value in data.items():
                    alert_message += f"📊 **{key.title()}**: {value}\n"
            
            alert_message += f"\n⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            
            await self.send_notification(
                alert_message, 
                notification_type="risk", 
                priority="high"
            )
            
        except Exception as e:
            logger.error(f"Error sending risk alert: {e}")
    
    async def send_performance_notification(self, performance_data: Dict):
        """Send performance update notification."""
        try:
            total_trades = performance_data.get("total_trades", 0)
            win_rate = performance_data.get("win_rate", 0)
            total_pnl = performance_data.get("total_pnl", 0)
            drawdown = performance_data.get("drawdown", 0)
            
            message = (
                f"📈 **PERFORMANCE UPDATE** 📈\n\n"
                f"📊 **Total Trades**: {total_trades}\n"
                f"🎯 **Win Rate**: {win_rate:.1f}%\n"
                f"💰 **Total P&L**: ${total_pnl:.2f}\n"
                f"📉 **Drawdown**: {drawdown:.2f}%\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}"
            )
            
            await self.send_notification(
                message, 
                notification_type="performance", 
                priority="medium"
            )
            
        except Exception as e:
            logger.error(f"Error sending performance notification: {e}")
    
    async def send_startup_notification(self):
        """Send startup notification."""
        try:
            message = (
                "🚀 **AI TRADING BOT STARTED** 🚀\n\n"
                "✅ System initialized successfully\n"
                "📊 Monitoring active\n"
                "🔔 Notifications enabled\n\n"
                f"⏰ **Startup Time**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                "Use /start to see available commands"
            )
            
            await self.send_notification(
                message, 
                notification_type="system", 
                priority="low"
            )
            
        except Exception as e:
            logger.error(f"Error sending startup notification: {e}")
    
    async def send_error_notification(self, error_message: str, component: str = "Unknown"):
        """Send error notification."""
        try:
            message = (
                "❌ **SYSTEM ERROR** ❌\n\n"
                f"🔧 **Component**: {component}\n"
                f"📝 **Error**: {error_message}\n\n"
                f"⏰ **Time**: {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}\n\n"
                "Please check system logs for details"
            )
            
            await self.send_notification(
                message, 
                notification_type="error", 
                priority="high"
            )
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
    
    def _is_notification_enabled(self, notification_type: str) -> bool:
        """Check if notification type is enabled."""
        if notification_type in self.notification_preferences:
            return self.notification_preferences[notification_type]["enabled"]
        return True
    
    async def _process_notifications(self):
        """Process notification queue."""
        while self.running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    await self._send_notification_to_all(notification)
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Error processing notifications: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _send_notification_to_all(self, notification: Dict):
        """Send notification to all registered chat IDs."""
        if not self.chat_ids:
            logger.warning("No chat IDs registered for notifications")
            return
        
        message = notification["message"]
        notification_type = notification["type"]
        priority = notification["priority"]
        
        # Format message based on priority
        if priority == "high":
            message = f"🚨 {message}"
        elif priority == "medium":
            message = f"⚠️ {message}"
        elif priority == "low":
            message = f"ℹ️ {message}"
        
        # Send to all chat IDs
        for chat_id in self.chat_ids:
            try:
                # This would be implemented by the Telegram bot
                # For now, just log the notification
                logger.info(f"Notification sent to {chat_id}: {notification_type} - {priority}")
                
            except Exception as e:
                logger.error(f"Failed to send notification to {chat_id}: {e}")
    
    def get_notification_stats(self) -> Dict:
        """Get notification statistics."""
        return {
            "total_notifications": len(self.notification_queue),
            "chat_ids_count": len(self.chat_ids),
            "enabled_types": [
                ntype for ntype, prefs in self.notification_preferences.items() 
                if prefs["enabled"]
            ],
            "running": self.running
        }
    
    def update_preferences(self, notification_type: str, enabled: bool, priority: str = "medium"):
        """Update notification preferences."""
        if notification_type in self.notification_preferences:
            self.notification_preferences[notification_type]["enabled"] = enabled
            self.notification_preferences[notification_type]["priority"] = priority
            logger.info(f"Updated preferences for {notification_type}: enabled={enabled}, priority={priority}")
        else:
            self.notification_preferences[notification_type] = {
                "enabled": enabled,
                "priority": priority
            }
            logger.info(f"Added preferences for {notification_type}: enabled={enabled}, priority={priority}")
