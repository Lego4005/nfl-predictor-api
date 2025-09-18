"""
Real-time Prediction Monitoring Dashboard

Tracks accuracy in real-time, monitors expert performance metrics,
detects model drift, and provides alert system for anomalies.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from collections import defaultdict, deque
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class MetricType(Enum):
    """Types of metrics to monitor"""
    ACCURACY = "accuracy"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    PREDICTION_VOLUME = "prediction_volume"
    ERROR_RATE = "error_rate"
    DRIFT_SCORE = "drift_score"
    RESPONSE_TIME = "response_time"

@dataclass
class Alert:
    """Alert for monitoring anomalies"""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    expert_id: Optional[str]
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolution_timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['level'] = self.level.value
        data['metric_type'] = self.metric_type.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.resolution_timestamp:
            data['resolution_timestamp'] = self.resolution_timestamp.isoformat()
        return data

@dataclass
class MetricSnapshot:
    """Snapshot of metrics at a point in time"""
    timestamp: datetime
    expert_id: Optional[str]
    metric_type: MetricType
    value: float
    context: Dict[str, Any]

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metric_type'] = self.metric_type.value
        return data

@dataclass
class PerformanceDashboard:
    """Real-time performance dashboard data"""
    timestamp: datetime
    overall_accuracy: float
    expert_accuracies: Dict[str, float]
    recent_predictions: int
    active_alerts: int
    drift_scores: Dict[str, float]
    confidence_calibration: float
    prediction_volume_trend: str
    system_health: str

class RealTimeMetricsCollector:
    """Collects metrics in real-time"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_buffer = defaultdict(lambda: deque(maxlen=window_size))
        self.accuracy_buffer = deque(maxlen=window_size)
        self.prediction_times = deque(maxlen=window_size)
        self.confidence_buffer = deque(maxlen=window_size)
        self.actual_buffer = deque(maxlen=window_size)
        self.lock = threading.Lock()

    def add_prediction_result(self, expert_id: str, prediction: float,
                            actual: float, confidence: float, response_time: float):
        """Add a prediction result for real-time tracking"""
        with self.lock:
            timestamp = datetime.now()

            # Calculate if prediction was correct
            is_correct = (prediction > 0.5) == (actual > 0.5)

            # Add to buffers
            self.accuracy_buffer.append(is_correct)
            self.prediction_times.append(response_time)
            self.confidence_buffer.append(confidence)
            self.actual_buffer.append(actual)

            # Add to expert-specific metrics
            self.metrics_buffer[f"{expert_id}_accuracy"].append(is_correct)
            self.metrics_buffer[f"{expert_id}_confidence"].append(confidence)
            self.metrics_buffer[f"{expert_id}_response_time"].append(response_time)
            self.metrics_buffer[f"{expert_id}_error"].append(abs(prediction - actual))

    def get_current_accuracy(self, expert_id: Optional[str] = None) -> float:
        """Get current accuracy for system or specific expert"""
        with self.lock:
            if expert_id:
                buffer = self.metrics_buffer[f"{expert_id}_accuracy"]
                if not buffer:
                    return 0.5
                return sum(buffer) / len(buffer)
            else:
                if not self.accuracy_buffer:
                    return 0.5
                return sum(self.accuracy_buffer) / len(self.accuracy_buffer)

    def get_confidence_calibration(self, expert_id: Optional[str] = None) -> float:
        """Get confidence calibration score"""
        with self.lock:
            if expert_id:
                conf_buffer = self.metrics_buffer[f"{expert_id}_confidence"]
                acc_buffer = self.metrics_buffer[f"{expert_id}_accuracy"]
            else:
                conf_buffer = self.confidence_buffer
                acc_buffer = self.accuracy_buffer

            if len(conf_buffer) < 10 or len(acc_buffer) < 10:
                return 0.5

            # Simple calibration score: 1 - |mean_confidence - accuracy|
            mean_confidence = sum(conf_buffer) / len(conf_buffer)
            accuracy = sum(acc_buffer) / len(acc_buffer)
            return 1.0 - abs(mean_confidence - accuracy)

    def get_average_response_time(self, expert_id: Optional[str] = None) -> float:
        """Get average response time"""
        with self.lock:
            if expert_id:
                buffer = self.metrics_buffer[f"{expert_id}_response_time"]
            else:
                buffer = self.prediction_times

            if not buffer:
                return 0.0

            return sum(buffer) / len(buffer)

    def get_error_rate(self, expert_id: Optional[str] = None) -> float:
        """Get average prediction error"""
        with self.lock:
            if expert_id:
                buffer = self.metrics_buffer[f"{expert_id}_error"]
            else:
                # Calculate from accuracy buffer
                if not self.accuracy_buffer:
                    return 0.5
                return 1.0 - (sum(self.accuracy_buffer) / len(self.accuracy_buffer))

            if not buffer:
                return 0.5

            return sum(buffer) / len(buffer)

    def get_prediction_volume_trend(self) -> str:
        """Get prediction volume trend"""
        with self.lock:
            if len(self.accuracy_buffer) < 20:
                return "stable"

            recent_count = len([1 for _ in range(min(10, len(self.accuracy_buffer)))])
            older_count = len([1 for _ in range(min(10, len(self.accuracy_buffer) - 10))])

            if recent_count > older_count * 1.2:
                return "increasing"
            elif recent_count < older_count * 0.8:
                return "decreasing"
            else:
                return "stable"

