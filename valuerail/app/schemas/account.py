"""Account-related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field


class AccountCreate(BaseModel):
    """Schema for creating a new account."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the account holder"
    )


class AccountResponse(BaseModel):
    """Schema for account response."""
    
    id: str = Field(..., description="Unique account identifier")
    name: str = Field(..., description="Name of the account holder")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = {"from_attributes": True}


class BalanceResponse(BaseModel):
    """Schema for balance response."""
    
    amount: int = Field(..., description="Current balance in smallest units (e.g., cents)")
    updated_at: datetime = Field(..., description="Last balance update timestamp")
    
    model_config = {"from_attributes": True}


class AccountWithBalance(BaseModel):
    """Schema for account with balance details."""
    
    id: str = Field(..., description="Unique account identifier")
    name: str = Field(..., description="Name of the account holder")
    balance: int = Field(..., description="Current balance in smallest units")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    model_config = {"from_attributes": True}
