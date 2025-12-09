"""
Redis caching layer for query results, schema metadata, and permissions.
Implements multi-tier caching strategy for optimal performance.
"""
import hashlib
import json
from typing import Any, Optional

import redis.asyncio as aioredis
from redis.asyncio.connection import ConnectionPool

from shared.config import settings


class RedisCache:
    """Redis caching manager with connection pooling."""
    
    # Cache key prefixes
    QUERY_RESULT_PREFIX = "query:result:"
    SCHEMA_META_PREFIX = "schema:meta:"
    USER_PERM_PREFIX = "user:perm:"
    RATE_LIMIT_PREFIX = "rate:limit:"
    
    # Cache TTLs (in seconds)
    QUERY_RESULT_TTL = settings.query_cache_ttl_seconds  # 5 minutes
    SCHEMA_META_TTL = 3600  # 1 hour
    USER_PERM_TTL = 900  # 15 minutes
    RATE_LIMIT_TTL = 3600  # 1 hour
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._disabled: bool = False  # Flag to disable cache on connection failure
    
    def initialize(self) -> None:
        """Initialize Redis connection pool."""
        if self._pool is not None:
            return
        
        if self._disabled:
            print("⚠️  Redis cache is disabled due to previous connection failure")
            return
        
        try:
            self._pool = ConnectionPool.from_url(
                settings.redis_url,
                max_connections=settings.redis_max_connections,
                decode_responses=False,  # We'll handle encoding/decoding
            )
            self._client = aioredis.Redis(connection_pool=self._pool)
            print("✅ Redis cache initialized successfully")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print("⚠️  Continuing without cache - queries will not be cached")
            self._disabled = True
            self._client = None
            self._pool = None
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        
        if self._pool is not None:
            await self._pool.aclose()
            self._pool = None
    
    @property
    def client(self) -> aioredis.Redis:
        """Get Redis client."""
        if self._disabled:
            raise RuntimeError("Redis cache is disabled")
        if self._client is None:
            raise RuntimeError("Redis not initialized. Call initialize() first.")
        return self._client
    
    @staticmethod
    def _generate_query_key(sql: str, params: Optional[dict] = None) -> str:
        """Generate cache key for query results using content hash."""
        content = sql
        if params:
            content += json.dumps(params, sort_keys=True)
        
        hash_digest = hashlib.sha256(content.encode()).hexdigest()
        return f"{RedisCache.QUERY_RESULT_PREFIX}{hash_digest}"
    
    @staticmethod
    def _generate_schema_key(database: str, table: str) -> str:
        """Generate cache key for schema metadata."""
        return f"{RedisCache.SCHEMA_META_PREFIX}{database}:{table}"
    
    @staticmethod
    def _generate_permission_key(user_id: int, database: str, table: str) -> str:
        """Generate cache key for user permissions."""
        return f"{RedisCache.USER_PERM_PREFIX}{user_id}:{database}:{table}"
    
    @staticmethod
    def _generate_rate_limit_key(user_id: int) -> str:
        """Generate cache key for rate limiting."""
        return f"{RedisCache.RATE_LIMIT_PREFIX}{user_id}"
    
    async def get(self, key: str) -> Optional[dict]:
        """
        Get a cached value by key.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value as dict or None if not found
        """
        if self._disabled or self._client is None:
            return None
        
        try:
            data = await self.client.get(key)
            if data:
                return json.loads(data.decode())
            return None
        except Exception:
            return None
    
    async def set(
        self, key: str, value: dict, expire: Optional[int] = None
    ) -> bool:
        """
        Set a cached value.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON serializable)
            expire: Expiration time in seconds (optional)
        
        Returns:
            True if successful, False otherwise
        """
        if self._disabled or self._client is None:
            return False
        
        try:
            data = json.dumps(value).encode()
            if expire:
                await self.client.setex(key, expire, data)
            else:
                await self.client.set(key, data)
            return True
        except Exception:
            return False
    
    async def get_query_result(
        self, sql: str, params: Optional[dict] = None
    ) -> Optional[list[dict]]:
        """
        Get cached query result.
        
        Args:
            sql: SQL query string
            params: Query parameters
        
        Returns:
            Cached query result or None if not found
        """
        key = self._generate_query_key(sql, params)
        data = await self.client.get(key)
        
        if data is None:
            return None
        
        return json.loads(data.decode("utf-8"))
    
    async def set_query_result(
        self, sql: str, result: list[dict], params: Optional[dict] = None
    ) -> None:
        """
        Cache query result.
        
        Args:
            sql: SQL query string
            result: Query result to cache
            params: Query parameters
        """
        key = self._generate_query_key(sql, params)
        data = json.dumps(result).encode("utf-8")
        await self.client.setex(key, self.QUERY_RESULT_TTL, data)
    
    async def get_schema_metadata(
        self, database: str, table: str
    ) -> Optional[dict[str, Any]]:
        """
        Get cached schema metadata.
        
        Args:
            database: Database name
            table: Table name
        
        Returns:
            Schema metadata or None if not found
        """
        key = self._generate_schema_key(database, table)
        data = await self.client.get(key)
        
        if data is None:
            return None
        
        return json.loads(data.decode("utf-8"))
    
    async def set_schema_metadata(
        self, database: str, table: str, metadata: dict[str, Any]
    ) -> None:
        """
        Cache schema metadata.
        
        Args:
            database: Database name
            table: Table name
            metadata: Schema metadata to cache
        """
        key = self._generate_schema_key(database, table)
        data = json.dumps(metadata).encode("utf-8")
        await self.client.setex(key, self.SCHEMA_META_TTL, data)
    
    async def get_user_permissions(
        self, user_id: int, database: str, table: str
    ) -> Optional[dict[str, Any]]:
        """
        Get cached user permissions.
        
        Args:
            user_id: User ID
            database: Database name
            table: Table name
        
        Returns:
            User permissions or None if not found
        """
        key = self._generate_permission_key(user_id, database, table)
        data = await self.client.get(key)
        
        if data is None:
            return None
        
        return json.loads(data.decode("utf-8"))
    
    async def set_user_permissions(
        self, user_id: int, database: str, table: str, permissions: dict[str, Any]
    ) -> None:
        """
        Cache user permissions.
        
        Args:
            user_id: User ID
            database: Database name
            table: Table name
            permissions: User permissions to cache
        """
        key = self._generate_permission_key(user_id, database, table)
        data = json.dumps(permissions).encode("utf-8")
        await self.client.setex(key, self.USER_PERM_TTL, data)
    
    async def invalidate_query_cache(self) -> None:
        """Invalidate all query result caches."""
        pattern = f"{self.QUERY_RESULT_PREFIX}*"
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)
    
    async def invalidate_schema_cache(self, database: str, table: str) -> None:
        """Invalidate schema cache for specific table."""
        key = self._generate_schema_key(database, table)
        await self.client.delete(key)
    
    async def invalidate_user_permissions(self, user_id: int) -> None:
        """Invalidate all permissions for a user."""
        pattern = f"{self.USER_PERM_PREFIX}{user_id}:*"
        async for key in self.client.scan_iter(match=pattern):
            await self.client.delete(key)
    
    async def check_rate_limit(self, user_id: int, limit: int) -> bool:
        """
        Check if user has exceeded rate limit.
        
        Args:
            user_id: User ID
            limit: Maximum requests per hour
        
        Returns:
            True if within limit, False if exceeded
        """
        key = self._generate_rate_limit_key(user_id)
        current = await self.client.get(key)
        
        if current is None:
            # First request in this hour
            await self.client.setex(key, self.RATE_LIMIT_TTL, "1")
            return True
        
        count = int(current.decode("utf-8"))
        if count >= limit:
            return False
        
        # Increment counter
        await self.client.incr(key)
        return True
    
    async def get_rate_limit_remaining(self, user_id: int, limit: int) -> int:
        """
        Get remaining requests for user.
        
        Args:
            user_id: User ID
            limit: Maximum requests per hour
        
        Returns:
            Number of remaining requests
        """
        key = self._generate_rate_limit_key(user_id)
        current = await self.client.get(key)
        
        if current is None:
            return limit
        
        count = int(current.decode("utf-8"))
        return max(0, limit - count)


# Global cache instance
cache = RedisCache()
