"""
User model for authentication and authorization.
"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    """User model for system authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    api_keys = relationship(
        "APIKey", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    trades = relationship("Trade", back_populates="user", cascade="all, delete-orphan")
    journals = relationship(
        "Journal", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}')>"
