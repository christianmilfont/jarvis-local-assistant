"""Structured JSON logging middleware for request tracing."""

import json
import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured JSON logging with request tracing.

    This middleware provides unique request ID generation for tracing,
    request start logging with timestamp, method, path, request completion
    logging with status code and processing time, error logging with full
    context and stack trace, JSON format for all logs, and message content
    privacy (no plain text message content in logs).

    Privacy Note: Per SC-002, message content is never logged in plain text.
    Only metadata (request_id, method, path, status_code, processing_time) is logged.
    """

    async def dispatch(self, request: Request, call_next):
        """Process request through the middleware pipeline.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler in the pipeline

        Returns:
            The HTTP response from the next handler
        """
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
        """Log request start event.

        Args:
            request: The incoming HTTP request
            request_id: Unique identifier for this request
        """
        log_data = {
            "timestamp": time.time(),
            "level": "INFO",
            "request_id": request_id,
            "message": "Request started",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "client_host": request.client.host if request.client else None,
            },
        }
        logger.info(json.dumps(log_data))

    def _log_request_complete(
        self, request: Request, request_id: str, status_code: int, processing_time: float
    ):
        """Log request completion event.

        Args:
            request: The HTTP request
            request_id: Unique identifier for this request
            status_code: HTTP status code of the response
            processing_time: Processing time in milliseconds
        """
        log_data = {
            "timestamp": time.time(),
            "level": "INFO",
            "request_id": request_id,
            "message": "Request completed",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "processing_time_ms": processing_time,
            },
        }
        logger.info(json.dumps(log_data))

    def _log_request_error(
        self, request: Request, request_id: str, error: str, processing_time: float
    ):
        """Log request error event with full context.

        Args:
            request: The HTTP request
            request_id: Unique identifier for this request
            error: Error message
            processing_time: Processing time in milliseconds
        """
        log_data = {
            "timestamp": time.time(),
            "level": "ERROR",
            "request_id": request_id,
            "message": "Request failed",
            "context": {
                "method": request.method,
                "path": request.url.path,
                "error": error,
                "processing_time_ms": processing_time,
            },
        }
        logger.error(json.dumps(log_data), exc_info=True)
