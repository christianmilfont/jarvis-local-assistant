# Text Interaction Implementation Plan

**Feature ID:** 001-text-interaction  
**Feature Name:** Text Interaction  
**Status:** Draft  
**Version:** 1.0  
**Created:** 2025-09-24  
**Specification:** specs/001-text-interaction/spec.md v1.1

---

## 1. Proposed Project Structure

The implementation will follow a modular monolith architecture as specified in the Constitution (Principle III - Simplicity). The structure supports clear separation of concerns while maintaining simplicity.

```
jarvis-local-assistant/
├── apps/
│   ├── core/                          # JARVIS Core - Business logic
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI application entry point
│   │   ├── config.py                  # Configuration management
│   │   ├── models/                    # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── message.py             # Message request/response models
│   │   │   └── error.py               # Error response models
│   │   ├── providers/                 # LLM provider implementations
│   │   │   ├── __init__.py
│   │   │   ├── base.py                # LLM provider interface
│   │   │   └── mock.py                # MockLLMProvider implementation
│   │   ├── services/                  # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── message_service.py     # Message processing service
│   │   │   └── validation_service.py  # Input validation service
│   │   ├── api/                       # FastAPI routes
│   │   │   ├── __init__.py
│   │   │   └── messages.py            # Message endpoints
│   │   └── middleware/                # Custom middleware
│   │       ├── __init__.py
│   │       ├── logging.py             # Structured logging middleware
│   │       └── rate_limit.py          # Rate limiting middleware
│   ├── ui/                            # React UI (placeholder for future)
│   │   └── (empty - out of scope for this feature)
│   └── voice/                         # Voice processing (placeholder for future)
│       └── (empty - out of scope for this feature)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Pytest configuration and fixtures
│   ├── unit/                          # Unit tests
│   │   ├── __init__.py
│   │   ├── test_validation.py         # Validation logic tests
│   │   ├── test_providers.py          # Provider interface tests
│   │   └── test_models.py             # Model validation tests
│   ├── integration/                   # Integration tests
│   │   ├── __init__.py
│   │   ├── test_message_flow.py       # End-to-end message flow tests
│   │   └── test_api_contract.py       # API contract compliance tests
│   └── contract/                      # Contract tests
│       ├── __init__.py
│       └── test_schemas.py            # Schema validation tests
├── infrastructure/
│   └── docker/
│       ├── Dockerfile                 # Application container
│       └── docker-compose.yml        # Local development environment
├── requirements.txt                   # Python dependencies
├── pyproject.toml                     # Project configuration
├── pytest.ini                         # Pytest configuration
├── .ruff.toml                         # Ruff linting configuration
├── .env.example                       # Environment variables template
└── README.md                          # Updated with feature instructions
```

**Rationale:** This structure follows the modular monolith approach specified in Principle III, providing clear separation between core business logic, providers, services, and API layers while maintaining simplicity.

---

## 2. Backend Architecture

### 2.1 Overall Architecture

The backend uses a layered architecture within a modular monolith:

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (apps/core/main.py)                    │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         API Layer                       │
│  (apps/core/api/messages.py)            │
│  - Request validation                   │
│  - Response formatting                  │
│  - Error handling                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Service Layer                    │
│  (apps/core/services/)                  │
│  - Message processing logic             │
│  - Input validation                     │
│  - Business rules                       │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│         Provider Layer                   │
│  (apps/core/providers/)                 │
│  - LLM provider interface               │
│  - MockLLMProvider implementation       │
└─────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

**FastAPI Application Layer (`apps/core/main.py`)**
- Application initialization and configuration
- Middleware registration (logging, rate limiting)
- Route registration
- Health endpoint (`/health`)
- Startup/shutdown event handlers

**API Layer (`apps/core/api/messages.py`)**
- HTTP endpoint implementation (`POST /api/messages`)
- Request/response model validation using Pydantic
- HTTP status code management
- Error response formatting

**Service Layer (`apps/core/services/`)**
- **MessageService:** Orchestrates message processing workflow
- **ValidationService:** Implements input validation rules
- Business logic separation from HTTP concerns