class ThresholdManager:
    """Manages alert thresholds for different metrics"""

    def __init__(self):
        self.thresholds = {
            MetricType.ACCURACY: {
                AlertLevel.WARNING: 0.6,
                AlertLevel.CRITICAL: 0.5,
                AlertLevel.EMERGENCY: 0.4
            },
            MetricType.CONFIDENCE_CALIBRATION: {
                AlertLevel.WARNING: 0.7,
                AlertLevel.CRITICAL: 0.6,
                AlertLevel.EMERGENCY: 0.5
            },
            MetricType.ERROR_RATE: {
                AlertLevel.WARNING: 0.4,
                AlertLevel.CRITICAL: 0.5,
                AlertLevel.EMERGENCY: 0.6
            },
            MetricType.DRIFT_SCORE: {
                AlertLevel.WARNING: 0.3,
                AlertLevel.CRITICAL: 0.5,
                AlertLevel.EMERGENCY: 0.7
            },
            MetricType.RESPONSE_TIME: {
                AlertLevel.WARNING: 2.0,
                AlertLevel.CRITICAL: 5.0,
                AlertLevel.EMERGENCY: 10.0
            }
        }

    def check_threshold(self, metric_type: MetricType, value: float) -> Optional[AlertLevel]:
        """Check if value exceeds any threshold"""
        if metric_type not in self.thresholds:
            return None

        thresholds = self.thresholds[metric_type]

        # For accuracy and confidence calibration, lower values are worse
        if metric_type in [MetricType.ACCURACY, MetricType.CONFIDENCE_CALIBRATION]:
            for level in [AlertLevel.EMERGENCY, AlertLevel.CRITICAL, AlertLevel.WARNING]:
                if value <= thresholds[level]:
                    return level
        else:
            # For error rate, drift, and response time, higher values are worse
            for level in [AlertLevel.EMERGENCY, AlertLevel.CRITICAL, AlertLevel.WARNING]:
                if value >= thresholds[level]:
                    return level

        return None

    def update_threshold(self, metric_type: MetricType, level: AlertLevel, value: float):
        """Update a threshold value"""
        if metric_type not in self.thresholds:
            self.thresholds[metric_type] = {}
        self.thresholds[metric_type][level] = value

class AlertManager:
    """Manages alerts and notifications"""

    def __init__(self, max_alerts: int = 1000):
        self.alerts = deque(maxlen=max_alerts)
        self.active_alerts = {}  # alert_id -> Alert
        self.alert_callbacks = []
        self.lock = threading.Lock()

    def create_alert(self, level: AlertLevel, metric_type: MetricType,
                    message: str, value: float, threshold: float,
                    expert_id: Optional[str] = None) -> Alert:
        """Create a new alert"""
        with self.lock:
            alert_id = f"alert_{int(time.time() * 1000)}_{metric_type.value}"
            if expert_id:
                alert_id += f"_{expert_id}"

            alert = Alert(
                alert_id=alert_id,
                level=level,
                metric_type=metric_type,
                expert_id=expert_id,
                message=message,
                value=value,
                threshold=threshold,
                timestamp=datetime.now()
            )

            self.alerts.append(alert)
            self.active_alerts[alert_id] = alert

            # Trigger callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Error in alert callback: {e}")

            logger.warning(f"ALERT [{level.value.upper()}]: {message}")
            return alert

    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved"""
        with self.lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.resolved = True
                alert.resolution_timestamp = datetime.now()
                del self.active_alerts[alert_id]
                logger.info(f"Resolved alert: {alert_id}")

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by level"""
        with self.lock:
            alerts = list(self.active_alerts.values())
            if level:
                alerts = [a for a in alerts if a.level == level]
            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)

    def add_callback(self, callback):
        """Add callback function for alerts"""
        self.alert_callbacks.append(callback)

