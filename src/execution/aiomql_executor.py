from __future__ import annotations

import time
import asyncio
from typing import Dict, List, Optional, Any

from ..core.logging import (
    get_logger, 
    log_error_with_context, 
    log_system_event,
    log_trade_event,
    log_performance_metric,
    log_operation_timing
)
from ..core.error_handler import (
    with_error_handling,
    ErrorContext,
    CircuitBreaker
)
from ..core.exceptions import (
    MT5ConnectionError,
    MT5ExecutionError,
    AioMQLError
)
from .mt5_executor import MT5Executor

logger = get_logger(__name__)

try:
    import aiomql
    from aiomql import Account, Terminal
    _AIOMQL_AVAILABLE = True
    logger.info("aiomql library loaded successfully")
except ImportError as e:
    _AIOMQL_AVAILABLE = False
    aiomql = None
    Account = None
    Terminal = None
    logger.warning(f"aiomql not installed ({e}); falling back to MT5Executor standard path")


class AioMQLExecutor(MT5Executor):
    """Async MT5 executor using aiomql when available, with graceful fallback.

    This class keeps the same public async interface as MT5Executor so it can be
    plugged into existing managers without wider refactors.
    
    Features:
    - Automatic fallback to MT5Executor if aiomql unavailable
    - Circuit breaker for connection reliability
    - Enhanced error handling and logging
    - Performance monitoring and timeout controls
    """

    def __init__(self, config):
        super().__init__(config)
        self._ai_client = None
        self._ai_session = None
        self._symbols_cache = {}
        self._connection_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=60.0,
            expected_exception=AioMQLError
        )
        self._last_heartbeat = None

    @with_error_handling("aiomql_connect", notify_telegram=True, fallback_value=False)
    async def connect(self) -> bool:
        """Connect using aiomql if available; otherwise defer to parent."""
        start_time = time.time()
        
        if _AIOMQL_AVAILABLE and self.config.is_configured:
            async with ErrorContext("aiomql_connection", {
                "login": self.config.login,
                "server": self.config.server
            }) as ctx:
                try:
                    # Check circuit breaker
                    if not self._connection_circuit_breaker.can_execute():
                        logger.warning("Connection circuit breaker is open, using fallback")
                        return await super().connect()
                    
                    logger.info("Attempting aiomql connection...")
                    
                    # Create account instance
                    account = Account(
                        login=int(self.config.login),
                        password=self.config.password,
                        server=self.config.server
                    )
                    
                    # Initialize terminal connection with timeout
                    terminal = Terminal()
                    
                    # Attempt to initialize with timeout
                    terminal_init = await asyncio.wait_for(
                        terminal.initialize(), timeout=30.0
                    )
                    
                    if terminal_init:
                        log_system_event("aiomql", "terminal_init", "Terminal initialized successfully")
                        
                        # Attempt login with timeout
                        login_success = await asyncio.wait_for(
                            account.login(), timeout=30.0
                        )
                        
                        if login_success:
                            self._ai_client = account
                            self._ai_session = terminal
                            self.connected = True
                            self._last_heartbeat = time.time()
                            
                            # Record success in circuit breaker
                            self._connection_circuit_breaker.record_success()
                            
                            # Get account info with error handling
                            try:
                                self.account_info = await self.get_account_info()
                                if self.account_info:
                                    log_system_event(
                                        "aiomql", "login_success",
                                        f"Connected to account: {self.account_info.get('login', 'unknown')}",
                                        context={"account_balance": self.account_info.get('balance', 0)}
                                    )
                            except Exception as e:
                                logger.warning(f"Failed to get aiomql account info: {e}")
                            
                            log_operation_timing("aiomql_connect", start_time, time.time())
                            return True
                        else:
                            raise AioMQLError("Login failed")
                    else:
                        raise AioMQLError("Terminal initialization failed")
                        
                except asyncio.TimeoutError:
                    self._connection_circuit_breaker.record_failure()
                    raise AioMQLError("Connection timeout")
                except Exception as e:
                    self._connection_circuit_breaker.record_failure()
                    await self._cleanup_aiomql_partial()
                    raise AioMQLError(f"Connection failed: {e}")
        
        # Fallback to standard MT5Executor logic
        log_system_event("aiomql", "fallback", "Using MT5Executor fallback")
        return await super().connect()
        
    async def _cleanup_aiomql_partial(self):
        """Clean up partial aiomql initialization."""
        try:
            if self._ai_session and hasattr(self._ai_session, 'shutdown'):
                await asyncio.wait_for(self._ai_session.shutdown(), timeout=5.0)
        except Exception as e:
            logger.warning(f"Error during aiomql partial cleanup: {e}")
        finally:
            self._ai_client = None
            self._ai_session = None
            self.connected = False

    async def disconnect(self):
        """Disconnect from aiomql or fallback executor."""
        if _AIOMQL_AVAILABLE and self.connected and (self._ai_session or self._ai_client):
            try:
                if self._ai_session and hasattr(self._ai_session, 'shutdown'):
                    await self._ai_session.shutdown()
                    logger.info("aiomql terminal shutdown successfully")
            except Exception as e:
                logger.warning(f"Error shutting down aiomql terminal: {e}")
            
            try:
                if self._ai_client and hasattr(self._ai_client, 'logout'):
                    await self._ai_client.logout()
                    logger.info("aiomql account logged out successfully")
            except Exception as e:
                logger.warning(f"Error logging out aiomql account: {e}")
        
        self._ai_client = None
        self._ai_session = None
        self.connected = False
        await super().disconnect()

    async def place_order(self, order) -> Dict:
        """Place order via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Validate order data
                if not isinstance(order, dict):
                    logger.error("Order must be a dictionary")
                    return await super().place_order(order)
                
                # Validate required fields
                symbol = order.get('symbol', '').strip()
                if not symbol:
                    logger.error("Order missing symbol")
                    return await super().place_order(order)
                
                # Map and validate order parameters
                order_type_raw = order.get('type', 'BUY')
                order_type = self._map_order_type(order_type_raw)
                
                # Validate numeric fields
                try:
                    volume = float(order.get('volume', 0.01))
                    price = float(order.get('price', 0.0))
                    sl = float(order.get('sl', 0.0)) if order.get('sl') else 0.0
                    tp = float(order.get('tp', 0.0)) if order.get('tp') else 0.0
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid numeric values in order: {e}")
                    return await super().place_order(order)
                
                if volume <= 0:
                    logger.error(f"Invalid volume: {volume}")
                    return await super().place_order(order)
                
                comment = str(order.get('comment', 'AioMQL Order'))[:31]  # MT5 comment limit
                
                # Execute order through aiomql with timeout
                try:
                    result = await asyncio.wait_for(
                        self._ai_session.trade_action(
                            action="DEAL",
                            symbol=symbol,
                            type=order_type,
                            volume=volume,
                            price=price,
                            sl=sl if sl > 0 else None,
                            tp=tp if tp > 0 else None,
                            comment=comment
                        ),
                        timeout=30.0
                    )
                    
                    if result and hasattr(result, 'retcode'):
                        if result.retcode == 10009:  # TRADE_RETCODE_DONE
                            order_id = getattr(result, 'order', 0)
                            logger.info(f"Order placed successfully via aiomql: {order_id}")
                            return {
                                'order_id': order_id,
                                'symbol': symbol,
                                'volume': volume,
                                'price': price,
                                'sl': sl,
                                'tp': tp,
                                'comment': comment,
                                'status': 'success',
                                'retcode': result.retcode
                            }
                        else:
                            logger.warning(f"aiomql order failed with retcode: {result.retcode}")
                    else:
                        logger.warning(f"aiomql order placement returned invalid result: {result}")
                        
                except asyncio.TimeoutError:
                    logger.warning("aiomql place_order timeout, using fallback")
                    
            except Exception as e:
                logger.warning(f"aiomql place_order failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().place_order(order)

    async def modify_order(self, order_id: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict:
        """Modify order via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Get current order details first
                orders = await self.get_orders()
                order = next((o for o in orders if o.get('order_id') == order_id), None)
                
                if order:
                    # Execute order modification through aiomql
                    result = await self._ai_session.trade_action(
                        action="MODIFY",
                        order=order_id,
                        sl=sl if sl is not None else order.get('sl', 0.0),
                        tp=tp if tp is not None else order.get('tp', 0.0)
                    )
                    
                    if result and hasattr(result, 'retcode') and result.retcode == 10009:  # TRADE_RETCODE_DONE
                        logger.info(f"Order {order_id} modified successfully via aiomql")
                        return {
                            'order_id': order_id,
                            'sl': sl if sl is not None else order.get('sl', 0.0),
                            'tp': tp if tp is not None else order.get('tp', 0.0),
                            'status': 'success'
                        }
                    else:
                        logger.warning(f"aiomql order modification returned invalid result: {result}")
                else:
                    logger.warning(f"Order {order_id} not found for modification")
            except Exception as e:
                logger.warning(f"aiomql modify_order failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().modify_order(order_id, sl=sl, tp=tp)

    async def close_position(self, position_id: int, volume: Optional[float] = None) -> Dict:
        """Close position via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Get current position details first
                positions = await self.get_positions()
                position = next((p for p in positions if p.get('position_id') == position_id), None)
                
                if position:
                    # Determine volume to close
                    close_volume = volume if volume is not None else position.get('volume', 0.01)
                    
                    # Execute position close through aiomql
                    result = await self._ai_session.trade_action(
                        action="DEAL",
                        position=position_id,
                        type="SELL" if position.get('type') == "BUY" else "BUY",
                        volume=close_volume,
                        comment="Close position"
                    )
                    
                    if result and hasattr(result, 'retcode') and result.retcode == 10009:  # TRADE_RETCODE_DONE
                        logger.info(f"Position {position_id} closed successfully via aiomql")
                        return {
                            'position_id': position_id,
                            'volume': close_volume,
                            'status': 'success'
                        }
                    else:
                        logger.warning(f"aiomql position close returned invalid result: {result}")
                else:
                    logger.warning(f"Position {position_id} not found for closing")
            except Exception as e:
                logger.warning(f"aiomql close_position failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().close_position(position_id, volume=volume)

    async def get_positions(self) -> List[Dict]:
        """Get positions via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Get positions through aiomql with timeout
                positions = await asyncio.wait_for(
                    self._ai_session.get_positions(), timeout=15.0
                )
                
                if positions is not None:
                    # Transform to standard format with validation
                    result = []
                    for pos in positions:
                        try:
                            # Validate and extract position data
                            ticket = getattr(pos, 'ticket', None)
                            symbol = getattr(pos, 'symbol', None)
                            pos_type = getattr(pos, 'type', None)
                            
                            # Skip positions with missing critical data
                            if ticket is None or symbol is None or pos_type is None:
                                logger.warning(f"Skipping position with missing data: {pos}")
                                continue
                            
                            position_dict = {
                                'position_id': int(ticket) if isinstance(ticket, (int, str)) else 0,
                                'symbol': str(symbol).strip(),
                                'type': "BUY" if pos_type == 0 else "SELL",
                                'volume': float(getattr(pos, 'volume', 0.0)),
                                'open_price': float(getattr(pos, 'price_open', 0.0)),
                                'current_price': float(getattr(pos, 'price_current', 0.0)),
                                'sl': float(getattr(pos, 'sl', 0.0)),
                                'tp': float(getattr(pos, 'tp', 0.0)),
                                'profit': float(getattr(pos, 'profit', 0.0)),
                                'swap': float(getattr(pos, 'swap', 0.0)),
                                'time': int(getattr(pos, 'time', 0)),
                                'comment': str(getattr(pos, 'comment', '')).strip()
                            }
                            
                            result.append(position_dict)
                            
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error processing position {getattr(pos, 'ticket', 'unknown')}: {e}")
                            continue
                    
                    logger.info(f"Retrieved {len(result)} positions via aiomql")
                    return result
                else:
                    logger.warning("aiomql get_positions returned None")
                    
            except asyncio.TimeoutError:
                logger.warning("aiomql get_positions timeout, using fallback")
            except Exception as e:
                logger.warning(f"aiomql get_positions failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().get_positions()

    async def get_orders(self) -> List[Dict]:
        """Get orders via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Get orders through aiomql
                orders = await self._ai_session.get_orders()
                
                if orders is not None:
                    # Transform to standard format
                    result = []
                    for order in orders:
                        result.append({
                            'order_id': getattr(order, 'ticket', 0),
                            'symbol': getattr(order, 'symbol', ''),
                            'type': self._map_order_type_reverse(getattr(order, 'type', 0)),
                            'volume': getattr(order, 'volume_initial', 0.0),
                            'price': getattr(order, 'price_open', 0.0),
                            'sl': getattr(order, 'sl', 0.0),
                            'tp': getattr(order, 'tp', 0.0),
                            'time': getattr(order, 'time_setup', 0),
                            'comment': getattr(order, 'comment', '')
                        })
                    
                    logger.info(f"Retrieved {len(result)} orders via aiomql")
                    return result
                else:
                    logger.warning("aiomql get_orders returned None")
            except Exception as e:
                logger.warning(f"aiomql get_orders failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().get_orders()

    async def get_account_info(self) -> Optional[Dict[str, Any]]:
        """Get account info via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_client:
            try:
                # Get account info through aiomql Account
                if hasattr(self._ai_client, 'info'):
                    account_info = self._ai_client.info
                    
                    if account_info is not None:
                        # Transform to standard format
                        return {
                            'login': getattr(account_info, 'login', self.config.login),
                            'balance': getattr(account_info, 'balance', 0.0),
                            'equity': getattr(account_info, 'equity', 0.0),
                            'margin': getattr(account_info, 'margin', 0.0),
                            'free_margin': getattr(account_info, 'margin_free', 0.0),
                            'leverage': getattr(account_info, 'leverage', 100),
                            'currency': getattr(account_info, 'currency', 'USD'),
                            'server': getattr(account_info, 'server', self.config.server),
                            'name': getattr(account_info, 'name', ''),
                            'company': getattr(account_info, 'company', '')
                        }
                    else:
                        logger.warning("aiomql account info is None")
                else:
                    logger.warning("aiomql account client has no info attribute")
            except Exception as e:
                logger.warning(f"aiomql get_account_info failed ({e}); using fallback")
        
        # Fallback to standard MT5Executor
        return await super().get_account_info()

    @property
    def is_connected(self) -> bool:
        """Check if connected to MT5 or aiomql."""
        return self.connected
        
    # Helper methods for aiomql integration
    def _map_order_type(self, order_type: str) -> str:
        """Map order type from our format to aiomql format."""
        order_type = str(order_type).upper().strip()
        
        type_map = {
            'BUY': 'BUY',
            'SELL': 'SELL',
            'BUY_LIMIT': 'BUY_LIMIT',
            'SELL_LIMIT': 'SELL_LIMIT',
            'BUY_STOP': 'BUY_STOP',
            'SELL_STOP': 'SELL_STOP',
            'BUYLIMIT': 'BUY_LIMIT',
            'SELLLIMIT': 'SELL_LIMIT',
            'BUYSTOP': 'BUY_STOP',
            'SELLSTOP': 'SELL_STOP',
            'MARKET': 'BUY',  # Default to BUY for MARKET orders
            'LONG': 'BUY',
            'SHORT': 'SELL'
        }
        
        mapped_type = type_map.get(order_type)
        if not mapped_type:
            logger.warning(f"Unknown order type '{order_type}', defaulting to BUY")
            return 'BUY'
        return mapped_type
        
    def _map_order_type_reverse(self, order_type_int: int) -> str:
        """Map order type from aiomql integer format to our string format."""
        type_map = {
            0: 'BUY',
            1: 'SELL',
            2: 'BUY_LIMIT',
            3: 'SELL_LIMIT',
            4: 'BUY_STOP',
            5: 'SELL_STOP'
        }
        return type_map.get(order_type_int, 'UNKNOWN')
        
    async def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol information via aiomql if available; otherwise fallback to MT5Executor."""
        if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
            try:
                # Check cache first
                if symbol in self._symbols_cache:
                    return self._symbols_cache[symbol]
                
                # Get symbol info through aiomql
                symbol_info = await self._ai_session.get_symbol_info(symbol)
                
                if symbol_info is not None:
                    # Transform to standard format
                    result = {
                        'name': getattr(symbol_info, 'name', symbol),
                        'bid': getattr(symbol_info, 'bid', 0.0),
                        'ask': getattr(symbol_info, 'ask', 0.0),
                        'point': getattr(symbol_info, 'point', 0.00001),
                        'digits': getattr(symbol_info, 'digits', 5),
                        'spread': getattr(symbol_info, 'spread', 0),
                        'trade_stops_level': getattr(symbol_info, 'trade_stops_level', 0)
                    }
                    
                    # Cache the result
                    self._symbols_cache[symbol] = result
                    return result
                else:
                    logger.warning(f"aiomql get_symbol_info returned None for {symbol}")
            except Exception as e:
                logger.warning(f"aiomql get_symbol_info failed for {symbol}: {e}")
        
        # Fallback to standard MT5Executor
        return await super().get_symbol_info(symbol) if hasattr(super(), 'get_symbol_info') else None
