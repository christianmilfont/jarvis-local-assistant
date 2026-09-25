"""Message API endpoints for JARVIS Core."""

import logging
import time

from fastapi import APIRouter, HTTPException, Request

from apps.core.models.error import ProviderError, ProviderTimeoutError, ValidationError
from apps.core.models.message import MessageRequest, MessageResponse
from apps.core.providers import create_provider
from apps.core.services.message_service import MessageService

logger = logging.getLogger(__name__)

router = APIRouter()
message_service = MessageService(create_provider())


@router.post("/api/messages", response_model=MessageResponse)
async def submit_message(request: Request, message_request: MessageRequest):
    """Submit a message for processing.

    This endpoint accepts a text message, processes it through the JARVIS Core
    workflow, and returns a response from the LLM provider.

    Args:
        request: The HTTP request
        message_request: The message request with validated data

    Returns:
        MessageResponse with the generated response and metadata

    Raises:
        HTTPException: For validation errors (400), provider errors (503),
                      provider timeouts (504), or internal errors (500)
    """
    start_time = time.time()

    try:
        # Process message through service layer
        response = await message_service.process_message(message_request)
        processing_time = int((time.time() - start_time) * 1000)
        response.data.processing_time_ms = processing_time
        return response

    except ValidationError:
        # Validation errors - return 400
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Message validation failed",
                "details": {"field": "message", "reason": "validation_failed"},
            },
        )

    except ProviderTimeoutError:
        # Provider timeout - return 504
        raise HTTPException(
            status_code=504,
            detail={
                "code": "PROVIDER_TIMEOUT",
                "message": "Response generation timed out",
                "details": {"provider": "MockLLMProvider", "timeout_seconds": 30},
            },
        )

    except ProviderError as e:
        # Provider error - return 503
        raise HTTPException(
            status_code=503,
            detail={
                "code": "PROVIDER_ERROR",
                "message": "Unable to generate response - provider unavailable",
                "details": {"provider": "MockLLMProvider", "reason": str(e)},
            },
        )

    except Exception as e:
        # Unexpected error - return 500
        request_id = (
            request.state.request_id if hasattr(request.state, "request_id") else "unknown"
        )
        # Log full error context
        logger.error(f"Unexpected error processing message {request_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": {"request_id": request_id},
            },
        )
