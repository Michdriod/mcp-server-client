#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables defined in the models.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.db.connection import db
from server.db.models import Base
from shared.config import settings


async def init_database():
    """Initialize database by creating all tables."""
    print("🔧 Initializing database...")
    print(f"📍 Database URL: {settings.database_url}")
    
    try:
        # Initialize connection
        await db.initialize()
        print("✅ Database connection established")
        
        # Create all tables
        async with db.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ Database tables created successfully")
        
        # Test the connection
        async with db.session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print("✅ Database connection test passed")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(init_database())