"""Unit tests for rate limiting middleware."""

import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from apps.core.middleware.rate_limit import RateLimitMiddleware


class TestRateLimitMiddleware:
    """Tests for RateLimitMiddleware class."""

    def test_middleware_inherits_from_base_http_middleware(self):
        """Test that RateLimitMiddleware inherits from BaseHTTPMiddleware."""
        middleware = RateLimitMiddleware(app=MagicMock())
        assert isinstance(middleware, BaseHTTPMiddleware)

    def test_middleware_requires_app(self):
        """Test that middleware requires an app parameter."""
        with pytest.raises(TypeError):
            RateLimitMiddleware()

    def test_default_requests_per_minute(self):
        """Test that default requests per minute is 10."""
        middleware = RateLimitMiddleware(app=MagicMock())
        assert middleware.requests_per_minute == 10

    def test_custom_requests_per_minute(self):
        """Test that custom requests per minute can be set."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=5)
        assert middleware.requests_per_minute == 5

    def test_requests_per_minute_from_environment(self):
        """Test that requests per minute can be set via environment variable."""
        with patch.dict("os.environ", {"API_RATE_LIMIT_REQUESTS_PER_MINUTE": "20"}):
            middleware = RateLimitMiddleware(app=MagicMock())
            assert middleware.requests_per_minute == 20

    def test_request_history_initialization(self):
        """Test that request history is initialized as defaultdict."""
        middleware = RateLimitMiddleware(app=MagicMock())
        assert middleware.request_history is not None
        assert isinstance(middleware.request_history, dict)

    @pytest.mark.asyncio
    async def test_first_request_allowed(self):
        """Test that the first request from an IP is allowed."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=5)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        response = await middleware.dispatch(mock_request, call_next)

        # Request should be allowed
        assert response is mock_response
        assert middleware.request_history["127.0.0.1"] is not None
        assert len(middleware.request_history["127.0.0.1"]) == 1

    @pytest.mark.asyncio
    async def test_requests_within_limit_allowed(self):
        """Test that requests within the limit are allowed."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=5)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 5 requests (within limit)
        for _ in range(5):
            response = await middleware.dispatch(mock_request, call_next)
            assert response is mock_response

        assert len(middleware.request_history["127.0.0.1"]) == 5

    @pytest.mark.asyncio
    async def test_requests_exceeding_limit_blocked(self):
        """Test that requests exceeding the limit are blocked."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=3)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 3 requests (at limit)
        for _ in range(3):
            response = await middleware.dispatch(mock_request, call_next)
            assert response is mock_response

        # 4th request should be rate limited
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_rate_limit_response_format(self):
        """Test that rate limit response has correct format."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=2)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 2 requests (at limit)
        for _ in range(2):
            await middleware.dispatch(mock_request, call_next)

        # 3rd request should be rate limited
        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 429
        assert response.media_type == "application/json"

        # Parse response body
        response_data = json.loads(response.body.decode())
        assert response_data["status"] == "error"
        assert response_data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert response_data["error"]["message"] == "Too many requests, please try again later"
        assert response_data["error"]["details"]["limit"] == "2 requests per minute"
        assert "retry_after" in response_data["error"]["details"]
        assert isinstance(response_data["error"]["details"]["retry_after"], int)

    @pytest.mark.asyncio
    async def test_rate_limit_response_includes_retry_after_header(self):
        """Test that rate limit response includes Retry-After header."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=2)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 2 requests (at limit)
        for _ in range(2):
            await middleware.dispatch(mock_request, call_next)

        # 3rd request should be rate limited
        response = await middleware.dispatch(mock_request, call_next)

        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] is not None

    @pytest.mark.asyncio
    async def test_different_ips_have_separate_limits(self):
        """Test that different IP addresses have separate rate limits."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=2)

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 2 requests from IP1 (at limit)
        request1 = MagicMock(spec=Request)
        request1.client = MagicMock()
        request1.client.host = "192.168.1.1"

        for _ in range(2):
            response = await middleware.dispatch(request1, call_next)
            assert response is mock_response

        # IP1 should be rate limited
        response = await middleware.dispatch(request1, call_next)
        assert response.status_code == 429

        # IP2 should still be allowed
        request2 = MagicMock(spec=Request)
        request2.client = MagicMock()
        request2.client.host = "192.168.1.2"

        response = await middleware.dispatch(request2, call_next)
        assert response is mock_response

    @pytest.mark.asyncio
    async def test_old_requests_cleaned_up(self):
        """Test that requests older than 1 minute are cleaned up."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=3)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 3 requests (at limit)
        for _ in range(3):
            await middleware.dispatch(mock_request, call_next)

        assert len(middleware.request_history["127.0.0.1"]) == 3

        # Manually add an old request (older than 1 minute)
        old_time = time.time() - 70
        middleware.request_history["127.0.0.1"].append(old_time)

        # Make another request - should clean up old request
        await middleware.dispatch(mock_request, call_next)

        # Old request should be cleaned up
        assert all(t > time.time() - 60 for t in middleware.request_history["127.0.0.1"])

    @pytest.mark.asyncio
    async def test_requests_after_minute_expire(self):
        """Test that requests made after 1 minute don't count against limit."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=2)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 2 requests (at limit)
        for _ in range(2):
            await middleware.dispatch(mock_request, call_next)

        # Should be rate limited
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 429

        # Manually expire the requests by setting them to old timestamps
        old_time = time.time() - 65
        middleware.request_history["127.0.0.1"] = [old_time, old_time]

        # Now requests should be allowed again
        response = await middleware.dispatch(mock_request, call_next)
        assert response is mock_response

    @pytest.mark.asyncio
    async def test_handles_none_client(self):
        """Test that middleware handles requests with no client info."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=5)

        mock_request = MagicMock(spec=Request)
        mock_request.client = None

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Should not raise an exception
        response = await middleware.dispatch(mock_request, call_next)
        assert response is mock_response

    def test_get_client_ip_with_client(self):
        """Test that _get_client_ip returns client IP when available."""
        middleware = RateLimitMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_without_client(self):
        """Test that _get_client_ip returns 'unknown' when client is None."""
        middleware = RateLimitMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.client = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    def test_get_client_ip_without_host(self):
        """Test that _get_client_ip returns 'unknown' when client.host is None."""
        middleware = RateLimitMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = None

        ip = middleware._get_client_ip(mock_request)
        assert ip == "unknown"

    def test_is_rate_limited_under_limit(self):
        """Test that _is_rate_limited returns False when under limit."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=5)

        # Add 2 recent requests
        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [current_time, current_time - 10]

        assert middleware._is_rate_limited("127.0.0.1") is False

    def test_is_rate_limited_at_limit(self):
        """Test that _is_rate_limited returns True when at limit."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=2)

        # Add 2 recent requests (at limit)
        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [current_time, current_time - 10]

        assert middleware._is_rate_limited("127.0.0.1") is True

    def test_is_rate_limited_over_limit(self):
        """Test that _is_rate_limited returns True when over limit."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=2)

        # Add 3 recent requests (over limit)
        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [
            current_time,
            current_time - 10,
            current_time - 20,
        ]

        assert middleware._is_rate_limited("127.0.0.1") is True

    def test_is_rate_limited_with_old_requests(self):
        """Test that _is_rate_limited ignores old requests."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=3)

        # Add 2 recent requests and 1 old request
        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [
            current_time,
            current_time - 10,
            current_time - 70,  # Old request
        ]

        # Should not be rate limited because old request is ignored
        assert middleware._is_rate_limited("127.0.0.1") is False

    def test_record_request(self):
        """Test that _record_request adds request timestamp."""
        middleware = RateLimitMiddleware(app=MagicMock())

        middleware._record_request("127.0.0.1")

        assert "127.0.0.1" in middleware.request_history
        assert len(middleware.request_history["127.0.0.1"]) == 1
        assert middleware.request_history["127.0.0.1"][0] > 0

    def test_record_request_multiple(self):
        """Test that _record_request adds multiple request timestamps."""
        middleware = RateLimitMiddleware(app=MagicMock())

        for _ in range(3):
            middleware._record_request("127.0.0.1")

        assert len(middleware.request_history["127.0.0.1"]) == 3

    def test_cleanup_old_requests(self):
        """Test that _cleanup_old_requests removes old requests."""
        middleware = RateLimitMiddleware(app=MagicMock())

        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [
            current_time,
            current_time - 30,
            current_time - 70,  # Old request
        ]

        middleware._cleanup_old_requests("127.0.0.1")

        # Old request should be removed
        assert len(middleware.request_history["127.0.0.1"]) == 2
        assert all(t > current_time - 60 for t in middleware.request_history["127.0.0.1"])

    def test_cleanup_old_requests_empty_history(self):
        """Test that _cleanup_old_requests handles empty history."""
        middleware = RateLimitMiddleware(app=MagicMock())

        middleware._cleanup_old_requests("127.0.0.1")

        # Should not raise an exception
        assert "127.0.0.1" not in middleware.request_history or len(
            middleware.request_history["127.0.0.1"]
        ) == 0

    def test_create_rate_limit_response(self):
        """Test that _create_rate_limit_response creates correct response."""
        middleware = RateLimitMiddleware(app=MagicMock(), requests_per_minute=5)

        response = middleware._create_rate_limit_response("127.0.0.1")

        assert response.status_code == 429
        assert response.media_type == "application/json"

        response_data = json.loads(response.body.decode())
        assert response_data["status"] == "error"
        assert response_data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert response_data["error"]["message"] == "Too many requests, please try again later"
        assert response_data["error"]["details"]["limit"] == "5 requests per minute"
        assert "retry_after" in response_data["error"]["details"]

    def test_create_rate_limit_response_includes_retry_after_header(self):
        """Test that _create_rate_limit_response includes Retry-After header."""
        middleware = RateLimitMiddleware(app=MagicMock())

        response = middleware._create_rate_limit_response("127.0.0.1")

        assert "Retry-After" in response.headers
        assert response.headers["Retry-After"] is not None

    @pytest.mark.asyncio
    async def test_sliding_window_accuracy(self):
        """Test that sliding window provides accurate rate limiting."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=3)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 3 requests at different times (within limit)
        current_time = time.time()
        middleware.request_history["127.0.0.1"] = [
            current_time,
            current_time - 10,
            current_time - 20,
        ]

        # Should be rate limited
        response = await middleware.dispatch(mock_request, call_next)
        assert response.status_code == 429

        # Manually expire the first request (set to 65 seconds ago)
        middleware.request_history["127.0.0.1"][0] = current_time - 65

        # Now should be allowed again (only 2 recent requests)
        response = await middleware.dispatch(mock_request, call_next)
        assert response is mock_response

    @pytest.mark.asyncio
    async def test_retry_after_calculation(self):
        """Test that retry_after is calculated correctly."""
        mock_app = AsyncMock()
        middleware = RateLimitMiddleware(app=mock_app, requests_per_minute=2)

        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        # Make 2 requests
        for _ in range(2):
            await middleware.dispatch(mock_request, call_next)

        # Manually set first request to 30 seconds ago
        current_time = time.time()
        middleware.request_history["127.0.0.1"][0] = current_time - 30

        # Should be rate limited with retry_after ~30 seconds
        response = await middleware.dispatch(mock_request, call_next)
        response_data = json.loads(response.body.decode())

        retry_after = response_data["error"]["details"]["retry_after"]
        assert 25 <= retry_after <= 35  # Allow some tolerance
