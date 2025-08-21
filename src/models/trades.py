"""
Trade model for completed trades.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Trade(Base):
    """Trade model for completed trades."""
    
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    direction = Column(String(10), nullable=False)  # BUY, SELL
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    open_time = Column(String(50), nullable=False)  # ISO8601 string
    close_time = Column(String(50), nullable=True)  # ISO8601 string
    profit_loss = Column(Float, nullable=True)
    swap = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN, CLOSED, PARTIAL
    mt_ticket = Column(String(50), nullable=True)  # MetaTrader ticket number
    trade_data = Column(JSON, nullable=True)  # Additional trade data
    
    # Relationships
    order = relationship("Order")
    instrument = relationship("Instrument", back_populates="trades")
    user = relationship("User", back_populates="trades")
    signal = relationship("Signal")
    positions = relationship("Position", back_populates="trade", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Trade(trade_id='{self.trade_id}', direction='{self.direction}', status='{self.status}')>"