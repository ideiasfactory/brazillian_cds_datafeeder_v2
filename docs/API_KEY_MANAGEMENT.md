# API Key Management Guide

## 🔐 Security Best Practices

This guide explains how to securely manage API keys for the Brazilian CDS Data Feeder API.

## Table of Contents

- [Overview](#overview)
- [Security Model](#security-model)
- [Using the CLI Tool](#using-the-cli-tool)
- [Best Practices](#best-practices)
- [Key Rotation](#key-rotation)
- [Incident Response](#incident-response)
- [FAQ](#faq)

---

## Overview

The Brazilian CDS Data Feeder uses API Key authentication to protect data endpoints. Keys are:

- **Generated once**: Shown only at creation time
- **Hashed with SHA-256**: Only the hash is stored in the database
- **Irreversible**: Cannot be recovered if lost
- **Revocable**: Can be disabled at any time

## Security Model

### How Keys Are Protected

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Key Generation                                           │
│    Random 32-byte token → "80negxMi_KVJzX-7z0EY4sq-C65W..."│
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Hashing (SHA-256)                                        │
│    Irreversible hash → "a1b2c3d4e5f6..."                   │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Database Storage                                         │
│    Only the hash is stored, never the original key         │
└─────────────────────────────────────────────────────────────┘
```

### What's Safe to Commit to Git

✅ **SAFE** - Include in repository:
- CLI management tools (`scripts/manage_api_keys.py`)
- Authentication middleware (`src/api/auth.py`)
- Database migration scripts (`scripts/create_api_keys_table.py`)
- Documentation files

❌ **NEVER COMMIT**:
- Generated API keys (the actual tokens)
- `.env` files with credentials
- Database dumps containing key hashes
- API key lists or backups

---

## Using the CLI Tool

### Prerequisites

1. Ensure your database is configured and accessible
2. Have the virtual environment activated
3. Have necessary environment variables set

### Creating a New API Key

```bash
python scripts/manage_api_keys.py create "Production App" "Main production API key"
```

**Output:**
```
✅ API Key Created Successfully!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔑 API Key (SAVE THIS - shown only once):
   80negxMi_KVJzX-7z0EY4sq-C65W8U6GAZhJMhYB8C8

📋 Details:
   Name:        Production App
   Description: Main production API key
   Created:     2025-11-19 23:45:12
   Status:      ✅ Active

⚠️  WARNING: Store this key securely!
   • Save it in a password manager or secrets vault
   • Add it to your environment variables
   • Never commit it to version control
   • This is your ONLY chance to see this key
```

**IMPORTANT**: Copy and save the key immediately. It cannot be retrieved later.

### Listing All API Keys

```bash
python scripts/manage_api_keys.py list
```

Shows all keys with their status (active/revoked) and usage statistics.

### Getting Key Details

```bash
python scripts/manage_api_keys.py info 1
```

Shows detailed information about a specific key including:
- Creation date
- Last used timestamp
- Request count
- Expiration date (if set)

### Revoking a Key

```bash
python scripts/manage_api_keys.py revoke 1
```

Immediately disables the key. Requests using this key will be rejected.

### Deleting a Key

```bash
python scripts/manage_api_keys.py delete 1
```

Permanently removes the key from the database. Use with caution.

---

## Best Practices

### 1. Key Storage

**DO:**
- ✅ Use environment variables in production
- ✅ Store in secure vaults (AWS Secrets Manager, HashiCorp Vault, 1Password)
- ✅ Use `.env` files for local development (excluded from git)
- ✅ Encrypt keys at rest in your applications

**DON'T:**
- ❌ Hard-code keys in source code
- ❌ Commit keys to version control
- ❌ Share keys via email or chat
- ❌ Store keys in plain text files

### 2. Key Naming

Use descriptive names to identify key purpose:

```bash
# Good examples
"Production API - Frontend App"
"Development - Testing Team"
"CI/CD Pipeline - GitHub Actions"
"Partner Integration - CompanyX"

# Bad examples
"key1"
"test"
"my_key"
```

### 3. Environment Separation

Create separate keys for each environment:

```bash
# Development
python scripts/manage_api_keys.py create "Dev Environment" "Development testing"

# Staging
python scripts/manage_api_keys.py create "Staging Environment" "Pre-production testing"

# Production
python scripts/manage_api_keys.py create "Production App" "Live production key"
```

### 4. Access Control

- Limit key distribution to authorized personnel only
- Use different keys for different applications/services
- Document who has access to which keys
- Review access periodically

---

## Key Rotation

Regular key rotation enhances security. Recommended schedule:

- **Production keys**: Every 90 days
- **Development keys**: Every 180 days
- **Immediately**: If compromised or suspected breach

### Rotation Process

1. **Create new key:**
   ```bash
   python scripts/manage_api_keys.py create "Production App v2" "Rotated key"
   ```

2. **Update applications** with new key

3. **Test** that new key works correctly

4. **Monitor** for any issues (grace period: 24-48 hours)

5. **Revoke old key:**
   ```bash
   python scripts/manage_api_keys.py revoke <old_key_id>
   ```

6. **Document** the rotation in your change log

---

## Incident Response

### If a Key is Compromised

**Immediate Actions (within 5 minutes):**

1. **Revoke the key immediately:**
   ```bash
   python scripts/manage_api_keys.py revoke <compromised_key_id>
   ```

2. **Create a new key:**
   ```bash
   python scripts/manage_api_keys.py create "Emergency Replacement" "Replaced compromised key"
   ```

3. **Update all services** using the old key

**Follow-up Actions (within 24 hours):**

4. **Audit access logs** to check for unauthorized usage:
   ```bash
   python scripts/manage_api_keys.py info <compromised_key_id>
   ```

5. **Review how the compromise occurred**

6. **Document the incident** and lessons learned

7. **Update security procedures** if needed

### If You Lose a Key

Keys cannot be recovered if lost. You must:

1. Create a new key
2. Update your application configuration
3. Revoke the old key (optional, or wait for expiration)

---

## FAQ

### Q: Can I recover a lost API key?
**A:** No. Keys are hashed using SHA-256, which is irreversible. If you lose a key, you must create a new one.

### Q: How do I know if my key is working?
**A:** Test it with a simple API call:
```bash
curl -H "X-API-Key: YOUR_KEY_HERE" https://your-api.com/api/cds/info
```

### Q: Can I have multiple active keys?
**A:** Yes. You can create as many keys as needed. This is useful for:
- Different environments (dev, staging, prod)
- Multiple applications
- Partner integrations
- Team members

### Q: What happens if I hit the API without a key?
**A:** Protected endpoints will return:
```json
{
  "detail": "API Key required. Include X-API-Key header."
}
```

### Q: How do I add an expiration date to a key?
**A:** Currently, keys don't expire by default. You can implement expiration by:
1. Setting a reminder for rotation
2. Or manually revoking keys after a period

### Q: Is it safe to include the CLI tool in the repository?
**A:** Yes! The CLI tool is just a management interface. It doesn't contain any secrets. Only the generated keys need to be kept secret.

### Q: What if I accidentally commit a key to Git?
**A:** 
1. **Revoke the key immediately**
2. **Remove it from Git history** using `git filter-branch` or BFG Repo-Cleaner
3. **Rotate all other keys** as a precaution
4. **Review who had access** to the repository

### Q: Can I see which key made a request in logs?
**A:** Yes. The authentication middleware logs the key name (not the key itself) with each request.

---

## Environment Variables Setup

### Development (.env file)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cds_db

# API Key for testing
API_KEY=your_development_key_here
```

### Production (Vercel/Environment)

Set these in your hosting platform:

```bash
DATABASE_URL=<your_neon_postgres_url>
ENVIRONMENT=production
API_VERSION=2.0.0
```

**Never set actual API keys as environment variables.** Keys should be:
- Provided by clients in request headers
- Stored only in the database (as hashes)

---

## Additional Security Measures

### Rate Limiting

Consider implementing rate limiting per API key:
- Prevents abuse
- Protects against DDoS
- Can be tracked using the `request_count` field

### Audit Logging

The system automatically tracks:
- `created_at`: When the key was created
- `last_used_at`: Last successful authentication
- `request_count`: Total number of requests

### IP Whitelisting

For enhanced security, consider adding IP restrictions:
- Limit keys to specific IP ranges
- Useful for server-to-server communication
- Reduces risk of stolen key usage

---

## Support and Questions

If you have questions about API key management:

1. Check the [main authentication documentation](./AUTHENTICATION.md)
2. Review the [authentication summary](./AUTHENTICATION_SUMMARY.md)
3. Open an issue on GitHub
4. Contact the development team

---

## Changelog

**v2.0.0** (2025-11-19)
- Initial API Key authentication system
- CLI management tool
- SHA-256 hashing
- Basic CRUD operations

---

**Remember**: Security is everyone's responsibility. When in doubt, revoke and rotate keys. 🔐
