"""
Performance Monitoring Dashboard
Real-time metrics collection, analysis, and alerting system for NFL Predictor API
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import aiohttp
import psutil
import numpy as np
from prometheus_client import (
    Counter, Histogram, Gauge, Info, start_http_server,
    CollectorRegistry, push_to_gateway
)
from prometheus_client.exposition import generate_latest
import redis
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import websocket
from threading import Thread
import queue


class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class MetricSnapshot:
    timestamp: datetime
    api_response_time: float
    prediction_accuracy: float
    cache_hit_rate: float
    model_performance: Dict[str, float]
    data_source_availability: Dict[str, bool]
    websocket_connections: int
    system_cpu: float
    system_memory: float
    database_connections: int
    error_rate: float


@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: AlertSeverity
    metric: str
    threshold: float
    current_value: float
    message: str
    resolved: bool = False


class PrometheusMetrics:
    """Prometheus metrics collection"""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()

        # API Metrics
        self.api_requests = Counter(
            'nfl_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.api_duration = Histogram(
            'nfl_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # ML Model Metrics
        self.prediction_accuracy = Gauge(
            'nfl_prediction_accuracy',
            'Current prediction accuracy',
            ['model_type'],
            registry=self.registry
        )

        self.model_training_time = Gauge(
            'nfl_model_training_duration_seconds',
            'Time taken to train models',
            ['model_type'],
            registry=self.registry
        )

        # Cache Metrics
        self.cache_hit_rate = Gauge(
            'nfl_cache_hit_rate',
            'Cache hit rate percentage',
            registry=self.registry
        )

        self.cache_size = Gauge(
            'nfl_cache_size_bytes',
            'Current cache size in bytes',
            registry=self.registry
        )

        # Data Source Metrics
        self.data_source_status = Gauge(
            'nfl_data_source_available',
            'Data source availability',
            ['source'],
            registry=self.registry
        )

        self.data_freshness = Gauge(
            'nfl_data_freshness_seconds',
            'Time since last data update',
            ['source'],
            registry=self.registry
        )

        # WebSocket Metrics
        self.websocket_connections = Gauge(
            'nfl_websocket_connections',
            'Current WebSocket connections',
            registry=self.registry
        )

        self.websocket_messages = Counter(
            'nfl_websocket_messages_total',
            'Total WebSocket messages',
            ['type'],
            registry=self.registry
        )

        # System Metrics
        self.system_cpu = Gauge(
            'nfl_system_cpu_percent',
            'System CPU usage',
            registry=self.registry
        )

        self.system_memory = Gauge(
            'nfl_system_memory_percent',
            'System memory usage',
            registry=self.registry
        )

        self.database_connections = Gauge(
            'nfl_database_connections',
            'Active database connections',
            registry=self.registry
        )


class PerformanceDashboard:
    """Main performance monitoring dashboard"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics = PrometheusMetrics()
        self.redis_client = redis.Redis(
            host=config.get('redis_host', 'localhost'),
            port=config.get('redis_port', 6379),
            db=config.get('redis_db', 0)
        )

        # Database connection
        self.db_engine = create_engine(config['database_url'])

        # Alert system
        self.alerts: List[Alert] = []
        self.alert_thresholds = config.get('alert_thresholds', {})

        # Historical data storage
        self.metrics_history: List[MetricSnapshot] = []
        self.max_history_size = config.get('max_history_size', 10000)

        # WebSocket monitoring
        self.ws_connections = set()
        self.ws_message_queue = queue.Queue()

        # Performance tracking
        self.sla_targets = config.get('sla_targets', {
            'api_response_time': 200,  # ms
            'prediction_accuracy': 0.75,
            'uptime': 0.999,
            'cache_hit_rate': 0.8
        })

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    async def start_monitoring(self):
        """Start the monitoring system"""
        self.logger.info("Starting performance monitoring dashboard")

        # Start Prometheus metrics server
        start_http_server(self.config.get('prometheus_port', 8000))

        # Start monitoring tasks
        tasks = [
            self._collect_metrics_loop(),
            self._check_alerts_loop(),
            self._cleanup_history_loop(),
            self._generate_reports_loop()
        ]

        await asyncio.gather(*tasks)

    async def _collect_metrics_loop(self):
        """Main metrics collection loop"""
        while True:
            try:
                snapshot = await self.collect_metrics()
                self.metrics_history.append(snapshot)
                await self._update_prometheus_metrics(snapshot)
                await self._store_metrics_redis(snapshot)

            except Exception as e:
                self.logger.error(f"Error collecting metrics: {e}")

            await asyncio.sleep(self.config.get('collection_interval', 30))

    async def collect_metrics(self) -> MetricSnapshot:
        """Collect all performance metrics"""
        timestamp = datetime.utcnow()

        # Collect API metrics
        api_response_time = await self._measure_api_response_time()

        # Collect ML model metrics
        prediction_accuracy = await self._get_prediction_accuracy()
        model_performance = await self._get_model_performance()

        # Collect cache metrics
        cache_hit_rate = await self._get_cache_hit_rate()

        # Collect data source availability
        data_source_availability = await self._check_data_sources()

        # Collect WebSocket metrics
        websocket_connections = len(self.ws_connections)

        # Collect system metrics
        system_cpu = psutil.cpu_percent()
        system_memory = psutil.virtual_memory().percent

        # Collect database metrics
        database_connections = await self._get_database_connections()

        # Calculate error rate
        error_rate = await self._calculate_error_rate()

        return MetricSnapshot(
            timestamp=timestamp,
            api_response_time=api_response_time,
            prediction_accuracy=prediction_accuracy,
            cache_hit_rate=cache_hit_rate,
            model_performance=model_performance,
            data_source_availability=data_source_availability,
            websocket_connections=websocket_connections,
            system_cpu=system_cpu,
            system_memory=system_memory,
            database_connections=database_connections,
            error_rate=error_rate
        )

    async def _measure_api_response_time(self) -> float:
        """Measure API response time"""
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config['api_base_url']}/health"
                ) as response:
                    await response.text()
            return (time.time() - start_time) * 1000  # Convert to ms
        except Exception as e:
            self.logger.error(f"API health check failed: {e}")
            return float('inf')

    async def _get_prediction_accuracy(self) -> float:
        """Get current prediction accuracy from database"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT AVG(CASE WHEN actual_result = predicted_result THEN 1.0 ELSE 0.0 END) as accuracy
                    FROM predictions
                    WHERE created_at >= NOW() - INTERVAL '24 HOURS'
                    AND actual_result IS NOT NULL
                """))
                row = result.fetchone()
                return float(row[0]) if row and row[0] else 0.0
        except Exception as e:
            self.logger.error(f"Error getting prediction accuracy: {e}")
            return 0.0

    async def _get_model_performance(self) -> Dict[str, float]:
        """Get performance metrics for each ML model"""
        models = ['enhanced_ensemble', 'xgboost', 'neural_network']
        performance = {}

        for model in models:
            try:
                with self.db_engine.connect() as conn:
                    result = conn.execute(text("""
                        SELECT AVG(confidence_score) as avg_confidence,
                               COUNT(*) as prediction_count
                        FROM predictions
                        WHERE model_name = :model
                        AND created_at >= NOW() - INTERVAL '1 HOUR'
                    """), {"model": model})
                    row = result.fetchone()
                    if row and row[0]:
                        performance[model] = {
                            'avg_confidence': float(row[0]),
                            'prediction_count': int(row[1])
                        }
            except Exception as e:
                self.logger.error(f"Error getting {model} performance: {e}")
                performance[model] = {'avg_confidence': 0.0, 'prediction_count': 0}

        return performance

    async def _get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        try:
            info = self.redis_client.info()
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            return (hits / total) if total > 0 else 0.0
        except Exception as e:
            self.logger.error(f"Error getting cache hit rate: {e}")
            return 0.0

    async def _check_data_sources(self) -> Dict[str, bool]:
        """Check availability of external data sources"""
        sources = {
            'espn_api': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard',
            'nfl_api': 'https://api.nfl.com/v1/reroute?_query=query%7Bviewer%7Bleague%7Bseasons%28first%3A1%29%7Bedges%7Bnode%7Bvalue%7D%7D%7D%7D%7D%7D',
            'database': 'internal'
        }

        availability = {}

        for source, url in sources.items():
            if source == 'database':
                try:
                    with self.db_engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    availability[source] = True
                except Exception:
                    availability[source] = False
            else:
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                        async with session.get(url) as response:
                            availability[source] = response.status == 200
                except Exception:
                    availability[source] = False

        return availability

    async def _get_database_connections(self) -> int:
        """Get current database connection count"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM pg_stat_activity
                    WHERE state = 'active' AND datname = current_database()
                """))
                row = result.fetchone()
                return int(row[0]) if row else 0
        except Exception as e:
            self.logger.error(f"Error getting database connections: {e}")
            return 0

    async def _calculate_error_rate(self) -> float:
        """Calculate current error rate from logs"""
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT
                        COUNT(CASE WHEN status_code >= 400 THEN 1 END)::float /
                        COUNT(*)::float as error_rate
                    FROM api_logs
                    WHERE created_at >= NOW() - INTERVAL '1 HOUR'
                """))
                row = result.fetchone()
                return float(row[0]) if row and row[0] else 0.0
        except Exception as e:
            self.logger.error(f"Error calculating error rate: {e}")
            return 0.0

    async def _update_prometheus_metrics(self, snapshot: MetricSnapshot):
        """Update Prometheus metrics"""
        # Update gauges
        self.metrics.prediction_accuracy.labels(model_type='overall').set(snapshot.prediction_accuracy)
        self.metrics.cache_hit_rate.set(snapshot.cache_hit_rate)
        self.metrics.websocket_connections.set(snapshot.websocket_connections)
        self.metrics.system_cpu.set(snapshot.system_cpu)
        self.metrics.system_memory.set(snapshot.system_memory)
        self.metrics.database_connections.set(snapshot.database_connections)

        # Update data source availability
        for source, available in snapshot.data_source_availability.items():
            self.metrics.data_source_status.labels(source=source).set(1 if available else 0)

        # Update model performance
        for model, perf in snapshot.model_performance.items():
            if isinstance(perf, dict) and 'avg_confidence' in perf:
                self.metrics.prediction_accuracy.labels(model_type=model).set(perf['avg_confidence'])

    async def _store_metrics_redis(self, snapshot: MetricSnapshot):
        """Store metrics in Redis for quick access"""
        try:
            data = asdict(snapshot)
            data['timestamp'] = snapshot.timestamp.isoformat()
            self.redis_client.lpush('metrics_history', json.dumps(data, default=str))
            self.redis_client.ltrim('metrics_history', 0, self.max_history_size - 1)
        except Exception as e:
            self.logger.error(f"Error storing metrics in Redis: {e}")

    async def _check_alerts_loop(self):
        """Monitor for alert conditions"""
        while True:
            try:
                if self.metrics_history:
                    latest = self.metrics_history[-1]
                    await self._check_alert_conditions(latest)
            except Exception as e:
                self.logger.error(f"Error checking alerts: {e}")

            await asyncio.sleep(self.config.get('alert_check_interval', 60))

    async def _check_alert_conditions(self, snapshot: MetricSnapshot):
        """Check if any metrics breach alert thresholds"""
        checks = [
            ('api_response_time', snapshot.api_response_time, self.alert_thresholds.get('api_response_time', 1000)),
            ('prediction_accuracy', snapshot.prediction_accuracy, self.alert_thresholds.get('prediction_accuracy', 0.5)),
            ('cache_hit_rate', snapshot.cache_hit_rate, self.alert_thresholds.get('cache_hit_rate', 0.3)),
            ('system_cpu', snapshot.system_cpu, self.alert_thresholds.get('system_cpu', 80)),
            ('system_memory', snapshot.system_memory, self.alert_thresholds.get('system_memory', 85)),
            ('error_rate', snapshot.error_rate, self.alert_thresholds.get('error_rate', 0.1))
        ]

        for metric, value, threshold in checks:
            if self._should_alert(metric, value, threshold):
                alert = Alert(
                    id=f"{metric}_{snapshot.timestamp.strftime('%Y%m%d_%H%M%S')}",
                    timestamp=snapshot.timestamp,
                    severity=self._get_alert_severity(metric, value, threshold),
                    metric=metric,
                    threshold=threshold,
                    current_value=value,
                    message=f"{metric} is {value}, threshold is {threshold}"
                )

                self.alerts.append(alert)
                await self._send_alert(alert)

    def _should_alert(self, metric: str, value: float, threshold: float) -> bool:
        """Determine if an alert should be triggered"""
        if metric in ['prediction_accuracy', 'cache_hit_rate']:
            return value < threshold  # Lower is worse
        else:
            return value > threshold  # Higher is worse

    def _get_alert_severity(self, metric: str, value: float, threshold: float) -> AlertSeverity:
        """Determine alert severity based on how much threshold is breached"""
        if metric in ['prediction_accuracy', 'cache_hit_rate']:
            ratio = value / threshold
            if ratio < 0.5:
                return AlertSeverity.CRITICAL
            elif ratio < 0.7:
                return AlertSeverity.HIGH
            elif ratio < 0.9:
                return AlertSeverity.MEDIUM
            else:
                return AlertSeverity.LOW
        else:
            ratio = value / threshold
            if ratio > 2.0:
                return AlertSeverity.CRITICAL
            elif ratio > 1.5:
                return AlertSeverity.HIGH
            elif ratio > 1.2:
                return AlertSeverity.MEDIUM
            else:
                return AlertSeverity.LOW

    async def _send_alert(self, alert: Alert):
        """Send alert notification"""
        try:
            # Log alert
            self.logger.warning(f"ALERT [{alert.severity.value.upper()}]: {alert.message}")

            # Send email if configured
            if self.config.get('email_alerts'):
                await self._send_email_alert(alert)

            # Send Slack notification if configured
            if self.config.get('slack_webhook'):
                await self._send_slack_alert(alert)

        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")

    async def _send_email_alert(self, alert: Alert):
        """Send email alert notification"""
        smtp_config = self.config.get('smtp', {})
        if not smtp_config:
            return

        msg = MimeMultipart()
        msg['From'] = smtp_config['from_email']
        msg['To'] = ', '.join(smtp_config['to_emails'])
        msg['Subject'] = f"NFL Predictor Alert: {alert.severity.value.upper()} - {alert.metric}"

        body = f"""
        Alert Details:
        - Metric: {alert.metric}
        - Current Value: {alert.current_value}
        - Threshold: {alert.threshold}
        - Severity: {alert.severity.value}
        - Time: {alert.timestamp}
        - Message: {alert.message}
        """

        msg.attach(MimeText(body, 'plain'))

        try:
            server = smtplib.SMTP(smtp_config['host'], smtp_config['port'])
            if smtp_config.get('use_tls'):
                server.starttls()
            if smtp_config.get('username'):
                server.login(smtp_config['username'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
        except Exception as e:
            self.logger.error(f"Error sending email alert: {e}")

    async def _send_slack_alert(self, alert: Alert):
        """Send Slack alert notification"""
        webhook_url = self.config.get('slack_webhook')
        if not webhook_url:
            return

        color_map = {
            AlertSeverity.LOW: "#36a64f",
            AlertSeverity.MEDIUM: "#ff9500",
            AlertSeverity.HIGH: "#ff0000",
            AlertSeverity.CRITICAL: "#8b0000"
        }

        payload = {
            "attachments": [{
                "color": color_map[alert.severity],
                "title": f"NFL Predictor Alert - {alert.severity.value.upper()}",
                "fields": [
                    {"title": "Metric", "value": alert.metric, "short": True},
                    {"title": "Current Value", "value": str(alert.current_value), "short": True},
                    {"title": "Threshold", "value": str(alert.threshold), "short": True},
                    {"title": "Time", "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": True}
                ],
                "text": alert.message
            }]
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status != 200:
                        self.logger.error(f"Slack notification failed: {response.status}")
        except Exception as e:
            self.logger.error(f"Error sending Slack alert: {e}")

    async def _cleanup_history_loop(self):
        """Clean up old historical data"""
        while True:
            try:
                # Keep only recent history in memory
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]

                # Clean up resolved alerts older than 24 hours
                cutoff = datetime.utcnow() - timedelta(hours=24)
                self.alerts = [
                    alert for alert in self.alerts
                    if not alert.resolved or alert.timestamp > cutoff
                ]

            except Exception as e:
                self.logger.error(f"Error during cleanup: {e}")

            await asyncio.sleep(3600)  # Run every hour

    async def _generate_reports_loop(self):
        """Generate automated performance reports"""
        while True:
            try:
                # Generate daily report
                if datetime.utcnow().hour == 6:  # 6 AM UTC
                    await self._generate_daily_report()

                # Generate weekly report
                if datetime.utcnow().weekday() == 0 and datetime.utcnow().hour == 8:  # Monday 8 AM UTC
                    await self._generate_weekly_report()

            except Exception as e:
                self.logger.error(f"Error generating reports: {e}")

            await asyncio.sleep(3600)  # Check every hour

    async def _generate_daily_report(self):
        """Generate daily performance report"""
        if not self.metrics_history:
            return

        # Get last 24 hours of data
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]

        if not recent_metrics:
            return

        report = self._create_performance_report(recent_metrics, "Daily")

        # Store report in Redis
        self.redis_client.setex(
            'daily_report',
            86400,  # 24 hours
            json.dumps(report, default=str, cls=PlotlyJSONEncoder)
        )

        self.logger.info("Generated daily performance report")

    async def _generate_weekly_report(self):
        """Generate weekly performance report"""
        if not self.metrics_history:
            return

        # Get last 7 days of data
        cutoff = datetime.utcnow() - timedelta(days=7)
        weekly_metrics = [m for m in self.metrics_history if m.timestamp > cutoff]

        if not weekly_metrics:
            return

        report = self._create_performance_report(weekly_metrics, "Weekly")

        # Store report in Redis
        self.redis_client.setex(
            'weekly_report',
            604800,  # 7 days
            json.dumps(report, default=str, cls=PlotlyJSONEncoder)
        )

        self.logger.info("Generated weekly performance report")

    def _create_performance_report(self, metrics: List[MetricSnapshot], period: str) -> Dict[str, Any]:
        """Create performance report from metrics data"""
        df = pd.DataFrame([asdict(m) for m in metrics])

        # Calculate SLA compliance
        sla_compliance = {}
        for metric, target in self.sla_targets.items():
            if metric in df.columns:
                if metric in ['prediction_accuracy', 'cache_hit_rate']:
                    compliance = (df[metric] >= target).mean()
                else:
                    compliance = (df[metric] <= target).mean()
                sla_compliance[metric] = compliance

        # Calculate averages and trends
        averages = {}
        trends = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            if col != 'timestamp':
                averages[col] = df[col].mean()
                # Simple trend calculation (correlation with time)
                time_numeric = pd.to_numeric(pd.to_datetime(df['timestamp']))
                trends[col] = np.corrcoef(time_numeric, df[col])[0, 1] if len(df) > 1 else 0

        # Create charts
        charts = self._create_performance_charts(df)

        return {
            'period': period,
            'start_time': metrics[0].timestamp.isoformat(),
            'end_time': metrics[-1].timestamp.isoformat(),
            'sla_compliance': sla_compliance,
            'averages': averages,
            'trends': trends,
            'charts': charts,
            'total_alerts': len([a for a in self.alerts if a.timestamp >= metrics[0].timestamp]),
            'critical_alerts': len([a for a in self.alerts
                                   if a.timestamp >= metrics[0].timestamp and a.severity == AlertSeverity.CRITICAL])
        }

    def _create_performance_charts(self, df: pd.DataFrame) -> Dict[str, str]:
        """Create performance charts as JSON"""
        charts = {}

        # API Response Time Chart
        fig = px.line(df, x='timestamp', y='api_response_time',
                     title='API Response Time Over Time')
        fig.add_hline(y=self.sla_targets.get('api_response_time', 200),
                     line_dash="dash", annotation_text="SLA Target")
        charts['api_response_time'] = fig.to_json()

        # Prediction Accuracy Chart
        fig = px.line(df, x='timestamp', y='prediction_accuracy',
                     title='Prediction Accuracy Over Time')
        fig.add_hline(y=self.sla_targets.get('prediction_accuracy', 0.75),
                     line_dash="dash", annotation_text="SLA Target")
        charts['prediction_accuracy'] = fig.to_json()

        # Cache Hit Rate Chart
        fig = px.line(df, x='timestamp', y='cache_hit_rate',
                     title='Cache Hit Rate Over Time')
        fig.add_hline(y=self.sla_targets.get('cache_hit_rate', 0.8),
                     line_dash="dash", annotation_text="SLA Target")
        charts['cache_hit_rate'] = fig.to_json()

        # System Resource Usage
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['system_cpu'],
                                mode='lines', name='CPU %'))
        fig.add_trace(go.Scatter(x=df['timestamp'], y=df['system_memory'],
                                mode='lines', name='Memory %'))
        fig.update_layout(title='System Resource Usage',
                         xaxis_title='Time', yaxis_title='Usage %')
        charts['system_resources'] = fig.to_json()

        return charts

    def get_current_status(self) -> Dict[str, Any]:
        """Get current system status for API endpoints"""
        if not self.metrics_history:
            return {"status": "No data available"}

        latest = self.metrics_history[-1]

        # Calculate overall health score
        health_score = self._calculate_health_score(latest)

        # Get recent alerts
        recent_alerts = [a for a in self.alerts
                        if a.timestamp > datetime.utcnow() - timedelta(hours=1)]

        return {
            "timestamp": latest.timestamp.isoformat(),
            "health_score": health_score,
            "status": "healthy" if health_score > 0.8 else "degraded" if health_score > 0.5 else "unhealthy",
            "metrics": {
                "api_response_time": latest.api_response_time,
                "prediction_accuracy": latest.prediction_accuracy,
                "cache_hit_rate": latest.cache_hit_rate,
                "websocket_connections": latest.websocket_connections,
                "system_cpu": latest.system_cpu,
                "system_memory": latest.system_memory,
                "error_rate": latest.error_rate
            },
            "data_sources": latest.data_source_availability,
            "recent_alerts": len(recent_alerts),
            "sla_compliance": self._get_current_sla_compliance()
        }

    def _calculate_health_score(self, snapshot: MetricSnapshot) -> float:
        """Calculate overall system health score (0-1)"""
        scores = []

        # API response time score
        if snapshot.api_response_time < 200:
            scores.append(1.0)
        elif snapshot.api_response_time < 500:
            scores.append(0.8)
        elif snapshot.api_response_time < 1000:
            scores.append(0.5)
        else:
            scores.append(0.2)

        # Prediction accuracy score
        scores.append(min(snapshot.prediction_accuracy * 1.2, 1.0))

        # Cache hit rate score
        scores.append(min(snapshot.cache_hit_rate * 1.1, 1.0))

        # System resource scores
        cpu_score = max(0, 1 - (snapshot.system_cpu / 100))
        memory_score = max(0, 1 - (snapshot.system_memory / 100))
        scores.extend([cpu_score, memory_score])

        # Data source availability score
        available_sources = sum(snapshot.data_source_availability.values())
        total_sources = len(snapshot.data_source_availability)
        availability_score = available_sources / total_sources if total_sources > 0 else 0
        scores.append(availability_score)

        # Error rate score
        error_score = max(0, 1 - (snapshot.error_rate * 10))
        scores.append(error_score)

        return sum(scores) / len(scores)

    def _get_current_sla_compliance(self) -> Dict[str, float]:
        """Get current SLA compliance percentages"""
        if len(self.metrics_history) < 10:
            return {}

        # Use last 24 hours or available data
        recent_count = min(len(self.metrics_history), 2880)  # 24h at 30s intervals
        recent_metrics = self.metrics_history[-recent_count:]

        compliance = {}
        for metric, target in self.sla_targets.items():
            values = []
            for snapshot in recent_metrics:
                if hasattr(snapshot, metric):
                    values.append(getattr(snapshot, metric))

            if values:
                if metric in ['prediction_accuracy', 'cache_hit_rate']:
                    compliance[metric] = sum(1 for v in values if v >= target) / len(values)
                else:
                    compliance[metric] = sum(1 for v in values if v <= target) / len(values)

        return compliance


# Configuration helper
def create_dashboard_config() -> Dict[str, Any]:
    """Create default dashboard configuration"""
    return {
        'database_url': 'postgresql://user:password@localhost/nfl_predictor',
        'redis_host': 'localhost',
        'redis_port': 6379,
        'redis_db': 0,
        'api_base_url': 'http://localhost:8080',
        'prometheus_port': 8000,
        'collection_interval': 30,  # seconds
        'alert_check_interval': 60,  # seconds
        'max_history_size': 10000,
        'alert_thresholds': {
            'api_response_time': 1000,  # ms
            'prediction_accuracy': 0.6,
            'cache_hit_rate': 0.5,
            'system_cpu': 80,
            'system_memory': 85,
            'error_rate': 0.1
        },
        'sla_targets': {
            'api_response_time': 200,
            'prediction_accuracy': 0.75,
            'uptime': 0.999,
            'cache_hit_rate': 0.8
        },
        'email_alerts': True,
        'smtp': {
            'host': 'smtp.gmail.com',
            'port': 587,
            'use_tls': True,
            'username': 'alerts@nflpredictor.com',
            'password': 'app_password',
            'from_email': 'alerts@nflpredictor.com',
            'to_emails': ['admin@nflpredictor.com']
        },
        'slack_webhook': 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    }


# Main execution
if __name__ == "__main__":
    config = create_dashboard_config()
    dashboard = PerformanceDashboard(config)

    try:
        asyncio.run(dashboard.start_monitoring())
    except KeyboardInterrupt:
        print("Monitoring stopped")