"""
Binance exchange executor for cryptocurrency trading.
"""

from __future__ import annotations

import asyncio
import time
import hmac
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from urllib.parse import urlencode

import aiohttp

from ...core.logging import get_logger, log_trade_event, log_error_with_context
from ...core.error_handler import with_error_handling, ErrorContext
from ...core.exceptions import TradingBotException
from ..base_executor import BaseExecutor, PlatformType, OrderType, OrderSide, OrderStatus

logger = get_logger(__name__)


class BinanceExecutor(BaseExecutor):
    """Binance exchange executor with spot and futures trading support."""
    
    def __init__(self, config):
        super().__init__(config, PlatformType.BINANCE)
        self.api_key = config.binance_api_key
        self.secret_key = config.binance_secret_key
        self.testnet = config.binance_testnet
        self.is_demo = self.testnet
        
        # API endpoints
        if self.testnet:
            self.base_url = "https://testnet.binance.vision"
            self.futures_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://api.binance.com"
            self.futures_url = "https://fapi.binance.com"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.listen_key = None
        
    @property
    def platform_name(self) -> str:
        return f"Binance {'Testnet' if self.testnet else 'Live'}"
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """Sign request for Binance API."""
        query_string = urlencode(params)
        return hmac.new(
            self.secret_key.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, signed: bool = False) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "X-MBX-APIKEY": self.api_key
        }
        return headers
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          params: Optional[Dict] = None, 
                          signed: bool = False,
                          futures: bool = False) -> Dict[str, Any]:
        """Make API request to Binance."""
        if not self.session:
            raise TradingBotException("Session not initialized")
        
        params = params or {}
        base_url = self.futures_url if futures else self.base_url
        url = f"{base_url}{endpoint}"
        
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._sign_request(params)
        
        headers = self._get_headers(signed)
        
        try:
            async with self.session.request(
                method, url, params=params, headers=headers, timeout=30
            ) as response:
                data = await response.json()
                
                if response.status != 200:
                    error_msg = data.get('msg', f'HTTP {response.status}')
                    raise TradingBotException(f"Binance API error: {error_msg}")
                
                return data
                
        except aiohttp.ClientError as e:
            raise TradingBotException(f"Binance connection error: {e}")
    
    @with_error_handling("binance_connect", notify_telegram=True)
    async def connect(self) -> bool:
        """Connect to Binance exchange."""
        try:
            async with ErrorContext("binance_connection") as ctx:
                # Create HTTP session
                connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
                self.session = aiohttp.ClientSession(connector=connector)
                
                # Test connection
                await self._make_request("GET", "/api/v3/ping")
                
                # Get account info if credentials provided
                if self.api_key and self.secret_key:
                    account_info = await self._make_request("GET", "/api/v3/account", signed=True)
                    self.account_info = self._format_account_info(account_info)
                    
                    # Create listen key for user data stream
                    listen_key_data = await self._make_request("POST", "/api/v3/userDataStream", signed=True)
                    self.listen_key = listen_key_data.get('listenKey')
                
                self.connected = True
                logger.info(f"Connected to {self.platform_name}")
                return True
                
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "connect"})
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Binance exchange."""
        try:
            if self.listen_key:
                await self._make_request("DELETE", f"/api/v3/userDataStream", 
                                       params={"listenKey": self.listen_key}, signed=True)
            
            if self.session:
                await self.session.close()
                self.session = None
            
            self.connected = False
            logger.info(f"Disconnected from {self.platform_name}")
            return True
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "disconnect"})
            return False
    
    async def test_connection(self) -> bool:
        """Test Binance connection."""
        try:
            await self._make_request("GET", "/api/v3/ping")
            return True
        except:
            return False
    
    def _format_account_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format account info to standard format."""
        balances = {}
        for balance in data.get('balances', []):
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            if free > 0 or locked > 0:
                balances[asset] = {
                    "free": free,
                    "locked": locked,
                    "total": free + locked
                }
        
        return {
            "platform": self.platform_name,
            "account_type": data.get('accountType', 'SPOT'),
            "can_trade": data.get('canTrade', False),
            "can_withdraw": data.get('canWithdraw', False),
            "can_deposit": data.get('canDeposit', False),
            "balances": balances,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        try:
            if not self.api_key or not self.secret_key:
                return None
            
            data = await self._make_request("GET", "/api/v3/account", signed=True)
            return self._format_account_info(data)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_account_info"})
            return None
    
    async def get_balance(self, asset: str = "USDT") -> float:
        """Get balance for specific asset."""
        try:
            account_info = await self.get_account_info()
            if account_info and asset in account_info.get('balances', {}):
                return account_info['balances'][asset]['free']
            return 0.0
        except:
            return 0.0
    
    @with_error_handling("binance_place_order", notify_telegram=True)
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place order on Binance."""
        try:
            async with ErrorContext("binance_place_order", {"symbol": order.get("symbol")}) as ctx:
                # Validate required fields
                symbol = self.standardize_symbol(order["symbol"])
                side = order["side"].upper()
                order_type = order.get("type", "MARKET").upper()
                quantity = float(order["quantity"])
                
                # Build order parameters
                params = {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity
                }
                
                # Add price for limit orders
                if order_type in ["LIMIT", "STOP_LOSS_LIMIT", "TAKE_PROFIT_LIMIT"]:
                    params["price"] = float(order["price"])
                    params["timeInForce"] = "GTC"  # Good Till Cancelled
                
                # Add stop price for stop orders
                if order_type in ["STOP_LOSS", "STOP_LOSS_LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_LIMIT"]:
                    params["stopPrice"] = float(order["stopPrice"])
                
                # Place order
                result = await self._make_request("POST", "/api/v3/order", params=params, signed=True)
                
                # Log trade event
                log_trade_event("binance", "order_placed", {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "order_id": result.get("orderId")
                })
                
                return self.format_order_data(result)
                
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "place_order", "order": order})
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order on Binance."""
        try:
            params = {
                "symbol": self.standardize_symbol(symbol),
                "orderId": int(order_id)
            }
            
            result = await self._make_request("DELETE", "/api/v3/order", params=params, signed=True)
            
            log_trade_event("binance", "order_cancelled", {
                "symbol": symbol,
                "order_id": order_id
            })
            
            return self.format_order_data(result)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "cancel_order"})
            return {"success": False, "error": str(e)}
    
    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify order (Binance doesn't support modification, cancel and recreate)."""
        # Binance doesn't support order modification
        # Would need to cancel and place new order
        return {"success": False, "error": "Order modification not supported by Binance"}
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        try:
            params = {
                "symbol": self.standardize_symbol(symbol),
                "orderId": int(order_id)
            }
            
            result = await self._make_request("GET", "/api/v3/order", params=params, signed=True)
            return self.format_order_data(result)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_order"})
            return None
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        try:
            params = {}
            if symbol:
                params["symbol"] = self.standardize_symbol(symbol)
            
            orders = await self._make_request("GET", "/api/v3/openOrders", params=params, signed=True)
            return [self.format_order_data(order) for order in orders]
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_orders"})
            return []
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions (for futures trading)."""
        try:
            # Spot trading doesn't have positions, return balances instead
            account_info = await self.get_account_info()
            if not account_info:
                return []
            
            positions = []
            for asset, balance_info in account_info.get('balances', {}).items():
                if balance_info['total'] > 0:
                    positions.append({
                        "position_id": f"{asset}_balance",
                        "symbol": asset,
                        "side": "LONG",  # Spot positions are always long
                        "size": balance_info['total'],
                        "entry_price": 0,  # Not available for spot
                        "current_price": 0,  # Would need to get from ticker
                        "unrealized_pnl": 0,
                        "realized_pnl": 0,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "platform": self.platform_type.value
                    })
            
            return positions
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_positions"})
            return []
    
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close position (sell all of an asset for spot trading)."""
        # For spot trading, this would mean selling the entire balance
        return {"success": False, "error": "Position closing not applicable for spot trading"}
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        try:
            # Get exchange info for symbol filters
            exchange_info = await self._make_request("GET", "/api/v3/exchangeInfo")
            
            symbol_std = self.standardize_symbol(symbol)
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == symbol_std:
                    return {
                        "symbol": symbol_info['symbol'],
                        "base_asset": symbol_info['baseAsset'],
                        "quote_asset": symbol_info['quoteAsset'],
                        "status": symbol_info['status'],
                        "min_qty": self._get_filter_value(symbol_info['filters'], 'LOT_SIZE', 'minQty'),
                        "max_qty": self._get_filter_value(symbol_info['filters'], 'LOT_SIZE', 'maxQty'),
                        "step_size": self._get_filter_value(symbol_info['filters'], 'LOT_SIZE', 'stepSize'),
                        "min_price": self._get_filter_value(symbol_info['filters'], 'PRICE_FILTER', 'minPrice'),
                        "max_price": self._get_filter_value(symbol_info['filters'], 'PRICE_FILTER', 'maxPrice'),
                        "tick_size": self._get_filter_value(symbol_info['filters'], 'PRICE_FILTER', 'tickSize'),
                        "platform": self.platform_type.value
                    }
            
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_symbol_info"})
            return None
    
    def _get_filter_value(self, filters: List[Dict], filter_type: str, field: str) -> float:
        """Extract filter value from symbol filters."""
        for f in filters:
            if f['filterType'] == filter_type:
                return float(f.get(field, 0))
        return 0.0
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        try:
            params = {"symbol": self.standardize_symbol(symbol)}
            ticker = await self._make_request("GET", "/api/v3/ticker/24hr", params=params)
            
            return {
                "symbol": ticker['symbol'],
                "price": float(ticker['lastPrice']),
                "bid": float(ticker['bidPrice']),
                "ask": float(ticker['askPrice']),
                "volume": float(ticker['volume']),
                "change_24h": float(ticker['priceChange']),
                "change_percent_24h": float(ticker['priceChangePercent']),
                "high_24h": float(ticker['highPrice']),
                "low_24h": float(ticker['lowPrice']),
                "timestamp": int(ticker['closeTime']),
                "platform": self.platform_type.value
            }
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_ticker"})
            return None
    
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical kline data."""
        try:
            params = {
                "symbol": self.standardize_symbol(symbol),
                "interval": timeframe,
                "limit": min(limit, 1000)  # Binance max is 1000
            }
            
            klines = await self._make_request("GET", "/api/v3/klines", params=params)
            
            result = []
            for kline in klines:
                result.append({
                    "timestamp": int(kline[0]),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "close_time": int(kline[6]),
                    "quote_volume": float(kline[7]),
                    "trades": int(kline[8])
                })
            
            return result
            
        except Exception as e:
            log_error_with_context(e, {"platform": "binance", "operation": "get_klines"})
            return []
    
    def standardize_symbol(self, symbol: str) -> str:
        """Standardize symbol for Binance (remove separators)."""
        return symbol.upper().replace("/", "").replace("-", "").replace("_", "")
