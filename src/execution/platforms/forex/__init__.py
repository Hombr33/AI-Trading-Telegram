"""
Forex trading platform executors (Windows only).
"""

import logging
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .aiomql_executor import AioMQLExecutor
    from .mt5_executor import MT5Executor

logger = logging.getLogger(__name__)

# Platform executors - conditionally imported based on OS
MT5Executor: Optional[type] = None
AioMQLExecutor: Optional[type] = None

try:
    import platform

    if platform.system() == "Windows":
        from .aiomql_executor import AioMQLExecutor
        from .mt5_executor import MT5Executor

        logger.info("Forex executors loaded successfully")
    else:
        logger.warning("Forex executors not available on this platform")
except ImportError as e:
    logger.warning(f"Failed to import forex executors: {e}")

__all__ = ["MT5Executor", "AioMQLExecutor"]
