"""Mock LLM provider for development and testing."""

import asyncio
import os

from apps.core.models.error import ProviderError
from apps.core.providers.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for development and testing."""

    # Predefined response templates based on message content
    RESPONSE_TEMPLATES = {
        "hello": "Hello! I'm JARVIS, your local AI assistant. How can I help you today?",
        "hi": "Hi there! I'm JARVIS. What would you like to know?",
        "help": "I can help you with various tasks. What do you need assistance with?",
        "default": "I understand your message. This is a mock response for testing purposes.",
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
