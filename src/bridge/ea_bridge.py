"""
EA Bridge service for MT5 platform integration.
"""

import logging
import asyncio
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from aiohttp import ClientSession, ClientTimeout
from sqlalchemy.orm import Session

from src.models.telegram_users import TelegramUser, PlatformConnection, PlatformType
from src.database.session import SessionLocal
from src.services.user_manager import UserManager
from src.services.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class EABridge:
    """Service for communicating with MT5 Expert Advisors."""

    def __init__(self):
        self.user_manager = UserManager()
        self.config_manager = ConfigManager()
        self.default_server_endpoint = "http://127.0.0.1:8000"
        self.timeout = ClientTimeout(total=30)

    async def get_server_endpoint(self, user_id: int = None) -> str:
        """Get server endpoint for EA communication."""
        # Check if user has custom endpoint
        if user_id:
            session = SessionLocal()
            try:
                connection = session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user_id,
                    PlatformConnection.platform_type == PlatformType.MT5,
                    PlatformConnection.is_active == True
                ).first()
                
                if connection and connection.server_endpoint:
                    return connection.server_endpoint
            finally:
                session.close()

        # Check server configuration
        server_config = await self.config_manager.get_server_config("ea_server_endpoint")
        if server_config:
            return server_config

        return self.default_server_endpoint

    async def register_ea_connection(self, telegram_id: int, api_key: str, 
                                   connection_name: str = "MT5 EA") -> bool:
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
                server_endpoint=await self.get_server_endpoint()
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
                    f"{endpoint}/api/v1/ea/validate",
                    json={"api_key": api_key}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Failed to validate EA API key: {e}")
            return False

    async def send_order_to_ea(self, telegram_id: int, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send trading order to EA."""
        try:
            # Get user's EA connection
            db_session = SessionLocal()
            try:
                user = db_session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = db_session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.MT5,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                endpoint = connection.server_endpoint or await self.get_server_endpoint()
                
                # Prepare order payload
                payload = {
                    "api_key": connection.api_key,
                    "order": order_data
                }

                async with ClientSession(timeout=self.timeout) as http_session:
                    async with http_session.post(
                        f"{endpoint}/api/v1/ea/order",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Order sent to EA for user {telegram_id}: {result}")
                            return result
                        else:
                            logger.error(f"EA order failed with status {response.status}")
                            return None
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"Failed to send order to EA: {e}")
            return None

    async def get_positions_from_ea(self, telegram_id: int) -> Optional[List[Dict[str, Any]]]:
        """Get current positions from EA."""
        try:
            db_session = SessionLocal()
            try:
                user = db_session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = db_session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.MT5,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                endpoint = connection.server_endpoint or await self.get_server_endpoint()
                
                payload = {"api_key": connection.api_key}

                async with ClientSession(timeout=self.timeout) as http_session:
                    async with http_session.post(
                        f"{endpoint}/api/v1/ea/positions",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result.get("positions", [])
                        else:
                            logger.error(f"Failed to get positions with status {response.status}")
            finally:
                db_session.close()

        except Exception as e:
            logger.error(f"Failed to get positions from EA: {e}")
            return None

    async def get_user_ea_connection(self, telegram_id: int) -> Optional[Dict[str, str]]:
        """Get user's EA connection info."""
        try:
            db_session = SessionLocal()
            try:
                user = db_session.query(TelegramUser).filter(
                    TelegramUser.telegram_id == telegram_id
                ).first()

                if not user:
                    return None

                connection = db_session.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user.id,
                    PlatformConnection.platform_type == PlatformType.MT5,
                    PlatformConnection.is_active == True
                ).first()

                if not connection:
                    return None

                return {
                    "api_key": connection.api_key,
                    "server_endpoint": connection.server_endpoint or await self.get_server_endpoint()
                }
            finally:
                db_session.close()
        except Exception as e:
            logger.error(f"Failed to get user EA connection: {e}")
            return None

    async def get_account_info_from_ea(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get account information from EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return None

            endpoint = connection["server_endpoint"]
            
            payload = {"api_key": connection["api_key"]}

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/account",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("account", {})
                    else:
                        logger.error(f"Failed to get account info with status {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Failed to get account info from EA: {e}")
            return None

    async def modify_position_in_ea(self, telegram_id: int, position_ticket: int, 
                                   new_sl: float = None, new_tp: float = None) -> bool:
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
                "new_tp": new_tp
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/modify",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Position {position_ticket} modified for user {telegram_id}")
                        return True
                    else:
                        logger.error(f"Failed to modify position with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to modify position in EA: {e}")
            return False

    async def close_position_in_ea(self, telegram_id: int, position_ticket: int, 
                                  volume: float = None) -> bool:
        """Close position in EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return False

            endpoint = connection["server_endpoint"]
            
            payload = {
                "api_key": connection["api_key"],
                "ticket": position_ticket,
                "volume": volume  # None for full close
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/close",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Position {position_ticket} closed for user {telegram_id}")
                        return True
                    else:
                        logger.error(f"Failed to close position with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to close position in EA: {e}")
            return False

    async def get_trade_history_from_ea(self, telegram_id: int, days: int = 7) -> Optional[List[Dict[str, Any]]]:
        """Get trade history from EA."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return None

            endpoint = connection["server_endpoint"]
            
            payload = {
                "api_key": connection["api_key"],
                "days": days
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/history",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get("trades", [])
                    else:
                        logger.error(f"Failed to get trade history with status {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Failed to get trade history from EA: {e}")
            return None

    async def update_ea_settings(self, telegram_id: int, settings: Dict[str, Any]) -> bool:
        """Update EA settings."""
        try:
            connection = await self.get_user_ea_connection(telegram_id)

            if not connection:
                return False

            endpoint = connection["server_endpoint"]
            
            payload = {
                "api_key": connection["api_key"],
                "settings": settings
            }

            async with ClientSession(timeout=self.timeout) as http_session:
                async with http_session.post(
                    f"{endpoint}/api/v1/ea/settings",
                    json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"EA settings updated for user {telegram_id}")
                        return True
                    else:
                        logger.error(f"Failed to update EA settings with status {response.status}")
                        return False

        except Exception as e:
            logger.error(f"Failed to update EA settings: {e}")
            return False
