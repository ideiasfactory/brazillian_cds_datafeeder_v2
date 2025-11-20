"""Unit tests for database models."""

import pytest
from datetime import datetime, timezone, timedelta

from src.database.models import APIKey


@pytest.mark.unit
class TestAPIKeyModel:
    """Test APIKey model methods."""

    def test_api_key_to_dict(self):
        """Test converting APIKey to dictionary."""
        key = APIKey(
            id=1,
            key_hash="test_hash",
            name="Test Key",
            description="Test description",
            is_active=True,
            created_at=datetime.now(timezone.utc),
            request_count=10,
        )

        result = key.to_dict()

        assert result["id"] == 1
        assert result["name"] == "Test Key"
        assert result["description"] == "Test description"
        assert result["is_active"] is True
        assert result["request_count"] == 10
        assert "key_hash" not in result  # Should not expose hash
        assert "created_at" in result

    def test_api_key_is_expired_no_expiration(self):
        """Test is_expired when no expiration is set."""
        key = APIKey(id=1, key_hash="test_hash", name="Test Key", expires_at=None)

        assert key.is_expired() is False

    def test_api_key_is_expired_future_date(self):
        """Test is_expired with future expiration date."""
        future_date = datetime.now(timezone.utc) + timedelta(days=30)
        key = APIKey(
            id=1, key_hash="test_hash", name="Test Key", expires_at=future_date
        )

        assert key.is_expired() is False

    def test_api_key_is_expired_past_date(self):
        """Test is_expired with past expiration date."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        key = APIKey(id=1, key_hash="test_hash", name="Test Key", expires_at=past_date)

        assert key.is_expired() is True

    def test_api_key_is_valid_active_not_expired(self):
        """Test is_valid when key is active and not expired."""
        key = APIKey(
            id=1, key_hash="test_hash", name="Test Key", is_active=True, expires_at=None
        )

        assert key.is_valid() is True

    def test_api_key_is_valid_inactive(self):
        """Test is_valid when key is inactive."""
        key = APIKey(id=1, key_hash="test_hash", name="Test Key", is_active=False)

        assert key.is_valid() is False

    def test_api_key_is_valid_expired(self):
        """Test is_valid when key is expired."""
        past_date = datetime.now(timezone.utc) - timedelta(days=1)
        key = APIKey(
            id=1,
            key_hash="test_hash",
            name="Test Key",
            is_active=True,
            expires_at=past_date,
        )

        assert key.is_valid() is False
