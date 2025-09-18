"""
Enhanced Caching Strategy for Real-time NFL Data Pipeline

Advanced caching implementation with Redis optimization, intelligent TTL management,
cache warming, and performance monitoring for real-time data scenarios.
"""

import asyncio
import logging
import json
import pickle
from typing import Dict, List, Optional, Any, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import weakref
from concurrent.futures import ThreadPoolExecutor

import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Cache strategy types"""
    WRITE_THROUGH = "write_through"      # Write to cache and storage simultaneously
    WRITE_BEHIND = "write_behind"        # Write to cache first, storage later
    WRITE_AROUND = "write_around"        # Write to storage, invalidate cache
    READ_THROUGH = "read_through"        # Read from cache, fallback to storage
    REFRESH_AHEAD = "refresh_ahead"      # Proactively refresh before expiration


class CacheEvent(Enum):
    """Cache event types for monitoring"""
    HIT = "hit"
    MISS = "miss"
    SET = "set"
    DELETE = "delete"
    EXPIRE = "expire"
    EVICT = "evict"


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    memory_usage: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0

    @property
    def miss_rate(self) -> float:
        """Calculate cache miss rate percentage"""
        return 100.0 - self.hit_rate


@dataclass
class CacheConfiguration:
    """Cache configuration settings"""
    # Redis connection
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    redis_max_connections: int = 20

    # TTL settings (minutes)
    default_ttl: int = 30
    live_data_ttl: int = 2
    game_state_ttl: int = 5
    odds_ttl: int = 3
    player_stats_ttl: int = 10
    historical_ttl: int = 1440  # 24 hours

    # Performance settings
    max_memory_cache_size: int = 1000
    compression_threshold: int = 1024  # bytes
    batch_size: int = 100

    # Refresh settings
    refresh_threshold: float = 0.8  # Refresh when 80% of TTL elapsed
    refresh_concurrency: int = 5

    # Monitoring
    enable_metrics: bool = True
    metrics_retention_hours: int = 24


class CacheKey:
    """Cache key generator with consistent formatting"""

    @staticmethod
    def game_state(game_id: str) -> str:
        """Generate cache key for game state"""
        return f"nfl:game:{game_id}:state"

    @staticmethod
    def live_scores(week: int, year: int = 2025) -> str:
        """Generate cache key for live scores"""
        return f"nfl:scores:{year}:week{week}"

    @staticmethod
    def odds(game_id: str) -> str:
        """Generate cache key for odds data"""
        return f"nfl:odds:{game_id}"

    @staticmethod
    def player_stats(player_id: str, game_id: str) -> str:
        """Generate cache key for player stats"""
        return f"nfl:player:{player_id}:game:{game_id}"

    @staticmethod
    def team_stats(team: str, game_id: str) -> str:
        """Generate cache key for team stats"""
        return f"nfl:team:{team}:game:{game_id}"

    @staticmethod
    def predictions(model_type: str, game_id: str) -> str:
        """Generate cache key for predictions"""
        return f"nfl:prediction:{model_type}:{game_id}"

    @staticmethod
    def api_response(source: str, endpoint: str, params_hash: str) -> str:
        """Generate cache key for API responses"""
        return f"nfl:api:{source}:{endpoint}:{params_hash}"

    @staticmethod
    def custom(namespace: str, identifier: str) -> str:
        """Generate custom cache key"""
        return f"nfl:{namespace}:{identifier}"


class EnhancedCacheManager:
    """
    Enhanced cache manager with Redis optimization and intelligent strategies

    Features:
    - Multiple cache strategies (write-through, read-through, etc.)
    - Intelligent TTL management based on data type
    - Cache warming and refresh-ahead
    - Compression for large objects
    - Performance monitoring and metrics
    - Fallback to in-memory cache
    - Batch operations for efficiency
    """

    def __init__(self, config: Optional[CacheConfiguration] = None):
        """
        Initialize enhanced cache manager

        Args:
            config: Cache configuration settings
        """
        self.config = config or CacheConfiguration()

        # Redis clients
        self._redis_client: Optional[redis.Redis] = None
        self._redis_healthy = False

        # In-memory fallback cache
        self._memory_cache: Dict[str, Any] = {}
        self._memory_timestamps: Dict[str, datetime] = {}

        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self._metric_history: List[Dict[str, Any]] = []

        # Background tasks
        self._refresh_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        self._metrics_task: Optional[asyncio.Task] = None

        # Refresh queue
        self._refresh_queue: asyncio.Queue = asyncio.Queue()
        self._refresh_in_progress: Set[str] = set()

        # Thread pool for CPU-intensive operations
        self._thread_pool = ThreadPoolExecutor(max_workers=4)

        # Event handlers
        self._event_handlers: Dict[CacheEvent, List[Callable]] = {
            event: [] for event in CacheEvent
        }

    async def initialize(self):
        """Initialize cache manager and start background tasks"""
        try:
            # Initialize Redis connection
            await self._initialize_redis()

            # Start background tasks
            self._refresh_task = asyncio.create_task(self._refresh_worker())
            self._cleanup_task = asyncio.create_task(self._cleanup_worker())

            if self.config.enable_metrics:
                self._metrics_task = asyncio.create_task(self._metrics_worker())

            logger.info("Enhanced cache manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize cache manager: {e}")
            raise

    async def shutdown(self):
        """Shutdown cache manager and cleanup resources"""
        try:
            # Cancel background tasks
            for task in [self._refresh_task, self._cleanup_task, self._metrics_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            # Close Redis connection
            if self._redis_client:
                await self._redis_client.close()

            # Shutdown thread pool
            self._thread_pool.shutdown(wait=True)

            logger.info("Enhanced cache manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during cache manager shutdown: {e}")

    async def _initialize_redis(self):
        """Initialize Redis connection with proper configuration"""
        try:
            self._redis_client = redis.from_url(
                self.config.redis_url,
                db=self.config.redis_db,
                max_connections=self.config.redis_max_connections,
                retry_on_timeout=True,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=False  # Handle binary data for compression
            )

            # Test connection
            await self._redis_client.ping()
            self._redis_healthy = True
            logger.info("Redis connection established")

        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self._redis_healthy = False

    async def get(
        self,
        key: str,
        strategy: CacheStrategy = CacheStrategy.READ_THROUGH,
        fallback_func: Optional[Callable] = None
    ) -> Optional[Any]:
        """
        Get value from cache with strategy support

        Args:
            key: Cache key
            strategy: Cache strategy to use
            fallback_func: Function to call on cache miss

        Returns:
            Cached value or None if not found
        """
        start_time = datetime.utcnow()

        try:
            # Try Redis first
            if self._redis_healthy and self._redis_client:
                value = await self._redis_get(key)
                if value is not None:
                    self._record_event(CacheEvent.HIT, key)
                    return value

            # Try memory cache
            value = self._memory_get(key)
            if value is not None:
                self._record_event(CacheEvent.HIT, key)
                return value

            # Cache miss
            self._record_event(CacheEvent.MISS, key)

            # Handle read-through strategy
            if strategy == CacheStrategy.READ_THROUGH and fallback_func:
                value = await self._execute_fallback(fallback_func, key)
                if value is not None:
                    await self.set(key, value)
                return value

            return None

        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            self.metrics.errors += 1
            return None

        finally:
            self._update_response_time(start_time)

    async def set(
        self,
        key: str,
        value: Any,
        ttl_minutes: Optional[int] = None,
        strategy: CacheStrategy = CacheStrategy.WRITE_THROUGH
    ) -> bool:
        """
        Set value in cache with strategy support

        Args:
            key: Cache key
            value: Value to cache
            ttl_minutes: TTL in minutes (uses default if None)
            strategy: Cache strategy to use

        Returns:
            True if successfully cached
        """
        try:
            ttl = ttl_minutes or self._get_default_ttl(key)
            success = False

            # Serialize and compress if needed
            serialized_value = await self._serialize_value(value)

            # Write to Redis
            if self._redis_healthy and self._redis_client:
                redis_success = await self._redis_set(key, serialized_value, ttl)
                if redis_success:
                    success = True

            # Write to memory cache as backup
            self._memory_set(key, value, ttl)
            success = True

            if success:
                self._record_event(CacheEvent.SET, key)

                # Schedule refresh if refresh-ahead strategy
                if strategy == CacheStrategy.REFRESH_AHEAD:
                    await self._schedule_refresh(key, ttl)

            return success

        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            self.metrics.errors += 1
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache

        Args:
            key: Cache key to delete

        Returns:
            True if key was deleted
        """
        try:
            deleted = False

            # Delete from Redis
            if self._redis_healthy and self._redis_client:
                redis_deleted = await self._redis_client.delete(key)
                if redis_deleted:
                    deleted = True

            # Delete from memory cache
            if key in self._memory_cache:
                del self._memory_cache[key]
                del self._memory_timestamps[key]
                deleted = True

            if deleted:
                self._record_event(CacheEvent.DELETE, key)

            return deleted

        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            self.metrics.errors += 1
            return False

    async def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from cache efficiently

        Args:
            keys: List of cache keys

        Returns:
            Dictionary of key-value pairs found in cache
        """
        results = {}

        try:
            # Try Redis pipeline for efficiency
            if self._redis_healthy and self._redis_client:
                redis_results = await self._redis_get_multi(keys)
                results.update(redis_results)

            # Fill gaps from memory cache
            missing_keys = set(keys) - set(results.keys())
            for key in missing_keys:
                value = self._memory_get(key)
                if value is not None:
                    results[key] = value

            # Record metrics
            for key in keys:
                if key in results:
                    self._record_event(CacheEvent.HIT, key)
                else:
                    self._record_event(CacheEvent.MISS, key)

            return results

        except Exception as e:
            logger.error(f"Error getting multiple cache keys: {e}")
            self.metrics.errors += 1
            return {}

    async def set_multi(self, data: Dict[str, Any], ttl_minutes: Optional[int] = None) -> bool:
        """
        Set multiple values in cache efficiently

        Args:
            data: Dictionary of key-value pairs to cache
            ttl_minutes: TTL in minutes for all keys

        Returns:
            True if all keys were successfully cached
        """
        try:
            success = True

            # Serialize all values
            serialized_data = {}
            for key, value in data.items():
                serialized_data[key] = await self._serialize_value(value)

            # Set in Redis using pipeline
            if self._redis_healthy and self._redis_client:
                redis_success = await self._redis_set_multi(serialized_data, ttl_minutes)
                if not redis_success:
                    success = False

            # Set in memory cache
            for key, value in data.items():
                ttl = ttl_minutes or self._get_default_ttl(key)
                self._memory_set(key, value, ttl)

            # Record metrics
            for key in data.keys():
                self._record_event(CacheEvent.SET, key)

            return success

        except Exception as e:
            logger.error(f"Error setting multiple cache keys: {e}")
            self.metrics.errors += 1
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern

        Args:
            pattern: Pattern to match (supports wildcards)

        Returns:
            Number of keys invalidated
        """
        try:
            count = 0

            # Invalidate in Redis
            if self._redis_healthy and self._redis_client:
                redis_keys = await self._redis_client.keys(pattern)
                if redis_keys:
                    count += await self._redis_client.delete(*redis_keys)

            # Invalidate in memory cache
            import fnmatch
            memory_keys = [
                key for key in self._memory_cache.keys()
                if fnmatch.fnmatch(key, pattern)
            ]

            for key in memory_keys:
                del self._memory_cache[key]
                del self._memory_timestamps[key]
                count += 1

            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count

        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            self.metrics.errors += 1
            return 0

    async def warm_cache(self, warm_functions: Dict[str, Callable]) -> Dict[str, bool]:
        """
        Warm cache with popular data

        Args:
            warm_functions: Dictionary of cache_key -> function_to_get_data

        Returns:
            Dictionary of cache_key -> success_status
        """
        results = {}

        try:
            # Execute warming functions concurrently
            tasks = []
            for cache_key, func in warm_functions.items():
                task = asyncio.create_task(self._warm_single_key(cache_key, func))
                tasks.append((cache_key, task))

            # Wait for all warming tasks to complete
            for cache_key, task in tasks:
                try:
                    results[cache_key] = await task
                except Exception as e:
                    logger.error(f"Error warming cache key {cache_key}: {e}")
                    results[cache_key] = False

            logger.info(f"Cache warming completed: {sum(results.values())}/{len(results)} successful")
            return results

        except Exception as e:
            logger.error(f"Error during cache warming: {e}")
            return {key: False for key in warm_functions.keys()}

    async def _warm_single_key(self, cache_key: str, func: Callable) -> bool:
        """Warm a single cache key"""
        try:
            # Check if already cached and fresh
            existing = await self.get(cache_key)
            if existing is not None:
                return True

            # Execute function to get fresh data
            if asyncio.iscoroutinefunction(func):
                data = await func()
            else:
                data = await asyncio.get_event_loop().run_in_executor(
                    self._thread_pool, func
                )

            if data is not None:
                return await self.set(cache_key, data)

            return False

        except Exception as e:
            logger.error(f"Error warming cache key {cache_key}: {e}")
            return False

    async def _redis_get(self, key: str) -> Optional[Any]:
        """Get value from Redis with deserialization"""
        try:
            serialized_value = await self._redis_client.get(key)
            if serialized_value is None:
                return None

            return await self._deserialize_value(serialized_value)

        except Exception as e:
            logger.warning(f"Redis get error for key {key}: {e}")
            self._redis_healthy = False
            return None

    async def _redis_set(self, key: str, serialized_value: bytes, ttl_minutes: int) -> bool:
        """Set value in Redis with TTL"""
        try:
            ttl_seconds = ttl_minutes * 60
            await self._redis_client.setex(key, ttl_seconds, serialized_value)
            return True

        except Exception as e:
            logger.warning(f"Redis set error for key {key}: {e}")
            self._redis_healthy = False
            return False

    async def _redis_get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from Redis using pipeline"""
        try:
            if not keys:
                return {}

            # Use pipeline for efficiency
            pipeline = self._redis_client.pipeline()
            for key in keys:
                pipeline.get(key)

            raw_results = await pipeline.execute()
            results = {}

            for key, raw_value in zip(keys, raw_results):
                if raw_value is not None:
                    try:
                        results[key] = await self._deserialize_value(raw_value)
                    except Exception as e:
                        logger.warning(f"Error deserializing key {key}: {e}")

            return results

        except Exception as e:
            logger.warning(f"Redis multi-get error: {e}")
            self._redis_healthy = False
            return {}

    async def _redis_set_multi(self, serialized_data: Dict[str, bytes], ttl_minutes: Optional[int]) -> bool:
        """Set multiple values in Redis using pipeline"""
        try:
            if not serialized_data:
                return True

            pipeline = self._redis_client.pipeline()
            ttl_seconds = (ttl_minutes or self.config.default_ttl) * 60

            for key, value in serialized_data.items():
                pipeline.setex(key, ttl_seconds, value)

            await pipeline.execute()
            return True

        except Exception as e:
            logger.warning(f"Redis multi-set error: {e}")
            self._redis_healthy = False
            return False

    def _memory_get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key not in self._memory_cache:
            return None

        # Check expiration
        timestamp = self._memory_timestamps.get(key)
        if timestamp and datetime.utcnow() > timestamp:
            # Expired
            del self._memory_cache[key]
            del self._memory_timestamps[key]
            return None

        return self._memory_cache[key]

    def _memory_set(self, key: str, value: Any, ttl_minutes: int):
        """Set value in memory cache"""
        expiry_time = datetime.utcnow() + timedelta(minutes=ttl_minutes)

        self._memory_cache[key] = value
        self._memory_timestamps[key] = expiry_time

        # Enforce size limit
        if len(self._memory_cache) > self.config.max_memory_cache_size:
            self._cleanup_memory_cache()

    def _cleanup_memory_cache(self):
        """Clean up expired entries and enforce size limits"""
        now = datetime.utcnow()

        # Remove expired entries
        expired_keys = [
            key for key, expiry in self._memory_timestamps.items()
            if expiry <= now
        ]

        for key in expired_keys:
            del self._memory_cache[key]
            del self._memory_timestamps[key]

        # If still over limit, remove oldest entries
        if len(self._memory_cache) > self.config.max_memory_cache_size:
            sorted_items = sorted(
                self._memory_timestamps.items(),
                key=lambda x: x[1]
            )

            excess_count = len(self._memory_cache) - self.config.max_memory_cache_size
            for key, _ in sorted_items[:excess_count]:
                del self._memory_cache[key]
                del self._memory_timestamps[key]

    async def _serialize_value(self, value: Any) -> bytes:
        """Serialize value with optional compression"""
        try:
            # Use pickle for Python objects
            serialized = pickle.dumps(value)

            # Compress if above threshold
            if len(serialized) > self.config.compression_threshold:
                import gzip
                serialized = gzip.compress(serialized)

            return serialized

        except Exception as e:
            logger.error(f"Serialization error: {e}")
            raise

    async def _deserialize_value(self, serialized_value: bytes) -> Any:
        """Deserialize value with decompression"""
        try:
            # Try decompression first
            try:
                import gzip
                decompressed = gzip.decompress(serialized_value)
                return pickle.loads(decompressed)
            except:
                # Not compressed, try direct pickle
                return pickle.loads(serialized_value)

        except Exception as e:
            logger.error(f"Deserialization error: {e}")
            raise

    def _get_default_ttl(self, key: str) -> int:
        """Get default TTL based on key pattern"""
        if ":game:" in key and ":state" in key:
            return self.config.game_state_ttl
        elif ":scores:" in key:
            return self.config.live_data_ttl
        elif ":odds:" in key:
            return self.config.odds_ttl
        elif ":player:" in key:
            return self.config.player_stats_ttl
        elif ":api:" in key:
            return self.config.live_data_ttl
        else:
            return self.config.default_ttl

    async def _schedule_refresh(self, key: str, ttl_minutes: int):
        """Schedule refresh for refresh-ahead strategy"""
        refresh_time = datetime.utcnow() + timedelta(
            minutes=ttl_minutes * self.config.refresh_threshold
        )

        await self._refresh_queue.put((refresh_time, key))

    async def _refresh_worker(self):
        """Background worker for refresh-ahead strategy"""
        while True:
            try:
                refresh_time, key = await self._refresh_queue.get()

                # Wait until refresh time
                now = datetime.utcnow()
                if refresh_time > now:
                    await asyncio.sleep((refresh_time - now).total_seconds())

                # Skip if already being refreshed
                if key in self._refresh_in_progress:
                    continue

                self._refresh_in_progress.add(key)

                # Trigger refresh by emitting event
                await self._emit_event(CacheEvent.EXPIRE, key)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in refresh worker: {e}")
            finally:
                self._refresh_in_progress.discard(key)

    async def _cleanup_worker(self):
        """Background worker for cache cleanup"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Cleanup memory cache
                self._cleanup_memory_cache()

                # Check Redis health
                if self._redis_client and not self._redis_healthy:
                    try:
                        await self._redis_client.ping()
                        self._redis_healthy = True
                        logger.info("Redis connection restored")
                    except:
                        pass

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")

    async def _metrics_worker(self):
        """Background worker for metrics collection"""
        while True:
            try:
                await asyncio.sleep(60)  # Collect metrics every minute

                # Snapshot current metrics
                snapshot = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'metrics': {
                        'hits': self.metrics.hits,
                        'misses': self.metrics.misses,
                        'hit_rate': self.metrics.hit_rate,
                        'total_requests': self.metrics.total_requests,
                        'avg_response_time': self.metrics.avg_response_time,
                        'errors': self.metrics.errors
                    },
                    'redis_healthy': self._redis_healthy,
                    'memory_cache_size': len(self._memory_cache)
                }

                self._metric_history.append(snapshot)

                # Keep only recent history
                cutoff_time = datetime.utcnow() - timedelta(hours=self.config.metrics_retention_hours)
                self._metric_history = [
                    m for m in self._metric_history
                    if datetime.fromisoformat(m['timestamp']) > cutoff_time
                ]

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics worker: {e}")

    def _record_event(self, event: CacheEvent, key: str):
        """Record cache event for metrics"""
        self.metrics.total_requests += 1

        if event == CacheEvent.HIT:
            self.metrics.hits += 1
        elif event == CacheEvent.MISS:
            self.metrics.misses += 1
        elif event == CacheEvent.SET:
            self.metrics.sets += 1
        elif event == CacheEvent.DELETE:
            self.metrics.deletes += 1

    def _update_response_time(self, start_time: datetime):
        """Update average response time metric"""
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000  # ms

        if self.metrics.total_requests == 1:
            self.metrics.avg_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.avg_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.avg_response_time
            )

    async def _emit_event(self, event: CacheEvent, key: str):
        """Emit cache event to registered handlers"""
        for handler in self._event_handlers.get(event, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event, key)
                else:
                    handler(event, key)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")

    async def _execute_fallback(self, fallback_func: Callable, key: str) -> Any:
        """Execute fallback function for cache miss"""
        try:
            if asyncio.iscoroutinefunction(fallback_func):
                return await fallback_func(key)
            else:
                return await asyncio.get_event_loop().run_in_executor(
                    self._thread_pool, fallback_func, key
                )
        except Exception as e:
            logger.error(f"Error executing fallback for key {key}: {e}")
            return None

    def add_event_handler(self, event: CacheEvent, handler: Callable):
        """Add event handler for cache events"""
        self._event_handlers[event].append(handler)

    def get_metrics(self) -> Dict[str, Any]:
        """Get current cache metrics"""
        return {
            'current': {
                'hit_rate': self.metrics.hit_rate,
                'miss_rate': self.metrics.miss_rate,
                'total_requests': self.metrics.total_requests,
                'avg_response_time_ms': self.metrics.avg_response_time,
                'errors': self.metrics.errors,
                'memory_cache_size': len(self._memory_cache),
                'redis_healthy': self._redis_healthy
            },
            'history': self._metric_history[-60:] if self._metric_history else []  # Last hour
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Get cache health status"""
        status = "healthy"

        if not self._redis_healthy:
            status = "degraded" if len(self._memory_cache) > 0 else "unhealthy"
        elif self.metrics.hit_rate < 50 and self.metrics.total_requests > 100:
            status = "degraded"

        return {
            'status': status,
            'redis_healthy': self._redis_healthy,
            'memory_cache_size': len(self._memory_cache),
            'hit_rate': self.metrics.hit_rate,
            'error_rate': (self.metrics.errors / max(self.metrics.total_requests, 1)) * 100,
            'avg_response_time_ms': self.metrics.avg_response_time
        }