class DriftMonitor:
    """Monitors for model drift"""

    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.prediction_history = defaultdict(lambda: deque(maxlen=window_size))
        self.actual_history = defaultdict(lambda: deque(maxlen=window_size))
        self.drift_scores = {}

    def update_predictions(self, expert_id: str, predictions: List[float], actuals: List[float]):
        """Update prediction history for drift calculation"""
        for pred, actual in zip(predictions, actuals):
            self.prediction_history[expert_id].append(pred)
            self.actual_history[expert_id].append(actual)

        # Calculate drift score
        self.drift_scores[expert_id] = self._calculate_drift(expert_id)

    def _calculate_drift(self, expert_id: str) -> float:
        """Calculate drift score for an expert"""
        pred_history = self.prediction_history[expert_id]
        actual_history = self.actual_history[expert_id]

        if len(pred_history) < self.window_size // 2:
            return 0.0

        # Split into two windows
        mid_point = len(pred_history) // 2
        recent_preds = list(pred_history)[mid_point:]
        older_preds = list(pred_history)[:mid_point]
        recent_actuals = list(actual_history)[mid_point:]
        older_actuals = list(actual_history)[:mid_point]

        # Calculate distribution differences
        recent_pred_mean = np.mean(recent_preds)
        older_pred_mean = np.mean(older_preds)
        recent_actual_mean = np.mean(recent_actuals)
        older_actual_mean = np.mean(older_actuals)

        # Simple drift score based on mean differences
        pred_drift = abs(recent_pred_mean - older_pred_mean)
        actual_drift = abs(recent_actual_mean - older_actual_mean)

        return (pred_drift + actual_drift) / 2

    def get_drift_score(self, expert_id: str) -> float:
        """Get current drift score for an expert"""
        return self.drift_scores.get(expert_id, 0.0)

