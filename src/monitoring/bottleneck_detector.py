"""
Performance Bottleneck Detection System
Automated analysis and detection of performance bottlenecks in the NFL Predictor API
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from sklearn.ensemble import IsolationForest
import json
import redis


class BottleneckType(Enum):
    CPU_BOUND = "cpu_bound"
    MEMORY_BOUND = "memory_bound"
    IO_BOUND = "io_bound"
    DATABASE_BOUND = "database_bound"
    NETWORK_BOUND = "network_bound"
    CACHE_INEFFICIENCY = "cache_inefficiency"
    ALGORITHM_INEFFICIENCY = "algorithm_inefficiency"


class BottleneckSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BottleneckDetection:
    timestamp: datetime
    type: BottleneckType
    severity: BottleneckSeverity
    affected_component: str
    root_cause: str
    impact_score: float
    suggested_actions: List[str]
    correlation_metrics: Dict[str, float]
    confidence_score: float


@dataclass
class PerformanceAnomaly:
    timestamp: datetime
    metric_name: str
    expected_value: float
    actual_value: float
    deviation_score: float
    is_significant: bool
    context: Dict[str, Any]


class BottleneckDetector:
    """Advanced bottleneck detection using statistical analysis and ML techniques"""

    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Statistical analysis parameters
        self.anomaly_threshold = config.get('anomaly_threshold', 2.5)  # Standard deviations
        self.correlation_threshold = config.get('correlation_threshold', 0.7)
        self.window_size = config.get('analysis_window_minutes', 30)

        # ML models for anomaly detection
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()

        # Historical data for baseline
        self.baseline_data: Dict[str, List[float]] = {}
        self.detection_history: List[BottleneckDetection] = []

    async def detect_bottlenecks(self, metrics_data: List[Dict[str, Any]]) -> List[BottleneckDetection]:
        """Main bottleneck detection method"""
        if len(metrics_data) < 10:
            return []

        try:
            # Convert to DataFrame for analysis
            df = pd.DataFrame(metrics_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Detect anomalies
            anomalies = await self._detect_anomalies(df)

            # Analyze correlations
            correlations = await self._analyze_correlations(df)

            # Identify bottleneck patterns
            bottlenecks = await self._identify_bottlenecks(df, anomalies, correlations)

            # Update historical data
            self.detection_history.extend(bottlenecks)

            # Store results in Redis
            await self._store_detections(bottlenecks)

            return bottlenecks

        except Exception as e:
            self.logger.error(f"Error in bottleneck detection: {e}")
            return []

    async def _detect_anomalies(self, df: pd.DataFrame) -> List[PerformanceAnomaly]:
        """Detect performance anomalies using statistical methods"""
        anomalies = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        for col in numeric_cols:
            if col == 'timestamp':
                continue

            values = df[col].dropna()
            if len(values) < 5:
                continue

            # Calculate statistical baseline
            mean_val = values.mean()
            std_val = values.std()

            if std_val == 0:
                continue

            # Z-score analysis
            z_scores = np.abs((values - mean_val) / std_val)
            anomaly_indices = np.where(z_scores > self.anomaly_threshold)[0]

            for idx in anomaly_indices:
                anomaly = PerformanceAnomaly(
                    timestamp=df.iloc[idx]['timestamp'],
                    metric_name=col,
                    expected_value=mean_val,
                    actual_value=values.iloc[idx],
                    deviation_score=z_scores.iloc[idx],
                    is_significant=z_scores.iloc[idx] > 3.0,
                    context={
                        'std_dev': std_val,
                        'percentile_rank': stats.percentileofscore(values, values.iloc[idx])
                    }
                )
                anomalies.append(anomaly)

        # Use Isolation Forest for multivariate anomaly detection
        if len(numeric_cols) > 2:
            try:
                feature_data = df[numeric_cols].fillna(df[numeric_cols].mean())
                if len(feature_data) > 10:
                    # Fit and predict
                    anomaly_scores = self.isolation_forest.fit_predict(feature_data)
                    outlier_indices = np.where(anomaly_scores == -1)[0]

                    for idx in outlier_indices:
                        anomaly = PerformanceAnomaly(
                            timestamp=df.iloc[idx]['timestamp'],
                            metric_name='multivariate_anomaly',
                            expected_value=0.0,
                            actual_value=1.0,
                            deviation_score=3.0,  # High score for ML-detected anomalies
                            is_significant=True,
                            context={
                                'detection_method': 'isolation_forest',
                                'feature_count': len(numeric_cols)
                            }
                        )
                        anomalies.append(anomaly)

            except Exception as e:
                self.logger.warning(f"Isolation Forest failed: {e}")

        return anomalies

    async def _analyze_correlations(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Analyze correlations between metrics to identify dependencies"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        correlations = {}

        if len(numeric_cols) < 2:
            return correlations

        try:
            # Calculate correlation matrix
            corr_matrix = df[numeric_cols].corr()

            for col1 in numeric_cols:
                correlations[col1] = {}
                for col2 in numeric_cols:
                    if col1 != col2 and not np.isnan(corr_matrix.loc[col1, col2]):
                        correlations[col1][col2] = corr_matrix.loc[col1, col2]

            return correlations

        except Exception as e:
            self.logger.error(f"Error calculating correlations: {e}")
            return {}

    async def _identify_bottlenecks(
        self,
        df: pd.DataFrame,
        anomalies: List[PerformanceAnomaly],
        correlations: Dict[str, Dict[str, float]]
    ) -> List[BottleneckDetection]:
        """Identify specific bottlenecks based on anomalies and correlations"""
        bottlenecks = []

        # Group anomalies by time windows
        anomaly_windows = self._group_anomalies_by_time(anomalies)

        for window_start, window_anomalies in anomaly_windows.items():
            # Analyze each time window for bottleneck patterns
            bottleneck = await self._analyze_bottleneck_pattern(
                window_start, window_anomalies, correlations, df
            )
            if bottleneck:
                bottlenecks.append(bottleneck)

        return bottlenecks

    def _group_anomalies_by_time(
        self,
        anomalies: List[PerformanceAnomaly]
    ) -> Dict[datetime, List[PerformanceAnomaly]]:
        """Group anomalies into time windows"""
        windows = {}
        window_minutes = 5

        for anomaly in anomalies:
            # Round timestamp to window
            window_start = anomaly.timestamp.replace(
                minute=(anomaly.timestamp.minute // window_minutes) * window_minutes,
                second=0,
                microsecond=0
            )

            if window_start not in windows:
                windows[window_start] = []
            windows[window_start].append(anomaly)

        # Only return windows with multiple anomalies (indicating systemic issues)
        return {k: v for k, v in windows.items() if len(v) >= 2}

    async def _analyze_bottleneck_pattern(
        self,
        timestamp: datetime,
        anomalies: List[PerformanceAnomaly],
        correlations: Dict[str, Dict[str, float]],
        df: pd.DataFrame
    ) -> Optional[BottleneckDetection]:
        """Analyze a specific pattern of anomalies to identify bottleneck type"""

        # Extract metric names from anomalies
        anomaly_metrics = {a.metric_name for a in anomalies}

        # Define bottleneck patterns
        patterns = {
            BottleneckType.CPU_BOUND: {
                'primary_metrics': ['system_cpu', 'api_response_time'],
                'secondary_metrics': ['websocket_connections'],
                'correlation_pairs': [('system_cpu', 'api_response_time')]
            },
            BottleneckType.MEMORY_BOUND: {
                'primary_metrics': ['system_memory'],
                'secondary_metrics': ['system_cpu', 'api_response_time', 'cache_hit_rate'],
                'correlation_pairs': [('system_memory', 'api_response_time')]
            },
            BottleneckType.DATABASE_BOUND: {
                'primary_metrics': ['database_connections', 'api_response_time'],
                'secondary_metrics': ['system_cpu'],
                'correlation_pairs': [('database_connections', 'api_response_time')]
            },
            BottleneckType.CACHE_INEFFICIENCY: {
                'primary_metrics': ['cache_hit_rate'],
                'secondary_metrics': ['api_response_time', 'database_connections'],
                'correlation_pairs': [('cache_hit_rate', 'api_response_time')]
            },
            BottleneckType.NETWORK_BOUND: {
                'primary_metrics': ['api_response_time', 'error_rate'],
                'secondary_metrics': ['websocket_connections'],
                'correlation_pairs': [('api_response_time', 'error_rate')]
            }
        }

        # Score each bottleneck type
        best_match = None
        best_score = 0

        for bottleneck_type, pattern in patterns.items():
            score = await self._score_bottleneck_pattern(
                anomaly_metrics, pattern, correlations
            )

            if score > best_score and score > 0.5:
                best_score = score
                best_match = bottleneck_type

        if not best_match:
            return None

        # Calculate severity and impact
        severity = self._calculate_bottleneck_severity(anomalies)
        impact_score = self._calculate_impact_score(anomalies, correlations)

        # Generate suggested actions
        suggested_actions = self._generate_suggested_actions(best_match, anomalies)

        # Get correlation metrics for the detected bottleneck
        correlation_metrics = self._extract_relevant_correlations(
            best_match, correlations, patterns[best_match]
        )

        return BottleneckDetection(
            timestamp=timestamp,
            type=best_match,
            severity=severity,
            affected_component=self._identify_affected_component(best_match, anomalies),
            root_cause=self._determine_root_cause(best_match, anomalies),
            impact_score=impact_score,
            suggested_actions=suggested_actions,
            correlation_metrics=correlation_metrics,
            confidence_score=best_score
        )

    async def _score_bottleneck_pattern(
        self,
        anomaly_metrics: set,
        pattern: Dict[str, Any],
        correlations: Dict[str, Dict[str, float]]
    ) -> float:
        """Score how well anomalies match a bottleneck pattern"""
        score = 0.0
        max_score = 0.0

        # Score primary metrics presence
        for metric in pattern['primary_metrics']:
            max_score += 2.0
            if metric in anomaly_metrics:
                score += 2.0

        # Score secondary metrics presence
        for metric in pattern.get('secondary_metrics', []):
            max_score += 1.0
            if metric in anomaly_metrics:
                score += 1.0

        # Score correlation patterns
        for metric1, metric2 in pattern.get('correlation_pairs', []):
            max_score += 3.0
            if (metric1 in correlations and
                metric2 in correlations[metric1] and
                abs(correlations[metric1][metric2]) > self.correlation_threshold):
                score += 3.0

        return score / max_score if max_score > 0 else 0.0

    def _calculate_bottleneck_severity(self, anomalies: List[PerformanceAnomaly]) -> BottleneckSeverity:
        """Calculate severity based on anomaly characteristics"""
        if not anomalies:
            return BottleneckSeverity.LOW

        # Get maximum deviation score
        max_deviation = max(a.deviation_score for a in anomalies)
        significant_count = sum(1 for a in anomalies if a.is_significant)
        total_count = len(anomalies)

        if max_deviation > 5.0 or significant_count / total_count > 0.8:
            return BottleneckSeverity.CRITICAL
        elif max_deviation > 4.0 or significant_count / total_count > 0.6:
            return BottleneckSeverity.HIGH
        elif max_deviation > 3.0 or significant_count / total_count > 0.4:
            return BottleneckSeverity.MEDIUM
        else:
            return BottleneckSeverity.LOW

    def _calculate_impact_score(
        self,
        anomalies: List[PerformanceAnomaly],
        correlations: Dict[str, Dict[str, float]]
    ) -> float:
        """Calculate the impact score of the bottleneck (0-1)"""
        if not anomalies:
            return 0.0

        # Base impact from anomaly severity
        base_impact = min(sum(a.deviation_score for a in anomalies) / (len(anomalies) * 5.0), 1.0)

        # Amplify impact based on correlation spread
        correlation_amplifier = 1.0
        critical_metrics = {'api_response_time', 'prediction_accuracy', 'error_rate'}

        for anomaly in anomalies:
            if anomaly.metric_name in critical_metrics:
                correlation_amplifier += 0.3

            # Check how many other metrics this anomaly correlates with
            metric_correlations = correlations.get(anomaly.metric_name, {})
            high_correlations = sum(1 for corr in metric_correlations.values()
                                  if abs(corr) > self.correlation_threshold)
            correlation_amplifier += high_correlations * 0.1

        return min(base_impact * correlation_amplifier, 1.0)

    def _generate_suggested_actions(
        self,
        bottleneck_type: BottleneckType,
        anomalies: List[PerformanceAnomaly]
    ) -> List[str]:
        """Generate specific suggested actions for each bottleneck type"""
        actions = {
            BottleneckType.CPU_BOUND: [
                "Scale up CPU resources or add more instances",
                "Optimize CPU-intensive algorithms",
                "Implement caching for expensive computations",
                "Profile code to identify CPU hotspots",
                "Consider async processing for heavy tasks"
            ],
            BottleneckType.MEMORY_BOUND: [
                "Increase available memory",
                "Optimize memory usage in algorithms",
                "Implement pagination for large datasets",
                "Clear unused objects and caches",
                "Profile memory usage to find leaks"
            ],
            BottleneckType.DATABASE_BOUND: [
                "Optimize database queries",
                "Add database indexes",
                "Increase connection pool size",
                "Consider read replicas",
                "Implement query caching",
                "Review slow query logs"
            ],
            BottleneckType.CACHE_INEFFICIENCY: [
                "Increase cache size",
                "Optimize cache key strategy",
                "Review cache eviction policies",
                "Implement cache warming",
                "Add cache monitoring"
            ],
            BottleneckType.NETWORK_BOUND: [
                "Optimize network calls",
                "Implement connection pooling",
                "Add CDN for static assets",
                "Compress response data",
                "Review timeout configurations"
            ],
            BottleneckType.IO_BOUND: [
                "Optimize file I/O operations",
                "Use async I/O where possible",
                "Add SSD storage",
                "Implement I/O caching",
                "Review disk usage patterns"
            ],
            BottleneckType.ALGORITHM_INEFFICIENCY: [
                "Review algorithm complexity",
                "Implement more efficient data structures",
                "Add algorithmic optimizations",
                "Consider parallel processing",
                "Profile algorithm performance"
            ]
        }

        base_actions = actions.get(bottleneck_type, ["Monitor system closely"])

        # Add specific actions based on anomaly metrics
        specific_actions = []
        for anomaly in anomalies:
            if anomaly.metric_name == 'api_response_time' and anomaly.deviation_score > 4.0:
                specific_actions.append("Investigate API endpoint performance immediately")
            elif anomaly.metric_name == 'prediction_accuracy' and anomaly.actual_value < 0.6:
                specific_actions.append("Review and retrain ML models")
            elif anomaly.metric_name == 'error_rate' and anomaly.actual_value > 0.1:
                specific_actions.append("Investigate error logs for root cause")

        return base_actions[:3] + specific_actions  # Limit to most important actions

    def _identify_affected_component(
        self,
        bottleneck_type: BottleneckType,
        anomalies: List[PerformanceAnomaly]
    ) -> str:
        """Identify the primary affected component"""
        component_mapping = {
            BottleneckType.CPU_BOUND: "compute_engine",
            BottleneckType.MEMORY_BOUND: "memory_system",
            BottleneckType.DATABASE_BOUND: "database_layer",
            BottleneckType.CACHE_INEFFICIENCY: "cache_system",
            BottleneckType.NETWORK_BOUND: "network_layer",
            BottleneckType.IO_BOUND: "storage_system",
            BottleneckType.ALGORITHM_INEFFICIENCY: "ml_algorithms"
        }

        return component_mapping.get(bottleneck_type, "unknown")

    def _determine_root_cause(
        self,
        bottleneck_type: BottleneckType,
        anomalies: List[PerformanceAnomaly]
    ) -> str:
        """Determine the likely root cause of the bottleneck"""
        # Analyze anomaly patterns to infer root cause
        primary_anomaly = max(anomalies, key=lambda x: x.deviation_score)

        root_causes = {
            BottleneckType.CPU_BOUND: f"High CPU utilization detected (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.MEMORY_BOUND: f"Memory pressure detected (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.DATABASE_BOUND: f"Database performance degradation (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.CACHE_INEFFICIENCY: f"Cache hit rate dropped significantly (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.NETWORK_BOUND: f"Network latency or connectivity issues (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.IO_BOUND: f"I/O subsystem performance issues (deviation: {primary_anomaly.deviation_score:.2f}σ)",
            BottleneckType.ALGORITHM_INEFFICIENCY: f"Algorithm performance degradation (deviation: {primary_anomaly.deviation_score:.2f}σ)"
        }

        return root_causes.get(bottleneck_type, f"Performance anomaly detected: {primary_anomaly.metric_name}")

    def _extract_relevant_correlations(
        self,
        bottleneck_type: BottleneckType,
        correlations: Dict[str, Dict[str, float]],
        pattern: Dict[str, Any]
    ) -> Dict[str, float]:
        """Extract relevant correlation metrics for the detected bottleneck"""
        relevant_correlations = {}

        for metric1, metric2 in pattern.get('correlation_pairs', []):
            if metric1 in correlations and metric2 in correlations[metric1]:
                key = f"{metric1}_vs_{metric2}"
                relevant_correlations[key] = correlations[metric1][metric2]

        return relevant_correlations

    async def _store_detections(self, bottlenecks: List[BottleneckDetection]):
        """Store bottleneck detections in Redis"""
        try:
            for bottleneck in bottlenecks:
                detection_data = {
                    'timestamp': bottleneck.timestamp.isoformat(),
                    'type': bottleneck.type.value,
                    'severity': bottleneck.severity.value,
                    'affected_component': bottleneck.affected_component,
                    'root_cause': bottleneck.root_cause,
                    'impact_score': bottleneck.impact_score,
                    'suggested_actions': bottleneck.suggested_actions,
                    'correlation_metrics': bottleneck.correlation_metrics,
                    'confidence_score': bottleneck.confidence_score
                }

                # Store individual detection
                key = f"bottleneck_detection:{bottleneck.timestamp.strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.setex(key, 86400, json.dumps(detection_data))

                # Add to detection history list
                self.redis_client.lpush('bottleneck_history', json.dumps(detection_data))
                self.redis_client.ltrim('bottleneck_history', 0, 999)  # Keep last 1000 detections

        except Exception as e:
            self.logger.error(f"Error storing bottleneck detections: {e}")

    def get_recent_bottlenecks(self, hours: int = 24) -> List[BottleneckDetection]:
        """Get recent bottleneck detections"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [
            detection for detection in self.detection_history
            if detection.timestamp > cutoff
        ]

    def get_bottleneck_summary(self) -> Dict[str, Any]:
        """Get summary of bottleneck detections"""
        recent_bottlenecks = self.get_recent_bottlenecks(24)

        if not recent_bottlenecks:
            return {
                'total_bottlenecks': 0,
                'severity_breakdown': {},
                'type_breakdown': {},
                'most_affected_component': None,
                'average_impact_score': 0.0
            }

        severity_counts = {}
        type_counts = {}
        component_counts = {}

        for bottleneck in recent_bottlenecks:
            # Count severities
            severity = bottleneck.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Count types
            btype = bottleneck.type.value
            type_counts[btype] = type_counts.get(btype, 0) + 1

            # Count components
            component = bottleneck.affected_component
            component_counts[component] = component_counts.get(component, 0) + 1

        return {
            'total_bottlenecks': len(recent_bottlenecks),
            'severity_breakdown': severity_counts,
            'type_breakdown': type_counts,
            'most_affected_component': max(component_counts.items(), key=lambda x: x[1])[0] if component_counts else None,
            'average_impact_score': sum(b.impact_score for b in recent_bottlenecks) / len(recent_bottlenecks),
            'average_confidence_score': sum(b.confidence_score for b in recent_bottlenecks) / len(recent_bottlenecks)
        }