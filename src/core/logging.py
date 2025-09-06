"""
Logging configuration using loguru and rich for better output formatting.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text
from rich.traceback import install as install_rich_traceback

# Colorama for Windows color support detection
try:
    import colorama

    colorama.init()
except ImportError:
    colorama = None


def terminal_supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Windows: colorama handles enabling VT100, but check for basic support
    if sys.platform == "win32":
        return colorama is not None and sys.stdout.isatty()
    # Other: check if stdout is a tty
    return sys.stdout.isatty()


# Install rich traceback handler
install_rich_traceback()

# Create rich console
console = Console()

# Remove default loguru handler
logger.remove()


def setup_logging(
    level: str = "INFO",
    format_type: str = "rich",
    file_path: Optional[str] = None,
    enable_console: bool = True,
    enable_file: bool = True,
) -> None:
    """
    Setup logging with loguru and rich.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format type ('rich', 'json', 'simple')
        file_path: Path to log file
        enable_console: Enable console logging
        enable_file: Enable file logging
    """

    # Configure loguru logger
    loguru_config = {
        "handlers": [],
        "levels": [
            {"name": "TRADE", "no": 25, "color": "<green>"},
            {"name": "SIGNAL", "no": 26, "color": "<blue>"},
            {"name": "RISK", "no": 27, "color": "<yellow>"},
            {"name": "SYSTEM", "no": 28, "color": "<cyan>"},
        ],
    }

    # Add console handler
    if enable_console:
        if format_type == "rich":
            # Rich console handler with colors and formatting
            console_handler = {
                "sink": RichHandler(
                    console=console,
                    show_time=True,
                    show_path=False,
                    markup=True,
                    rich_tracebacks=True,
                ),
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": level,
                "colorize": True,
            }
        elif format_type == "json":
            # JSON format for structured logging
            console_handler = {
                "sink": sys.stdout,
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": level,
                "serialize": True,
            }
        else:
            # Simple format
            console_handler = {
                "sink": sys.stdout,
                "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                "level": level,
            }

        loguru_config["handlers"].append(console_handler)

    # Add file handler
    if enable_file and file_path:
        # Ensure log directory exists
        log_dir = Path(file_path).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = {
            "sink": file_path,
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
            "level": level,
            "rotation": "10 MB",
            "retention": "30 days",
            "compression": "gz",
        }
        loguru_config["handlers"].append(file_handler)

    # Apply configuration
    for handler in loguru_config["handlers"]:
        logger.add(**handler)

    # Add custom levels
    for level_config in loguru_config["levels"]:
        try:
            # Check if level already exists before adding
            existing_levels = logger._core.min_levels
            if level_config["name"] not in existing_levels:
                logger.level(
                    level_config["name"],
                    level_config["no"],
                    color=level_config["color"],
                )
        except (ValueError, AttributeError):
            # Level already exists or logger not properly initialized, skip
            pass


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)


def log_system_event(
    component: str, action: str, message: str, level: str = "INFO", **kwargs
):
    """Log a system event with structured data."""
    extra_data = {
        "component": component,
        "action": action,
        "event_type": "system_event",
        **kwargs,
    }

    if level == "TRADE":
        logger.bind(**extra_data).log("TRADE", message)
    elif level == "SIGNAL":
        logger.bind(**extra_data).log("SIGNAL", message)
    elif level == "RISK":
        logger.bind(**extra_data).log("RISK", message)
    elif level == "SYSTEM":
        logger.bind(**extra_data).log("SYSTEM", message)
    else:
        logger.bind(**extra_data).log(level, message)


def log_trade_event(
    symbol: str, action: str, details: Dict[str, Any], level: str = "INFO"
):
    """Log a trade-related event."""
    extra_data = {
        "symbol": symbol,
        "action": action,
        "event_type": "trade_event",
        **details,
    }
    logger.bind(**extra_data).log("TRADE", f"Trade {action} for {symbol}")


def log_signal_event(
    symbol: str, bias: str, confidence: float, details: Dict[str, Any]
):
    """Log a trading signal event."""
    extra_data = {
        "symbol": symbol,
        "bias": bias,
        "confidence": confidence,
        "event_type": "signal_event",
        **details,
    }
    logger.bind(**extra_data).log(
        "SIGNAL", f"Signal generated for {symbol}: {bias} (confidence: {confidence}%)"
    )


def log_risk_event(event_type: str, details: Dict[str, Any], level: str = "WARNING"):
    """Log a risk management event."""
    extra_data = {"event_type": "risk_event", "risk_type": event_type, **details}
    logger.bind(**extra_data).log("RISK", f"Risk event: {event_type}")


def log_performance_metric(metric_name: str, value: float, unit: str = "", **kwargs):
    """Log a performance metric."""
    extra_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "event_type": "performance_metric",
        **kwargs,
    }
    logger.bind(**extra_data).info(f"Performance: {metric_name} = {value}{unit}")


def log_operation_timing(operation: str, start_time: float, end_time: float, **context):
    """Log operation timing for performance monitoring."""
    (end_time - start_time) * 1000
    # log_performance_metric(
    #     f"{operation}_duration",
    #     duration_ms,
    #     "ms",
    #     operation=operation,
    #     **context
    # )


def log_error_with_context(
    error: Exception, context: Dict[str, Any], level: str = "ERROR"
):
    """Log an error with additional context."""
    extra_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "event_type": "error",
        **context,
    }
    logger.bind(**extra_data).log(level, f"Error occurred: {error}")


def print_banner(title: str, subtitle: str = "", color: str = "cyan"):
    """Print a rich banner to the console."""
    banner_text = Text()
    banner_text.append(title, style=f"bold {color}")
    if subtitle:
        banner_text.append(f"\n{subtitle}", style=f"dim {color}")

    panel = Panel(
        banner_text, border_style=color, padding=(1, 2), title="AI Trading Bot"
    )
    console.print(panel)


def print_status_table(status_data: Dict[str, Any]):
    """Print a status table using rich."""
    from rich.table import Table

    table = Table(title="System Status")
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Details", style="white")

    for component, info in status_data.items():
        status = info.get("status", "unknown")
        details = info.get("details", "")

        # Color code the status
        if status == "running" or status == "connected":
            status_style = "green"
        elif status == "stopped" or status == "disconnected":
            status_style = "red"
        elif status == "warning":
            status_style = "yellow"
        else:
            status_style = "white"

        table.add_row(component, f"[{status_style}]{status}[/{status_style}]", details)

    console.print(table)


# Initialize logging with auto-detected format
_log_format = "rich" if terminal_supports_color() else "simple"
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format_type=_log_format,
    file_path=os.getenv("LOG_FILE", "logs/ai_trading_bot.log"),
    enable_console=True,
    enable_file=True,
)
