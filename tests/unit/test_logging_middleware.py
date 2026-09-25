"""Unit tests for logging middleware."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from apps.core.middleware.logging import LoggingMiddleware


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware class."""

    def test_middleware_inherits_from_base_http_middleware(self):
        """Test that LoggingMiddleware inherits from BaseHTTPMiddleware."""
        middleware = LoggingMiddleware(app=MagicMock())
        assert isinstance(middleware, BaseHTTPMiddleware)

    def test_middleware_requires_app(self):
        """Test that middleware requires an app parameter."""
        with pytest.raises(TypeError):
            LoggingMiddleware()

    @pytest.mark.asyncio
    async def test_request_id_generation(self):
        """Test that middleware generates unique request IDs."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        # Create mock request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        # Create mock response
        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ):
            await middleware.dispatch(mock_request, call_next)

        # Verify request ID was generated and stored
        assert hasattr(mock_request.state, "request_id")
        assert mock_request.state.request_id is not None
        assert len(mock_request.state.request_id) > 0

    @pytest.mark.asyncio
    async def test_request_id_unique(self):
        """Test that each request gets a unique request ID."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        request_ids = []

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ):
            for _ in range(5):
                mock_request.state = MagicMock()
                await middleware.dispatch(mock_request, call_next)
                request_ids.append(mock_request.state.request_id)

        # All request IDs should be unique
        assert len(set(request_ids)) == 5

    @pytest.mark.asyncio
    async def test_log_request_start_called(self):
        """Test that _log_request_start is called with correct parameters."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start") as mock_log_start, patch.object(
            middleware, "_log_request_complete"
        ):
            await middleware.dispatch(mock_request, call_next)

            # Verify _log_request_start was called
            mock_log_start.assert_called_once()
            call_args = mock_log_start.call_args
            assert call_args[0][0] == mock_request
            assert len(call_args[0][1]) > 0  # request_id should be a non-empty string

    @pytest.mark.asyncio
    async def test_log_request_complete_called(self):
        """Test that _log_request_complete is called with correct parameters."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ) as mock_log_complete:
            await middleware.dispatch(mock_request, call_next)

            # Verify _log_request_complete was called
            mock_log_complete.assert_called_once()
            call_args = mock_log_complete.call_args
            assert call_args[0][0] == mock_request
            assert len(call_args[0][1]) > 0  # request_id
            assert call_args[0][2] == 200  # status_code
            assert call_args[0][3] >= 0  # processing_time_ms

    @pytest.mark.asyncio
    async def test_log_request_error_called_on_exception(self):
        """Test that _log_request_error is called when an exception occurs."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        async def call_next(request):
            raise ValueError("Test error")

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_error"
        ) as mock_log_error:
            with pytest.raises(ValueError):
                await middleware.dispatch(mock_request, call_next)

            # Verify _log_request_error was called
            mock_log_error.assert_called_once()
            call_args = mock_log_error.call_args
            assert call_args[0][0] == mock_request
            assert len(call_args[0][1]) > 0  # request_id
            assert "Test error" in call_args[0][2]  # error message
            assert call_args[0][3] >= 0  # processing_time_ms

    def test_log_request_start_format(self):
        """Test that _log_request_start logs in correct JSON format."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_start(mock_request, "test-request-id")

            # Verify logger.info was called
            mock_logger.info.assert_called_once()

            # Verify the log data is valid JSON
            log_call_arg = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify log structure
            assert log_data["level"] == "INFO"
            assert log_data["request_id"] == "test-request-id"
            assert log_data["message"] == "Request started"
            assert log_data["context"]["method"] == "POST"
            assert log_data["context"]["path"] == "/api/messages"
            assert log_data["context"]["client_host"] == "127.0.0.1"
            assert "timestamp" in log_data

    def test_log_request_complete_format(self):
        """Test that _log_request_complete logs in correct JSON format."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_complete(mock_request, "test-request-id", 200, 123.45)

            # Verify logger.info was called
            mock_logger.info.assert_called_once()

            # Verify the log data is valid JSON
            log_call_arg = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify log structure
            assert log_data["level"] == "INFO"
            assert log_data["request_id"] == "test-request-id"
            assert log_data["message"] == "Request completed"
            assert log_data["context"]["method"] == "POST"
            assert log_data["context"]["path"] == "/api/messages"
            assert log_data["context"]["status_code"] == 200
            assert log_data["context"]["processing_time_ms"] == 123.45
            assert "timestamp" in log_data

    def test_log_request_error_format(self):
        """Test that _log_request_error logs in correct JSON format."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_error(mock_request, "test-request-id", "Test error", 123.45)

            # Verify logger.error was called
            mock_logger.error.assert_called_once()

            # Verify the log data is valid JSON
            log_call_arg = mock_logger.error.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify log structure
            assert log_data["level"] == "ERROR"
            assert log_data["request_id"] == "test-request-id"
            assert log_data["message"] == "Request failed"
            assert log_data["context"]["method"] == "POST"
            assert log_data["context"]["path"] == "/api/messages"
            assert log_data["context"]["error"] == "Test error"
            assert log_data["context"]["processing_time_ms"] == 123.45
            assert "timestamp" in log_data

            # Verify exc_info=True was passed for stack trace
            assert mock_logger.error.call_args[1]["exc_info"] is True

    def test_log_request_start_no_message_content(self):
        """Test that request start logs do not contain message content."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_start(mock_request, "test-request-id")

            log_call_arg = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify no message content is logged
            assert "message" not in log_data["context"]
            assert "body" not in log_data["context"]
            assert "content" not in log_data["context"]

    def test_log_request_complete_no_message_content(self):
        """Test that request complete logs do not contain message content."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_complete(mock_request, "test-request-id", 200, 123.45)

            log_call_arg = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify no message content is logged
            assert "message" not in log_data["context"]
            assert "body" not in log_data["context"]
            assert "content" not in log_data["context"]

    def test_log_request_error_no_message_content(self):
        """Test that request error logs do not contain message content."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_error(mock_request, "test-request-id", "Test error", 123.45)

            log_call_arg = mock_logger.error.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify no message content is logged
            assert "message" not in log_data["context"]
            assert "body" not in log_data["context"]
            assert "content" not in log_data["context"]

    @pytest.mark.asyncio
    async def test_processing_time_tracking(self):
        """Test that processing time is tracked correctly."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ) as mock_log_complete:
            await middleware.dispatch(mock_request, call_next)

            # Verify processing time was passed to _log_request_complete
            call_args = mock_log_complete.call_args
            assert call_args[0][3] >= 0  # processing_time_ms should be non-negative

    @pytest.mark.asyncio
    async def test_handles_none_client(self):
        """Test that middleware handles requests with no client info."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = None
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ):
            # Should not raise an exception
            await middleware.dispatch(mock_request, call_next)

    def test_log_request_start_with_none_client(self):
        """Test that _log_request_start handles None client correctly."""
        middleware = LoggingMiddleware(app=MagicMock())

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = None

        with patch("apps.core.middleware.logging.logger") as mock_logger:
            middleware._log_request_start(mock_request, "test-request-id")

            log_call_arg = mock_logger.info.call_args[0][0]
            log_data = json.loads(log_call_arg)

            # Verify client_host is None when client is None
            assert log_data["context"]["client_host"] is None

    @pytest.mark.asyncio
    async def test_exception_propagates_after_logging(self):
        """Test that exceptions are propagated after error logging."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        async def call_next(request):
            raise ValueError("Test error")

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_error"
        ):
            with pytest.raises(ValueError, match="Test error"):
                await middleware.dispatch(mock_request, call_next)

    @pytest.mark.asyncio
    async def test_response_returned_successfully(self):
        """Test that response is returned successfully on normal flow."""
        mock_app = AsyncMock()
        middleware = LoggingMiddleware(app=mock_app)

        mock_request = MagicMock(spec=Request)
        mock_request.method = "POST"
        mock_request.url.path = "/api/messages"
        mock_request.client = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.state = MagicMock()

        mock_response = MagicMock(spec=Response)
        mock_response.status_code = 200

        async def call_next(request):
            return mock_response

        with patch.object(middleware, "_log_request_start"), patch.object(
            middleware, "_log_request_complete"
        ):
            response = await middleware.dispatch(mock_request, call_next)

            # Verify the response is returned
            assert response is mock_response
