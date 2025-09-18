"""
Performance Optimization Service for NFL Predictions API
Implements caching, database optimization, and parallel processing for sub-second response times
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import hashlib
from functools import wraps

logger = logging.getLogger(__name__)

class PredictionCache:
    """Advanced caching system for prediction data"""

    def __init__(self):
        self.cache: Dict[str, Tuple[Any, float, int]] = {}  # key: (data, timestamp, ttl)
        self.hit_count = 0
        self.miss_count = 0
        self.size_limit = 1000  # Maximum cache entries

    def _generate_key(self, *args, **kwargs) -> str:
        """Generate unique cache key"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get data from cache"""
        if key in self.cache:
            data, timestamp, ttl = self.cache[key]
            if time.time() - timestamp < ttl:
                self.hit_count += 1
                return data
            else:
                del self.cache[key]
                self.miss_count += 1
                return None
        else:
            self.miss_count += 1
            return None

    def set(self, key: str, data: Any, ttl: int = 60):
        """Store data in cache"""
        # Implement LRU eviction if cache is full
        if len(self.cache) >= self.size_limit:
            self._evict_lru()

        self.cache[key] = (data, time.time(), ttl)

    def _evict_lru(self):
        """Evict least recently used items"""
        # Sort by timestamp and remove oldest 10%
        sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
        evict_count = max(1, len(sorted_items) // 10)

        for i in range(evict_count):
            key = sorted_items[i][0]
            del self.cache[key]

    def clear_expired(self):
        """Clear expired cache entries"""
        now = time.time()
        expired_keys = [
            key for key, (_, timestamp, ttl) in self.cache.items()
            if now - timestamp >= ttl
        ]
        for key in expired_keys:
            del self.cache[key]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0

        return {
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "hit_rate": hit_rate,
            "cache_size": len(self.cache),
            "memory_usage": sum(len(str(data)) for data, _, _ in self.cache.values())
        }

# Global cache instance
prediction_cache = PredictionCache()

class ParallelPredictionProcessor:
    """Parallel processing for generating multiple predictions"""

    def __init__(self, max_workers: int = 10):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def process_experts_parallel(self, expert_funcs: List[Callable], *args, **kwargs) -> List[Any]:
        """Process multiple expert predictions in parallel"""
        loop = asyncio.get_event_loop()

        # Submit all expert functions to thread pool
        futures = [
            loop.run_in_executor(self.executor, func, *args, **kwargs)
            for func in expert_funcs
        ]

        # Wait for all predictions with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*futures, return_exceptions=True),
                timeout=5.0  # 5 second timeout
            )

            # Filter out exceptions and return valid results
            valid_results = [
                result for result in results
                if not isinstance(result, Exception)
            ]

            return valid_results

        except asyncio.TimeoutError:
            logger.warning("Some expert predictions timed out")
            # Return partial results
            completed_futures = [f for f in futures if f.done()]
            return [f.result() for f in completed_futures if not f.exception()]

    async def batch_process_games(self, game_ids: List[str], process_func: Callable) -> Dict[str, Any]:
        """Process multiple games in parallel"""
        loop = asyncio.get_event_loop()

        # Submit all game processing to thread pool
        futures = {
            game_id: loop.run_in_executor(self.executor, process_func, game_id)
            for game_id in game_ids
        }

        results = {}
        # Process results as they complete
        for game_id, future in futures.items():
            try:
                result = await asyncio.wait_for(future, timeout=3.0)
                results[game_id] = result
            except Exception as e:
                logger.error(f"Error processing game {game_id}: {e}")
                results[game_id] = None

        return results

# Global parallel processor
parallel_processor = ParallelPredictionProcessor()

class DatabaseOptimizer:
    """Database query optimization and connection pooling"""

    def __init__(self):
        self.query_cache: Dict[str, Tuple[Any, float]] = {}
        self.prepared_statements: Dict[str, str] = {}

    def cache_query_result(self, query_hash: str, result: Any, ttl: int = 300):
        """Cache database query results"""
        self.query_cache[query_hash] = (result, time.time() + ttl)

    def get_cached_query(self, query_hash: str) -> Optional[Any]:
        """Get cached query result"""
        if query_hash in self.query_cache:
            result, expiry = self.query_cache[query_hash]
            if time.time() < expiry:
                return result
            else:
                del self.query_cache[query_hash]
        return None

    def optimize_prediction_queries(self) -> Dict[str, str]:
        """Optimized SQL queries for prediction data"""
        return {
            "expert_performance": """
                SELECT expert_id, accuracy, total_predictions, recent_form
                FROM expert_performance
                WHERE last_updated > %s
                ORDER BY accuracy DESC
            """,
            "game_data": """
                SELECT game_id, home_team, away_team, spread, total, weather_data
                FROM games
                WHERE game_id = %s AND game_date > %s
            """,
            "recent_predictions": """
                SELECT p.*, e.expert_name
                FROM predictions p
                JOIN experts e ON p.expert_id = e.expert_id
                WHERE p.game_id = %s AND p.created_at > %s
                ORDER BY p.confidence DESC
            """
        }

