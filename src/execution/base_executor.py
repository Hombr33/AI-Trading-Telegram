"""
Base executor implementation for all trading platforms.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
import time

from .interfaces import (
    IExecutor, PlatformType, OrderRequest, OrderResponse, 
    PositionData, AccountInfo, MarketData, OrderStatus, HealthStatus
)
from .monitoring import get_executor_monitor
from ..core.logging import get_logger, log_trade_event
from ..core.error_handler import with_error_handling
from ..core.exceptions import TradingBotException

logger = get_logger(__name__)


class BaseExecutor(ABC):
    """Production-grade base executor implementation."""
    
    def __init__(self, config: Dict[str, Any], platform_type: PlatformType):
        self.config = config
        self.platform_type = platform_type
        self.connected = False
        self.account_info = None
        self.is_demo = config.get("demo", False)
        
        # Monitoring and metrics
        self._monitor = get_executor_monitor()
        self._connection_attempts = 0
        self._last_health_check = None
        self._performance_metrics = {}
        
        # Connection settings
        self._max_retries = config.get("max_retries", 3)
        self._retry_delay = config.get("retry_delay", 1.0)
        self._timeout = config.get("timeout", 30.0)
        
        # Register with monitor
        self._monitor.register_executor(self.platform_name, self)
        
    def __del__(self):
        """Cleanup on destruction."""
        try:
            self._monitor.unregister_executor(self.platform_name)
        except:
            pass
    
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Platform display name."""
        pass
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to platform."""
        return self.connected
    
    # Connection Management with retry logic and monitoring
    async def connect_with_retry(self) -> bool:
        """Connect to platform with retry logic."""
        for attempt in range(self._max_retries):
            try:
                self._connection_attempts += 1
                start_time = time.time()
                
                result = await asyncio.wait_for(
                    self._connect_impl(),
                    timeout=self._timeout
                )
                
                response_time = (time.time() - start_time) * 1000
                
                if result:
                    self.connected = True
                    self._monitor.record_connection_event(self.platform_name, "connected")
                    self._monitor.record_api_call(
                        self.platform_name, "connect", response_time, True
                    )
                    logger.info(f"Connected to {self.platform_name} (attempt {attempt + 1})")
                    return True
                else:
                    logger.warning(f"Connection failed for {self.platform_name} (attempt {attempt + 1})")
                    
            except asyncio.TimeoutError:
                logger.error(f"Connection timeout for {self.platform_name} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Connection error for {self.platform_name}: {e} (attempt {attempt + 1})")
                self._monitor.record_connection_event(self.platform_name, "connection_failed")
                
            if attempt < self._max_retries - 1:
                await asyncio.sleep(self._retry_delay * (attempt + 1))  # Exponential backoff
        
        logger.error(f"Failed to connect to {self.platform_name} after {self._max_retries} attempts")
        return False
    
    async def connect(self) -> bool:
        """Connect to trading platform."""
        return await self.connect_with_retry()
    
    @abstractmethod
    async def _connect_impl(self) -> bool:
        """Platform-specific connection implementation."""
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
    
    # Order Management with monitoring and validation
    async def place_order(self, request: OrderRequest) -> OrderResponse:
        """Place order with monitoring and validation."""
        start_time = time.time()
        success = False
        
        try:
            # Validate order request
            self._validate_order_request(request)
            
            # Execute platform-specific order placement
            response = await self._place_order_impl(request)
            
            success = True
            response_time = (time.time() - start_time) * 1000
            
            # Record metrics
            self._monitor.record_order_placed(self.platform_name, response_time, success)
            self._monitor.record_api_call(self.platform_name, "place_order", response_time, success)
            
            # Log trade event
            log_trade_event("order_placed", {
                "platform": self.platform_name,
                "order_id": response.order_id,
                "symbol": response.symbol,
                "side": response.side,
                "type": response.type,
                "amount": response.amount,
                "price": response.price,
                "status": response.status
            })
            
            return response
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._monitor.record_order_placed(self.platform_name, response_time, False)
            self._monitor.record_api_call(self.platform_name, "place_order", response_time, False)
            
            logger.error(f"Order placement failed on {self.platform_name}: {e}")
            raise
    
    def _validate_order_request(self, request: OrderRequest) -> None:
        """Validate order request parameters."""
        if not request.symbol:
            raise ValueError("Symbol is required")
        if not request.side or request.side not in ["buy", "sell"]:
            raise ValueError("Invalid order side")
        if not request.type or request.type not in ["market", "limit", "stop", "stop_limit"]:
            raise ValueError("Invalid order type")
        if request.amount <= 0:
            raise ValueError("Amount must be positive")
        if request.type in ["limit", "stop_limit"] and (not request.price or request.price <= 0):
            raise ValueError("Price is required for limit orders")
    
    @abstractmethod
    async def _place_order_impl(self, request: OrderRequest) -> OrderResponse:
        """Platform-specific order placement implementation."""
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
    
    @with_error_handling("health_check", fallback_value={"status": "unknown"})
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check with metrics."""
        start_time = time.time()
        self._last_health_check = datetime.now(timezone.utc)
        
        try:
            if not self.connected:
                return {
                    "status": HealthStatus.UNHEALTHY.value,
                    "platform": self.platform_name,
                    "connected": False,
                    "error": "Not connected",
                    "response_time_ms": (time.time() - start_time) * 1000,
                    "timestamp": self._last_health_check.isoformat()
                }
            
            # Test connection
            connection_ok = await self.test_connection()
            
            # Get account info to verify API access
            account_info = None
            try:
                account_info = await self.get_account_info()
            except Exception as e:
                logger.warning(f"Failed to get account info during health check: {e}")
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine overall health status
            if connection_ok and account_info is not None:
                status = HealthStatus.HEALTHY
                error = None
            elif connection_ok:
                status = HealthStatus.DEGRADED
                error = "Connection OK but API access limited"
            else:
                status = HealthStatus.UNHEALTHY
                error = "Connection test failed"
            
            # Update account balance metric if available
            if account_info and hasattr(account_info, 'balance'):
                for currency, balance in account_info.balance.items():
                    self._monitor.set_account_balance(self.platform_name, balance, currency)
            
            return {
                "status": status.value,
                "platform": self.platform_name,
                "connected": self.connected,
                "connection_test": connection_ok,
                "api_access": account_info is not None,
                "connection_attempts": self._connection_attempts,
                "response_time_ms": response_time,
                "timestamp": self._last_health_check.isoformat(),
                "error": error
            }
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"{self.platform_name} health check failed: {e}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "platform": self.platform_name,
                "connected": self.connected,
                "error": str(e),
                "response_time_ms": response_time,
                "timestamp": self._last_health_check.isoformat()
            }
    
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
