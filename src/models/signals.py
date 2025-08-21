"""
Signal model for AI trading signals.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Signal(Base):
    """Signal model for AI trading signals."""
    
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(50), unique=True, nullable=False, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    bias = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    confidence = Column(Integer, nullable=False)  # 0-100
    timeframe = Column(String(10), nullable=False)  # H4, H1, M15, M5, M1
    analysis_data = Column(JSON, nullable=True)  # Full analysis data
    setups = Column(JSON, nullable=False)  # Trading setups array
    risk_parameters = Column(JSON, nullable=True)  # Risk management parameters
    management_rules = Column(JSON, nullable=True)  # Position management rules
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(String(50), nullable=True)  # ISO8601 string
    source = Column(String(50), nullable=False)  # AI_ANALYSIS, MANUAL, etc.
    
    # Relationships
    instrument = relationship("Instrument", back_populates="signals")
    orders = relationship("Order", back_populates="signal", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Signal(signal_id='{self.signal_id}', symbol='{self.instrument.symbol if self.instrument else 'N/A'}', bias='{self.bias}')>"