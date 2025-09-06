"""
Signal model for trading signals.
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Signal(Base):
    """Signal model for trading signals."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    bias = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    confidence = Column(Integer, nullable=False)  # 0-100 confidence score
    timeframe = Column(String(10), nullable=False)  # Single timeframe
    analysis_data = Column(JSON, nullable=True)  # Full analysis data
    setups = Column(JSON, nullable=False)  # Array of setup configurations
    risk_parameters = Column(JSON, nullable=True)  # Risk management parameters
    management_rules = Column(JSON, nullable=True)  # Position management rules
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(String(50), nullable=True)  # Expiration timestamp
    source = Column(String(50), nullable=False)  # Signal source
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)
    notes = Column(String, nullable=True)

    # Relationships
    instrument = relationship("Instrument", back_populates="signals")
    orders = relationship("Order", back_populates="signal")
    trades = relationship("Trade", back_populates="signal")

    @property
    def symbol(self) -> str:
        """Get symbol from instrument relationship."""
        return self.instrument.symbol if self.instrument else "UNKNOWN"

    def __repr__(self) -> str:
        return f"<Signal(signal_id='{self.signal_id}', instrument_id={self.instrument_id}, bias='{self.bias}', confidence={self.confidence})>"
