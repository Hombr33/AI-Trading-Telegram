"""
Cryptocurrency exchange executor using CCXT unified library.
"""

try:
    from .ccxt_executor import CCXTExecutor, create_crypto_executor
    CCXT_AVAILABLE = True
except ImportError:
    CCXT_AVAILABLE = False

__all__ = [
    "CCXTExecutor",
    "create_crypto_executor", 
    "CCXT_AVAILABLE"
]