**Provider Layer (`apps/core/providers/`)**
- **LLMProvider (Abstract Base Class):** Interface definition
- **MockLLMProvider:** Mock implementation for development/testing
- Provider instantiation and configuration

**Middleware Layer (`apps/core/middleware/`)**
- **LoggingMiddleware:** Structured JSON logging with request IDs
- **RateLimitMiddleware:** Simple in-memory rate limiting

### 2.3 Data Flow

```
User Request
    ↓
FastAPI Route Handler
    ↓
Pydantic Model Validation
    ↓
ValidationService (business rules)
    ↓
MessageService (orchestration)
    ↓
LLMProvider.generate_response()
    ↓
Response Formatting
    ↓
HTTP Response
```

**Constitution Alignment:** This architecture follows Principle III (Simplicity) by using a straightforward layered approach within a monolith, and Principle IV (Hardware Abstraction) by isolating external dependencies behind the provider interface.

---

## 3. Core Interfaces

### 3.1 LLM Provider Interface

```python
# apps/core/providers/base.py
from abc import ABC, abstractmethod
from typing import Optional

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    async def generate_response(self, message: str) -> str:
        """
        Generate a response for the given message.
        
        Args:
            message: The user's message
            
        Returns:
            The generated response text
            
        Raises:
            ProviderError: If the provider fails to generate a response
            ProviderTimeoutError: If the provider times out
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is operational.
        
        Returns:
            True if the provider is healthy, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider implementation."""
        pass
```

**Rationale:** This interface provides the abstraction specified in FR-004, enabling provider switching without modifying business logic (FR-004 acceptance criteria).

### 3.2 Service Interfaces

```python
# apps/core/services/message_service.py
from typing import Dict, Any
from apps.core.providers.base import LLMProvider
from apps.core.models.message import MessageRequest, MessageResponse

class MessageService:
    """Service for processing messages through JARVIS Core."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
    
    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """
        Process a message through the JARVIS Core workflow.
        
        Args:
            request: The validated message request
            
        Returns:
            MessageResponse with the generated response
            
        Raises:
            ValidationError: If message validation fails
            ProviderError: If LLM provider fails
        """
        pass
```

```python
# apps/core/services/validation_service.py
from apps.core.models.message import MessageRequest

class ValidationService:
    """Service for validating message input."""
    
    def validate_message(self, request: MessageRequest) -> tuple[bool, Optional[str]]:
        """
        Validate a message request against business rules.
        
        Args:
            request: The message request to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
```

**Rationale:** Service interfaces separate business logic from HTTP concerns, supporting Principle III (Simplicity) and enabling easier testing (Principle VI - Testability).

---

## 4. MockLLMProvider Design

### 4.1 Implementation Approach

```python
# apps/core/providers/mock.py
import asyncio
import os
from typing import Dict
from apps.core.providers.base import LLMProvider
from apps.core.models.error import ProviderError, ProviderTimeoutError

class MockLLMProvider(LLMProvider):
    """Mock LLM provider for development and testing."""
    
    # Predefined response templates based on message content
    RESPONSE_TEMPLATES = {
        "hello": "Hello! I'm JARVIS, your local AI assistant. How can I help you today?",
        "hi": "Hi there! I'm JARVIS. What would you like to know?",
        "help": "I can help you with various tasks. What do you need assistance with?",
        "default": "I understand your message. This is a mock response for testing purposes."
    }
    
    def __init__(self):
        self._delay_ms = int(os.getenv("MOCK_LLM_DELAY_MS", "1000"))
        self._simulate_errors = os.getenv("MOCK_LLM_SIMULATE_ERRORS", "false").lower() == "true"
    
    @property
    def provider_name(self) -> str:
        return "MockLLMProvider"
    
    async def generate_response(self, message: str) -> str:
        """Generate a mock response based on message content."""
        # Simulate processing delay
        await asyncio.sleep(self._delay_ms / 1000.0)
        
        # Simulate errors if configured
        if self._simulate_errors:
            raise ProviderError("Simulated provider error for testing")
        
        # Generate deterministic response based on message content
        message_lower = message.lower().strip()
        
        for key, template in self.RESPONSE_TEMPLATES.items():
            if key in message_lower:
                return template
        
        return self.RESPONSE_TEMPLATES["default"]
    
    async def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True
```

