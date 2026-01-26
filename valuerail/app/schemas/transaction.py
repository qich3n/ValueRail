"""Transaction-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

# Maximum transaction amount: $999,999,999.99 (in cents)
MAX_TRANSACTION_AMOUNT = 99_999_999_999


class MintRequest(BaseModel):
    """Schema for minting new value to an account."""
    
    account_id: str = Field(..., description="Target account to mint value to")
    amount: int = Field(
        ...,
        gt=0,
        le=MAX_TRANSACTION_AMOUNT,
        description="Amount to mint in smallest units (must be positive)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description of the mint operation"
    )
    idempotency_key: Optional[str] = Field(
        None,
        max_length=255,
        description="Unique key to ensure idempotent operation"
    )
    
    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize description by removing control characters."""
        if v is None:
            return v
        v = v.strip()
        # Remove control characters but preserve newlines and tabs
        v = "".join(c for c in v if ord(c) >= 32 or c in "\n\t")
        return v if v else None


class TransferRequest(BaseModel):
    """Schema for transferring value between accounts."""
    
    from_account_id: str = Field(..., description="Source account ID")
    to_account_id: str = Field(..., description="Destination account ID")
    amount: int = Field(
        ...,
        gt=0,
        le=MAX_TRANSACTION_AMOUNT,
        description="Amount to transfer in smallest units (must be positive)"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional description of the transfer"
    )
    idempotency_key: Optional[str] = Field(
        None,
        max_length=255,
        description="Unique key to ensure idempotent operation"
    )
    
    @field_validator("to_account_id")
    @classmethod
    def accounts_must_differ(cls, v, info):
        """Ensure source and destination accounts are different."""
        if "from_account_id" in info.data and v == info.data["from_account_id"]:
            raise ValueError("Cannot transfer to the same account")
        return v
    
    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v):
        """Sanitize description by removing control characters."""
        if v is None:
            return v
        v = v.strip()
        # Remove control characters but preserve newlines and tabs
        v = "".join(c for c in v if ord(c) >= 32 or c in "\n\t")
        return v if v else None


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    
    id: str = Field(..., description="Unique transaction identifier")
    type: str = Field(..., description="Transaction type (MINT or TRANSFER)")
    from_account_id: Optional[str] = Field(
        None,
        description="Source account ID (null for MINT)"
    )
    to_account_id: str = Field(..., description="Destination account ID")
    amount: int = Field(..., description="Transaction amount")
    description: Optional[str] = Field(None, description="Transaction description")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key if provided")
    created_at: datetime = Field(..., description="Transaction timestamp")
    
    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Schema for listing transactions."""
    
    transactions: List[TransactionResponse]
    total: int = Field(..., description="Total number of transactions")
