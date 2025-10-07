#!/usr/bin/env python3
"""
Memory Retrieval Caching System

Implements intelligent caching for episodic memory retrieval to optimize
performance and reduce database load.

Requirements: 10.1, 10.2, 10.3
"""

import logging
import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import threading
from collections import OrderedDict

logger = logging.getLogger(__name__)


class CacheEntryType(Enum):
    """Types of cache entries"""
    MEMORY_RETRIEVAL = "memory_retrieval"
    VECTOR_SEARCH = "vector_search"
    TEAM_MEMORIES = "team_memories"
    MATCHUP_MEMORIES = "matchup_memories"
    SITUATIONAL_MEMORIES = "situational_memories"
    LEARNING_MEMORIES = "learning_memories"


@dataclass
class CacheEntry:
    """Individual cache entry with metadata"""
    key: str
    entry_type: CacheEntryType
    data: Any
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    ttl_seconds: int = 3600  # 1 hour default TTL
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return (datetime.now() - self.created_at).total_seconds() > self.ttl_seconds

    def is_stale(self, staleness_threshold_seconds: int = 1800) -> bool:
        """Check if cache entry is stale (30 minutes default)"""
        return (datetime.now() - self.created_at).total_seconds() > staleness_threshold_seconds

    def touch(self):
        """Update last accessed time and increment access count"""
        self.last_accessed = datetime.now()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'key': self.key,
            'entry_type': self.entry_type.value,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'access_count': self.access_count,
            'ttl_seconds': self.ttl_seconds,
            'metadata': self.metadata,
            'is_expired': self.is_expired(),
            'is_stale': self.is_stale()
        }


