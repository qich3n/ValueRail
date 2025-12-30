"""Idempotency key model for ensuring exactly-once semantics."""

from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text

from app.database import Base


class IdempotencyKey(Base):
    """
    IdempotencyKey ensures that operations with the same key are not duplicated.
    
    When a client sends a request with an idempotency key:
    1. If the key doesn't exist, process the request and store the result
    2. If the key exists, return the stored result without reprocessing
    
    This prevents double-spending in case of network retries or client errors.
    
    Keys are stored with:
    - The unique key provided by the client
    - The response that was generated
    - Timestamp for potential cleanup of old keys
    """
    
    __tablename__ = "idempotency_keys"
    
    key = Column(String(255), primary_key=True)
    response = Column(Text, nullable=False)  # JSON serialized response
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def __repr__(self):
        return f"<IdempotencyKey(key={self.key})>"
