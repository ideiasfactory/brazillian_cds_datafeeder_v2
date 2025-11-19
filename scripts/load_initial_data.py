"""
Script to load initial historical CDS data from CSV into database.

This script reads brasil_CDS_historical.csv and bulk inserts the data
into the PostgreSQL database. It's meant to be run once after database
tables are created to initialize historical data.

Usage:
    python scripts/load_initial_data.py
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings
from src.database.connection import get_async_session
from src.database.repositories.cds_repository import CDSRepository


async def load_csv_to_database(csv_path: str, skip_duplicates: bool = False):
    """
    Load historical CDS data from CSV into database.
    
    Args:
        csv_path: Path to CSV file
        skip_duplicates: If True, skip existing records; if False, update them
    """
    logger.info(f"Loading data from {csv_path}")
    
    # Check if file exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        return
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path, parse_dates=["date"])
        logger.info(f"Read {len(df)} records from CSV")
        logger.info(f"Columns: {df.columns.tolist()}")
        logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    except Exception as e:
        logger.error(f"Error reading CSV: {e}")
        return
    
    # Convert DataFrame to list of dicts
    records = []
    for _, row in df.iterrows():
        record = {
            "date": row["date"].date() if isinstance(row["date"], pd.Timestamp) else row["date"],
            "open": float(row["open"]) if pd.notna(row["open"]) else None,
            "high": float(row["high"]) if pd.notna(row["high"]) else None,
            "low": float(row["low"]) if pd.notna(row["low"]) else None,
            "close": float(row["close"]) if pd.notna(row["close"]) else None,
            "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else None,
        }
        records.append(record)
    
    logger.info(f"Prepared {len(records)} records for insertion")
    
    # Insert into database
    try:
        async with get_async_session() as session:
            repo = CDSRepository(session)
            
            logger.info("Inserting records into database...")
            result = await repo.bulk_insert(
                records, 
                source="csv_import", 
                skip_duplicates=skip_duplicates
            )
            
            logger.success(
                f"Database loaded: {result['inserted']} inserted, "
                f"{result['updated']} updated, {result['skipped']} skipped"
            )
            
            # Log the import
            await repo.log_update(
                status="success",
                records_fetched=len(records),
                records_inserted=result["inserted"],
                records_updated=result["updated"],
                source="csv_import"
            )
            
            # Show database statistics
            stats = await repo.get_statistics()
            logger.info(
                f"Database statistics after import: {stats['total_records']} total records, "
                f"date range: {stats['earliest_date']} to {stats['latest_date']}"
            )
    except Exception as e:
        logger.error(f"Error inserting into database: {e}")
        raise


async def main():
    """Main function."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
    )
    
    logger.info("=" * 60)
    logger.info("CDS Historical Data Loader")
    logger.info("=" * 60)
    
    # Check database configuration
    if not settings.database_url:
        logger.error("DATABASE_URL not configured in environment")
        logger.error("Please set DATABASE_URL in .env file")
        return
    
    logger.info(f"Database: {settings.database_url[:50]}...")
    logger.info(f"Environment: {settings.environment}")
    
    # Path to CSV file
    csv_path = project_root / "data" / "brasil_CDS_historical.csv"
    
    # Ask for confirmation
    logger.warning("This will load historical data into the database.")
    logger.warning(f"CSV file: {csv_path}")
    
    response = input("Do you want to proceed? [y/N]: ").strip().lower()
    if response != "y":
        logger.info("Operation cancelled by user")
        return
    
    # Ask about duplicate handling
    response = input("Skip duplicates (y) or update them (n)? [y/N]: ").strip().lower()
    skip_duplicates = response == "y"
    
    logger.info("Starting data load...")
    await load_csv_to_database(str(csv_path), skip_duplicates=skip_duplicates)
    logger.success("Data load completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
