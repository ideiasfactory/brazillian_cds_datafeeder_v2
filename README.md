# Brazilian CDS Data Feeder v2

A production-ready FastAPI application that scrapes, stores, and serves Brazilian CDS 5-year historical data.

## 🚀 Features

- **FastAPI Framework**: Modern, fast async web framework
- **Automated Data Collection**: Scheduled scraping from Investing.com
- **Dual Storage**: CSV for development, PostgreSQL for production
- **RESTful API**: Clean endpoints with OpenAPI documentation
- **Health Monitoring**: Kubernetes-ready liveness and readiness probes
- **Serverless Deployment**: Optimized for Vercel

## 📁 Project Structure

```
.
├── main.py                 # FastAPI application entry point
├── src/
│   └── api/
│       ├── index.py       # Vercel ASGI entry point
│       ├── models/        # Pydantic data models
│       │   ├── health.py  # Health check models
│       │   └── home.py    # Home page models
│       └── routes/        # API route handlers
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

## 📡 API Endpoints

### Home
- `GET /` - Landing page with API information
- `GET /api/home/data` - Structured home page data (JSON)

### Health Monitoring
- `GET /health` - Comprehensive health check
- `GET /health/liveness` - Simple liveness probe
- `GET /health/readiness` - Readiness probe (checks database)

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

```bash
# Run tests (when test suite is added)
pytest

# Check code style
flake8 .
black --check .
```

## 📦 Dependencies

- **fastapi** >= 0.115.0 - Web framework
- **uvicorn** >= 0.30.0 - ASGI server
- **pydantic** >= 2.0.0 - Data validation

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
