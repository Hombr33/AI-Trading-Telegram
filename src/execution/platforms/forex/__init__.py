"""
Forex trading platform executors (Windows only).
"""

import logging
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .mt5_executor import MT5Executor
    from .aiomql_executor import AioMQLExecutor

logger = logging.getLogger(__name__)

# Platform executors - conditionally imported based on OS
MT5Executor: Optional[type] = None
AioMQLExecutor: Optional[type] = None

try:
    import platform

    if platform.system() == "Windows":
        from .mt5_executor import MT5Executor
        from .aiomql_executor import AioMQLExecutor

        logger.info("Forex executors loaded successfully")
    else:
        logger.warning("Forex executors not available on this platform")
except ImportError as e:
    logger.warning(f"Failed to import forex executors: {e}")

__all__ = ["MT5Executor", "AioMQLExecutor"]
