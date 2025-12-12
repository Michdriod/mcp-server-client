#!/usr/bin/env python3
"""
Database table recreation script.
Drops and recreates the scheduled_reports table with the correct schema.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.db.connection import db
from server.db.models import ScheduledReport
from sqlalchemy import text


async def recreate_table():
    """Drop and recreate the scheduled_reports table."""
    print("🔧 Recreating scheduled_reports table...")
    
    try:
        # Initialize connection
        await db.initialize()
        print("✅ Database connection established")
        
        # Drop the existing table and enums
        async with db.engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS scheduled_reports CASCADE"))
            print("✅ Dropped existing scheduled_reports table")
            
            # Drop and recreate enum types
            await conn.execute(text("DROP TYPE IF EXISTS reportstatus CASCADE"))
            await conn.execute(text("DROP TYPE IF EXISTS reportformat CASCADE"))
            print("✅ Dropped existing enum types")
            
            # Create the table with correct schema
            await conn.run_sync(ScheduledReport.__table__.create)
            print("✅ Created scheduled_reports table with correct schema")
        
        # Verify the table structure
        async with db.session() as session:
            result = await session.execute(text('SELECT column_name FROM information_schema.columns WHERE table_name = \'scheduled_reports\' ORDER BY ordinal_position'))
            columns = [row[0] for row in result.fetchall()]
            print("✅ New table columns:", columns)
            
    except Exception as e:
        print(f"❌ Failed to recreate table: {e}")
        sys.exit(1)
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(recreate_table())