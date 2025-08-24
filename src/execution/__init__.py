"""
Production-grade execution module for cross-platform trading.

This module provides a modular, extensible architecture for trading across
multiple platforms with full cross-platform compatibility, monitoring, and
production-grade error handling.
"""

# Core interfaces and data models
from .interfaces import (
    # Protocols and interfaces
    IExecutor, IPlatformManager, IConnectable, IHealthCheckable,
    IOrderExecutor, IPositionManager, IMarketDataProvider, IAccountManager,
    
    # Data models
    OrderRequest, OrderResponse, PositionData, AccountInfo, MarketData,
    
    # Enums
    PlatformType, OrderType, OrderSide, OrderStatus, HealthStatus,
    
    # Context managers
    executor_context, platform_manager_context
)

# Platform compatibility and factory
from .platform_compatibility import (
    get_compatibility_manager, init_platform_compatibility, 
    is_windows, is_linux, is_macos, log_platform_status
)
from .factory import (
    get_platform_manager, get_executor_factory,
    create_executor, initialize_execution_system, shutdown_execution_system
)

# Configuration validation
from .config_validator import (
    validate_execution_config, ConfigurationValidator, ValidationLevel
)

# Monitoring and health checks
from .monitoring import get_executor_monitor

# Base implementation
from .base_executor import BaseExecutor

# Legacy managers (still available for backwards compatibility)
from .order_manager import OrderManager
from .position_manager import PositionManager
from .trailing_manager import TrailingManager
from .platform_manager import PlatformManager as LegacyPlatformManager

# Platform implementations (imported conditionally)
from .platforms import *

# Initialize platform compatibility on module import
init_platform_compatibility()

# Public API
__all__ = [
    # Core interfaces
    "IExecutor", "IPlatformManager", "IConnectable", "IHealthCheckable",
    "IOrderExecutor", "IPositionManager", "IMarketDataProvider", "IAccountManager",
    
    # Data models
    "OrderRequest", "OrderResponse", "PositionData", "AccountInfo", "MarketData",
    
    # Enums
    "PlatformType", "OrderType", "OrderSide", "OrderStatus", "HealthStatus",
    
    # Factory and management
    "get_platform_manager", "get_executor_factory", "create_executor",
    "initialize_execution_system", "shutdown_execution_system",
    
    # Platform compatibility
    "get_compatibility_manager", "is_windows", "is_linux", "is_macos",
    "log_platform_status",
    
    # Configuration
    "validate_execution_config", "ConfigurationValidator", "ValidationLevel",
    
    # Monitoring
    "get_executor_monitor",
    
    # Base classes
    "BaseExecutor",
    
    # Context managers
    "executor_context", "platform_manager_context",
    
    # Legacy components (backwards compatibility)
    "OrderManager", "PositionManager", "TrailingManager", "LegacyPlatformManager",
    
    # Platform executors (conditionally available)
    "CCXTExecutor", "create_crypto_executor",
    "MT5Executor", "AioMQLExecutor", 
    "DemoExecutor", "PaperExecutor"
]

# Version info
__version__ = "2.0.0"
__author__ = "AI Trading Bot Team"
__description__ = "Production-grade cross-platform trading execution module"
