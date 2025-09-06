"""
Trading platform implementations organized by category.
"""

from .crypto import *
from .forex import *
from .simulation import *

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
