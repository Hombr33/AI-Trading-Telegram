"""
Core module for the AI Trading Bot.
"""

from .config import config
from .logging import get_logger, setup_logging

__all__ = ["config", "get_logger", "setup_logging"]
