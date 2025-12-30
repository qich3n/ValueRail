"""Common Pydantic schemas."""

from typing import Optional, Any
from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Any] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Schema for generic success responses."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
