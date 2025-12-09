"""
Integration Tests for MCP Server
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from client.mcp_client import QueryAssistantClient


@pytest.fixture
async def mock_server():
    """Mock MCP server responses"""
    with patch('client.mcp_client.stdio_client') as mock:
        mock_session = AsyncMock()
        mock_session.call_tool = AsyncMock()
        mock.__aenter__ = AsyncMock(return_value=(mock_session, None))
        mock.__aexit__ = AsyncMock()
        yield mock_session


@pytest.mark.asyncio
async def test_query_database(mock_server):
    """Test query execution through MCP"""
    # Mock response
    mock_server.call_tool.return_value = AsyncMock(
        content=[
            AsyncMock(
                text='{"results": [{"id": 1, "name": "Test"}], "row_count": 1, "column_count": 2, "execution_time_ms": 50.0, "cached": false}'
            )
        ]
    )
    
    async with QueryAssistantClient() as client:
        result = await client.query_database("Show test data", user_id=1)
        
        assert result is not None
        assert "results" in result
        assert result["row_count"] == 1


@pytest.mark.asyncio
async def test_save_query(mock_server):
    """Test saving a query through MCP"""
    mock_server.call_tool.return_value = AsyncMock(
        content=[AsyncMock(text='{"query_id": 123}')]
    )
    
    async with QueryAssistantClient() as client:
        result = await client.save_query(
            user_id=1,
            name="Test Query",
            description="Test description",
            query="Show test data"
        )
        
        assert result is not None
        assert "query_id" in result
        assert result["query_id"] == 123


@pytest.mark.asyncio
async def test_list_tables(mock_server):
    """Test listing tables through MCP"""
    mock_server.call_tool.return_value = AsyncMock(
        content=[AsyncMock(text='["users", "products", "orders"]')]
    )
    
    async with QueryAssistantClient() as client:
        tables = await client.list_tables()
        
        assert isinstance(tables, list)
        assert "users" in tables
        assert "products" in tables


@pytest.mark.asyncio
async def test_export_query_results(mock_server):
    """Test exporting query results"""
    mock_server.call_tool.return_value = AsyncMock(
        content=[AsyncMock(text='{"file_path": "/path/to/export.xlsx"}')]
    )
    
    async with QueryAssistantClient() as client:
        result = await client.export_query_results(
            user_id=1,
            query="Show test data",
            format="excel"
        )
        
        assert result is not None
        assert "file_path" in result


@pytest.mark.asyncio
async def test_create_scheduled_report(mock_server):
    """Test creating a scheduled report"""
    mock_server.call_tool.return_value = AsyncMock(
        content=[AsyncMock(text='{"schedule_id": 456}')]
    )
    
    async with QueryAssistantClient() as client:
        result = await client.create_scheduled_report(
            user_id=1,
            name="Daily Report",
            query="Show daily data",
            schedule="0 9 * * *",
            email="test@example.com",
            format="excel"
        )
        
        assert result is not None
        assert "schedule_id" in result
        assert result["schedule_id"] == 456
