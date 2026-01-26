"""Account-related Pydantic schemas."""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class AccountCreate(BaseModel):
    """Schema for creating a new account."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the account holder"
    )
    
    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v):
        """Sanitize account name by stripping whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty or whitespace only")
        # Basic sanitization: remove control characters
        v = "".join(c for c in v if ord(c) >= 32 or c in "\n\t")
        return v


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