### 4.2 Configuration

Environment variables in `.env.example`:

```bash
# LLM Provider Configuration
LLM_PROVIDER=mock

# Mock LLM Provider Configuration
MOCK_LLM_DELAY_MS=1000
MOCK_LLM_SIMULATE_ERRORS=false
```

### 4.3 Provider Factory

```python
# apps/core/providers/__init__.py
from apps.core.providers.base import LLMProvider
from apps.core.providers.mock import MockLLMProvider
import os

def create_provider() -> LLMProvider:
    """Factory function to create the configured LLM provider."""
    provider_type = os.getenv("LLM_PROVIDER", "mock")
    
    if provider_type == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
```

**Rationale:** This design satisfies FR-005 (MockLLMProvider requirements) and supports the approved decision for predefined response templates. It's configurable via environment variables (Principle VII - Security) and deterministic for testing (FR-010).

---

## 5. API Contract

### 5.1 Endpoint Specification

**POST /api/messages**

**Request Headers:**
```
Content-Type: application/json
```

**Request Body:**
```json
{
  "message": "string (required, 1-1000 characters)",
  "timestamp": "ISO 8601 datetime (optional)",
  "metadata": {
    "source": "string (optional)",
    "user_id": "string (optional)"
  }
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "data": {
    "message_id": "uuid-string",
    "response": "string (max 5000 characters)",
    "processing_time_ms": 1234,
    "timestamp": "2025-09-24T12:00:00Z"
  }
}
```

**Validation Error Response (400 Bad Request):**
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Message cannot be empty",
    "details": {
      "field": "message",
      "reason": "empty_message"
    }
  }
}
```

**Provider Error Response (503 Service Unavailable):**
```json
{
  "status": "error",
  "error": {
    "code": "PROVIDER_ERROR",
    "message": "Unable to generate response - provider unavailable",
    "details": {
      "provider": "MockLLMProvider",
      "reason": "simulated_error"
    }
  }
}
```

**Provider Timeout Response (504 Gateway Timeout):**
```json
{
  "status": "error",
  "error": {
    "code": "PROVIDER_TIMEOUT",
    "message": "Response generation timed out",
    "details": {
      "provider": "MockLLMProvider",
      "timeout_seconds": 30
    }
  }
}
```

**Rate Limit Error Response (429 Too Many Requests):**
```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests, please try again later",
    "details": {
      "limit": "10 requests per minute",
      "retry_after": 45
    }
  }
}
```

### 5.2 Health Endpoint

**GET /health**

**Response (200 OK):**
```json
{
  "status": "healthy",
  "provider": "MockLLMProvider",
  "provider_healthy": true,
  "timestamp": "2025-09-24T12:00:00Z"
}
```

**Rationale:** This API contract matches the specification exactly and supports all specified error scenarios (ES-001 through ES-008).

---

## 6. Request and Response Models

### 6.1 Pydantic Models

```python
# apps/core/models/message.py
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict
from datetime import datetime
import uuid

class MessageMetadata(BaseModel):
    """Optional metadata for message requests."""
    source: Optional[str] = None
    user_id: Optional[str] = None

