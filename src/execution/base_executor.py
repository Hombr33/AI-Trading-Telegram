"""
Base executor interface for all trading platforms.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from enum import Enum

from ..core.logging import get_logger, log_trade_event
from ..core.error_handler import with_error_handling
from ..core.exceptions import TradingBotException

logger = get_logger(__name__)


class PlatformType(Enum):
    """Trading platform types."""
    MT5 = "mt5"
    BINANCE = "binance"
    BYBIT = "bybit"
    BITGET = "bitget"
    DEMO = "demo"


class OrderType(Enum):
    """Universal order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Universal order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Universal order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class BaseExecutor(ABC):
    """Base executor interface for all trading platforms."""
    
    def __init__(self, config, platform_type: PlatformType):
        self.config = config
        self.platform_type = platform_type
        self.connected = False
        self.account_info = None
        self.is_demo = False
        
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform display name."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to platform."""
        return self.connected
    
    # Connection Management
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to trading platform."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from trading platform."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test platform connection."""
        pass
    
    # Account Information
    @abstractmethod
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_balance(self, asset: str = "USD") -> float:
        """Get account balance for specific asset."""
        pass
    
    # Order Management
    @abstractmethod
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place a new order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an existing order."""
        pass
    
    @abstractmethod
    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify an existing order."""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        pass
    
    @abstractmethod
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all orders."""
        pass
    
    # Position Management
    @abstractmethod
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all positions."""
        pass
    
    @abstractmethod
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close position."""
        pass
    
    # Market Data
    @abstractmethod
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        pass
    
    @abstractmethod
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        pass
    
    @abstractmethod
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical kline/candlestick data."""
        pass
    
    # Utility Methods
    def standardize_symbol(self, symbol: str) -> str:
        """Standardize symbol format for the platform."""
        return symbol.upper().replace("/", "").replace("-", "")
    
    def calculate_position_size(self, 
                              balance: float, 
                              risk_pct: float, 
                              entry_price: float, 
                              stop_loss: float,
                              leverage: float = 1.0) -> float:
        """Calculate position size based on risk management."""
        if stop_loss == 0 or entry_price == 0:
            return 0.0
        
        risk_amount = balance * (risk_pct / 100)
        price_diff = abs(entry_price - stop_loss)
        position_size = (risk_amount / price_diff) * leverage
        
        return round(position_size, 6)
    
    def format_order_data(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Format order data to universal format."""
        return {
            "order_id": order.get("id", order.get("order_id", "")),
            "symbol": order.get("symbol", ""),
            "side": order.get("side", OrderSide.BUY.value),
            "type": order.get("type", OrderType.MARKET.value),
            "amount": float(order.get("amount", order.get("volume", 0))),
            "price": float(order.get("price", 0)),
            "filled": float(order.get("filled", 0)),
            "remaining": float(order.get("remaining", 0)),
            "status": order.get("status", OrderStatus.PENDING.value),
            "timestamp": order.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "platform": self.platform_type.value
        }
    
    def format_position_data(self, position: Dict[str, Any]) -> Dict[str, Any]:
        """Format position data to universal format."""
        return {
            "position_id": position.get("id", position.get("position_id", "")),
            "symbol": position.get("symbol", ""),
            "side": position.get("side", OrderSide.BUY.value),
            "size": float(position.get("size", position.get("volume", 0))),
            "entry_price": float(position.get("entry_price", position.get("price_open", 0))),
            "current_price": float(position.get("current_price", position.get("mark_price", 0))),
            "unrealized_pnl": float(position.get("unrealized_pnl", position.get("profit", 0))),
            "realized_pnl": float(position.get("realized_pnl", 0)),
            "timestamp": position.get("timestamp", datetime.now(timezone.utc).isoformat()),
            "platform": self.platform_type.value
        }
    
    @with_error_handling("health_check", fallback_value=False)
    async def health_check(self) -> bool:
        """Perform health check."""
        try:
            if not self.connected:
                return False
            
            # Test basic connectivity
            return await self.test_connection()
        except Exception as e:
            logger.error(f"{self.platform_name} health check failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get platform status."""
        return {
            "platform": self.platform_name,
            "type": self.platform_type.value,
            "connected": self.connected,
            "is_demo": self.is_demo,
            "account_info": self.account_info,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
