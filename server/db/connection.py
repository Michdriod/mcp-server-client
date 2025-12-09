"""
Database connection management with async SQLAlchemy.
Implements connection pooling for scalability.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from shared.config import settings


class DatabaseConnection:
    """Manages database connections with pooling."""
    
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            return
        
        self._engine = create_async_engine(
            settings.database_url,
            echo=False,  # Disable SQL logging to prevent STDIO pollution
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,    # Recycle connections after 1 hour
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
        
        # Test the connection
        async with self._engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    
    async def close(self) -> None:
        """Close database engine and cleanup connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    @property
    def engine(self) -> AsyncEngine:
        """Get the database engine."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session as a context manager.
        
        Usage:
            async with db.session() as session:
                result = await session.execute(query)
        """
        # Auto-initialize if not already done
        if self._session_factory is None:
            await self.initialize()
            
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


# Global database connection instance
db = DatabaseConnection()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database sessions.
    
    Usage in FastMCP or FastAPI:
        @app.tool()
        async def my_tool(session: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with db.session() as session:
        yield session
