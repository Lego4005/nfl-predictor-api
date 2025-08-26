"""
Cache Health Monitor for NFL Predictor live data integration.

Monitors cache performance, health status, and provides automatic fallback logic.
Implements cache invalidation strategies and health reporting.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .cache_manager import CacheManager, CacheStatus

logger = logging.getLogger(__name__)


@dataclass
class CacheHealthMetrics:
    """Cache health metrics and statistics."""
    hit_rate: float
    miss_rate: float
    error_rate: float
    average_response_time: float
    redis_available: bool
    memory_cache_size: int
    total_requests: int
    total_hits: int
    total_misses: int
    total_errors: int


class CacheHealthMonitor:
    """
    Monitors cache health and provides fallback logic.
    
    Tracks cache performance metrics, handles Redis failures,
    and implements intelligent cache invalidation strategies.
    """
    
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.metrics = {
            'requests': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'response_times': []
        }
        self.health_checks = []
        self.last_health_check = None
        self.redis_failure_count = 0
        self.max_redis_failures = 3
        self.health_check_interval = 300  # 5 minutes
    
    def record_cache_hit(self, response_time: float = 0.0):
        """Record a cache hit with response time."""
        self.metrics['requests'] += 1
        self.metrics['hits'] += 1
        if response_time > 0:
            self.metrics['response_times'].append(response_time)
    
    def record_cache_miss(self, response_time: float = 0.0):
        """Record a cache miss with response time."""
        self.metrics['requests'] += 1
        self.metrics['misses'] += 1
        if response_time > 0:
            self.metrics['response_times'].append(response_time)
    
    def record_cache_error(self, error_type: str, response_time: float = 0.0):
        """Record a cache error with details."""
        self.metrics['requests'] += 1
        self.metrics['errors'] += 1
        if response_time > 0:
            self.metrics['response_times'].append(response_time)
        
        # Track Redis-specific failures
        if 'redis' in error_type.lower():
            self.redis_failure_count += 1
            logger.warning(f"Redis failure #{self.redis_failure_count}: {error_type}")
    
    def get_health_metrics(self) -> CacheHealthMetrics:
        """Calculate and return current health metrics."""
        total_requests = self.metrics['requests']
        
        if total_requests == 0:
            hit_rate = miss_rate = error_rate = 0.0
            avg_response_time = 0.0
        else:
            hit_rate = self.metrics['hits'] / total_requests
            miss_rate = self.metrics['misses'] / total_requests
            error_rate = self.metrics['errors'] / total_requests
            
            response_times = self.metrics['response_times']
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0.0
        
        cache_status = self.cache_manager.get_health_status()
        
        return CacheHealthMetrics(
            hit_rate=hit_rate,
            miss_rate=miss_rate,
            error_rate=error_rate,
            average_response_time=avg_response_time,
            redis_available=cache_status.get('redis_healthy', False),
            memory_cache_size=cache_status.get('memory_cache_size', 0),
            total_requests=total_requests,
            total_hits=self.metrics['hits'],
            total_misses=self.metrics['misses'],
            total_errors=self.metrics['errors']
        )
    
    def is_cache_healthy(self) -> bool:
        """
        Determine if cache is healthy based on metrics.
        
        Returns:
            True if cache is performing well, False otherwise
        """
        metrics = self.get_health_metrics()
        
        # Cache is unhealthy if:
        # - Error rate > 20%
        # - Redis is down and memory cache is full
        # - Too many consecutive Redis failures
        
        if metrics.error_rate > 0.2:
            logger.warning(f"Cache unhealthy: high error rate ({metrics.error_rate:.2%})")
            return False
        
        if not metrics.redis_available and metrics.memory_cache_size > 900:  # Near limit
            logger.warning("Cache unhealthy: Redis down and memory cache near full")
            return False
        
        if self.redis_failure_count >= self.max_redis_failures:
            logger.warning(f"Cache unhealthy: too many Redis failures ({self.redis_failure_count})")
            return False
        
        return True
    
    def should_use_cache(self) -> bool:
        """
        Determine if cache should be used based on health status.
        
        Returns:
            True if cache should be used, False to bypass cache
        """
        if not self.is_cache_healthy():
            return False
        
        # Additional logic for cache bypass
        metrics = self.get_health_metrics()
        
        # If hit rate is very low, might be better to bypass cache temporarily
        if metrics.total_requests > 100 and metrics.hit_rate < 0.1:
            logger.info("Bypassing cache due to low hit rate")
            return False
        
        return True
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive cache health check.
        
        Returns:
            Health check results with recommendations
        """
        start_time = datetime.utcnow()
        
        health_result = {
            'timestamp': start_time.isoformat(),
            'overall_status': 'healthy',
            'redis_status': 'unknown',
            'memory_cache_status': 'unknown',
            'recommendations': [],
            'metrics': None
        }
        
        try:
            # Test Redis connectivity
            cache_status = self.cache_manager.get_health_status()
            redis_healthy = cache_status.get('redis_healthy', False)
            
            if redis_healthy:
                health_result['redis_status'] = 'healthy'
                # Reset failure count on successful check
                self.redis_failure_count = 0
            else:
                health_result['redis_status'] = 'unhealthy'
                health_result['overall_status'] = 'degraded'
                health_result['recommendations'].append(
                    "Redis is unavailable. Using in-memory cache fallback."
                )
            
            # Check memory cache status
            memory_size = cache_status.get('memory_cache_size', 0)
            memory_limit = cache_status.get('memory_cache_limit', 1000)
            memory_usage = memory_size / memory_limit if memory_limit > 0 else 0
            
            if memory_usage < 0.8:
                health_result['memory_cache_status'] = 'healthy'
            elif memory_usage < 0.95:
                health_result['memory_cache_status'] = 'warning'
                health_result['recommendations'].append(
                    f"Memory cache usage high ({memory_usage:.1%}). Consider clearing old entries."
                )
            else:
                health_result['memory_cache_status'] = 'critical'
                health_result['overall_status'] = 'unhealthy'
                health_result['recommendations'].append(
                    "Memory cache nearly full. Performance may be degraded."
                )
            
            # Get performance metrics
            metrics = self.get_health_metrics()
            health_result['metrics'] = {
                'hit_rate': f"{metrics.hit_rate:.2%}",
                'error_rate': f"{metrics.error_rate:.2%}",
                'avg_response_time': f"{metrics.average_response_time:.3f}s",
                'total_requests': metrics.total_requests
            }
            
            # Performance-based recommendations
            if metrics.hit_rate < 0.3 and metrics.total_requests > 50:
                health_result['recommendations'].append(
                    f"Low cache hit rate ({metrics.hit_rate:.1%}). Consider adjusting TTL or cache warming."
                )
            
            if metrics.error_rate > 0.1:
                health_result['recommendations'].append(
                    f"High error rate ({metrics.error_rate:.1%}). Check cache configuration."
                )
            
            # Update overall status based on all factors
            if not self.is_cache_healthy():
                health_result['overall_status'] = 'unhealthy'
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            health_result['overall_status'] = 'error'
            health_result['recommendations'].append(f"Health check failed: {str(e)}")
        
        # Record health check
        self.health_checks.append(health_result)
        self.last_health_check = start_time
        
        # Keep only last 24 health checks
        if len(self.health_checks) > 24:
            self.health_checks = self.health_checks[-24:]
        
        return health_result
    
    async def invalidate_on_api_error(
        self,
        source: str,
        endpoint: str,
        week: int,
        error_type: str
    ) -> int:
        """
        Invalidate cache entries when API errors occur.
        
        Args:
            source: Data source that failed
            endpoint: API endpoint that failed
            week: NFL week number
            error_type: Type of error that occurred
            
        Returns:
            Number of cache entries invalidated
        """
        invalidated_count = 0
        
        try:
            # Generate cache key pattern for the failed request
            cache_key_base = self.cache_manager.get_cache_key_for_predictions(
                week=week,
                prediction_type="*",
                year=2025
            )
            
            # Different invalidation strategies based on error type
            if error_type in ['authentication_error', 'api_unavailable']:
                # Invalidate all data from this source for this week
                pattern = f"{cache_key_base}:{source}:*"
                invalidated_count = self.cache_manager.invalidate_pattern(pattern)
                logger.info(f"Invalidated {invalidated_count} entries for {source} due to {error_type}")
                
            elif error_type == 'invalid_data':
                # Invalidate specific endpoint data
                endpoint_clean = endpoint.replace('/', '_')
                pattern = f"{cache_key_base}:{source}:{endpoint_clean}"
                invalidated_count = self.cache_manager.invalidate_pattern(pattern)
                logger.info(f"Invalidated {invalidated_count} entries for {source}:{endpoint} due to invalid data")
                
            elif error_type == 'rate_limited':
                # Don't invalidate on rate limiting - data might still be valid
                logger.info(f"Rate limited for {source}, keeping cached data")
                
            else:
                # For other errors, invalidate conservatively
                endpoint_clean = endpoint.replace('/', '_')
                pattern = f"{cache_key_base}:{source}:{endpoint_clean}"
                invalidated_count = self.cache_manager.invalidate_pattern(pattern)
                logger.info(f"Invalidated {invalidated_count} entries for {source}:{endpoint} due to {error_type}")
        
        except Exception as e:
            logger.error(f"Failed to invalidate cache on API error: {str(e)}")
        
        return invalidated_count
    
    def get_fallback_recommendation(self) -> Dict[str, Any]:
        """
        Get recommendation for cache fallback strategy.
        
        Returns:
            Fallback strategy recommendation
        """
        metrics = self.get_health_metrics()
        cache_status = self.cache_manager.get_health_status()
        
        recommendation = {
            'use_cache': True,
            'strategy': 'normal',
            'reason': 'Cache is healthy',
            'alternatives': []
        }
        
        if not metrics.redis_available:
            if metrics.memory_cache_size > 0:
                recommendation.update({
                    'use_cache': True,
                    'strategy': 'memory_only',
                    'reason': 'Redis unavailable, using memory cache',
                    'alternatives': ['Direct API calls if memory cache fails']
                })
            else:
                recommendation.update({
                    'use_cache': False,
                    'strategy': 'bypass',
                    'reason': 'No cache available',
                    'alternatives': ['Direct API calls only']
                })
        
        elif metrics.error_rate > 0.3:
            recommendation.update({
                'use_cache': False,
                'strategy': 'bypass_temporary',
                'reason': f'High error rate ({metrics.error_rate:.1%})',
                'alternatives': ['Direct API calls until cache recovers']
            })
        
        elif metrics.memory_cache_size > 950:  # Near memory limit
            recommendation.update({
                'use_cache': True,
                'strategy': 'aggressive_cleanup',
                'reason': 'Memory cache nearly full',
                'alternatives': ['Clear old entries', 'Reduce TTL temporarily']
            })
        
        return recommendation
    
    def reset_metrics(self):
        """Reset performance metrics (useful for testing or periodic resets)."""
        self.metrics = {
            'requests': 0,
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'response_times': []
        }
        self.redis_failure_count = 0
        logger.info("Cache metrics reset")
    
    def get_health_history(self) -> List[Dict[str, Any]]:
        """Get historical health check results."""
        return self.health_checks.copy()