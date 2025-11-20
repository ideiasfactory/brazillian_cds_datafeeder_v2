# Vercel Deployment Notes

## 🌐 Live Deployment

**Production URL**: https://brazillian-cds-datafeeder-v2.vercel.app/

**Deployment Status**: ✅ Active

## 📝 Recent Updates (Nov 9, 2025)

### Fixed Template Path Issue

**Problem**: The HTML template (`public/home.html`) was not being found in the Vercel serverless environment.

**Root Cause**: 
- Vercel serverless functions run in `/var/task/` directory
- Path resolution using relative paths from `__file__` didn't work correctly
- Static files weren't properly configured in `vercel.json`

**Solution Implemented**:

1. **Updated `src/api/routes/home.py`**:
   - Added multiple path resolution strategies
   - Tries Vercel paths first: `/var/task/public/home.html`
   - Falls back to relative paths for local development
   - Provides embedded HTML fallback if template not found
   - Uses environment variables for version and environment detection

2. **Updated `vercel.json`**:
   - Added static file build configuration for `public/**`
   - Configured favicon route
   - Added `API_VERSION` environment variable
   - Properly set `ENVIRONMENT=production`

3. **Environment Detection**:
   - Uses `VERCEL` environment variable to detect deployment
   - Automatically switches between development and production
   - Reads version from `API_VERSION` env var

## 🔧 Configuration

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "src/api/index.py",
      "use": "@vercel/python"
    },
    {
      "src": "public/**",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/favicon.ico",
      "dest": "/public/favicon.ico"
    },
    {
      "src": "/(.*)",
      "dest": "src/api/index.py"
    }
  ],
  "env": {
    "ENVIRONMENT": "production",
    "API_VERSION": "2.0.0"
  }
}
```

### Environment Variables

Set in Vercel Dashboard:

| Variable | Value | Purpose |
|----------|-------|---------|
| `ENVIRONMENT` | `production` | Deployment environment |
| `API_VERSION` | `2.0.0` | API version string |
| `VERCEL` | (auto-set) | Indicates Vercel environment |

## 📊 Endpoints Status

All endpoints are working:

- ✅ `GET /` - Home page with embedded HTML
- ✅ `GET /docs` - Swagger UI documentation
- ✅ `GET /redoc` - ReDoc documentation
- ✅ `GET /health` - Health check endpoint
- ✅ `GET /health/liveness` - Liveness probe
- ✅ `GET /health/readiness` - Readiness probe
- ✅ `GET /api/home/data` - Home page data (JSON)

## 🐛 Troubleshooting

### Template Not Found Error

If you see "Template file not found":

1. Check `public/home.html` exists in repository
2. Verify `vercel.json` includes static build
3. Check Vercel build logs
4. The app will show a fallback HTML page

### Path Resolution Order

The application tries these paths in order:

1. `/var/task/public/home.html` (Vercel)
2. `Path(__file__).parent.parent.parent.parent / "public" / "home.html"` (relative)
3. `Path.cwd() / "public" / "home.html"` (current working directory)
4. Embedded HTML fallback

### Build Logs

To check deployment:

1. Go to Vercel Dashboard
2. Select: `brazillian-cds-datafeeder-v2`
3. Click on latest deployment
4. View "Build Logs" and "Function Logs"

## 🚀 Deployment Process

### Automatic Deployment

- **Trigger**: Push to `master` branch
- **Build Time**: ~30-60 seconds
- **Status**: Check [Vercel Dashboard](https://vercel.com/dashboard)

### Manual Deployment

```bash
# From project root
vercel --prod
```

## 📈 Performance

- **Region**: Auto (closest to user)
- **Cold Start**: ~1-2 seconds
- **Warm Response**: ~100-300ms
- **Timeout**: 10 seconds (free tier)

## 🔄 Next Deployment Steps

1. Push changes to GitHub
2. Vercel auto-deploys from master branch
3. Check deployment status in dashboard
4. Verify all endpoints are working

## 📚 Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Full deployment guide
- [README.md](./README.md) - Project documentation
- [MIGRATION.md](./MIGRATION.md) - Migration from Flask to FastAPI

## ⚠️ Known Limitations

1. **Serverless Timeout**: 10 seconds on free tier
2. **Build Time**: Limited build minutes per month (free tier)
3. **File Size**: Functions must be < 50MB
4. **Memory**: 1024MB RAM limit

## ✨ Recent Improvements

- ✅ Fixed template path resolution for serverless
- ✅ Added fallback HTML for resilience
- ✅ Environment-aware configuration
- ✅ Proper static file handling
- ✅ Multiple path resolution strategies

---

Last Updated: November 9, 2025
Deployment: v2.0.0
Status: Production Ready ✅
