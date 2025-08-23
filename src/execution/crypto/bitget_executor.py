"""
Bitget exchange executor for cryptocurrency trading.
"""

from __future__ import annotations

import asyncio
import time
import hmac
import hashlib
import base64
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

import aiohttp

from ...core.logging import get_logger, log_trade_event, log_error_with_context
from ...core.error_handler import with_error_handling, ErrorContext
from ...core.exceptions import TradingBotException
from ..base_executor import BaseExecutor, PlatformType, OrderType, OrderSide, OrderStatus

logger = get_logger(__name__)


class BitgetExecutor(BaseExecutor):
    """Bitget exchange executor with spot and futures trading support."""
    
    def __init__(self, config):
        super().__init__(config, PlatformType.BITGET)
        self.api_key = config.bitget_api_key
        self.secret_key = config.bitget_secret_key
        self.passphrase = config.bitget_passphrase
        self.testnet = config.bitget_testnet
        self.is_demo = self.testnet
        
        # API endpoints
        if self.testnet:
            self.base_url = "https://api.bitget.com"  # Bitget uses same URL for both
        else:
            self.base_url = "https://api.bitget.com"
        
        self.session: Optional[aiohttp.ClientSession] = None
        
    @property
    def platform_name(self) -> str:
        return f"Bitget {'Testnet' if self.testnet else 'Live'}"
    
    def _sign_request(self, method: str, endpoint: str, body: str, timestamp: str) -> str:
        """Sign request for Bitget API."""
        message = timestamp + method.upper() + endpoint + body
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        return signature
    
    def _get_headers(self, method: str, endpoint: str, body: str = "") -> Dict[str, str]:
        """Get request headers with signature."""
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            "Content-Type": "application/json",
            "ACCESS-KEY": self.api_key,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase
        }
        
        if self.api_key and self.secret_key:
            signature = self._sign_request(method, endpoint, body, timestamp)
            headers["ACCESS-SIGN"] = signature
        
        return headers
    
    async def _make_request(self, 
                          method: str, 
                          endpoint: str, 
                          params: Optional[Dict] = None,
                          data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Bitget."""
        if not self.session:
            raise TradingBotException("Session not initialized")
        
        url = f"{self.base_url}{endpoint}"
        body = ""
        
        if method == "GET" and params:
            url += "?" + "&".join([f"{k}={v}" for k, v in params.items()])
        elif method in ["POST", "PUT", "DELETE"] and data:
            body = json.dumps(data)
        
        headers = self._get_headers(method, endpoint, body)
        
        try:
            if method == "GET":
                async with self.session.get(url, headers=headers, timeout=30) as response:
                    result = await response.json()
            else:
                async with self.session.request(method, url, data=body, headers=headers, timeout=30) as response:
                    result = await response.json()
            
            if result.get('code') != '00000':
                error_msg = result.get('msg', f'Error code: {result.get("code")}')
                raise TradingBotException(f"Bitget API error: {error_msg}")
            
            return result.get('data', result)
                
        except aiohttp.ClientError as e:
            raise TradingBotException(f"Bitget connection error: {e}")
    
    @with_error_handling("bitget_connect", notify_telegram=True)
    async def connect(self) -> bool:
        """Connect to Bitget exchange."""
        try:
            async with ErrorContext("bitget_connection") as ctx:
                # Create HTTP session
                connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
                self.session = aiohttp.ClientSession(connector=connector)
                
                # Test connection
                await self._make_request("GET", "/api/spot/v1/public/time")
                
                # Get account info if credentials provided
                if self.api_key and self.secret_key:
                    account_info = await self._make_request("GET", "/api/spot/v1/account/assets")
                    self.account_info = self._format_account_info(account_info)
                
                self.connected = True
                logger.info(f"Connected to {self.platform_name}")
                return True
                
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "connect"})
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Bitget exchange."""
        try:
            if self.session:
                await self.session.close()
                self.session = None
            
            self.connected = False
            logger.info(f"Disconnected from {self.platform_name}")
            return True
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "disconnect"})
            return False
    
    async def test_connection(self) -> bool:
        """Test Bitget connection."""
        try:
            await self._make_request("GET", "/api/spot/v1/public/time")
            return True
        except:
            return False
    
    def _format_account_info(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Format account info to standard format."""
        balances = {}
        
        for asset_info in data:
            asset = asset_info['coinName']
            available = float(asset_info['available'])
            locked = float(asset_info['lock'])
            total = available + locked
            
            if total > 0:
                balances[asset] = {
                    "free": available,
                    "locked": locked,
                    "total": total
                }
        
        return {
            "platform": self.platform_name,
            "account_type": "SPOT",
            "balances": balances,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        try:
            if not self.api_key or not self.secret_key:
                return None
            
            data = await self._make_request("GET", "/api/spot/v1/account/assets")
            return self._format_account_info(data)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_account_info"})
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
    
    @with_error_handling("bitget_place_order", notify_telegram=True)
    async def place_order(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place order on Bitget."""
        try:
            async with ErrorContext("bitget_place_order", {"symbol": order.get("symbol")}) as ctx:
                # Validate required fields
                symbol = order["symbol"]
                side = order["side"].lower()  # buy/sell
                order_type = order.get("type", "market").lower()
                quantity = str(float(order["quantity"]))
                
                # Build order parameters
                params = {
                    "symbol": symbol,
                    "side": side,
                    "orderType": order_type,
                    "quantity": quantity
                }
                
                # Add price for limit orders
                if order_type == "limit":
                    params["price"] = str(float(order["price"]))
                
                # Add client order ID
                params["clientOid"] = f"ai_bot_{int(time.time() * 1000)}"
                
                # Place order
                result = await self._make_request("POST", "/api/spot/v1/trade/orders", data=params)
                
                # Log trade event
                log_trade_event("bitget", "order_placed", {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "order_id": result.get("orderId")
                })
                
                return {
                    "success": True,
                    "order_id": result.get("orderId"),
                    "client_oid": result.get("clientOid"),
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "quantity": quantity,
                    "platform": self.platform_type.value
                }
                
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "place_order", "order": order})
            return {"success": False, "error": str(e)}
    
    async def cancel_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """Cancel order on Bitget."""
        try:
            params = {
                "symbol": symbol,
                "orderId": order_id
            }
            
            result = await self._make_request("POST", "/api/spot/v1/trade/cancel-order", data=params)
            
            log_trade_event("bitget", "order_cancelled", {
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
            log_error_with_context(e, {"platform": "bitget", "operation": "cancel_order"})
            return {"success": False, "error": str(e)}
    
    async def modify_order(self, order_id: str, **kwargs) -> Dict[str, Any]:
        """Modify order (Bitget requires cancel and recreate)."""
        # Bitget doesn't support direct order modification
        return {"success": False, "error": "Order modification not supported by Bitget"}
    
    async def get_order(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        try:
            params = {
                "orderId": order_id
            }
            
            result = await self._make_request("GET", "/api/spot/v1/trade/orderInfo", params)
            return self.format_order_data(result)
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_order"})
            return None
    
    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all open orders."""
        try:
            params = {}
            if symbol:
                params["symbol"] = symbol
            
            result = await self._make_request("GET", "/api/spot/v1/trade/open-orders", params)
            
            orders = []
            for order in result:
                orders.append(self.format_order_data(order))
            
            return orders
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_orders"})
            return []
    
    async def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions (spot balances for Bitget spot trading)."""
        try:
            # For spot trading, return non-zero balances as positions
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
            log_error_with_context(e, {"platform": "bitget", "operation": "get_positions"})
            return []
    
    async def close_position(self, position_id: str, volume: Optional[float] = None) -> Dict[str, Any]:
        """Close position (sell all of an asset for spot trading)."""
        # For spot trading, this would mean selling the entire balance
        return {"success": False, "error": "Position closing not applicable for spot trading"}
    
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information."""
        try:
            params = {"symbol": symbol}
            result = await self._make_request("GET", "/api/spot/v1/public/product", params)
            
            if result:
                return {
                    "symbol": result["symbol"],
                    "base_coin": result["baseCoin"],
                    "quote_coin": result["quoteCoin"],
                    "status": result["status"],
                    "min_trade_amount": float(result["minTradeAmount"]),
                    "max_trade_amount": float(result["maxTradeAmount"]),
                    "price_scale": int(result["priceScale"]),
                    "quantity_scale": int(result["quantityScale"]),
                    "platform": self.platform_type.value
                }
            
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_symbol_info"})
            return None
    
    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        try:
            params = {"symbol": symbol}
            result = await self._make_request("GET", "/api/spot/v1/market/ticker", params)
            
            if result:
                return {
                    "symbol": result["symbol"],
                    "price": float(result["close"]),
                    "bid": float(result["bidPr"]),
                    "ask": float(result["askPr"]),
                    "volume": float(result["baseVol"]),
                    "change_24h": float(result["change"]),
                    "change_percent_24h": float(result["changeUtc"]),
                    "high_24h": float(result["high24h"]),
                    "low_24h": float(result["low24h"]),
                    "timestamp": int(result["ts"]),
                    "platform": self.platform_type.value
                }
            
            return None
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_ticker"})
            return None
    
    async def get_klines(self, symbol: str, timeframe: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical kline data."""
        try:
            params = {
                "symbol": symbol,
                "period": timeframe,
                "limit": min(limit, 1000)  # Bitget max is 1000
            }
            
            result = await self._make_request("GET", "/api/spot/v1/market/candles", params)
            
            klines_data = []
            for kline in result:
                klines_data.append({
                    "timestamp": int(kline[0]),
                    "open": float(kline[1]),
                    "high": float(kline[2]),
                    "low": float(kline[3]),
                    "close": float(kline[4]),
                    "volume": float(kline[5]),
                    "quote_volume": float(kline[6])
                })
            
            return klines_data
            
        except Exception as e:
            log_error_with_context(e, {"platform": "bitget", "operation": "get_klines"})
            return []
    
    def standardize_symbol(self, symbol: str) -> str:
        """Standardize symbol for Bitget (keep format like BTCUSDT)."""
        return symbol.upper().replace("/", "").replace("-", "")
