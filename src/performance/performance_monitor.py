#!/usr/bin/env python3
"""
Performance Monitoring and Alerting System
Real-time monitoring for NFL prediction system performance with SLA tracking
"""

import asyncio
import logging
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class MetricType(Enum):
    """Types of metrics to monitor"""
    RESPONSE_TIME = "response_time"
    PREDICTION_COUNT = "prediction_count"
    CACHE_HIT_RATE = "cache_hit_rate"
    ERROR_RATE = "error_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DATABASE_CONNECTIONS = "database_connections"
    CONCURRENT_REQUESTS = "concurrent_requests"


@dataclass
class PerformanceThreshold:
    """Performance threshold definition"""
    metric_type: MetricType
    warning_threshold: float
    critical_threshold: float
    emergency_threshold: Optional[float] = None
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """Performance alert"""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'level': self.level.value,
            'metric_type': self.metric_type.value,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'resolved': self.resolved,
            'resolution_time': self.resolution_time.isoformat() if self.resolution_time else None
        }


@dataclass
class SLATarget:
    """Service Level Agreement target"""
    name: str
    metric_type: MetricType
    target_value: float
    measurement_window_minutes: int
    description: str


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    response_time_ms: float
    prediction_count: int
    cache_hit_rate: float
    error_rate: float
    cpu_usage_percent: float
    memory_usage_percent: float
    database_connections: int
    concurrent_requests: int
    disk_usage_percent: float
    network_latency_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'response_time_ms': self.response_time_ms,
            'prediction_count': self.prediction_count,
            'cache_hit_rate': self.cache_hit_rate,
            'error_rate': self.error_rate,
            'cpu_usage_percent': self.cpu_usage_percent,
            'memory_usage_percent': self.memory_usage_percent,
            'database_connections': self.database_connections,
            'concurrent_requests': self.concurrent_requests,
            'disk_usage_percent': self.disk_usage_percent,
            'network_latency_ms': self.network_latency_ms
        }


