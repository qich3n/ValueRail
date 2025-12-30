"""Account model."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class Account(Base):
    """
    Account represents a participant in the ledger system.
    
    Each account has a unique identifier and can hold digital value.
    """
    
    __tablename__ = "accounts"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Relationships
    balance = relationship("Balance", back_populates="account", uselist=False)
    
    def __repr__(self):
        return f"<Account(id={self.id}, name={self.name})>"
