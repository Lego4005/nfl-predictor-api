"""
Cache monitoring and alerting system for NFL Predictor.
Provides real-time monitoring, metrics collection, and alerting for Redis cache.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import time
import statistics

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to collect"""
    MEMORY_USAGE = "memory_usage"
    CONNECTION_COUNT = "connection_count"
    HIT_RATE = "hit_rate"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class CacheMetric:
    """Cache metric data point"""
    metric_type: MetricType
    value: float
    timestamp: datetime
    unit: str
    tags: Dict[str, str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit,
            "tags": self.tags or {}
        }


@dataclass
class CacheAlert:
    """Cache alert information"""
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "level": self.level.value,
            "metric_type": self.metric_type.value,
            "message": self.message,
            "value": self.value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved
        }


@dataclass
class MonitoringConfig:
    """Configuration for cache monitoring"""
    collection_interval: int = 30  # seconds
    retention_hours: int = 24
    memory_warning_threshold: float = 80.0  # percentage
    memory_critical_threshold: float = 90.0  # percentage
    connection_warning_threshold: int = 50
    connection_critical_threshold: int = 100
    response_time_warning_threshold: float = 100.0  # milliseconds
    response_time_critical_threshold: float = 500.0  # milliseconds
    error_rate_warning_threshold: float = 5.0  # percentage
    error_rate_critical_threshold: float = 10.0  # percentage
    hit_rate_warning_threshold: float = 70.0  # percentage
    hit_rate_critical_threshold: float = 50.0  # percentage


