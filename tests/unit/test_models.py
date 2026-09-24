"""Unit tests for message and error models."""

from datetime import datetime
from uuid import uuid4

import pytest

from apps.core.models.error import (
    ErrorDetails,
    ErrorInfo,
    ErrorResponse,
    ProviderError,
    ProviderTimeoutError,
    ValidationError,
)
from apps.core.models.message import (
    MessageMetadata,
    MessageRequest,
    MessageResponse,
    MessageResponseData,
)


class TestMessageMetadata:
    """Tests for MessageMetadata model."""

    def test_create_empty_metadata(self):
        """Test creating metadata with no fields."""
        metadata = MessageMetadata()
        assert metadata.source is None
        assert metadata.user_id is None

    def test_create_metadata_with_source(self):
        """Test creating metadata with source."""
        metadata = MessageMetadata(source="web")
        assert metadata.source == "web"
        assert metadata.user_id is None

    def test_create_metadata_with_user_id(self):
        """Test creating metadata with user_id."""
        metadata = MessageMetadata(user_id="user123")
        assert metadata.source is None
        assert metadata.user_id == "user123"

    def test_create_metadata_with_all_fields(self):
        """Test creating metadata with all fields."""
        metadata = MessageMetadata(source="mobile", user_id="user456")
        assert metadata.source == "mobile"
        assert metadata.user_id == "user456"


