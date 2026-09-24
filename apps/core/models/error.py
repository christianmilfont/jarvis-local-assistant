from typing import Optional

from pydantic import BaseModel, Field


class ErrorDetails(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    reason: Optional[str] = None
    provider: Optional[str] = None
    timeout_seconds: Optional[int] = None
    limit: Optional[str] = None
    retry_after: Optional[int] = None


class ErrorInfo(BaseModel):
    """Error information containing code, message, and optional details."""
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[ErrorDetails] = None


class ErrorResponse(BaseModel):
    """Standard error response model."""
    status: str = "error"
    error: ErrorInfo


class ValidationError(Exception):
    """Raised when input validation fails."""
    pass


class ProviderError(Exception):
    """Raised when LLM provider fails."""
    pass


class ProviderTimeoutError(Exception):
    """Raised when LLM provider times out."""
    pass
