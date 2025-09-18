"""
Cache Strategy Service
Intelligent caching for premium data sources with TTL, invalidation, and performance optimization
"""

import os
import json
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import hashlib
import pickle
import gzip
from dotenv import load_dotenv
import threading
import time

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CacheStrategyService:
    """Intelligent caching service for premium NFL data"""

    def __init__(self):
        # Cache configuration
        self.cache_config = {
            'live_odds': {'ttl': 60, 'priority': 'high'},           # 1 minute
            'player_props': {'ttl': 3600, 'priority': 'medium'},   # 1 hour
            'analytics': {'ttl': 1800, 'priority': 'medium'},      # 30 minutes
            'game_feed': {'ttl': 30, 'priority': 'high'},          # 30 seconds
            'team_stats': {'ttl': 7200, 'priority': 'low'},        # 2 hours
            'injury_reports': {'ttl': 1800, 'priority': 'medium'}, # 30 minutes
            'weather': {'ttl': 900, 'priority': 'low'},            # 15 minutes
            'betting_trends': {'ttl': 300, 'priority': 'high'},    # 5 minutes
            'historical_data': {'ttl': 86400, 'priority': 'low'}   # 24 hours
        }

        # Multi-layer cache setup
        self.memory_cache = {}  # L1 Cache - In-memory
        self.redis_cache = None  # L2 Cache - Redis
        self.file_cache = {}     # L3 Cache - File system

        # Cache statistics
        self.cache_stats = {
            'hits': {'l1': 0, 'l2': 0, 'l3': 0},
            'misses': 0,
            'writes': 0,
            'evictions': 0,
            'errors': 0
        }

        # Cache monitoring
        self.performance_metrics = {
            'avg_get_time': 0.0,
            'avg_set_time': 0.0,
            'cache_hit_ratio': 0.0,
            'memory_usage': 0,
            'total_operations': 0
        }

        # Initialize Redis if available
        self._initialize_redis()

        # Start cache maintenance thread
        self._start_cache_maintenance()

        logger.info("🗄️ Cache Strategy Service initialized")

    def _initialize_redis(self):
        """Initialize Redis connection if available"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_cache = redis.from_url(redis_url, decode_responses=False)
            self.redis_cache.ping()
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache only: {e}")
            self.redis_cache = None

    def get(self, key: str, data_type: str = 'default') -> Optional[Any]:
        """Get data from cache with intelligent fallback"""
        start_time = time.time()

        try:
            # Generate cache key with data type
            cache_key = self._generate_cache_key(key, data_type)

            # L1 Cache - Memory (fastest)
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_entry, data_type):
                    self.cache_stats['hits']['l1'] += 1
                    self._update_performance_metrics('get', start_time)
                    return cache_entry['data']
                else:
                    # Remove expired entry
                    del self.memory_cache[cache_key]

            # L2 Cache - Redis (medium speed)
            if self.redis_cache:
                try:
                    cached_data = self.redis_cache.get(cache_key)
                    if cached_data:
                        cache_entry = pickle.loads(gzip.decompress(cached_data))
                        if self._is_cache_valid(cache_entry, data_type):
                            # Promote to L1 cache
                            self.memory_cache[cache_key] = cache_entry
                            self.cache_stats['hits']['l2'] += 1
                            self._update_performance_metrics('get', start_time)
                            return cache_entry['data']
                        else:
                            # Remove expired entry
                            self.redis_cache.delete(cache_key)
                except Exception as e:
                    logger.error(f"Redis get error: {e}")

            # L3 Cache - File system (slowest)
            file_data = self._get_from_file_cache(cache_key, data_type)
            if file_data:
                # Promote to higher cache levels
                self.set(key, file_data, data_type)
                self.cache_stats['hits']['l3'] += 1
                self._update_performance_metrics('get', start_time)
                return file_data

            # Cache miss
            self.cache_stats['misses'] += 1
            self._update_performance_metrics('get', start_time)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats['errors'] += 1
            return None

    def set(self, key: str, data: Any, data_type: str = 'default', ttl_override: int = None) -> bool:
        """Set data in cache with intelligent distribution"""
        start_time = time.time()

        try:
            cache_key = self._generate_cache_key(key, data_type)
            ttl = ttl_override or self.cache_config.get(data_type, {}).get('ttl', 3600)
            priority = self.cache_config.get(data_type, {}).get('priority', 'medium')

            cache_entry = {
                'data': data,
                'timestamp': datetime.now().timestamp(),
                'ttl': ttl,
                'priority': priority,
                'access_count': 0,
                'data_type': data_type
            }

            # Always store in L1 (memory) cache
            self.memory_cache[cache_key] = cache_entry

            # Store in L2 (Redis) cache for medium/high priority
            if self.redis_cache and priority in ['medium', 'high']:
                try:
                    compressed_data = gzip.compress(pickle.dumps(cache_entry))
                    self.redis_cache.setex(cache_key, ttl, compressed_data)
                except Exception as e:
                    logger.error(f"Redis set error: {e}")

            # Store in L3 (file) cache for low priority or large data
            if priority == 'low' or self._is_large_data(data):
                self._set_file_cache(cache_key, cache_entry)

            # Manage cache size
            self._manage_cache_size()

            self.cache_stats['writes'] += 1
            self._update_performance_metrics('set', start_time)
            return True

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            self.cache_stats['errors'] += 1
            return False

    def invalidate(self, pattern: str = None, data_type: str = None) -> int:
        """Invalidate cache entries by pattern or data type"""
        invalidated_count = 0

        try:
            # Invalidate from memory cache
            keys_to_remove = []
            for cache_key, cache_entry in self.memory_cache.items():
                if self._should_invalidate(cache_key, cache_entry, pattern, data_type):
                    keys_to_remove.append(cache_key)

            for key in keys_to_remove:
                del self.memory_cache[key]
                invalidated_count += 1

            # Invalidate from Redis cache
            if self.redis_cache:
                try:
                    if pattern:
                        redis_keys = self.redis_cache.keys(f"*{pattern}*")
                        if redis_keys:
                            self.redis_cache.delete(*redis_keys)
                            invalidated_count += len(redis_keys)
                except Exception as e:
                    logger.error(f"Redis invalidation error: {e}")

            logger.info(f"Invalidated {invalidated_count} cache entries")
            return invalidated_count

        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0

    def get_multiple(self, keys: List[str], data_type: str = 'default') -> Dict[str, Any]:
        """Get multiple cache entries efficiently"""
        results = {}

        # Batch get from memory cache
        memory_hits = {}
        remaining_keys = []

        for key in keys:
            cache_key = self._generate_cache_key(key, data_type)
            if cache_key in self.memory_cache:
                cache_entry = self.memory_cache[cache_key]
                if self._is_cache_valid(cache_entry, data_type):
                    memory_hits[key] = cache_entry['data']
                    self.cache_stats['hits']['l1'] += 1
                else:
                    remaining_keys.append(key)
            else:
                remaining_keys.append(key)

        results.update(memory_hits)

        # Batch get from Redis cache
        if self.redis_cache and remaining_keys:
            try:
                redis_keys = [self._generate_cache_key(key, data_type) for key in remaining_keys]
                redis_results = self.redis_cache.mget(redis_keys)

                redis_hits = {}
                still_remaining = []

                for i, (key, cached_data) in enumerate(zip(remaining_keys, redis_results)):
                    if cached_data:
                        try:
                            cache_entry = pickle.loads(gzip.decompress(cached_data))
                            if self._is_cache_valid(cache_entry, data_type):
                                redis_hits[key] = cache_entry['data']
                                # Promote to L1
                                cache_key = self._generate_cache_key(key, data_type)
                                self.memory_cache[cache_key] = cache_entry
                                self.cache_stats['hits']['l2'] += 1
                            else:
                                still_remaining.append(key)
                        except:
                            still_remaining.append(key)
                    else:
                        still_remaining.append(key)

                results.update(redis_hits)
                remaining_keys = still_remaining

            except Exception as e:
                logger.error(f"Redis batch get error: {e}")

        # Update miss count
        self.cache_stats['misses'] += len(remaining_keys)

        return results

    def set_multiple(self, data_dict: Dict[str, Any], data_type: str = 'default') -> int:
        """Set multiple cache entries efficiently"""
        success_count = 0

        # Batch set to memory cache
        cache_entries = {}
        ttl = self.cache_config.get(data_type, {}).get('ttl', 3600)
        priority = self.cache_config.get(data_type, {}).get('priority', 'medium')

        for key, data in data_dict.items():
            cache_key = self._generate_cache_key(key, data_type)
            cache_entry = {
                'data': data,
                'timestamp': datetime.now().timestamp(),
                'ttl': ttl,
                'priority': priority,
                'access_count': 0,
                'data_type': data_type
            }
            cache_entries[cache_key] = cache_entry
            self.memory_cache[cache_key] = cache_entry
            success_count += 1

        # Batch set to Redis cache
        if self.redis_cache and priority in ['medium', 'high']:
            try:
                redis_data = {}
                for cache_key, cache_entry in cache_entries.items():
                    compressed_data = gzip.compress(pickle.dumps(cache_entry))
                    redis_data[cache_key] = compressed_data

                # Use pipeline for efficiency
                pipe = self.redis_cache.pipeline()
                for cache_key, compressed_data in redis_data.items():
                    pipe.setex(cache_key, ttl, compressed_data)
                pipe.execute()

            except Exception as e:
                logger.error(f"Redis batch set error: {e}")

        self.cache_stats['writes'] += success_count
        return success_count

    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache statistics"""
        total_hits = sum(self.cache_stats['hits'].values())
        total_operations = total_hits + self.cache_stats['misses']

        hit_ratio = (total_hits / total_operations * 100) if total_operations > 0 else 0

        return {
            'hit_ratio': round(hit_ratio, 2),
            'total_hits': total_hits,
            'l1_hits': self.cache_stats['hits']['l1'],
            'l2_hits': self.cache_stats['hits']['l2'],
            'l3_hits': self.cache_stats['hits']['l3'],
            'misses': self.cache_stats['misses'],
            'writes': self.cache_stats['writes'],
            'evictions': self.cache_stats['evictions'],
            'errors': self.cache_stats['errors'],
            'memory_entries': len(self.memory_cache),
            'performance_metrics': self.performance_metrics,
            'cache_efficiency': self._calculate_cache_efficiency()
        }

    def optimize_cache(self) -> Dict:
        """Optimize cache performance and size"""
        optimization_result = {
            'optimizations_applied': [],
            'memory_freed': 0,
            'performance_improvement': 0
        }

        # Remove expired entries
        expired_count = self._cleanup_expired_entries()
        if expired_count > 0:
            optimization_result['optimizations_applied'].append(f"Removed {expired_count} expired entries")

        # Optimize memory usage
        memory_optimized = self._optimize_memory_usage()
        optimization_result['memory_freed'] = memory_optimized

        # Defragment Redis cache
        if self.redis_cache:
            try:
                self.redis_cache.execute_command('MEMORY', 'PURGE')
                optimization_result['optimizations_applied'].append("Redis memory defragmented")
            except Exception as e:
                logger.warning(f"Redis defragmentation failed: {e}")

        # Update performance metrics
        self._update_cache_efficiency()

        return optimization_result

    def warm_cache(self, data_sources: Dict[str, callable]) -> Dict:
        """Warm cache with frequently accessed data"""
        warming_result = {
            'warmed_entries': 0,
            'failed_entries': 0,
            'data_types_warmed': []
        }

        for data_type, fetch_function in data_sources.items():
            try:
                # Get commonly accessed keys for this data type
                common_keys = self._get_common_cache_keys(data_type)

                for key in common_keys:
                    try:
                        data = fetch_function(key)
                        if data:
                            self.set(key, data, data_type)
                            warming_result['warmed_entries'] += 1
                    except Exception as e:
                        logger.error(f"Cache warming failed for {key}: {e}")
                        warming_result['failed_entries'] += 1

                warming_result['data_types_warmed'].append(data_type)

            except Exception as e:
                logger.error(f"Cache warming failed for {data_type}: {e}")

        return warming_result

    def clear_cache(self, data_type: str = None) -> int:
        """Clear cache completely or by data type"""
        cleared_count = 0

        if data_type:
            # Clear specific data type
            keys_to_remove = [
                key for key, entry in self.memory_cache.items()
                if entry.get('data_type') == data_type
            ]
            for key in keys_to_remove:
                del self.memory_cache[key]
                cleared_count += 1

            # Clear from Redis
            if self.redis_cache:
                try:
                    pattern_keys = self.redis_cache.keys(f"*{data_type}*")
                    if pattern_keys:
                        self.redis_cache.delete(*pattern_keys)
                        cleared_count += len(pattern_keys)
                except Exception as e:
                    logger.error(f"Redis clear error: {e}")
        else:
            # Clear all caches
            cleared_count = len(self.memory_cache)
            self.memory_cache.clear()

            if self.redis_cache:
                try:
                    self.redis_cache.flushdb()
                except Exception as e:
                    logger.error(f"Redis flush error: {e}")

        # Reset statistics
        if not data_type:
            self.cache_stats = {
                'hits': {'l1': 0, 'l2': 0, 'l3': 0},
                'misses': 0,
                'writes': 0,
                'evictions': 0,
                'errors': 0
            }

        logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count

    # Private helper methods
    def _generate_cache_key(self, key: str, data_type: str) -> str:
        """Generate a standardized cache key"""
        return f"nfl_predictor:{data_type}:{hashlib.md5(key.encode()).hexdigest()}"

    def _is_cache_valid(self, cache_entry: Dict, data_type: str) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False

        age = datetime.now().timestamp() - cache_entry.get('timestamp', 0)
        ttl = cache_entry.get('ttl', self.cache_config.get(data_type, {}).get('ttl', 3600))

        # Update access count
        cache_entry['access_count'] = cache_entry.get('access_count', 0) + 1

        return age < ttl

    def _should_invalidate(self, cache_key: str, cache_entry: Dict, pattern: str, data_type: str) -> bool:
        """Check if cache entry should be invalidated"""
        if pattern and pattern in cache_key:
            return True
        if data_type and cache_entry.get('data_type') == data_type:
            return True
        return False

    def _is_large_data(self, data: Any) -> bool:
        """Check if data is considered large (> 1MB)"""
        try:
            return len(pickle.dumps(data)) > 1024 * 1024  # 1MB
        except:
            return False

    def _manage_cache_size(self):
        """Manage memory cache size using LRU eviction"""
        max_entries = 10000  # Maximum entries in memory cache

        if len(self.memory_cache) > max_entries:
            # Sort by access count and age
            sorted_entries = sorted(
                self.memory_cache.items(),
                key=lambda x: (x[1].get('access_count', 0), x[1].get('timestamp', 0))
            )

            # Remove least accessed/oldest entries
            entries_to_remove = len(self.memory_cache) - max_entries
            for i in range(entries_to_remove):
                key, _ = sorted_entries[i]
                del self.memory_cache[key]
                self.cache_stats['evictions'] += 1

    def _cleanup_expired_entries(self) -> int:
        """Clean up expired cache entries"""
        expired_count = 0
        current_time = datetime.now().timestamp()

        expired_keys = []
        for key, entry in self.memory_cache.items():
            age = current_time - entry.get('timestamp', 0)
            ttl = entry.get('ttl', 3600)
            if age > ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self.memory_cache[key]
            expired_count += 1

        return expired_count

    def _optimize_memory_usage(self) -> int:
        """Optimize memory usage by compressing large objects"""
        memory_freed = 0

        for key, entry in self.memory_cache.items():
            data = entry['data']
            if self._is_large_data(data):
                try:
                    # Compress large data objects
                    compressed_data = gzip.compress(pickle.dumps(data))
                    original_size = len(pickle.dumps(data))
                    compressed_size = len(compressed_data)

                    if compressed_size < original_size * 0.7:  # >30% compression
                        entry['data'] = compressed_data
                        entry['compressed'] = True
                        memory_freed += original_size - compressed_size
                except Exception as e:
                    logger.error(f"Compression failed for {key}: {e}")

        return memory_freed

    def _update_performance_metrics(self, operation: str, start_time: float):
        """Update performance metrics"""
        operation_time = time.time() - start_time
        self.performance_metrics['total_operations'] += 1

        if operation == 'get':
            current_avg = self.performance_metrics['avg_get_time']
            total_ops = self.performance_metrics['total_operations']
            self.performance_metrics['avg_get_time'] = (
                (current_avg * (total_ops - 1) + operation_time) / total_ops
            )
        elif operation == 'set':
            current_avg = self.performance_metrics['avg_set_time']
            total_ops = self.performance_metrics['total_operations']
            self.performance_metrics['avg_set_time'] = (
                (current_avg * (total_ops - 1) + operation_time) / total_ops
            )

    def _calculate_cache_efficiency(self) -> Dict:
        """Calculate cache efficiency metrics"""
        total_hits = sum(self.cache_stats['hits'].values())
        total_operations = total_hits + self.cache_stats['misses']

        if total_operations == 0:
            return {'overall': 0, 'l1_efficiency': 0, 'l2_efficiency': 0}

        return {
            'overall': round(total_hits / total_operations * 100, 2),
            'l1_efficiency': round(self.cache_stats['hits']['l1'] / total_operations * 100, 2),
            'l2_efficiency': round(self.cache_stats['hits']['l2'] / total_operations * 100, 2),
            'l3_efficiency': round(self.cache_stats['hits']['l3'] / total_operations * 100, 2)
        }

    def _update_cache_efficiency(self):
        """Update cache efficiency in performance metrics"""
        efficiency = self._calculate_cache_efficiency()
        self.performance_metrics['cache_hit_ratio'] = efficiency['overall']

    def _get_common_cache_keys(self, data_type: str) -> List[str]:
        """Get commonly accessed cache keys for warming"""
        # This would be based on actual usage patterns
        common_keys = {
            'live_odds': ['week_1_games', 'week_2_games'],
            'player_props': ['week_1_qb_props', 'week_1_rb_props', 'week_1_wr_props'],
            'analytics': ['team_epa_week_1', 'team_dvoa_week_1'],
            'game_feed': ['live_games']
        }
        return common_keys.get(data_type, [])

    def _get_from_file_cache(self, cache_key: str, data_type: str) -> Optional[Any]:
        """Get data from file cache"""
        try:
            file_path = f"/tmp/nfl_cache/{cache_key}.pkl"
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    cache_entry = pickle.load(f)
                    if self._is_cache_valid(cache_entry, data_type):
                        return cache_entry['data']
        except Exception as e:
            logger.error(f"File cache read error: {e}")
        return None

    def _set_file_cache(self, cache_key: str, cache_entry: Dict):
        """Set data in file cache"""
        try:
            os.makedirs("/tmp/nfl_cache", exist_ok=True)
            file_path = f"/tmp/nfl_cache/{cache_key}.pkl"
            with open(file_path, 'wb') as f:
                pickle.dump(cache_entry, f)
        except Exception as e:
            logger.error(f"File cache write error: {e}")

    def _start_cache_maintenance(self):
        """Start background cache maintenance thread"""
        def maintenance_loop():
            while True:
                try:
                    # Clean expired entries every 5 minutes
                    self._cleanup_expired_entries()

                    # Optimize cache every 15 minutes
                    if int(time.time()) % 900 == 0:  # Every 15 minutes
                        self.optimize_cache()

                    time.sleep(60)  # Check every minute

                except Exception as e:
                    logger.error(f"Cache maintenance error: {e}")
                    time.sleep(60)

        maintenance_thread = threading.Thread(target=maintenance_loop, daemon=True)
        maintenance_thread.start()

# Create singleton instance
cache_strategy_service = CacheStrategyService()