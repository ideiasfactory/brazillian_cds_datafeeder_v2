# Brazilian CDS Data Feeder v2

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/actions/workflows/tests.yml/badge.svg)](https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/ideiasfactory/brazillian_cds_datafeeder_v2/branch/master/graph/badge.svg)](https://codecov.io/gh/ideiasfactory/brazillian_cds_datafeeder_v2)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black.svg)](https://vercel.com)
[![API Status](https://img.shields.io/badge/API-Live-success.svg)](https://brazillian-cds-datafeeder-v2.vercel.app/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-ready FastAPI application that scrapes, stores, and serves Brazilian CDS 5-year historical data.

## 🌐 Live Demo

**Production**: [https://brazillian-cds-datafeeder-v2.vercel.app/](https://brazillian-cds-datafeeder-v2.vercel.app/)

- 📚 [API Documentation](https://brazillian-cds-datafeeder-v2.vercel.app/docs)
- ❤️ [Health Check](https://brazillian-cds-datafeeder-v2.vercel.app/health)

## 🚀 Features

- **FastAPI Framework**: Modern, fast async web framework
- **Automated Data Collection**: Script-based scraping from Investing.com
- **Dual Storage**: CSV for development, PostgreSQL for production
- **RESTful API**: Clean endpoints with OpenAPI documentation
- **API Key Authentication**: Secure API access with database-managed keys
- **Standardized Responses**: All endpoints return consistent structure with correlation IDs
- **Health Monitoring**: Kubernetes-ready liveness and readiness probes
- **BetterStack Logging**: Structured logging with correlation tracking
- **Serverless Deployment**: Optimized for Vercel

## 📁 Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── scripts/
│   ├── update_cds_data.py # CLI script for data updates
│   └── SCHEDULING.md      # Comprehensive scheduling guide
├── src/
│   ├── logging_config.py  # BetterStack structured logging
│   ├── config.py          # Configuration management
│   └── api/
│       ├── index.py       # Vercel ASGI entry point
│       ├── models/        # Pydantic data models
│       │   ├── cds.py     # CDS API standardized responses
│       │   ├── health.py  # Health check models
│       │   └── home.py    # Home page models
│       └── routes/        # API route handlers
│           ├── cds.py     # CDS data endpoints with correlation IDs
│           ├── health.py  # Health endpoints
│           └── home.py    # Home page routes
├── public/
│   └── home.html         # Landing page template
├── requirements.txt      # Python dependencies
├── pyproject.toml       # Project metadata
└── vercel.json          # Vercel deployment config
```

## 🛠️ Installation

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2.git
   cd brazillian_cds_datafeeder_v2
   ```

2. **Set up Python environment**
   ```bash
   # Using pyenv (recommended)
   pyenv virtualenv 3.11.0 brazillian_cds_datafeeder_v2
   pyenv local brazillian_cds_datafeeder_v2
   
   # Or using venv
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your settings
   nano .env
   ```
   
   See [docs/ENVIRONMENT.md](docs/ENVIRONMENT.md) for detailed configuration guide.

5. **Run the application**

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the application**
   - Home page: <http://localhost:8000>
   - API docs: <http://localhost:8000/docs>
   - ReDoc: <http://localhost:8000/redoc>
   - Health check: <http://localhost:8000/health>

## 🌐 Deployment to Vercel

### Prerequisites
- Vercel account
- Vercel CLI (optional): `npm i -g vercel`

### Deploy via CLI

```bash
vercel
```

### Deploy via Git Integration

1. Push your code to GitHub
2. Import project in Vercel dashboard
3. Vercel will automatically detect Python and deploy

### Environment Variables (Optional)

Set in Vercel dashboard:
- `ENVIRONMENT`: `production` or `development`
- `API_VERSION`: Version string (e.g., `2.0.0`)

## � Documentation

Comprehensive guides are available in the `docs/` folder:

- **[AUTHENTICATION.md](docs/AUTHENTICATION.md)** - Authentication system overview and usage
- **[API_KEY_MANAGEMENT.md](docs/API_KEY_MANAGEMENT.md)** - Complete guide for managing API keys securely
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Deployment instructions
- **[ENVIRONMENT.md](docs/ENVIRONMENT.md)** - Environment configuration guide
- **[LOGGING.md](docs/LOGGING.md)** - Logging configuration and best practices
- **[scripts/SCHEDULING.md](scripts/SCHEDULING.md)** - Data update scheduling guides

## �📡 API Endpoints

### Authentication

Most data endpoints require API key authentication. See **[docs/AUTHENTICATION.md](docs/AUTHENTICATION.md)** and **[docs/API_KEY_MANAGEMENT.md](docs/API_KEY_MANAGEMENT.md)** for:
- How to create and manage API keys
- Using authenticated endpoints
- Security best practices
- Key rotation and incident response

### Home
- `GET /` - Landing page with API information
- `GET /api/home/data` - Structured home page data (JSON)

### Health Monitoring

- `GET /health` - Comprehensive health check (public)
- `GET /health/liveness` - Simple liveness probe (public)
- `GET /health/readiness` - Readiness probe, checks database (public)

### CDS Data

#### Public Endpoints
- `GET /api/cds/info` - Schema documentation and optional statistics (no authentication)

#### Protected Endpoints (Require API Key)
- `GET /api/cds/latest` - Get most recent CDS record 🔒
- `GET /api/cds` - List CDS records with optional date filtering 🔒
- `GET /api/cds/statistics` - Get statistical summary 🔒

All CDS endpoints return standardized responses with correlation IDs for request tracking.

**Example with authentication:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  https://brazillian-cds-datafeeder-v2.vercel.app/api/cds/latest
```

### Documentation
- `GET /docs` - Interactive Swagger UI
- `GET /redoc` - ReDoc documentation

## 🔧 Configuration

The HTML template (`public/home.html`) uses placeholder substitution:
- `${API_VERSION}` - Replaced with API version
- `${ENVIRONMENT}` - Replaced with environment name
- `${ENVIRONMENT_CLASS}` - CSS class for environment badge

## 📝 Development

### Adding New Routes

1. Create a new route file in `src/api/routes/`
2. Define Pydantic models in `src/api/models/`
3. Register router in `main.py`

Example:
```python
# src/api/routes/my_route.py
from fastapi import APIRouter

router = APIRouter(prefix="/my-route", tags=["MyRoute"])

@router.get("/")
async def my_endpoint():
    return {"message": "Hello"}

# main.py
from src.api.routes.my_route import router as my_router
app.include_router(my_router)
```

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run only unit tests
pytest tests/unit -v -m unit

# Run only integration tests
pytest tests/integration -v -m integration

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_auth.py -v

# Run tests in parallel (faster)
pytest -n auto
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_auth.py        # Authentication tests
│   └── test_models.py      # Model tests
└── integration/             # Integration tests (API endpoints)
    └── test_api_endpoints.py
```

### Writing Tests

Tests use pytest with async support. Example:

```python
import pytest

@pytest.mark.unit
@pytest.mark.asyncio
async def test_my_function(test_session):
    result = await my_async_function()
    assert result is not None
```

### Continuous Integration

Tests run automatically on:
- Every push to `main`/`master`/`develop` branches
- Every pull request
- Multiple Python versions (3.11, 3.12)

See [`.github/workflows/tests.yml`](.github/workflows/tests.yml) for CI configuration.

### Code Coverage

Coverage reports are generated automatically and uploaded to Codecov. View detailed coverage:

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## 📦 Dependencies

- **fastapi** >= 0.115.0 - Web framework
- **uvicorn** >= 0.30.0 - ASGI server
- **pydantic** >= 2.0.0 - Data validation
- **sqlalchemy** >= 2.0.0 - Database ORM (async)
- **psycopg** - PostgreSQL driver for async operations
- **logtail-python** - BetterStack logging integration

## ⏰ Scheduling Data Updates

CDS data is updated via the `scripts/update_cds_data.py` CLI script. **Never expose data updates via REST endpoints** for security.

See **[scripts/SCHEDULING.md](scripts/SCHEDULING.md)** for comprehensive scheduling guides including:

- Linux cron and systemd timers
- GitHub Actions workflows
- Windows Task Scheduler
- Docker + cron
- Cloud schedulers (AWS, GCP, Azure)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## ��‍💻 Author

**Ideas Factory**
- GitHub: [@ideiasfactory](https://github.com/ideiasfactory)

## 🐛 Issues

Report issues at: <https://github.com/ideiasfactory/brazillian_cds_datafeeder_v2/issues>

---

Made with ❤️ for the Brazilian financial data community
