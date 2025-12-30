"""Transaction-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator


class MintRequest(BaseModel):
    """Schema for minting new value to an account."""
    
    account_id: str = Field(..., description="Target account to mint value to")
    amount: int = Field(
        ...,
        gt=0,
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


class TransferRequest(BaseModel):
    """Schema for transferring value between accounts."""
    
    from_account_id: str = Field(..., description="Source account ID")
    to_account_id: str = Field(..., description="Destination account ID")
    amount: int = Field(
        ...,
        gt=0,
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
