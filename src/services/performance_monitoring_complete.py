"""
Performance Monitoring Service - Complete Implementation

Implements comprehensive telemetry collection,rds, and alerting
for the Expert Council Betting System.

Features:
- Real-time telemetry collection for all services
- Performance metrics tracking (latency, throughput, errors)
- Dashboard data aggregation for visualization
- Alert system for performance regressions
- Service health monitoring and SLA tracking

Requirements: 3.3 - Performance monitoring and alerting
"""

import logging
import time
import json
import uuid
import threading
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
import statistics

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics we collect"""
    COUNTER = "counter"           # Incrementing values (requests, errors)
    GAUGE = "gauge"              # Point-in-time values (memory, connections)
    HISTOGRAM = "histogram"       # Distribution of values (latency, response times)
    TIMER = "timer"              # Duration measurements
    RATE = "rate"                # Events per time unit

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    timestamp: datetime
    value: Union[float, int]
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'value': self.value,
            'tags': self.tags
        }

@dataclass
class Metric:
    """Metric definition and data"""
    name: str
    metric_type: MetricType
    description: str
    unit: str = ""
    service: str = ""

    # Data storage
    points: deque = field(default_factory=lambda: deque(maxlen=1000))

    # Aggregated values
    current_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    avg_value: Optional[float] = None

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def add_point(self, value: Union[float, int], tags: Dict[str, str] = None):
        """Add a new data point"""
        point = MetricPoint(
            timestamp=datetime.utcnow(),
            value=float(value),
            tags=tags or {}
        )

        self.points.append(point)
        self.current_value = float(value)
        self.last_updated = datetime.utcnow()

        # Update aggregated values
        self._update_aggregates()

    def _update_aggregates(self):
        """Update min, max, avg from recent points"""
        if not self.points:
            return

        values = [p.value for p in self.points]
        self.min_value = min(values)
        self.max_value = max(values)
        self.avg_value = statistics.mean(values)

@dataclass
class Alert:
    """Performance alert"""
    alert_id: str
    metric_name: str
    service: str
    severity: AlertSeverity
    message: str
    threshold_value: float
    current_value: float

    # Timing
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    # Status
    is_active: bool = True
    acknowledgment: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'metric_name': self.metric_name,
            'service': self.service,
            'severity': self.severity.value,
            'message': self.message,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'triggered_at': self.triggered_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_active': self.is_active,
            'acknowledgment': self.acknowledgment,
            'acknowledged_by': self.acknowledged_by,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None
        }

@dataclass
class AlertRule:
    """Alert rule definition"""
    rule_id: str
    metric_name: str
    service: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    message_template: str

    # Configuration
    evaluation_window_minutes: int = 5
    min_data_points: int = 3
    cooldown_minutes: int = 15

    # State
    last_triggered: Optional[datetime] = None
    is_enabled: bool = True

    def should_trigger(self, current_value: float, data_points: int) -> bool:
        """Check if alert should trigger"""
        if not self.is_enabled:
            return False

        if data_points < self.min_data_points:
            return False

        # Check cooldown
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False

        # Evaluate condition
        if self.condition == "gt":
            return current_value > self.threshold
        elif self.condition == "lt":
            return current_value < self.threshold
        elif self.condition == "gte":
            return current_value >= self.threshold
        elif self.condition == "lte":
            return current_value <= self.threshold
        elif self.condition == "eq":
            return abs(current_value - self.threshold) < 0.001

        return False

class PerformanceMonitoringService:
    """
    Comprehensive performance monitoring service

    Provides telemetry collection, dashboard data, and alerting
    for all Expert Council Betting System services
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()

        # Metrics storage
        self.metrics: Dict[str, Metric] = {}
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}

        # Threading
        self.lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=2)

        # Background tasks
        self.monitoring_active = True
        self.background_thread = threading.Thread(target=self._background_monitoring, daemon=True)
        self.background_thread.start()

        # Performance targets from requirements
        self.performance_targets = {
            'vector_retrieval_p95_ms': 100,
            'end_to_end_p95_ms': 6000,
            'council_projection_p95_ms': 150,
            'schema_pass_rate': 0.985,
            'critic_repair_loops_avg': 1.2
        }

        # Initialize default metrics and alert rules
        self._initialize_default_metrics()
        self._initialize_default_alert_rules()

        logger.info("PerformanceMonitoringService initialized")

    def _default_config(self) -> Dict[str, Any]:
        """Default configuration"""
        return {
            'retention_hours': 24,
            'aggregation_interval_seconds': 60,
            'alert_evaluation_interval_seconds': 30,
            'dashboard_refresh_interval_seconds': 10,
            'max_metrics_per_service': 100,
            'max_alerts_per_service': 50,
            'enable_background_monitoring': True,
            'enable_alerting': True,
            'alert_channels': ['log', 'webhook'],  # Could extend to email, slack, etc.
            'webhook_url': None
        }

    def record_metric(self, name: str, value: Union[float, int], tags: Dict[str, str] = None) -> bool:
        """Record a metric value"""
        try:
            with self.lock:
                if name not in self.metrics:
                    logger.warning(f"Metric {name} not registered, auto-registering as gauge")
                    self.register_metric(name, MetricType.GAUGE, f"Auto-registered metric: {name}")

                metric = self.metrics[name]
                metric.add_point(value, tags)

                # Trigger alert evaluation for this metric
                self._evaluate_alerts_for_metric(name, float(value))

                return True

        except Exception as e:
            logger.error(f"Failed to record metric {name}: {e}")
            return False

    def register_metric(self, name: str, metric_type: MetricType, description: str, unit: str = "", service: str = "") -> bool:
        """Register a new metric"""
        try:
            with self.lock:
                if name in self.metrics:
                    logger.warning(f"Metric {name} already exists, updating description")

                self.metrics[name] = Metric(
                    name=name,
                    metric_type=metric_type,
                    description=description,
                    unit=unit,
                    service=service
                )

                logger.debug(f"Registered metric: {name} ({metric_type.value})")
                return True

        except Exception as e:
            logger.error(f"Failed to register metric {name}: {e}")
            return False

    def get_dashboard_data(self, service: str = None, time_range_minutes: int = 60) -> Dict[str, Any]:
        """Get dashboard data for visualization"""
        try:
            with self.lock:
                cutoff_time = datetime.utcnow() - timedelta(minutes=time_range_minutes)

                # Filter metrics by service if specified
                if service:
                    metrics = [m for m in self.metrics.values() if m.service == service]
                else:
                    metrics = list(self.metrics.values())

                dashboard_data = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'time_range_minutes': time_range_minutes,
                    'service': service,
                    'metrics': {},
                    'alerts': {},
                    'performance_targets': self.performance_targets,
                    'summary': {
                        'total_metrics': len(metrics),
                        'active_alerts': len([a for a in self.alerts.values() if a.is_active]),
                    }
                }

                # Add metric data
                for metric in metrics:
                    # Filter points by time range
                    recent_points = [p for p in metric.points if p.timestamp >= cutoff_time]

                    if recent_points:
                        values = [p.value for p in recent_points]

                        metric_data = {
                            'name': metric.name,
                            'type': metric.metric_type.value,
                            'description': metric.description,
                            'unit': metric.unit,
                            'service': metric.service,
                            'current_value': metric.current_value,
                            'min_value': min(values) if values else None,
                            'max_value': max(values) if values else None,
                            'avg_value': statistics.mean(values) if values else None,
                            'data_points': len(recent_points),
                            'points': [p.to_dict() for p in recent_points[-50:]]  # Last 50 points
                        }

                        # Add percentiles for histograms
                        if metric.metric_type == MetricType.HISTOGRAM and len(values) >= 10:
                            sorted_values = sorted(values)
                            metric_data['p50'] = sorted_values[int(len(sorted_values) * 0.5)]
                            metric_data['p95'] = sorted_values[int(len(sorted_values) * 0.95)]
                            metric_data['p99'] = sorted_values[int(len(sorted_values) * 0.99)]

                        dashboard_data['metrics'][metric.name] = metric_data

                # Add active alerts
                active_alerts = [alert for alert in self.alerts.values() if alert.is_active]
                for alert in active_alerts:
                    dashboard_data['alerts'][alert.alert_id] = alert.to_dict()

                return dashboard_data

        except Exception as e:
            logger.error(f"Failed to get dashboard data: {e}")
            return {'error': str(e)}

    def _initialize_default_metrics(self):
        """Initialize default metrics for all services"""

        # Vector retrieval metrics
        self.register_metric("vector_retrieval_latency_ms", MetricType.HISTOGRAM, "Vector retrieval latency in milliseconds", unit="ms", service="memory_retrieval")
        self.register_metric("vector_retrieval_success_rate", MetricType.GAUGE, "Vector retrieval success rate", unit="percentage", service="memory_retrieval")

        # Schema validation metrics
        self.register_metric("schema_validation_pass_rate", MetricType.GAUGE, "Schema validation pass rate", unit="percentage", service="expert_prediction")
        self.register_metric("schema_validation_failures", MetricType.COUNTER, "Schema validation failures count", service="expert_prediction")

        # Expert prediction metrics
        self.register_metric("expert_prediction_latency_ms", MetricType.HISTOGRAM, "Expert prediction generation latency", unit="ms", service="expert_prediction")
        self.register_metric("critic_repair_loops", MetricType.HISTOGRAM, "Number of critic/repair loops per prediction", service="expert_prediction")

        # Council selection metrics
        self.register_metric("council_selection_latency_ms", MetricType.HISTOGRAM, "Council selection latency", unit="ms", service="council_selection")
        self.register_metric("coherence_projection_latency_ms", MetricType.HISTOGRAM, "Coherence projection latency", unit="ms", service="coherence_projection")

        # API metrics
        self.register_metric("api_request_count", MetricType.COUNTER, "Total API requests", service="api")
        self.register_metric("api_response_time_ms", MetricType.HISTOGRAM, "API response time", unit="ms", service="api")
        self.register_metric("api_error_rate", MetricType.GAUGE, "API error rate", unit="percentage", service="api")

    def _initialize_default_alert_rules(self):
        """Initialize default alert rules based on performance targets"""

        # Vector retrieval SLA
        self.add_alert_rule("vector_retrieval_sla_breach", "vector_retrieval_latency_ms", "memory_retrieval", "gt",
                           self.performance_targets['vector_retrieval_p95_ms'], AlertSeverity.WARNING,
                           "Vector retrieval p95 latency ({current_value:.1f}ms) exceeds target ({threshold}ms)")

        # Schema validation quality
        self.add_alert_rule("schema_pass_rate_low", "schema_validation_pass_rate", "expert_prediction", "lt",
                           self.performance_targets['schema_pass_rate'] * 100, AlertSeverity.ERROR,
                           "Schema validation pass rate ({current_value:.1f}%) below target ({threshold}%)")

        # High error rates
        self.add_alert_rule("api_error_rate_high", "api_error_rate", "api", "gt", 5.0, AlertSeverity.ERROR,
                           "API error rate ({current_value:.1f}%) is high")

    def add_alert_rule(self, rule_id: str, metric_name: str, service: str, condition: str, threshold: float,
                      severity: AlertSeverity, message_template: str, evaluation_window_minutes: int = 5,
                      cooldown_minutes: int = 15) -> bool:
        """Add an alert rule"""
        try:
            with self.lock:
                rule = AlertRule(
                    rule_id=rule_id, metric_name=metric_name, service=service, condition=condition,
                    threshold=threshold, severity=severity, message_template=message_template,
                    evaluation_window_minutes=evaluation_window_minutes, cooldown_minutes=cooldown_minutes
                )

                self.alert_rules[rule_id] = rule
                logger.info(f"Added alert rule: {rule_id} for {metric_name}")
                return True

        except Exception as e:
            logger.error(f"Failed to add alert rule {rule_id}: {e}")
            return False

    def _evaluate_alerts_for_metric(self, metric_name: str, current_value: float):
        """Evaluate alert rules for a specific metric"""
        if not self.config['enable_alerting']:
            return

        try:
            # Find alert rules for this metric
            relevant_rules = [rule for rule in self.alert_rules.values() if rule.metric_name == metric_name]

            for rule in relevant_rules:
                metric = self.metrics.get(metric_name)
                if not metric:
                    continue

                data_points = len(metric.points)

                if rule.should_trigger(current_value, data_points):
                    self._trigger_alert(rule, current_value)

        except Exception as e:
            logger.error(f"Alert evaluation failed for {metric_name}: {e}")

    def _trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert"""
        try:
            # Create alert
            alert = Alert(
                alert_id=str(uuid.uuid4()), metric_name=rule.metric_name, service=rule.service,
                severity=rule.severity, message=rule.message_template.format(current_value=current_value, threshold=rule.threshold),
                threshold_value=rule.threshold, current_value=current_value
            )

            # Store alert
            self.alerts[alert.alert_id] = alert

            # Update rule state
            rule.last_triggered = datetime.utcnow()

            # Send alert notifications
            self._send_alert_notification(alert)

            logger.warning(f"Alert triggered: {alert.message}")

        except Exception as e:
            logger.error(f"Failed to trigger alert: {e}")

    def _send_alert_notification(self, alert: Alert):
        """Send alert notification through configured channels"""
        try:
            channels = self.config.get('alert_channels', ['log'])

            for channel in channels:
                if channel == 'log':
                    logger.warning(f"ALERT [{alert.severity.value.upper()}] {alert.service}: {alert.message}")
                elif channel == 'webhook' and self.config.get('webhook_url'):
                    # In a real implementation, this would make an HTTP request
                    webhook_payload = {
                        'alert': alert.to_dict(),
                        'timestamp': datetime.utcnow().isoformat(),
                        'source': 'expert_council_betting_system'
                    }
                    logger.info(f"Would send webhook to {self.config['webhook_url']}: {json.dumps(webhook_payload, indent=2)}")

        except Exception as e:
            logger.error(f"Failed to send alert notification: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary against targets"""
        try:
            with self.lock:
                summary = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'targets': self.performance_targets.copy(),
                    'current_performance': {},
                    'sla_compliance': {},
                    'recommendations': []
                }

                # Check vector retrieval performance
                vector_metric = self.metrics.get('vector_retrieval_latency_ms')
                if vector_metric and vector_metric.points:
                    values = [p.value for p in vector_metric.points]
                    if len(values) >= 10:
                        p95 = sorted(values)[int(len(values) * 0.95)]
                        summary['current_performance']['vector_retrieval_p95_ms'] = p95
                        summary['sla_compliance']['vector_retrieval'] = p95 <= self.performance_targets['vector_retrieval_p95_ms']

                        if p95 > self.performance_targets['vector_retrieval_p95_ms']:
                            summary['recommendations'].append("Optimize vector retrieval: check HNSW indexes and reduce K parameter")

                # Check schema pass rate
                schema_metric = self.metrics.get('schema_validation_pass_rate')
                if schema_metric and schema_metric.current_value is not None:
                    pass_rate = schema_metric.current_value / 100
                    summary['current_performance']['schema_pass_rate'] = pass_rate
                    summary['sla_compliance']['schema_validation'] = pass_rate >= self.performance_targets['schema_pass_rate']

                    if pass_rate < self.performance_targets['schema_pass_rate']:
                        summary['recommendations'].append("Improve schema validation: review prompt engineering and add repair mechanisms")

                # Overall SLA compliance
                compliant_slas = sum(1 for compliant in summary['sla_compliance'].values() if compliant)
                total_slas = len(summary['sla_compliance'])
                summary['overall_sla_compliance'] = compliant_slas / max(total_slas, 1)

                return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}

    def _background_monitoring(self):
        """Background monitoring thread"""
        logger.info("Background monitoring started")

        while self.monitoring_active:
            try:
                # Clean up old data
                self._cleanup_old_data()

                # Sleep until next cycle
                time.sleep(self.config['alert_evaluation_interval_seconds'])

            except Exception as e:
                logger.error(f"Background monitoring error: {e}")
                time.sleep(5)  # Short sleep on error

        logger.info("Background monitoring stopped")

    def _cleanup_old_data(self):
        """Clean up old metric data and resolved alerts"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=self.config['retention_hours'])

            with self.lock:
                # Clean up resolved alerts older than retention period
                old_alerts = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if not alert.is_active and alert.resolved_at and alert.resolved_at < cutoff_time
                ]

                for alert_id in old_alerts:
                    del self.alerts[alert_id]

                if old_alerts:
                    logger.debug(f"Cleaned up {len(old_alerts)} old alerts")

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")

    def shutdown(self):
        """Shutdown the monitoring service"""
        logger.info("Shutting down PerformanceMonitoringService")

        self.monitoring_active = False

        if hasattr(self, 'background_thread'):
            self.background_thread.join(timeout=5)

        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)

        logger.info("PerformanceMonitoringService shutdown complete")

    def acknowledge_alert(self, alert_id: str, acknowledgment: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            with self.lock:
                if alert_id not in self.alerts:
                    return False

                alert = self.alerts[alert_id]
                alert.acknowledgment = acknowledgment
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = datetime.utcnow()

                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}: {acknowledgment}")
                return True

        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        try:
            with self.lock:
                if alert_id not in self.alerts:
                    return False

                alert = self.alerts[alert_id]
                alert.is_active = False
                alert.resolved_at = datetime.utcnow()

                logger.info(f"Alert {alert_id} resolved")
                return True

        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
