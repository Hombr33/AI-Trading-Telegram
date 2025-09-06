"""
Alert model for system alerts.
"""

from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Alert(Base):
    """Alert model for system alerts."""

    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    alert_type = Column(
        String(50), nullable=False
    )  # TRADE_ALERT, RISK_ALERT, SYSTEM_ALERT, etc.
    severity = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    read_at = Column(String(50), nullable=True)  # ISO8601 string
    delivery_method = Column(
        String(50), nullable=False
    )  # TELEGRAM, EMAIL, WEBHOOK, etc.
    delivery_status = Column(
        String(20), nullable=False, default="PENDING"
    )  # PENDING, SENT, FAILED
    delivery_data = Column(JSON, nullable=True)  # Delivery details
    alert_data = Column(JSON, nullable=True)  # Additional alert data

    # Relationships
    user = relationship("User")
    trade = relationship("Trade")
    signal = relationship("Signal")

    def __repr__(self) -> str:
        return f"<Alert(alert_id='{self.alert_id}', type='{self.alert_type}', severity='{self.severity}')>"
