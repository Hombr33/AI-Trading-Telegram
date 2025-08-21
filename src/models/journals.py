"""
Journal model for trade journaling.
"""

from sqlalchemy import Column, String, Boolean, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import Base


class Journal(Base):
    """Journal model for trade journaling."""
    
    __tablename__ = "journals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    journal_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=True)
    entry_type = Column(String(50), nullable=False)  # TRADE_ENTRY, TRADE_EXIT, SIGNAL_ANALYSIS, etc.
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    analysis_data = Column(JSON, nullable=True)  # Analysis results
    sentiment_score = Column(Float, nullable=True)  # -1 to 1
    confidence_score = Column(Float, nullable=True)  # 0 to 1
    tags = Column(Text, nullable=True)  # Comma-separated tags
    is_public = Column(Boolean, default=False, nullable=False)
    journal_data = Column(JSON, nullable=True)  # Additional journal data
    
    # Relationships
    user = relationship("User", back_populates="journals")
    trade = relationship("Trade")
    signal = relationship("Signal")
    
    def __repr__(self) -> str:
        return f"<Journal(journal_id='{self.journal_id}', title='{self.title}', entry_type='{self.entry_type}')>"