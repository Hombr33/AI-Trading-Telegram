"""
Webhook model for webhook management.
"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Webhook(Base):
    """Webhook model for webhook management."""

    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    events = Column(Text, nullable=False)  # Comma-separated event types
    headers = Column(JSON, nullable=True)  # Custom headers
    is_active = Column(Boolean, default=True, nullable=False)
    last_triggered = Column(String(50), nullable=True)  # ISO8601 string
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    webhook_data = Column(JSON, nullable=True)  # Additional webhook data

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Webhook(webhook_id='{self.webhook_id}', name='{self.name}', url='{self.url}')>"
