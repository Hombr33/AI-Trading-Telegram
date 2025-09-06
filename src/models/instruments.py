"""
Instrument model for trading instruments.
"""

from sqlalchemy import JSON, Boolean, Column, Float, Integer, String, Text
from sqlalchemy.orm import relationship

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
    min_lot = Column(Float, nullable=True)
    max_lot = Column(Float, nullable=True)
    lot_step = Column(Float, nullable=True)
    spread = Column(Float, nullable=True)
    swap_long = Column(Float, nullable=True)
    swap_short = Column(Float, nullable=True)
    trading_hours = Column(JSON, nullable=True)  # Trading hours configuration
    is_active = Column(Boolean, default=True, nullable=False)
    instrument_metadata = Column(JSON, nullable=True)  # Additional instrument metadata

    # Relationships
    orders = relationship("Order", back_populates="instrument")
    trades = relationship("Trade", back_populates="instrument")
    positions = relationship("Position", back_populates="instrument")

    def __repr__(self) -> str:
        return f"<Instrument(symbol='{self.symbol}', type='{self.type}', name='{self.name}')>"