class MemoryCache:
    """
    Intelligent caching system for memory retrieval operations.

    Features:
    - LRU eviction with TTL
    - Cache hit/miss tracking
    - Intelligent cache key generation
    - Thread-safe operations
    - Performance monitoring integration
    """

    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds

        # Thread-safe cache storage using OrderedDict for LRU
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()

        # Performance tracking
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expired_entries': 0,
            'total_requests': 0
        }

        # Start background cleanup
        self._start_background_cleanup()

        logger.info(f"✅ Memory Cache initialized (max_size={max_size}, ttl={default_ttl_seconds}s)")

    def get(self, key: str) -> Optional[Any]:
        """
        Get cached data by key.

        Args:
            key: Cache key

        Returns:
            Cached data if found and not expired, None otherwise
        """
        with self._lock:
            self.stats['total_requests'] += 1

            if key not in self._cache:
                self.stats['misses'] += 1
                return None

            entry = self._cache[key]

            # Check if expired
            if entry.is_expired():
                del self._cache[key]
                self.stats['expired_entries'] += 1
                self.stats['misses'] += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()

            self.stats['hits'] += 1
            return entry.data

    def put(
        self,
        key: str,
        data: Any,
        entry_type: CacheEntryType,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache
            entry_type: Type of cache entry
            ttl_seconds: Time to live in seconds (uses default if None)
            metadata: Additional metadata
        """
        with self._lock:
            ttl = ttl_seconds or self.default_ttl_seconds
            now = datetime.now()

            entry = CacheEntry(
                key=key,
                entry_type=entry_type,
                data=data,
                created_at=now,
                last_accessed=now,
                ttl_seconds=ttl,
                metadata=metadata or {}
            )

            # Remove existing entry if present
            if key in self._cache:
                del self._cache[key]

            # Add new entry
            self._cache[key] = entry

            # Evict oldest entries if over capacity
            while len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.stats['evictions'] += 1

    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.

        Args:
            key: Cache key to invalidate

        Returns:
            True if entry was found and removed, False otherwise
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching a pattern.

        Args:
            pattern: Pattern to match (simple substring matching)

        Returns:
            Number of entries invalidated
        """
        with self._lock:
            keys_to_remove = [key for key in self._cache.keys() if pattern in key]
            for key in keys_to_remove:
                del self._cache[key]
            return len(keys_to_remove)

    def invalidate_by_expert(self, expert_id: str) -> int:
        """
        Invalidate all cache entries for a specific expert.

        Args:
            expert_id: Expert ID

        Returns:
            Number of entries invalidated
        """
        return self.invalidate_by_pattern(f"expert:{expert_id}")

    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
            logger.info("🗑️ Memory cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self._lock:
            total_requests = self.stats['total_requests']
            hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
            miss_rate = self.stats['misses'] / total_requests if total_requests > 0 else 0

            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'hit_rate': hit_rate,
                'miss_rate': miss_rate,
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'expired_entries': self.stats['expired_entries'],
                'total_requests': total_requests
            }

    def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information"""
        with self._lock:
            entries_by_type = {}
            expired_count = 0
            stale_count = 0

            for entry in self._cache.values():
                entry_type = entry.entry_type.value
                entries_by_type[entry_type] = entries_by_type.get(entry_type, 0) + 1

                if entry.is_expired():
                    expired_count += 1
                elif entry.is_stale():
                    stale_count += 1

            return {
                'stats': self.get_stats(),
                'entries_by_type': entries_by_type,
                'expired_entries': expired_count,
                'stale_entries': stale_count,
                'oldest_entry': min(self._cache.values(), key=lambda e: e.created_at).created_at.isoformat() if self._cache else None,
                'newest_entry': max(self._cache.values(), key=lambda e: e.created_at).created_at.isoformat() if self._cache else None
            }

    def _start_background_cleanup(self):
        """Start background thread for cache cleanup"""
        def cleanup_expired():
            while True:
                try:
                    self._cleanup_expired_entries()
                    time.sleep(300)  # Cleanup every 5 minutes
                except Exception as e:
                    logger.error(f"❌ Error in cache cleanup: {e}")
                    time.sleep(300)

        thread = threading.Thread(target=cleanup_expired, daemon=True)
        thread.start()
        logger.info("✅ Background cache cleanup started")

    def _cleanup_expired_entries(self):
        """Remove expired entries from cache"""
        with self._lock:
            expired_keys = []
            for key, entry in self._cache.items():
                if entry.is_expired():
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]
                self.stats['expired_entries'] += 1

            if expired_keys:
                logger.debug(f"🗑️ Cleaned up {len(expired_keys)} expired cache entries")


class MemoryCacheKeyGenerator:
    """Generates consistent cache keys for memory retrieval operations"""

    @staticmethod
    def generate_memory_retrieval_key(
        expert_id: str,
        game_context: Dict[str, Any],
        limit: int,
        bucket_type: str = "all"
    ) -> str:
        """
        Generate cache key for memory retrieval operation.

        Args:
            expert_id: Expert identifier
            game_context: Game context dictionary
            limit: Number of memories to retrieve
            bucket_type: Type of memory bucket

        Returns:
            Consistent cache key string
        """
        # Extract key context elements
        key_elements = {
            'expert_id': expert_id,
            'home_team': game_context.get('home_team'),
            'away_team': game_context.get('away_team'),
            'season': game_context.get('season'),
            'week': game_context.get('week'),
            'is_divisional': game_context.get('is_divisional', False),
            'is_primetime': game_context.get('is_primetime', False),
            'playoff_implications': game_context.get('playoff_implications', False),
            'limit': limit,
            'bucket_type': bucket_type
        }

        # Include weather conditions if significant
        weather = game_context.get('weather_conditions')
        if weather:
            if weather.get('temperature', 70) < 32:
                key_elements['cold_weather'] = True
            if weather.get('wind_speed', 0) > 15:
                key_elements['high_wind'] = True
            if weather.get('precipitation', 0) > 0:
                key_elements['precipitation'] = True

        # Create deterministic key
        key_string = json.dumps(key_elements, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"memory_retrieval:expert:{expert_id}:hash:{key_hash}"

    @staticmethod
    def generate_vector_search_key(
        expert_id: str,
        query_text: str,
        limit: int,
        threshold: float = 0.5
    ) -> str:
        """
        Generate cache key for vector search operation.

        Args:
            expert_id: Expert identifier
            query_text: Query text for embedding
            limit: Number of results to retrieve
            threshold: Similarity threshold

        Returns:
            Consistent cache key string
        """
        key_elements = {
            'expert_id': expert_id,
            'query_text': query_text,
            'limit': limit,
            'threshold': threshold
        }

        key_string = json.dumps(key_elements, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"vector_search:expert:{expert_id}:hash:{key_hash}"

    @staticmethod
    def generate_team_memories_key(
        expert_id: str,
        team: str,
        limit: int,
        memory_types: Optional[List[str]] = None
    ) -> str:
        """
        Generate cache key for team-specific memories.

        Args:
            expert_id: Expert identifier
            team: Team name
            limit: Number of memories to retrieve
            memory_types: Specific memory types to filter

        Returns:
            Consistent cache key string
        """
        key_elements = {
            'expert_id': expert_id,
            'team': team,
            'limit': limit,
            'memory_types': sorted(memory_types) if memory_types else None
        }

        key_string = json.dumps(key_elements, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()[:16]

        return f"team_memories:expert:{expert_id}:team:{team}:hash:{key_hash}"


# Global cache instance
_global_cache: Optional[MemoryCache] = None


def get_memory_cache() -> MemoryCache:
    """Get the global memory cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = MemoryCache()
    return _global_cache


def cache_memory_retrieval(
    key: str,
    data: Any,
    ttl_seconds: int = 3600,
    metadata: Optional[Dict[str, Any]] = None
):
    """Cache memory retrieval results"""
    cache = get_memory_cache()
    cache.put(
        key=key,
        data=data,
        entry_type=CacheEntryType.MEMORY_RETRIEVAL,
        ttl_seconds=ttl_seconds,
        metadata=metadata
    )


def get_cached_memory_retrieval(key: str) -> Optional[Any]:
    """Get cached memory retrieval results"""
    cache = get_memory_cache()
    return cache.get(key)


def invalidate_expert_cache(expert_id: str) -> int:
    """Invalidate all cache entries for an expert"""
    cache = get_memory_cache()
    return cache.invalidate_by_expert(expert_id)
