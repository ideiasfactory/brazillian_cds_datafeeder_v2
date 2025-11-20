"""Create API keys table in the database."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import text
from src.database.connection import get_async_session


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS api_keys (
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

CREATE INDEX IF NOT EXISTS idx_key_hash_active ON api_keys(key_hash, is_active);
CREATE INDEX IF NOT EXISTS idx_expires_at ON api_keys(expires_at);

COMMENT ON TABLE api_keys IS 'API keys for authentication';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the API key';
COMMENT ON COLUMN api_keys.name IS 'Friendly name for the key';
COMMENT ON COLUMN api_keys.is_active IS 'Whether the key is active';
COMMENT ON COLUMN api_keys.request_count IS 'Total number of requests made with this key';
"""

# Split statements for asyncpg
SQL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS api_keys (
        id SERIAL PRIMARY KEY,
        key_hash VARCHAR(64) UNIQUE NOT NULL,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT TRUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
        expires_at TIMESTAMP WITH TIME ZONE,
        last_used_at TIMESTAMP WITH TIME ZONE,
        request_count INTEGER DEFAULT 0 NOT NULL
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_key_hash_active ON api_keys(key_hash, is_active)",
    "CREATE INDEX IF NOT EXISTS idx_expires_at ON api_keys(expires_at)",
    "COMMENT ON TABLE api_keys IS 'API keys for authentication'",
    "COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the API key'",
    "COMMENT ON COLUMN api_keys.name IS 'Friendly name for the key'",
    "COMMENT ON COLUMN api_keys.is_active IS 'Whether the key is active'",
    "COMMENT ON COLUMN api_keys.request_count IS 'Total number of requests made with this key'"
]


async def create_api_keys_table():
    """Create the api_keys table in the database."""
    print("Creating api_keys table...")
    
    async with get_async_session() as session:
        try:
            for sql in SQL_STATEMENTS:
                await session.execute(text(sql))
            await session.commit()
            print("✅ api_keys table created successfully!")
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            await session.rollback()
            raise


async def main():
    """Main entry point."""
    await create_api_keys_table()


if __name__ == "__main__":
    asyncio.run(main())
