"""Unit tests for API Key authentication."""

import pytest
import secrets
from fastapi import HTTPException

from src.database.repositories.api_key_repository import APIKeyRepository


@pytest.mark.unit
@pytest.mark.auth
@pytest.mark.asyncio
class TestAPIKeyRepository:
    """Test API Key repository operations."""

    async def test_create_api_key(self, api_key_repository: APIKeyRepository):
        """Test creating a new API key."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Test Key", description="Test description"
        )

        assert api_key is not None
        assert len(api_key) == 43  # URL-safe base64 encoded 32 bytes
        assert record.name == "Test Key"
        assert record.description == "Test description"
        assert record.is_active is True
        assert record.request_count == 0

    async def test_validate_api_key_success(self, api_key_repository: APIKeyRepository):
        """Test validating a valid API key."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Valid Key", description="Test"
        )

        validated_record = await api_key_repository.validate_key(api_key)

        assert validated_record is not None
        assert validated_record.id == record.id
        assert validated_record.name == "Valid Key"
        assert validated_record.request_count == 1  # Should increment

    async def test_validate_api_key_invalid(self, api_key_repository: APIKeyRepository):
        """Test validating an invalid API key."""
        result = await api_key_repository.validate_key("invalid_key_123")

        assert result is None

    async def test_validate_api_key_revoked(self, api_key_repository: APIKeyRepository):
        """Test validating a revoked API key."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Revoked Key", description="Test"
        )

        # Revoke the key
        await api_key_repository.revoke_key(record.id)

        # Try to validate
        result = await api_key_repository.validate_key(api_key)

        assert result is None

    async def test_list_api_keys(self, api_key_repository: APIKeyRepository):
        """Test listing all API keys."""
        # Create multiple keys
        await api_key_repository.create_key(
            key=secrets.token_urlsafe(32), name="Key 1", description="Description 1"
        )
        await api_key_repository.create_key(
            key=secrets.token_urlsafe(32), name="Key 2", description="Description 2"
        )
        await api_key_repository.create_key(
            key=secrets.token_urlsafe(32), name="Key 3", description="Description 3"
        )

        keys = await api_key_repository.list_all()

        assert len(keys) == 3
        assert all(key.name in ["Key 1", "Key 2", "Key 3"] for key in keys)

    async def test_get_api_key_by_id(self, api_key_repository: APIKeyRepository):
        """Test getting API key by ID."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Test Key", description="Test"
        )

        retrieved = await api_key_repository.get_by_id(record.id)

        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.name == "Test Key"

    async def test_get_api_key_by_id_not_found(
        self, api_key_repository: APIKeyRepository
    ):
        """Test getting non-existent API key by ID."""
        result = await api_key_repository.get_by_id(99999)

        assert result is None

    async def test_revoke_api_key(self, api_key_repository: APIKeyRepository):
        """Test revoking an API key."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Test Key", description="Test"
        )

        success = await api_key_repository.revoke_key(record.id)

        assert success is True

        # Verify it's revoked
        updated = await api_key_repository.get_by_id(record.id)
        assert updated is not None
        assert updated.is_active is False

    async def test_delete_api_key(self, api_key_repository: APIKeyRepository):
        """Test deleting an API key."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Test Key", description="Test"
        )

        success = await api_key_repository.delete_key(record.id)

        assert success is True

        # Verify it's deleted
        deleted = await api_key_repository.get_by_id(record.id)
        assert deleted is None

    async def test_api_key_request_counter(self, api_key_repository: APIKeyRepository):
        """Test that request counter increments correctly."""
        api_key = secrets.token_urlsafe(32)
        record = await api_key_repository.create_key(
            key=api_key, name="Test Key", description="Test"
        )

        initial_count = record.request_count
        assert initial_count == 0

        # Validate 3 times
        for _ in range(3):
            await api_key_repository.validate_key(api_key)

        # Check count
        updated = await api_key_repository.get_by_id(record.id)
        assert updated is not None
        assert updated.request_count == 3


@pytest.mark.unit
def test_hash_key():
    """Test that hash_key produces consistent hashes."""
    from src.database.repositories.api_key_repository import APIKeyRepository

    key = "test_key_123"
    hash1 = APIKeyRepository.hash_key(key)
    hash2 = APIKeyRepository.hash_key(key)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64-char hex string

    # Different keys should produce different hashes
    hash3 = APIKeyRepository.hash_key("different_key")
    assert hash1 != hash3
