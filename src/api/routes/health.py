from datetime import datetime
from time import time
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..models.health import HealthResponse, DatabaseStatus
from src.config import settings

router = APIRouter(prefix="/health", tags=["Health"])

# Track application start time for uptime calculation
_start_time = time()


async def get_database_status() -> DatabaseStatus:
    """
    Check database connection and gather status information.
    
    This function should be customized based on your actual database implementation.
    """
    # TODO: Implement actual database health check
    # This is a placeholder implementation
    try:
        # Add your database connection check here
        # For example:
        # async with get_db_connection() as conn:
        #     result = await conn.fetchone("SELECT COUNT(*) FROM cds_data")
        #     records_count = result[0]
        
        return DatabaseStatus(
            connected=True,
            type="postgresql",  # or "csv" based on your configuration
            latency_ms=None,  # Calculate actual latency
            records_count=None,  # Get from database
            last_updated=None  # Get from database
        )
    except Exception as e:
        return DatabaseStatus(
            connected=False,
            type="unknown",
            latency_ms=None,
            records_count=None,
            last_updated=None
        )


@router.get("/", response_model=HealthResponse, summary="Health Check")
async def health_check(
    db_status: DatabaseStatus = Depends(get_database_status)
) -> HealthResponse:
    """
    Get API health status.
    
    Returns comprehensive health information including:
    - Overall API status
    - Version and environment
    - Current timestamp and uptime
    - Database connection status
    
    Returns:
        HealthResponse: Detailed health information
    """
    uptime = time() - _start_time
    
    # Determine overall status based on database connection
    if db_status.connected:
        status = "healthy"
    else:
        status = "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.api_version,
        environment=settings.environment,
        timestamp=datetime.utcnow(),
        uptime_seconds=uptime,
        database=db_status
    )


@router.get("/liveness", summary="Liveness Probe")
async def liveness_check() -> JSONResponse:
    """
    Simple liveness check for container orchestration.
    
    Returns 200 if the service is running, regardless of dependencies.
    Useful for Kubernetes liveness probes.
    
    Returns:
        JSONResponse: Simple alive status
    """
    return JSONResponse(
        status_code=200,
        content={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    )


@router.get("/readiness", summary="Readiness Probe")
async def readiness_check(
    db_status: DatabaseStatus = Depends(get_database_status)
) -> JSONResponse:
    """
    Readiness check for container orchestration.
    
    Returns 200 if the service is ready to accept traffic (database connected).
    Returns 503 if not ready. Useful for Kubernetes readiness probes.
    
    Returns:
        JSONResponse: Readiness status
    """
    if db_status.connected:
        return JSONResponse(
            status_code=200,
            content={
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected"
            }
        )
    else:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "disconnected"
            }
        )
