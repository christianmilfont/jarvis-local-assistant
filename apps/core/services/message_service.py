"""Message processing service for JARVIS Core."""

import time
from datetime import UTC, datetime

from apps.core.models.error import ProviderError, ProviderTimeoutError
from apps.core.models.message import MessageRequest, MessageResponse, MessageResponseData
from apps.core.providers.base import LLMProvider


class MessageService:
    """Service for processing messages through JARVIS Core.

    This service orchestrates the message processing workflow by:
    1. Validating the message request
    2. Calling the LLM provider to generate a response
    3. Formatting the response with metadata
    4. Tracking processing time

    The service uses dependency injection for the LLM provider, allowing
    different implementations (mock, real providers) to be used.
    """

    def __init__(self, llm_provider: LLMProvider):
        """Initialize the message service with an LLM provider.

        Args:
            llm_provider: An implementation of the LLMProvider interface
        """
        self.llm_provider = llm_provider

    async def process_message(self, request: MessageRequest) -> MessageResponse:
        """Process a message through the JARVIS Core workflow.

        This method orchestrates the complete message processing flow:
        1. Track start time for performance measurement
        2. Call the LLM provider to generate a response
        3. Format the response with metadata (message_id, timestamp, processing time)
        4. Return the formatted response

        Args:
            request: The validated message request

        Returns:
            MessageResponse with the generated response and metadata

        Raises:
            ValidationError: If message validation fails
            ProviderError: If LLM provider fails to generate a response
            ProviderTimeoutError: If LLM provider times out
        """
        start_time = time.time()

        try:
            # Generate response using the LLM provider
            response_text = await self.llm_provider.generate_response(request.message)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Format response with metadata
            response_data = MessageResponseData(
                response=response_text,
                processing_time_ms=processing_time_ms,
                timestamp=datetime.now(UTC),
            )

            return MessageResponse(status="success", data=response_data)

        except ProviderTimeoutError:
            # Re-raise provider timeout errors
            raise
        except ProviderError:
            # Re-raise provider errors
            raise
        except Exception as e:
            # Wrap unexpected errors as provider errors
            raise ProviderError(f"Unexpected error during message processing: {str(e)}") from e
