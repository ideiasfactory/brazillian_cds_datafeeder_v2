from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from ..models.home import HomePageData, FeatureInfo, EndpointInfo

router = APIRouter(tags=["Home"])


def get_home_page_data(version: str = "2.0.0", environment: str = "development") -> HomePageData:
    """
    Generate home page data with default features and endpoints.
    
    Args:
        version: API version string
        environment: Deployment environment
        
    Returns:
        HomePageData: Structured data for home page rendering
    """
    features = [
        FeatureInfo(
            icon="🔄",
            title="Automated Scraping",
            description="Daily updates from Investing.com with retry logic and backup strategies"
        ),
        FeatureInfo(
            icon="💾",
            title="Dual Storage",
            description="CSV for development, PostgreSQL for production with async operations"
        ),
        FeatureInfo(
            icon="⚡",
            title="FastAPI Powered",
            description="Modern async framework with automatic OpenAPI documentation"
        ),
        FeatureInfo(
            icon="☁️",
            title="Serverless Ready",
            description="Optimized for Vercel deployment with zero configuration"
        ),
    ]
    
    endpoints = [
        EndpointInfo(method="GET", path="/cds/", description="Get all CDS data"),
        EndpointInfo(method="GET", path="/cds/latest", description="Latest records"),
        EndpointInfo(method="GET", path="/cds/stats", description="Dataset statistics"),
        EndpointInfo(method="GET", path="/health", description="API health status"),
    ]
    
    environment_class = "production" if environment == "production" else ""
    
    return HomePageData(
        version=version,
        environment=environment,
        environment_class=environment_class,
        features=features,
        endpoints=endpoints
    )


def render_home_page(data: HomePageData) -> str:
    """
    Render the home page HTML with provided data.
    
    Args:
        data: HomePageData object with all page information
        
    Returns:
        str: Rendered HTML content
    """
    # Read the HTML template
    template_path = Path(__file__).parent.parent.parent.parent / "public" / "home.html"
    
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        # Fallback if template not found
        return """
        <html>
            <body>
                <h1>Brazilian CDS Data Feeder</h1>
                <p>Template file not found. Please check public/home.html</p>
            </body>
        </html>
        """
    
    # Replace placeholders with actual data
    html_content = html_content.replace("${API_VERSION}", data.version)
    html_content = html_content.replace("${ENVIRONMENT}", data.environment)
    html_content = html_content.replace("${ENVIRONMENT_CLASS}", data.environment_class)
    
    return html_content


@router.get("/", response_class=HTMLResponse, summary="Home Page")
async def home_page(request: Request) -> HTMLResponse:
    """
    Serve the application home page.
    
    Returns a beautifully designed HTML page with:
    - API information and version
    - Feature highlights
    - Quick links to documentation
    - Available endpoints list
    
    Returns:
        HTMLResponse: Rendered home page
    """
    # TODO: Get version and environment from settings/config
    version = "2.0.0"
    environment = "development"
    
    page_data = get_home_page_data(version=version, environment=environment)
    html_content = render_home_page(page_data)
    
    return HTMLResponse(content=html_content, status_code=200)


@router.get("/api/home/data", response_model=HomePageData, summary="Home Page Data")
async def get_home_data() -> HomePageData:
    """
    Get structured home page data as JSON.
    
    Useful for programmatic access to home page information
    or for building custom frontends.
    
    Returns:
        HomePageData: Structured home page data
    """
    # TODO: Get version and environment from settings/config
    version = "2.0.0"
    environment = "development"
    
    return get_home_page_data(version=version, environment=environment)
