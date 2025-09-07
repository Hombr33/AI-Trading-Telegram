"""
Trading platform implementations organized by category.
"""

from .crypto import *  # noqa: F403, F405
from .forex import *  # noqa: F403, F405
from .simulation import *  # noqa: F403, F405

__all__ = [
    # Crypto platforms (CCXT unified)
    "CCXTExecutor",
    "create_crypto_executor",
    # Forex platforms (Windows only)
    "MT5Executor",
    "AioMQLExecutor",
    # Simulation platforms
    "DemoExecutor",
    "PaperExecutor",
]