class MessageRequest(BaseModel):
    """Request model for message submission."""
    message: str = Field(..., min_length=1, max_length=1000)
    timestamp: Optional[datetime] = None
    metadata: Optional[MessageMetadata] = None
    
    @validator('message')
    def validate_message_content(cls, v):
        """Validate that message is not whitespace only."""
        if not v.strip():
            raise ValueError("Message cannot contain only whitespace")
        return v
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Validate timestamp format if provided."""
        if v is not None and not isinstance(v, datetime):
            raise ValueError("Invalid timestamp format")
        return v

class MessageResponseData(BaseModel):
    """Data portion of successful message response."""
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    response: str = Field(..., max_length=5000)
    processing_time_ms: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class MessageResponse(BaseModel):
    """Success response model for message processing."""
    status: str = "success"
    data: MessageResponseData
```

### 6.2 Error Models

```python
# apps/core/models/error.py
from pydantic import BaseModel, Field
from typing import Optional, Dict

class ErrorDetails(BaseModel):
    """Detailed error information."""
    field: Optional[str] = None
    reason: str
    provider: Optional[str] = None
    timeout_seconds: Optional[int] = None
    limit: Optional[str] = None
    retry_after: Optional[int] = None

class ErrorResponse(BaseModel):
    """Standard error response model."""
    status: str = "error"
    error: ErrorDetails
    code: str = Field(..., description="Error code for programmatic handling")
    message: str = Field(..., description="Human-readable error message")

# Custom exceptions
class ValidationError(Exception):
    """Raised when input validation fails."""
    pass

class ProviderError(Exception):
    """Raised when LLM provider fails."""
    pass

class ProviderTimeoutError(Exception):
    """Raised when LLM provider times out."""
    pass
```

**Rationale:** Pydantic models provide automatic validation, type safety, and schema generation, supporting Principle V (Controlled Actions) and ensuring API contract compliance (AC-007).

---

## 7. Error Handling

### 7.1 Error Handling Strategy

**Validation Errors (FR-002, FR-007, ES-001-004, ES-007)**
- Pydantic model validation for schema validation
- ValidationService for business rule validation
- Return 400 Bad Request with VALIDATION_ERROR code
- Include field and reason in error details

**Provider Errors (FR-008, ES-005, ES-006, AC-004)**
- Catch ProviderError and ProviderTimeoutError exceptions
- Return 503 Service Unavailable for provider errors
- Return 504 Gateway Timeout for provider timeouts
- Include provider name and reason in error details
- System remains operational (error isolation)

**Rate Limiting (SC-003, ES-008)**
- In-memory rate limiting middleware
- Return 429 Too Many Requests when limit exceeded
- Include limit and retry_after in error details

**System Errors**
- Catch unexpected exceptions
- Return 500 Internal Server Error
- Log full error context for diagnosis
- Return generic error message to user

### 7.2 Error Handling Implementation

```python
# apps/core/api/messages.py
from fastapi import APIRouter, HTTPException, Request
from apps.core.models.message import MessageRequest, MessageResponse
from apps.core.models.error import ErrorResponse, ErrorDetails
from apps.core.services.message_service import MessageService
from apps.core.providers import create_provider
import time

router = APIRouter()
message_service = MessageService(create_provider())

@router.post("/api/messages", response_model=MessageResponse)
async def submit_message(request: Request, message_request: MessageRequest):
    """Submit a message for processing."""
    start_time = time.time()
    
    try:
        # Process message through service layer
        response = await message_service.process_message(message_request)
        processing_time = int((time.time() - start_time) * 1000)
        response.data.processing_time_ms = processing_time
        return response
        
    except ValidationError as e:
        # Validation errors - return 400
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
                "details": {"field": "message", "reason": "validation_failed"}
            }
        )
        
    except ProviderTimeoutError as e:
        # Provider timeout - return 504
        raise HTTPException(
            status_code=504,
            detail={
                "code": "PROVIDER_TIMEOUT",
                "message": "Response generation timed out",
                "details": {"provider": "MockLLMProvider", "timeout_seconds": 30}
            }
        )
        
    except ProviderError as e:
        # Provider error - return 503
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PROVIDER_ERROR",
                "message": "Unable to generate response - provider unavailable",
                "details": {"provider": "MockLLMProvider", "reason": str(e)}
            }
        )
        
    except Exception as e:
        # Unexpected error - return 500
        request_id = request.state.request_id if hasattr(request.state, 'request_id') else "unknown"
        # Log full error context
        logger.error(f"Unexpected error processing message {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"request_id": request_id}
            }
        )
```

**Rationale:** This error handling strategy supports all specified error scenarios, maintains system stability (FR-008), and provides sufficient context for diagnosis (OR-004, AC-008).

---

## 8. Testing Strategy

### 8.1 Testing Approach

The testing strategy follows Principle VI (Testability) and FR-010 (testability without external APIs). All tests use MockLLMProvider to ensure offline execution.

### 8.2 Unit Tests

**Target:** Individual components in isolation

**Test Files:**
- `tests/unit/test_validation.py` - Validation logic
- `tests/unit/test_providers.py` - Provider interface and mock implementation
- `tests/unit/test_models.py` - Pydantic model validation

**Example Test:**
```python
# tests/unit/test_validation.py
import pytest
from apps.core.services.validation_service import ValidationService
from apps.core.models.message import MessageRequest

def test_empty_message_validation():
    """Test that empty messages are rejected."""
    service = ValidationService()
    request = MessageRequest(message="")
    is_valid, error = service.validate_message(request)
    assert not is_valid
    assert "empty" in error.lower()

def test_message_too_long():
    """Test that messages exceeding 1000 characters are rejected."""
    service = ValidationService()
    long_message = "a" * 1001
    request = MessageRequest(message=long_message)
    is_valid, error = service.validate_message(request)
    assert not is_valid
    assert "length" in error.lower()
```

### 8.3 Integration Tests

**Target:** Component interactions and end-to-end flows

**Test Files:**
- `tests/integration/test_message_flow.py` - Complete message processing flow
- `tests/integration/test_api_contract.py` - API contract compliance

**Example Test:**
```python
# tests/integration/test_message_flow.py
import pytest
from httpx import AsyncClient
from apps.core.main import app

@pytest.mark.asyncio
async def test_complete_message_flow():
    """Test complete message flow from request to response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/messages",
            json={"message": "Hello JARVIS"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "response" in data["data"]
        assert data["data"]["processing_time_ms"] > 0
```

### 8.4 Contract Tests

**Target:** API schema compliance

**Test Files:**
- `tests/contract/test_schemas.py` - Request/response schema validation

**Example Test:**
```python
# tests/contract/test_schemas.py
import pytest
from apps.core.models.message import MessageRequest, MessageResponse
from pydantic import ValidationError

def test_message_request_schema_validation():
    """Test that message request schema validates correctly."""
    # Valid request
    valid_request = MessageRequest(message="Hello")
    assert valid_request.message == "Hello"
    
    # Invalid request - too long
    with pytest.raises(ValidationError):
        MessageRequest(message="a" * 1001)
```

### 8.5 Test Configuration

```python
# tests/conftest.py
import pytest
from apps.core.main import app
from apps.core.providers.mock import MockLLMProvider

@pytest.fixture
def mock_provider():
    """Fixture providing MockLLMProvider for tests."""
    return MockLLMProvider()

@pytest.fixture
def test_client():
    """Fixture providing test client for FastAPI app."""
    from httpx import AsyncClient
    return AsyncClient(app=app, base_url="http://test")

@pytest.fixture
def override_provider(monkeypatch):
    """Fixture to override provider for testing."""
    def _override(provider):
        monkeypatch.setattr("apps.core.services.message_service.message_service.llm_provider", provider)
    return _override
```

### 8.6 Test Execution

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --cov=apps/core
    --cov-report=term-missing
    --cov-report=html
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    contract: Contract tests
```

**Rationale:** This testing strategy ensures 80% code coverage (NFR-006, AC-006), supports offline execution (FR-010), and validates all acceptance criteria.

---

## 9. Logging Strategy

### 9.1 Structured Logging

**Format:** JSON structured logging for machine readability

**Log Levels:**
- INFO: Normal operations (message processing, health checks)
- WARNING: Rate limiting, minor issues
- ERROR: Provider errors, validation failures
- CRITICAL: System failures

**Log Fields:**
- timestamp: ISO 8601 format
- level: Log level (INFO, WARNING, ERROR, CRITICAL)
- request_id: Unique request identifier for tracing
- message: Log message
- context: Additional context (error codes, processing time, etc.)
- stack_trace: For errors only

### 9.2 Logging Implementation

```python
# apps/core/middleware/logging.py
import json
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging."""
    
    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Log request start
        self._log_request_start(request, request_id)
        
        try:
            response = await call_next(request)
            
            # Log request completion
            processing_time = (time.time() - start_time) * 1000
            self._log_request_complete(request, request_id, response.status_code, processing_time)
            
            return response
            
        except Exception as e:
            # Log error with full context
            processing_time = (time.time() - start_time) * 1000
            self._log_request_error(request, request_id, str(e), processing_time)
            raise
    
    def _log_request_start(self, request: Request, request_id: str):
        log_data = {
            "timestamp": time.time(),
            "level": "INFO",
            "request_id": request_id,
            "message": "Request started",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None
            }
        }
        logger.info(json.dumps(log_data))
    
    def _log_request_complete(self, request: Request, request_id: str, status_code: int, processing_time: float):
        log_data = {
            "timestamp": time.time(),
            "level": "INFO",
            "request_id": request_id,
            "message": "Request completed",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "processing_time_ms": processing_time
            }
        }
        logger.info(json.dumps(log_data))
    
    def _log_request_error(self, request: Request, request_id: str, error: str, processing_time: float):
        log_data = {
            "timestamp": time.time(),
            "level": "ERROR",
            "request_id": request_id,
            "message": "Request failed",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "error": error,
                "processing_time_ms": processing_time
            }
        }
        logger.error(json.dumps(log_data), exc_info=True)
```

### 9.3 Security Considerations

**Message Content Privacy (SC-002, AC-010):**
- Log only message metadata (message_id, timestamp, length)
- Never log message content in plain text
- Hash message content if needed for debugging

**Example:**
```python
# Instead of logging: "Processing message: 'Hello JARVIS'"
# Log: "Processing message: id='abc-123', length=12, timestamp='2025-09-24T12:00:00Z'"
```

**Rationale:** This logging strategy satisfies OR-001 (structured logging), OR-004 (error context), OR-005 (request tracing), and SC-002 (message privacy).

---

## 10. Dependencies

### 10.1 Python Dependencies

```txt
# requirements.txt
# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2

# Code Quality
ruff==0.1.6

# Utilities
python-dotenv==1.0.0
```

### 10.2 Development Dependencies

```txt
# requirements-dev.txt
# Add to requirements.txt for development
black==23.12.0
mypy==1.7.1
```

### 10.3 Configuration Files

**pyproject.toml:**
```toml
[project]
name = "jarvis-local-assistant"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.104.1",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.3",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "httpx>=0.25.2",
    "ruff>=0.1.6",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
```

**.ruff.toml:**
```toml
line-length = 100
target-version = "py312"
select = ["E", "F", "I", "N", "W"]
```

**pytest.ini:**
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --strict-markers --cov=apps/core --cov-report=term-missing --cov-report=html --cov-fail-under=80
markers = unit: Unit tests, integration: Integration tests, contract: Contract tests
```

**Rationale:** These dependencies support the approved technology stack (Python 3.12, FastAPI, pytest, Ruff) and enable local-first development without cloud dependencies.

---

## 11. Files to Create

### 11.1 Core Application Files

**Backend Structure:**
- `apps/core/__init__.py` - Package initialization
- `apps/core/main.py` - FastAPI application entry point
- `apps/core/config.py` - Configuration management
- `apps/core/models/__init__.py` - Models package initialization
- `apps/core/models/message.py` - Message request/response models
- `apps/core/models/error.py` - Error response models
- `apps/core/providers/__init__.py` - Providers package initialization
- `apps/core/providers/base.py` - LLM provider interface
- `apps/core/providers/mock.py` - MockLLMProvider implementation
- `apps/core/services/__init__.py` - Services package initialization
- `apps/core/services/message_service.py` - Message processing service
- `apps/core/services/validation_service.py` - Input validation service
- `apps/core/api/__init__.py` - API package initialization
- `apps/core/api/messages.py` - Message API endpoints
- `apps/core/middleware/__init__.py` - Middleware package initialization
- `apps/core/middleware/logging.py` - Structured logging middleware
- `apps/core/middleware/rate_limit.py` - Rate limiting middleware

### 11.2 Test Files

**Test Structure:**
- `tests/__init__.py` - Test package initialization
- `tests/conftest.py` - Pytest configuration and fixtures
- `tests/unit/__init__.py` - Unit tests package
- `tests/unit/test_validation.py` - Validation logic tests
- `tests/unit/test_providers.py` - Provider interface tests
- `tests/unit/test_models.py` - Model validation tests
- `tests/integration/__init__.py` - Integration tests package
- `tests/integration/test_message_flow.py` - End-to-end message flow tests
- `tests/integration/test_api_contract.py` - API contract compliance tests
- `tests/contract/__init__.py` - Contract tests package
- `tests/contract/test_schemas.py` - Schema validation tests

### 11.3 Configuration Files

**Project Configuration:**
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `pytest.ini` - Pytest configuration
- `.ruff.toml` - Ruff linting configuration
- `.env.example` - Environment variables template (updated)

### 11.4 Infrastructure Files

**Docker Configuration:**
- `infrastructure/docker/Dockerfile` - Application container
- `infrastructure/docker/docker-compose.yml` - Local development environment

### 11.5 Documentation Files

**Updated Documentation:**
- `README.md` - Updated with feature setup and usage instructions
- `docs/decisions/001-text-interaction-architecture.md` - Architecture decision record

**Total Files to Create:** 32 files

---

## 12. Files to Modify

### 12.1 Configuration Updates

**`.env.example`** - Add new environment variables:
```bash
# LLM Provider Configuration
LLM_PROVIDER=mock

# Mock LLM Provider Configuration
MOCK_LLM_DELAY_MS=1000
MOCK_LLM_SIMULATE_ERRORS=false

# API Configuration
API_RATE_LIMIT_REQUESTS_PER_MINUTE=10
```

**`README.md`** - Add setup and usage instructions:
```markdown
## Text Interaction Feature

### Setup
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: `cp .env.example .env`
3. Start server: `uvicorn apps.core.main:app --reload`

### Usage
Send a POST request to `http://localhost:8000/api/messages`:
```bash
curl -X POST http://localhost:8000/api/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello JARVIS"}'
```

### Testing
Run tests: `pytest`
Run with coverage: `pytest --cov=apps/core --cov-report=html`
```

**Total Files to Modify:** 2 files

---

## 13. Implementation Order

### Phase 1: Foundation (Infrastructure Setup)

**Objective:** Establish development environment and project structure

**Tasks:**
1. Create Python project configuration files (`pyproject.toml`, `requirements.txt`)
2. Create development configuration files (`pytest.ini`, `.ruff.toml`)
3. Update `.env.example` with new environment variables
4. Create directory structure for `apps/core/`
5. Create basic `apps/core/__init__.py` files

**Validation:** 
- Project structure created
- Dependencies can be installed
- Configuration files are valid

**Traceability:** Supports Principle X (Incremental Delivery)

---

### Phase 2: Core Interfaces and Models

**Objective:** Define data models and provider interface

**Tasks:**
1. Create Pydantic models (`apps/core/models/message.py`, `apps/core/models/error.py`)
2. Create LLM provider interface (`apps/core/providers/base.py`)
3. Create MockLLMProvider implementation (`apps/core/providers/mock.py`)
4. Create provider factory (`apps/core/providers/__init__.py`)
5. Write unit tests for models and providers

**Validation:**
- Unit tests for models pass
- Unit tests for providers pass
- Provider interface is implemented correctly
- Mock provider returns deterministic responses

**Traceability:** FR-004, FR-005, AC-003

---

### Phase 3: Service Layer

**Objective:** Implement business logic services

**Tasks:**
1. Create ValidationService (`apps/core/services/validation_service.py`)
2. Create MessageService (`apps/core/services/message_service.py`)
3. Write unit tests for validation service
4. Write unit tests for message service

**Validation:**
- Validation service correctly validates messages
- Message service orchestrates processing workflow
- Unit tests for services pass

**Traceability:** FR-002, FR-003, FR-007, AC-002

---

### Phase 4: API Layer

**Objective:** Implement HTTP endpoints and middleware

**Tasks:**
1. Create logging middleware (`apps/core/middleware/logging.py`)
2. Create rate limiting middleware (`apps/core/middleware/rate_limit.py`)
3. Create message API endpoints (`apps/core/api/messages.py`)
4. Create FastAPI application (`apps/core/main.py`)
5. Add health endpoint
6. Write integration tests for API

**Validation:**
- API endpoints accept valid requests
- API returns proper error responses
- Middleware functions correctly
- Integration tests pass

**Traceability:** FR-001, FR-006, AC-001, AC-007

---

### Phase 5: Error Handling and Edge Cases

**Objective:** Implement comprehensive error handling

**Tasks:**
1. Implement validation error handling
2. Implement provider error handling
3. Implement rate limiting error handling
4. Add error context logging
5. Write integration tests for error scenarios

**Validation:**
- All error scenarios (ES-001 through ES-008) are handled correctly
- Error responses match specification
- System remains operational after errors
- Error logs contain required context

**Traceability:** FR-007, FR-008, AC-004, AC-008

---

### Phase 6: Testing and Validation

**Objective:** Ensure comprehensive test coverage and validation

**Tasks:**
1. Write contract tests for API schemas
2. Write performance tests for concurrent requests
3. Write security tests for input validation
4. Achieve 80% code coverage
5. Validate all acceptance criteria
6. Update README with usage instructions

**Validation:**
- All tests pass with 80%+ coverage
- All acceptance criteria (AC-001 through AC-010) are met
- Performance requirements (NFR-001, NFR-003) are met
- Security requirements (SC-001 through SC-005) are met
- Observability requirements (OR-001 through OR-005) are met

**Traceability:** NFR-006, AC-006, AC-009, AC-010

---

### Phase 7: Documentation and Cleanup

**Objective:** Complete documentation and code quality

**Tasks:**
1. Create architecture decision record
2. Add inline code documentation
3. Run linting and fix issues
4. Run type checking
5. Final integration testing
6. Update README with complete instructions

**Validation:**
- Code passes linting (Ruff)
- Code passes type checking (if implemented)
- Documentation is complete
- All tests pass
- Feature is ready for validation

**Traceability:** NFR-005, Principle IX (Documentation)

---

## Implementation Summary

**Total Phases:** 7  
**Estimated Duration:** 2-3 weeks  
**Total Files to Create:** 32  
**Total Files to Modify:** 2  

**Key Architectural Decisions:**

1. **Modular Monolith:** Follows Principle III (Simplicity) - no microservices
2. **Layered Architecture:** Clear separation of concerns (API, Service, Provider)
3. **Provider Abstraction:** Supports FR-004 and enables future provider additions
4. **Mock-First Development:** Supports FR-010 and local-first execution
5. **Structured Logging:** JSON logging for observability and debugging
6. **Comprehensive Testing:** Unit, integration, and contract tests for quality

**Constitution Compliance:**

- ✅ Principle I (Specification First): All implementation traceable to specification
- ✅ Principle II (Local First): No cloud dependencies, mock provider for development
- ✅ Principle III (Simplicity): Modular monolith, standard web stack
- ✅ Principle IV (Hardware Abstraction): Provider interface isolates external dependencies
- ✅ Principle V (Controlled Actions): Input validation, error handling
- ✅ Principle VI (Testability): 80% coverage, offline test execution
- ✅ Principle VII (Security): Environment variables, message privacy
- ✅ Principle VIII (Observability): Structured logging, error context
- ✅ Principle IX (Documentation): Inline docs, README, ADR
- ✅ Principle X (Incremental Delivery): 7 phases, each independently validated

**Specification Compliance:**

- ✅ All functional requirements (FR-001 through FR-010) addressed
- ✅ All non-functional requirements (NFR-001 through NFR-006) addressed
- ✅ All error scenarios (ES-001 through ES-008) handled
- ✅ All acceptance criteria (AC-001 through AC-010) testable
- ✅ All security considerations (SC-001 through SC-005) implemented
- ✅ All observability requirements (OR-001 through OR-005) supported

**No Clarification Questions Required:** The specification is sufficient for implementation. All open questions were resolved during specification review.

---

**Status:** Draft - Awaiting Review and Approval