"""
Crypto exchange bridge service for multi-platform trading.
"""

import logging
import asyncio
import hmac
import hashlib
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
from aiohttp import ClientSession, ClientTimeout
from sqlalchemy.orm import Session

from ..models.telegram_users import TelegramUser, PlatformConnection, PlatformType
from ..database.connection import get_db_session
from ..services.user_manager import UserManager
from ..services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class CryptoBridge:
    """Service for communicating with crypto exchanges."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.timeout = ClientTimeout(total=30)
        
        # Exchange endpoints
        self.endpoints = {
            "binance": {
                "base_url": "https://api.binance.com",
                "testnet_url": "https://testnet.binance.vision"
            },
            "bybit": {
                "base_url": "https://api.bybit.com",
                "testnet_url": "https://api-testnet.bybit.com"
            }
        }

    async def register_crypto_connection(self, telegram_id: int, exchange: str, 
                                       api_key: str, api_secret: str, 
                                       connection_name: str = None, testnet: bool = False) -> bool:
        """Register crypto exchange connection for user."""
        try:
            exchange = exchange.lower()
            if exchange not in self.endpoints:
                return False

            # Validate API credentials
            if not await self.validate_crypto_credentials(exchange, api_key, api_secret, testnet):
                return False

            # Register platform connection
            success = await self.user_manager.register_platform_connection(
                telegram_id=telegram_id,
                platform_type=PlatformType.CRYPTO,
                connection_name=connection_name or f"{exchange.title()} Exchange",
                api_key=api_key,
                api_secret=api_secret,
                server_endpoint=f"{exchange}{'_testnet' if testnet else ''}"
            )

            if success:
                logger.info(f"Crypto connection registered for user {telegram_id}: {exchange}")
                return True

        except Exception as e:
            logger.error(f"Failed to register crypto connection: {e}")

        return False

    async def validate_crypto_credentials(self, exchange: str, api_key: str, 
                                        api_secret: str, testnet: bool = False) -> bool:
        """Validate crypto exchange API credentials."""
        try:
            if exchange == "binance":
                return await self._validate_binance_credentials(api_key, api_secret, testnet)
            elif exchange == "bybit":
                return await self._validate_bybit_credentials(api_key, api_secret, testnet)
            
            return False
        except Exception as e:
            logger.error(f"Failed to validate {exchange} credentials: {e}")
            return False

    async def _validate_binance_credentials(self, api_key: str, api_secret: str, testnet: bool) -> bool:
        """Validate Binance API credentials."""
        base_url = self.endpoints["binance"]["testnet_url" if testnet else "base_url"]
        endpoint = "/api/v3/account"
        
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-MBX-APIKEY': api_key
        }
        
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def _validate_bybit_credentials(self, api_key: str, api_secret: str, testnet: bool) -> bool:
        """Validate Bybit API credentials."""
        base_url = self.endpoints["bybit"]["testnet_url" if testnet else "base_url"]
        endpoint = "/v5/account/wallet-balance"
        
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        param_str = f"timestamp={timestamp}&recv_window={recv_window}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window
        }
        
        url = f"{base_url}{endpoint}?{param_str}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200

    async def get_crypto_account_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get crypto account information."""
        try:
            with get_db_session() as session:
                user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.CRYPTO,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                # Parse exchange from server_endpoint
                exchange = connection.server_endpoint.split('_')[0] if connection.server_endpoint else "binance"
                testnet = "_testnet" in connection.server_endpoint if connection.server_endpoint else False

                if exchange == "binance":
                    return await self._get_binance_account_info(connection.api_key, connection.api_secret, testnet)
                elif exchange == "bybit":
                    return await self._get_bybit_account_info(connection.api_key, connection.api_secret, testnet)

                return None

        except Exception as e:
            logger.error(f"Failed to get crypto account info: {e}")
            return None

    async def _get_binance_account_info(self, api_key: str, api_secret: str, testnet: bool) -> Dict[str, Any]:
        """Get Binance account information."""
        base_url = self.endpoints["binance"]["testnet_url" if testnet else "base_url"]
        endpoint = "/api/v3/account"
        
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {'X-MBX-APIKEY': api_key}
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Calculate total balance in USDT
                    total_balance = 0
                    balances = []
                    
                    for balance in data.get('balances', []):
                        free = float(balance['free'])
                        locked = float(balance['locked'])
                        total = free + locked
                        
                        if total > 0:
                            balances.append({
                                'asset': balance['asset'],
                                'free': free,
                                'locked': locked,
                                'total': total
                            })
                            
                            # For simplicity, assume 1:1 for stablecoins
                            if balance['asset'] in ['USDT', 'USDC', 'BUSD']:
                                total_balance += total

                    return {
                        'exchange': 'binance',
                        'total_balance_usdt': total_balance,
                        'balances': balances,
                        'can_trade': data.get('canTrade', False),
                        'can_withdraw': data.get('canWithdraw', False),
                        'can_deposit': data.get('canDeposit', False)
                    }
                    
                return None

    async def _get_bybit_account_info(self, api_key: str, api_secret: str, testnet: bool) -> Dict[str, Any]:
        """Get Bybit account information."""
        base_url = self.endpoints["bybit"]["testnet_url" if testnet else "base_url"]
        endpoint = "/v5/account/wallet-balance"
        
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        param_str = f"timestamp={timestamp}&recv_window={recv_window}"
        
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window
        }
        
        url = f"{base_url}{endpoint}?{param_str}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    result = data.get('result', {})
                    
                    total_balance = 0
                    balances = []
                    
                    for account in result.get('list', []):
                        for coin in account.get('coin', []):
                            wallet_balance = float(coin.get('walletBalance', 0))
                            available_balance = float(coin.get('availableToWithdraw', 0))
                            
                            if wallet_balance > 0:
                                balances.append({
                                    'asset': coin.get('coin'),
                                    'wallet_balance': wallet_balance,
                                    'available_balance': available_balance,
                                    'total': wallet_balance
                                })
                                
                                # For simplicity, assume 1:1 for stablecoins
                                if coin.get('coin') in ['USDT', 'USDC']:
                                    total_balance += wallet_balance

                    return {
                        'exchange': 'bybit',
                        'total_balance_usdt': total_balance,
                        'balances': balances
                    }
                    
                return None

    async def place_crypto_order(self, telegram_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Place order on crypto exchange."""
        try:
            with get_db_session() as session:
                user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.CRYPTO,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                # Parse exchange from server_endpoint
                exchange = connection.server_endpoint.split('_')[0] if connection.server_endpoint else "binance"
                testnet = "_testnet" in connection.server_endpoint if connection.server_endpoint else False

                if exchange == "binance":
                    return await self._place_binance_order(
                        connection.api_key, connection.api_secret, order_data, testnet
                    )
                elif exchange == "bybit":
                    return await self._place_bybit_order(
                        connection.api_key, connection.api_secret, order_data, testnet
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to place crypto order: {e}")
            return None

    async def _place_binance_order(self, api_key: str, api_secret: str, 
                                 order_data: Dict[str, Any], testnet: bool) -> Dict[str, Any]:
        """Place order on Binance."""
        base_url = self.endpoints["binance"]["testnet_url" if testnet else "base_url"]
        endpoint = "/api/v3/order"
        
        timestamp = int(time.time() * 1000)
        
        params = {
            'symbol': order_data['symbol'],
            'side': order_data['side'],  # BUY or SELL
            'type': order_data.get('type', 'MARKET'),  # MARKET, LIMIT, etc.
            'timestamp': timestamp
        }
        
        if order_data.get('quantity'):
            params['quantity'] = order_data['quantity']
        if order_data.get('price'):
            params['price'] = order_data['price']
        if order_data.get('timeInForce'):
            params['timeInForce'] = order_data['timeInForce']
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        headers = {'X-MBX-APIKEY': api_key}
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.post(f"{base_url}{endpoint}", data=params, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Binance order placed: {result}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Binance order failed: {error}")
                    return None

    async def _place_bybit_order(self, api_key: str, api_secret: str, 
                               order_data: Dict[str, Any], testnet: bool) -> Dict[str, Any]:
        """Place order on Bybit."""
        base_url = self.endpoints["bybit"]["testnet_url" if testnet else "base_url"]
        endpoint = "/v5/order/create"
        
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        payload = {
            'category': order_data.get('category', 'spot'),
            'symbol': order_data['symbol'],
            'side': order_data['side'],  # Buy or Sell
            'orderType': order_data.get('orderType', 'Market'),
            'qty': order_data['quantity']
        }
        
        if order_data.get('price'):
            payload['price'] = order_data['price']
        
        param_str = f"timestamp={timestamp}&recv_window={recv_window}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
            'Content-Type': 'application/json'
        }
        
        url = f"{base_url}{endpoint}?{param_str}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"Bybit order placed: {result}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Bybit order failed: {error}")
                    return None

    async def get_crypto_positions(self, telegram_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get crypto positions/open orders."""
        try:
            with get_db_session() as session:
                user = session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.CRYPTO,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                # Parse exchange from server_endpoint
                exchange = connection.server_endpoint.split('_')[0] if connection.server_endpoint else "binance"
                testnet = "_testnet" in connection.server_endpoint if connection.server_endpoint else False

                if exchange == "binance":
                    return await self._get_binance_open_orders(connection.api_key, connection.api_secret, testnet)
                elif exchange == "bybit":
                    return await self._get_bybit_open_orders(connection.api_key, connection.api_secret, testnet)

                return []

        except Exception as e:
            logger.error(f"Failed to get crypto positions: {e}")
            return None

    async def _get_binance_open_orders(self, api_key: str, api_secret: str, testnet: bool) -> List[Dict[str, Any]]:
        """Get Binance open orders."""
        base_url = self.endpoints["binance"]["testnet_url" if testnet else "base_url"]
        endpoint = "/api/v3/openOrders"
        
        timestamp = int(time.time() * 1000)
        query_string = f"timestamp={timestamp}"
        signature = hmac.new(
            api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {'X-MBX-APIKEY': api_key}
        url = f"{base_url}{endpoint}?{query_string}&signature={signature}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    orders = await response.json()
                    return [
                        {
                            'order_id': order['orderId'],
                            'symbol': order['symbol'],
                            'side': order['side'],
                            'type': order['type'],
                            'quantity': float(order['origQty']),
                            'price': float(order['price']),
                            'status': order['status'],
                            'time': order['time']
                        }
                        for order in orders
                    ]
                return []

    async def _get_bybit_open_orders(self, api_key: str, api_secret: str, testnet: bool) -> List[Dict[str, Any]]:
        """Get Bybit open orders."""
        base_url = self.endpoints["bybit"]["testnet_url" if testnet else "base_url"]
        endpoint = "/v5/order/realtime"
        
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        param_str = f"category=spot&timestamp={timestamp}&recv_window={recv_window}"
        
        signature = hmac.new(
            api_secret.encode('utf-8'),
            param_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            'X-BAPI-API-KEY': api_key,
            'X-BAPI-SIGN': signature,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window
        }
        
        url = f"{base_url}{endpoint}?{param_str}"
        
        async with ClientSession(timeout=self.timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    orders = data.get('result', {}).get('list', [])
                    return [
                        {
                            'order_id': order['orderId'],
                            'symbol': order['symbol'],
                            'side': order['side'],
                            'type': order['orderType'],
                            'quantity': float(order['qty']),
                            'price': float(order.get('price', 0)),
                            'status': order['orderStatus'],
                            'time': order['createdTime']
                        }
                        for order in orders
                    ]
                return []
