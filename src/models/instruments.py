"""
Instrument model for trading instruments.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text
from sqlalchemy.orm import relationship
from .base import Base


class Instrument(Base):
    """Instrument model for trading instruments."""
    
    __tablename__ = "instruments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # FOREX, CRYPTO, STOCK, etc.
    base_currency = Column(String(10), nullable=True)
    quote_currency = Column(String(10), nullable=True)
    pip_value = Column(Float, nullable=True)
    point_value = Column(Float, nullable=True)
    min_lot_size = Column(Float, nullable=True)
    max_lot_size = Column(Float, nullable=True)
    lot_step = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    trading_hours = Column(Text, nullable=True)  # JSON string of trading hours
    spread_avg = Column(Float, nullable=True)
    volatility_avg = Column(Float, nullable=True)
    
    # Relationships
    signals = relationship("Signal", back_populates="instrument", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="instrument", cascade="all, delete-orphan")
    trades = relationship("Trade", back_populates="instrument", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="instrument", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Instrument(symbol='{self.symbol}', type='{self.type}')>"