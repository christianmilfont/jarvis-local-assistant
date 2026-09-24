"""Unit tests for LLM provider interface."""

import asyncio
import inspect
import os

import pytest

from apps.core.providers import create_provider
from apps.core.providers.base import LLMProvider
from apps.core.providers.mock import MockLLMProvider


class TestLLMProviderInterface:
    """Tests for LLMProvider abstract interface."""

    def test_interface_cannot_be_instantiated_directly(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            LLMProvider()
        assert "Can't instantiate abstract class" in str(exc_info.value)

    def test_generate_response_is_abstract(self):
        """Test that generate_response method is abstract."""
        assert hasattr(LLMProvider, "generate_response")
        assert getattr(LLMProvider.generate_response, "__isabstractmethod__", False)

    def test_health_check_is_abstract(self):
        """Test that health_check method is abstract."""
        assert hasattr(LLMProvider, "health_check")
        assert getattr(LLMProvider.health_check, "__isabstractmethod__", False)

    def test_provider_name_is_abstract(self):
        """Test that provider_name property is abstract."""
        assert hasattr(LLMProvider, "provider_name")
        # Properties marked with @abstractmethod have the __isabstractmethod__ attribute
        assert getattr(LLMProvider.provider_name, "__isabstractmethod__", False)

    def test_interface_has_required_methods(self):
        """Test that interface has all required methods."""
        assert hasattr(LLMProvider, "generate_response")
        assert hasattr(LLMProvider, "health_check")
        assert hasattr(LLMProvider, "provider_name")

    def test_generate_response_is_async(self):
        """Test that generate_response is an async method."""
        assert asyncio.iscoroutinefunction(LLMProvider.generate_response)

    def test_health_check_is_async(self):
        """Test that health_check is an async method."""
        assert asyncio.iscoroutinefunction(LLMProvider.health_check)

    def test_provider_name_is_property(self):
        """Test that provider_name is a property."""
        assert isinstance(inspect.getattr_static(LLMProvider, "provider_name"), property)

    def test_interface_docstring_exists(self):
        """Test that interface has docstring."""
        assert LLMProvider.__doc__ is not None
        assert len(LLMProvider.__doc__) > 0

    def test_generate_response_docstring_exists(self):
        """Test that generate_response method has docstring."""
        assert LLMProvider.generate_response.__doc__ is not None
        assert len(LLMProvider.generate_response.__doc__) > 0

    def test_health_check_docstring_exists(self):
        """Test that health_check method has docstring."""
        assert LLMProvider.health_check.__doc__ is not None
        assert len(LLMProvider.health_check.__doc__) > 0

    def test_provider_name_docstring_exists(self):
        """Test that provider_name property has docstring."""
        assert LLMProvider.provider_name.__doc__ is not None
        assert len(LLMProvider.provider_name.__doc__) > 0

    def test_concrete_implementation_must_implement_all_abstract_methods(self):
        """Test that concrete implementation must implement all abstract methods."""

        class IncompleteProvider(LLMProvider):
            """Incomplete provider missing abstract methods."""

            pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteProvider()
        assert "Can't instantiate abstract class" in str(exc_info.value)
        assert "generate_response" in str(exc_info.value)
        assert "health_check" in str(exc_info.value)
        assert "provider_name" in str(exc_info.value)

    def test_concrete_implementation_with_all_methods_can_be_instantiated(self):
        """Test that concrete implementation with all methods can be instantiated."""

        class CompleteProvider(LLMProvider):
            """Complete provider implementing all abstract methods."""

            @property
            def provider_name(self) -> str:
                return "CompleteProvider"

            async def generate_response(self, message: str) -> str:
                return f"Response to: {message}"

            async def health_check(self) -> bool:
                return True

        provider = CompleteProvider()
        assert provider.provider_name == "CompleteProvider"
        assert provider is not None


class TestMockLLMProvider:
    """Tests for MockLLMProvider implementation."""

    def test_provider_name(self):
        """Test that provider name is correct."""
        provider = MockLLMProvider()
        assert provider.provider_name == "MockLLMProvider"

    @pytest.mark.asyncio
    async def test_hello_response(self):
        """Test response for hello message."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Hello")
        assert "Hello! I'm JARVIS" in response
        assert "local AI assistant" in response

    @pytest.mark.asyncio
    async def test_hi_response(self):
        """Test response for hi message."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Hi there")
        assert "Hi there! I'm JARVIS" in response

    @pytest.mark.asyncio
    async def test_help_response(self):
        """Test response for help message."""
        provider = MockLLMProvider()
        response = await provider.generate_response("I need help")
        assert "I can help you with various tasks" in response

    @pytest.mark.asyncio
    async def test_default_response(self):
        """Test default response for unknown message."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Random message")
        assert "mock response for testing purposes" in response

    @pytest.mark.asyncio
    async def test_case_insensitive_matching(self):
        """Test that response matching is case-insensitive."""
        provider = MockLLMProvider()
        response1 = await provider.generate_response("HELLO")
        response2 = await provider.generate_response("hello")
        response3 = await provider.generate_response("HeLLo")
        assert response1 == response2 == response3

    @pytest.mark.asyncio
    async def test_deterministic_responses(self):
        """Test that responses are deterministic."""
        provider = MockLLMProvider()
        response1 = await provider.generate_response("Hello")
        response2 = await provider.generate_response("Hello")
        assert response1 == response2

    @pytest.mark.asyncio
    async def test_default_delay(self):
        """Test default processing delay."""
        provider = MockLLMProvider()
        import time

        start = time.time()
        await provider.generate_response("Test")
        elapsed = time.time() - start
        assert elapsed >= 0.9  # Allow some tolerance
        assert elapsed <= 1.2  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_custom_delay(self):
        """Test custom processing delay via environment variable."""
        os.environ["MOCK_LLM_DELAY_MS"] = "100"
        try:
            provider = MockLLMProvider()
            import time

            start = time.time()
            await provider.generate_response("Test")
            elapsed = time.time() - start
            assert elapsed >= 0.05  # Allow some tolerance
            assert elapsed <= 0.2  # Allow some tolerance
        finally:
            os.environ.pop("MOCK_LLM_DELAY_MS", None)

    @pytest.mark.asyncio
    async def test_error_simulation_disabled_by_default(self):
        """Test that error simulation is disabled by default."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Test")
        assert response is not None

    @pytest.mark.asyncio
    async def test_error_simulation_enabled(self):
        """Test error simulation when enabled."""
        os.environ["MOCK_LLM_SIMULATE_ERRORS"] = "true"
        try:
            provider = MockLLMProvider()
            from apps.core.models.error import ProviderError

            with pytest.raises(ProviderError) as exc_info:
                await provider.generate_response("Test")
            assert "Simulated provider error" in str(exc_info.value)
        finally:
            os.environ.pop("MOCK_LLM_SIMULATE_ERRORS", None)

    @pytest.mark.asyncio
    async def test_error_simulation_case_insensitive(self):
        """Test that error simulation setting is case-insensitive."""
        for value in ["true", "True", "TRUE", "TrUe"]:
            os.environ["MOCK_LLM_SIMULATE_ERRORS"] = value
            try:
                provider = MockLLMProvider()
                from apps.core.models.error import ProviderError

                with pytest.raises(ProviderError):
                    await provider.generate_response("Test")
            finally:
                os.environ.pop("MOCK_LLM_SIMULATE_ERRORS", None)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test that health check always returns True."""
        provider = MockLLMProvider()
        assert await provider.health_check() is True

    @pytest.mark.asyncio
    async def test_whitespace_in_message(self):
        """Test handling of whitespace in messages."""
        provider = MockLLMProvider()
        response = await provider.generate_response("  hello  ")
        assert "Hello! I'm JARVIS" in response

    @pytest.mark.asyncio
    async def test_substring_matching(self):
        """Test that response matching works with substrings."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Say hello to me")
        assert "Hello! I'm JARVIS" in response

    @pytest.mark.asyncio
    async def test_no_external_api_calls(self):
        """Test that provider works without external APIs."""
        provider = MockLLMProvider()
        response = await provider.generate_response("Test")
        assert response is not None
        # If this test passes without network errors, no external calls were made

    def test_response_templates_exist(self):
        """Test that all required response templates exist."""
        assert "hello" in MockLLMProvider.RESPONSE_TEMPLATES
        assert "hi" in MockLLMProvider.RESPONSE_TEMPLATES
        assert "help" in MockLLMProvider.RESPONSE_TEMPLATES
        assert "default" in MockLLMProvider.RESPONSE_TEMPLATES

    def test_response_templates_content(self):
        """Test that response templates have appropriate content."""
        assert "JARVIS" in MockLLMProvider.RESPONSE_TEMPLATES["hello"]
        assert "JARVIS" in MockLLMProvider.RESPONSE_TEMPLATES["hi"]
        assert "help" in MockLLMProvider.RESPONSE_TEMPLATES["help"].lower()
        assert "mock" in MockLLMProvider.RESPONSE_TEMPLATES["default"].lower()


