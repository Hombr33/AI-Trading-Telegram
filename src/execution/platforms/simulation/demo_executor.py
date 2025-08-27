"""
Demo executor for simulated trading without real market data.
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from decimal import Decimal
import random

from ....core.logging import get_logger, log_trade_event, log_error_with_context
from ....core.error_handler import with_error_handling, ErrorContext
from ....core.exceptions import TradingBotException
from ...interfaces import (
    PlatformType, OrderType, OrderSide, OrderStatus, HealthStatus,
    OrderRequest, OrderResponse, PositionData, AccountInfo, MarketData,
    IExecutor
)
from ...base_executor import BaseExecutor

logger = get_logger(__name__)


class DemoExecutor(BaseExecutor):
    """Demo executor for testing and simulation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.platform_type = PlatformType.DEMO
        self.connected = False
        self.account_info = None
        self.is_demo = True
        
        # Simulated state
        self._orders: Dict[str, OrderResponse] = {}
        self._positions: Dict[str, PositionData] = {}
        self._balance = {"USD": 10000.0}  # Demo balance
        self._last_prices: Dict[str, float] = {}
        
        # Simulation parameters
        self._latency_ms = config.get("latency_ms", 50)  # Simulated latency
        self._failure_rate = config.get("failure_rate", 0.01)  # 1% failure rate
        self._price_volatility = config.get("price_volatility", 0.001)  # Price movement
    
    @property
    def platform_name(self) -> str:
        return "Demo Trading"
    
    @property
    def is_connected(self) -> bool:
        return self.connected
    
    @with_error_handling("connect", fallback_value=False)
    async def connect(self) -> bool:
        """Connect to demo platform (always succeeds)."""
        await asyncio.sleep(self._latency_ms / 1000.0)  # Simulate connection time
        
        self.connected = True
        self.account_info = {
            "account_id": "demo_account_001",
            "account_type": "demo",
            "currency": "USD",
            "leverage": 1.0,
            "margin_mode": "isolated"
        }
        
        logger.info("Connected to demo trading platform")
        return True
    
    @with_error_handling("disconnect", fallback_value=False)
    async def disconnect(self) -> bool:
        """Disconnect from demo platform."""
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        self.connected = False
        logger.info("Disconnected from demo trading platform")
        return True
    
    @with_error_handling("test_connection", fallback_value=False)
    async def test_connection(self) -> bool:
        """Test demo connection."""
        await asyncio.sleep(self._latency_ms / 1000.0)
        return self.connected
    
    @with_error_handling("get_account_info", fallback_value=None)
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get demo account information."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        return AccountInfo(
            account_id="demo_account_001",
            balance=self._balance.copy(),
            equity=sum(self._balance.values()),
            margin_used=0.0,
            margin_available=sum(self._balance.values()),
            is_demo=True,
            platform="demo",
            timestamp=datetime.now(timezone.utc),
            permissions=["trade", "read"]
        )
    
    @with_error_handling("get_balance", fallback_value=0.0)
    async def get_balance(self, asset: str = "USD") -> float:
        """Get demo account balance."""
        if not self.connected:
            return 0.0
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        return self._balance.get(asset, 0.0)
    
    @with_error_handling("place_order", fallback_value=None)
    async def place_order(self, request: OrderRequest) -> OrderResponse:
        """Place a simulated order."""
        if not self.connected:
            raise RuntimeError("Not connected to demo platform")
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        # Simulate occasional failures
        if random.random() < self._failure_rate:
            raise RuntimeError("Simulated order placement failure")
        
        # Generate order ID
        order_id = f"demo_{uuid.uuid4().hex[:8]}"
        
        # Simulate order execution
        current_price = self._get_simulated_price(request.symbol)
        filled_amount = request.amount
        
        # Create order response
        response = OrderResponse(
            order_id=order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            amount=request.amount,
            price=request.price or current_price,
            filled=filled_amount,
            remaining=0.0,
            status=OrderStatus.FILLED.value,
            timestamp=datetime.now(timezone.utc),
            platform="demo",
            fees={"USD": request.amount * 0.001},  # Simulate 0.1% fee
            metadata={"simulated": True}
        )
        
        # Store order
        self._orders[order_id] = response
        
        # Update positions if filled
        if response.status == OrderStatus.FILLED.value:
            self._update_position(response)
        
        logger.info(f"Demo order placed: {order_id} for {request.symbol}")
        return response
    
    @with_error_handling("cancel_order", fallback_value=None)
    async def cancel_order(self, order_id: str) -> OrderResponse:
        """Cancel a simulated order."""
        if not self.connected:
            raise RuntimeError("Not connected to demo platform")
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self._orders[order_id]
        if order.status in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value]:
            raise ValueError(f"Cannot cancel order {order_id} with status {order.status}")
        
        # Update order status
        order.status = OrderStatus.CANCELLED.value
        order.timestamp = datetime.now(timezone.utc)
        
        logger.info(f"Demo order cancelled: {order_id}")
        return order
    
    @with_error_handling("modify_order", fallback_value=None)
    async def modify_order(self, order_id: str, **kwargs) -> OrderResponse:
        """Modify a simulated order."""
        if not self.connected:
            raise RuntimeError("Not connected to demo platform")
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self._orders[order_id]
        
        # Update order fields
        if "price" in kwargs:
            order.price = kwargs["price"]
        if "amount" in kwargs:
            order.amount = kwargs["amount"]
            order.remaining = max(0, order.amount - order.filled)
        
        order.timestamp = datetime.now(timezone.utc)
        
        logger.info(f"Demo order modified: {order_id}")
        return order
    
    @with_error_handling("get_order", fallback_value=None)
    async def get_order(self, order_id: str) -> Optional[OrderResponse]:
        """Get demo order details."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        return self._orders.get(order_id)
    
    @with_error_handling("get_orders", fallback_value=[])
    async def get_orders(self, symbol: Optional[str] = None) -> List[OrderResponse]:
        """Get all demo orders."""
        if not self.connected:
            return []
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        orders = list(self._orders.values())
        if symbol:
            orders = [order for order in orders if order.symbol == symbol]
        
        return orders
    
    @with_error_handling("get_positions", fallback_value=[])
    async def get_positions(self, symbol: Optional[str] = None) -> List[PositionData]:
        """Get all demo positions."""
        if not self.connected:
            return []
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        positions = list(self._positions.values())
        if symbol:
            positions = [pos for pos in positions if pos.symbol == symbol]
        
        return positions
    
    @with_error_handling("close_position", fallback_value=None)
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> OrderResponse:
        """Close a demo position."""
        if not self.connected:
            raise RuntimeError("Not connected to demo platform")
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        if position_id not in self._positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self._positions[position_id]
        close_volume = volume or position.size
        
        # Create closing order
        order_request = OrderRequest(
            symbol=position.symbol,
            side="sell" if position.side == "buy" else "buy",
            type="market",
            amount=close_volume
        )
        
        # Execute closing order
        response = await self.place_order(order_request)
        
        # Update position
        position.size -= close_volume
        if position.size <= 0:
            del self._positions[position_id]
        
        logger.info(f"Demo position closed: {position_id}")
        return response
    
    @with_error_handling("get_symbol_info", fallback_value=None)
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get demo symbol information."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        # Return simulated symbol info
        return {
            "symbol": symbol,
            "base_asset": symbol.split("/")[0] if "/" in symbol else symbol[:3],
            "quote_asset": symbol.split("/")[1] if "/" in symbol else symbol[3:],
            "min_quantity": 0.001,
            "max_quantity": 10000.0,
            "tick_size": 0.01,
            "is_trading": True,
            "fees": {"maker": 0.001, "taker": 0.001}
        }
    
    @with_error_handling("get_ticker", fallback_value=None)
    async def get_ticker(self, symbol: str) -> Optional[MarketData]:
        """Get demo ticker data."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        price = self._get_simulated_price(symbol)
        
        return MarketData(
            symbol=symbol,
            price=price,
            bid=price * 0.9995,  # Simulate bid/ask spread
            ask=price * 1.0005,
            volume_24h=random.uniform(1000000, 10000000),
            change_24h=random.uniform(-5.0, 5.0),
            timestamp=datetime.now(timezone.utc)
        )
    
    @with_error_handling("get_klines", fallback_value=[])
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get demo kline data."""
        if not self.connected:
            return []
        
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        # Generate simulated klines
        base_price = self._get_simulated_price(symbol)
        klines = []
        
        for i in range(limit):
            # Simple random walk for price simulation
            price_change = random.uniform(-0.02, 0.02)
            open_price = base_price * (1 + price_change)
            high_price = open_price * (1 + abs(price_change))
            low_price = open_price * (1 - abs(price_change))
            close_price = random.uniform(low_price, high_price)
            
            kline = {
                "timestamp": datetime.now(timezone.utc).timestamp() - (i * 60),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": random.uniform(1000, 50000)
            }
            klines.append(kline)
        
        return list(reversed(klines))  # Return chronological order
    
    def _get_simulated_price(self, symbol: str) -> float:
        """Get simulated price for symbol."""
        # Use cached price with small random movement
        if symbol in self._last_prices:
            price = self._last_prices[symbol]
            # Add some price movement
            price *= (1 + random.uniform(-self._price_volatility, self._price_volatility))
        else:
            # Initial price based on symbol hash for consistency
            price = 100.0 + (hash(symbol) % 900)  # Price between 100-1000
        
        self._last_prices[symbol] = price
        return round(price, 2)
    
    def _update_position(self, order: OrderResponse) -> None:
        """Update position based on filled order."""
        position_id = f"{order.symbol}_{order.side}"
        
        if position_id in self._positions:
            position = self._positions[position_id]
            if order.side == position.side:
                # Add to position
                total_size = position.size + order.filled
                avg_price = ((position.entry_price * position.size) + (order.price * order.filled)) / total_size
                position.size = total_size
                position.entry_price = avg_price
            else:
                # Reduce position
                position.size = max(0, position.size - order.filled)
                if position.size == 0:
                    del self._positions[position_id]
        else:
            # Create new position
            self._positions[position_id] = PositionData(
                position_id=position_id,
                symbol=order.symbol,
                side=order.side,
                size=order.filled,
                entry_price=order.price,
                current_price=order.price,
                unrealized_pnl=0.0,
                realized_pnl=0.0,
                leverage=1.0,
                margin=order.price * order.filled,
                timestamp=datetime.now(timezone.utc),
                platform="demo"
            )
    
    @with_error_handling("health_check", fallback_value={"status": "unknown"})
    async def health_check(self) -> Dict[str, Any]:
        """Perform demo health check."""
        await asyncio.sleep(self._latency_ms / 1000.0)
        
        return {
            "status": "healthy" if self.connected else "unhealthy",
            "platform": "demo",
            "connected": self.connected,
            "orders_count": len(self._orders),
            "positions_count": len(self._positions),
            "balance": self._balance.copy(),
            "latency_ms": self._latency_ms,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get demo platform status."""
        return {
            "platform": self.platform_name,
            "type": self.platform_type.value,
            "connected": self.connected,
            "is_demo": self.is_demo,
            "account_info": self.account_info,
            "orders_count": len(self._orders),
            "positions_count": len(self._positions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
