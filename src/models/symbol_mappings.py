"""Symbol mappings model."""

from sqlalchemy import Column, String
from .base import Base


class SymbolMapping(Base):
    """Model for storing symbol mappings between standard and broker symbols."""

    __tablename__ = "symbol_mappings"

    standard_symbol = Column(String, primary_key=True)
    broker_name = Column(String, primary_key=True)
    broker_symbol = Column(String, nullable=False)
    description = Column(String, nullable=True)

    def __repr__(self):
        return f"<SymbolMapping(standard={self.standard_symbol}, broker={self.broker_symbol}, broker_name={self.broker_name})>"
