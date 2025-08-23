"""
Execution module for trade execution and order management.
"""

import sys

# Import base executors (always available)
from .order_manager import OrderManager
from .position_manager import PositionManager
from .trailing_manager import TrailingManager

# Import platform-specific executors conditionally
MT5Executor = None
AioMQLExecutor = None

if sys.platform == "win32":
    try:
        from .mt5_executor import MT5Executor
        from .aiomql_executor import AioMQLExecutor
    except ImportError:
        pass

__all__ = ["MT5Executor", "AioMQLExecutor", "OrderManager", "PositionManager", "TrailingManager"]
