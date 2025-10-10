"""
Performance Monitoring API Endpoints

Provides REST API endpoints for accessing performance monitoring data,
dashboards, and alerts for the Expert Council Betting System.

Requirements: 3.3 - Performance monitoring and alerting
"""

fromort APIRouter, HTTPException, Query, Depends
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ..services.performance_monitoring_complete import (
    PerformanceMonitoringService, MetricType, AlertSeverity
)

logger = logging.getLogger(__name__)

# Global monitoring service instance
monitoring_service = None

def get_monitoring_service() -> PerformanceMonitoringService:
    """Get or create monitoring service instance"""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = PerformanceMonitoringService()
    return monitoring_service

# Create router
router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

@router.get("/health")
async def monitoring_health():
    """Get monitoring service health status"""
    try:
        service = get_monitoring_service()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring_active": service.monitoring_active,
            "metrics_count": len(service.metrics),
            "alert_rules_count": len(service.alert_rules),
            "active_alerts_count": len([a for a in service.alerts.values() if a.is_active])
        }
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard")
async def get_dashboard(
    service: Optional[str] = Query(None, description="Filter by service name"),
    time_range_minutes: int = Query(60, ge=1, le=1440, description="Time range in minutes")
):
    """Get dashboard data for visualization"""
    try:
        monitoring = get_monitoring_service()
        dashboard_data = monitoring.get_dashboard_data(service, time_range_minutes)

        if 'error' in dashboard_data:
            raise HTTPException(status_code=500, detail=dashboard_data['error'])

        return dashboard_data
    except Exception as e:
        logger.error(f"Dashboard data retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_metrics(
    service: Optional[str] = Query(None, description="Filter by service name"),
    metric_type: Optional[str] = Query(None, description="Filter by metric type")
):
    """Get all metrics with optional filtering"""
    try:
        monitoring = get_monitoring_service()

        with monitoring.lock:
            metrics = list(monitoring.metrics.values())

            # Apply filters
            if service:
                metrics = [m for m in metrics if m.service == service]

            if metric_type:
                try:
                    filter_type = MetricType(metric_type.lower())
                    metrics = [m for m in metrics if m.metric_type == filter_type]
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid metric type: {metric_type}")

            # Convert to dict format
            metrics_data = []
            for metric in metrics:
                metric_data = {
                    'name': metric.name,
                    'type': metric.metric_type.value,
                    'description': metric.description,
                    'unit': metric.unit,
                    'service': metric.service,
                    'current_value': metric.current_value,
                    'min_value': metric.min_value,
                    'max_value': metric.max_value,
                    'avg_value': metric.avg_value,
                    'data_points': len(metric.points),
                    'created_at': metric.created_at.isoformat(),
                    'last_updated': metric.last_updated.isoformat()
                }
                metrics_data.append(metric_data)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_metrics': len(metrics_data),
            'filters': {
                'service': service,
                'metric_type': metric_type
            },
            'metrics': metrics_data
        }
    except Exception as e:
        logger.error(f"Metrics retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics/{metric_name}")
