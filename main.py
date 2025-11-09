from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import health_router, home_router

# Create FastAPI application
app = FastAPI(
    title="Brazilian CDS Data Feeder",
    description="Credit Default Swap Historical Data API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS for Vercel deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home_router)  # Includes GET / for home page
app.include_router(health_router)  # Includes /health endpoints