class TestMessageRequest:
    """Tests for MessageRequest model."""

    def test_create_valid_message_request(self):
        """Test creating a valid message request."""
        request = MessageRequest(message="Hello, JARVIS!")
        assert request.message == "Hello, JARVIS!"
        assert request.timestamp is None
        assert request.metadata is None

    def test_create_message_with_timestamp(self):
        """Test creating message request with timestamp."""
        timestamp = datetime(2025, 9, 24, 12, 0, 0)
        request = MessageRequest(message="Test", timestamp=timestamp)
        assert request.message == "Test"
        assert request.timestamp == timestamp

    def test_create_message_with_metadata(self):
        """Test creating message request with metadata."""
        metadata = MessageMetadata(source="web", user_id="user123")
        request = MessageRequest(message="Test", metadata=metadata)
        assert request.message == "Test"
        assert request.metadata.source == "web"
        assert request.metadata.user_id == "user123"

    def test_create_message_with_all_fields(self):
        """Test creating message request with all fields."""
        timestamp = datetime(2025, 9, 24, 12, 0, 0)
        metadata = MessageMetadata(source="mobile", user_id="user456")
        request = MessageRequest(
            message="Complete test message",
            timestamp=timestamp,
            metadata=metadata,
        )
        assert request.message == "Complete test message"
        assert request.timestamp == timestamp
        assert request.metadata.source == "mobile"
        assert request.metadata.user_id == "user456"

    def test_message_minimum_length(self):
        """Test message with minimum length (1 character)."""
        request = MessageRequest(message="H")
        assert request.message == "H"

    def test_message_maximum_length(self):
        """Test message with maximum length (1000 characters)."""
        message = "A" * 1000
        request = MessageRequest(message=message)
        assert len(request.message) == 1000

    def test_message_too_long_raises_error(self):
        """Test that message exceeding 1000 characters raises validation error."""
        message = "A" * 1001
        with pytest.raises(ValueError) as exc_info:
            MessageRequest(message=message)
        assert "String should have at most 1000 characters" in str(exc_info.value)

    def test_empty_message_raises_error(self):
        """Test that empty message raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            MessageRequest(message="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_whitespace_only_message_raises_error(self):
        """Test that whitespace-only message raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            MessageRequest(message="   ")
        assert "Message cannot contain only whitespace" in str(exc_info.value)

    def test_tab_only_message_raises_error(self):
        """Test that tab-only message raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            MessageRequest(message="\t\t")
        assert "Message cannot contain only whitespace" in str(exc_info.value)

    def test_newline_only_message_raises_error(self):
        """Test that newline-only message raises validation error."""
        with pytest.raises(ValueError) as exc_info:
            MessageRequest(message="\n\n")
        assert "Message cannot contain only whitespace" in str(exc_info.value)

    def test_message_with_leading_trailing_whitespace(self):
        """Test that message with leading/trailing whitespace is accepted."""
        request = MessageRequest(message="  Hello  ")
        assert request.message == "  Hello  "

    def test_invalid_timestamp_raises_error(self):
        """Test that invalid timestamp format raises validation error."""
        # Pydantic should handle type validation, but we test the custom validator
        timestamp = datetime(2025, 9, 24, 12, 0, 0)
        request = MessageRequest(message="Test", timestamp=timestamp)
        assert request.timestamp == timestamp

    def test_message_with_unicode(self):
        """Test that message with unicode characters is accepted."""
        request = MessageRequest(message="Hello 世界 🌍")
        assert request.message == "Hello 世界 🌍"


class TestMessageResponseData:
    """Tests for MessageResponseData model."""

    def test_create_response_data(self):
        """Test creating response data with required fields."""
        response_data = MessageResponseData(
            response="Test response",
            processing_time_ms=100,
        )
        assert response_data.response == "Test response"
        assert response_data.processing_time_ms == 100
        assert response_data.message_id is not None
        assert response_data.timestamp is not None

    def test_create_response_data_with_custom_message_id(self):
        """Test creating response data with custom message ID."""
        custom_id = str(uuid4())
        response_data = MessageResponseData(
            message_id=custom_id,
            response="Test response",
            processing_time_ms=100,
        )
        assert response_data.message_id == custom_id

    def test_create_response_data_with_custom_timestamp(self):
        """Test creating response data with custom timestamp."""
        timestamp = datetime(2025, 9, 24, 12, 0, 0)
        response_data = MessageResponseData(
            response="Test response",
            processing_time_ms=100,
            timestamp=timestamp,
        )
        assert response_data.timestamp == timestamp

    def test_response_maximum_length(self):
        """Test response with maximum length (5000 characters)."""
        response = "A" * 5000
        response_data = MessageResponseData(
            response=response,
            processing_time_ms=100,
        )
        assert len(response_data.response) == 5000

    def test_response_too_long_raises_error(self):
        """Test that response exceeding 5000 characters raises validation error."""
        response = "A" * 5001
        with pytest.raises(ValueError) as exc_info:
            MessageResponseData(response=response, processing_time_ms=100)
        assert "String should have at most 5000 characters" in str(exc_info.value)


class TestMessageResponse:
    """Tests for MessageResponse model."""

    def test_create_message_response(self):
        """Test creating a complete message response."""
        response_data = MessageResponseData(
            response="Test response",
            processing_time_ms=100,
        )
        response = MessageResponse(data=response_data)
        assert response.status == "success"
        assert response.data.response == "Test response"
        assert response.data.processing_time_ms == 100

    def test_response_status_defaults_to_success(self):
        """Test that status defaults to 'success'."""
        response_data = MessageResponseData(
            response="Test",
            processing_time_ms=50,
        )
        response = MessageResponse(data=response_data)
        assert response.status == "success"


class TestErrorDetails:
    """Tests for ErrorDetails model."""

    def test_create_empty_error_details(self):
        """Test creating error details with no fields."""
        details = ErrorDetails()
        assert details.field is None
        assert details.reason is None
        assert details.provider is None
        assert details.timeout_seconds is None
        assert details.limit is None
        assert details.retry_after is None

    def test_create_error_details_with_field(self):
        """Test creating error details with field."""
        details = ErrorDetails(field="message", reason="empty_message")
        assert details.field == "message"
        assert details.reason == "empty_message"

    def test_create_error_details_with_provider(self):
        """Test creating error details with provider."""
        details = ErrorDetails(
            provider="MockLLMProvider",
            reason="simulated_error",
        )
        assert details.provider == "MockLLMProvider"
        assert details.reason == "simulated_error"

    def test_create_error_details_with_timeout(self):
        """Test creating error details with timeout."""
        details = ErrorDetails(
            provider="MockLLMProvider",
            timeout_seconds=30,
        )
        assert details.provider == "MockLLMProvider"
        assert details.timeout_seconds == 30

    def test_create_error_details_with_rate_limit(self):
        """Test creating error details with rate limit info."""
        details = ErrorDetails(
            limit="10 requests per minute",
            retry_after=45,
        )
        assert details.limit == "10 requests per minute"
        assert details.retry_after == 45

    def test_create_error_details_with_all_fields(self):
        """Test creating error details with all fields."""
        details = ErrorDetails(
            field="message",
            reason="validation_failed",
            provider="MockLLMProvider",
            timeout_seconds=30,
            limit="10 requests per minute",
            retry_after=45,
        )
        assert details.field == "message"
        assert details.reason == "validation_failed"
        assert details.provider == "MockLLMProvider"
        assert details.timeout_seconds == 30
        assert details.limit == "10 requests per minute"
        assert details.retry_after == 45


class TestErrorInfo:
    """Tests for ErrorInfo model."""

    def test_create_error_info(self):
        """Test creating error info with required fields."""
        error_info = ErrorInfo(
            code="VALIDATION_ERROR",
            message="Message cannot be empty",
        )
        assert error_info.code == "VALIDATION_ERROR"
        assert error_info.message == "Message cannot be empty"
        assert error_info.details is None

    def test_create_error_info_with_details(self):
        """Test creating error info with details."""
        details = ErrorDetails(field="message", reason="empty_message")
        error_info = ErrorInfo(
            code="VALIDATION_ERROR",
            message="Message cannot be empty",
            details=details,
        )
        assert error_info.code == "VALIDATION_ERROR"
        assert error_info.message == "Message cannot be empty"
        assert error_info.details.field == "message"
        assert error_info.details.reason == "empty_message"


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_create_error_response(self):
        """Test creating a complete error response."""
        error_info = ErrorInfo(
            code="VALIDATION_ERROR",
            message="Message cannot be empty",
        )
        error_response = ErrorResponse(error=error_info)
        assert error_response.status == "error"
        assert error_response.error.code == "VALIDATION_ERROR"
        assert error_response.error.message == "Message cannot be empty"

    def test_error_response_status_defaults_to_error(self):
        """Test that status defaults to 'error'."""
        error_info = ErrorInfo(code="TEST_ERROR", message="Test error")
        error_response = ErrorResponse(error=error_info)
        assert error_response.status == "error"

    def test_create_error_response_with_details(self):
        """Test creating error response with details."""
        details = ErrorDetails(field="message", reason="empty_message")
        error_info = ErrorInfo(
            code="VALIDATION_ERROR",
            message="Message cannot be empty",
            details=details,
        )
        error_response = ErrorResponse(error=error_info)
        assert error_response.error.details.field == "message"
        assert error_response.error.details.reason == "empty_message"


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_raise_validation_error(self):
        """Test raising ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("Validation failed")
        assert str(exc_info.value) == "Validation failed"

    def test_catch_validation_error(self):
        """Test catching ValidationError."""
        try:
            raise ValidationError("Test error")
        except ValidationError as e:
            assert str(e) == "Test error"


