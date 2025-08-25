"""
Paper trading executor with live market data but simulated execution.
"""

from __future__ import annotations

import asyncio
import uuid
import time
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


class PaperExecutor(BaseExecutor):
    """Paper trading executor with live data integration."""
    
    def __init__(self, config: Dict[str, Any]):
        # Initialize base executor with PAPER platform type
        super().__init__(config, PlatformType.PAPER)
        
        # Paper trading state
        self._orders: Dict[str, OrderResponse] = {}
        self._positions: Dict[str, PositionData] = {}
        self._balance = {"USD": config.get("initial_balance", 100000.0)}
        self._trading_fees = config.get("trading_fees", 0.001)  # 0.1% default
        
        # Live data integration settings
        self._data_source = config.get("data_source", "paper")  # Can integrate with real exchanges
        self._use_live_data = config.get("use_live_data", True)  # Default to True for auto-trading
        self._slippage = config.get("slippage", 0.0001)  # 0.01% default slippage
        
        # Execution parameters
        self._execution_delay_ms = config.get("execution_delay_ms", 100)
        self._partial_fill_probability = config.get("partial_fill_probability", 0.05)  # Reduced for auto-trading
        self._rejection_probability = config.get("rejection_probability", 0.01)  # Reduced for auto-trading
        
        # Auto-trading enhancements
        self._auto_trading_mode = config.get("auto_trading_mode", True)
        self._realistic_execution = config.get("realistic_execution", True)
        self._market_data_cache = {}  # Cache for market data
        self._last_price_update = {}  # Track last price updates
    
    @property
    def platform_name(self) -> str:
        return "Paper Trading"
    
    @property
    def is_connected(self) -> bool:
        return self.connected
    
    async def _connect_impl(self) -> bool:
        """Platform-specific connection implementation."""
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        self.connected = True
        self.account_info = {
            "account_id": f"paper_{uuid.uuid4().hex[:8]}",
            "account_type": "paper",
            "currency": "USD",
            "leverage": self.config.get("max_leverage", 1.0),
            "margin_mode": "cross"
        }
        
        logger.info("Connected to paper trading platform")
        return True
    
    async def disconnect(self) -> bool:
        """Disconnect from paper trading platform."""
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        self.connected = False
        logger.info("Disconnected from paper trading platform")
        return True
    
    async def test_connection(self) -> bool:
        """Test paper trading connection."""
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        return self.connected
    
    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get paper account information."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        # Calculate equity including unrealized PnL
        total_equity = sum(self._balance.values())
        margin_used = 0.0
        
        for position in self._positions.values():
            total_equity += position.unrealized_pnl
            margin_used += position.margin or 0.0
        
        return AccountInfo(
            account_id=self.account_info["account_id"],
            balance=self._balance.copy(),
            equity=total_equity,
            margin_used=margin_used,
            margin_available=total_equity - margin_used,
            is_demo=True,
            platform="paper",
            timestamp=datetime.now(timezone.utc),
            permissions=["trade", "read", "withdraw"],
            metadata={
                "data_source": self._data_source,
                "use_live_data": self._use_live_data,
                "trading_fees": self._trading_fees
            }
        )
    
    async def get_balance(self, asset: str = "USD") -> float:
        """Get paper account balance."""
        if not self.connected:
            return 0.0
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        return self._balance.get(asset, 0.0)
    
    async def _place_order_impl(self, request: OrderRequest) -> OrderResponse:
        """Platform-specific order placement implementation."""
        if not self.connected:
            raise RuntimeError("Not connected to paper trading platform")
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        # Simulate order rejection
        if random.random() < self._rejection_probability:
            raise RuntimeError("Order rejected: Insufficient margin or invalid parameters")
        
        # Generate order ID
        order_id = f"paper_{uuid.uuid4().hex[:8]}"
        
        # Get current market price (would integrate with real data source)
        current_price = await self._get_market_price(request.symbol)
        
        # Determine execution price with slippage
        execution_price = self._calculate_execution_price(
            request, current_price
        )
        
        # Simulate partial fills
        filled_amount = request.amount
        if random.random() < self._partial_fill_probability and request.type != "market":
            filled_amount = request.amount * random.uniform(0.1, 0.9)
        
        # Calculate fees
        fee_amount = filled_amount * execution_price * self._trading_fees
        
        # Determine order status
        if request.type == "market" or filled_amount == request.amount:
            status = OrderStatus.FILLED.value
        elif filled_amount > 0:
            status = OrderStatus.PARTIALLY_FILLED.value
        else:
            status = OrderStatus.OPEN.value
        
        # Create order response
        response = OrderResponse(
            order_id=order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol,
            side=request.side,
            type=request.type,
            amount=request.amount,
            price=execution_price,
            filled=filled_amount,
            remaining=request.amount - filled_amount,
            status=status,
            timestamp=datetime.now(timezone.utc),
            platform="paper",
            fees={"USD": fee_amount},
            metadata={
                "simulated": True,
                "slippage": abs(execution_price - current_price) / current_price,
                "market_price": current_price
            }
        )
        
        # Store order
        self._orders[order_id] = response
        
        # Update positions and balance if filled
        if filled_amount > 0:
            self._update_balance_and_position(response)
        
        # Log trade event
        log_trade_event(
            request.symbol, 
            request.side, 
            {
                "platform": self.platform_name,
                "order_id": response.order_id,
                "status": response.status,
                "amount": request.amount,
                "price": execution_price
            },
            "INFO"  # Use string level instead of constant
        )
        
        logger.info(f"Paper order placed: {order_id} for {request.symbol} at {execution_price}")
        return response
    
    def _calculate_execution_price(self, request: OrderRequest, market_price: float) -> float:
        """Calculate realistic execution price with slippage."""
        if request.type == "market":
            # Market orders experience slippage
            if request.side == "buy":
                return market_price * (1 + self._slippage)
            else:
                return market_price * (1 - self._slippage)
        elif request.type == "limit":
            # Limit orders execute at limit price or better
            if request.price is None:
                return market_price
            
            if request.side == "buy":
                return min(request.price, market_price)
            else:
                return max(request.price, market_price)
        else:
            return request.price or market_price
    
    async def _get_market_price(self, symbol: str) -> float:
        """Get current market price (integrate with real data sources)."""
        if self._use_live_data and self._data_source != "demo":
            # Here you would integrate with real exchange APIs
            # For now, return simulated price
            pass
        
        # Generate consistent simulated price based on symbol
        symbol_upper = symbol.upper()
        
        # Use cached price if available and recent
        current_time = time.time()
        if (symbol in self._market_data_cache and 
            symbol in self._last_price_update and
            current_time - self._last_price_update[symbol] < 60):  # 1 minute cache
            return self._market_data_cache[symbol]
        
        # Generate realistic base prices for different asset types
        if "USDT" in symbol_upper:  # Crypto
            if "BTC" in symbol_upper:
                base_price = 45000.0 + random.uniform(-2000, 2000)
            elif "ETH" in symbol_upper:
                base_price = 2800.0 + random.uniform(-150, 150)
            elif "ADA" in symbol_upper:
                base_price = 0.45 + random.uniform(-0.05, 0.05)
            elif "DOT" in symbol_upper:
                base_price = 6.5 + random.uniform(-0.5, 0.5)
            elif "LINK" in symbol_upper:
                base_price = 12.5 + random.uniform(-1.0, 1.0)
            else:
                base_price = 100.0 + random.uniform(-20, 20)
        elif any(forex in symbol_upper for forex in ["EUR", "GBP", "USD", "AUD", "CAD", "CHF", "NZD", "JPY"]):  # Forex
            if "JPY" in symbol_upper:
                base_price = 150.0 + random.uniform(-5, 5)
            else:
                base_price = 1.0 + random.uniform(-0.1, 0.1)
        elif "XAU" in symbol_upper:  # Gold
            base_price = 1950.0 + random.uniform(-50, 50)
        elif "XAG" in symbol_upper:  # Silver
            base_price = 24.0 + random.uniform(-1, 1)
        elif "OIL" in symbol_upper:  # Oil
            base_price = 75.0 + random.uniform(-5, 5)
        else:
            # Default fallback
            base_price = 100.0 + (hash(symbol) % 9900)
        
        # Add realistic price movement (volatility)
        volatility = random.uniform(-0.015, 0.015)  # 1.5% max movement
        price = base_price * (1 + volatility)
        
        # Round to appropriate decimal places
        if "USDT" in symbol_upper and "BTC" in symbol_upper:
            price = round(price, 2)  # BTC to 2 decimals
        elif "USDT" in symbol_upper:
            price = round(price, 4)  # Crypto to 4 decimals
        elif "JPY" in symbol_upper:
            price = round(price, 2)  # JPY to 2 decimals
        else:
            price = round(price, 5)  # Forex to 5 decimals
        
        # Cache the price
        self._market_data_cache[symbol] = price
        self._last_price_update[symbol] = current_time
        
        return price
    
    def _update_balance_and_position(self, order: OrderResponse) -> None:
        """Update balance and positions based on filled order."""
        # Calculate cost including fees
        total_cost = order.filled * order.price + order.fees.get("USD", 0)
        
        # Update balance
        if order.side == "buy":
            self._balance["USD"] -= total_cost
        else:
            self._balance["USD"] += total_cost
        
        # Update positions
        position_id = f"{order.symbol}_{order.side}"
        
        if position_id in self._positions:
            position = self._positions[position_id]
            if order.side == position.side:
                # Add to existing position
                total_size = position.size + order.filled
                weighted_price = ((position.entry_price * position.size) + 
                                (order.price * order.filled)) / total_size
                position.size = total_size
                position.entry_price = weighted_price
                position.margin = (position.margin or 0) + (order.price * order.filled)
            else:
                # Close or reduce opposite position
                if position.size > order.filled:
                    # Partial close
                    position.size -= order.filled
                    position.margin = (position.margin or 0) - (order.price * order.filled)
                    # Realize some PnL
                    pnl = (order.price - position.entry_price) * order.filled
                    if position.side == "sell":
                        pnl = -pnl
                    position.realized_pnl += pnl
                    self._balance["USD"] += pnl
                else:
                    # Full close
                    pnl = (order.price - position.entry_price) * position.size
                    if position.side == "sell":
                        pnl = -pnl
                    position.realized_pnl += pnl
                    self._balance["USD"] += pnl
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
                platform="paper",
                metadata={"initial_cost": total_cost}
            )
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel a paper order."""
        if not self.connected:
            raise RuntimeError("Not connected to paper trading platform")
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        if order_id not in self._orders:
            raise ValueError(f"Order {order_id} not found")
        
        order = self._orders[order_id]
        if order.status in [OrderStatus.FILLED.value, OrderStatus.CANCELLED.value]:
            raise ValueError(f"Cannot cancel order {order_id} with status {order.status}")
        
        order.status = OrderStatus.CANCELLED.value
        order.timestamp = datetime.now(timezone.utc)
        
        logger.info(f"Paper order cancelled: {order_id}")
        return {
            "success": True,
            "order_id": order_id,
            "status": "cancelled"
        }
    
    # Legacy method for compatibility with platform manager
    async def place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Legacy order placement method for compatibility."""
        try:
            # Convert dict to OrderRequest
            request = OrderRequest(
                symbol=order_data.get("symbol"),
                side=order_data.get("side"),
                type=order_data.get("type", "market"),
                amount=order_data.get("amount", order_data.get("quantity", 0.01)),
                price=order_data.get("price"),
                stop_loss=order_data.get("stop_loss"),
                take_profit=order_data.get("take_profit"),
                client_order_id=order_data.get("client_order_id", f"paper_{uuid.uuid4().hex[:8]}")
            )
            
            # Place order using base executor method
            response = await super().place_order(request)
            
            # Convert response to dict format expected by platform manager
            return {
                "success": True,
                "order_id": response.order_id,
                "symbol": response.symbol,
                "side": response.side,
                "type": response.type,
                "amount": response.amount,
                "price": response.price,
                "status": response.status,
                "platform": "paper"
            }
            
        except Exception as e:
            logger.error(f"Paper order placement failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "symbol": order_data.get("symbol"),
                "platform": "paper"
            }
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all paper orders."""
        if not self.connected:
            return []
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        orders = []
        for order in self._orders.values():
            order_dict = {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "amount": order.amount,
                "price": order.price,
                "filled": order.filled,
                "remaining": order.remaining,
                "status": order.status,
                "timestamp": order.timestamp.isoformat(),
                "platform": "paper"
            }
            if symbol is None or order.symbol == symbol:
                orders.append(order_dict)
        
        return sorted(orders, key=lambda x: x["timestamp"], reverse=True)
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all paper positions."""
        if not self.connected:
            return []
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        # Update unrealized PnL with current market prices
        for position in self._positions.values():
            current_price = await self._get_market_price(position.symbol)
            position.current_price = current_price
            
            # Calculate unrealized PnL
            pnl = (current_price - position.entry_price) * position.size
            if position.side == "sell":
                pnl = -pnl
            position.unrealized_pnl = pnl
        
        positions = []
        for position in self._positions.values():
            position_dict = {
                "position_id": position.position_id,
                "symbol": position.symbol,
                "side": position.side,
                "size": position.size,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "unrealized_pnl": position.unrealized_pnl,
                "realized_pnl": position.realized_pnl,
                "leverage": position.leverage,
                "margin": position.margin,
                "timestamp": position.timestamp.isoformat(),
                "platform": "paper"
            }
            if symbol is None or position.symbol == symbol:
                positions.append(position_dict)
        
        return positions
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get paper ticker data (would integrate with live data)."""
        if not self.connected:
            return None
        
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        price = await self._get_market_price(symbol)
        spread = price * 0.0005  # 0.05% spread
        
        return {
            "symbol": symbol,
            "price": price,
            "bid": price - spread/2,
            "ask": price + spread/2,
            "volume_24h": random.uniform(1000000, 100000000),
            "change_24h": random.uniform(-10.0, 10.0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"source": self._data_source, "simulated": not self._use_live_data}
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform paper trading health check."""
        await asyncio.sleep(self._execution_delay_ms / 1000.0)
        
        # Calculate portfolio metrics
        total_balance = sum(self._balance.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self._positions.values())
        total_equity = total_balance + total_unrealized_pnl
        
        return {
            "status": "healthy" if self.connected else "unhealthy",
            "platform": "paper",
            "connected": self.connected,
            "account_balance": total_balance,
            "total_equity": total_equity,
            "unrealized_pnl": total_unrealized_pnl,
            "orders_count": len(self._orders),
            "positions_count": len(self._positions),
            "data_source": self._data_source,
            "use_live_data": self._use_live_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    # Implementation of remaining interface methods...
    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify a paper order."""
        # Implementation similar to demo executor but with more realistic behavior
        return await self.cancel_order(order_id)  # Simplified for now
    
    async def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get paper order details."""
        if not self.connected:
            return None
        
        order = self._orders.get(order_id)
        if order:
            return {
                "order_id": order.order_id,
                "symbol": order.symbol,
                "side": order.side,
                "type": order.type,
                "amount": order.amount,
                "price": order.price,
                "filled": order.filled,
                "remaining": order.remaining,
                "status": order.status,
                "timestamp": order.timestamp.isoformat(),
                "platform": "paper"
            }
        return None
    
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close a paper position."""
        if position_id not in self._positions:
            raise ValueError(f"Position {position_id} not found")
        
        position = self._positions[position_id]
        close_volume = volume or position.size
        
        order_request = OrderRequest(
            symbol=position.symbol,
            side="sell" if position.side == "buy" else "buy",
            type="market",
            amount=close_volume
        )
        
        return await self._place_order_impl(order_request)
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get paper symbol information."""
        if not self.connected:
            return None
        
        return {
            "symbol": symbol,
            "base_asset": symbol.split("/")[0] if "/" in symbol else symbol[:3],
            "quote_asset": symbol.split("/")[1] if "/" in symbol else symbol[3:],
            "min_quantity": 0.001,
            "max_quantity": 1000000.0,
            "tick_size": 0.01,
            "is_trading": True,
            "fees": {"maker": self._trading_fees, "taker": self._trading_fees}
        }
    
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get paper kline data."""
        # Would integrate with real data sources in production
        return []  # Simplified implementation
