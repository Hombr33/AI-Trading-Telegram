"""
Audit model for audit logging.
"""

from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class Audit(Base):
    """Audit model for audit logging."""

    __tablename__ = "audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    audit_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)  # USER, TRADE, SIGNAL, etc.
    resource_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_data = Column(JSON, nullable=True)  # Request data
    response_data = Column(JSON, nullable=True)  # Response data
    status = Column(String(20), nullable=False)  # SUCCESS, FAILURE, ERROR
    error_message = Column(Text, nullable=True)
    audit_data = Column(JSON, nullable=True)  # Additional audit data

    # Relationships
    user = relationship("User")

    def __repr__(self) -> str:
        return f"<Audit(audit_id='{self.audit_id}', action='{self.action}', resource_type='{self.resource_type}')>"
