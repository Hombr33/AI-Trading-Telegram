"""
Unified cryptocurrency exchange executor using CCXT library.
Supports multiple exchanges with a consistent API.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timezone
from decimal import Decimal

try:
    import ccxt.pro as ccxt

    CCXT_AVAILABLE = True
except ImportError:
    try:
        import ccxt

        CCXT_AVAILABLE = True
    except ImportError:
        CCXT_AVAILABLE = False
        ccxt = None

from ....core.logging import get_logger, log_trade_event, log_error_with_context
from ....core.error_handler import with_error_handling, ErrorContext
from ....core.exceptions import TradingBotException
from ...base_executor import BaseExecutor
from ...interfaces import PlatformType, OrderType, OrderSide, OrderStatus

logger = get_logger(__name__)


class CCXTExecutor(BaseExecutor):
    """Unified crypto exchange executor using CCXT library."""

    def __init__(self, config, exchange_name: str):
        """Initialize CCXT executor for specific exchange.

        Args:
            config: Configuration object with exchange credentials
            exchange_name: Exchange name (binance, bybit, bitget, etc.)
        """
        # Map exchange names to platform types
        platform_map = {
            "binance": PlatformType.BINANCE,
            "bybit": PlatformType.BYBIT,
            "bitget": PlatformType.BITGET,
        }

        super().__init__(config, platform_map.get(exchange_name, PlatformType.BINANCE))

        if not CCXT_AVAILABLE:
            raise ImportError(
                "CCXT library not available. Install with: pip install ccxt"
            )

        self.exchange_name = exchange_name.lower()
        self.exchange: Optional[ccxt.Exchange] = None

        # Get exchange-specific configuration
        self._setup_exchange_config(config)

    def _setup_exchange_config(self, config):
        """Setup exchange-specific configuration."""
        if self.exchange_name == "binance":
            self.api_key = getattr(config, "binance_api_key", None)
            self.secret_key = getattr(config, "binance_secret_key", None)
            self.testnet = getattr(config, "binance_testnet", False)
        elif self.exchange_name == "bybit":
            self.api_key = getattr(config, "bybit_api_key", None)
            self.secret_key = getattr(config, "bybit_secret_key", None)
            self.testnet = getattr(config, "bybit_testnet", False)
        elif self.exchange_name == "bitget":
            self.api_key = getattr(config, "bitget_api_key", None)
            self.secret_key = getattr(config, "bitget_secret_key", None)
            self.passphrase = getattr(config, "bitget_passphrase", None)
            self.testnet = getattr(config, "bitget_testnet", False)
        else:
            raise ValueError(f"Unsupported exchange: {self.exchange_name}")

        self.is_demo = self.testnet

    @property
    def platform_name(self) -> str:
        return f"{self.exchange_name.title()} {'Testnet' if self.testnet else 'Live'}"

    def _map_order_type(self, order_type: OrderType) -> str:
        """Map internal order type to CCXT order type."""
        mapping = {
            OrderType.MARKET: "market",
            OrderType.LIMIT: "limit",
            OrderType.STOP: "stop",
            OrderType.STOP_LIMIT: "stop_limit",
        }
        return mapping.get(order_type, "market")

    def _map_order_side(self, side: OrderSide) -> str:
        """Map internal order side to CCXT side."""
        return "buy" if side == OrderSide.BUY else "sell"

    def _map_order_status(self, status: str) -> OrderStatus:
        """Map CCXT order status to internal status."""
        mapping = {
            "open": OrderStatus.PENDING,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
            "expired": OrderStatus.EXPIRED,
        }
        return mapping.get(status.lower(), OrderStatus.UNKNOWN)

    async def _connect_impl(self) -> bool:
        """Platform-specific connection implementation for BaseExecutor."""
        try:
            # Get exchange class
            exchange_class = getattr(ccxt, self.exchange_name)

            # Setup exchange configuration
            config = {
                "apiKey": self.api_key,
                "secret": self.secret_key,
                "enableRateLimit": True,
                "timeout": 30000,
            }

            # Add exchange-specific config
            if self.exchange_name == "bitget" and hasattr(self, "passphrase"):
                config["password"] = self.passphrase

            if self.testnet:
                config["sandbox"] = True

            # Create exchange instance
            self.exchange = exchange_class(config)

            # Test connection
            await self.exchange.load_markets()

            # Test API credentials if provided
            if self.api_key and self.secret_key:
                await self.exchange.fetch_balance()

            logger.info(f"Connected to {self.platform_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from exchange."""
        try:
            if self.exchange:
                await self.exchange.close()
                self.exchange = None

            self.connected = False
            logger.info(f"Disconnected from {self.platform_name}")
            return True

        except Exception as e:
            logger.error(f"Error disconnecting from {self.exchange_name}: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test exchange connection."""
        try:
            if not self.exchange:
                return False
            await self.exchange.fetch_status()
            return True
        except Exception:
            return False

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account information."""
        try:
            if not self.exchange:
                return None

            balance = await self.exchange.fetch_balance()

            # Format balances
            balances = {}
            for asset, balance_info in balance.get("total", {}).items():
                if balance_info and balance_info > 0:
                    balances[asset] = {
                        "free": balance.get("free", {}).get(asset, 0),
                        "used": balance.get("used", {}).get(asset, 0),
                        "total": balance_info,
                    }

            return {
                "platform": self.platform_name,
                "balances": balances,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting account info from {self.exchange_name}: {e}")
            return None

    async def get_balance(self, asset: str = "USDT") -> float:
        """Get balance for specific asset."""
        try:
            if not self.exchange:
                return 0.0

            balance = await self.exchange.fetch_balance()
            return float(balance.get("free", {}).get(asset, 0))

        except Exception:
            return 0.0

    async def _place_order_impl(self, request) -> "OrderResponse":
        """Platform-specific order placement for BaseExecutor."""
        try:
            if not self.exchange:
                raise TradingBotException(f"Not connected to {self.exchange_name}")

            # Extract order parameters
            symbol = request.symbol
            side = request.side.lower()
            order_type = request.type.lower()
            amount = float(request.amount)
            price = float(request.price) if request.price else None

            # Place order using CCXT
            if order_type == "market":
                result = await self.exchange.create_market_order(symbol, side, amount)
            elif order_type == "limit":
                if price is None:
                    raise ValueError("Price required for limit orders")
                result = await self.exchange.create_limit_order(
                    symbol, side, amount, price
                )
            else:
                result = await self.exchange.create_order(
                    symbol, order_type, side, amount, price
                )

            # Log trade event
            log_trade_event(
                self.exchange_name,
                "order_placed",
                {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "amount": amount,
                    "order_id": result.get("id"),
                },
            )

            # Return OrderResponse object
            from ...interfaces import OrderResponse

            return OrderResponse(
                order_id=result.get("id", ""),
                client_order_id=result.get("clientOrderId"),
                symbol=result.get("symbol", symbol),
                side=result.get("side", side),
                type=result.get("type", order_type),
                amount=float(result.get("amount", amount)),
                price=float(result.get("price", price or 0)),
                filled=float(result.get("filled", 0)),
                remaining=float(result.get("remaining", amount)),
                status=self._map_order_status(result.get("status", "unknown")).value,
                timestamp=(
                    datetime.fromtimestamp(
                        result.get("timestamp", 0) / 1000, timezone.utc
                    )
                    if result.get("timestamp")
                    else datetime.now(timezone.utc)
                ),
                platform=self.platform_type.value,
            )

        except Exception as e:
            logger.error(f"Error placing order on {self.exchange_name}: {e}")
            raise TradingBotException(f"Order placement failed: {e}")

    @with_error_handling("ccxt_place_order", notify_telegram=True)
    async def _place_order_ccxt(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Place order using CCXT."""
        try:
            if not self.exchange:
                return {
                    "success": False,
                    "error": f"Not connected to {self.exchange_name}",
                }

            # Extract order parameters
            symbol = order["symbol"]
            side = order["side"].lower()
            order_type = order.get("type", "market").lower()
            amount = float(order["amount"])

            # Optional parameters
            price = float(order["price"]) if "price" in order else None
            params = order.get("params", {})

            # Place order using CCXT
            if order_type == "market":
                result = await self.exchange.create_market_order(
                    symbol, side, amount, None, None, params
                )
            elif order_type == "limit":
                if price is None:
                    return {
                        "success": False,
                        "error": "Price required for limit orders",
                    }
                result = await self.exchange.create_limit_order(
                    symbol, side, amount, price, None, params
                )
            else:
                result = await self.exchange.create_order(
                    symbol, order_type, side, amount, price, None, params
                )

            # Log trade event
            log_trade_event(
                self.exchange_name,
                "order_placed",
                {
                    "symbol": symbol,
                    "side": side,
                    "type": order_type,
                    "amount": amount,
                    "order_id": result.get("id"),
                },
            )

            return self.format_order_data(result)

        except Exception as e:
            logger.error(f"Error placing order on {self.exchange_name}: {e}")
            return {"success": False, "error": str(e)}

    async def cancel_order(self, order_id: str, symbol: str = None) -> Dict[str, Any]:
        """Cancel order."""
        try:
            if not self.exchange:
                return {
                    "success": False,
                    "error": f"Not connected to {self.exchange_name}",
                }

            result = await self.exchange.cancel_order(order_id, symbol)

            log_trade_event(
                self.exchange_name,
                "order_cancelled",
                {"symbol": symbol, "order_id": order_id},
            )

            return self.format_order_data(result)

        except Exception as e:
            logger.error(f"Error cancelling order on {self.exchange_name}: {e}")
            return {"success": False, "error": str(e)}

    async def get_order(self, order_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Get order details."""
        try:
            if not self.exchange:
                return None

            result = await self.exchange.fetch_order(order_id, symbol)
            return self.format_order_data(result)

        except Exception as e:
            logger.error(f"Error getting order from {self.exchange_name}: {e}")
            return None

    async def get_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get open orders."""
        try:
            if not self.exchange:
                return []

            if symbol:
                orders = await self.exchange.fetch_open_orders(symbol)
            else:
                orders = await self.exchange.fetch_open_orders()

            return [self.format_order_data(order) for order in orders]

        except Exception as e:
            logger.error(f"Error getting orders from {self.exchange_name}: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get current ticker data."""
        try:
            if not self.exchange:
                return None

            ticker = await self.exchange.fetch_ticker(symbol)

            return {
                "symbol": ticker["symbol"],
                "price": ticker["last"],
                "bid": ticker["bid"],
                "ask": ticker["ask"],
                "volume": ticker["baseVolume"],
                "change_24h": ticker["change"],
                "change_percent_24h": ticker["percentage"],
                "high_24h": ticker["high"],
                "low_24h": ticker["low"],
                "timestamp": ticker["timestamp"],
                "platform": self.platform_type.value,
            }

        except Exception as e:
            logger.error(f"Error getting ticker from {self.exchange_name}: {e}")
            return None

    async def get_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV data."""
        try:
            if not self.exchange:
                return []

            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            result = []
            for candle in ohlcv:
                result.append(
                    {
                        "timestamp": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                    }
                )

            return result

        except Exception as e:
            logger.error(f"Error getting klines from {self.exchange_name}: {e}")
            return []

    def format_order_data(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format order data to standard format."""
        return {
            "success": True,
            "order_id": order_data.get("id"),
            "symbol": order_data.get("symbol"),
            "side": order_data.get("side"),
            "type": order_data.get("type"),
            "amount": order_data.get("amount"),
            "price": order_data.get("price"),
            "filled": order_data.get("filled", 0),
            "remaining": order_data.get("remaining", 0),
            "status": self._map_order_status(order_data.get("status", "unknown")),
            "timestamp": order_data.get("timestamp"),
            "platform": self.platform_type.value,
        }

    def standardize_symbol(self, symbol: str) -> str:
        """Standardize symbol format for the exchange."""
        # CCXT handles symbol standardization automatically
        return symbol.upper()


# Factory function to create exchange-specific executors
def create_crypto_executor(config, exchange_name: str) -> CCXTExecutor:
    """Create a crypto executor for the specified exchange.

    Args:
        config: Configuration object
        exchange_name: Exchange name (binance, bybit, bitget)

    Returns:
        CCXTExecutor instance for the specified exchange
    """
    return CCXTExecutor(config, exchange_name)


# Convenience functions for specific exchanges
def create_binance_executor(config) -> CCXTExecutor:
    """Create Binance executor."""
    return CCXTExecutor(config, "binance")


def create_bybit_executor(config) -> CCXTExecutor:
    """Create Bybit executor."""
    return CCXTExecutor(config, "bybit")


def create_bitget_executor(config) -> CCXTExecutor:
    """Create Bitget executor."""
    return CCXTExecutor(config, "bitget")
