from pathlib import Path
from datetime import datetime
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from src.api import health_router, home_router
from src.api.routes import cds as cds_router
from src.config import settings
from src.logging_config import get_logger, log_with_context

# Initialize logger
logger = get_logger(__name__)

# Log application startup
log_with_context(
    logger,
    'info',
    'Initializing Brazilian CDS Data Feeder API',
    version=settings.api_version,
    environment=settings.environment,
    betterstack_enabled=settings.betterstack_enabled
)

# Create FastAPI application
app = FastAPI(
    title="Brazilian CDS Data Feeder",
    description="Credit Default Swap Historical Data API",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom exception handler for HTTPException to return standardized error format."""
    
    # Get correlation_id from request state
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Determine status type based on status code
    if 400 <= exc.status_code < 500:
        status_type = "client_error"
    elif 500 <= exc.status_code < 600:
        status_type = "error"
    else:
        status_type = "error"
    
    # Get query parameters to log invalid data
    query_params = dict(request.query_params) if request.query_params else {}
    
    log_with_context(
        logger,
        'warning' if status_type == "client_error" else 'error',
        f"HTTP Exception: {exc.detail}",
        correlation_id=correlation_id,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method,
        query_params=query_params if query_params else None
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": status_type,
            "correlation_id": correlation_id,
            "data": None,
            "error_message": exc.detail,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Custom exception handler for request validation errors."""
    
    # Get correlation_id from request state
    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))
    
    # Format validation errors in a friendly way
    errors = exc.errors()
    error_messages = []
    error_details = []
    
    for error in errors:
        field = " -> ".join(str(loc) for loc in error["loc"])
        msg = error["msg"]
        error_messages.append(f"{field}: {msg}")
        error_details.append({
            "field": field,
            "message": msg,
            "input": error.get("input"),
            "type": error.get("type")
        })
    
    error_detail = "; ".join(error_messages)
    
    # Get query parameters and body to log invalid data
    query_params = dict(request.query_params) if request.query_params else {}
    
    log_with_context(
        logger,
        'warning',
        f"Validation error: {error_detail}",
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
        query_params=query_params if query_params else None,
        validation_errors=error_details
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "client_error",
            "correlation_id": correlation_id,
            "data": None,
            "error_message": f"Validation error: {error_detail}",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests with timing."""
    start_time = time.time()
    
    # Get correlation_id from request state (set by correlation_id_middleware)
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    
    # Log incoming request
    log_with_context(
        logger,
        'info',
        f"Incoming request: {request.method} {request.url.path}",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent', 'unknown')
    )
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Log response
    log_with_context(
        logger,
        'info',
        f"Request completed: {request.method} {request.url.path}",
        correlation_id=correlation_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=round(duration, 4)
    )
    
    return response


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Middleware to add correlation_id to all requests. Must be declared last to run first."""
    # Get correlation_id from header or generate new one
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    
    # Store correlation_id in request state for access in routes
    request.state.correlation_id = correlation_id
    
    # Process request
    response = await call_next(request)
    
    # Add correlation_id to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (for favicon and other public assets)
public_dir = Path(__file__).parent / "public"
if public_dir.exists():
    app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

# Include routers
app.include_router(home_router)  # Includes GET / for home page
app.include_router(health_router)  # Includes /health endpoints
app.include_router(cds_router.router, prefix="/api")  # Includes /api/cds endpoints
# Cron endpoints were intentionally removed from the HTTP API. Cron jobs should
# be executed via standalone Python scripts or scheduled tasks (see scripts/).
# Do NOT expose cron triggers over REST to avoid accidental or unauthorized runs.
