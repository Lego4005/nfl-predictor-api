"""
Advanced Cache Manager for Betting Analytics

Provides intelligent caching with:
- Multi-level caching (memory + Redis)
- Cache warming strategies
- TTL optimization based on data volatility
- Cache invalidation patterns
- Performance monitoring
"""

import redis
import json
import pickle
import hashlib
import asyncio
from typing import Dict, Any, Optional, List, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from functools import wraps
import time
import threading
from collections import defaultdict, OrderedDict

logger = logging.getLogger(__name__)

class CacheLevel(Enum):
    MEMORY = "memory"
    REDIS = "redis"
    BOTH = "both"

class DataVolatility(Enum):
    """Data volatility levels affecting cache TTL"""
    STATIC = "static"      # Rarely changes (historical data)
    STABLE = "stable"      # Changes infrequently (team stats)
    DYNAMIC = "dynamic"    # Changes regularly (odds, lines)
    VOLATILE = "volatile"  # Changes frequently (live data)

@dataclass
class CacheConfig:
    """Configuration for cache behavior"""
    default_ttl: int = 300  # 5 minutes
    memory_limit: int = 1000  # Max items in memory cache
    volatility_ttls: Dict[DataVolatility, int] = None
    compression: bool = True
    metrics_enabled: bool = True

    def __post_init__(self):
        if self.volatility_ttls is None:
            self.volatility_ttls = {
                DataVolatility.STATIC: 86400,    # 24 hours
                DataVolatility.STABLE: 3600,     # 1 hour
                DataVolatility.DYNAMIC: 300,     # 5 minutes
                DataVolatility.VOLATILE: 60      # 1 minute
            }

@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    redis_calls: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0

    @property
    def total_operations(self) -> int:
        return self.hits + self.misses + self.sets + self.deletes