class PredictionMonitor:
    """Main prediction monitoring system"""

    def __init__(self, db_path: str = "data/prediction_monitoring.db"):
        self.db_path = db_path
        self.metrics_collector = RealTimeMetricsCollector()
        self.threshold_manager = ThresholdManager()
        self.alert_manager = AlertManager()
        self.drift_monitor = DriftMonitor()
        self.monitoring_active = True
        self.monitoring_thread = None
        self.dashboard_data = None

        self._init_database()
        self._start_monitoring()

    def _init_database(self):
        """Initialize monitoring database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            # Metric snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metric_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    expert_id TEXT,
                    metric_type TEXT,
                    value REAL,
                    context TEXT
                )
            """)

            # Alerts
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id TEXT UNIQUE,
                    level TEXT,
                    metric_type TEXT,
                    expert_id TEXT,
                    message TEXT,
                    value REAL,
                    threshold REAL,
                    timestamp TEXT,
                    resolved BOOLEAN,
                    resolution_timestamp TEXT
                )
            """)

            # Performance snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    overall_accuracy REAL,
                    expert_accuracies TEXT,
                    recent_predictions INTEGER,
                    active_alerts INTEGER,
                    drift_scores TEXT,
                    confidence_calibration REAL,
                    prediction_volume_trend TEXT,
                    system_health TEXT
                )
            """)

            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_metric_snapshots_timestamp ON metric_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)")

    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started prediction monitoring")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_metrics()
                self._check_alerts()
                self._update_dashboard()
                time.sleep(10)  # Check every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5)

    def _collect_metrics(self):
        """Collect current metrics"""
        try:
            timestamp = datetime.now()

            # Collect system-wide metrics
            overall_accuracy = self.metrics_collector.get_current_accuracy()
            confidence_calibration = self.metrics_collector.get_confidence_calibration()
            avg_response_time = self.metrics_collector.get_average_response_time()
            error_rate = self.metrics_collector.get_error_rate()

            # Store system metrics
            metrics = [
                MetricSnapshot(timestamp, None, MetricType.ACCURACY, overall_accuracy, {}),
                MetricSnapshot(timestamp, None, MetricType.CONFIDENCE_CALIBRATION, confidence_calibration, {}),
                MetricSnapshot(timestamp, None, MetricType.RESPONSE_TIME, avg_response_time, {}),
                MetricSnapshot(timestamp, None, MetricType.ERROR_RATE, error_rate, {})
            ]

            # Collect expert-specific metrics
            expert_ids = set()
            for key in self.metrics_collector.metrics_buffer.keys():
                if '_' in key:
                    expert_id = key.split('_')[0]
                    expert_ids.add(expert_id)

            for expert_id in expert_ids:
                expert_accuracy = self.metrics_collector.get_current_accuracy(expert_id)
                expert_confidence = self.metrics_collector.get_confidence_calibration(expert_id)
                expert_response_time = self.metrics_collector.get_average_response_time(expert_id)
                expert_error_rate = self.metrics_collector.get_error_rate(expert_id)
                expert_drift = self.drift_monitor.get_drift_score(expert_id)

                expert_metrics = [
                    MetricSnapshot(timestamp, expert_id, MetricType.ACCURACY, expert_accuracy, {}),
                    MetricSnapshot(timestamp, expert_id, MetricType.CONFIDENCE_CALIBRATION, expert_confidence, {}),
                    MetricSnapshot(timestamp, expert_id, MetricType.RESPONSE_TIME, expert_response_time, {}),
                    MetricSnapshot(timestamp, expert_id, MetricType.ERROR_RATE, expert_error_rate, {}),
                    MetricSnapshot(timestamp, expert_id, MetricType.DRIFT_SCORE, expert_drift, {})
                ]

                metrics.extend(expert_metrics)

            # Store metrics in database
            self._store_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")

    def _check_alerts(self):
        """Check for alert conditions"""
        try:
            # Check system-wide metrics
            overall_accuracy = self.metrics_collector.get_current_accuracy()
            confidence_calibration = self.metrics_collector.get_confidence_calibration()
            avg_response_time = self.metrics_collector.get_average_response_time()
            error_rate = self.metrics_collector.get_error_rate()

            # Check thresholds
            self._check_metric_threshold(MetricType.ACCURACY, overall_accuracy, None)
            self._check_metric_threshold(MetricType.CONFIDENCE_CALIBRATION, confidence_calibration, None)
            self._check_metric_threshold(MetricType.RESPONSE_TIME, avg_response_time, None)
            self._check_metric_threshold(MetricType.ERROR_RATE, error_rate, None)

            # Check expert-specific metrics
            expert_ids = set()
            for key in self.metrics_collector.metrics_buffer.keys():
                if '_' in key:
                    expert_id = key.split('_')[0]
                    expert_ids.add(expert_id)

            for expert_id in expert_ids:
                expert_accuracy = self.metrics_collector.get_current_accuracy(expert_id)
                expert_drift = self.drift_monitor.get_drift_score(expert_id)

                self._check_metric_threshold(MetricType.ACCURACY, expert_accuracy, expert_id)
                self._check_metric_threshold(MetricType.DRIFT_SCORE, expert_drift, expert_id)

        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    def _check_metric_threshold(self, metric_type: MetricType, value: float, expert_id: Optional[str]):
        """Check if a metric exceeds thresholds"""
        alert_level = self.threshold_manager.check_threshold(metric_type, value)

        if alert_level:
            threshold = self.threshold_manager.thresholds[metric_type][alert_level]
            expert_str = f" for {expert_id}" if expert_id else ""
            message = f"{metric_type.value.title()} {value:.3f} exceeded threshold {threshold:.3f}{expert_str}"

            self.alert_manager.create_alert(
                level=alert_level,
                metric_type=metric_type,
                message=message,
                value=value,
                threshold=threshold,
                expert_id=expert_id
            )

    def _update_dashboard(self):
        """Update dashboard data"""
        try:
            timestamp = datetime.now()
            overall_accuracy = self.metrics_collector.get_current_accuracy()
            confidence_calibration = self.metrics_collector.get_confidence_calibration()
            prediction_volume_trend = self.metrics_collector.get_prediction_volume_trend()

            # Get expert accuracies
            expert_accuracies = {}
            expert_ids = set()
            for key in self.metrics_collector.metrics_buffer.keys():
                if '_accuracy' in key:
                    expert_id = key.replace('_accuracy', '')
                    expert_ids.add(expert_id)

            for expert_id in expert_ids:
                expert_accuracies[expert_id] = self.metrics_collector.get_current_accuracy(expert_id)

            # Get drift scores
            drift_scores = {}
            for expert_id in expert_ids:
                drift_scores[expert_id] = self.drift_monitor.get_drift_score(expert_id)

            # Determine system health
            active_alerts = len(self.alert_manager.get_active_alerts())
            critical_alerts = len(self.alert_manager.get_active_alerts(AlertLevel.CRITICAL))
            emergency_alerts = len(self.alert_manager.get_active_alerts(AlertLevel.EMERGENCY))

            if emergency_alerts > 0:
                system_health = "critical"
            elif critical_alerts > 0:
                system_health = "degraded"
            elif active_alerts > 5:
                system_health = "warning"
            else:
                system_health = "healthy"

            self.dashboard_data = PerformanceDashboard(
                timestamp=timestamp,
                overall_accuracy=overall_accuracy,
                expert_accuracies=expert_accuracies,
                recent_predictions=len(self.metrics_collector.accuracy_buffer),
                active_alerts=active_alerts,
                drift_scores=drift_scores,
                confidence_calibration=confidence_calibration,
                prediction_volume_trend=prediction_volume_trend,
                system_health=system_health
            )

            # Store dashboard snapshot
            self._store_dashboard_snapshot(self.dashboard_data)

        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def _store_metrics(self, metrics: List[MetricSnapshot]):
        """Store metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for metric in metrics:
                    conn.execute("""
                        INSERT INTO metric_snapshots (timestamp, expert_id, metric_type, value, context)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        metric.timestamp.isoformat(),
                        metric.expert_id,
                        metric.metric_type.value,
                        metric.value,
                        json.dumps(metric.context, default=str)
                    ))
        except Exception as e:
            logger.error(f"Error storing metrics: {e}")

    def _store_dashboard_snapshot(self, dashboard: PerformanceDashboard):
        """Store dashboard snapshot in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO performance_snapshots
                    (timestamp, overall_accuracy, expert_accuracies, recent_predictions,
                     active_alerts, drift_scores, confidence_calibration,
                     prediction_volume_trend, system_health)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    dashboard.timestamp.isoformat(),
                    dashboard.overall_accuracy,
                    json.dumps(dashboard.expert_accuracies, default=str),
                    dashboard.recent_predictions,
                    dashboard.active_alerts,
                    json.dumps(dashboard.drift_scores, default=str),
                    dashboard.confidence_calibration,
                    dashboard.prediction_volume_trend,
                    dashboard.system_health
                ))
        except Exception as e:
            logger.error(f"Error storing dashboard snapshot: {e}")

    # Public API methods

    def record_prediction(self, expert_id: str, prediction: float, actual: float,
                         confidence: float, response_time: float = 0.0):
        """Record a prediction result"""
        self.metrics_collector.add_prediction_result(
            expert_id, prediction, actual, confidence, response_time
        )

        # Update drift monitor
        self.drift_monitor.update_predictions(expert_id, [prediction], [actual])

    def get_dashboard_data(self) -> Optional[PerformanceDashboard]:
        """Get current dashboard data"""
        return self.dashboard_data

    def get_expert_metrics(self, expert_id: str) -> Dict[str, float]:
        """Get current metrics for a specific expert"""
        return {
            'accuracy': self.metrics_collector.get_current_accuracy(expert_id),
            'confidence_calibration': self.metrics_collector.get_confidence_calibration(expert_id),
            'response_time': self.metrics_collector.get_average_response_time(expert_id),
            'error_rate': self.metrics_collector.get_error_rate(expert_id),
            'drift_score': self.drift_monitor.get_drift_score(expert_id)
        }

    def get_system_metrics(self) -> Dict[str, float]:
        """Get current system-wide metrics"""
        return {
            'overall_accuracy': self.metrics_collector.get_current_accuracy(),
            'confidence_calibration': self.metrics_collector.get_confidence_calibration(),
            'avg_response_time': self.metrics_collector.get_average_response_time(),
            'error_rate': self.metrics_collector.get_error_rate(),
            'prediction_count': len(self.metrics_collector.accuracy_buffer)
        }

    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Dict]:
        """Get active alerts"""
        alerts = self.alert_manager.get_active_alerts(level)
        return [alert.to_dict() for alert in alerts]

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        self.alert_manager.resolve_alert(alert_id)

    def update_threshold(self, metric_type: MetricType, level: AlertLevel, value: float):
        """Update alert threshold"""
        self.threshold_manager.update_threshold(metric_type, level, value)

    def add_alert_callback(self, callback):
        """Add callback for alert notifications"""
        self.alert_manager.add_callback(callback)

    def get_historical_metrics(self, metric_type: MetricType, expert_id: Optional[str] = None,
                             hours: int = 24) -> List[Dict]:
        """Get historical metrics"""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)

            with sqlite3.connect(self.db_path) as conn:
                query = """
                    SELECT timestamp, expert_id, value FROM metric_snapshots
                    WHERE metric_type = ? AND timestamp > ?
                """
                params = [metric_type.value, cutoff.isoformat()]

                if expert_id:
                    query += " AND expert_id = ?"
                    params.append(expert_id)

                query += " ORDER BY timestamp"

                cursor = conn.execute(query, params)
                return [
                    {'timestamp': row[0], 'expert_id': row[1], 'value': row[2]}
                    for row in cursor.fetchall()
                ]
        except Exception as e:
            logger.error(f"Error getting historical metrics: {e}")
            return []

    def stop_monitoring(self):
        """Stop monitoring system"""
        self.monitoring_active = False
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped prediction monitoring")

    def generate_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        try:
            dashboard = self.get_dashboard_data()
            system_metrics = self.get_system_metrics()
            active_alerts = self.get_active_alerts()

            # Get top performing and worst performing experts
            expert_performances = []
            for expert_id, accuracy in dashboard.expert_accuracies.items():
                expert_performances.append({
                    'expert_id': expert_id,
                    'accuracy': accuracy,
                    'drift_score': dashboard.drift_scores.get(expert_id, 0.0)
                })

            expert_performances.sort(key=lambda x: x['accuracy'], reverse=True)

            return {
                'timestamp': datetime.now().isoformat(),
                'system_health': dashboard.system_health if dashboard else 'unknown',
                'system_metrics': system_metrics,
                'expert_count': len(dashboard.expert_accuracies) if dashboard else 0,
                'top_experts': expert_performances[:5],
                'worst_experts': expert_performances[-5:] if len(expert_performances) >= 5 else [],
                'active_alerts_count': len(active_alerts),
                'critical_alerts': [a for a in active_alerts if a['level'] == AlertLevel.CRITICAL.value],
                'recent_prediction_count': system_metrics.get('prediction_count', 0),
                'overall_accuracy': system_metrics.get('overall_accuracy', 0.0),
                'confidence_calibration': system_metrics.get('confidence_calibration', 0.0)
            }
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

# Example usage and testing
if __name__ == "__main__":
    # Initialize monitor
    monitor = PredictionMonitor()

    # Add alert callback
    def print_alert(alert):
        print(f"ALERT: {alert.message}")

    monitor.add_alert_callback(print_alert)

    # Simulate some predictions
    import time
    import random

    for i in range(50):
        expert_id = f"expert_{i % 5}"
        prediction = random.uniform(0.1, 0.9)
        actual = random.uniform(0.1, 0.9)
        confidence = random.uniform(0.5, 1.0)
        response_time = random.uniform(0.1, 2.0)

        monitor.record_prediction(expert_id, prediction, actual, confidence, response_time)
        time.sleep(0.1)

    # Get dashboard
    dashboard = monitor.get_dashboard_data()
    if dashboard:
        print(f"System Health: {dashboard.system_health}")
        print(f"Overall Accuracy: {dashboard.overall_accuracy:.3f}")
        print(f"Active Alerts: {dashboard.active_alerts}")

    # Generate report
    report = monitor.generate_monitoring_report()
    print(json.dumps(report, indent=2))

    # Stop monitoring
    monitor.stop_monitoring()