# Global database optimizer
db_optimizer = DatabaseOptimizer()

class PerformanceMonitor:
    """Real-time performance monitoring and optimization"""

    def __init__(self):
        self.response_times: List[float] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_requests": 0,
            "total_time": 0.0,
            "min_time": float('inf'),
            "max_time": 0.0,
            "error_count": 0
        })

    def record_request(self, endpoint: str, response_time: float, success: bool = True):
        """Record request performance metrics"""
        stats = self.endpoint_stats[endpoint]
        stats["total_requests"] += 1
        stats["total_time"] += response_time
        stats["min_time"] = min(stats["min_time"], response_time)
        stats["max_time"] = max(stats["max_time"], response_time)

        if not success:
            stats["error_count"] += 1
            self.error_counts[endpoint] += 1

        # Keep rolling window of response times
        self.response_times.append(response_time)
        if len(self.response_times) > 1000:
            self.response_times.pop(0)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        if not self.response_times:
            return {"status": "no_data"}

        avg_response_time = sum(self.response_times) / len(self.response_times)
        p95_response_time = sorted(self.response_times)[int(0.95 * len(self.response_times))]

        endpoint_summaries = {}
        for endpoint, stats in self.endpoint_stats.items():
            if stats["total_requests"] > 0:
                endpoint_summaries[endpoint] = {
                    "avg_response_time": stats["total_time"] / stats["total_requests"],
                    "min_response_time": stats["min_time"],
                    "max_response_time": stats["max_time"],
                    "total_requests": stats["total_requests"],
                    "error_rate": stats["error_count"] / stats["total_requests"],
                    "requests_per_minute": stats["total_requests"]  # Simplified calculation
                }

        return {
            "overall": {
                "avg_response_time": avg_response_time,
                "p95_response_time": p95_response_time,
                "total_requests": len(self.response_times),
                "cache_stats": prediction_cache.get_stats()
            },
            "endpoints": endpoint_summaries,
            "errors": dict(self.error_counts)
        }

    def is_performance_degraded(self) -> Tuple[bool, str]:
        """Check if performance is degraded"""
        if len(self.response_times) < 10:
            return False, "Insufficient data"

        recent_avg = sum(self.response_times[-10:]) / 10
        overall_avg = sum(self.response_times) / len(self.response_times)

        # Performance is degraded if recent average is 50% higher than overall
        if recent_avg > overall_avg * 1.5:
            return True, f"Response time degraded: {recent_avg:.3f}s vs {overall_avg:.3f}s avg"

        return False, "Performance normal"

# Global performance monitor
performance_monitor = PerformanceMonitor()