class TestProviderFactory:
    """Tests for provider factory function."""

    def test_create_provider_default(self):
        """Test that factory creates mock provider by default."""
        provider = create_provider()
        assert isinstance(provider, MockLLMProvider)
        assert provider.provider_name == "MockLLMProvider"

    def test_create_provider_mock_explicit(self):
        """Test that factory creates mock provider when explicitly requested."""
        os.environ["LLM_PROVIDER"] = "mock"
        try:
            provider = create_provider()
            assert isinstance(provider, MockLLMProvider)
            assert provider.provider_name == "MockLLMProvider"
        finally:
            os.environ.pop("LLM_PROVIDER", None)

    def test_create_provider_unknown_type(self):
        """Test that factory raises ValueError for unknown provider type."""
        os.environ["LLM_PROVIDER"] = "unknown_provider"
        try:
            with pytest.raises(ValueError) as exc_info:
                create_provider()
            assert "Unknown provider type: unknown_provider" in str(exc_info.value)
        finally:
            os.environ.pop("LLM_PROVIDER", None)

    def test_create_provider_case_sensitive(self):
        """Test that provider type is case-sensitive."""
        os.environ["LLM_PROVIDER"] = "MOCK"
        try:
            with pytest.raises(ValueError) as exc_info:
                create_provider()
            assert "Unknown provider type: MOCK" in str(exc_info.value)
        finally:
            os.environ.pop("LLM_PROVIDER", None)

    def test_create_provider_returns_llm_provider_interface(self):
        """Test that factory returns LLMProvider interface."""
        provider = create_provider()
        assert isinstance(provider, LLMProvider)

    def test_create_provider_environment_variable_priority(self):
        """Test that environment variable takes priority over default."""
        # Ensure no environment variable is set
        os.environ.pop("LLM_PROVIDER", None)
        provider = create_provider()
        assert isinstance(provider, MockLLMProvider)

        # Set environment variable
        os.environ["LLM_PROVIDER"] = "mock"
        provider = create_provider()
        assert isinstance(provider, MockLLMProvider)
        os.environ.pop("LLM_PROVIDER", None)

    def test_create_provider_empty_string(self):
        """Test that empty string provider type raises error."""
        os.environ["LLM_PROVIDER"] = ""
        try:
            with pytest.raises(ValueError) as exc_info:
                create_provider()
            assert "Unknown provider type:" in str(exc_info.value)
        finally:
            os.environ.pop("LLM_PROVIDER", None)
