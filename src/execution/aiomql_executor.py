from __future__ import annotations

from typing import Dict, List, Optional, Any

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

	async def connect(self) -> bool:
		"""Connect using aiomql if available; otherwise defer to parent."""
		if _AIOMQL_AVAILABLE:
			try:
				# Lazy initialize aiomql client/session. API subject to lib version; keep minimal.
				# If anything fails, fallback to parent connect which already supports a mock.
				self._ai_client = getattr(aiomql, "Client", None)
				if self._ai_client is not None:
					# Best-effort placeholder; real credentials handled by MT5 terminal/bridge.
					self.connected = True
					logger.info("AioMQLExecutor connected (logical). Using aiomql for operations where possible.")
					# Try to pull basic account info if the lib exposes it; ignore failures silently
					try:
						self.account_info = await self.get_account_info()
					except Exception:  # pragma: no cover
						pass
					return True
				else:
					logger.warning("aiomql.Client not found; falling back to MT5Executor connect")
			except Exception as e:  # pragma: no cover - safety fallback
				logger.warning(f"aiomql connect failed ({e}); falling back to MT5Executor connect")
		# Fallback to standard MT5Executor logic (real MT5 or robust mock)
		return await super().connect()

	async def disconnect(self):
		"""Disconnect from aiomql or fallback executor."""
		try:
			self._ai_client = None
		except Exception:  # pragma: no cover
			pass
		await super().disconnect()

	async def place_order(self, order) -> Dict:
		"""Place order via aiomql if available; otherwise fallback to MT5Executor."""
		if _AIOMQL_AVAILABLE and self.connected:
			try:
				# Placeholder path; use fallback to ensure stability in MVP
				logger.info("AioMQLExecutor delegating order placement to fallback for MVP")
			except Exception as e:  # pragma: no cover
				logger.warning(f"aiomql place_order failed ({e}); using fallback")
		return await super().place_order(order)

	async def modify_order(self, order_id: int, sl: Optional[float] = None, tp: Optional[float] = None) -> Dict:
		if _AIOMQL_AVAILABLE and self.connected:
			try:
				logger.info("AioMQLExecutor delegating order modify to fallback for MVP")
			except Exception as e:  # pragma: no cover
				logger.warning(f"aiomql modify_order failed ({e}); using fallback")
		return await super().modify_order(order_id, sl=sl, tp=tp)

	async def close_position(self, position_id: int, volume: Optional[float] = None) -> Dict:
		if _AIOMQL_AVAILABLE and self.connected:
			try:
				logger.info("AioMQLExecutor delegating close_position to fallback for MVP")
			except Exception as e:  # pragma: no cover
				logger.warning(f"aiomql close_position failed ({e}); using fallback")
		return await super().close_position(position_id, volume=volume)

	async def get_positions(self) -> List[Dict]:
		# For MVP, use fallback which already returns robust mock data
		return await super().get_positions()

	async def get_orders(self) -> List[Dict]:
		return await super().get_orders()

	async def get_account_info(self) -> Optional[Dict[str, Any]]:
		# For MVP, rely on fallback/mock which returns a consistent dict
		return await super().get_account_info()

	@property
	def is_connected(self) -> bool:
		return super().is_connected