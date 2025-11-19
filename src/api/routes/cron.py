"""Cron endpoint for automated CDS data updates."""

import os
import asyncio
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, status
from pydantic import BaseModel

from src.config import settings
from src.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/cron",
    tags=["cron"],
)


class CronUpdateResponse(BaseModel):
    """Response model for cron update."""
    
    status: str
    message: str
    records_fetched: int
    records_inserted: int
    records_updated: int
    timestamp: datetime


async def run_cds_update() -> dict:
    """
    Run the CDS update process.
    
    This function calls the update_cds_investing logic asynchronously.
    
    Returns:
        Dictionary with update results
    """
    # Import here to avoid circular imports
    import sys
    from pathlib import Path
    
    # Ensure update_cds_investing can be imported
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        # Import async_main from update_cds_investing
        from update_cds_investing import async_main
        
        logger.info("Starting CDS data update via cron endpoint")
        
        # Run the update
        await async_main()
        
        # TODO: Return actual statistics from the update
        # For now, return a placeholder response
        return {
            "status": "success",
            "message": "CDS data updated successfully",
            "records_fetched": 0,  # TODO: capture from async_main
            "records_inserted": 0,
            "records_updated": 0,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        logger.error(f"Error during CDS update: {e}")
        raise


@router.post("/update-cds", response_model=CronUpdateResponse)
async def update_cds(
    authorization: Optional[str] = Header(None)
) -> CronUpdateResponse:
    """
    Trigger CDS data update.
    
    This endpoint is called by Vercel Cron to update CDS data daily.
    It verifies the Vercel Cron secret for security.
    
    Args:
        authorization: Vercel Cron secret from Authorization header
        
    Returns:
        Update result with statistics
        
    Raises:
        HTTPException: If authorization fails or update fails
    """
    # Verify Vercel Cron secret
    expected_secret = os.getenv("CRON_SECRET")
    
    if expected_secret:
        # Extract Bearer token from Authorization header
        if not authorization:
            logger.warning("Missing authorization header in cron request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authorization header"
            )
        
        # Check if it's a Bearer token
        if not authorization.startswith("Bearer "):
            logger.warning("Invalid authorization format in cron request")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization format"
            )
        
        token = authorization[7:]  # Remove "Bearer " prefix
        
        if token != expected_secret:
            logger.warning("Invalid cron secret provided")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization token"
            )
    else:
        logger.warning("CRON_SECRET not configured - endpoint is unprotected!")
    
    # Run the update
    try:
        result = await run_cds_update()
        logger.info(f"CDS update completed: {result['message']}")
        return CronUpdateResponse(**result)
    except Exception as e:
        logger.error(f"CDS update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Update failed: {str(e)}"
        )


@router.get("/health")
async def cron_health():
    """
    Health check endpoint for cron service.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "cron",
        "timestamp": datetime.utcnow()
    }
