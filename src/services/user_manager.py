"""
User management service for multi-user trading system.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models.telegram_users import (
    TelegramUser,
    UserRole,
    SubscriptionStatus,
    UserConfiguration,
    PlatformConnection,
    PlatformType,
    SignalSubscription,
    ServerConfiguration,
)
from ..database.session import SessionLocal

logger = logging.getLogger(__name__)


class UserManager:
    """Service for managing Telegram users and their configurations."""

    def __init__(self):
        self.initial_admin_id = 6077091585  # Initial admin user ID

    async def create_user(
        self,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
    ) -> bool:
        """Create a new Telegram user."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    # Create new user
                    role = (
                        UserRole.ADMIN
                        if telegram_id == self.initial_admin_id
                        else UserRole.USER
                    )
                    user = TelegramUser(
                        telegram_id=telegram_id,
                        username=username,
                        first_name=first_name,
                        last_name=last_name,
                        role=role,
                        subscription_status=(
                            SubscriptionStatus.ACTIVE
                            if role == UserRole.ADMIN
                            else SubscriptionStatus.EXPIRED
                        ),
                    )
                    session.add(user)
                    session.commit()
                    session.refresh(user)
                    logger.info(
                        f"Created new user: {telegram_id} with role {role.value}"
                    )
                    return True
                else:
                    # Update user info if provided
                    if username and user.username != username:
                        user.username = username
                    if first_name and user.first_name != first_name:
                        user.first_name = first_name
                    if last_name and user.last_name != last_name:
                        user.last_name = last_name

                    user.last_activity = datetime.utcnow()
                    session.commit()
                    return True
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False

    async def unsubscribe_from_symbol(self, telegram_id: int, symbol: str) -> bool:
        """Unsubscribe user from trading signal for a symbol."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == telegram_id,
                        TelegramUser.is_active == True,
                    )
                    .first()
                )

                if not user:
                    return False

                subscription = (
                    session.query(SignalSubscription)
                    .filter(
                        SignalSubscription.user_id == user.id,
                        SignalSubscription.symbol == symbol,
                    )
                    .first()
                )

                if subscription:
                    subscription.is_active = False
                    session.commit()
                    logger.info(
                        f"User {telegram_id} unsubscribed from {symbol} signals"
                    )
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Failed to unsubscribe user from symbol: {e}")
            return False

    async def is_admin(self, telegram_id: int) -> bool:
        """Check if user has admin privileges."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == telegram_id,
                        TelegramUser.is_active == True,
                    )
                    .first()
                )

                return user and user.is_admin
        except Exception as e:
            logger.error(f"Failed to check if user is admin: {e}")
            return False

    async def add_admin(self, admin_telegram_id: int, target_telegram_id: int) -> bool:
        """Add admin privileges to a user (admin only)."""
        try:
            if not await self.is_admin(admin_telegram_id):
                return False

            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == target_telegram_id)
                    .first()
                )

                if user:
                    user.role = UserRole.ADMIN
                    user.subscription_status = SubscriptionStatus.ACTIVE
                    session.commit()
                    logger.info(
                        f"User {target_telegram_id} promoted to admin by {admin_telegram_id}"
                    )
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Failed to add admin privileges: {e}")
            return False

    async def remove_admin(
        self, admin_telegram_id: int, target_telegram_id: int
    ) -> bool:
        """Remove admin privileges from a user (admin only)."""
        try:
            if not await self.is_admin(admin_telegram_id):
                return False

            if target_telegram_id == self.initial_admin_id:
                return False  # Cannot remove initial admin

            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == target_telegram_id)
                    .first()
                )

                if user and user.is_admin:
                    user.role = UserRole.USER
                    session.commit()
                    logger.info(
                        f"Admin privileges removed from {target_telegram_id} by {admin_telegram_id}"
                    )
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Failed to remove admin privileges: {e}")
            return False

    async def set_subscription(
        self,
        admin_telegram_id: int,
        target_telegram_id: int,
        status: SubscriptionStatus,
        expires_at: datetime = None,
    ) -> bool:
        """Set user subscription status (admin only)."""
        try:
            if not await self.is_admin(admin_telegram_id):
                return False

            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == target_telegram_id)
                    .first()
                )

                if user:
                    user.subscription_status = status
                    user.subscription_expires_at = expires_at
                    session.commit()
                    logger.info(
                        f"Subscription for {target_telegram_id} set to {status.value} by {admin_telegram_id}"
                    )
                    return True
                else:
                    return False
        except Exception as e:
            logger.error(f"Failed to set subscription status: {e}")
            return False

    async def get_all_users(
        self, admin_telegram_id: int
    ) -> Optional[List[Dict[str, Any]]]:
        """Get all registered users (admin only)."""
        try:
            if not await self.is_admin(admin_telegram_id):
                return None

            with SessionLocal() as session:
                users = session.query(TelegramUser).all()
                return [
                    {
                        "telegram_id": user.telegram_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "role": user.role.value,
                        "subscription_status": user.subscription_status.value,
                        "is_active": user.is_active,
                        "created_at": user.created_at,
                        "last_activity": user.last_activity,
                    }
                    for user in users
                ]
        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return None

    async def register_platform_connection(
        self,
        telegram_id: int,
        platform_type: PlatformType,
        connection_name: str,
        api_key: str,
        api_secret: str = None,
        server_endpoint: str = None,
    ) -> bool:
        """Register platform connection for user."""
        try:
            if not await self.is_user_authorized(telegram_id):
                return False

            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return False

                # Check if connection already exists
                existing = (
                    session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user.id,
                        PlatformConnection.platform_type == platform_type,
                        PlatformConnection.api_key == api_key,
                    )
                    .first()
                )

                if existing:
                    return False  # Connection already exists

                connection = PlatformConnection(
                    user_id=user.id,
                    platform_type=platform_type,
                    connection_name=connection_name,
                    api_key=api_key,
                    api_secret=api_secret,
                    server_endpoint=server_endpoint,
                    last_connected=datetime.utcnow(),
                )

                session.add(connection)
                session.commit()
                logger.info(
                    f"Platform connection registered for user {telegram_id}: {platform_type.value}"
                )
                return True
        except Exception as e:
            logger.error(f"Failed to register platform connection: {e}")
            return False

    async def get_user_platform_connections(
        self, telegram_id: int
    ) -> List[Dict[str, Any]]:
        """Get user's platform connections."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return []

                connections = (
                    session.query(PlatformConnection)
                    .filter(
                        PlatformConnection.user_id == user.id,
                        PlatformConnection.is_active == True,
                    )
                    .all()
                )

                return [
                    {
                        "id": conn.id,
                        "platform_type": conn.platform_type.value,
                        "connection_name": conn.connection_name,
                        "api_key": (
                            conn.api_key[:8] + "..." if conn.api_key else None
                        ),  # Masked
                        "server_endpoint": conn.server_endpoint,
                        "last_connected": conn.last_connected,
                        "created_at": conn.created_at,
                    }
                    for conn in connections
                ]
        except Exception as e:
            logger.error(f"Failed to get user platform connections: {e}")
            return []

    async def subscribe_to_symbol(
        self, telegram_id: int, symbol: str, min_confidence: int = 60
    ) -> bool:
        """Subscribe user to trading signal for a symbol."""
        try:
            if not await self.is_user_authorized(telegram_id):
                return False

            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return False

                # Check if subscription already exists
                existing = (
                    session.query(SignalSubscription)
                    .filter(
                        SignalSubscription.user_id == user.id,
                        SignalSubscription.symbol == symbol,
                    )
                    .first()
                )

                if existing:
                    existing.is_active = True
                    existing.min_confidence = min_confidence
                else:
                    subscription = SignalSubscription(
                        user_id=user.id, symbol=symbol, min_confidence=min_confidence
                    )
                    session.add(subscription)

                session.commit()
                logger.info(f"User {telegram_id} subscribed to {symbol} signals")
                return True
        except Exception as e:
            logger.error(f"Failed to subscribe to symbol: {e}")
            return False

    async def get_user_subscriptions(self, telegram_id: int) -> List[Dict[str, Any]]:
        """Get user's symbol subscriptions."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )

                if not user:
                    return []

                subscriptions = (
                    session.query(SignalSubscription)
                    .filter(
                        SignalSubscription.user_id == user.id,
                        SignalSubscription.is_active == True,
                    )
                    .all()
                )

                return [
                    {
                        "symbol": sub.symbol,
                        "min_confidence": sub.min_confidence,
                        "created_at": sub.created_at,
                    }
                    for sub in subscriptions
                ]
        except Exception as e:
            logger.error(f"Failed to get user subscriptions: {e}")
            return []

    async def get_user(self, telegram_id: int) -> Optional[TelegramUser]:
        """Get user by Telegram ID."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(TelegramUser.telegram_id == telegram_id)
                    .first()
                )
                return user
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None

    async def is_subscribed(self, telegram_id: int) -> bool:
        """Check if user has active subscription."""
        try:
            with SessionLocal() as session:
                user = (
                    session.query(TelegramUser)
                    .filter(
                        TelegramUser.telegram_id == telegram_id,
                        TelegramUser.is_active == True,
                    )
                    .first()
                )

                if not user:
                    return False

                # Check subscription status and expiration
                if user.subscription_status == SubscriptionStatus.ACTIVE:
                    if user.subscription_expires_at is None:
                        return True
                    return user.subscription_expires_at > datetime.utcnow()

                return False
        except Exception as e:
            logger.error(f"Failed to check subscription status: {e}")
            return False

    async def is_user_authorized(self, telegram_id: int) -> bool:
        """Check if user is authorized to use the system."""
        user = await self.get_user(telegram_id)
        if not user or not user.is_active:
            return False

        # Admin users are always authorized
        if user.is_admin:
            return True

        # Regular users need active subscription
        return await self.is_subscribed(telegram_id)
