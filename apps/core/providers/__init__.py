"""LLM provider factory and implementations."""

import os

from apps.core.providers.base import LLMProvider
from apps.core.providers.mock import MockLLMProvider


def create_provider() -> LLMProvider:
    """Factory function to create the configured LLM provider.

    Reads the LLM_PROVIDER environment variable to determine which provider
    to instantiate. Defaults to MockLLMProvider if not set.

    Returns:
        LLMProvider: An instance of the configured provider

    Raises:
        ValueError: If an unknown provider type is specified

    Environment Variables:
        LLM_PROVIDER: The type of provider to create (default: "mock")
    """
    provider_type = os.getenv("LLM_PROVIDER", "mock")

    if provider_type == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
