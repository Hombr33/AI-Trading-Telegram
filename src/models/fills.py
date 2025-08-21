"""
Fill model for order fills.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Fill(Base):
    """Fill model for order fills."""
    
    __tablename__ = "fills"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    fill_id = Column(String(50), unique=True, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False)
    volume = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fill_time = Column(String(50), nullable=False)  # ISO8601 string
    commission = Column(Float, nullable=True)
    swap = Column(Float, nullable=True)
    mt_ticket = Column(String(50), nullable=True)  # MetaTrader ticket number
    fill_data = Column(JSON, nullable=True)  # Additional fill data
    
    # Relationships
    order = relationship("Order", back_populates="fills")
    instrument = relationship("Instrument")
    
    def __repr__(self) -> str:
        return f"<Fill(fill_id='{self.fill_id}', volume={self.volume}, price={self.price})>"