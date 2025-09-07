"""Constants for Telegram bot."""

from enum import Enum


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


class CallbackType(Enum):
    """Callback query types."""

    STATUS = "status"
    POSITIONS = "positions"
    ORDERS = "orders"
    ACCOUNT = "account"
    SIGNALS = "signals"
    RISK = "risk"
    SETTINGS = "settings"
    HELP = "help"
    MONITOR = "monitor"
    PERFORMANCE = "performance"
    REFRESH_STATUS = "refresh_status"
    REFRESH_POSITIONS = "refresh_positions"
    REFRESH_SIGNALS = "refresh_signals"
    REFRESH_ACCOUNT = "refresh_account"
    REFRESH_MONITOR = "refresh_monitor"
    ACCOUNT_HISTORY = "account_history"
