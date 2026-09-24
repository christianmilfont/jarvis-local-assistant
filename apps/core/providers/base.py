"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod


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
        pass  # pragma: no cover

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is operational.

        Returns:
            True if the provider is healthy, False otherwise
        """
        pass  # pragma: no cover

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider implementation."""
        pass  # pragma: no cover
