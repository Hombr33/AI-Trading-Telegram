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
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


class Signal(Base):
    """Signal model for trading signals."""

    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    bias = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    timeframes = Column(JSON, nullable=True)  # Array of timeframes analyzed
    setups = Column(JSON, nullable=False)  # Array of setup configurations
    confidence = Column(Float, nullable=False)  # 0-100 confidence score
    analysis_data = Column(JSON, nullable=True)  # Full analysis data
    status = Column(
        String(20), nullable=False, default="ACTIVE"
    )  # ACTIVE, EXECUTED, EXPIRED, CANCELLED
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    orders = relationship("Order", back_populates="signal")
    trades = relationship("Trade", back_populates="signal")

    def __repr__(self) -> str:
        return f"<Signal(signal_id='{self.signal_id}', symbol='{self.symbol}', bias='{self.bias}', confidence={self.confidence})>"
