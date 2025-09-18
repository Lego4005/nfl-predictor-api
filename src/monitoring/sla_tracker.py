"""
SLA Compliance Tracker
Monitors and tracks SLA compliance metrics with historical analysis
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
import redis
from sqlalchemy import create_engine, text


class SLAStatus(Enum):
    MEETING = "meeting"
    WARNING = "warning"
    BREACHED = "breached"
    CRITICAL = "critical"


@dataclass
class SLATarget:
    metric_name: str
    target_value: float
    comparison_type: str  # 'less_than', 'greater_than', 'equals'
    warning_threshold: float  # % of target for warning
    critical_threshold: float  # % of target for critical
    measurement_window: int  # minutes
    description: str


@dataclass
class SLAMeasurement:
    timestamp: datetime
    metric_name: str
    measured_value: float
    target_value: float
    compliance_percentage: float
    status: SLAStatus
    measurement_window: int
    breach_duration: int  # minutes in breach


@dataclass
class SLAReport:
    period_start: datetime
    period_end: datetime
    overall_compliance: float
    metrics: Dict[str, Dict[str, Any]]
    breaches: List[SLAMeasurement]
    improvements: List[str]
    action_items: List[str]
    trends: Dict[str, str]


class SLATracker:
    """SLA compliance monitoring and tracking system"""

    def __init__(self, redis_client: redis.Redis, db_engine, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.db_engine = db_engine
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Define SLA targets
        self.sla_targets = self._initialize_sla_targets()

        # Historical data for trend analysis
        self.measurement_history: List[SLAMeasurement] = []
        self.max_history_size = config.get('max_sla_history', 10000)

        # Breach tracking
        self.active_breaches: Dict[str, datetime] = {}

    def _initialize_sla_targets(self) -> Dict[str, SLATarget]:
        """Initialize SLA targets from configuration"""
        default_targets = {
            'api_response_time': SLATarget(
                metric_name='api_response_time',
                target_value=200.0,  # ms
                comparison_type='less_than',
                warning_threshold=0.8,  # 80% of target (160ms)
                critical_threshold=2.0,  # 200% of target (400ms)
                measurement_window=5,  # 5 minutes
                description='API response time should be under 200ms'
            ),
            'prediction_accuracy': SLATarget(
                metric_name='prediction_accuracy',
                target_value=0.75,  # 75%
                comparison_type='greater_than',
                warning_threshold=0.9,  # 90% of target (67.5%)
                critical_threshold=0.8,  # 80% of target (60%)
                measurement_window=60,  # 60 minutes
                description='Prediction accuracy should be above 75%'
            ),
            'cache_hit_rate': SLATarget(
                metric_name='cache_hit_rate',
                target_value=0.8,  # 80%
                comparison_type='greater_than',
                warning_threshold=0.875,  # 87.5% of target (70%)
                critical_threshold=0.75,  # 75% of target (60%)
                measurement_window=15,  # 15 minutes
                description='Cache hit rate should be above 80%'
            ),
            'system_uptime': SLATarget(
                metric_name='system_uptime',
                target_value=0.999,  # 99.9%
                comparison_type='greater_than',
                warning_threshold=0.995,  # 99.5%
                critical_threshold=0.99,  # 99%
                measurement_window=60,  # 60 minutes
                description='System uptime should be above 99.9%'
            ),
            'error_rate': SLATarget(
                metric_name='error_rate',
                target_value=0.01,  # 1%
                comparison_type='less_than',
                warning_threshold=0.5,  # 0.5%
                critical_threshold=2.0,  # 2%
                measurement_window=15,  # 15 minutes
                description='Error rate should be below 1%'
            ),
            'database_response_time': SLATarget(
                metric_name='database_response_time',
                target_value=50.0,  # ms
                comparison_type='less_than',
                warning_threshold=0.8,  # 40ms
                critical_threshold=2.0,  # 100ms
                measurement_window=5,  # 5 minutes
                description='Database response time should be under 50ms'
            )
        }

        # Override with configuration values
        config_targets = self.config.get('sla_targets', {})
        for name, target in default_targets.items():
            if name in config_targets:
                config_data = config_targets[name]
                target.target_value = config_data.get('target_value', target.target_value)
                target.warning_threshold = config_data.get('warning_threshold', target.warning_threshold)
                target.critical_threshold = config_data.get('critical_threshold', target.critical_threshold)
                target.measurement_window = config_data.get('measurement_window', target.measurement_window)

        return default_targets

    async def measure_sla_compliance(self, metrics_data: List[Dict[str, Any]]) -> List[SLAMeasurement]:
        """Measure SLA compliance for current metrics"""
        measurements = []

        if not metrics_data:
            return measurements

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(metrics_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        current_time = datetime.utcnow()

        for target_name, target in self.sla_targets.items():
            if target.metric_name not in df.columns:
                continue

            # Get data for the measurement window
            window_start = current_time - timedelta(minutes=target.measurement_window)
            window_data = df[df['timestamp'] >= window_start]

            if len(window_data) == 0:
                continue

            # Calculate metric based on comparison type
            if target.comparison_type == 'less_than':
                measured_value = window_data[target.metric_name].mean()
                is_compliant = measured_value <= target.target_value
                compliance_percentage = min(1.0, target.target_value / measured_value) if measured_value > 0 else 1.0
            elif target.comparison_type == 'greater_than':
                measured_value = window_data[target.metric_name].mean()
                is_compliant = measured_value >= target.target_value
                compliance_percentage = min(1.0, measured_value / target.target_value) if target.target_value > 0 else 1.0
            else:  # equals
                measured_value = window_data[target.metric_name].mean()
                is_compliant = abs(measured_value - target.target_value) <= (target.target_value * 0.05)  # 5% tolerance
                compliance_percentage = 1.0 - abs(measured_value - target.target_value) / target.target_value

            # Determine status
            status = self._determine_sla_status(target, measured_value, compliance_percentage)

            # Calculate breach duration
            breach_duration = self._calculate_breach_duration(target_name, status, current_time)

            measurement = SLAMeasurement(
                timestamp=current_time,
                metric_name=target.metric_name,
                measured_value=measured_value,
                target_value=target.target_value,
                compliance_percentage=compliance_percentage,
                status=status,
                measurement_window=target.measurement_window,
                breach_duration=breach_duration
            )

            measurements.append(measurement)

        # Store measurements
        self.measurement_history.extend(measurements)
        await self._store_measurements(measurements)

        return measurements

    def _determine_sla_status(self, target: SLATarget, measured_value: float, compliance_percentage: float) -> SLAStatus:
        """Determine SLA status based on target and measured value"""
        if target.comparison_type == 'less_than':
            if measured_value <= target.target_value:
                return SLAStatus.MEETING
            elif measured_value <= target.target_value * target.critical_threshold:
                if measured_value <= target.target_value / target.warning_threshold:
                    return SLAStatus.WARNING
                else:
                    return SLAStatus.BREACHED
            else:
                return SLAStatus.CRITICAL
        elif target.comparison_type == 'greater_than':
            if measured_value >= target.target_value:
                return SLAStatus.MEETING
            elif measured_value >= target.target_value * target.critical_threshold:
                if measured_value >= target.target_value * target.warning_threshold:
                    return SLAStatus.WARNING
                else:
                    return SLAStatus.BREACHED
            else:
                return SLAStatus.CRITICAL
        else:  # equals
            tolerance = target.target_value * 0.05
            if abs(measured_value - target.target_value) <= tolerance:
                return SLAStatus.MEETING
            elif abs(measured_value - target.target_value) <= tolerance * 2:
                return SLAStatus.WARNING
            elif abs(measured_value - target.target_value) <= tolerance * 4:
                return SLAStatus.BREACHED
            else:
                return SLAStatus.CRITICAL

    def _calculate_breach_duration(self, target_name: str, status: SLAStatus, current_time: datetime) -> int:
        """Calculate how long a metric has been in breach"""
        if status == SLAStatus.MEETING:
            if target_name in self.active_breaches:
                del self.active_breaches[target_name]
            return 0

        if target_name not in self.active_breaches:
            self.active_breaches[target_name] = current_time

        breach_start = self.active_breaches[target_name]
        return int((current_time - breach_start).total_seconds() / 60)  # minutes

    async def _store_measurements(self, measurements: List[SLAMeasurement]):
        """Store SLA measurements in Redis"""
        try:
            for measurement in measurements:
                measurement_data = asdict(measurement)
                measurement_data['timestamp'] = measurement.timestamp.isoformat()
                measurement_data['status'] = measurement.status.value

                # Store individual measurement
                key = f"sla_measurement:{measurement.metric_name}:{measurement.timestamp.strftime('%Y%m%d_%H%M%S')}"
                self.redis_client.setex(key, 86400, json.dumps(measurement_data, default=str))

                # Add to measurement history list
                self.redis_client.lpush('sla_measurements', json.dumps(measurement_data, default=str))
                self.redis_client.ltrim('sla_measurements', 0, self.max_history_size - 1)

        except Exception as e:
            self.logger.error(f"Error storing SLA measurements: {e}")

    async def get_sla_status(self) -> Dict[str, Any]:
        """Get current SLA status summary"""
        if not self.measurement_history:
            return {'status': 'no_data'}

        # Get latest measurements for each metric
        latest_measurements = {}
        for measurement in reversed(self.measurement_history[-50:]):  # Check last 50 measurements
            if measurement.metric_name not in latest_measurements:
                latest_measurements[measurement.metric_name] = measurement

        # Calculate overall compliance
        if latest_measurements:
            overall_compliance = sum(m.compliance_percentage for m in latest_measurements.values()) / len(latest_measurements)
        else:
            overall_compliance = 0.0

        # Count statuses
        status_counts = {status.value: 0 for status in SLAStatus}
        for measurement in latest_measurements.values():
            status_counts[measurement.status.value] += 1

        # Determine overall status
        if status_counts['critical'] > 0:
            overall_status = 'critical'
        elif status_counts['breached'] > 0:
            overall_status = 'breached'
        elif status_counts['warning'] > 0:
            overall_status = 'warning'
        else:
            overall_status = 'meeting'

        return {
            'overall_status': overall_status,
            'overall_compliance': overall_compliance,
            'metrics': {
                name: {
                    'status': measurement.status.value,
                    'compliance_percentage': measurement.compliance_percentage,
                    'measured_value': measurement.measured_value,
                    'target_value': measurement.target_value,
                    'breach_duration': measurement.breach_duration
                }
                for name, measurement in latest_measurements.items()
            },
            'status_counts': status_counts,
            'active_breaches': len(self.active_breaches),
            'timestamp': datetime.utcnow().isoformat()
        }

    async def generate_sla_report(self, start_date: datetime, end_date: datetime) -> SLAReport:
        """Generate comprehensive SLA report for a period"""
        try:
            # Get measurements for the period
            period_measurements = [
                m for m in self.measurement_history
                if start_date <= m.timestamp <= end_date
            ]

            if not period_measurements:
                return SLAReport(
                    period_start=start_date,
                    period_end=end_date,
                    overall_compliance=0.0,
                    metrics={},
                    breaches=[],
                    improvements=[],
                    action_items=[],
                    trends={}
                )

            # Group measurements by metric
            metric_measurements = {}
            for measurement in period_measurements:
                if measurement.metric_name not in metric_measurements:
                    metric_measurements[measurement.metric_name] = []
                metric_measurements[measurement.metric_name].append(measurement)

            # Calculate metrics summary
            metrics_summary = {}
            all_compliance_values = []

            for metric_name, measurements in metric_measurements.items():
                compliance_values = [m.compliance_percentage for m in measurements]
                all_compliance_values.extend(compliance_values)

                # Count breaches
                breaches = [m for m in measurements if m.status in [SLAStatus.BREACHED, SLAStatus.CRITICAL]]
                breach_time = sum(m.breach_duration for m in breaches)

                # Calculate availability (time not in breach)
                total_time = int((end_date - start_date).total_seconds() / 60)  # minutes
                availability = max(0, (total_time - breach_time) / total_time) if total_time > 0 else 1.0

                metrics_summary[metric_name] = {
                    'average_compliance': np.mean(compliance_values),
                    'min_compliance': np.min(compliance_values),
                    'max_compliance': np.max(compliance_values),
                    'breach_count': len(breaches),
                    'total_breach_time': breach_time,
                    'availability_percentage': availability,
                    'trend': self._calculate_metric_trend(measurements),
                    'target_value': self.sla_targets[metric_name].target_value if metric_name in self.sla_targets else 0,
                    'measurements_count': len(measurements)
                }

            # Overall compliance
            overall_compliance = np.mean(all_compliance_values) if all_compliance_values else 0.0

            # Find all breaches
            breaches = [m for m in period_measurements if m.status in [SLAStatus.BREACHED, SLAStatus.CRITICAL]]

            # Generate improvements and action items
            improvements = self._identify_improvements(metrics_summary)
            action_items = self._generate_action_items(metrics_summary, breaches)

            # Calculate trends
            trends = {metric: summary['trend'] for metric, summary in metrics_summary.items()}

            return SLAReport(
                period_start=start_date,
                period_end=end_date,
                overall_compliance=overall_compliance,
                metrics=metrics_summary,
                breaches=breaches,
                improvements=improvements,
                action_items=action_items,
                trends=trends
            )

        except Exception as e:
            self.logger.error(f"Error generating SLA report: {e}")
            return SLAReport(
                period_start=start_date,
                period_end=end_date,
                overall_compliance=0.0,
                metrics={},
                breaches=[],
                improvements=[],
                action_items=[f"Error generating report: {e}"],
                trends={}
            )

    def _calculate_metric_trend(self, measurements: List[SLAMeasurement]) -> str:
        """Calculate trend direction for a metric"""
        if len(measurements) < 5:
            return 'insufficient_data'

        # Sort by timestamp
        measurements.sort(key=lambda x: x.timestamp)

        # Compare first half to second half
        mid_point = len(measurements) // 2
        first_half = measurements[:mid_point]
        second_half = measurements[mid_point:]

        first_avg = np.mean([m.compliance_percentage for m in first_half])
        second_avg = np.mean([m.compliance_percentage for m in second_half])

        change = (second_avg - first_avg) / first_avg if first_avg > 0 else 0

        if change > 0.05:
            return 'improving'
        elif change < -0.05:
            return 'degrading'
        else:
            return 'stable'

    def _identify_improvements(self, metrics_summary: Dict[str, Any]) -> List[str]:
        """Identify areas where SLA compliance has improved"""
        improvements = []

        for metric_name, summary in metrics_summary.items():
            if summary['trend'] == 'improving':
                improvements.append(
                    f"{metric_name.replace('_', ' ').title()} compliance improved "
                    f"(avg: {summary['average_compliance']:.1%})"
                )

            if summary['average_compliance'] > 0.95:
                improvements.append(
                    f"{metric_name.replace('_', ' ').title()} exceeded target "
                    f"({summary['average_compliance']:.1%} compliance)"
                )

        return improvements

    def _generate_action_items(self, metrics_summary: Dict[str, Any], breaches: List[SLAMeasurement]) -> List[str]:
        """Generate action items based on SLA performance"""
        action_items = []

        # Check for consistent underperformers
        for metric_name, summary in metrics_summary.items():
            if summary['average_compliance'] < 0.9:
                action_items.append(
                    f"Investigate {metric_name.replace('_', ' ')} performance "
                    f"(only {summary['average_compliance']:.1%} compliant)"
                )

            if summary['breach_count'] > 10:
                action_items.append(
                    f"Address frequent {metric_name.replace('_', ' ')} breaches "
                    f"({summary['breach_count']} incidents)"
                )

            if summary['trend'] == 'degrading':
                action_items.append(
                    f"Urgent: {metric_name.replace('_', ' ')} performance degrading"
                )

            if summary['availability_percentage'] < 0.99:
                action_items.append(
                    f"Improve {metric_name.replace('_', ' ')} availability "
                    f"(currently {summary['availability_percentage']:.2%})"
                )

        # Check for critical breaches
        critical_breaches = [b for b in breaches if b.status == SLAStatus.CRITICAL]
        if critical_breaches:
            action_items.append(
                f"Immediate attention required: {len(critical_breaches)} critical SLA breaches"
            )

        return action_items

    async def get_sla_compliance_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get SLA compliance history for a specific metric"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        history = []
        for measurement in self.measurement_history:
            if (measurement.metric_name == metric_name and
                measurement.timestamp >= cutoff):
                history.append({
                    'timestamp': measurement.timestamp.isoformat(),
                    'compliance_percentage': measurement.compliance_percentage,
                    'measured_value': measurement.measured_value,
                    'target_value': measurement.target_value,
                    'status': measurement.status.value,
                    'breach_duration': measurement.breach_duration
                })

        return sorted(history, key=lambda x: x['timestamp'])

    def get_sla_targets(self) -> Dict[str, Dict[str, Any]]:
        """Get current SLA targets configuration"""
        return {
            name: {
                'target_value': target.target_value,
                'comparison_type': target.comparison_type,
                'warning_threshold': target.warning_threshold,
                'critical_threshold': target.critical_threshold,
                'measurement_window': target.measurement_window,
                'description': target.description
            }
            for name, target in self.sla_targets.items()
        }

    async def update_sla_target(self, metric_name: str, target_updates: Dict[str, Any]) -> bool:
        """Update SLA target configuration"""
        try:
            if metric_name not in self.sla_targets:
                self.logger.error(f"SLA target {metric_name} not found")
                return False

            target = self.sla_targets[metric_name]

            # Update target values
            for field, value in target_updates.items():
                if hasattr(target, field):
                    setattr(target, field, value)
                else:
                    self.logger.warning(f"Unknown SLA target field: {field}")

            # Store updated configuration
            config_key = f"sla_target:{metric_name}"
            target_data = asdict(target)
            self.redis_client.setex(config_key, 86400 * 30, json.dumps(target_data))

            self.logger.info(f"Updated SLA target for {metric_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error updating SLA target: {e}")
            return False

    def get_breach_summary(self) -> Dict[str, Any]:
        """Get summary of active breaches"""
        current_time = datetime.utcnow()

        return {
            'active_breaches': len(self.active_breaches),
            'breach_details': {
                metric: {
                    'breach_start': breach_start.isoformat(),
                    'duration_minutes': int((current_time - breach_start).total_seconds() / 60)
                }
                for metric, breach_start in self.active_breaches.items()
            },
            'longest_breach': max([
                int((current_time - breach_start).total_seconds() / 60)
                for breach_start in self.active_breaches.values()
            ]) if self.active_breaches else 0
        }