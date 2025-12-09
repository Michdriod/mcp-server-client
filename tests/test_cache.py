"""
Unit Tests for Cache Layer
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from server.cache.redis_cache import RedisCache


@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    redis_mock = AsyncMock()
    redis_mock.get = AsyncMock(return_value=None)
    redis_mock.setex = AsyncMock()
    redis_mock.delete = AsyncMock()
    redis_mock.exists = AsyncMock(return_value=0)
    return redis_mock


@pytest.fixture
def cache(mock_redis):
    """Create cache instance with mocked Redis"""
    with patch('server.cache.redis_cache.redis.from_url', return_value=mock_redis):
        cache = RedisCache("redis://localhost")
        cache.client = mock_redis
        return cache


@pytest.mark.asyncio
async def test_cache_set_get(cache, mock_redis):
    """Test setting and getting cache values"""
    # Set value
    await cache.set("test_key", {"data": "value"}, ttl=300)
    mock_redis.setex.assert_called_once()
    
    # Get value (cache miss first)
    result = await cache.get("test_key")
    assert result is None
    
    # Simulate cache hit
    import json
    mock_redis.get.return_value = json.dumps({"data": "value"})
    result = await cache.get("test_key")
    assert result == {"data": "value"}


@pytest.mark.asyncio
async def test_cache_delete(cache, mock_redis):
    """Test cache deletion"""
    await cache.delete("test_key")
    mock_redis.delete.assert_called_once_with("test_key")


@pytest.mark.asyncio
async def test_cache_exists(cache, mock_redis):
    """Test cache existence check"""
    mock_redis.exists.return_value = 1
    exists = await cache.exists("test_key")
    assert exists is True
    
    mock_redis.exists.return_value = 0
    exists = await cache.exists("test_key")
    assert exists is False


@pytest.mark.asyncio
async def test_cache_key_generation():
    """Test cache key generation"""
    from server.cache.redis_cache import generate_cache_key
    
    key = generate_cache_key("query", user_id=1, query="SELECT * FROM users")
    assert "query" in key
    assert "1" in key
    
    # Same inputs should generate same key
    key2 = generate_cache_key("query", user_id=1, query="SELECT * FROM users")
    assert key == key2
    
    # Different inputs should generate different keys
    key3 = generate_cache_key("query", user_id=2, query="SELECT * FROM users")
    assert key != key3
