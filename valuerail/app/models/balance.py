"""Balance model."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class Balance(Base):
    """
    Balance tracks the current value held by an account.
    
    The amount is stored in the smallest unit (e.g., cents for dollars)
    to avoid floating-point precision issues.
    
    Constraints:
    - Balance cannot be negative (enforced at database level)
    - Each account has exactly one balance record
    """
    
    __tablename__ = "balances"
    
    account_id = Column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        primary_key=True
    )
    amount = Column(Integer, nullable=False, default=0)
    version = Column(Integer, nullable=False, default=1)  # For optimistic locking
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    # Ensure balance is never negative
    __table_args__ = (
        CheckConstraint("amount >= 0", name="balance_non_negative"),
    )
    
    # Relationships
    account = relationship("Account", back_populates="balance")
    
    def __repr__(self):
        return f"<Balance(account_id={self.account_id}, amount={self.amount})>"