class PerformanceMonitor:
    """
    Real-time performance monitoring system

    Features:
    - SLA tracking with 99th percentile metrics
    - Real-time alerting for performance degradation
    - System resource monitoring (CPU, memory, disk)
    - Database connection pool monitoring
    - Cache performance tracking
    - Automated alert escalation
    """

    def __init__(self):
        # Performance thresholds
        self.thresholds = self._define_performance_thresholds()

        # SLA targets
        self.sla_targets = self._define_sla_targets()

        # Monitoring data
        self.metrics_history: List[SystemMetrics] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

        # Monitoring configuration
        self.monitoring_interval_seconds = 30
        self.metrics_retention_hours = 24
        self.max_metrics_history = 2880  # 24 hours at 30-second intervals

        # Alert handlers
        self.alert_handlers: List[Callable[[Alert], None]] = []

        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.alerting_task: Optional[asyncio.Task] = None

        # Current system state
        self.current_metrics: Optional[SystemMetrics] = None
        self.monitoring_active = False

        # Performance counters
        self.request_count = 0
        self.total_response_time = 0.0
        self.error_count = 0
        self.concurrent_requests = 0

        logger.info("🔍 Performance Monitor initialized")

    async def start_monitoring(self):
        """Start performance monitoring"""
        try:
            self.monitoring_active = True

            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            # Start alerting task
            self.alerting_task = asyncio.create_task(self._alerting_loop())

            logger.info("✅ Performance monitoring started")

        except Exception as e:
            logger.error(f"❌ Failed to start performance monitoring: {e}")
            raise

    async def stop_monitoring(self):
        """Stop performance monitoring"""
        try:
            self.monitoring_active = False

            # Cancel monitoring tasks
            for task in [self.monitoring_task, self.alerting_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            logger.info("✅ Performance monitoring stopped")

        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")

    def record_request_metrics(
        self,
        response_time_ms: float,
        prediction_count: int,
        error: bool = False
    ):
        """Record metrics for a prediction request"""
        self.request_count += 1
        self.total_response_time += response_time_ms

        if error:
            self.error_count += 1

        # Update current metrics
        if self.current_metrics:
            self.current_metrics.response_time_ms = response_time_ms
            self.current_metrics.prediction_count += prediction_count

    def start_request(self) -> str:
        """Start tracking a concurrent request"""
        request_id = f"req_{self.request_count}_{int(time.time() * 1000)}"
        self.concurrent_requests += 1
        return request_id

    def end_request(self, request_id: str):
        """End tracking a concurrent request"""
        self.concurrent_requests = max(0, self.concurrent_requests - 1)

    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                self.current_metrics = metrics

                # Store metrics
                self._store_metrics(metrics)

                # Check for threshold violations
                await self._check_thresholds(metrics)

                # Sleep until next monitoring interval
                await asyncio.sleep(self.monitoring_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Brief pause on error

    async def _alerting_loop(self):
        """Alert management loop"""
        while self.monitoring_active:
            try:
                # Check for alert resolution
                await self._check_alert_resolution()

                # Clean up old alerts
                self._cleanup_old_alerts()

                # Sleep until next check
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in alerting loop: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system metrics"""

        # System resource metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Calculate average response time
        avg_response_time = (
            self.total_response_time / max(self.request_count, 1)
        ) if self.request_count > 0 else 0

        # Calculate error rate
        error_rate = (
            self.error_count / max(self.request_count, 1) * 100
        ) if self.request_count > 0 else 0

        # Get cache hit rate (would be injected from cache manager)
        cache_hit_rate = await self._get_cache_hit_rate()

        # Get database connection count
        db_connections = await self._get_database_connections()

        # Network latency (mock for now)
        network_latency = await self._measure_network_latency()

        return SystemMetrics(
            timestamp=datetime.utcnow(),
            response_time_ms=avg_response_time,
            prediction_count=self.request_count,
            cache_hit_rate=cache_hit_rate,
            error_rate=error_rate,
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory.percent,
            database_connections=db_connections,
            concurrent_requests=self.concurrent_requests,
            disk_usage_percent=disk.percent,
            network_latency_ms=network_latency
        )

    async def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate from cache manager"""
        try:
            # This would be injected from the actual cache manager
            # For now, return a mock value
            return 85.0
        except Exception:
            return 0.0

    async def _get_database_connections(self) -> int:
        """Get current database connection count"""
        try:
            # This would be injected from the database optimizer
            # For now, return a mock value
            return 8
        except Exception:
            return 0

    async def _measure_network_latency(self) -> float:
        """Measure network latency"""
        try:
            # Mock network latency measurement
            return 25.0
        except Exception:
            return 0.0

    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics in history"""
        self.metrics_history.append(metrics)

        # Maintain size limit
        if len(self.metrics_history) > self.max_metrics_history:
            # Remove oldest metrics
            excess = len(self.metrics_history) - self.max_metrics_history
            self.metrics_history = self.metrics_history[excess:]

    async def _check_thresholds(self, metrics: SystemMetrics):
        """Check metrics against thresholds and create alerts"""

        checks = [
            (MetricType.RESPONSE_TIME, metrics.response_time_ms),
            (MetricType.ERROR_RATE, metrics.error_rate),
            (MetricType.CPU_USAGE, metrics.cpu_usage_percent),
            (MetricType.MEMORY_USAGE, metrics.memory_usage_percent),
            (MetricType.CACHE_HIT_RATE, 100 - metrics.cache_hit_rate),  # Inverted
            (MetricType.DATABASE_CONNECTIONS, metrics.database_connections),
            (MetricType.CONCURRENT_REQUESTS, metrics.concurrent_requests)
        ]

        for metric_type, current_value in checks:
            threshold = self.thresholds.get(metric_type)
            if not threshold:
                continue

            # Check for threshold violations
            alert_level = None
            threshold_value = None

            if (threshold.emergency_threshold and
                current_value >= threshold.emergency_threshold):
                alert_level = AlertLevel.EMERGENCY
                threshold_value = threshold.emergency_threshold

            elif current_value >= threshold.critical_threshold:
                alert_level = AlertLevel.CRITICAL
                threshold_value = threshold.critical_threshold

            elif current_value >= threshold.warning_threshold:
                alert_level = AlertLevel.WARNING
                threshold_value = threshold.warning_threshold

            # Create alert if threshold violated
            if alert_level:
                await self._create_alert(
                    metric_type, alert_level, current_value, threshold_value
                )

    async def _create_alert(
        self,
        metric_type: MetricType,
        level: AlertLevel,
        current_value: float,
        threshold_value: float
    ):
        """Create and handle a performance alert"""

        alert_id = f"{metric_type.value}_{level.value}_{int(time.time())}"

        # Check if similar alert already exists
        existing_key = f"{metric_type.value}_{level.value}"
        if existing_key in self.active_alerts:
            return  # Don't duplicate alerts

        # Create alert
        alert = Alert(
            alert_id=alert_id,
            level=level,
            metric_type=metric_type,
            current_value=current_value,
            threshold_value=threshold_value,
            message=self._generate_alert_message(
                metric_type, level, current_value, threshold_value
            ),
            timestamp=datetime.utcnow()
        )

        # Store alert
        self.active_alerts[existing_key] = alert
        self.alert_history.append(alert)

        # Trigger alert handlers
        await self._trigger_alert_handlers(alert)

        logger.warning(f"🚨 {level.value.upper()} ALERT: {alert.message}")

    def _generate_alert_message(
        self,
        metric_type: MetricType,
        level: AlertLevel,
        current_value: float,
        threshold_value: float
    ) -> str:
        """Generate human-readable alert message"""

        threshold = self.thresholds.get(metric_type)
        unit = threshold.unit if threshold else ""

        messages = {
            MetricType.RESPONSE_TIME: f"Response time {current_value:.1f}{unit} exceeds threshold {threshold_value:.1f}{unit}",
            MetricType.ERROR_RATE: f"Error rate {current_value:.1f}{unit} exceeds threshold {threshold_value:.1f}{unit}",
            MetricType.CPU_USAGE: f"CPU usage {current_value:.1f}{unit} exceeds threshold {threshold_value:.1f}{unit}",
            MetricType.MEMORY_USAGE: f"Memory usage {current_value:.1f}{unit} exceeds threshold {threshold_value:.1f}{unit}",
            MetricType.CACHE_HIT_RATE: f"Cache miss rate {current_value:.1f}{unit} exceeds threshold {threshold_value:.1f}{unit}",
            MetricType.DATABASE_CONNECTIONS: f"Database connections {current_value:.0f} exceeds threshold {threshold_value:.0f}",
            MetricType.CONCURRENT_REQUESTS: f"Concurrent requests {current_value:.0f} exceeds threshold {threshold_value:.0f}"
        }

        return messages.get(metric_type, f"{metric_type.value} alert: {current_value} > {threshold_value}")

    async def _trigger_alert_handlers(self, alert: Alert):
        """Trigger all registered alert handlers"""
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")

    async def _check_alert_resolution(self):
        """Check if active alerts should be resolved"""
        if not self.current_metrics:
            return

        resolved_alerts = []

        for key, alert in self.active_alerts.items():
            metric_type = alert.metric_type
            threshold = self.thresholds.get(metric_type)

            if not threshold:
                continue

            # Get current value for this metric
            current_value = self._get_current_metric_value(metric_type)

            # Check if alert should be resolved
            should_resolve = False

            if alert.level == AlertLevel.WARNING:
                should_resolve = current_value < threshold.warning_threshold * 0.9
            elif alert.level == AlertLevel.CRITICAL:
                should_resolve = current_value < threshold.critical_threshold * 0.9
            elif alert.level == AlertLevel.EMERGENCY:
                should_resolve = current_value < threshold.emergency_threshold * 0.9

            if should_resolve:
                alert.resolved = True
                alert.resolution_time = datetime.utcnow()
                resolved_alerts.append(key)

                logger.info(f"✅ Alert resolved: {alert.message}")

        # Remove resolved alerts from active list
        for key in resolved_alerts:
            del self.active_alerts[key]

    def _get_current_metric_value(self, metric_type: MetricType) -> float:
        """Get current value for a specific metric type"""
        if not self.current_metrics:
            return 0.0

        value_map = {
            MetricType.RESPONSE_TIME: self.current_metrics.response_time_ms,
            MetricType.ERROR_RATE: self.current_metrics.error_rate,
            MetricType.CPU_USAGE: self.current_metrics.cpu_usage_percent,
            MetricType.MEMORY_USAGE: self.current_metrics.memory_usage_percent,
            MetricType.CACHE_HIT_RATE: 100 - self.current_metrics.cache_hit_rate,
            MetricType.DATABASE_CONNECTIONS: self.current_metrics.database_connections,
            MetricType.CONCURRENT_REQUESTS: self.current_metrics.concurrent_requests
        }

        return value_map.get(metric_type, 0.0)

    def _cleanup_old_alerts(self):
        """Clean up old alert history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]

    def _define_performance_thresholds(self) -> Dict[MetricType, PerformanceThreshold]:
        """Define performance threshold values"""
        return {
            MetricType.RESPONSE_TIME: PerformanceThreshold(
                metric_type=MetricType.RESPONSE_TIME,
                warning_threshold=1000.0,  # 1 second
                critical_threshold=2000.0,  # 2 seconds
                emergency_threshold=5000.0,  # 5 seconds
                unit="ms",
                description="API response time threshold"
            ),

            MetricType.ERROR_RATE: PerformanceThreshold(
                metric_type=MetricType.ERROR_RATE,
                warning_threshold=5.0,   # 5%
                critical_threshold=10.0,  # 10%
                emergency_threshold=25.0, # 25%
                unit="%",
                description="Error rate threshold"
            ),

            MetricType.CPU_USAGE: PerformanceThreshold(
                metric_type=MetricType.CPU_USAGE,
                warning_threshold=70.0,  # 70%
                critical_threshold=85.0, # 85%
                emergency_threshold=95.0, # 95%
                unit="%",
                description="CPU usage threshold"
            ),

            MetricType.MEMORY_USAGE: PerformanceThreshold(
                metric_type=MetricType.MEMORY_USAGE,
                warning_threshold=75.0,  # 75%
                critical_threshold=90.0, # 90%
                emergency_threshold=95.0, # 95%
                unit="%",
                description="Memory usage threshold"
            ),

            MetricType.CACHE_HIT_RATE: PerformanceThreshold(
                metric_type=MetricType.CACHE_HIT_RATE,
                warning_threshold=20.0,  # 20% miss rate
                critical_threshold=40.0, # 40% miss rate
                emergency_threshold=60.0, # 60% miss rate
                unit="% miss",
                description="Cache miss rate threshold"
            ),

            MetricType.DATABASE_CONNECTIONS: PerformanceThreshold(
                metric_type=MetricType.DATABASE_CONNECTIONS,
                warning_threshold=15.0,  # 15 connections
                critical_threshold=18.0, # 18 connections
                emergency_threshold=20.0, # 20 connections (max pool size)
                unit="",
                description="Database connection count threshold"
            ),

            MetricType.CONCURRENT_REQUESTS: PerformanceThreshold(
                metric_type=MetricType.CONCURRENT_REQUESTS,
                warning_threshold=80.0,  # 80 concurrent requests
                critical_threshold=120.0, # 120 concurrent requests
                emergency_threshold=150.0, # 150 concurrent requests
                unit="",
                description="Concurrent request count threshold"
            )
        }

    def _define_sla_targets(self) -> List[SLATarget]:
        """Define SLA targets for monitoring"""
        return [
            SLATarget(
                name="Sub-second Response Time",
                metric_type=MetricType.RESPONSE_TIME,
                target_value=1000.0,  # 1 second
                measurement_window_minutes=60,
                description="99th percentile response time under 1 second"
            ),

            SLATarget(
                name="High Availability",
                metric_type=MetricType.ERROR_RATE,
                target_value=1.0,  # 1% error rate
                measurement_window_minutes=60,
                description="Error rate below 1% over 1 hour"
            ),

            SLATarget(
                name="Cache Performance",
                metric_type=MetricType.CACHE_HIT_RATE,
                target_value=80.0,  # 80% hit rate
                measurement_window_minutes=30,
                description="Cache hit rate above 80% over 30 minutes"
            )
        ]

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add alert handler function"""
        self.alert_handlers.append(handler)

    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status"""
        return {
            'monitoring_active': self.monitoring_active,
            'current_metrics': self.current_metrics.to_dict() if self.current_metrics else None,
            'active_alerts': {k: v.to_dict() for k, v in self.active_alerts.items()},
            'sla_compliance': self._calculate_sla_compliance(),
            'system_health': self._calculate_system_health()
        }

    def get_performance_dashboard(self) -> Dict[str, Any]:
        """Get performance dashboard data"""
        recent_metrics = self.metrics_history[-60:]  # Last 60 data points

        if not recent_metrics:
            return {'no_data': True}

        # Calculate statistics
        response_times = [m.response_time_ms for m in recent_metrics]
        error_rates = [m.error_rate for m in recent_metrics]
        cpu_usage = [m.cpu_usage_percent for m in recent_metrics]
        memory_usage = [m.memory_usage_percent for m in recent_metrics]

        return {
            'timeframe': '30 minutes',
            'data_points': len(recent_metrics),
            'response_time': {
                'current': response_times[-1] if response_times else 0,
                'average': sum(response_times) / len(response_times) if response_times else 0,
                'max': max(response_times) if response_times else 0,
                'p99': self._calculate_percentile(response_times, 99),
                'trend': response_times[-10:] if len(response_times) >= 10 else response_times
            },
            'error_rate': {
                'current': error_rates[-1] if error_rates else 0,
                'average': sum(error_rates) / len(error_rates) if error_rates else 0,
                'trend': error_rates[-10:] if len(error_rates) >= 10 else error_rates
            },
            'system_resources': {
                'cpu_current': cpu_usage[-1] if cpu_usage else 0,
                'memory_current': memory_usage[-1] if memory_usage else 0,
                'cpu_trend': cpu_usage[-10:] if len(cpu_usage) >= 10 else cpu_usage,
                'memory_trend': memory_usage[-10:] if len(memory_usage) >= 10 else memory_usage
            },
            'active_alerts': len(self.active_alerts),
            'sla_compliance': self._calculate_sla_compliance()
        }

    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]

    def _calculate_sla_compliance(self) -> Dict[str, Any]:
        """Calculate SLA compliance metrics"""
        compliance = {}

        for sla in self.sla_targets:
            # Get recent metrics for this SLA window
            window_start = datetime.utcnow() - timedelta(minutes=sla.measurement_window_minutes)
            window_metrics = [
                m for m in self.metrics_history
                if m.timestamp >= window_start
            ]

            if not window_metrics:
                compliance[sla.name] = {'status': 'no_data'}
                continue

            # Calculate compliance based on metric type
            if sla.metric_type == MetricType.RESPONSE_TIME:
                values = [m.response_time_ms for m in window_metrics]
                p99_value = self._calculate_percentile(values, 99)
                is_compliant = p99_value <= sla.target_value

            elif sla.metric_type == MetricType.ERROR_RATE:
                values = [m.error_rate for m in window_metrics]
                avg_value = sum(values) / len(values)
                is_compliant = avg_value <= sla.target_value

            elif sla.metric_type == MetricType.CACHE_HIT_RATE:
                values = [m.cache_hit_rate for m in window_metrics]
                avg_value = sum(values) / len(values)
                is_compliant = avg_value >= sla.target_value

            else:
                is_compliant = True  # Default to compliant for unknown metrics

            compliance[sla.name] = {
                'status': 'compliant' if is_compliant else 'violated',
                'target': sla.target_value,
                'actual': p99_value if sla.metric_type == MetricType.RESPONSE_TIME else avg_value,
                'window_minutes': sla.measurement_window_minutes
            }

        return compliance

    def _calculate_system_health(self) -> str:
        """Calculate overall system health status"""
        if not self.current_metrics:
            return "unknown"

        # Count critical alerts
        critical_alerts = sum(
            1 for alert in self.active_alerts.values()
            if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
        )

        warning_alerts = sum(
            1 for alert in self.active_alerts.values()
            if alert.level == AlertLevel.WARNING
        )

        if critical_alerts > 0:
            return "critical"
        elif warning_alerts > 2:
            return "degraded"
        elif warning_alerts > 0:
            return "warning"
        else:
            return "healthy"


# Global performance monitor instance
performance_monitor = PerformanceMonitor()

async def get_performance_monitor() -> PerformanceMonitor:
    """Get the performance monitor instance"""
    return performance_monitor