class CacheMonitor:
    """
    Real-time cache monitoring and alerting system.
    Collects metrics, detects anomalies, and sends alerts.
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        config: Optional[MonitoringConfig] = None
    ):
        self.redis_client = redis_client
        self.config = config or MonitoringConfig()
        
        # Metrics storage
        self.metrics: Dict[MetricType, List[CacheMetric]] = {
            metric_type: [] for metric_type in MetricType
        }
        
        # Active alerts
        self.active_alerts: List[CacheAlert] = []
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[CacheAlert], None]] = []
        
        # Monitoring state
        self._monitoring_active = False
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._last_stats = {}
        self._operation_counts = {"hits": 0, "misses": 0, "errors": 0}
    
    def add_alert_callback(self, callback: Callable[[CacheAlert], None]):
        """Add callback function for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.config.retention_hours)
        
        for metric_type in self.metrics:
            self.metrics[metric_type] = [
                metric for metric in self.metrics[metric_type]
                if metric.timestamp > cutoff_time
            ]
    
    def _collect_redis_metrics(self) -> List[CacheMetric]:
        """Collect metrics from Redis"""
        if not self.redis_client:
            return []
        
        metrics = []
        timestamp = datetime.utcnow()
        
        try:
            # Get Redis info
            info = self.redis_client.info()
            
            # Memory usage metrics
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            
            if max_memory > 0:
                memory_usage_percent = (used_memory / max_memory) * 100
                metrics.append(CacheMetric(
                    metric_type=MetricType.MEMORY_USAGE,
                    value=memory_usage_percent,
                    timestamp=timestamp,
                    unit="percent"
                ))
            
            # Connection count
            connected_clients = info.get("connected_clients", 0)
            metrics.append(CacheMetric(
                metric_type=MetricType.CONNECTION_COUNT,
                value=connected_clients,
                timestamp=timestamp,
                unit="count"
            ))
            
            # Hit rate calculation
            keyspace_hits = info.get("keyspace_hits", 0)
            keyspace_misses = info.get("keyspace_misses", 0)
            total_requests = keyspace_hits + keyspace_misses
            
            if total_requests > 0:
                hit_rate = (keyspace_hits / total_requests) * 100
                metrics.append(CacheMetric(
                    metric_type=MetricType.HIT_RATE,
                    value=hit_rate,
                    timestamp=timestamp,
                    unit="percent"
                ))
            
            # Throughput (operations per second)
            if self._last_stats:
                time_diff = timestamp - self._last_stats.get("timestamp", timestamp)
                if time_diff.total_seconds() > 0:
                    ops_diff = info.get("total_commands_processed", 0) - self._last_stats.get("total_commands", 0)
                    throughput = ops_diff / time_diff.total_seconds()
                    
                    metrics.append(CacheMetric(
                        metric_type=MetricType.THROUGHPUT,
                        value=throughput,
                        timestamp=timestamp,
                        unit="ops/sec"
                    ))
            
            # Store current stats for next calculation
            self._last_stats = {
                "timestamp": timestamp,
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": keyspace_hits,
                "keyspace_misses": keyspace_misses
            }
            
        except Exception as e:
            logger.error(f"Failed to collect Redis metrics: {e}")
            
            # Record error rate
            self._operation_counts["errors"] += 1
            total_ops = sum(self._operation_counts.values())
            if total_ops > 0:
                error_rate = (self._operation_counts["errors"] / total_ops) * 100
                metrics.append(CacheMetric(
                    metric_type=MetricType.ERROR_RATE,
                    value=error_rate,
                    timestamp=timestamp,
                    unit="percent"
                ))
        
        return metrics
    
    def _measure_response_time(self) -> Optional[float]:
        """Measure Redis response time"""
        if not self.redis_client:
            return None
        
        try:
            start_time = time.time()
            self.redis_client.ping()
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            return response_time
        except Exception as e:
            logger.warning(f"Response time measurement failed: {e}")
            return None
    
    def _check_thresholds(self, metrics: List[CacheMetric]):
        """Check metrics against thresholds and generate alerts"""
        for metric in metrics:
            alerts_to_create = []
            
            if metric.metric_type == MetricType.MEMORY_USAGE:
                if metric.value >= self.config.memory_critical_threshold:
                    alerts_to_create.append((AlertLevel.CRITICAL, f"Memory usage critical: {metric.value:.1f}%"))
                elif metric.value >= self.config.memory_warning_threshold:
                    alerts_to_create.append((AlertLevel.WARNING, f"Memory usage high: {metric.value:.1f}%"))
            
            elif metric.metric_type == MetricType.CONNECTION_COUNT:
                if metric.value >= self.config.connection_critical_threshold:
                    alerts_to_create.append((AlertLevel.CRITICAL, f"Connection count critical: {metric.value}"))
                elif metric.value >= self.config.connection_warning_threshold:
                    alerts_to_create.append((AlertLevel.WARNING, f"Connection count high: {metric.value}"))
            
            elif metric.metric_type == MetricType.RESPONSE_TIME:
                if metric.value >= self.config.response_time_critical_threshold:
                    alerts_to_create.append((AlertLevel.CRITICAL, f"Response time critical: {metric.value:.1f}ms"))
                elif metric.value >= self.config.response_time_warning_threshold:
                    alerts_to_create.append((AlertLevel.WARNING, f"Response time high: {metric.value:.1f}ms"))
            
            elif metric.metric_type == MetricType.ERROR_RATE:
                if metric.value >= self.config.error_rate_critical_threshold:
                    alerts_to_create.append((AlertLevel.CRITICAL, f"Error rate critical: {metric.value:.1f}%"))
                elif metric.value >= self.config.error_rate_warning_threshold:
                    alerts_to_create.append((AlertLevel.WARNING, f"Error rate high: {metric.value:.1f}%"))
            
            elif metric.metric_type == MetricType.HIT_RATE:
                if metric.value <= self.config.hit_rate_critical_threshold:
                    alerts_to_create.append((AlertLevel.CRITICAL, f"Hit rate critical: {metric.value:.1f}%"))
                elif metric.value <= self.config.hit_rate_warning_threshold:
                    alerts_to_create.append((AlertLevel.WARNING, f"Hit rate low: {metric.value:.1f}%"))
            
            # Create alerts
            for level, message in alerts_to_create:
                threshold = self._get_threshold_for_metric(metric.metric_type, level)
                alert = CacheAlert(
                    level=level,
                    metric_type=metric.metric_type,
                    message=message,
                    value=metric.value,
                    threshold=threshold,
                    timestamp=metric.timestamp
                )
                
                # Check if similar alert already exists
                if not self._alert_exists(alert):
                    self.active_alerts.append(alert)
                    self._notify_alert(alert)
    
    def _get_threshold_for_metric(self, metric_type: MetricType, level: AlertLevel) -> float:
        """Get threshold value for metric type and alert level"""
        thresholds = {
            MetricType.MEMORY_USAGE: {
                AlertLevel.WARNING: self.config.memory_warning_threshold,
                AlertLevel.CRITICAL: self.config.memory_critical_threshold
            },
            MetricType.CONNECTION_COUNT: {
                AlertLevel.WARNING: self.config.connection_warning_threshold,
                AlertLevel.CRITICAL: self.config.connection_critical_threshold
            },
            MetricType.RESPONSE_TIME: {
                AlertLevel.WARNING: self.config.response_time_warning_threshold,
                AlertLevel.CRITICAL: self.config.response_time_critical_threshold
            },
            MetricType.ERROR_RATE: {
                AlertLevel.WARNING: self.config.error_rate_warning_threshold,
                AlertLevel.CRITICAL: self.config.error_rate_critical_threshold
            },
            MetricType.HIT_RATE: {
                AlertLevel.WARNING: self.config.hit_rate_warning_threshold,
                AlertLevel.CRITICAL: self.config.hit_rate_critical_threshold
            }
        }
        
        return thresholds.get(metric_type, {}).get(level, 0.0)
    
    def _alert_exists(self, new_alert: CacheAlert) -> bool:
        """Check if similar alert already exists"""
        for alert in self.active_alerts:
            if (alert.metric_type == new_alert.metric_type and
                alert.level == new_alert.level and
                not alert.resolved and
                (new_alert.timestamp - alert.timestamp).total_seconds() < 300):  # 5 minutes
                return True
        return False
    
    def _notify_alert(self, alert: CacheAlert):
        """Send alert notifications"""
        logger.warning(f"Cache Alert [{alert.level.value.upper()}]: {alert.message}")
        
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        logger.info("Cache monitoring started")
        
        while self._monitoring_active:
            try:
                # Collect metrics
                metrics = self._collect_redis_metrics()
                
                # Measure response time
                response_time = self._measure_response_time()
                if response_time is not None:
                    metrics.append(CacheMetric(
                        metric_type=MetricType.RESPONSE_TIME,
                        value=response_time,
                        timestamp=datetime.utcnow(),
                        unit="ms"
                    ))
                
                # Store metrics
                for metric in metrics:
                    self.metrics[metric.metric_type].append(metric)
                
                # Check thresholds
                self._check_thresholds(metrics)
                
                # Cleanup old metrics
                self._cleanup_old_metrics()
                
                # Wait for next collection
                await asyncio.sleep(self.config.collection_interval)
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(self.config.collection_interval)
        
        logger.info("Cache monitoring stopped")
    
    async def start_monitoring(self):
        """Start cache monitoring"""
        if self._monitoring_active:
            logger.warning("Monitoring is already active")
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Cache monitoring started")
    
    async def stop_monitoring(self):
        """Stop cache monitoring"""
        if not self._monitoring_active:
            return
        
        self._monitoring_active = False
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Cache monitoring stopped")
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current cache metrics"""
        current_metrics = {}
        
        for metric_type in MetricType:
            metrics_list = self.metrics[metric_type]
            if metrics_list:
                latest_metric = metrics_list[-1]
                current_metrics[metric_type.value] = {
                    "value": latest_metric.value,
                    "unit": latest_metric.unit,
                    "timestamp": latest_metric.timestamp.isoformat()
                }
        
        return current_metrics
    
    def get_metric_history(
        self,
        metric_type: MetricType,
        hours: int = 1
    ) -> List[Dict[str, Any]]:
        """Get metric history for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        metrics_list = self.metrics.get(metric_type, [])
        recent_metrics = [
            metric for metric in metrics_list
            if metric.timestamp > cutoff_time
        ]
        
        return [metric.to_dict() for metric in recent_metrics]
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get list of active alerts"""
        return [alert.to_dict() for alert in self.active_alerts if not alert.resolved]
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Resolve an alert by index"""
        if 0 <= alert_id < len(self.active_alerts):
            self.active_alerts[alert_id].resolved = True
            return True
        return False
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall cache health summary"""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()
        
        # Determine overall health status
        critical_alerts = [alert for alert in active_alerts if alert["level"] == "critical"]
        warning_alerts = [alert for alert in active_alerts if alert["level"] == "warning"]
        
        if critical_alerts:
            health_status = "critical"
        elif warning_alerts:
            health_status = "warning"
        else:
            health_status = "healthy"
        
        return {
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics,
            "active_alerts": {
                "total": len(active_alerts),
                "critical": len(critical_alerts),
                "warning": len(warning_alerts)
            },
            "monitoring_active": self._monitoring_active,
            "collection_interval": self.config.collection_interval
        }
    
    def export_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Export metrics for external analysis"""
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "time_range_hours": hours,
            "metrics": {}
        }
        
        for metric_type in MetricType:
            export_data["metrics"][metric_type.value] = self.get_metric_history(metric_type, hours)
        
        export_data["alerts"] = [alert.to_dict() for alert in self.active_alerts]
        
        return export_data


# Default alert callback for logging
def default_alert_callback(alert: CacheAlert):
    """Default alert callback that logs to file"""
    log_message = f"[{alert.timestamp.isoformat()}] {alert.level.value.upper()}: {alert.message}"
    
    # Log to file (create directory if needed)
    import os
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    with open(f"{log_dir}/cache_alerts.log", "a") as f:
        f.write(log_message + "\n")


def create_cache_monitor(redis_client: Optional[redis.Redis] = None) -> CacheMonitor:
    """Create cache monitor with default configuration"""
    monitor = CacheMonitor(redis_client)
    monitor.add_alert_callback(default_alert_callback)
    return monitor