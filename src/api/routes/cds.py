"""CDS data API endpoints."""

from datetime import date, datetime, timedelta
from typing import Optional, List
import uuid
from fastapi import APIRouter, HTTPException, Query, Depends, status, Request

from src.database.connection import get_async_session
from src.database.repositories.cds_repository import CDSRepository
from src.api.models.cds import (
    StandardResponse,
    CDSRecordResponse,
    CDSListData,
    CDSLatestData,
    CDSStatisticsData
)
from src.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/cds",
    tags=["cds"],
)


def get_correlation_id(request: Request) -> str:
    """Get correlation_id from request state or generate new one."""
    return getattr(request.state, "correlation_id", str(uuid.uuid4()))


def parse_date_or_error(date_str: str, param_name: str, correlation_id: Optional[str] = None) -> date:
    """
    Parse date string or raise HTTPException.
    
    Args:
        date_str: Date string in format yyyy-MM-dd
        param_name: Name of the parameter for error message
        correlation_id: Correlation ID for logging
        
    Returns:
        Parsed date object
        
    Raises:
        HTTPException: If date format is invalid or date doesn't exist
    """
    try:
        # Try to parse the date
        parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        return parsed_date
    except ValueError as e:
        # Check if it's a format error or invalid date
        error_msg = str(e)
        
        if "does not match format" in error_msg:
            logger.warning(
                f"Invalid date format received for '{param_name}'",
                extra={
                    "correlation_id": correlation_id,
                    "param_name": param_name,
                    "invalid_value": date_str,
                    "error_type": "format_error",
                    "expected_format": "yyyy-MM-dd"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date format for '{param_name}'. Expected format: yyyy-MM-dd (e.g., 2025-01-15)"
            )
        else:
            # Invalid date like 2025-13-28 or 2025-02-30
            logger.warning(
                f"Invalid date value received for '{param_name}'",
                extra={
                    "correlation_id": correlation_id,
                    "param_name": param_name,
                    "invalid_value": date_str,
                    "error_type": "invalid_date",
                    "error_message": str(e)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid date value for '{param_name}': {date_str}. Please provide a valid date."
            )


@router.get("/latest", response_model=StandardResponse)
async def get_latest_cds(request: Request):
    """
    Get the most recent CDS record.
    
    Returns:
        Standardized response with latest CDS record
    """
    correlation_id = get_correlation_id(request)
    
    try:
        async with get_async_session() as session:
            repo = CDSRepository(session)
            records = await repo.get_latest(limit=1)
            
            if not records:
                logger.warning("No CDS records found in database", extra={"correlation_id": correlation_id})
                return StandardResponse(
                    status="success",
                    correlation_id=correlation_id,
                    data=CDSLatestData(
                        record=None,
                        message="No CDS data available"
                    ).model_dump(),
                    error_message=None,
                    timestamp=datetime.utcnow()
                )
            
            latest_record = records[0]
            logger.info(f"Retrieved latest CDS record: {latest_record.date}", extra={"correlation_id": correlation_id})
            
            return StandardResponse(
                status="success",
                correlation_id=correlation_id,
                data=CDSLatestData(
                    record=CDSRecordResponse.model_validate(latest_record),
                    message="Latest CDS record retrieved successfully"
                ).model_dump(),
                error_message=None,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Error retrieving latest CDS record: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve latest CDS record: {str(e)}"
        )


@router.get("", response_model=StandardResponse)
async def get_cds_records(
    request: Request,
    data_inicial: Optional[str] = Query(
        None,
        description="Start date in format yyyy-MM-dd (e.g., 2025-01-01)"
    ),
    data_final: Optional[str] = Query(
        None,
        description="End date in format yyyy-MM-dd (e.g., 2025-12-31)"
    ),
    order: str = Query(
        "desc",
        description="Sort order: 'asc' for ascending, 'desc' for descending"
    )
):
    """
    Get CDS records with optional date range filtering.
    
    **Date Range Logic:**
    - If both dates provided: returns records between the dates
    - If only `data_inicial` provided: returns records from that date + 30 days
    - If only `data_final` provided: returns records from 30 days before that date
    - If neither provided: returns all records
    
    **Date Format:**
    - Must be in format: yyyy-MM-dd (e.g., 2025-01-15)
    - Invalid formats return 400 error
    - Invalid dates (e.g., 2025-13-28) return 400 error
    
    Args:
        data_inicial: Start date (optional)
        data_final: End date (optional)
        order: Sort order - 'asc' or 'desc' (default: 'desc')
        
    Returns:
        List of CDS records with total count and date range info
    """
    correlation_id = get_correlation_id(request)
    
    # Validate order parameter
    if order not in ["asc", "desc"]:
        logger.warning(
            f"Invalid order parameter received",
            extra={
                "correlation_id": correlation_id,
                "param_name": "order",
                "invalid_value": order,
                "expected_values": ["asc", "desc"]
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order value: '{order}'. Must be 'asc' or 'desc'"
        )
    
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Parse and validate dates
    if data_inicial:
        start_date = parse_date_or_error(data_inicial, "data_inicial", correlation_id)
    
    if data_final:
        end_date = parse_date_or_error(data_final, "data_final", correlation_id)
    
    # Apply 30-day logic
    if start_date and not end_date:
        # Only start date provided: add 30 days
        end_date = start_date + timedelta(days=30)
        logger.info(
            f"Auto-calculated data_final: {end_date} (30 days after data_inicial)",
            extra={"correlation_id": correlation_id}
        )
    elif end_date and not start_date:
        # Only end date provided: subtract 30 days
        start_date = end_date - timedelta(days=30)
        logger.info(
            f"Auto-calculated data_inicial: {start_date} (30 days before data_final)",
            extra={"correlation_id": correlation_id}
        )
    
    # Validate date range
    if start_date and end_date and start_date > end_date:
        logger.warning(
            f"Invalid date range: data_inicial is after data_final",
            extra={
                "correlation_id": correlation_id,
                "data_inicial": start_date.isoformat(),
                "data_final": end_date.isoformat(),
                "error_type": "invalid_date_range"
            }
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"data_inicial ({start_date}) cannot be after data_final ({end_date})"
        )
    
    try:
        async with get_async_session() as session:
            repo = CDSRepository(session)
            
            # Get records
            records = await repo.get_date_range(
                start_date=start_date,
                end_date=end_date,
                order_by=order
            )
            
            # Prepare response
            total = len(records)
            
            date_range_info = None
            if records:
                dates = [r.date for r in records]
                date_range_info = {
                    "earliest": min(dates).isoformat(),
                    "latest": max(dates).isoformat(),
                    "requested_start": start_date.isoformat() if start_date else None,
                    "requested_end": end_date.isoformat() if end_date else None
                }
            
            logger.info(
                f"Retrieved {total} CDS records (start: {start_date}, end: {end_date}, order: {order})",
                extra={"correlation_id": correlation_id}
            )
            
            return StandardResponse(
                status="success",
                correlation_id=correlation_id,
                data=CDSListData(
                    total=total,
                    records=[CDSRecordResponse.model_validate(r) for r in records],
                    date_range=date_range_info
                ).model_dump(),
                error_message=None,
                timestamp=datetime.utcnow()
            )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving CDS records: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve CDS records: {str(e)}"
        )


@router.get("/statistics", response_model=StandardResponse)
async def get_cds_statistics(request: Request):
    """
    Get statistics about CDS data.
    
    Returns:
        Standardized response with statistics including total records, date range, and data sources
    """
    correlation_id = get_correlation_id(request)
    
    try:
        async with get_async_session() as session:
            repo = CDSRepository(session)
            stats = await repo.get_statistics()
            
            logger.info(
                f"Retrieved CDS statistics: {stats['total_records']} total records",
                extra={"correlation_id": correlation_id}
            )
            
            return StandardResponse(
                status="success",
                correlation_id=correlation_id,
                data=CDSStatisticsData(**stats).model_dump(),
                error_message=None,
                timestamp=datetime.utcnow()
            )
    except Exception as e:
        logger.error(f"Error retrieving CDS statistics: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve CDS statistics: {str(e)}"
        )
