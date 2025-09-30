"""
Redis Cache Service
"""
import redis.asyncio as redis
from typing import Optional, Any
import json
from functools import wraps
from src.api.config import settings
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service wrapper"""

    def __init__(self):
        self.client: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis client"""
        try:
            self.client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.client.ping()
            logger.info("Redis client initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available: {e}")
            self.client = None

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 60):
        """Set value in cache with TTL"""
        if not self.client:
            return

        try:
            serialized = json.dumps(value, default=str)
            await self.client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")

    async def delete(self, pattern: str):
        """Delete keys matching pattern"""
        if not self.client:
            return

        try:
            keys = await self.client.keys(pattern)
            if keys:
                await self.client.delete(*keys)
        except Exception as e:
            logger.error(f"Cache delete error for pattern {pattern}: {e}")

    async def close(self):
        """Close Redis connection"""
        if self.client:
            await self.client.close()


def cache_response(ttl: int = 60, key_prefix: str = ""):
    """Decorator for caching endpoint responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}"

            # Add args to cache key
            if args:
                cache_key += f":{':'.join(str(arg) for arg in args[1:])}"  # Skip 'self'

            # Add kwargs to cache key
            if kwargs:
                cache_key += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

            # Try to get from cache
            cached = await cache_service.get(cache_key)
            if cached is not None:
                return cached

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_service.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator


# Singleton instance
cache_service = CacheService()