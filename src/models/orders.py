"""
Order model for trading orders.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Order(Base):
    """Order model for trading orders."""

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(20), nullable=False)  # OPEN, CLOSE, MODIFY
    order_type = Column(
        String(20), nullable=False
    )  # BUY, SELL, BUYLIMIT, SELLLIMIT, BUYSTOP, SELLSTOP
    volume = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    magic_number = Column(Integer, nullable=True)
    comment = Column(Text, nullable=True)
    status = Column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, FILLED, PARTIAL, REJECTED, CANCELLED
    mt_ticket = Column(String(50), nullable=True)  # MetaTrader ticket number
    execution_data = Column(JSON, nullable=True)  # Execution details

    # Relationships
    signal = relationship("Signal", back_populates="orders")
    instrument = relationship("Instrument", back_populates="orders")
    user = relationship("User")
    fills = relationship("Fill", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Order(order_id='{self.order_id}', action='{self.action}', type='{self.order_type}', status='{self.status}')>"
