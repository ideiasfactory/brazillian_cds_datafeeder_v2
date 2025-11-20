"""CSV Data Source for local development."""

import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from loguru import logger


class CSVDataSource:
    """
    CSV-based data source for local development.

    Provides similar interface to CDSRepository but reads/writes to CSV file.
    This allows development without database connection.
    """

    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize CSV data source.

        Args:
            csv_path: Path to CSV file. If None, uses default location.
        """
        if csv_path is None:
            # Default to data/brasil_CDS_historical.csv
            project_root = Path(__file__).parent.parent.parent
            csv_path = str(project_root / "data" / "brasil_CDS_historical.csv")

        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None
        self._load_csv()

    def _load_csv(self) -> None:
        """Load CSV file into DataFrame."""
        if os.path.exists(self.csv_path):
            try:
                self._df = pd.read_csv(self.csv_path, parse_dates=["date"])
                # Ensure date column is datetime
                self._df["date"] = pd.to_datetime(self._df["date"]).dt.date
                # Sort by date descending
                self._df = self._df.sort_values("date", ascending=False)
                logger.info(f"Loaded {len(self._df)} records from {self.csv_path}")
            except Exception as e:
                logger.error(f"Error loading CSV: {e}")
                self._df = pd.DataFrame(
                    columns=["date", "open", "high", "low", "close", "change_pct"]
                )
        else:
            logger.warning(f"CSV file not found: {self.csv_path}")
            self._df = pd.DataFrame(
                columns=["date", "open", "high", "low", "close", "change_pct"]
            )

    def _save_csv(self) -> None:
        """Save DataFrame to CSV file."""
        if self._df is None or self._df.empty:
            logger.warning("No data to save")
            return

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

            # Sort by date descending before saving
            df_to_save = self._df.sort_values("date", ascending=False)

            df_to_save.to_csv(self.csv_path, index=False)
            logger.info(f"Saved {len(df_to_save)} records to {self.csv_path}")
        except Exception as e:
            logger.error(f"Error saving CSV: {e}")
            raise

    def get_by_date(self, record_date: date) -> Optional[Dict[str, Any]]:
        """
        Get CDS record by specific date.

        Args:
            record_date: Date to query

        Returns:
            Dictionary with record data if found, None otherwise
        """
        if self._df is None or self._df.empty:
            return None

        matching = self._df[self._df["date"] == record_date]
        if matching.empty:
            return None

        return matching.iloc[0].to_dict()

    def get_latest(self, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Get the most recent CDS records.

        Args:
            limit: Number of records to return (default: 1)

        Returns:
            List of dictionaries with record data
        """
        if self._df is None or self._df.empty:
            return []

        # Already sorted by date descending
        latest_records = self._df.head(limit)
        return list(latest_records.to_dict(orient="records"))  # type: ignore[return-value]

    def get_date_range(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        order_by: str = "desc",
    ) -> List[Dict[str, Any]]:
        """
        Get CDS records within a date range.

        Args:
            start_date: Start date (inclusive), if None fetches from beginning
            end_date: End date (inclusive), if None fetches until last
            order_by: Sort order, "desc" or "asc" (default: "desc")

        Returns:
            List of dictionaries with record data
        """
        if self._df is None or self._df.empty:
            return []

        df_filtered = self._df.copy()

        if start_date:
            df_filtered = df_filtered[df_filtered["date"] >= start_date]
        if end_date:
            df_filtered = df_filtered[df_filtered["date"] <= end_date]

        # Apply ordering
        ascending = order_by.lower() == "asc"
        df_filtered = df_filtered.sort_values("date", ascending=ascending)

        return list(df_filtered.to_dict(orient="records"))  # type: ignore[return-value]

    def upsert_record(
        self, record_data: Dict[str, Any], source: str = "investing.com"
    ) -> Dict[str, Any]:
        """
        Insert or update a single CDS record.

        Args:
            record_data: Dictionary with keys: date, open, high, low, close, change_pct
            source: Data source identifier (stored but not used in CSV)

        Returns:
            Dictionary with record data after upsert

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ["date", "open", "high", "low", "close"]
        missing = [f for f in required_fields if f not in record_data]
        if missing:
            raise ValueError(f"Missing required fields: {missing}")

        record_date = record_data["date"]
        if isinstance(record_date, str):
            record_date = pd.to_datetime(record_date).date()

        # Check if record exists
        if self._df is not None and not self._df.empty:
            existing_idx = self._df[self._df["date"] == record_date].index
            if not existing_idx.empty:
                # Update existing record
                for key, value in record_data.items():
                    self._df.loc[existing_idx[0], key] = value
                logger.debug(f"Updated CDS record for date {record_date}")
            else:
                # Insert new record
                new_row = pd.DataFrame([record_data])
                new_row["date"] = pd.to_datetime(new_row["date"]).dt.date
                self._df = pd.concat([self._df, new_row], ignore_index=True)
                self._df = self._df.sort_values("date", ascending=False)
                logger.debug(f"Inserted CDS record for date {record_date}")
        else:
            # Create new DataFrame with first record
            self._df = pd.DataFrame([record_data])
            self._df["date"] = pd.to_datetime(self._df["date"]).dt.date
            logger.debug(f"Created CSV with first record for date {record_date}")

        self._save_csv()
        result = self.get_by_date(record_date)
        if result is None:
            raise RuntimeError(
                f"Failed to retrieve record after upsert for date {record_date}"
            )
        return result

    def bulk_insert(
        self,
        records: List[Dict[str, Any]],
        source: str = "investing.com",
        skip_duplicates: bool = False,
    ) -> Dict[str, int]:
        """
        Bulk insert CDS records with optional duplicate handling.

        Args:
            records: List of dictionaries with CDS data
            source: Data source identifier (stored but not used in CSV)
            skip_duplicates: If True, skip duplicates; if False, update them

        Returns:
            Dictionary with counts: {"inserted": N, "updated": M, "skipped": K}
        """
        if not records:
            return {"inserted": 0, "updated": 0, "skipped": 0}

        inserted = 0
        updated = 0
        skipped = 0

        for record in records:
            record_date = record["date"]
            if isinstance(record_date, str):
                record_date = pd.to_datetime(record_date).date()

            existing = self.get_by_date(record_date)

            if existing:
                if skip_duplicates:
                    skipped += 1
                else:
                    self.upsert_record(record, source)
                    updated += 1
            else:
                self.upsert_record(record, source)
                inserted += 1

        logger.info(
            f"Bulk insert completed: {inserted} inserted, "
            f"{updated} updated, {skipped} skipped"
        )

        return {"inserted": inserted, "updated": updated, "skipped": skipped}

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the CDS data.

        Returns:
            Dictionary with total_records, earliest_date, latest_date, sources
        """
        if self._df is None or self._df.empty:
            return {
                "total_records": 0,
                "earliest_date": None,
                "latest_date": None,
                "sources": [],
            }

        return {
            "total_records": len(self._df),
            "earliest_date": self._df["date"].min(),
            "latest_date": self._df["date"].max(),
            "sources": ["csv"],
        }

    def count_records(self) -> int:
        """
        Count total CDS records.

        Returns:
            Total number of records
        """
        if self._df is None:
            return 0
        return len(self._df)

    def delete_by_date_range(self, start_date: date, end_date: date) -> int:
        """
        Delete CDS records within a date range.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Number of deleted records
        """
        if self._df is None or self._df.empty:
            return 0

        initial_count = len(self._df)

        # Keep records outside the date range
        self._df = self._df[
            (self._df["date"] < start_date) | (self._df["date"] > end_date)
        ]

        deleted_count = initial_count - len(self._df)

        if deleted_count > 0:
            self._save_csv()
            logger.info(
                f"Deleted {deleted_count} records from {start_date} to {end_date}"
            )

        return deleted_count
