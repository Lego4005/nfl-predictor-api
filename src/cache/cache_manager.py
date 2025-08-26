"""
Cache Manager for NFL Predictor live data integration.

Provides Redis-based caching with TTL management and in-memory fallback.
Implements cache key generation, expiration handling, and health monitoring.
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass
from enum import Enum

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheStatus(Enum):
    """Cache status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    data: Any
    timestamp: datetime
    ttl_minutes: int
    source: str
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        expiry_time = self.timestamp + timedelta(minutes=self.ttl_minutes)
        return datetime.utcnow() > expiry_time
    
    @property
    def age_minutes(self) -> float:
        """Get age of cache entry in minutes."""
        delta = datetime.utcnow() - self.timestamp
        return delta.total_seconds() / 60


class CacheManager:
    """
    Cache Manager with Redis integration and in-memory fallback.
    
    Provides TTL-based cache expiration (30 minutes default),
    cache key generation, and health monitoring.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_ttl_minutes: int = 30,
        max_memory_cache_size: int = 1000
    ):
        """
        Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL
            default_ttl_minutes: Default TTL for cache entries
            max_memory_cache_size: Maximum in-memory cache entries
        """
        self.redis_url = redis_url
        self.default_ttl_minutes = default_ttl_minutes
        self.max_memory_cache_size = max_memory_cache_size
        
        # In-memory cache fallback
        self._memory_cache: Dict[str, CacheEntry] = {}
        
        # Redis client
        self._redis_client: Optional[redis.Redis] = None
        self._redis_healthy = False
        
        # Initialize Redis connection
        self._initialize_redis()
    
    def _initialize_redis(self) -> None:
        """Initialize Redis connection."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using in-memory cache only")
            return
        
        try:
            self._redis_client = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            self._redis_client.ping()
            self._redis_healthy = True
            logger.info("Redis connection established successfully")
            
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self._redis_healthy = False
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from prefix and parameters.
        
        Args:
            prefix: Cache key prefix
            **kwargs: Key-value pairs to include in key
            
        Returns:
            Generated cache key
        """
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        param_string = "&".join(f"{k}={v}" for k, v in sorted_params)
        
        # Create hash for long parameter strings
        if len(param_string) > 100:
            param_hash = hashlib.md5(param_string.encode()).hexdigest()[:8]
            return f"nfl_predictor:{prefix}:{param_hash}"
        
        return f"nfl_predictor:{prefix}:{param_string}"
    
    def _cleanup_memory_cache(self) -> None:
        """Clean up expired entries and enforce size limits."""
        # Remove expired entries
        expired_keys = [
            key for key, entry in self._memory_cache.items()
            if entry.is_expired
        ]
        
        for key in expired_keys:
            del self._memory_cache[key]
        
        # Enforce size limit (remove oldest entries)
        if len(self._memory_cache) > self.max_memory_cache_size:
            # Sort by timestamp and remove oldest
            sorted_items = sorted(
                self._memory_cache.items(),
                key=lambda x: x[1].timestamp
            )
            
            excess_count = len(self._memory_cache) - self.max_memory_cache_size
            for key, _ in sorted_items[:excess_count]:
                del self._memory_cache[key]
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached data by key.
        
        Args:
            key: Cache key
            
        Returns:
            Cached data with metadata or None if not found/expired
        """
        # Try Redis first if available
        if self._redis_healthy and self._redis_client:
            try:
                cached_data = self._redis_client.get(key)
                if cached_data:
                    entry_dict = json.loads(cached_data)
                    entry = CacheEntry(
                        data=entry_dict['data'],
                        timestamp=datetime.fromisoformat(entry_dict['timestamp']),
                        ttl_minutes=entry_dict['ttl_minutes'],
                        source=entry_dict['source']
                    )
                    
                    if not entry.is_expired:
                        return {
                            'data': entry.data,
                            'cached': True,
                            'source': entry.source,
                            'timestamp': entry.timestamp.isoformat(),
                            'age_minutes': entry.age_minutes
                        }
                    else:
                        # Remove expired entry
                        self._redis_client.delete(key)
                        
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
                self._redis_healthy = False
        
        # Fallback to memory cache
        if key in self._memory_cache:
            entry = self._memory_cache[key]
            if not entry.is_expired:
                return {
                    'data': entry.data,
                    'cached': True,
                    'source': entry.source,
                    'timestamp': entry.timestamp.isoformat(),
                    'age_minutes': entry.age_minutes
                }
            else:
                # Remove expired entry
                del self._memory_cache[key]
        
        return None
    
    def set(
        self,
        key: str,
        data: Any,
        source: str,
        ttl_minutes: Optional[int] = None
    ) -> bool:
        """
        Set cached data with TTL.
        
        Args:
            key: Cache key
            data: Data to cache
            source: Data source identifier
            ttl_minutes: TTL in minutes (uses default if None)
            
        Returns:
            True if successfully cached
        """
        ttl = ttl_minutes or self.default_ttl_minutes
        timestamp = datetime.utcnow()
        
        entry = CacheEntry(
            data=data,
            timestamp=timestamp,
            ttl_minutes=ttl,
            source=source
        )
        
        success = False
        
        # Try Redis first if available
        if self._redis_healthy and self._redis_client:
            try:
                entry_dict = {
                    'data': data,
                    'timestamp': timestamp.isoformat(),
                    'ttl_minutes': ttl,
                    'source': source
                }
                
                # Set with TTL in seconds
                ttl_seconds = ttl * 60
                self._redis_client.setex(
                    key,
                    ttl_seconds,
                    json.dumps(entry_dict, default=str)
                )
                success = True
                
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
                self._redis_healthy = False
        
        # Always store in memory cache as backup
        self._memory_cache[key] = entry
        self._cleanup_memory_cache()
        
        return success or True  # Memory cache always succeeds
    
    def delete(self, key: str) -> bool:
        """
        Delete cached data by key.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted
        """
        deleted = False
        
        # Delete from Redis
        if self._redis_healthy and self._redis_client:
            try:
                result = self._redis_client.delete(key)
                deleted = result > 0
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")
                self._redis_healthy = False
        
        # Delete from memory cache
        if key in self._memory_cache:
            del self._memory_cache[key]
            deleted = True
        
        return deleted
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.
        
        Args:
            pattern: Pattern to match (supports wildcards)
            
        Returns:
            Number of keys invalidated
        """
        count = 0
        
        # Invalidate in Redis
        if self._redis_healthy and self._redis_client:
            try:
                keys = self._redis_client.keys(pattern)
                if keys:
                    count += self._redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis pattern invalidation failed: {e}")
                self._redis_healthy = False
        
        # Invalidate in memory cache
        import fnmatch
        memory_keys = [
            key for key in self._memory_cache.keys()
            if fnmatch.fnmatch(key, pattern)
        ]
        
        for key in memory_keys:
            del self._memory_cache[key]
            count += 1
        
        return count
    
    def get_cache_key_for_predictions(
        self,
        week: int,
        prediction_type: str,
        year: int = 2025
    ) -> str:
        """
        Generate cache key for NFL predictions.
        
        Args:
            week: NFL week number
            prediction_type: Type of prediction (games, props, fantasy)
            year: NFL season year
            
        Returns:
            Cache key for predictions
        """
        return self._generate_cache_key(
            "predictions",
            year=year,
            week=week,
            type=prediction_type
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get cache health status and metrics.
        
        Returns:
            Health status information
        """
        status = {
            'redis_healthy': self._redis_healthy,
            'memory_cache_size': len(self._memory_cache),
            'memory_cache_limit': self.max_memory_cache_size,
            'default_ttl_minutes': self.default_ttl_minutes
        }
        
        if self._redis_healthy and self._redis_client:
            try:
                info = self._redis_client.info()
                status.update({
                    'redis_memory_used': info.get('used_memory_human', 'unknown'),
                    'redis_connected_clients': info.get('connected_clients', 0),
                    'redis_uptime_seconds': info.get('uptime_in_seconds', 0)
                })
            except Exception as e:
                logger.warning(f"Failed to get Redis info: {e}")
                status['redis_healthy'] = False
                self._redis_healthy = False
        
        # Determine overall status
        if self._redis_healthy:
            status['overall_status'] = CacheStatus.HEALTHY.value
        elif len(self._memory_cache) > 0:
            status['overall_status'] = CacheStatus.DEGRADED.value
        else:
            status['overall_status'] = CacheStatus.UNAVAILABLE.value
        
        return status
    
    def warm_cache(self, data_fetcher, keys_to_warm: list) -> Dict[str, bool]:
        """
        Warm cache with popular data.
        
        Args:
            data_fetcher: Function to fetch data for cache warming
            keys_to_warm: List of cache keys to warm
            
        Returns:
            Dictionary of key -> success status
        """
        results = {}
        
        for key in keys_to_warm:
            try:
                # Check if already cached and fresh
                cached = self.get(key)
                if cached and cached['age_minutes'] < 15:  # Fresh within 15 minutes
                    results[key] = True
                    continue
                
                # Fetch fresh data
                data = data_fetcher(key)
                if data:
                    success = self.set(key, data, 'cache_warming')
                    results[key] = success
                else:
                    results[key] = False
                    
            except Exception as e:
                logger.warning(f"Cache warming failed for key {key}: {e}")
                results[key] = False
        
        return results