"""
Automated Monitoring and Alerting System
Implements continuous performance tracking and automated alert generation
for the NFL prediction platform comprehensive testing framework.
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import json
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(Enum):
    PERFORMANCE_DEGRADATION = "performance_degradation"
    DATA_QUALITY_ISSUE = "data_quality_issue"
    SYSTEM_ERROR = "system_error"
    COUNCIL_INSTABILITY = "council_instability"
    PREDICTION_ANOMALY = "prediction_anomaly"
    LEARNING_FAILURE = "learning_failure"
    INFRASTRUCTURE_ISSUE = "infrastructure_issue"

@dataclass
class Alert:
    alert_id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source_component: str
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False

@dataclass
class AlertThreshold:
    metric_name: str
    threshold_value: float
    comparison: str  # 'greater_than', 'less_than'
    severity: AlertSeverity
    alert_type: AlertType
    description: str
    enabled: bool = True

@dataclass
class SystemHealthMetrics:
    timestamp: datetime
    overall_health_score: float
    component_health: Dict[str, float]
    active_alerts: int
    critical_alerts: int
    expert_performance_avg: float
    council_stability_score: float
    data_quality_score: float
    api_response_time: float

class AlertManager:
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: List[Callable] = []
    
    def add_notification_channel(self, channel: Callable):
        self.notification_channels.append(channel)
    
    async def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        source_component: str,
        metric_value: Optional[float] = None,
        threshold_value: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Alert:
        alert_id = f"{alert_type.value}_{source_component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source_component=source_component,
            metric_value=metric_value,
            threshold_value=threshold_value,
            context=context or {}
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Send notifications
        await self._send_notifications(alert)
        
        logger.warning(f"Alert created: {severity.value.upper()} - {title}")
        return alert
    
    async def resolve_alert(self, alert_id: str) -> bool:
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")
            return True
        return False
    
    async def _send_notifications(self, alert: Alert):
        for channel in self.notification_channels:
            try:
                await channel(alert)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

class MonitoringRule:
    def __init__(
        self,
        rule_id: str,
        name: str,
        check_function: Callable,
        thresholds: List[AlertThreshold],
        check_interval: timedelta,
        enabled: bool = True
    ):
        self.rule_id = rule_id
        self.name = name
        self.check_function = check_function
        self.thresholds = thresholds
        self.check_interval = check_interval
        self.enabled = enabled
        self.last_check: Optional[datetime] = None
        self.consecutive_failures = 0

class SystemMonitor:
    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.alert_manager = AlertManager()
        self.monitoring_rules: Dict[str, MonitoringRule] = {}
        self.health_history: deque = deque(maxlen=1000)
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        self._setup_default_thresholds()
        self._setup_default_monitoring_rules()
    
    def _setup_default_thresholds(self):
        self.default_thresholds = [
            AlertThreshold(
                metric_name="expert_accuracy",
                threshold_value=0.5,
                comparison="less_than",
                severity=AlertSeverity.HIGH,
                alert_type=AlertType.PERFORMANCE_DEGRADATION,
                description="Expert accuracy below 50%"
            ),
            AlertThreshold(
                metric_name="api_response_time",
                threshold_value=0.5,
                comparison="greater_than",
                severity=AlertSeverity.MEDIUM,
                alert_type=AlertType.INFRASTRUCTURE_ISSUE,
                description="API response time above 500ms"
            ),
            AlertThreshold(
                metric_name="data_completeness",
                threshold_value=0.95,
                comparison="less_than",
                severity=AlertSeverity.MEDIUM,
                alert_type=AlertType.DATA_QUALITY_ISSUE,
                description="Data completeness below 95%"
            ),
            AlertThreshold(
                metric_name="council_volatility",
                threshold_value=0.4,
                comparison="greater_than",
                severity=AlertSeverity.MEDIUM,
                alert_type=AlertType.COUNCIL_INSTABILITY,
                description="Council selection too volatile"
            )
        ]
    
    def _setup_default_monitoring_rules(self):
        self.add_monitoring_rule(MonitoringRule(
            rule_id="expert_performance_check",
            name="Expert Performance Monitor",
            check_function=self._check_expert_performance,
            thresholds=[t for t in self.default_thresholds if 'expert' in t.metric_name],
            check_interval=timedelta(minutes=15)
        ))
        
        self.add_monitoring_rule(MonitoringRule(
            rule_id="system_health_check",
            name="System Health Monitor",
            check_function=self._check_system_health,
            thresholds=[t for t in self.default_thresholds if 'api' in t.metric_name],
            check_interval=timedelta(minutes=5)
        ))
        
        self.add_monitoring_rule(MonitoringRule(
            rule_id="data_quality_check",
            name="Data Quality Monitor",
            check_function=self._check_data_quality,
            thresholds=[t for t in self.default_thresholds if 'data' in t.metric_name],
            check_interval=timedelta(minutes=10)
        ))
    
    def add_monitoring_rule(self, rule: MonitoringRule):
        self.monitoring_rules[rule.rule_id] = rule
        logger.info(f"Added monitoring rule: {rule.name}")
    
    async def start_monitoring(self):
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("System monitoring started")
    
    async def stop_monitoring(self):
        self.is_monitoring = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self):
        try:
            while self.is_monitoring:
                for rule in self.monitoring_rules.values():
                    if not rule.enabled:
                        continue
                    
                    now = datetime.now()
                    if (rule.last_check is None or 
                        (now - rule.last_check) >= rule.check_interval):
                        
                        try:
                            await self._execute_monitoring_rule(rule)
                            rule.last_check = now
                            rule.consecutive_failures = 0
                        except Exception as e:
                            rule.consecutive_failures += 1
                            logger.error(f"Monitoring rule {rule.rule_id} failed: {e}")
                
                await self._generate_health_snapshot()
                await asyncio.sleep(60)
                
        except asyncio.CancelledError:
            logger.info("Monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Monitoring loop error: {e}")
            self.is_monitoring = False
    
    async def _execute_monitoring_rule(self, rule: MonitoringRule):
        metrics = await rule.check_function()
        
        for threshold in rule.thresholds:
            if not threshold.enabled:
                continue
            
            metric_value = metrics.get(threshold.metric_name)
            if metric_value is None:
                continue
            
            threshold_violated = False
            if threshold.comparison == "greater_than" and metric_value > threshold.threshold_value:
                threshold_violated = True
            elif threshold.comparison == "less_than" and metric_value < threshold.threshold_value:
                threshold_violated = True
            
            if threshold_violated:
                await self.alert_manager.create_alert(
                    threshold.alert_type,
                    threshold.severity,
                    f"Threshold Violation: {threshold.metric_name}",
                    f"{threshold.description}. Current: {metric_value}, Threshold: {threshold.threshold_value}",
                    rule.rule_id,
                    metric_value=metric_value,
                    threshold_value=threshold.threshold_value
                )
    
    async def _check_expert_performance(self) -> Dict[str, float]:
        # Mock implementation - integrate with actual expert system
        return {
            'expert_accuracy': 0.65,
            'expert_consistency': 0.75,
            'confidence_calibration': 0.70
        }
    
    async def _check_system_health(self) -> Dict[str, float]:
        # Mock implementation - integrate with actual system metrics
        return {
            'api_response_time': 0.15,
            'prediction_generation_time': 0.04,
            'system_uptime': 0.999,
            'error_rate': 0.005
        }
    
    async def _check_data_quality(self) -> Dict[str, float]:
        # Mock implementation - integrate with data pipeline
        return {
            'data_completeness': 0.98,
            'data_freshness': 180,
            'data_accuracy': 0.97,
            'source_availability': 0.999
        }
    
    async def _generate_health_snapshot(self):
        try:
            all_metrics = {}
            for rule in self.monitoring_rules.values():
                if rule.enabled:
                    try:
                        rule_metrics = await rule.check_function()
                        all_metrics.update(rule_metrics)
                    except Exception:
                        pass
            
            component_health = {
                'experts': all_metrics.get('expert_accuracy', 0.5),
                'system': 1.0 - min(all_metrics.get('api_response_time', 0.2) / 0.5, 1.0),
                'data': all_metrics.get('data_completeness', 0.95),
                'council': 1.0 - all_metrics.get('council_volatility', 0.2)
            }
            
            overall_health = sum(component_health.values()) / len(component_health)
            
            snapshot = SystemHealthMetrics(
                timestamp=datetime.now(),
                overall_health_score=overall_health,
                component_health=component_health,
                active_alerts=len(self.alert_manager.active_alerts),
                critical_alerts=len([a for a in self.alert_manager.active_alerts.values() 
                                   if a.severity == AlertSeverity.CRITICAL]),
                expert_performance_avg=all_metrics.get('expert_accuracy', 0.5),
                council_stability_score=1.0 - all_metrics.get('council_volatility', 0.2),
                data_quality_score=component_health['data'],
                api_response_time=all_metrics.get('api_response_time', 0.2)
            )
            
            self.health_history.append(snapshot)
            
            if self.supabase:
                await self._store_health_snapshot(snapshot)
                
        except Exception as e:
            logger.error(f"Failed to generate health snapshot: {e}")
    
    async def _store_health_snapshot(self, snapshot: SystemHealthMetrics):
        try:
            record = {
                'timestamp': snapshot.timestamp.isoformat(),
                'overall_health_score': snapshot.overall_health_score,
                'component_health': json.dumps(snapshot.component_health),
                'active_alerts': snapshot.active_alerts,
                'critical_alerts': snapshot.critical_alerts,
                'expert_performance_avg': snapshot.expert_performance_avg,
                'council_stability_score': snapshot.council_stability_score,
                'data_quality_score': snapshot.data_quality_score,
                'api_response_time': snapshot.api_response_time
            }
            
            self.supabase.table('system_health_history').insert(record).execute()
            
        except Exception as e:
            logger.warning(f"Failed to store health snapshot: {e}")
    
    def get_current_health_status(self) -> Dict[str, Any]:
        if not self.health_history:
            return {'status': 'unknown', 'message': 'No health data available'}
        
        latest_snapshot = self.health_history[-1]
        health_score = latest_snapshot.overall_health_score
        
        if health_score >= 0.9:
            status = "excellent"
        elif health_score >= 0.8:
            status = "good"
        elif health_score >= 0.7:
            status = "fair"
        elif health_score >= 0.5:
            status = "poor"
        else:
            status = "critical"
        
        return {
            'status': status,
            'health_score': health_score,
            'timestamp': latest_snapshot.timestamp.isoformat(),
            'component_health': latest_snapshot.component_health,
            'active_alerts': latest_snapshot.active_alerts,
            'critical_alerts': latest_snapshot.critical_alerts,
            'monitoring_status': 'active' if self.is_monitoring else 'inactive'
        }
    
    def get_alert_summary(self, hours: int = 24) -> Dict[str, Any]:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        period_alerts = [
            alert for alert in self.alert_manager.alert_history
            if alert.timestamp >= cutoff_time
        ]
        
        severity_counts = defaultdict(int)
        for alert in period_alerts:
            severity_counts[alert.severity.value] += 1
        
        return {
            'period_hours': hours,
            'total_alerts': len(period_alerts),
            'active_alerts': len(self.alert_manager.active_alerts),
            'by_severity': dict(severity_counts),
            'resolution_rate': len([a for a in period_alerts if a.resolved]) / max(len(period_alerts), 1)
        }

# Notification channels
class EmailNotificationChannel:
    def __init__(self, recipients: List[str]):
        self.recipients = recipients
    
    async def __call__(self, alert: Alert):
        # Mock email notification
        logger.info(f"Email notification: {alert.title} to {', '.join(self.recipients)}")

class WebhookNotificationChannel:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    async def __call__(self, alert: Alert):
        # Mock webhook notification
        logger.info(f"Webhook notification: {alert.title} to {self.webhook_url}")

async def setup_monitoring_system() -> SystemMonitor:
    monitor = SystemMonitor()
    
    # Setup notification channels
    email_channel = EmailNotificationChannel(["admin@nflpredictor.com"])
    webhook_channel = WebhookNotificationChannel("https://hooks.slack.com/webhook")
    
    monitor.alert_manager.add_notification_channel(email_channel)
    monitor.alert_manager.add_notification_channel(webhook_channel)
    
    await monitor.start_monitoring()
    return monitor