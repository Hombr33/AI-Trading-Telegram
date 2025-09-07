"""
EA Bridge service for MT5 platform integration with enhanced multi-user support.
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from aiohttp import ClientSession, ClientTimeout

from src.database.session import SessionLocal
from src.models.telegram_users import PlatformConnection, PlatformType, TelegramUser
from src.services.config_manager import ConfigManager
from src.services.user_manager import UserManager

logger = logging.getLogger(__name__)


class EABridge:
    """Enhanced service for communicating with MT5 Expert Advisors with multi-user support."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.default_server_endpoint = "http://127.0.0.1:8000"
        self.timeout = ClientTimeout(total=30)

        # Multi-user enhancements
        self._user_connections = {}  # Cache for user connections
        self._connection_lock = asyncio.Lock()
        self._user_positions = defaultdict(dict)  # user_id -> {ticket: position_data}
        self._user_risk_metrics = defaultdict(dict)  # user_id -> risk_metrics
        self._position_update_tasks = {}  # user_id -> task
        self._connection_health = defaultdict(dict)  # user_id -> health_status

    async def get_server_endpoint(self, user_id: int = None) -> str:
        """Get server endpoint for EA communication."""
        # Check if user has custom endpoint
        if user_id:
            session = SessionLocal()
            try:
                connection = (
                    session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user_id,
                        PlatformConnection.platform_type == PlatformType.MT5,
                        PlatformConnection.is_active,
                    )
                    .first()
                )

                if connection and connection.server_endpoint:
                    return connection.server_endpoint
            finally:
                session.close()

        # Check server configuration
        server_config = await self.config_manager.get_server_config(
            "ea_server_endpoint"
        )
        if server_config:
            return server_config

        return self.default_server_endpoint

    async def register_ea_connection(
        self, telegram_id: int, api_key: str, connection_name: str = "MT5 EA"
    ) -> bool:
        """Register EA connection for user."""
        try:
            # Validate API key with EA
            if not await self.validate_ea_api_key(api_key):
                return False

            # Register platform connection
            success = await self.user_manager.register_platform_connection(
                telegram_id=telegram_id,
                platform_type=PlatformType.MT5,
                connection_name=connection_name,
                api_key=api_key,
                server_endpoint=await self.get_server_endpoint(),
            )

            if success:
                logger.info(f"EA connection registered for user {telegram_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to register EA connection: {e}")

        return False

    async def validate_ea_api_key(self, api_key: str) -> bool:
        """Validate EA API key by testing connection."""
        try:
            endpoint = await self.get_server_endpoint()
            async with ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{endpoint}/api/v1/ea/validate", json={"api_key": api_key}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to validate EA API key: {e}")
            return False

    async def send_order_to_ea(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send trading order to EA."""
        try:
            # Get user's EA connection
            db_session = SessionLocal()
            try:
                user = (
                    db_session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return None

                connection = (
                    db_session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user.id,
                        PlatformConnection.platform_type == PlatformType.MT5,
                        PlatformConnection.is_active,
                    )
                    .first()
                )

                if not connection:
                    return None

                endpoint = (
                    connection.server_endpoint or await self.get_server_endpoint()
                )

                # Prepare order payload
                payload = {"api_key": connection.api_key, "order": order_data}

                async with ClientSession(timeout=self.timeout) as http_session:
                    async with http_session.post(
                        f"{endpoint}/api/v1/ea/order", json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(
                                f"Order sent to EA for user {telegram_id}: {result}"
                            )
                            return result
                        else:
                            logger.error(
                                f"EA order failed with status {response.status}"
                            )
                            return None
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"Failed to send order to EA: {e}")
            return None

    async def get_positions_from_ea(
        self, telegram_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get current positions from EA."""
        try:
            db_session = SessionLocal()
            try:
                user = (
                    db_session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return None

                connection = (
                    db_session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user.id,
                        PlatformConnection.platform_type == PlatformType.MT5,
                        PlatformConnection.is_active,
                    )
                    .first()
                )

                if not connection:
                    return None

                endpoint = (
                    connection.server_endpoint or await self.get_server_endpoint()
                )

                payload = {"api_key": connection.api_key}

                async with ClientSession(timeout=self.timeout) as http_session:
                    async with http_session.post(
                        f"{endpoint}/api/v1/ea/positions", json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("positions", [])
                        else:
                            logger.error(
                                f"Failed to get positions with status {response.status}"
                            )
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"Failed to get positions from EA: {e}")
            return None

    async def get_user_ea_connection(
        self, telegram_id: int
    ) -> Optional[Dict[str, str]]:
        """Get user's EA connection info."""
        try:
            db_session = SessionLocal()
            try:
                user = (
                    db_session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return None

                connection = (
                    db_session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user.id,
                        PlatformConnection.platform_type == PlatformType.MT5,
                        PlatformConnection.is_active,
                    )
                    .first()
                )

                if not connection:
                    return None

                return {
                    "api_key": connection.api_key,
                    "server_endpoint": connection.server_endpoint
                    or await self.get_server_endpoint(),
                }
            finally:
                db_session.close()
        except Exception as e:
            logger.error(f"Failed to get user EA connection: {e}")
            return None

    async def get_account_info_from_ea(
        self, telegram_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get account information from EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return None

            endpoint = connection["server_endpoint"]

            payload = {"api_key": connection["api_key"]}

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/account", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("account", {})
                    else:
                        logger.error(
                            f"Failed to get account info with status {response.status}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Failed to get account info from EA: {e}")
            return None

    async def modify_position_in_ea(
        self,
        telegram_id: int,
        position_ticket: int,
        new_sl: float = None,
        new_tp: float = None,
    ) -> bool:
        """Modify position in EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return False

            endpoint = connection["server_endpoint"]

            payload = {
                "api_key": connection["api_key"],
                "ticket": position_ticket,
                "new_sl": new_sl,
                "new_tp": new_tp,
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/modify", json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Position {position_ticket} modified for user {telegram_id}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Failed to modify position with status {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to modify position in EA: {e}")
            return False

    async def close_position_in_ea(
        self, telegram_id: int, position_ticket: int, volume: float = None
    ) -> bool:
        """Close position in EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return False

            endpoint = connection["server_endpoint"]

            payload = {
                "api_key": connection["api_key"],
                "ticket": position_ticket,
                "volume": volume,  # None for full close
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/close", json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(
                            f"Position {position_ticket} closed for user {telegram_id}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Failed to close position with status {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to close position in EA: {e}")
            return False

    async def get_trade_history_from_ea(
        self, telegram_id: int, days: int = 7
    ) -> Optional[List[Dict[str, Any]]]:
        """Get trade history from EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return None

            endpoint = connection["server_endpoint"]

            payload = {"api_key": connection["api_key"], "days": days}

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/history", json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("trades", [])
                    else:
                        logger.error(
                            f"Failed to get trade history with status {response.status}"
                        )
                        return None

        except Exception as e:
            logger.error(f"Failed to get trade history from EA: {e}")
            return None

    async def update_ea_settings(
        self, telegram_id: int, settings: Dict[str, Any]
    ) -> bool:
        """Update EA settings."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return False

            endpoint = connection["server_endpoint"]

            payload = {"api_key": connection["api_key"], "settings": settings}

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/settings", json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"EA settings updated for user {telegram_id}")
                        return True
                    else:
                        logger.error(
                            f"Failed to update EA settings with status {response.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Failed to update EA settings: {e}")
            return False

    # Enhanced Multi-User Methods

    async def initialize_user_session(self, telegram_id: int) -> bool:
        """Initialize user session with connection caching and health monitoring."""
        try:
            async with self._connection_lock:
                if telegram_id in self._user_connections:
                    # Check if existing connection is still valid
                    if await self._validate_cached_connection(telegram_id):
                        return True

                # Establish new connection
                connection = await self._establish_user_connection(telegram_id)
                if connection:
                    self._user_connections[telegram_id] = connection
                    self._connection_health[telegram_id] = {
                        "status": "healthy",
                        "last_check": datetime.utcnow(),
                        "consecutive_failures": 0,
                    }

                    # Start position monitoring for user
                    await self._start_user_position_monitoring(telegram_id)
                    logger.info(f"User session initialized for {telegram_id}")
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to initialize user session for {telegram_id}: {e}")
            return False

    async def _establish_user_connection(
        self, telegram_id: int
    ) -> Optional[Dict[str, str]]:
        """Establish a validated connection for user."""
        try:
            # Get user connection details
            connection_info = await self.get_user_ea_connection(telegram_id)
            if not connection_info:
                return None

            # Validate connection
            if not await self.validate_ea_api_key(connection_info["api_key"]):
                logger.warning(f"Invalid API key for user {telegram_id}")
                return None

            # Test connection
            if not await self._test_connection(connection_info):
                logger.warning(f"Connection test failed for user {telegram_id}")
                return None

            return connection_info

        except Exception as e:
            logger.error(f"Failed to establish connection for user {telegram_id}: {e}")
            return None

    async def _validate_cached_connection(self, telegram_id: int) -> bool:
        """Validate cached connection is still active."""
        try:
            connection = self._user_connections.get(telegram_id)
            if not connection:
                return False

            # Test connection health
            return await self._test_connection(connection)

        except Exception as e:
            logger.error(f"Connection validation failed for user {telegram_id}: {e}")
            return False

    async def _test_connection(self, connection: Dict[str, str]) -> bool:
        """Test connection to EA server."""
        try:
            endpoint = connection["server_endpoint"]
            async with ClientSession(timeout=ClientTimeout(total=10)) as session:
                async with session.get(f"{endpoint}/api/v1/ea/health") as response:
                    return response.status == 200
        except Exception:
            return False

    async def _start_user_position_monitoring(self, telegram_id: int) -> None:
        """Start position monitoring for specific user."""
        try:
            if telegram_id in self._position_update_tasks:
                return  # Already monitoring

            task = asyncio.create_task(self._monitor_user_positions(telegram_id))
            self._position_update_tasks[telegram_id] = task
            logger.info(f"Started position monitoring for user {telegram_id}")

        except Exception as e:
            logger.error(
                f"Failed to start position monitoring for user {telegram_id}: {e}"
            )

    async def _monitor_user_positions(self, telegram_id: int) -> None:
        """Monitor positions for specific user."""
        while True:
            try:
                await asyncio.sleep(30)  # Update every 30 seconds

                # Check if user session is still active
                if telegram_id not in self._user_connections:
                    break

                # Update user positions
                positions = await self.get_positions_from_ea(telegram_id)
                if positions:
                    async with self._connection_lock:
                        self._user_positions[telegram_id] = {
                            pos.get("ticket"): pos for pos in positions
                        }

                    # Update risk metrics
                    await self._update_user_risk_metrics(telegram_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring positions for user {telegram_id}: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _update_user_risk_metrics(self, telegram_id: int) -> None:
        """Update risk metrics for specific user."""
        try:
            positions = self._user_positions.get(telegram_id, {})
            if not positions:
                self._user_risk_metrics[telegram_id] = {
                    "total_exposure": 0.0,
                    "total_pnl": 0.0,
                    "position_count": 0,
                    "daily_pnl": 0.0,
                    "last_update": datetime.utcnow(),
                }
                return

            total_exposure = 0.0
            total_pnl = 0.0
            position_count = len(positions)

            for pos in positions.values():
                volume = pos.get("volume", 0)
                current_price = pos.get("current_price", pos.get("price_open", 0))
                profit = pos.get("profit", 0)

                exposure = volume * current_price
                total_exposure += exposure
                total_pnl += profit

            self._user_risk_metrics[telegram_id] = {
                "total_exposure": total_exposure,
                "total_pnl": total_pnl,
                "position_count": position_count,
                "daily_pnl": total_pnl,  # Simplified - would need daily tracking
                "last_update": datetime.utcnow(),
            }

        except Exception as e:
            logger.error(f"Failed to update risk metrics for user {telegram_id}: {e}")

    async def get_user_positions(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get positions for specific user with enhanced tracking."""
        try:
            async with self._connection_lock:
                # Return cached positions if available
                if telegram_id in self._user_positions:
                    return list(self._user_positions[telegram_id].values())

                # Fallback to direct API call
                positions = await self.get_positions_from_ea(telegram_id)
                if positions:
                    self._user_positions[telegram_id] = {
                        pos.get("ticket"): pos for pos in positions
                    }
                return positions or []

        except Exception as e:
            logger.error(f"Failed to get user positions for {telegram_id}: {e}")
            return []

    async def get_user_risk_metrics(self, telegram_id: int) -> Dict[str, Any]:
        """Get risk metrics for specific user."""
        try:
            async with self._connection_lock:
                return self._user_risk_metrics.get(
                    telegram_id,
                    {
                        "total_exposure": 0.0,
                        "total_pnl": 0.0,
                        "position_count": 0,
                        "daily_pnl": 0.0,
                        "last_update": datetime.utcnow(),
                    },
                )
        except Exception as e:
            logger.error(f"Failed to get risk metrics for user {telegram_id}: {e}")
            return {}

    async def validate_user_risk_limits(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate order against user's risk limits."""
        try:
            risk_metrics = await self.get_user_risk_metrics(telegram_id)

            # Get user risk configuration
            user_config = await self.config_manager.get_user_config(telegram_id, "risk")
            if not user_config:
                return True, "No risk limits configured"

            # Check position count limit
            max_positions = user_config.get("max_open_positions", 5)
            if risk_metrics["position_count"] >= max_positions:
                return False, f"Maximum positions ({max_positions}) reached"

            # Check exposure limit
            max_exposure = user_config.get("max_exposure", 10000)
            if risk_metrics["total_exposure"] >= max_exposure:
                return False, f"Maximum exposure ({max_exposure}) reached"

            # Check daily drawdown limit
            max_drawdown = user_config.get("max_daily_drawdown_pct", 5.0)
            if risk_metrics["daily_pnl"] < 0:
                drawdown_pct = (
                    abs(risk_metrics["daily_pnl"])
                    / (risk_metrics["total_exposure"] + abs(risk_metrics["daily_pnl"]))
                    * 100
                )
                if drawdown_pct >= max_drawdown:
                    return False, f"Daily drawdown limit ({max_drawdown}%) reached"

            return True, "Risk check passed"

        except Exception as e:
            logger.error(f"Risk validation failed for user {telegram_id}: {e}")
            return False, f"Risk validation error: {str(e)}"

    async def send_order_with_risk_check(
        self, telegram_id: int, order_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Send order with comprehensive risk checking."""
        try:
            # Validate risk limits
            risk_valid, risk_message = await self.validate_user_risk_limits(
                telegram_id, order_data
            )
            if not risk_valid:
                logger.warning(
                    f"Risk limit violation for user {telegram_id}: {risk_message}"
                )
                return {
                    "success": False,
                    "error": f"Risk limit violation: {risk_message}",
                    "risk_check": False,
                }

            # Send order
            result = await self.send_order_to_ea(telegram_id, order_data)
            if result:
                # Update cached positions after successful order
                await asyncio.sleep(2)  # Brief delay for position update
                positions = await self.get_positions_from_ea(telegram_id)
                if positions:
                    async with self._connection_lock:
                        self._user_positions[telegram_id] = {
                            pos.get("ticket"): pos for pos in positions
                        }
                        await self._update_user_risk_metrics(telegram_id)

                result["risk_check"] = True
                return result

            return result

        except Exception as e:
            logger.error(
                f"Failed to send order with risk check for user {telegram_id}: {e}"
            )
            return {"success": False, "error": str(e), "risk_check": False}

    async def cleanup_user_session(self, telegram_id: int) -> None:
        """Cleanup user session and resources."""
        try:
            async with self._connection_lock:
                # Cancel position monitoring task
                if telegram_id in self._position_update_tasks:
                    task = self._position_update_tasks[telegram_id]
                    if not task.done():
                        task.cancel()
                    del self._position_update_tasks[telegram_id]

                # Clear cached data
                self._user_connections.pop(telegram_id, None)
                self._user_positions.pop(telegram_id, None)
                self._user_risk_metrics.pop(telegram_id, None)
                self._connection_health.pop(telegram_id, None)

                logger.info(f"Cleaned up session for user {telegram_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup session for user {telegram_id}: {e}")

    async def get_all_user_connections_health(self) -> Dict[str, Any]:
        """Get health status of all user connections."""
        try:
            async with self._connection_lock:
                health_status = {}
                for telegram_id, health in self._connection_health.items():
                    health_status[str(telegram_id)] = health.copy()

                return {
                    "total_connections": len(self._user_connections),
                    "healthy_connections": len(
                        [
                            h
                            for h in self._connection_health.values()
                            if h.get("status") == "healthy"
                        ]
                    ),
                    "connection_details": health_status,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logger.error(f"Failed to get connection health status: {e}")
            return {"error": str(e)}

    async def force_refresh_user_positions(self, telegram_id: int) -> bool:
        """Force refresh positions for specific user."""
        try:
            positions = await self.get_positions_from_ea(telegram_id)
            if positions is not None:
                async with self._connection_lock:
                    self._user_positions[telegram_id] = {
                        pos.get("ticket"): pos for pos in positions
                    }
                    await self._update_user_risk_metrics(telegram_id)
                return True
            return False

        except Exception as e:
            logger.error(f"Failed to refresh positions for user {telegram_id}: {e}")
            return False