def performance_tracked(endpoint_name: str):
    """Decorator to track endpoint performance"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                response_time = time.time() - start_time
                performance_monitor.record_request(endpoint_name, response_time, success)

        return wrapper
    return decorator

class PredictionOptimizer:
    """Main optimization service for predictions"""

    def __init__(self):
        self.cache = prediction_cache
        self.parallel_processor = parallel_processor
        self.db_optimizer = db_optimizer
        self.monitor = performance_monitor

    async def get_optimized_predictions(self, game_id: str, expert_ids: List[str]) -> List[Any]:
        """Get predictions with full optimization"""
        # Check cache first
        cache_key = f"predictions:{game_id}:{':'.join(sorted(expert_ids))}"
        cached_result = self.cache.get(cache_key)

        if cached_result:
            logger.info(f"Cache hit for game {game_id}")
            return cached_result

        # Generate predictions in parallel
        start_time = time.time()

        try:
            # This would be replaced with actual expert prediction functions
            expert_funcs = [lambda: f"prediction_from_{eid}" for eid in expert_ids]

            predictions = await self.parallel_processor.process_experts_parallel(
                expert_funcs, game_id
            )

            # Cache the results
            self.cache.set(cache_key, predictions, ttl=60)

            logger.info(f"Generated {len(predictions)} predictions in {time.time() - start_time:.3f}s")
            return predictions

        except Exception as e:
            logger.error(f"Error generating optimized predictions: {e}")
            raise

    async def batch_optimize_multiple_games(self, game_ids: List[str]) -> Dict[str, List[Any]]:
        """Optimize predictions for multiple games"""
        results = {}

        # Process games in parallel batches
        batch_size = 5
        for i in range(0, len(game_ids), batch_size):
            batch = game_ids[i:i + batch_size]

            batch_results = await self.parallel_processor.batch_process_games(
                batch,
                lambda gid: self.get_optimized_predictions(gid, ["expert_001", "expert_002"])
            )

            results.update(batch_results)

        return results

    def preload_cache(self, upcoming_games: List[str]):
        """Preload cache with likely requested data"""
        # This would run in background to warm up cache
        pass

    def optimize_database_queries(self):
        """Optimize database connections and queries"""
        # Implementation would include:
        # - Connection pooling optimization
        # - Query plan analysis
        # - Index recommendations
        pass

    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for further optimization"""
        perf_stats = self.monitor.get_performance_stats()
        cache_stats = self.cache.get_stats()

        recommendations = []

        # Cache hit rate recommendations
        if cache_stats.get("hit_rate", 0) < 0.7:
            recommendations.append({
                "type": "cache",
                "priority": "high",
                "message": f"Cache hit rate is low: {cache_stats.get('hit_rate', 0):.2%}",
                "action": "Increase cache TTL or preload more data"
            })

        # Response time recommendations
        overall_stats = perf_stats.get("overall", {})
        avg_response_time = overall_stats.get("avg_response_time", 0)

        if avg_response_time > 1.0:
            recommendations.append({
                "type": "performance",
                "priority": "high",
                "message": f"Average response time is high: {avg_response_time:.3f}s",
                "action": "Consider increasing parallel processing or database optimization"
            })

        # Error rate recommendations
        for endpoint, stats in perf_stats.get("endpoints", {}).items():
            error_rate = stats.get("error_rate", 0)
            if error_rate > 0.05:  # 5% error rate threshold
                recommendations.append({
                    "type": "reliability",
                    "priority": "medium",
                    "message": f"High error rate on {endpoint}: {error_rate:.2%}",
                    "action": "Review error handling and retry logic"
                })

        return {
            "recommendations": recommendations,
            "current_performance": perf_stats,
            "cache_efficiency": cache_stats
        }

# Global optimizer instance
prediction_optimizer = PredictionOptimizer()

# Utility functions for API endpoints
async def get_fast_prediction_data(game_id: str) -> Dict[str, Any]:
    """Optimized function to get prediction data quickly"""
    cache_key = f"game_data:{game_id}"
    cached_data = prediction_cache.get(cache_key)

    if cached_data:
        return cached_data

    # Simulate fast data retrieval (would be actual database call)
    game_data = {
        "game_id": game_id,
        "home_team": "KC",
        "away_team": "BUF",
        "spread": -2.5,
        "total": 54.5,
        "last_updated": datetime.now()
    }

    prediction_cache.set(cache_key, game_data, ttl=120)
    return game_data

async def get_expert_predictions_fast(game_id: str, expert_ids: List[str]) -> List[Dict[str, Any]]:
    """Fast expert prediction retrieval with caching"""
    return await prediction_optimizer.get_optimized_predictions(game_id, expert_ids)

# Background tasks
async def cache_maintenance_task():
    """Background task for cache maintenance"""
    while True:
        try:
            # Clear expired entries every 5 minutes
            prediction_cache.clear_expired()

            # Log performance stats every 10 minutes
            if int(time.time()) % 600 == 0:
                stats = performance_monitor.get_performance_stats()
                logger.info(f"Performance stats: {stats}")

            await asyncio.sleep(300)  # 5 minutes

        except Exception as e:
            logger.error(f"Cache maintenance error: {e}")
            await asyncio.sleep(60)

async def performance_monitoring_task():
    """Background task for performance monitoring"""
    while True:
        try:
            # Check for performance degradation
            is_degraded, message = performance_monitor.is_performance_degraded()

            if is_degraded:
                logger.warning(f"Performance degradation detected: {message}")

                # Get optimization recommendations
                recommendations = prediction_optimizer.get_optimization_recommendations()
                logger.info(f"Optimization recommendations: {recommendations}")

            await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Performance monitoring error: {e}")
            await asyncio.sleep(60)