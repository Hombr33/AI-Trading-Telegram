"""Formatting utilities for Telegram bot messages."""

from datetime import datetime, timezone


def format_timestamp(timestamp: datetime = None) -> str:
    """Format a timestamp for display in messages.

    Args:
        timestamp: The timestamp to format. Defaults to current UTC time.

    Returns:
        str: The formatted timestamp string.
    """
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)

    return timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")


def get_status_emoji(status: str) -> str:
    """Get an emoji representing a status.

    Args:
        status: The status string (e.g., 'Online', 'Offline', 'Warning').

    Returns:
        str: The emoji representing the status.
    """
    if status.lower() in ["online", "connected", "active", "running"]:
        return "✅"
    elif status.lower() in ["offline", "disconnected", "inactive", "stopped"]:
        return "❌"
    else:
        return "⚠️"


def get_direction_emoji(direction: str) -> str:
    """Get an emoji representing a trading direction.

    Args:
        direction: The direction string (e.g., 'BUY', 'SELL').

    Returns:
        str: The emoji representing the direction.
    """
    if direction.upper() == "BUY":
        return "📈"
    elif direction.upper() == "SELL":
        return "📉"
    else:
        return "📊"


def get_profit_emoji(profit: float) -> str:
    """Get an emoji representing a profit value.

    Args:
        profit: The profit value.

    Returns:
        str: The emoji representing the profit.
    """
    if profit > 0:
        return "🟢"
    elif profit < 0:
        return "🔴"
    else:
        return "⚪"


def get_risk_indicator(value: float, threshold: float) -> str:
    """Get an emoji representing a risk level.

    Args:
        value: The current value.
        threshold: The threshold value for high risk.

    Returns:
        str: The emoji representing the risk level.
    """
    if value <= threshold * 0.5:
        return "🟢"  # Safe
    elif value <= threshold * 0.8:
        return "🟡"  # Warning
    else:
        return "🔴"  # Danger


def format_currency(value: float, decimals: int = 2) -> str:
    """Format a currency value.

    Args:
        value: The currency value.
        decimals: The number of decimal places to show.

    Returns:
        str: The formatted currency string.
    """
    return f"${abs(value):,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """Format a percentage value.

    Args:
        value: The percentage value.
        decimals: The number of decimal places to show.

    Returns:
        str: The formatted percentage string.
    """
    return f"{value:.{decimals}f}%"
