"""
Production-grade interfaces and protocols for the execution module.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable


# Core Data Models
@dataclass
class OrderRequest:
    """Standard order request model."""

    symbol: str
    side: str  # 'buy' or 'sell'
    type: str  # 'market', 'limit', 'stop', 'stop_limit'
    amount: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    take_profit: Optional[float] = None
    stop_loss: Optional[float] = None
    leverage: Optional[float] = None
    reduce_only: bool = False
    time_in_force: str = "GTC"  # 'GTC', 'IOC', 'FOK'
    client_order_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderResponse:
    """Standard order response model."""

    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: str
    type: str
    amount: float
    price: Optional[float]
    filled: float
    remaining: float
    status: str
    timestamp: datetime
    platform: str
    fees: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PositionData:
    """Standard position data model."""

    position_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    leverage: Optional[float]
    margin: Optional[float]
    timestamp: datetime
    platform: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AccountInfo:
    """Standard account information model."""

    account_id: str
    balance: Dict[str, float]  # asset -> balance
    equity: float
    margin_used: float
    margin_available: float
    is_demo: bool
    platform: str
    timestamp: datetime
    permissions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketData:
    """Standard market data model."""

    symbol: str
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume_24h: Optional[float] = None
    change_24h: Optional[float] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)


# Enums
class PlatformType(Enum):
    """Trading platform types."""

    MT5 = "mt5"
    BINANCE = "binance"
    BYBIT = "bybit"
    BITGET = "bitget"
    DEMO = "demo"
    PAPER = "paper"


class OrderType(Enum):
    """Universal order types."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TRAILING_STOP = "trailing_stop"


class OrderSide(Enum):
    """Universal order sides."""

    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Universal order status."""

    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


class HealthStatus(Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


# Core Protocols
@runtime_checkable
class IConnectable(Protocol):
    """Protocol for connection management."""

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        ...

    async def connect(self) -> bool:
        """Connect to service."""
        ...

    async def disconnect(self) -> bool:
        """Disconnect from service."""
        ...

    async def test_connection(self) -> bool:
        """Test connection health."""
        ...


@runtime_checkable
class IHealthCheckable(Protocol):
    """Protocol for health monitoring."""

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        ...

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        ...


@runtime_checkable
class IOrderExecutor(Protocol):
    """Protocol for order execution."""

    async def place_order(self, request: OrderRequest) -> OrderResponse:
        """Place a new order."""
        ...

    async def cancel_order(self, order_id: str) -> OrderResponse:
        """Cancel an existing order."""
        ...

    async def modify_order(self, order_id: str, **kwargs) -> OrderResponse:
        """Modify an existing order."""
        ...

    async def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """Get order details."""
        ...

    async def get_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Get all orders."""
        ...


@runtime_checkable
class IPositionManager(Protocol):
    """Protocol for position management."""

    async def get_positions(self, symbol: Optional[str] = None) -> List[PositionData]:
        """Get all positions."""
        ...

    async def close_position(
        self, position_id: str, volume: Optional[float] = None
    ) -> OrderResponse:
        """Close position."""
        ...


@runtime_checkable
class IMarketDataProvider(Protocol):
    """Protocol for market data access."""

    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        ...

    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Get current ticker data."""
        ...

    async def get_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical kline/candlestick data."""
        ...


@runtime_checkable
class IAccountManager(Protocol):
    """Protocol for account management."""

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information."""
        ...

    async def get_balance(self, asset: str = "USD") -> float:
        """Get account balance for specific asset."""
        ...


# Main Executor Interface
@runtime_checkable
class IExecutor(
    IConnectable,
    IHealthCheckable,
    IOrderExecutor,
    IPositionManager,
    IMarketDataProvider,
    IAccountManager,
    Protocol,
):
    """Complete executor interface combining all protocols."""

    @property
    def platform_type(self) -> PlatformType:
        """Get platform type."""
        ...

    @property
    def platform_name(self) -> str:
        """Get platform display name."""
        ...


# Platform Manager Interface
class IPlatformManager(ABC):
    """Abstract base class for platform management."""

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize platform manager."""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """Shutdown platform manager."""
        pass

    @abstractmethod
    def get_available_platforms(self) -> List[str]:
        """Get list of available platforms."""
        pass

    @abstractmethod
    def is_platform_supported(self, platform: str) -> bool:
        """Check if platform is supported on current OS."""
        pass

    @abstractmethod
    async def create_executor(
        self, platform: str, config: Dict[str, Any]
    ) -> Optional[IExecutor]:
        """Create executor for specified platform."""
        pass

    @abstractmethod
    def get_executor(self, platform: str) -> Optional[IExecutor]:
        """Get existing executor instance."""
        pass

    @abstractmethod
    async def remove_executor(self, platform: str) -> bool:
        """Remove executor instance."""
        pass

    @abstractmethod
    async def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        """Perform health check on all executors."""
        pass


# Configuration Interfaces
@runtime_checkable
class IConfigurable(Protocol):
    """Protocol for configurable components."""

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        ...

    def get_required_config_keys(self) -> List[str]:
        """Get required configuration keys."""
        ...


# Event Interfaces
@runtime_checkable
class IEventEmitter(Protocol):
    """Protocol for event emission."""

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event."""
        ...

    def subscribe_to_events(self, event_type: str, callback) -> str:
        """Subscribe to events."""
        ...

    def unsubscribe_from_events(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        ...


# Context Managers
@asynccontextmanager
async def executor_context(executor: IExecutor):
    """Context manager for executor lifecycle."""
    try:
        if not executor.is_connected:
            await executor.connect()
        yield executor
    finally:
        if executor.is_connected:
            await executor.disconnect()


@asynccontextmanager
async def platform_manager_context(manager: IPlatformManager):
    """Context manager for platform manager lifecycle."""
    try:
        await manager.initialize()
        yield manager
    finally:
        await manager.shutdown()
