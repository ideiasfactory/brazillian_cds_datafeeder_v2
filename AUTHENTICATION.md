# API Authentication Guide

## Overview

The Brazilian CDS Data Feeder API uses **API Key authentication** to secure access to protected endpoints. API keys are stored securely in the database using SHA-256 hashing.

## Security Features

- **SHA-256 Hashing**: API keys are hashed before storage for security
- **Database Management**: Keys stored in Neon PostgreSQL with full CRUD support
- **Usage Tracking**: Track request count and last used timestamp for each key
- **Expiration Support**: Optional expiration dates for time-limited access
- **Easy Management**: CLI tool for creating, listing, and revoking keys

## Protected vs Public Endpoints

### Protected Endpoints (Require API Key)

These endpoints require a valid API key in the `X-API-Key` header:

- `GET /api/cds` - Get CDS records with date filtering
- `GET /api/cds/latest` - Get the most recent CDS record
- `GET /api/cds/statistics` - Get statistics about CDS data

### Public Endpoints (No Authentication)

These endpoints are publicly accessible without authentication:

- `GET /` - Home page
- `GET /health` - Health check endpoint
- `GET /api/cds/info` - Schema documentation and optional statistics

## Using API Keys

### Making Authenticated Requests

Include your API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  https://your-api.com/api/cds/latest
```

### Example with Query Parameters

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" \
  "https://your-api.com/api/cds?data_inicial=2025-01-01&data_final=2025-01-31&order=asc"
```

### Using with Python

```python
import requests

API_KEY = "YOUR_API_KEY_HERE"
BASE_URL = "https://your-api.com"

headers = {
    "X-API-Key": API_KEY
}

# Get latest CDS record
response = requests.get(f"{BASE_URL}/api/cds/latest", headers=headers)
data = response.json()

# Get records with date range
params = {
    "data_inicial": "2025-01-01",
    "data_final": "2025-01-31",
    "order": "asc"
}
response = requests.get(f"{BASE_URL}/api/cds", headers=headers, params=params)
data = response.json()
```

### Using with JavaScript/TypeScript

```javascript
const API_KEY = 'YOUR_API_KEY_HERE';
const BASE_URL = 'https://your-api.com';

const headers = {
  'X-API-Key': API_KEY
};

// Get latest CDS record
const response = await fetch(`${BASE_URL}/api/cds/latest`, { headers });
const data = await response.json();

// Get records with date range
const params = new URLSearchParams({
  data_inicial: '2025-01-01',
  data_final: '2025-01-31',
  order: 'asc'
});
const response2 = await fetch(`${BASE_URL}/api/cds?${params}`, { headers });
const data2 = await response2.json();
```

## Managing API Keys (CLI Tool)

The project includes a CLI tool for managing API keys. All commands must be run from the project root directory.

### Prerequisites

Activate the virtual environment and ensure you have the `DATABASE_URL` environment variable set:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (CMD)
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

### Create a New API Key

```bash
python scripts/manage_api_keys.py create "Key Name"
```

**With description:**
```bash
python scripts/manage_api_keys.py create "Production Key" --description "Key for production environment"
```

**With expiration (in days):**
```bash
python scripts/manage_api_keys.py create "Temporary Key" --days 30
```

**Output example:**
```
✅ API Key created successfully!

📝 Details:
  ID:          1
  Name:        Production Key
  Description: Key for production environment
  Created:     2025-01-20 10:30:00+00:00

🔑 API Key (save this, it won't be shown again):
  80negxMi_KVJzX-7z0EY4sq-C65W8U6GAZhJMhYB8C8

💡 Usage:
  curl -H 'X-API-Key: 80negxMi_KVJzX-7z0EY4sq-C65W8U6GAZhJMhYB8C8' https://your-api.com/api/cds
```

⚠️ **Important**: Save the API key immediately! It is only shown once and cannot be retrieved later.

### List All API Keys

```bash
python scripts/manage_api_keys.py list
```

**Include inactive keys:**
```bash
python scripts/manage_api_keys.py list --all
```

**Output example:**
```
📋 API Keys (3 total):

ID    Name                Active   Requests   Created            Expires
------------------------------------------------------------------------
1     Production Key      ✅ Yes    1247       2025-01-20 10:30   Never
2     Temporary Key       ✅ Yes    45         2025-01-25 14:20   2025-02-24
3     Old Key             ❌ No     892        2024-12-01 09:15   Never
```

