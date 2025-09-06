"""
Telegram user models for multi-user trading system.
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Integer,
    BigInteger,
    Text,
    JSON,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from .base import Base


class UserRole(PyEnum):
    """User role enumeration."""

    ADMIN = "admin"
    USER = "user"


class SubscriptionStatus(PyEnum):
    """Subscription status enumeration."""

    ACTIVE = "active"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class PlatformType(PyEnum):
    """Trading platform type enumeration."""

    MT5 = "mt5"
    CRYPTO = "crypto"


class TelegramUser(Base):
    """Telegram user model for multi-user trading system."""

    __tablename__ = "telegram_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    subscription_status = Column(
        Enum(SubscriptionStatus), default=SubscriptionStatus.EXPIRED, nullable=False
    )
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_activity = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    configurations = relationship(
        "UserConfiguration", back_populates="user", cascade="all, delete-orphan"
    )
    platform_connections = relationship(
        "PlatformConnection", back_populates="user", cascade="all, delete-orphan"
    )
    signal_subscriptions = relationship(
        "SignalSubscription", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TelegramUser(telegram_id={self.telegram_id}, username='{self.username}')>"

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN

    @property
    def is_subscribed(self) -> bool:
        """Check if user has active subscription."""
        return self.subscription_status == SubscriptionStatus.ACTIVE


class UserConfiguration(Base):
    """User-specific configuration settings."""

    __tablename__ = "user_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=False)
    config_type = Column(
        String(50), nullable=False
    )  # risk, symbol, signal, model, trading, rules
    config_data = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("TelegramUser", back_populates="configurations")

    def __repr__(self) -> str:
        return f"<UserConfiguration(user_id={self.user_id}, type='{self.config_type}')>"


class PlatformConnection(Base):
    """User platform connections (MT5/Crypto)."""

    __tablename__ = "platform_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=False)
    platform_type = Column(Enum(PlatformType), nullable=False)
    connection_name = Column(String(100), nullable=False)  # User-defined name
    api_key = Column(
        String(255), nullable=False
    )  # For MT5: EA API key, For Crypto: API key
    api_secret = Column(String(255), nullable=True)  # Only for crypto platforms
    server_endpoint = Column(String(255), nullable=True)  # Custom server endpoint
    is_active = Column(Boolean, default=True, nullable=False)
    last_connected = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("TelegramUser", back_populates="platform_connections")

    def __repr__(self) -> str:
        return f"<PlatformConnection(user_id={self.user_id}, platform='{self.platform_type.value}')>"


class SignalSubscription(Base):
    """User signal subscriptions for specific symbols."""

    __tablename__ = "signal_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("telegram_users.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    min_confidence = Column(
        Integer, default=60, nullable=False
    )  # Minimum confidence threshold
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("TelegramUser", back_populates="signal_subscriptions")

    def __repr__(self) -> str:
        return f"<SignalSubscription(user_id={self.user_id}, symbol='{self.symbol}')>"


class ServerConfiguration(Base):
    """Server-wide configuration settings (admin only)."""

    __tablename__ = "server_configurations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False, index=True)
    config_value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ServerConfiguration(key='{self.config_key}')>"
