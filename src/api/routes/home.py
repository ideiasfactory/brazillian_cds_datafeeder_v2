from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, FileResponse

from ..models.home import HomePageData, FeatureInfo, EndpointInfo
from src.config import settings
from src.logging_config import get_logger, log_with_context

# Initialize logger
logger = get_logger(__name__)

router = APIRouter(tags=["Home"])


def get_home_page_data(
    version: str = "2.0.0", environment: str = "development"
) -> HomePageData:
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
            description="Daily updates from Investing.com with retry logic and backup strategies",
        ),
        FeatureInfo(
            icon="💾",
            title="Dual Storage",
            description="CSV for development, PostgreSQL for production with async operations",
        ),
        FeatureInfo(
            icon="⚡",
            title="FastAPI Powered",
            description="Modern async framework with automatic OpenAPI documentation",
        ),
        FeatureInfo(
            icon="☁️",
            title="Serverless Ready",
            description="Optimized for Vercel deployment with zero configuration",
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
        endpoints=endpoints,
    )


def render_home_page(data: HomePageData) -> str:
    """
    Render the home page HTML with provided data.

    Args:
        data: HomePageData object with all page information

    Returns:
        str: Rendered HTML content
    """
    # Try multiple paths to locate the template (for local and Vercel environments)
    possible_paths = [
        # Relative to this file - templates folder (BEST for Vercel)
        Path(__file__).parent.parent / "templates" / "home.html",
        # Vercel serverless function path
        Path("/var/task/src/api/templates/home.html"),
        # Public folder (local development)
        Path(__file__).parent.parent.parent.parent / "public" / "home.html",
        # Alternative Vercel path
        Path("/var/task/public/home.html"),
        # Relative to current working directory
        Path.cwd() / "public" / "home.html",
    ]

    html_content = None

    log_with_context(
        logger, "debug", "Searching for home template", paths_count=len(possible_paths)
    )

    for path in possible_paths:
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    log_with_context(
                        logger,
                        "info",
                        "Home template found and loaded",
                        template_path=str(path),
                    )
                    break
        except (FileNotFoundError, PermissionError) as e:
            log_with_context(
                logger,
                "debug",
                "Failed to read template from path",
                path=str(path),
                error=str(e),
            )
            continue

    if html_content is None:
        log_with_context(
            logger,
            "warning",
            "Template not found - using fallback HTML",
            attempted_paths=len(possible_paths),
        )

        # Fallback if template not found - provide a basic HTML page
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Brazilian CDS Data Feeder</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 12px;
                    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
                }}
                h1 {{ color: #2d3748; margin-bottom: 10px; }}
                .version {{
                    background: #667eea; color: white; padding: 4px 12px;
                    border-radius: 12px; font-size: 14px;
                }}
                .links {{ margin-top: 30px; }}
                .link {{
                    display: inline-block; margin: 10px 10px 10px 0;
                    padding: 10px 20px; background: #667eea; color: white;
                    text-decoration: none; border-radius: 6px;
                }}
                .link:hover {{ background: #764ba2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🇧🇷 Brazilian CDS Data Feeder</h1>
                <span class="version">v{data.version}</span>
                <p style="margin-top: 20px; color: #4a5568;">
                    Credit Default Swap Historical Data API
                </p>
                <div class="links">
                    <a href="/docs" class="link">📚 API Documentation</a>
                    <a href="/health" class="link">❤️ Health Check</a>
                    <a href="/api/home/data" class="link">📊 API Data</a>
                </div>
            </div>
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
    try:
        log_with_context(
            logger,
            "debug",
            "Rendering home page",
            client_ip=request.client.host if request.client else None,
        )

        page_data = get_home_page_data(
            version=settings.api_version, environment=settings.environment
        )
        html_content = render_home_page(page_data)

        log_with_context(
            logger,
            "info",
            "Home page rendered successfully",
            version=settings.api_version,
            content_length=len(html_content),
        )

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to render home page",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


@router.get("/api/home/data", response_model=HomePageData, summary="Home Page Data")
async def get_home_data() -> HomePageData:
    """
    Get structured home page data as JSON.

    Useful for programmatic access to home page information
    or for building custom frontends.

    Returns:
        HomePageData: Structured home page data
    """
    try:
        log_with_context(logger, "debug", "Fetching home page data as JSON")

        data = get_home_page_data(
            version=settings.api_version, environment=settings.environment
        )

        log_with_context(
            logger,
            "info",
            "Home page data retrieved successfully",
            version=data.version,
            features_count=len(data.features),
            endpoints_count=len(data.endpoints),
        )

        return data

    except Exception as e:
        log_with_context(
            logger,
            "error",
            "Failed to fetch home page data",
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """
    Serve the favicon.ico file.

    Returns:
        FileResponse: Favicon file
    """
    # Try multiple paths to locate the favicon
    possible_paths = [
        # Relative to this file - templates folder (BEST for Vercel)
        Path(__file__).parent.parent / "templates" / "favicon.ico",
        # Vercel serverless function path
        Path("/var/task/src/api/templates/favicon.ico"),
        # Public folder (local development)
        Path(__file__).parent.parent.parent.parent / "public" / "favicon.ico",
        # Alternative paths
        Path("/var/task/public/favicon.ico"),
        Path.cwd() / "public" / "favicon.ico",
    ]

    log_with_context(
        logger, "debug", "Searching for favicon", paths_count=len(possible_paths)
    )

    for path in possible_paths:
        if path.exists():
            log_with_context(logger, "info", "Favicon found and served", path=str(path))
            return FileResponse(path, media_type="image/x-icon")

    # If favicon not found, return 404
    log_with_context(
        logger,
        "warning",
        "Favicon not found in any expected location",
        attempted_paths=len(possible_paths),
    )

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail="Favicon not found")
