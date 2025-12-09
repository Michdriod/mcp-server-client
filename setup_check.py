#!/usr/bin/env python3
"""
Quick setup script to initialize the database and cache connections.
Run this to verify Phase 1 setup is working correctly.
"""
import asyncio
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def check_environment():
    """Check if .env file exists and is configured."""
    import os
    from pathlib import Path
    
    env_path = Path(".env")
    if not env_path.exists():
        console.print("[red]❌ .env file not found![/red]")
        console.print("[yellow]💡 Copy .env.example to .env and configure it[/yellow]")
        return False
    
    # Check for required variables
    required_vars = ["DATABASE_URL", "REDIS_URL", "GROQ_API_KEY"]
    missing = []
    
    from dotenv import load_dotenv
    load_dotenv()
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        console.print(f"[red]❌ Missing required environment variables: {', '.join(missing)}[/red]")
        return False
    
    console.print("[green]✅ Environment configuration loaded[/green]")
    return True


async def test_database_connection():
    """Test database connection."""
    try:
        from server.db import db
        
        console.print("[cyan]Testing database connection...[/cyan]")
        db.initialize()
        
        # Try to connect
        async with db.session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.scalar_one()
        
        console.print("[green]✅ Database connection successful[/green]")
        await db.close()
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Database connection failed: {e}[/red]")
        return False


async def test_redis_connection():
    """Test Redis connection."""
    try:
        from server.cache import cache
        
        console.print("[cyan]Testing Redis connection...[/cyan]")
        cache.initialize()
        
        # Try to set and get a value
        await cache.client.set("test_key", "test_value", ex=10)
        value = await cache.client.get("test_key")
        await cache.client.delete("test_key")
        
        if value.decode("utf-8") == "test_value":
            console.print("[green]✅ Redis connection successful[/green]")
            await cache.close()
            return True
        else:
            console.print("[red]❌ Redis test failed[/red]")
            return False
        
    except Exception as e:
        console.print(f"[red]❌ Redis connection failed: {e}[/red]")
        return False


async def display_configuration():
    """Display current configuration."""
    from shared.config import settings
    
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    # Database
    table.add_row("Database URL", settings.database_url.split("@")[-1] if "@" in settings.database_url else "***")
    table.add_row("Pool Size", str(settings.database_pool_size))
    table.add_row("Max Overflow", str(settings.database_max_overflow))
    
    # Redis
    table.add_row("Redis URL", settings.redis_url)
    table.add_row("Query Cache TTL", f"{settings.query_cache_ttl_seconds}s")
    
    # Query Settings
    table.add_row("Query Timeout", f"{settings.query_timeout_seconds}s")
    table.add_row("Max Results", str(settings.max_query_results))
    table.add_row("Rate Limit", f"{settings.rate_limit_per_user_per_hour}/hour")
    
    # Environment
    table.add_row("Environment", settings.environment)
    
    console.print(table)


async def main():
    """Main setup and verification."""
    console.print(Panel.fit(
        "[bold cyan]Database Query Assistant - Phase 1 Setup[/bold cyan]\n"
        "Verifying core infrastructure...",
        border_style="cyan"
    ))
    
    # Check environment
    if not await check_environment():
        console.print("\n[yellow]Please configure your .env file first[/yellow]")
        sys.exit(1)
    
    console.print()
    
    # Display configuration
    await display_configuration()
    
    console.print()
    
    # Test connections
    db_ok = await test_database_connection()
    redis_ok = await test_redis_connection()
    
    console.print()
    
    # Summary
    if db_ok and redis_ok:
        console.print(Panel.fit(
            "[bold green]🎉 Phase 1 Setup Complete![/bold green]\n\n"
            "✅ Database connection working\n"
            "✅ Redis cache working\n"
            "✅ Configuration loaded\n\n"
            "[cyan]Next steps:[/cyan]\n"
            "1. Run database migrations: [yellow]alembic upgrade head[/yellow]\n"
            "2. Proceed to Phase 2 implementation",
            border_style="green"
        ))
        sys.exit(0)
    else:
        console.print(Panel.fit(
            "[bold red]❌ Setup Issues Detected[/bold red]\n\n"
            "Please fix the connection issues above and try again.",
            border_style="red"
        ))
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)