class CacheManager:
    """Advanced cache manager with multi-level caching and intelligent TTL"""

    def __init__(self, redis_url: str = "redis://localhost:6379", config: CacheConfig = None):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.config = config or CacheConfig()

        # Memory cache (LRU)
        self.memory_cache: OrderedDict = OrderedDict()
        self.memory_lock = threading.RLock()

        # Metrics
        self.metrics = defaultdict(CacheMetrics)
        self.global_metrics = CacheMetrics()

        # Cache warming registry
        self.warming_functions: Dict[str, Callable] = {}

        # Background tasks
        self._running = True
        self._maintenance_task = None

        if self.config.metrics_enabled:
            self._start_maintenance_task()

    def _start_maintenance_task(self):
        """Start background maintenance task"""
        def maintenance_loop():
            while self._running:
                try:
                    self._cleanup_expired_memory()
                    self._update_metrics()
                    time.sleep(60)  # Run every minute
                except Exception as e:
                    logger.error(f"Cache maintenance error: {e}")
                    time.sleep(60)

        self._maintenance_task = threading.Thread(target=maintenance_loop, daemon=True)
        self._maintenance_task.start()

    def _cleanup_expired_memory(self):
        """Clean up expired items from memory cache"""
        with self.memory_lock:
            current_time = time.time()
            expired_keys = []

            for key, (data, expiry, _) in self.memory_cache.items():
                if expiry and current_time > expiry:
                    expired_keys.append(key)

            for key in expired_keys:
                del self.memory_cache[key]
                self.global_metrics.evictions += 1

    def _update_metrics(self):
        """Update cache metrics"""
        with self.memory_lock:
            self.global_metrics.memory_usage = len(self.memory_cache)

    def _get_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate standardized cache key"""
        # Create a stable hash from args and kwargs
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            key_data += f":{hash(frozenset(sorted_kwargs))}"

        return f"betting_analytics:{key_data}"

    def _serialize_data(self, data: Any) -> str:
        """Serialize data for caching"""
        if self.config.compression:
            return json.dumps(data, default=str)
        else:
            return json.dumps(data, default=str)

    def _deserialize_data(self, data: str) -> Any:
        """Deserialize cached data"""
        return json.loads(data)

    def _get_ttl(self, volatility: DataVolatility) -> int:
        """Get TTL based on data volatility"""
        return self.config.volatility_ttls.get(volatility, self.config.default_ttl)

    async def get(self,
                  key: str,
                  category: str = "general",
                  level: CacheLevel = CacheLevel.BOTH) -> Optional[Any]:
        """
        Get data from cache

        Args:
            key: Cache key
            category: Category for metrics tracking
            level: Which cache level to check

        Returns:
            Cached data or None if not found
        """
        start_time = time.time()

        try:
            # Try memory cache first
            if level in [CacheLevel.MEMORY, CacheLevel.BOTH]:
                with self.memory_lock:
                    if key in self.memory_cache:
                        data, expiry, volatility = self.memory_cache[key]

                        # Check if expired
                        if expiry is None or time.time() < expiry:
                            # Move to end (LRU)
                            self.memory_cache.move_to_end(key)
                            self.metrics[category].hits += 1
                            self.global_metrics.hits += 1
                            return data
                        else:
                            # Expired, remove from memory
                            del self.memory_cache[key]

            # Try Redis cache
            if level in [CacheLevel.REDIS, CacheLevel.BOTH]:
                redis_data = self.redis_client.get(key)
                self.global_metrics.redis_calls += 1

                if redis_data:
                    try:
                        data = self._deserialize_data(redis_data)

                        # Store in memory cache if using both levels
                        if level == CacheLevel.BOTH:
                            self._store_in_memory(key, data, None, DataVolatility.DYNAMIC)

                        self.metrics[category].hits += 1
                        self.global_metrics.hits += 1
                        return data

                    except json.JSONDecodeError:
                        logger.error(f"Failed to deserialize cached data for key: {key}")
                        self.redis_client.delete(key)

            # Cache miss
            self.metrics[category].misses += 1
            self.global_metrics.misses += 1
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self.metrics[category].misses += 1
            self.global_metrics.misses += 1
            return None

        finally:
            # Track performance
            duration = time.time() - start_time
            logger.debug(f"Cache get for {key} took {duration:.3f}s")

    async def set(self,
                  key: str,
                  data: Any,
                  ttl: Optional[int] = None,
                  volatility: DataVolatility = DataVolatility.DYNAMIC,
                  category: str = "general",
                  level: CacheLevel = CacheLevel.BOTH) -> bool:
        """
        Store data in cache

        Args:
            key: Cache key
            data: Data to store
            ttl: Time to live in seconds
            volatility: Data volatility level
            category: Category for metrics
            level: Which cache level to use

        Returns:
            Success status
        """
        if ttl is None:
            ttl = self._get_ttl(volatility)

        try:
            # Store in memory cache
            if level in [CacheLevel.MEMORY, CacheLevel.BOTH]:
                self._store_in_memory(key, data, ttl, volatility)

            # Store in Redis cache
            if level in [CacheLevel.REDIS, CacheLevel.BOTH]:
                serialized_data = self._serialize_data(data)
                success = self.redis_client.setex(key, ttl, serialized_data)
                self.global_metrics.redis_calls += 1

                if not success:
                    logger.error(f"Failed to store data in Redis for key: {key}")
                    return False

            self.metrics[category].sets += 1
            self.global_metrics.sets += 1
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def _store_in_memory(self, key: str, data: Any, ttl: Optional[int], volatility: DataVolatility):
        """Store data in memory cache with LRU eviction"""
        with self.memory_lock:
            # Calculate expiry time
            expiry = time.time() + ttl if ttl else None

            # Add/update item
            self.memory_cache[key] = (data, expiry, volatility)
            self.memory_cache.move_to_end(key)  # Mark as recently used

            # Enforce memory limit
            while len(self.memory_cache) > self.config.memory_limit:
                oldest_key = next(iter(self.memory_cache))
                del self.memory_cache[oldest_key]
                self.global_metrics.evictions += 1

    async def delete(self,
                     key: str,
                     category: str = "general",
                     level: CacheLevel = CacheLevel.BOTH) -> bool:
        """
        Delete data from cache

        Args:
            key: Cache key to delete
            category: Category for metrics
            level: Which cache level to clear from

        Returns:
            Success status
        """
        try:
            deleted = False

            # Delete from memory cache
            if level in [CacheLevel.MEMORY, CacheLevel.BOTH]:
                with self.memory_lock:
                    if key in self.memory_cache:
                        del self.memory_cache[key]
                        deleted = True

            # Delete from Redis cache
            if level in [CacheLevel.REDIS, CacheLevel.BOTH]:
                redis_deleted = self.redis_client.delete(key)
                self.global_metrics.redis_calls += 1
                if redis_deleted:
                    deleted = True

            if deleted:
                self.metrics[category].deletes += 1
                self.global_metrics.deletes += 1

            return deleted

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def clear_category(self, category: str) -> int:
        """Clear all cache entries for a specific category"""
        pattern = f"betting_analytics:{category}:*"

        try:
            # Clear from Redis
            keys = self.redis_client.keys(pattern)
            deleted_count = 0

            if keys:
                deleted_count = self.redis_client.delete(*keys)

            # Clear from memory cache
            with self.memory_lock:
                memory_keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"betting_analytics:{category}:")]
                for key in memory_keys_to_delete:
                    del self.memory_cache[key]
                    deleted_count += 1

            logger.info(f"Cleared {deleted_count} cache entries for category: {category}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error clearing cache category {category}: {e}")
            return 0

    def cache_result(self,
                     category: str,
                     ttl: Optional[int] = None,
                     volatility: DataVolatility = DataVolatility.DYNAMIC,
                     level: CacheLevel = CacheLevel.BOTH):
        """
        Decorator for caching function results

        Args:
            category: Cache category
            ttl: Time to live
            volatility: Data volatility level
            level: Cache level to use
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                func_name = f"{func.__module__}.{func.__name__}"
                cache_key = self._get_cache_key(f"{category}:{func_name}", *args, **kwargs)

                # Try to get from cache
                result = await self.get(cache_key, category, level)
                if result is not None:
                    return result

                # Execute function
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)

                # Store result in cache
                if result is not None:
                    await self.set(cache_key, result, ttl, volatility, category, level)

                return result

            return wrapper
        return decorator

    def register_warming_function(self, category: str, func: Callable):
        """Register a function for cache warming"""
        self.warming_functions[category] = func

    async def warm_cache(self, categories: Optional[List[str]] = None):
        """Warm cache for specified categories"""
        if categories is None:
            categories = list(self.warming_functions.keys())

        for category in categories:
            if category in self.warming_functions:
                try:
                    logger.info(f"Warming cache for category: {category}")
                    func = self.warming_functions[category]

                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()

                    logger.info(f"Cache warming completed for category: {category}")

                except Exception as e:
                    logger.error(f"Cache warming failed for category {category}: {e}")

    async def get_metrics(self, category: Optional[str] = None) -> Dict:
        """Get cache performance metrics"""
        if category:
            category_metrics = self.metrics.get(category, CacheMetrics())
            return {
                "category": category,
                **asdict(category_metrics)
            }
        else:
            # Global metrics
            redis_info = {}
            try:
                redis_info = self.redis_client.info()
            except Exception as e:
                logger.error(f"Failed to get Redis info: {e}")

            return {
                "global_metrics": asdict(self.global_metrics),
                "category_metrics": {cat: asdict(metrics) for cat, metrics in self.metrics.items()},
                "memory_cache_size": len(self.memory_cache),
                "memory_limit": self.config.memory_limit,
                "redis_info": {
                    "used_memory": redis_info.get("used_memory_human", "unknown"),
                    "connected_clients": redis_info.get("connected_clients", 0),
                    "keyspace_hits": redis_info.get("keyspace_hits", 0),
                    "keyspace_misses": redis_info.get("keyspace_misses", 0)
                }
            }

    async def optimize_ttls(self):
        """Analyze access patterns and optimize TTL values"""
        # This would analyze cache hit/miss patterns and adjust TTL values
        # Implementation would track access patterns over time
        logger.info("TTL optimization not yet implemented")
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Perform cache health check"""
        try:
            # Test Redis connection
            redis_ping = self.redis_client.ping()

            # Test memory cache
            test_key = "health_check_test"
            await self.set(test_key, {"test": True}, ttl=10, level=CacheLevel.MEMORY)
            memory_test = await self.get(test_key, level=CacheLevel.MEMORY)
            await self.delete(test_key, level=CacheLevel.MEMORY)

            # Test Redis cache
            test_key_redis = "health_check_redis_test"
            await self.set(test_key_redis, {"test": True}, ttl=10, level=CacheLevel.REDIS)
            redis_test = await self.get(test_key_redis, level=CacheLevel.REDIS)
            await self.delete(test_key_redis, level=CacheLevel.REDIS)

            return {
                "status": "healthy",
                "redis_connected": redis_ping,
                "memory_cache_working": memory_test is not None,
                "redis_cache_working": redis_test is not None,
                "global_hit_rate": self.global_metrics.hit_rate,
                "total_operations": self.global_metrics.total_operations,
                "memory_usage": len(self.memory_cache),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def shutdown(self):
        """Shutdown cache manager and cleanup resources"""
        self._running = False

        if self._maintenance_task and self._maintenance_task.is_alive():
            self._maintenance_task.join(timeout=5)

        # Clear memory cache
        with self.memory_lock:
            self.memory_cache.clear()

        logger.info("Cache manager shut down successfully")