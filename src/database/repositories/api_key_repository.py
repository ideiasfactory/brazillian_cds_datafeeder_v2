"""API Key Repository for database operations."""

from datetime import datetime
from typing import Optional
import hashlib

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..models import APIKey


class APIKeyRepository:
    """
    Repository for API Key operations.

    Provides async CRUD operations for APIKey model.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    @staticmethod
    def hash_key(key: str) -> str:
        """
        Hash an API key using SHA-256.

        Args:
            key: Plain text API key

        Returns:
            Hashed key (hex digest)
        """
        return hashlib.sha256(key.encode()).hexdigest()

    async def validate_key(self, key: str) -> Optional[APIKey]:
        """
        Validate an API key and return the associated record if valid.

        Args:
            key: Plain text API key to validate

        Returns:
            APIKey record if valid, None otherwise
        """
        key_hash = self.hash_key(key)

        stmt = select(APIKey).where(
            and_(APIKey.key_hash == key_hash, APIKey.is_active == True)
        )

        result = await self.session.execute(stmt)
        api_key_record = result.scalar_one_or_none()

        if api_key_record is None:
            logger.warning(f"Invalid API key attempt: {key_hash[:8]}...")
            return None

        # Check expiration
        if (
            api_key_record.expires_at is not None
            and datetime.utcnow() > api_key_record.expires_at.replace(tzinfo=None)
        ):
            logger.warning(f"Expired API key used: {api_key_record.name}")
            return None

        # Update last used timestamp and increment counter
        api_key_record.last_used_at = datetime.utcnow()  # type: ignore[assignment]
        api_key_record.request_count += 1  # type: ignore[assignment]
        await self.session.commit()

        logger.info(
            f"Valid API key used: {api_key_record.name} (requests: {api_key_record.request_count})"
        )
        return api_key_record

    async def create_key(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> APIKey:
        """
        Create a new API key.

        Args:
            key: Plain text API key (will be hashed)
            name: Friendly name for the key
            description: Optional description
            expires_at: Optional expiration datetime

        Returns:
            Created APIKey record
        """
        key_hash = self.hash_key(key)

        api_key = APIKey(
            key_hash=key_hash,
            name=name,
            description=description,
            expires_at=expires_at,
            is_active=True,
        )

        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)

        logger.info(f"API key created: {name} (id={api_key.id})")
        return api_key

    async def get_by_id(self, key_id: int) -> Optional[APIKey]:
        """
        Get API key by ID.

        Args:
            key_id: API key ID

        Returns:
            APIKey record if found, None otherwise
        """
        stmt = select(APIKey).where(APIKey.id == key_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[APIKey]:
        """
        Get API key by name.

        Args:
            name: API key name

        Returns:
            APIKey record if found, None otherwise
        """
        stmt = select(APIKey).where(APIKey.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self, include_inactive: bool = False) -> list[APIKey]:
        """
        List all API keys.

        Args:
            include_inactive: If True, includes inactive keys

        Returns:
            List of APIKey records
        """
        stmt = select(APIKey)

        if not include_inactive:
            stmt = stmt.where(APIKey.is_active == True)

        stmt = stmt.order_by(APIKey.created_at.desc())

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def revoke_key(self, key_id: int) -> bool:
        """
        Revoke (deactivate) an API key.

        Args:
            key_id: API key ID to revoke

        Returns:
            True if key was revoked, False if not found
        """
        api_key = await self.get_by_id(key_id)

        if api_key is None:
            return False

        api_key.is_active = False  # type: ignore[assignment]
        await self.session.commit()

        logger.info(f"API key revoked: {api_key.name} (id={key_id})")
        return True

    async def delete_key(self, key_id: int) -> bool:
        """
        Permanently delete an API key.

        Args:
            key_id: API key ID to delete

        Returns:
            True if key was deleted, False if not found
        """
        api_key = await self.get_by_id(key_id)

        if api_key is None:
            return False

        await self.session.delete(api_key)
        await self.session.commit()

        logger.info(f"API key deleted: {api_key.name} (id={key_id})")
        return True
