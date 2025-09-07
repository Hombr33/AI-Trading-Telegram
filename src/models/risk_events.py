"""
RiskEvent model for risk management events.
"""

from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class RiskEvent(Base):
    """RiskEvent model for risk management events."""

    __tablename__ = "risk_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(50), unique=True, nullable=False, index=True)
    event_type = Column(
        String(50), nullable=False
    )  # DRAWDOWN_WARNING, CORRELATION_BREACH, etc.
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    description = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=True)
    threshold_value = Column(Float, nullable=True)
    actual_value = Column(Float, nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(String(50), nullable=True)  # ISO8601 string
    resolution_notes = Column(Text, nullable=True)
    event_data = Column(JSON, nullable=True)  # Additional event data

    # Relationships
    user = relationship("User")
    trade = relationship("Trade")
    position = relationship("Position")

    def __repr__(self) -> str:
        return f"<RiskEvent(event_id='{self.event_id}', type='{self.event_type}', severity='{self.severity}')>"
