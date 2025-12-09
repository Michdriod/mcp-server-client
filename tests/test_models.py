"""
Unit Tests for Database Models and Connections
"""
import pytest
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from server.db.models import Base, User, QueryHistory, SavedQuery, ScheduledReport


@pytest.fixture
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def test_session(test_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_user_creation(test_session):
    """Test creating a user"""
    user = User(
        username="testuser",
        email="test@example.com",
        role="analyst",
        is_active=True
    )
    
    test_session.add(user)
    await test_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_query_history(test_session):
    """Test query history creation"""
    user = User(username="testuser", email="test@example.com", role="admin")
    test_session.add(user)
    await test_session.commit()
    
    history = QueryHistory(
        user_id=user.id,
        natural_query="Show top customers",
        sql_query="SELECT * FROM customers LIMIT 10",
        execution_time_ms=150.5,
        row_count=10,
        cached=False
    )
    
    test_session.add(history)
    await test_session.commit()
    
    assert history.id is not None
    assert history.user_id == user.id
    assert history.execution_time_ms == 150.5


@pytest.mark.asyncio
async def test_saved_query(test_session):
    """Test saved query creation"""
    user = User(username="testuser", email="test@example.com", role="admin")
    test_session.add(user)
    await test_session.commit()
    
    saved = SavedQuery(
        user_id=user.id,
        name="Top Customers",
        description="Shows top 10 customers",
        natural_query="Show top 10 customers by revenue"
    )
    
    test_session.add(saved)
    await test_session.commit()
    
    assert saved.id is not None
    assert saved.name == "Top Customers"


@pytest.mark.asyncio
async def test_scheduled_report(test_session):
    """Test scheduled report creation"""
    user = User(username="testuser", email="test@example.com", role="admin")
    test_session.add(user)
    await test_session.commit()
    
    report = ScheduledReport(
        user_id=user.id,
        name="Daily Report",
        natural_query="Show today's sales",
        schedule="0 9 * * *",
        email="user@example.com",
        export_format="excel",
        is_active=True
    )
    
    test_session.add(report)
    await test_session.commit()
    
    assert report.id is not None
    assert report.schedule == "0 9 * * *"
    assert report.is_active is True
