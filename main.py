from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time

from src.api import health_router, home_router
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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all HTTP requests with timing."""
    start_time = time.time()
    
    # Log incoming request
    log_with_context(
        logger,
        'info',
        f"Incoming request: {request.method} {request.url.path}",
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
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=round(duration, 4)
    )
    
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
