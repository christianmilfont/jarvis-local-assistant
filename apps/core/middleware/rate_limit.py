"""In-memory rate limiting middleware for API protection."""

import json
import os
import time
from collections import defaultdict
from typing import Dict, List

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for in-memory rate limiting to prevent API abuse.

    This middleware implements simple in-memory rate limiting:
    - Limits requests to 10 per minute per IP address
    - Returns 429 Too Many Requests when limit exceeded
    - Error response includes limit and retry_after information
    - Uses sliding window approach for accurate rate limiting

    Configuration:
        Rate limit can be configured via environment variable:
        API_RATE_LIMIT_REQUESTS_PER_MINUTE (default: 10)
    """

    def __init__(self, app, requests_per_minute: int = 10):
        """Initialize the rate limiting middleware.

        Args:
            app: The ASGI application
            requests_per_minute: Maximum requests per minute per IP (default: 10)
        """
        super().__init__(app)
        self.requests_per_minute = int(
            os.getenv("API_RATE_LIMIT_REQUESTS_PER_MINUTE", str(requests_per_minute))
        )
        # Dictionary to track request timestamps per IP address
        # Format: {ip_address: [timestamp1, timestamp2, ...]}
        self.request_history: Dict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        """Process request through the middleware pipeline.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware or route handler in the pipeline

        Returns:
            The HTTP response from the next handler, or 429 error if rate limited
        """
        # Get client IP address
        client_ip = self._get_client_ip(request)

        # Clean up old requests (older than 1 minute) before checking
        self._cleanup_old_requests(client_ip)

        # Check if request should be rate limited
        if self._is_rate_limited(client_ip):
            return self._create_rate_limit_response(client_ip)

        # Record this request
        self._record_request(client_ip)

        # Process the request
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """Get the client IP address from the request.

        Args:
            request: The HTTP request

        Returns:
            The client IP address as a string
        """
        if request.client and request.client.host:
            return request.client.host
        return "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if the client has exceeded the rate limit.

        Args:
            client_ip: The client IP address

        Returns:
            True if rate limited, False otherwise
        """
        current_time = time.time()
        request_times = self.request_history.get(client_ip, [])

        # Filter requests within the last minute
        recent_requests = [t for t in request_times if current_time - t < 60]

        # Update the request history with only recent requests
        self.request_history[client_ip] = recent_requests

        # Check if the number of recent requests exceeds the limit
        return len(recent_requests) >= self.requests_per_minute

    def _record_request(self, client_ip: str):
        """Record a request from the client.

        Args:
            client_ip: The client IP address
        """
        current_time = time.time()
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        self.request_history[client_ip].append(current_time)

    def _cleanup_old_requests(self, client_ip: str):
        """Clean up requests older than 1 minute for the client.

        Args:
            client_ip: The client IP address
        """
        current_time = time.time()
        request_times = self.request_history.get(client_ip, [])

        # Keep only requests within the last minute
        self.request_history[client_ip] = [t for t in request_times if current_time - t < 60]

    def _create_rate_limit_response(self, client_ip: str) -> Response:
        """Create a 429 Too Many Requests response.

        Args:
            client_ip: The client IP address that exceeded the limit

        Returns:
            A Response object with rate limit error details
        """
        # Calculate retry_after (seconds until oldest request expires)
        current_time = time.time()
        retry_after = 60  # Default to 60 seconds

        # Find the oldest request for this client and calculate when it expires
        if client_ip in self.request_history and self.request_history[client_ip]:
            oldest_request = min(self.request_history[client_ip])
            retry_after = int(60 - (current_time - oldest_request))
            retry_after = max(1, retry_after)  # Ensure at least 1 second

        error_response = {
            "status": "error",
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests, please try again later",
                "details": {
                    "limit": f"{self.requests_per_minute} requests per minute",
                    "retry_after": retry_after,
                },
            },
        }

        return Response(
            content=json.dumps(error_response),
            status_code=429,
            media_type="application/json",
            headers={"Retry-After": str(retry_after)},
        )