### Get Detailed Information

```bash
python scripts/manage_api_keys.py info 1
```

**Output example:**
```
📋 API Key Details:

  ID:           1
  Name:         Production Key
  Description:  Key for production environment
  Active:       ✅ Yes
  Created:      2025-01-20 10:30:00+00:00
  Expires:      Never
  Last Used:    2025-01-30 08:45:23+00:00
  Request Count: 1247

Status: ✅ Valid and active
```

### Revoke (Deactivate) an API Key

Revoke a key without deleting it (can be reactivated later if needed):

```bash
python scripts/manage_api_keys.py revoke 1
```

**Output:**
```
✅ API key 'Production Key' has been revoked
```

### Delete an API Key

Permanently delete an API key from the database:

```bash
python scripts/manage_api_keys.py delete 1
```

**Confirmation required:**
```
⚠️  Warning: This will permanently delete the API key 'Production Key'
Type 'DELETE' to confirm: DELETE
✅ API key deleted successfully
```

## API Response Format

All authenticated endpoints return a standardized response format:

```json
{
  "status": "success",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "data": { ... },
  "error_message": null,
  "timestamp": "2025-01-30T10:30:45.123456"
}
```

## Error Responses

### Missing API Key (401 Unauthorized)

```json
{
  "detail": "Missing API key"
}
```

### Invalid or Expired API Key (401 Unauthorized)

```json
{
  "detail": "Invalid or expired API key"
}
```

## Database Schema

The `api_keys` table structure:

```sql
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_hash VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    request_count INTEGER DEFAULT 0 NOT NULL
);

CREATE INDEX idx_key_hash_active ON api_keys(key_hash, is_active);
CREATE INDEX idx_expires_at ON api_keys(expires_at);
```

## Security Best Practices

### For API Key Owners

1. **Store Securely**: Never commit API keys to version control
2. **Use Environment Variables**: Store keys in `.env` files (excluded from git)
3. **Rotate Regularly**: Create new keys and revoke old ones periodically
4. **Limit Scope**: Use different keys for different environments (dev, staging, prod)
5. **Monitor Usage**: Check request counts and last used timestamps regularly
6. **Set Expiration**: Use time-limited keys for temporary access

### For API Administrators

1. **Regular Audits**: Review active keys and revoke unused ones
2. **Monitor Activity**: Track request counts and suspicious patterns
3. **Key Hygiene**: Delete permanently revoked keys after grace period
4. **Backup**: Ensure database backups include api_keys table
5. **Rate Limiting**: Consider implementing rate limiting per API key (future enhancement)

## Migration

The database table is created automatically on first deployment. To manually create or recreate the table:

```bash
python scripts/create_api_keys_table.py
```

This script:
- Creates the `api_keys` table if it doesn't exist
- Creates necessary indexes
- Adds table and column comments for documentation

## Troubleshooting

### "Missing API key" Error

Ensure you're including the `X-API-Key` header in your request:

```bash
# ✅ Correct
curl -H "X-API-Key: YOUR_KEY" https://api.example.com/api/cds/latest

# ❌ Wrong (missing header)
curl https://api.example.com/api/cds/latest
```

### "Invalid or expired API key" Error

Possible causes:
1. The key is incorrect (typo or copy-paste error)
2. The key has been revoked (check with `list` command)
3. The key has expired (check with `info <id>` command)
4. The key doesn't exist in the database

Verify your key status:
```bash
python scripts/manage_api_keys.py list --all
```

### ModuleNotFoundError When Running Scripts

Make sure you're in the project root and the virtual environment is activated:

```bash
# Check current directory
pwd  # or cd on Windows

# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows PowerShell
source .venv/bin/activate     # Linux/Mac

# Run script
python scripts/manage_api_keys.py list
```

### Database Connection Errors

Ensure your `DATABASE_URL` environment variable is set correctly in `.env`:

```env
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/database
```

## Support

For issues or questions:
- Check the [main README](README.md) for general API documentation
- Review the [deployment guide](DEPLOYMENT.md) for production setup
- Check logs in BetterStack for request tracking (correlation_id included)

## Future Enhancements

Potential improvements for the authentication system:

- [ ] Rate limiting per API key
- [ ] API key scopes/permissions (read-only, read-write)
- [ ] API key usage analytics dashboard
- [ ] Automatic key rotation notifications
- [ ] IP whitelisting per key
- [ ] OAuth2/JWT support for additional security layers
