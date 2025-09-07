"""
API routes initialization.
"""

from . import bridge, health, metrics, trading, v1

__all__ = ["bridge", "health", "metrics", "v1", "trading"]
