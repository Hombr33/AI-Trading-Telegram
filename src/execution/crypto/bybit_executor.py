"""
Bybit exchange executor for cryptocurrency trading.
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


class BybitExecutor(BaseExecutor):
    """Bybit exchange executor with spot and derivatives trading support."""
    
    def __init__(self, config):
        super().__init__(config, PlatformType.BYBIT)
        self.api_key = config.bybit_api_key
        self.secret_key = config.bybit_secret_key
        self.testnet = config.bybit_testnet
        self.is_demo = self.testnet
        
        # API endpoints
        if self.testnet:
            self.base_url = "https://api-testnet.bybit.com"
        else:
            self.base_url = "https://api.bybit.com"
        
        self.session: Optional[aiohttp.ClientSession] = None
        
    @property
    def platform_name(self) -> str:
        return f"Bybit {'Testnet' if self.testnet else 'Live'}"
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """Sign request for Bybit API."""
        # Bybit V5 API signature
        param_str = urlencode(sorted(params.items()))
        return hmac.new(
            self.secret_key.encode(),
            param_str.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, params: Dict[str, Any] = None) -> Dict[str, str]:
        """Get request headers with signature."""
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        headers = {
            "Content-Type": "application/json",
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window
        }
        
        if params and self.api_key and self.secret_key:
            param_str = urlencode(sorted(params.items()))
            sign_str = timestamp + self.api_key + recv_window + param_str
            signature = hmac.new(
                self.secret_key.encode(),
                sign_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-BAPI-SIGN"] = signature
        
        return headers
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Bybit."""
        if not self.session:
            raise TradingBotException("Session not initialized")
        
        params = params or {}
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(params if method == "POST" else None)
        
        try:
            if method == "GET":
                async with self.session.get(url, params=params, headers=headers, timeout=30) as response:
                    data = await response.json()
            else:
                async with self.session.request(method, url, json=params, headers=headers, timeout=30) as response:
                    data = await response.json()
            
            if data.get('retCode') != 0:
                error_msg = data.get('retMsg', f'Error code: {data.get("retCode")}')
                raise TradingBotException(f"Bybit API error: {error_msg}")
            
            return data.get('result', data)
                
        except aiohttp.ClientError as e:
            raise TradingBotException(f"Bybit connection error: {e}")
    
    @with_error_handling("bybit_connect", notify_telegram=True)
    async def connect(self) -> bool:
        """Connect to Bybit exchange."""
        try:
            async with ErrorContext("bybit_connection") as ctx:
                # Create HTTP session
                connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
                self.session = aiohttp.ClientSession(connector=connector)
                
                # Test connection
                await self._make_request("GET", "/v5/market/time")
                
                # Get account info if credentials provided
                if self.api_key and self.secret_key:
                    account_info = await self._make_request("GET", "/v5/account/wallet-balance", 
                                                          {"accountType": "UNIFIED"})
                    self.account_info = self._format_account_info(account_info)
                
                self.connected = True
                logger.info(f"Connected to {self.platform_name}")
                return True
                
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "connect"})
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Bybit exchange."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.connected = False
            logger.info(f"Disconnected from {self.platform_name}")
            return True
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "disconnect"})
            return False
    
    async def test_connection(self) -> bool:
        """Test Bybit connection."""
        try:
            await self._make_request("GET", "/v5/market/time")
            return True
        except:
            return False
    
    def _format_account_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Format account info to standard format."""
        balances = {}
        
        for account in data.get('list', []):
            for coin in account.get('coin', []):
                asset = coin['coin']
                available = float(coin['availableToWithdraw'])
                locked = float(coin['locked'])
                total = float(coin['walletBalance'])
                
                if total > 0:
                    balances[asset] = {
                        "free": available,
                        "locked": locked,
                        "total": total
                    }
        
        return {
            "platform": self.platform_name,
            "account_type": "UNIFIED",
            "balances": balances,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        try:
            if not self.api_key or not self.secret_key:
                return None
            
            data = await self._make_request("GET", "/v5/account/wallet-balance", 
                                          {"accountType": "UNIFIED"})
            return self._format_account_info(data)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_account_info"})
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
    
    @with_error_handling("bybit_place_order", notify_telegram=True)
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place order on Bybit."""
        try:
            async with ErrorContext("bybit_place_order", {"symbol": order.get("symbol")}) as ctx:
                # Validate required fields
                symbol = order["symbol"]
                side = order["side"].capitalize()  # Buy/Sell
                order_type = order.get("type", "Market").capitalize()
                qty = str(float(order["qty"]))
                
                # Build order parameters
                params = {
                    "category": "spot",  # or "linear" for derivatives
                    "symbol": symbol,
                    "side": side,
                    "orderType": order_type,
                    "qty": qty
                }
                
                # Add price for limit orders
                if order_type == "Limit":
                    params["price"] = str(float(order["price"]))
                
                # Add stop price for conditional orders
                if "stopPrice" in order:
                    params["triggerPrice"] = str(float(order["stopPrice"]))
                
                # Add time in force
                if order_type == "Limit":
                    params["timeInForce"] = "GTC"  # Good Till Cancelled
                
                # Place order
                result = await self._make_request("POST", "/v5/order/create", params)
                
                # Log trade event
                log_trade_event("bybit", "order_placed", {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "qty": qty,
                    "order_id": result.get("orderId")
                })
                
                return {
                    "success": True,
                    "order_id": result.get("orderId"),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "qty": qty,
                    "platform": self.platform_type.value
                }
                
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "place_order", "order": order})
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order on Bybit."""
        try:
            params = {
                "category": "spot",
                "symbol": symbol,
                "orderId": order_id
            }
            
            result = await self._make_request("POST", "/v5/order/cancel", params)
            
            log_trade_event("bybit", "order_cancelled", {
                "symbol": symbol,
                "order_id": order_id
            })
            
            return {
                "success": True,
                "order_id": order_id,
                "symbol": symbol,
                "platform": self.platform_type.value
            }
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "cancel_order"})
            return {"success": False, "error": str(e)}
    
    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify order on Bybit."""
        try:
            params = {
                "category": "spot",
                "orderId": order_id
            }
            
            # Add modifiable fields
            if "qty" in kwargs:
                params["qty"] = str(float(kwargs["qty"]))
            if "price" in kwargs:
                params["price"] = str(float(kwargs["price"]))
            
            result = await self._make_request("POST", "/v5/order/amend", params)
            
            return {
                "success": True,
                "order_id": order_id,
                "platform": self.platform_type.value
            }
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "modify_order"})
            return {"success": False, "error": str(e)}
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        try:
            params = {
                "category": "spot",
                "orderId": order_id
            }
            
            result = await self._make_request("GET", "/v5/order/realtime", params)
            
            if result.get("list"):
                return self.format_order_data(result["list"][0])
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_order"})
            return None
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        try:
            params = {"category": "spot"}
            if symbol:
                params["symbol"] = symbol
            
            result = await self._make_request("GET", "/v5/order/realtime", params)
            
            orders = []
            for order in result.get("list", []):
                orders.append(self.format_order_data(order))
            
            return orders
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_orders"})
            return []
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions."""
        try:
            params = {"category": "linear"}  # For derivatives
            if symbol:
                params["symbol"] = symbol
            
            result = await self._make_request("GET", "/v5/position/list", params)
            
            positions = []
            for position in result.get("list", []):
                if float(position.get("size", 0)) > 0:
                    positions.append(self.format_position_data(position))
            
            return positions
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_positions"})
            return []
    
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close position on Bybit."""
        try:
            # Extract symbol from position_id (assuming format: symbol_side)
            symbol = position_id.split("_")[0] if "_" in position_id else position_id
            
            params = {
                "category": "linear",
                "symbol": symbol,
                "side": "Sell",  # Opposite side to close
                "orderType": "Market",
                "qty": "0",  # 0 means close entire position
                "reduceOnly": True
            }
            
            if volume:
                params["qty"] = str(volume)
            
            result = await self._make_request("POST", "/v5/order/create", params)
            
            return {
                "success": True,
                "order_id": result.get("orderId"),
                "symbol": symbol,
                "platform": self.platform_type.value
            }
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "close_position"})
            return {"success": False, "error": str(e)}
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        try:
            params = {
                "category": "spot",
                "symbol": symbol
            }
            
            result = await self._make_request("GET", "/v5/market/instruments-info", params)
            
            if result.get("list"):
                info = result["list"][0]
                return {
                    "symbol": info["symbol"],
                    "base_coin": info["baseCoin"],
                    "quote_coin": info["quoteCoin"],
                    "status": info["status"],
                    "min_order_qty": float(info["lotSizeFilter"]["minOrderQty"]),
                    "max_order_qty": float(info["lotSizeFilter"]["maxOrderQty"]),
                    "qty_step": float(info["lotSizeFilter"]["qtyStep"]),
                    "min_price": float(info["priceFilter"]["minPrice"]),
                    "max_price": float(info["priceFilter"]["maxPrice"]),
                    "tick_size": float(info["priceFilter"]["tickSize"]),
                    "platform": self.platform_type.value
                }
            
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_symbol_info"})
            return None
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        try:
            params = {
                "category": "spot",
                "symbol": symbol
            }
            
            result = await self._make_request("GET", "/v5/market/tickers", params)
            
            if result.get("list"):
                ticker = result["list"][0]
                return {
                    "symbol": ticker["symbol"],
                    "price": float(ticker["lastPrice"]),
                    "bid": float(ticker["bid1Price"]),
                    "ask": float(ticker["ask1Price"]),
                    "volume": float(ticker["volume24h"]),
                    "change_24h": float(ticker["price24hPcnt"]) * 100,  # Convert to percentage
                    "high_24h": float(ticker["highPrice24h"]),
                    "low_24h": float(ticker["lowPrice24h"]),
                    "timestamp": int(time.time() * 1000),
                    "platform": self.platform_type.value
                }
            
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_ticker"})
            return None
    
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical kline data."""
        try:
            params = {
                "category": "spot",
                "symbol": symbol,
                "interval": timeframe,
                "limit": min(limit, 1000)  # Bybit max is 1000
            }
            
            result = await self._make_request("GET", "/v5/market/kline", params)
            
            klines_data = []
            for kline in result.get("list", []):
                klines_data.append({
                    "timestamp": int(kline[0]),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "turnover": float(kline[6])
                })
            
            return klines_data
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bybit", "operation": "get_klines"})
            return []
    
    def standardize_symbol(self, symbol: str) -> str:
        """Standardize symbol for Bybit (keep format like BTCUSDT)."""
        return symbol.upper().replace("/", "").replace("-", "")
