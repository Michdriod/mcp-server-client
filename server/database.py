"""Database dependency for FastAPI."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from shared.config import settings

# Synchronous database connection for authentication
SYNC_DATABASE_URL = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")

sync_engine = create_engine(SYNC_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)

def get_db() -> Session: # type: ignore
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()