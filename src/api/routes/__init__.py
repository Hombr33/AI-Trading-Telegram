"""
API routes initialization.
"""

from . import bridge, health, metrics, v1, trading

__all__ = [
    "bridge",
    "health", 
    "metrics",
    "v1",
    "trading"
]