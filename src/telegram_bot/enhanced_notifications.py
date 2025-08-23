"""
Enhanced notification system with retry logic and priority management.
"""

import asyncio
import time
from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, field

from ..core.logging import get_logger, log_error_with_context, log_system_event
from ..core.error_handler import with_error_handling, ErrorContext
from ..core.exceptions import TelegramBotError

logger = get_logger(__name__)


class NotificationPriority(Enum):
    """Notification priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class NotificationStatus(Enum):
    """Notification delivery status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Notification:
    """Notification data structure."""
    id: str
    message: str
    notification_type: str
    priority: NotificationPriority
    chat_ids: List[int]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0
    max_attempts: int = 3
    status: NotificationStatus = NotificationStatus.PENDING
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EnhancedNotificationManager:
    """Enhanced notification manager with reliability features."""
    
    def __init__(self, telegram_bot, config):
        self.telegram_bot = telegram_bot
        self.config = config
        self.notification_queue: List[Notification] = []
        self.failed_notifications: List[Notification] = []
        self.delivery_stats = {
            "total_sent": 0,
            "total_failed": 0,
            "total_retries": 0
        }
        self.is_running = False
        self._processing_task = None
        self._retry_task = None
    
    async def start(self):
        """Start the notification processing."""
        self.is_running = True
        self._processing_task = asyncio.create_task(self._process_notifications())
        self._retry_task = asyncio.create_task(self._retry_failed_notifications())
        log_system_event("notifications", "started", "Enhanced notification manager started")
    
    async def stop(self):
        """Stop the notification processing."""
        self.is_running = False
        
        if self._processing_task:
            self._processing_task.cancel()
        if self._retry_task:
            self._retry_task.cancel()
        
        # Process remaining notifications
        await self._flush_queue()
        log_system_event("notifications", "stopped", "Enhanced notification manager stopped")
    
    @with_error_handling("send_notification", max_retries=2)
    async def send_notification(
        self,
        message: str,
        notification_type: str = "info",
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        chat_ids: Optional[List[int]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Send notification with enhanced reliability."""
        
        # Use default chat IDs if none provided
        if chat_ids is None:
            chat_ids = [self.config.chat_id] if self.config.chat_id else []
        
        if not chat_ids:
            logger.warning("No chat IDs configured for notification")
            return False
        
        # Create notification
        notification = Notification(
            id=f"{notification_type}_{int(time.time() * 1000)}",
            message=message,
            notification_type=notification_type,
            priority=priority,
            chat_ids=chat_ids,
            metadata=metadata or {}
        )
        
        # Add to queue based on priority
        if priority == NotificationPriority.CRITICAL:
            # Send immediately
            return await self._send_notification(notification)
        else:
            # Queue for processing
            self._add_to_queue(notification)
            return True
    
    def _add_to_queue(self, notification: Notification):
        """Add notification to queue with priority sorting."""
        # Insert based on priority (higher priority first)
        inserted = False
        for i, queued_notification in enumerate(self.notification_queue):
            if notification.priority.value > queued_notification.priority.value:
                self.notification_queue.insert(i, notification)
                inserted = True
                break
        
        if not inserted:
            self.notification_queue.append(notification)
        
        logger.debug(f"Queued notification {notification.id} (queue size: {len(self.notification_queue)})")
    
    async def _process_notifications(self):
        """Process notification queue."""
        while self.is_running:
            try:
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    success = await self._send_notification(notification)
                    
                    if not success and notification.attempts < notification.max_attempts:
                        self.failed_notifications.append(notification)
                else:
                    await asyncio.sleep(1)  # No notifications to process
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error_with_context(e, {"operation": "process_notifications"})
                await asyncio.sleep(5)  # Brief pause on error
    
    async def _retry_failed_notifications(self):
        """Retry failed notifications."""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Retry every 30 seconds
                
                if self.failed_notifications:
                    # Process oldest failed notifications first
                    notification = self.failed_notifications.pop(0)
                    
                    # Check if we should still retry
                    age_seconds = (datetime.now(timezone.utc) - notification.created_at).total_seconds()
                    if age_seconds > 3600:  # 1 hour max retry time
                        logger.warning(f"Dropping expired notification: {notification.id}")
                        continue
                    
                    notification.status = NotificationStatus.RETRYING
                    self.delivery_stats["total_retries"] += 1
                    
                    success = await self._send_notification(notification)
                    if not success and notification.attempts < notification.max_attempts:
                        self.failed_notifications.append(notification)  # Re-queue for retry
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                log_error_with_context(e, {"operation": "retry_notifications"})
    
    async def _send_notification(self, notification: Notification) -> bool:
        """Send individual notification."""
        notification.attempts += 1
        
        try:
            async with ErrorContext(f"send_notification_{notification.notification_type}", {
                "notification_id": notification.id,
                "attempt": notification.attempts
            }) as ctx:
                start_time = time.time()
                
                for chat_id in notification.chat_ids:
                    try:
                        await self.telegram_bot.application.bot.send_message(
                            chat_id=chat_id,
                            text=notification.message,
                            parse_mode=notification.metadata.get("parse_mode", "Markdown")
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to send notification to chat {chat_id}: {e}")
                        notification.last_error = str(e)
                        raise TelegramBotError(f"Failed to send to chat {chat_id}: {e}")
                
                # Record successful delivery
                notification.status = NotificationStatus.SENT
                self.delivery_stats["total_sent"] += 1
                
                duration_ms = (time.time() - start_time) * 1000
                log_system_event("notifications", "sent",
                               f"Notification sent successfully: {notification.id}",
                               context={"duration_ms": duration_ms})
                
                return True
                
        except Exception as e:
            notification.status = NotificationStatus.FAILED
            notification.last_error = str(e)
            self.delivery_stats["total_failed"] += 1
            
            log_error_with_context(e, {
                "notification_id": notification.id,
                "notification_type": notification.notification_type,
                "attempt": notification.attempts
            })
            
            return False
    
    async def _flush_queue(self):
        """Process remaining notifications in queue."""
        logger.info(f"Flushing {len(self.notification_queue)} pending notifications")
        
        for notification in self.notification_queue[:]:
            await self._send_notification(notification)
        
        self.notification_queue.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification delivery statistics."""
        return {
            "delivery_stats": self.delivery_stats,
            "queue_size": len(self.notification_queue),
            "failed_count": len(self.failed_notifications),
            "is_running": self.is_running,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Notification helper functions for common use cases
async def send_critical_alert(message: str, error: Optional[Exception] = None):
    """Send critical alert notification."""
    from ..main import telegram_bot
    
    if telegram_bot and hasattr(telegram_bot, 'enhanced_notification_manager'):
        error_detail = f"\nError: {str(error)}" if error else ""
        critical_message = f"🚨 *CRITICAL ALERT*\n\n{message}{error_detail}"
        
        await telegram_bot.enhanced_notification_manager.send_notification(
            critical_message,
            "critical_alert",
            NotificationPriority.CRITICAL,
            metadata={"parse_mode": "Markdown"}
        )


async def send_trade_notification(symbol: str, action: str, details: Dict[str, Any]):
    """Send standardized trade notification."""
    from ..main import telegram_bot
    
    if telegram_bot and hasattr(telegram_bot, 'enhanced_notification_manager'):
        message = format_trade_message(symbol, action, details)
        
        await telegram_bot.enhanced_notification_manager.send_notification(
            message,
            "trade",
            NotificationPriority.HIGH,
            metadata={"parse_mode": "Markdown"}
        )


def format_trade_message(symbol: str, action: str, details: Dict[str, Any]) -> str:
    """Format trade message with emojis and formatting."""
    action_emojis = {
        "order_placed": "📝",
        "order_filled": "✅",
        "order_cancelled": "❌",
        "position_opened": "🟢",
        "position_closed": "🔴",
        "position_modified": "🔄"
    }
    
    emoji = action_emojis.get(action, "📊")
    
    message = f"{emoji} *{action.replace('_', ' ').title()}*\n\n"
    message += f"Symbol: `{symbol}`\n"
    
    for key, value in details.items():
        if key in ['volume', 'price', 'profit', 'sl', 'tp']:
            message += f"{key.replace('_', ' ').title()}: `{value}`\n"
    
    message += f"\nTime: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
    
    return message
