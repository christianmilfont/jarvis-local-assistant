"""Integration tests for API contract compliance."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.core.api.messages import router
from apps.core.models.error import ProviderError, ProviderTimeoutError
from apps.core.services.message_service import MessageService


@pytest.fixture
def app():
    """Create a test FastAPI application with the messages router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


class TestMessageAPIContract:
    """Tests for API contract compliance."""

    def test_post_api_messages_success(self, client):
        """Test successful message submission returns correct response format."""
        response = client.post(
            "/api/messages",
            json={"message": "Hello JARVIS"},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["status"] == "success"
        assert "data" in data
        assert "message_id" in data["data"]
        assert "response" in data["data"]
        assert "processing_time_ms" in data["data"]
        assert "timestamp" in data["data"]

        # Verify data types
        assert isinstance(data["data"]["message_id"], str)
        assert isinstance(data["data"]["response"], str)
        assert isinstance(data["data"]["processing_time_ms"], int)
        assert isinstance(data["data"]["timestamp"], str)

    def test_post_api_messages_with_metadata(self, client):
        """Test message submission with metadata."""
        response = client.post(
            "/api/messages",
            json={
                "message": "Hello JARVIS",
                "metadata": {"source": "test", "user_id": "user123"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_with_timestamp(self, client):
        """Test message submission with timestamp."""
        response = client.post(
            "/api/messages",
            json={"message": "Hello JARVIS", "timestamp": "2025-09-24T12:00:00Z"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_empty_message(self, client):
        """Test that empty message returns validation error."""
        response = client.post("/api/messages", json={"message": ""})

        # Pydantic returns 422 for validation errors
        assert response.status_code == 422
        data = response.json()

        # Verify error structure
        assert "detail" in data

    def test_post_api_messages_whitespace_only(self, client):
        """Test that whitespace-only message returns validation error."""
        response = client.post("/api/messages", json={"message": "   "})

        # Pydantic returns 422 for validation errors
        assert response.status_code == 422
        data = response.json()

        assert "detail" in data

    def test_post_api_messages_too_long(self, client):
        """Test that message exceeding max length returns validation error."""
        long_message = "a" * 1001
        response = client.post("/api/messages", json={"message": long_message})

        # Pydantic returns 422 for validation errors
        assert response.status_code == 422
        data = response.json()

        assert "detail" in data

    def test_post_api_messages_missing_message_field(self, client):
        """Test that missing message field returns validation error."""
        response = client.post("/api/messages", json={})

        assert response.status_code == 422  # FastAPI validation error

    def test_post_api_messages_invalid_json(self, client):
        """Test that invalid JSON returns parsing error."""
        response = client.post(
            "/api/messages",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422  # FastAPI validation error

    def test_post_api_messages_processing_time_included(self, client):
        """Test that processing time is included in response."""
        response = client.post("/api/messages", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()

        assert "processing_time_ms" in data["data"]
        assert data["data"]["processing_time_ms"] >= 0
        assert isinstance(data["data"]["processing_time_ms"], int)

    def test_post_api_messages_message_id_unique(self, client):
        """Test that each message gets a unique message ID."""
        response1 = client.post("/api/messages", json={"message": "Hello"})
        response2 = client.post("/api/messages", json={"message": "Hello"})

        data1 = response1.json()
        data2 = response2.json()

        assert data1["data"]["message_id"] != data2["data"]["message_id"]

    def test_post_api_messages_message_id_format(self, client):
        """Test that message ID is in UUID format."""
        response = client.post("/api/messages", json={"message": "Hello"})

        data = response.json()
        message_id = data["data"]["message_id"]

        # UUID format: 8-4-4-4-12 hex characters
        assert len(message_id) == 36
        assert message_id.count("-") == 4

    def test_post_api_messages_response_content(self, client):
        """Test that response contains actual content from provider."""
        response = client.post("/api/messages", json={"message": "Hello"})

        data = response.json()
        assert len(data["data"]["response"]) > 0
        assert isinstance(data["data"]["response"], str)

    def test_post_api_messages_unicode_support(self, client):
        """Test that endpoint handles unicode characters."""
        response = client.post("/api/messages", json={"message": "Hello 世界 🌍"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_content_type(self, client):
        """Test that endpoint returns JSON content type."""
        response = client.post("/api/messages", json={"message": "Hello"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

    def test_post_api_messages_provider_error_handling(self, client):
        """Test that provider errors are handled correctly."""
        # Mock the message service to raise ProviderError
        with patch.object(
            MessageService, "process_message", AsyncMock(side_effect=ProviderError("Test error"))
        ):
            response = client.post("/api/messages", json={"message": "Hello"})

            assert response.status_code == 503
            data = response.json()

            assert data["detail"]["code"] == "PROVIDER_ERROR"
            assert "provider" in data["detail"]["details"]
            assert data["detail"]["details"]["provider"] == "MockLLMProvider"

    def test_post_api_messages_provider_timeout_handling(self, client):
        """Test that provider timeouts are handled correctly."""
        # Mock the message service to raise ProviderTimeoutError
        with patch.object(
            MessageService,
            "process_message",
            AsyncMock(side_effect=ProviderTimeoutError("Test timeout")),
        ):
            response = client.post("/api/messages", json={"message": "Hello"})

            assert response.status_code == 504
            data = response.json()

            assert data["detail"]["code"] == "PROVIDER_TIMEOUT"
            assert "timeout_seconds" in data["detail"]["details"]

    def test_post_api_messages_internal_error_handling(self, client):
        """Test that unexpected errors are handled correctly."""
        # Mock the message service to raise unexpected error
        with patch.object(
            MessageService, "process_message", AsyncMock(side_effect=Exception("Unexpected error"))
        ):
            response = client.post("/api/messages", json={"message": "Hello"})

            assert response.status_code == 500
            data = response.json()

            assert data["detail"]["code"] == "INTERNAL_ERROR"
            assert "request_id" in data["detail"]["details"]

    def test_post_api_messages_max_length_boundary(self, client):
        """Test message at maximum length boundary."""
        max_message = "a" * 1000
        response = client.post("/api/messages", json={"message": max_message})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_min_length_boundary(self, client):
        """Test message at minimum length boundary."""
        min_message = "a"
        response = client.post("/api/messages", json={"message": min_message})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_special_characters(self, client):
        """Test that endpoint handles special characters."""
        special_message = "Hello! @#$%^&*()_+-=[]{}|;':\",./<>?"
        response = client.post("/api/messages", json={"message": special_message})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_timestamp_format_validation(self, client):
        """Test that invalid timestamp format is rejected."""
        response = client.post(
            "/api/messages", json={"message": "Hello", "timestamp": "invalid-timestamp"}
        )

        # Pydantic should reject invalid datetime format
        assert response.status_code == 422

    def test_post_api_messages_metadata_validation(self, client):
        """Test that metadata is correctly handled."""
        response = client.post(
            "/api/messages",
            json={
                "message": "Hello",
                "metadata": {"source": "web", "user_id": "test-user"},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    def test_post_api_messages_response_schema_compliance(self, client):
        """Test that response matches the specified schema."""
        response = client.post("/api/messages", json={"message": "Hello"})

        assert response.status_code == 200
        data = response.json()

        # Verify required fields exist
        required_fields = ["status", "data"]
        for field in required_fields:
            assert field in data

        # Verify data structure
        required_data_fields = ["message_id", "response", "processing_time_ms", "timestamp"]
        for field in required_data_fields:
            assert field in data["data"]

        # Verify status value
        assert data["status"] == "success"

    def test_post_api_messages_error_response_schema_compliance(self, client):
        """Test that error responses match the specified schema."""
        response = client.post("/api/messages", json={"message": ""})

        # Pydantic returns 422 for validation errors
        assert response.status_code == 422
        data = response.json()

        # Verify error response structure
        assert "detail" in data

    def test_post_api_messages_method_not_allowed(self, client):
        """Test that non-POST methods are not allowed."""
        response = client.get("/api/messages")

        assert response.status_code == 405  # Method Not Allowed

    def test_post_api_messages_wrong_content_type(self, client):
        """Test that wrong content type is handled."""
        response = client.post(
            "/api/messages",
            data="message=Hello",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        assert response.status_code == 422  # Validation error

    def test_post_api_messages_extra_fields_ignored(self, client):
        """Test that extra fields in request are ignored."""
        response = client.post(
            "/api/messages",
            json={"message": "Hello", "extra_field": "should_be_ignored"},
        )

        # Pydantic should ignore extra fields by default
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
