from __future__ import annotations

from typing import Dict, List, Optional, Any
import asyncio

from ..core.logging import get_logger
from .mt5_executor import MT5Executor

logger = get_logger(__name__)

try:
	import aiomql  # type: ignore
	_AIOMQL_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
	_AIOMQL_AVAILABLE = False
	aiomql = None  # type: ignore
	logger.warning("aiomql not installed; falling back to MT5Executor mock/standard path")


class AioMQLExecutor(MT5Executor):
	"""Async MT5 executor using aiomql when available, with graceful fallback.

	This class keeps the same public async interface as MT5Executor so it can be
	plugged into existing managers without wider refactors.
	"""

	def __init__(self, config):
		super().__init__(config)
		self._ai_client = None
		self._ai_session = None
		self._symbols_cache = {}

	async def connect(self) -> bool:
		"""Connect using aiomql if available; otherwise defer to parent."""
		if _AIOMQL_AVAILABLE:
			try:
				# Initialize aiomql client with proper configuration
				if hasattr(aiomql, "Client"):
					self._ai_client = aiomql.Client(
						login=self.config.login if self.config.login else 0,
						password=self.config.password,
						server=self.config.server,
						timeout=self.config.timeout / 1000  # Convert ms to seconds
					)
					
					# Create and initialize session
					try:
						self._ai_session = await self._ai_client.create_session()
						if self._ai_session:
							self.connected = True
							logger.info("AioMQLExecutor connected successfully using aiomql.")
							
							# Get account info
							try:
								self.account_info = await self.get_account_info()
								logger.info(f"Connected to account: {self.account_info.get('login', 'unknown')}")
							except Exception as e:
								logger.warning(f"Failed to get account info: {e}")
							
							return True
					except Exception as e:
						logger.warning(f"Failed to create aiomql session: {e}")
				else:
					logger.warning("aiomql.Client not found; falling back to MT5Executor connect")
			except Exception as e:
				logger.warning(f"aiomql connect failed ({e}); falling back to MT5Executor connect")
		
		# Fallback to standard MT5Executor logic (real MT5 or robust mock)
		return await super().connect()

	async def disconnect(self):
		"""Disconnect from aiomql or fallback executor."""
		if _AIOMQL_AVAILABLE and self._ai_session:
			try:
				await self._ai_session.close()
				logger.info("AioMQLExecutor session closed successfully.")
			except Exception as e:
				logger.warning(f"Error closing aiomql session: {e}")
			
			try:
				if self._ai_client:
					await self._ai_client.close()
					logger.info("AioMQLExecutor client closed successfully.")
			except Exception as e:
				logger.warning(f"Error closing aiomql client: {e}")
		
		self._ai_client = None
		self._ai_session = None
		self.connected = False
		await super().disconnect()

	async def place_order(self, order) -> Dict:
		"""Place order via aiomql if available; otherwise fallback to MT5Executor."""
		if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
			try:
				# Map order parameters to aiomql format
				order_type = self._map_order_type(order.get('type', 'MARKET'))
				symbol = order.get('symbol', '')
				volume = order.get('volume', 0.01)
				price = order.get('price', 0.0)
				sl = order.get('sl', 0.0)
				tp = order.get('tp', 0.0)
				comment = order.get('comment', 'AioMQL Order')
				
				# Execute order through aiomql
				result = await self._ai_session.trade_action(
					action="DEAL",
					symbol=symbol,
					type=order_type,
					volume=volume,
					price=price,
					sl=sl,
					tp=tp,
					comment=comment
				)
				
				if result and hasattr(result, 'order'):
					logger.info(f"Order placed successfully via aiomql: {result.order}")
					return {
						'order_id': result.order,
						'symbol': symbol,
						'volume': volume,
						'price': price,
						'sl': sl,
						'tp': tp,
						'comment': comment,
						'status': 'success'
					}
				else:
					logger.warning(f"aiomql order placement returned invalid result: {result}")
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
				# Get positions through aiomql
				positions = await self._ai_session.get_positions()
				
				if positions is not None:
					# Transform to standard format
					result = []
					for pos in positions:
						result.append({
							'position_id': getattr(pos, 'ticket', 0),
							'symbol': getattr(pos, 'symbol', ''),
							'type': "BUY" if getattr(pos, 'type', 0) == 0 else "SELL",
							'volume': getattr(pos, 'volume', 0.0),
							'open_price': getattr(pos, 'price_open', 0.0),
							'current_price': getattr(pos, 'price_current', 0.0),
							'sl': getattr(pos, 'sl', 0.0),
							'tp': getattr(pos, 'tp', 0.0),
							'profit': getattr(pos, 'profit', 0.0),
							'swap': getattr(pos, 'swap', 0.0),
							'time': getattr(pos, 'time', 0),
							'comment': getattr(pos, 'comment', '')
						})
					
					logger.info(f"Retrieved {len(result)} positions via aiomql")
					return result
				else:
					logger.warning("aiomql get_positions returned None")
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
		if _AIOMQL_AVAILABLE and self.connected and self._ai_session:
			try:
				# Get account info through aiomql
				account = await self._ai_session.get_account_info()
				
				if account is not None:
					# Transform to standard format
					return {
						'login': getattr(account, 'login', 0),
						'balance': getattr(account, 'balance', 0.0),
						'equity': getattr(account, 'equity', 0.0),
						'margin': getattr(account, 'margin', 0.0),
						'free_margin': getattr(account, 'margin_free', 0.0),
						'leverage': getattr(account, 'leverage', 100),
						'currency': getattr(account, 'currency', 'USD'),
						'server': getattr(account, 'server', ''),
						'name': getattr(account, 'name', ''),
						'company': getattr(account, 'company', '')
					}
				else:
					logger.warning("aiomql get_account_info returned None")
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
		type_map = {
			'BUY': 'BUY',
			'SELL': 'SELL',
			'BUY_LIMIT': 'BUY_LIMIT',
			'SELL_LIMIT': 'SELL_LIMIT',
			'BUY_STOP': 'BUY_STOP',
			'SELL_STOP': 'SELL_STOP',
			'MARKET': 'BUY'  # Default to BUY for MARKET orders
		}
		return type_map.get(order_type, 'BUY')
		
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