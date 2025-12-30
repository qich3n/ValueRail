"""Transaction model - immutable ledger."""

import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Index

from app.database import Base


def generate_uuid():
    """Generate a new UUID string."""
    return str(uuid.uuid4())


class TransactionType(enum.Enum):
    """Types of transactions in the ledger."""
    MINT = "MINT"
    TRANSFER = "TRANSFER"


class Transaction(Base):
    """
    Transaction represents an immutable record in the ledger.
    
    This is an append-only table - records are never updated or deleted.
    Each transaction captures:
    - The type of operation (mint or transfer)
    - The source and destination accounts
    - The amount transferred
    - A reference to the idempotency key (if applicable)
    - Timestamp of when the transaction occurred
    
    For MINT transactions:
    - from_account_id is NULL (value created from nothing)
    - to_account_id is the recipient
    
    For TRANSFER transactions:
    - from_account_id is the sender
    - to_account_id is the recipient
    """
    
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(Enum(TransactionType), nullable=False)
    from_account_id = Column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=True  # NULL for MINT transactions
    )
    to_account_id = Column(
        String(36),
        ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False
    )
    amount = Column(Integer, nullable=False)
    idempotency_key = Column(String(255), nullable=True, index=True)
    description = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )
    
    __table_args__ = (
        Index("idx_transactions_from_account", "from_account_id"),
        Index("idx_transactions_to_account", "to_account_id"),
    )
    
    def __repr__(self):
        return (
            f"<Transaction(id={self.id}, type={self.type.value}, "
            f"amount={self.amount})>"
        )
