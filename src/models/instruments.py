"""
Instrument model for trading instruments.
"""

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Instrument(Base):
    """Instrument model for trading instruments."""

    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    type = Column(String(20), nullable=False)  # FOREX, CRYPTO, STOCK, COMMODITY
    base_currency = Column(String(10), nullable=True)
    quote_currency = Column(String(10), nullable=True)
    pip_value = Column(Float, nullable=True)
    point_value = Column(Float, nullable=True)
    min_lot_size = Column(Float, nullable=True)
    max_lot_size = Column(Float, nullable=True)
    lot_step = Column(Float, nullable=True)
    spread_avg = Column(Float, nullable=True)
    volatility_avg = Column(Float, nullable=True)
    trading_hours = Column(String, nullable=True)  # Trading hours configuration
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    notes = Column(String, nullable=True)

    # Relationships
    signals = relationship("Signal", back_populates="instrument")
    orders = relationship("Order", back_populates="instrument")
    trades = relationship("Trade", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")

    def __repr__(self) -> str:
        return f"<Instrument(symbol='{self.symbol}', type='{self.type}', name='{self.name}')>"
