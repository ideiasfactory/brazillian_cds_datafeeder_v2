"""
Script utilitário para atualizar dados CDS do Investing.com.

Este script executa o processo de atualização de dados CDS do Investing.com,
salvando no banco de dados (produção) ou CSV (desenvolvimento).

Usage:
    python scripts/update_cds_data.py
    python scripts/update_cds_data.py --force-csv  # Força uso de CSV mesmo em produção
    python scripts/update_cds_data.py --force-db   # Força uso de database mesmo em desenvolvimento
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
import argparse
from typing import Optional

from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import settings


def setup_logger():
    """Configure logger for the script."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
    )

async def run_update(force_mode: Optional[str] = None):
    """
    Execute CDS data update.
    
    Args:
        force_mode: "csv" to force CSV mode, "db" to force database mode, None for auto
    """
    # Import here to avoid circular imports and ensure logging is configured
    from update_cds_investing import fetch_investing_cds, save_to_database, save_to_csv
    
    # Determine storage mode
    use_database = bool(settings.database_url and settings.environment == "production")
    
    if force_mode == "csv":
        use_database = False
        logger.warning("Forcing CSV storage mode")
    elif force_mode == "db":
        if not settings.database_url:
            logger.error("Cannot force database mode: DATABASE_URL not configured")
            return False
        use_database = True
        logger.warning("Forcing database storage mode")
    
    if use_database:
        logger.info("Using database storage (production mode)")
    else:
        logger.info("Using CSV storage (development mode)")
    
    # Fetch data from Investing.com
    try:
        logger.info("Fetching data from Investing.com...")
        df_new = fetch_investing_cds()
        logger.success(f"✓ Fetched {len(df_new)} records from Investing.com")
        
        # Show date range
        if not df_new.empty:
            min_date = df_new['date'].min()
            max_date = df_new['date'].max()
            logger.info(f"Date range: {min_date} to {max_date}")
    except Exception as e:
        logger.error(f"✗ Failed to fetch data from Investing.com: {e}")
        return False
    
    # Save data
    try:
        if use_database:
            logger.info("Saving to database...")
            await save_to_database(df_new)
            logger.success("✓ Data saved to database successfully")
        else:
            logger.info("Saving to CSV...")
            save_to_csv(df_new)
            logger.success("✓ Data saved to CSV successfully")
        
        return True
    except Exception as e:
        logger.error(f"✗ Failed to save data: {e}")
        return False


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Update CDS data from Investing.com"
    )
    parser.add_argument(
        "--force-csv",
        action="store_true",
        help="Force CSV storage mode (ignore environment setting)"
    )
    parser.add_argument(
        "--force-db",
        action="store_true",
        help="Force database storage mode (ignore environment setting)"
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help="Reduce output verbosity"
    )
    
    args = parser.parse_args()
    
    # Setup logger
    setup_logger()
    
    if not args.silent:
        logger.info("=" * 60)
        logger.info("CDS Data Update Utility")
        logger.info("=" * 60)
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Database configured: {'Yes' if settings.database_url else 'No'}")
        logger.info("")
    
    # Validate arguments
    if args.force_csv and args.force_db:
        logger.error("Cannot use --force-csv and --force-db together")
        sys.exit(1)
    
    force_mode = None
    if args.force_csv:
        force_mode = "csv"
    elif args.force_db:
        force_mode = "db"
    
    # Run update
    start_time = datetime.now()
    success = await run_update(force_mode=force_mode)
    duration = (datetime.now() - start_time).total_seconds()
    
    if not args.silent:
        logger.info("")
        logger.info("=" * 60)
    
    if success:
        logger.success(f"✓ Update completed successfully in {duration:.2f}s")
        sys.exit(0)
    else:
        logger.error(f"✗ Update failed after {duration:.2f}s")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
