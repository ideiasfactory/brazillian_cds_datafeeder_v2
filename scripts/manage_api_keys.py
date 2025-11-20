"""CLI script to manage API keys."""

import asyncio
import secrets
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.database.connection import get_async_session
from src.database.repositories.api_key_repository import APIKeyRepository


def generate_api_key(length: int = 32) -> str:
    """Generate a secure random API key."""
    return secrets.token_urlsafe(length)


async def create_key(name: str, description: Optional[str] = None, days_valid: Optional[int] = None):
    """Create a new API key."""
    key = generate_api_key()
    expires_at = None
    
    if days_valid:
        expires_at = datetime.utcnow() + timedelta(days=days_valid)
    
    async with get_async_session() as session:
        repo = APIKeyRepository(session)
        
        # Check if name already exists
        existing = await repo.get_by_name(name)
        if existing:
            print(f"❌ Error: API key with name '{name}' already exists")
            return
        
        api_key = await repo.create_key(
            key=key,
            name=name,
            description=description,
            expires_at=expires_at
        )
        
        print("✅ API Key created successfully!")
        print(f"\n📝 Details:")
        print(f"  ID:          {api_key.id}")
        print(f"  Name:        {api_key.name}")
        if description:
            print(f"  Description: {description}")
        print(f"  Created:     {api_key.created_at}")
        if expires_at:
            print(f"  Expires:     {expires_at}")
        print(f"\n🔑 API Key (save this, it won't be shown again):")
        print(f"  {key}")
        print(f"\n💡 Usage:")
        print(f"  curl -H 'X-API-Key: {key}' https://your-api.com/api/cds")


async def list_keys(include_inactive: bool = False):
    """List all API keys."""
    async with get_async_session() as session:
        repo = APIKeyRepository(session)
        keys = await repo.list_all(include_inactive=include_inactive)
        
        if not keys:
            print("📭 No API keys found")
            return
        
        print(f"\n📋 API Keys ({len(keys)} total):\n")
        print(f"{'ID':<5} {'Name':<25} {'Active':<8} {'Requests':<10} {'Created':<20} {'Expires':<20}")
        print("-" * 100)
        
        for key in keys:
            status = "✅ Yes" if key.is_active is True else "❌ No"
            created = key.created_at.strftime("%Y-%m-%d %H:%M") if key.created_at is not None else "N/A"
            expires = key.expires_at.strftime("%Y-%m-%d %H:%M") if key.expires_at is not None else "Never"
            
            print(f"{key.id:<5} {key.name:<25} {status:<8} {key.request_count:<10} {created:<20} {expires:<20}")


async def revoke_key(key_id: int):
    """Revoke (deactivate) an API key."""
    async with get_async_session() as session:
        repo = APIKeyRepository(session)
        success = await repo.revoke_key(key_id)
        
        if success:
            print(f"✅ API key #{key_id} revoked successfully")
        else:
            print(f"❌ API key #{key_id} not found")


async def delete_key(key_id: int):
    """Permanently delete an API key."""
    async with get_async_session() as session:
        repo = APIKeyRepository(session)
        
        # Get key details first
        api_key = await repo.get_by_id(key_id)
        if not api_key:
            print(f"❌ API key #{key_id} not found")
            return
        
        # Confirm deletion
        print(f"\n⚠️  Warning: You are about to permanently delete:")
        print(f"  ID:   {api_key.id}")
        print(f"  Name: {api_key.name}")
        print(f"  Requests: {api_key.request_count}")
        
        confirm = input("\nType 'DELETE' to confirm: ")
        if confirm != "DELETE":
            print("❌ Deletion cancelled")
            return
        
        success = await repo.delete_key(key_id)
        if success:
            print(f"✅ API key #{key_id} deleted permanently")


async def show_key_info(key_id: int):
    """Show detailed information about an API key."""
    async with get_async_session() as session:
        repo = APIKeyRepository(session)
        api_key = await repo.get_by_id(key_id)
        
        if not api_key:
            print(f"❌ API key #{key_id} not found")
            return
        
        print(f"\n📝 API Key Details:\n")
        print(f"  ID:           {api_key.id}")
        print(f"  Name:         {api_key.name}")
        print(f"  Description:  {api_key.description or 'N/A'}")
        print(f"  Active:       {'✅ Yes' if api_key.is_active is True else '❌ No'}")
        print(f"  Created:      {api_key.created_at}")
        print(f"  Expires:      {api_key.expires_at or 'Never'}")
        print(f"  Last Used:    {api_key.last_used_at or 'Never'}")
        print(f"  Request Count: {api_key.request_count}")


def print_help():
    """Print usage help."""
    print("""
🔑 API Key Management Tool

Usage:
  python scripts/manage_api_keys.py <command> [arguments]

Commands:
  create <name> [--description DESC] [--days DAYS]
      Create a new API key
      --description: Optional description
      --days: Days until expiration (default: never)
      
      Example: python scripts/manage_api_keys.py create "Production App" --description "Main production key" --days 365

  list [--all]
      List all API keys
      --all: Include inactive keys
      
      Example: python scripts/manage_api_keys.py list

  info <id>
      Show detailed information about an API key
      
      Example: python scripts/manage_api_keys.py info 1

  revoke <id>
      Revoke (deactivate) an API key
      
      Example: python scripts/manage_api_keys.py revoke 1

  delete <id>
      Permanently delete an API key (requires confirmation)
      
      Example: python scripts/manage_api_keys.py delete 1

  help
      Show this help message
""")


async def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help":
        print_help()
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Error: Name is required")
            print("Usage: python scripts/manage_api_keys.py create <name> [--description DESC] [--days DAYS]")
            return
        
        name = sys.argv[2]
        description = None
        days_valid = None
        
        # Parse optional arguments
        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--description" and i + 1 < len(sys.argv):
                description = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--days" and i + 1 < len(sys.argv):
                try:
                    days_valid = int(sys.argv[i + 1])
                except ValueError:
                    print(f"❌ Error: Invalid days value: {sys.argv[i + 1]}")
                    return
                i += 2
            else:
                i += 1
        
        await create_key(name, description, days_valid)
    
    elif command == "list":
        include_inactive = "--all" in sys.argv
        await list_keys(include_inactive)
    
    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Error: Key ID is required")
            print("Usage: python scripts/manage_api_keys.py info <id>")
            return
        
        try:
            key_id = int(sys.argv[2])
            await show_key_info(key_id)
        except ValueError:
            print(f"❌ Error: Invalid key ID: {sys.argv[2]}")
    
    elif command == "revoke":
        if len(sys.argv) < 3:
            print("❌ Error: Key ID is required")
            print("Usage: python scripts/manage_api_keys.py revoke <id>")
            return
        
        try:
            key_id = int(sys.argv[2])
            await revoke_key(key_id)
        except ValueError:
            print(f"❌ Error: Invalid key ID: {sys.argv[2]}")
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Error: Key ID is required")
            print("Usage: python scripts/manage_api_keys.py delete <id>")
            return
        
        try:
            key_id = int(sys.argv[2])
            await delete_key(key_id)
        except ValueError:
            print(f"❌ Error: Invalid key ID: {sys.argv[2]}")
    
    else:
        print(f"❌ Error: Unknown command '{command}'")
        print_help()


if __name__ == "__main__":
    asyncio.run(main())
