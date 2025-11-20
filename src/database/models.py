"""
Database models for Brazilian CDS Data Feeder.

SQLAlchemy ORM models for storing CDS historical data.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Float,
    Date,
    DateTime,
    Index,
    String,
    Boolean,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CDSRecord(Base):
    """
    Model for Brazilian CDS (Credit Default Swap) historical data.

    Stores daily OHLC (Open, High, Low, Close) data and percentage changes
    for Brazilian 5-year CDS spreads in USD.
    """

    __tablename__ = "cds_records"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Date (indexed for fast lookups)
    record_date = Column("date", Date, unique=True, nullable=False, index=True)

    # OHLC Data (all in basis points)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=False)  # Close price is mandatory

    # Change percentage from previous day
    change_pct = Column(Float, nullable=True)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Source tracking
    source = Column(String(50), default="investing.com", nullable=True)

    # Indexes for performance
    __table_args__ = (
        Index("idx_date_desc", record_date.desc()),  # For latest data queries
        Index("idx_date_range", record_date),  # For date range queries
    )

    def __repr__(self) -> str:
        return (
            f"<CDSRecord(date={self.record_date}, close={self.close}, "
            f"change_pct={self.change_pct})>"
        )

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "date": self.record_date.isoformat() if self.record_date else None,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "change_pct": self.change_pct,
            "created_at": (
                self.created_at.isoformat() if self.created_at is not None else None
            ),
            "updated_at": (
                self.updated_at.isoformat() if self.updated_at is not None else None
            ),
            "source": self.source,
        }


class DataUpdateLog(Base):
    """
    Model for tracking CDS data updates.

    Logs each update operation for monitoring and debugging.
    """

    __tablename__ = "data_update_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Update details
    started_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Status: pending, success, error
    status = Column(String(20), nullable=False, default="pending")

    # Statistics
    records_fetched = Column(Integer, nullable=True)
    records_inserted = Column(Integer, nullable=True)
    records_updated = Column(Integer, nullable=True)

    # Error tracking
    error_message = Column(String(500), nullable=True)

    # Source
    source = Column(String(50), default="investing.com", nullable=True)
    trigger = Column(String(50), nullable=True)  # manual, cron, api

    def __repr__(self) -> str:
        return f"<DataUpdateLog(id={self.id}, status={self.status}, started_at={self.started_at})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "started_at": (
                self.started_at.isoformat() if self.started_at is not None else None
            ),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at is not None else None
            ),
            "status": self.status,
            "records_fetched": self.records_fetched,
            "records_inserted": self.records_inserted,
            "records_updated": self.records_updated,
            "error_message": self.error_message,
            "source": self.source,
            "trigger": self.trigger,
        }


class APIKey(Base):
    """
    Model for API Key management.

    Stores API keys for authentication and tracks usage.
    """

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # API Key (hashed with SHA-256)
    key_hash = Column(String(64), unique=True, nullable=False, index=True)

    # Key metadata
    name = Column(
        String(100), nullable=False
    )  # Friendly name (e.g., "GitHub Actions", "Production App")
    description = Column(Text, nullable=True)  # Optional description

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiration
    last_used_at = Column(DateTime(timezone=True), nullable=True)  # Track last usage

    # Usage tracking
    request_count = Column(
        Integer, default=0, nullable=False
    )  # Total requests made with this key

    # Indexes for performance
    __table_args__ = (
        Index("idx_key_hash_active", key_hash, is_active),
        Index("idx_expires_at", expires_at),
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name='{self.name}', is_active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": (
                self.created_at.isoformat() if self.created_at is not None else None
            ),
            "expires_at": (
                self.expires_at.isoformat() if self.expires_at is not None else None
            ),
            "last_used_at": (
                self.last_used_at.isoformat() if self.last_used_at is not None else None
            ),
            "request_count": self.request_count,
        }

    def is_expired(self) -> bool:
        """Check if the API key is expired."""
        if self.expires_at is None:
            return False
        return bool(datetime.now(self.expires_at.tzinfo) > self.expires_at)

    def is_valid(self) -> bool:
        """Check if the API key is valid (active and not expired)."""
        return bool(self.is_active) and not self.is_expired()
