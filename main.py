from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import health_router, home_router
from src.config import settings

# Create FastAPI application
app = FastAPI(
    title="Brazilian CDS Data Feeder",
    description="Credit Default Swap Historical Data API",
    version=settings.api_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS using settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home_router)  # Includes GET / for home page
app.include_router(health_router)  # Includes /health endpoints