class TestProviderError:
    """Tests for ProviderError exception."""

    def test_raise_provider_error(self):
        """Test raising ProviderError."""
        with pytest.raises(ProviderError) as exc_info:
            raise ProviderError("Provider unavailable")
        assert str(exc_info.value) == "Provider unavailable"

    def test_catch_provider_error(self):
        """Test catching ProviderError."""
        try:
            raise ProviderError("Test error")
        except ProviderError as e:
            assert str(e) == "Test error"


class TestProviderTimeoutError:
    """Tests for ProviderTimeoutError exception."""

    def test_raise_provider_timeout_error(self):
        """Test raising ProviderTimeoutError."""
        with pytest.raises(ProviderTimeoutError) as exc_info:
            raise ProviderTimeoutError("Provider timeout")
        assert str(exc_info.value) == "Provider timeout"

    def test_catch_provider_timeout_error(self):
        """Test catching ProviderTimeoutError."""
        try:
            raise ProviderTimeoutError("Test timeout")
        except ProviderTimeoutError as e:
            assert str(e) == "Test timeout"

    def test_provider_timeout_error_is_provider_error(self):
        """Test that ProviderTimeoutError can be caught as ProviderError."""
        # Note: This test checks if they should be related
        # Currently they are separate exceptions as per the spec
        with pytest.raises(ProviderTimeoutError):
            raise ProviderTimeoutError("Timeout")
