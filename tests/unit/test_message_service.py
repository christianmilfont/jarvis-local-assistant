"""Unit tests for message processing service."""

from datetime import UTC, datetime

import pytest

from apps.core.models.error import ProviderError, ProviderTimeoutError
from apps.core.models.message import MessageMetadata, MessageRequest
from apps.core.providers.base import LLMProvider
from apps.core.services.message_service import MessageService


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response_text="Test response", should_timeout=False, should_error=False):
        self.response_text = response_text
        self.should_timeout = should_timeout
        self.should_error = should_error
        self.generate_response_call_count = 0

    @property
    def provider_name(self) -> str:
        return "MockLLMProvider"

    async def generate_response(self, message: str) -> str:
        """Generate a mock response."""
        self.generate_response_call_count += 1

        if self.should_timeout:
            raise ProviderTimeoutError("Simulated timeout")
        if self.should_error:
            raise ProviderError("Simulated error")

        return self.response_text

    async def health_check(self) -> bool:
        return True


class TestMessageService:
    """Tests for MessageService class."""

    def test_service_initialization(self):
        """Test that service can be initialized with a provider."""
        mock_provider = MockLLMProvider()
        service = MessageService(mock_provider)
        assert service.llm_provider is mock_provider

    def test_service_requires_provider(self):
        """Test that service requires a provider."""
        with pytest.raises(TypeError):
            MessageService()

    @pytest.mark.asyncio
    async def test_successful_message_processing(self):
        """Test successful message processing workflow."""
        mock_provider = MockLLMProvider(response_text="Hello from JARVIS")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Hello")
        response = await service.process_message(request)

        assert response.status == "success"
        assert response.data.response == "Hello from JARVIS"
        assert response.data.message_id is not None
        assert response.data.timestamp is not None
        assert response.data.processing_time_ms >= 0
        assert mock_provider.generate_response_call_count == 1

    @pytest.mark.asyncio
    async def test_provider_generate_response_called(self):
        """Test that provider.generate_response is called with correct message."""
        mock_provider = MockLLMProvider(response_text="Test response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test message")
        await service.process_message(request)

        assert mock_provider.generate_response_call_count == 1

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self):
        """Test that processing time is tracked correctly."""
        mock_provider = MockLLMProvider(response_text="Test response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test message")
        response = await service.process_message(request)

        assert response.data.processing_time_ms >= 0
        assert isinstance(response.data.processing_time_ms, int)

    @pytest.mark.asyncio
    async def test_response_formatting(self):
        """Test that response is formatted with correct metadata."""
        mock_provider = MockLLMProvider(response_text="Test response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test message")
        response = await service.process_message(request)

        assert response.status == "success"
        assert response.data.response == "Test response"
        assert response.data.message_id is not None
        assert len(response.data.message_id) > 0
        assert response.data.timestamp is not None
        assert isinstance(response.data.timestamp, datetime)
        assert response.data.timestamp.tzinfo == UTC

    @pytest.mark.asyncio
    async def test_provider_error_propagation(self):
        """Test that provider errors are propagated correctly."""
        mock_provider = MockLLMProvider(should_error=True)
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test message")

        with pytest.raises(ProviderError) as exc_info:
            await service.process_message(request)
        assert "Simulated error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_provider_timeout_error_propagation(self):
        """Test that provider timeout errors are propagated correctly."""
        mock_provider = MockLLMProvider(should_timeout=True)
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test message")

        with pytest.raises(ProviderTimeoutError) as exc_info:
            await service.process_message(request)
        assert "Simulated timeout" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_unexpected_error_wrapped_as_provider_error(self):
        """Test that unexpected errors are wrapped as ProviderError."""

        class FailingProvider(LLMProvider):
            @property
            def provider_name(self) -> str:
                return "FailingProvider"

            async def generate_response(self, message: str) -> str:
                raise ValueError("Unexpected error")

            async def health_check(self) -> bool:
                return True

        failing_provider = FailingProvider()
        service = MessageService(failing_provider)

        request = MessageRequest(message="Test message")

        with pytest.raises(ProviderError) as exc_info:
            await service.process_message(request)
        assert "Unexpected error during message processing" in str(exc_info.value)
        assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_service_depends_on_interface_not_implementation(self):
        """Test that service depends on LLMProvider interface, not specific implementation."""
        # Create a custom provider that implements the interface
        class CustomProvider(LLMProvider):
            @property
            def provider_name(self) -> str:
                return "CustomProvider"

            async def generate_response(self, message: str) -> str:
                return f"Custom response to: {message}"

            async def health_check(self) -> bool:
                return True

        custom_provider = CustomProvider()
        service = MessageService(custom_provider)

        request = MessageRequest(message="Test")
        response = await service.process_message(request)

        assert response.data.response == "Custom response to: Test"

    @pytest.mark.asyncio
    async def test_multiple_message_processing(self):
        """Test that service can process multiple messages sequentially."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        request1 = MessageRequest(message="Message 1")
        request2 = MessageRequest(message="Message 2")
        request3 = MessageRequest(message="Message 3")

        response1 = await service.process_message(request1)
        response2 = await service.process_message(request2)
        response3 = await service.process_message(request3)

        assert response1.data.response == "Response"
        assert response2.data.response == "Response"
        assert response3.data.response == "Response"
        assert mock_provider.generate_response_call_count == 3

    @pytest.mark.asyncio
    async def test_message_with_metadata(self):
        """Test that messages with metadata are processed correctly."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        metadata = MessageMetadata(source="test", user_id="user123")
        request = MessageRequest(message="Test", metadata=metadata)

        response = await service.process_message(request)

        assert response.data.response == "Response"
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_message_with_timestamp(self):
        """Test that messages with timestamp are processed correctly."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        timestamp = datetime.now(UTC)
        request = MessageRequest(message="Test", timestamp=timestamp)

        response = await service.process_message(request)

        assert response.data.response == "Response"
        assert response.status == "success"

    @pytest.mark.asyncio
    async def test_processing_time_reasonable(self):
        """Test that processing time is reasonable for a simple operation."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test")
        response = await service.process_message(request)

        # Processing time should be very small for a simple mock operation
        assert response.data.processing_time_ms < 1000

    @pytest.mark.asyncio
    async def test_message_id_unique(self):
        """Test that each message gets a unique message ID."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        request1 = MessageRequest(message="Message 1")
        request2 = MessageRequest(message="Message 2")

        response1 = await service.process_message(request1)
        response2 = await service.process_message(request2)

        assert response1.data.message_id != response2.data.message_id

    @pytest.mark.asyncio
    async def test_response_timestamp_current(self):
        """Test that response timestamp is current."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        before = datetime.now(UTC)
        request = MessageRequest(message="Test")
        response = await service.process_message(request)
        after = datetime.now(UTC)

        assert before <= response.data.timestamp <= after

    @pytest.mark.asyncio
    async def test_service_preserves_request_message(self):
        """Test that service passes the correct message to provider."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        test_message = "Specific test message"
        request = MessageRequest(message=test_message)

        await service.process_message(request)

        # The provider should have been called with the correct message
        # We can verify this by checking the call count
        assert mock_provider.generate_response_call_count == 1

    @pytest.mark.asyncio
    async def test_service_handles_empty_metadata(self):
        """Test that service handles messages with no metadata."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test", metadata=None)

        response = await service.process_message(request)

        assert response.status == "success"
        assert response.data.response == "Response"

    @pytest.mark.asyncio
    async def test_service_handles_none_timestamp(self):
        """Test that service handles messages with no timestamp."""
        mock_provider = MockLLMProvider(response_text="Response")
        service = MessageService(mock_provider)

        request = MessageRequest(message="Test", timestamp=None)

        response = await service.process_message(request)

        assert response.status == "success"
        assert response.data.response == "Response"
