"""
Position model for open positions.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Position(Base):
    """Position model for open positions."""

    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    position_id = Column(String(50), unique=True, nullable=False, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    direction = Column(String(10), nullable=False)  # BUY, SELL
    volume = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    open_time = Column(String(50), nullable=False)  # ISO8601 string
    unrealized_pnl = Column(Float, nullable=True)
    swap = Column(Float, nullable=True)
    commission = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    mt_ticket = Column(String(50), nullable=True)  # MetaTrader ticket number
    position_data = Column(JSON, nullable=True)  # Additional position data

    # Relationships
    trade = relationship("Trade", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Position(position_id='{self.position_id}', direction='{self.direction}', volume={self.volume})>"
