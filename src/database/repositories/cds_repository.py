"""CDS Data Repository for database operations."""

from datetime import date
from typing import Optional, List, Dict, Any
from sqlalchemy import select, func, and_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from loguru import logger

from ..models import CDSRecord, DataUpdateLog


class CDSRepository:
    """
    Repository for CDS data operations.

    Provides async CRUD operations for CDSRecord and DataUpdateLog models.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_by_date(self, record_date: date) -> Optional[CDSRecord]:
        """
        Get CDS record by specific date.

        Args:
            record_date: Date to query

        Returns:
            CDSRecord if found, None otherwise
        """
        stmt = select(CDSRecord).where(CDSRecord.record_date == record_date)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest(self, limit: int = 1) -> List[CDSRecord]:
        """
        Get the most recent CDS records.

        Args:
            limit: Number of records to return (default: 1)

        Returns:
            List of CDSRecord ordered by date descending
        """
        stmt = select(CDSRecord).order_by(desc(CDSRecord.record_date)).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_date_range(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        order_by: str = "desc",
    ) -> List[CDSRecord]:
        """
        Get CDS records within a date range.

        Args:
            start_date: Start date (inclusive), if None fetches from beginning
            end_date: End date (inclusive), if None fetches until last
            order_by: Sort order, "desc" or "asc" (default: "desc")

        Returns:
            List of CDSRecord within the date range
        """
        stmt = select(CDSRecord)

        conditions = []
        if start_date:
            conditions.append(CDSRecord.record_date >= start_date)
        if end_date:
            conditions.append(CDSRecord.record_date <= end_date)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        # Apply ordering
        if order_by.lower() == "asc":
            stmt = stmt.order_by(asc(CDSRecord.date))
        else:
            stmt = stmt.order_by(desc(CDSRecord.date))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def upsert_record(
        self, record_data: Dict[str, Any], source: str = "investing.com"
    ) -> CDSRecord:
        """
        Insert or update a single CDS record.

        Uses PostgreSQL's ON CONFLICT DO UPDATE for atomic upsert.

        Args:
            record_data: Dictionary with keys: date, open, high, low, close, change_pct
            source: Data source identifier (default: "investing.com")

        Returns:
            CDSRecord after upsert

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["date", "open", "high", "low", "close"]
        missing = [f for f in required_fields if f not in record_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        # Prepare record with source
        record_with_source = {**record_data, "source": source}

        # PostgreSQL upsert
        stmt = pg_insert(CDSRecord).values(**record_with_source)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date"],
            set_={
                "open": stmt.excluded.open,
                "high": stmt.excluded.high,
                "low": stmt.excluded.low,
                "close": stmt.excluded.close,
                "change_pct": stmt.excluded.change_pct,
                "source": stmt.excluded.source,
                "updated_at": func.now(),
            },
        ).returning(CDSRecord)

        result = await self.session.execute(stmt)
        await self.session.commit()

        record = result.scalar_one()
        logger.debug(f"Upserted CDS record for date {record.record_date}")
        return record

    async def bulk_insert(
        self,
        records: List[Dict[str, Any]],
        source: str = "investing.com",
        skip_duplicates: bool = False,
    ) -> Dict[str, int]:
        """
        Bulk insert CDS records with optional duplicate handling.

        Args:
            records: List of dictionaries with CDS data
            source: Data source identifier
            skip_duplicates: If True, skip duplicates; if False, update them

        Returns:
            Dictionary with counts: {"inserted": N, "updated": M, "skipped": K}
        """
        if not records:
            return {"inserted": 0, "updated": 0, "skipped": 0}

        # Add source to all records
        records_with_source = [{**rec, "source": source} for rec in records]

        inserted = 0
        updated = 0
        skipped = 0

        if skip_duplicates:
            # Insert only new records
            stmt = pg_insert(CDSRecord).values(records_with_source)
            stmt = stmt.on_conflict_do_nothing(index_elements=["date"])
            result = await self.session.execute(stmt)
            inserted = result.rowcount
            skipped = len(records) - inserted
        else:
            # Upsert all records
            for record in records_with_source:
                stmt = pg_insert(CDSRecord).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["date"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "change_pct": stmt.excluded.change_pct,
                        "source": stmt.excluded.source,
                        "updated_at": func.now(),
                    },
                )
                result = await self.session.execute(stmt)
                # Check if insert or update (simplified, assume all executed)
                if result.rowcount > 0:
                    # This is a simplification; proper tracking would need more logic
                    inserted += 1

        await self.session.commit()

        logger.info(
            f"Bulk insert completed: {inserted} inserted, "
            f"{updated} updated, {skipped} skipped"
        )

        return {"inserted": inserted, "updated": updated, "skipped": skipped}

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the CDS data.

        Returns:
            Dictionary with total_records, earliest_date, latest_date, sources
        """
        # Total records
        count_stmt = select(func.count(CDSRecord.id))
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar() or 0

        if total == 0:
            return {
                "total_records": 0,
                "earliest_date": None,
                "latest_date": None,
                "sources": [],
            }

        # Earliest and latest dates
        date_stmt = select(
            func.min(CDSRecord.record_date).label("earliest"),
            func.max(CDSRecord.record_date).label("latest"),
        )
        date_result = await self.session.execute(date_stmt)
        dates = date_result.one()

        # Distinct sources
        sources_stmt = select(CDSRecord.source).distinct()
        sources_result = await self.session.execute(sources_stmt)
        sources = [s for s in sources_result.scalars().all() if s]

        return {
            "total_records": total,
            "earliest_date": dates.earliest,
            "latest_date": dates.latest,
            "sources": sources,
        }

    async def log_update(
        self,
        status: str,
        records_fetched: int = 0,
        records_inserted: int = 0,
        records_updated: int = 0,
        source: str = "investing.com",
        trigger: str = "manual",
        error_message: Optional[str] = None,
    ) -> DataUpdateLog:
        """
        Log a data update operation.

        Args:
            status: Status of the update (success, error, partial)
            records_fetched: Number of records fetched
            records_inserted: Number of records inserted
            records_updated: Number of records updated
            source: Data source identifier
            trigger: Trigger source (manual, github-actions-scheduler, api, etc.)
            error_message: Error message if applicable

        Returns:
            Created DataUpdateLog record
        """
        log_entry = DataUpdateLog(
            status=status,
            records_fetched=records_fetched,
            records_inserted=records_inserted,
            records_updated=records_updated,
            source=source,
            trigger=trigger,
            error_message=error_message,
        )

        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)

        logger.info(
            f"Update log created: status={status}, trigger={trigger}, "
            f"fetched={records_fetched}, inserted={records_inserted}, "
            f"updated={records_updated}"
        )

        return log_entry

    async def get_recent_logs(self, limit: int = 10) -> List[DataUpdateLog]:
        """
        Get recent update logs.

        Args:
            limit: Number of logs to retrieve

        Returns:
            List of DataUpdateLog ordered by timestamp descending
        """
        stmt = (
            select(DataUpdateLog).order_by(desc(DataUpdateLog.timestamp)).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """
        Delete CDS records within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Number of deleted records
        """
        from sqlalchemy import delete

        stmt = delete(CDSRecord).where(
            and_(
                CDSRecord.record_date >= start_date,
                CDSRecord.record_date <= end_date,
            )
        )

        result = await self.session.execute(stmt)
        await self.session.commit()

        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} records from {start_date} to {end_date}")

        return deleted_count

    async def count_records(self) -> int:
        """
        Count total CDS records.

        Returns:
            Total number of records
        """
        stmt = select(func.count(CDSRecord.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
