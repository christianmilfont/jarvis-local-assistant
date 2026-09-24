import uuid
from datetime import UTC, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MessageMetadata(BaseModel):
    """Optional metadata for message requests."""
    source: Optional[str] = None
    user_id: Optional[str] = None


class MessageRequest(BaseModel):
    """Request model for message submission."""
    message: str = Field(..., min_length=1, max_length=1000)
    timestamp: Optional[datetime] = None
    metadata: Optional[MessageMetadata] = None

    @field_validator('message')
    @classmethod
    def validate_message_content(cls, v: str) -> str:
        """Validate that message is not whitespace only."""
        if not v.strip():
            raise ValueError("Message cannot contain only whitespace")
        return v

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate timestamp format if provided."""
        if v is not None and not isinstance(v, datetime):
            raise ValueError("Invalid timestamp format")
        return v

class MessageResponseData(BaseModel):
    """Data portion of successful message response."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response: str = Field(..., max_length=5000)
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MessageResponse(BaseModel):
    """Success response model for message processing."""
    status: str = "success"
    data: MessageResponseData