async def record_metric(
    metric_name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None
):
    """Record a metric value"""
    try:
        monitoring = get_monitoring_service()
        success = monitoring.record_metric(metric_name, value, tags)

        if not success:
            raise HTTPException(status_code=400, detail=f"Failed to record metric: {metric_name}")

        return {
            'success': True,
            'metric_name': metric_name,
            'value': value,
            'tags': tags,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Metric recording failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/alerts")
async def get_alerts(
    service: Optional[str] = Query(None, description="Filter by service name"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    active_only: bool = Query(True, description="Show only active alerts")
):
    """Get alerts with optional filtering"""
    try:
        monitoring = get_monitoring_service()

        with monitoring.lock:
            alerts = list(monitoring.alerts.values())

            # Apply filters
            if active_only:
                alerts = [a for a in alerts if a.is_active]

            if service:
                alerts = [a for a in alerts if a.service == service]

            if severity:
                try:
                    filter_severity = AlertSeverity(severity.lower())
                    alerts = [a for a in alerts if a.severity == filter_severity]
                except ValueError:
                    raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

            # Sort by severity and timestamp
            severity_order = {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.ERROR: 1,
                AlertSeverity.WARNING: 2,
                AlertSeverity.INFO: 3
            }

            alerts.sort(key=lambda a: (severity_order[a.severity], a.triggered_at), reverse=True)

            # Convert to dict format
            alerts_data = [alert.to_dict() for alert in alerts]

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_alerts': len(alerts_data),
            'filters': {
                'service': service,
                'severity': severity,
                'active_only': active_only
            },
            'alerts': alerts_data
        }
    except Exception as e:
        logger.error(f"Alerts retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    acknowledgment: str,
    acknowledged_by: str
):
    """Acknowledge an alert"""
    try:
        monitoring = get_monitoring_service()
        success = monitoring.acknowledge_alert(alert_id, acknowledgment, acknowledged_by)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            'success': True,
            'alert_id': alert_id,
            'acknowledgment': acknowledgment,
            'acknowledged_by': acknowledged_by,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Alert acknowledgment failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    try:
        monitoring = get_monitoring_service()
        success = monitoring.resolve_alert(alert_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Alert not found: {alert_id}")

        return {
            'success': True,
            'alert_id': alert_id,
            'resolved_at': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Alert resolution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_summary():
    """Get performance summary against targets"""
    try:
        monitoring = get_monitoring_service()
        summary = monitoring.get_performance_summary()

        if 'error' in summary:
            raise HTTPException(status_code=500, detail=summary['error'])

        return summary
    except Exception as e:
        logger.error(f"Performance summary retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/services")
async def get_services():
    """Get list of monitored services"""
    try:
        monitoring = get_monitoring_service()

        with monitoring.lock:
            services = set()
            for metric in monitoring.metrics.values():
                if metric.service:
                    services.add(metric.service)

            service_data = []
            for service_name in sorted(services):
                service_metrics = [m for m in monitoring.metrics.values() if m.service == service_name]
                service_alerts = [a for a in monitoring.alerts.values() if a.service == service_name and a.is_active]

                service_data.append({
                    'name': service_name,
                    'metrics_count': len(service_metrics),
                    'active_alerts_count': len(service_alerts),
                    'last_updated': max([m.last_updated for m in service_metrics]).isoformat() if service_metrics else None
                })

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_services': len(service_data),
            'services': service_data
        }
    except Exception as e:
        logger.error(f"Services retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/targets")
async def get_performance_targets():
    """Get performance targets and SLA thresholds"""
    try:
        monitoring = get_monitoring_service()

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'performance_targets': monitoring.performance_targets,
            'alert_rules': {
                rule_id: {
                    'metric_name': rule.metric_name,
                    'service': rule.service,
                    'condition': rule.condition,
                    'threshold': rule.threshold,
                    'severity': rule.severity.value,
                    'is_enabled': rule.is_enabled
                }
                for rule_id, rule in monitoring.alert_rules.items()
            }
        }
    except Exception as e:
        logger.error(f"Performance targets retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Convenience endpoints for specific services

@router.get("/vector-retrieval")
async def get_vector_retrieval_metrics():
    """Get vector retrieval specific metrics"""
    return await get_dashboard(service="memory_retrieval", time_range_minutes=60)

@router.get("/expert-prediction")
async def get_expert_prediction_metrics():
    """Get expert prediction specific metrics"""
    return await get_dashboard(service="expert_prediction", time_range_minutes=60)

@router.get("/api-performance")
async def get_api_performance_metrics():
    """Get API performance specific metrics"""
    return await get_dashboard(service="api", time_range_minutes=60)

@router.get("/council-selection")
async def get_council_selection_metrics():
    """Get council selection specific metrics"""
    return await get_dashboard(service="council_selection", time_range_minutes=60)
