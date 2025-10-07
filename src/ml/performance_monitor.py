#!/usr/bin/env python3
"""
Performance Monitoring and Optimization System

Implements comprehensive performance tracking, caching, and optimization
for the NFL Expert Prediction System.

Requirements: 10.1, 10.2, 10.3, 10.6
"""

import logging
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


class PerformanceMetricType(Enum):
    """Types of performance metrics to track"""
    RESPONSE_TIME = "response_time"
    MEMORY_RETRIEVAL = "memory_retrieval"
    AI_CALL = "ai_call"
    PREDICTION_GENERATION = "prediction_generation"
    DATABASE_QUERY = "database_query"
    CACHE_HIT = "cache_hit"
    CACHE_MISS = "cache_miss"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceMetric:
    """Individual performance metric record"""
    metric_type: PerformanceMetricType
    operation_name: str
    duration_ms: float
    timestamp: datetime
    expert_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/logging"""
        return {
            'metric_type': self.metric_type.value,
            'operation_name': self.operation_name,
            'duration_ms': self.duration_ms,
            'timestamp': self.timestamp.isoformat(),
            'expert_id': self.expert_id,
            'success': self.success,
            'error_message': self.error_message,
            'metadata': self.metadata
        }


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system for expert analysis.

    Tracks response times, memory retrieval performance, AI call latency,
    and provides optimization recommendations.
    """

    def __init__(self, max_metrics_history: int = 10000):
        self.max_metrics_history = max_metrics_history
        self.metrics_history: deque = deque(maxlen=max_metrics_history)
        self.expert_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Thread-safe locks
        self._metrics_lock = threading.Lock()

        # Performance thresholds (configurable)
        self.thresholds = {
            'expert_analysis_max_ms': 60000,  # 60 seconds max per expert
            'memory_retrieval_max_ms': 2000,   # 2 seconds max for memory retrieval
            'ai_call_max_ms': 30000,          # 30 seconds max for AI calls
            'prediction_generation_max_ms': 5000,  # 5 seconds max for prediction building
            'error_rate_threshold': 0.05,      # 5% error rate threshold
            'cache_hit_rate_min': 0.7          # 70% minimum cache hit rate
        }

        logger.info("✅ Performance Monitor initialized")

    def record_metric(
        self,
        metric_type: PerformanceMetricType,
        operation_name: str,
        duration_ms: float,
        expert_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Record a performance metric.

        Args:
            metric_type: Type of metric being recorded
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            expert_id: Expert ID if applicable
            success: Whether the operation succeeded
            error_message: Error message if failed
            metadata: Additional metadata
        """
        metric = PerformanceMetric(
            metric_type=metric_type,
            operation_name=operation_name,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            expert_id=expert_id,
            success=success,
            error_message=error_message,
            metadata=metadata or {}
        )

        with self._metrics_lock:
            self.metrics_history.append(metric)

        # Check for performance issues
        self._check_performance_thresholds(metric)

    def _check_performance_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds performance thresholds"""
        operation_key = f"{metric.metric_type.value}_{metric.operation_name}"

        # Check duration thresholds
        if metric.metric_type == PerformanceMetricType.RESPONSE_TIME:
            if "expert_analysis" in metric.operation_name:
                if metric.duration_ms > self.thresholds['expert_analysis_max_ms']:
                    logger.warning(f"⚠️ Expert analysis exceeded threshold: {metric.duration_ms:.0f}ms > {self.thresholds['expert_analysis_max_ms']}ms")

        elif metric.metric_type == PerformanceMetricType.MEMORY_RETRIEVAL:
            if metric.duration_ms > self.thresholds['memory_retrieval_max_ms']:
                logger.warning(f"⚠️ Memory retrieval exceeded threshold: {metric.duration_ms:.0f}ms > {self.thresholds['memory_retrieval_max_ms']}ms")

        elif metric.metric_type == PerformanceMetricType.AI_CALL:
            if metric.duration_ms > self.thresholds['ai_call_max_ms']:
                logger.warning(f"⚠️ AI call exceeded threshold: {metric.duration_ms:.0f}ms > {self.thresholds['ai_call_max_ms']}ms")

        # Log errors
        if not metric.success:
            logger.error(f"❌ Operation failed: {operation_key} - {metric.error_message}")

    def get_system_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        with self._metrics_lock:
            now = datetime.now()
            recent_metrics = [m for m in self.metrics_history
                            if (now - m.timestamp).total_seconds() < 3600]  # Last hour

            if not recent_metrics:
                return {
                    'status': 'no_data',
                    'message': 'No recent performance data available',
                    'timestamp': now.isoformat()
                }

            # Calculate overall system metrics
            total_operations = len(recent_metrics)
            successful_operations = sum(1 for m in recent_metrics if m.success)
            error_rate = (total_operations - successful_operations) / total_operations if total_operations > 0 else 0

            # Calculate response time statistics
            durations = [m.duration_ms for m in recent_metrics if m.success]
            if durations:
                avg_duration = statistics.mean(durations)
                p95_duration = statistics.quantiles(durations, n=20)[18] if len(durations) >= 20 else max(durations)
            else:
                avg_duration = 0
                p95_duration = 0

            # Determine system status
            status = 'healthy'
            issues = []

            if error_rate > self.thresholds['error_rate_threshold']:
                status = 'degraded'
                issues.append(f"High error rate: {error_rate:.2%}")

            if avg_duration > self.thresholds['expert_analysis_max_ms'] / 2:
                status = 'degraded'
                issues.append(f"High average response time: {avg_duration:.0f}ms")

            return {
                'status': status,
                'timestamp': now.isoformat(),
                'issues': issues,
                'metrics': {
                    'total_operations_last_hour': total_operations,
                    'successful_operations': successful_operations,
                    'error_rate': error_rate,
                    'avg_response_time_ms': avg_duration,
                    'p95_response_time_ms': p95_duration
                },
                'thresholds': self.thresholds
            }


class PerformanceTimer:
    """Context manager for timing operations and recording metrics"""

    def __init__(
        self,
        monitor: PerformanceMonitor,
        metric_type: PerformanceMetricType,
        operation_name: str,
        expert_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.monitor = monitor
        self.metric_type = metric_type
        self.operation_name = operation_name
        self.expert_id = expert_id
        self.metadata = metadata or {}
        self.start_time = None
        self.success = True
        self.error_message = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000

            if exc_type is not None:
                self.success = False
                self.error_message = str(exc_val) if exc_val else "Unknown error"

            self.monitor.record_metric(
                metric_type=self.metric_type,
                operation_name=self.operation_name,
                duration_ms=duration_ms,
                expert_id=self.expert_id,
                success=self.success,
                error_message=self.error_message,
                metadata=self.metadata
            )

    def mark_error(self, error_message: str):
        """Mark the operation as failed with an error message"""
        self.success = False
        self.error_message = error_message


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def performance_timer(
    metric_type: PerformanceMetricType,
    operation_name: str,
    expert_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> PerformanceTimer:
    """Create a performance timer context manager"""
    monitor = get_performance_monitor()
    return PerformanceTimer(monitor, metric_type, operation_name, expert_id, metadata)


def record_performance_metric(
    metric_type: PerformanceMetricType,
    operation_name: str,
    duration_ms: float,
    expert_id: Optional[str] = None,
    success: bool = True,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Record a performance metric using the global monitor"""
    monitor = get_performance_monitor()
    monitor.record_metric(
        metric_type=metric_type,
        operation_name=operation_name,
        duration_ms=duration_ms,
        expert_id=expert_id,
        success=success,
        error_message=error_message,
        metadata=metadata
    )
