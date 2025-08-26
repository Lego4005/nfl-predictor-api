"""
Monitoring dashboard for NFL Predictor API.
Provides real-time monitoring interface and metrics visualization.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure"""
    timestamp: datetime
    api_health: Dict[str, Any]
    cache_health: Dict[str, Any]
    system_health: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    alerts: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "api_health": self.api_health,
            "cache_health": self.cache_health,
            "system_health": self.system_health,
            "performance_metrics": self.performance_metrics,
            "alerts": self.alerts
        }


class MonitoringDashboard:
    """
    Real-time monitoring dashboard for NFL Predictor API.
    Aggregates health checks, metrics, and alerts into a unified view.
    """
    
    def __init__(
        self,
        health_checker=None,
        cache_monitor=None,
        update_interval: int = 30
    ):
        self.health_checker = health_checker
        self.cache_monitor = cache_monitor
        self.update_interval = update_interval
        
        # Dashboard state
        self.current_metrics: Optional[DashboardMetrics] = None
        self.metrics_history: List[DashboardMetrics] = []
        self.max_history_size = 288  # 24 hours at 5-minute intervals
        
        # Dashboard status
        self._dashboard_active = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Performance tracking
        self._request_counts = {"total": 0, "errors": 0, "success": 0}
        self._response_times = []
        self._last_reset_time = datetime.utcnow()
    
    async def start_dashboard(self):
        """Start the monitoring dashboard"""
        if self._dashboard_active:
            logger.warning("Dashboard is already active")
            return
        
        self._dashboard_active = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Monitoring dashboard started")
    
    async def stop_dashboard(self):
        """Stop the monitoring dashboard"""
        if not self._dashboard_active:
            return
        
        self._dashboard_active = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Monitoring dashboard stopped")
    
    async def _update_loop(self):
        """Main dashboard update loop"""
        logger.info("Dashboard update loop started")
        
        while self._dashboard_active:
            try:
                # Collect current metrics
                metrics = await self._collect_metrics()
                
                # Update current state
                self.current_metrics = metrics
                
                # Store in history
                self.metrics_history.append(metrics)
                
                # Limit history size
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]
                
                # Wait for next update
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(self.update_interval)
        
        logger.info("Dashboard update loop stopped")
    
    async def _collect_metrics(self) -> DashboardMetrics:
        """Collect current metrics from all sources"""
        timestamp = datetime.utcnow()
        
        # Initialize metrics
        api_health = {"status": "unknown", "components": {}}
        cache_health = {"status": "unknown", "details": {}}
        system_health = {"status": "unknown", "details": {}}
        performance_metrics = self._get_performance_metrics()
        alerts = []
        
        # Collect API health metrics
        if self.health_checker:
            try:
                health_report = await self.health_checker.check_all_components()
                
                # Extract API health
                api_components = {
                    name: data for name, data in health_report["components"].items()
                    if data.get("component_type") == "api_source"
                }
                
                api_health = {
                    "status": self._determine_component_status(api_components),
                    "components": api_components,
                    "avg_response_time": health_report["summary"].get("avg_api_response_time_ms")
                }
                
                # Extract cache health
                cache_components = {
                    name: data for name, data in health_report["components"].items()
                    if data.get("component_type") == "cache"
                }
                
                if cache_components:
                    cache_health = {
                        "status": self._determine_component_status(cache_components),
                        "details": list(cache_components.values())[0] if cache_components else {}
                    }
                
                # Extract system health
                system_components = {
                    name: data for name, data in health_report["components"].items()
                    if data.get("component_type") == "system"
                }
                
                if system_components:
                    system_health = {
                        "status": self._determine_component_status(system_components),
                        "details": list(system_components.values())[0] if system_components else {}
                    }
                
            except Exception as e:
                logger.error(f"Failed to collect health metrics: {e}")
        
        # Collect cache monitoring alerts
        if self.cache_monitor:
            try:
                active_alerts = self.cache_monitor.get_active_alerts()
                alerts.extend(active_alerts)
            except Exception as e:
                logger.error(f"Failed to collect cache alerts: {e}")
        
        return DashboardMetrics(
            timestamp=timestamp,
            api_health=api_health,
            cache_health=cache_health,
            system_health=system_health,
            performance_metrics=performance_metrics,
            alerts=alerts
        )
    
    def _determine_component_status(self, components: Dict[str, Any]) -> str:
        """Determine overall status from component statuses"""
        if not components:
            return "unknown"
        
        statuses = [comp.get("status", "unknown") for comp in components.values()]
        
        if "unhealthy" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        elif "unknown" in statuses:
            return "unknown"
        else:
            return "healthy"
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        now = datetime.utcnow()
        time_since_reset = (now - self._last_reset_time).total_seconds()
        
        # Calculate rates
        total_requests = self._request_counts["total"]
        error_rate = (self._request_counts["errors"] / total_requests * 100) if total_requests > 0 else 0
        success_rate = (self._request_counts["success"] / total_requests * 100) if total_requests > 0 else 0
        request_rate = total_requests / time_since_reset if time_since_reset > 0 else 0
        
        # Calculate average response time
        avg_response_time = sum(self._response_times) / len(self._response_times) if self._response_times else 0
        
        return {
            "request_rate_per_second": round(request_rate, 2),
            "total_requests": total_requests,
            "error_rate_percent": round(error_rate, 2),
            "success_rate_percent": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
            "time_window_seconds": round(time_since_reset, 0)
        }
    
    def record_request(self, success: bool, response_time_ms: float):
        """Record API request metrics"""
        self._request_counts["total"] += 1
        
        if success:
            self._request_counts["success"] += 1
        else:
            self._request_counts["errors"] += 1
        
        self._response_times.append(response_time_ms)
        
        # Limit response time history
        if len(self._response_times) > 1000:
            self._response_times = self._response_times[-1000:]
    
    def reset_performance_metrics(self):
        """Reset performance metrics counters"""
        self._request_counts = {"total": 0, "errors": 0, "success": 0}
        self._response_times = []
        self._last_reset_time = datetime.utcnow()
    
    def get_current_dashboard(self) -> Dict[str, Any]:
        """Get current dashboard state"""
        if not self.current_metrics:
            return {
                "status": "initializing",
                "message": "Dashboard is collecting initial metrics",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        dashboard_data = self.current_metrics.to_dict()
        
        # Add dashboard metadata
        dashboard_data["dashboard_info"] = {
            "active": self._dashboard_active,
            "update_interval_seconds": self.update_interval,
            "metrics_history_count": len(self.metrics_history),
            "last_update": self.current_metrics.timestamp.isoformat()
        }
        
        return dashboard_data
    
    def get_dashboard_history(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get dashboard metrics history"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        recent_metrics = [
            metrics for metrics in self.metrics_history
            if metrics.timestamp > cutoff_time
        ]
        
        return [metrics.to_dict() for metrics in recent_metrics]
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary with key metrics"""
        if not self.current_metrics:
            return {"status": "no_data"}
        
        current = self.current_metrics
        
        # Count alerts by severity
        alert_counts = {"critical": 0, "warning": 0, "info": 0}
        for alert in current.alerts:
            level = alert.get("level", "info")
            alert_counts[level] = alert_counts.get(level, 0) + 1
        
        # Determine overall system status
        statuses = [
            current.api_health.get("status", "unknown"),
            current.cache_health.get("status", "unknown"),
            current.system_health.get("status", "unknown")
        ]
        
        if "unhealthy" in statuses:
            overall_status = "unhealthy"
        elif "degraded" in statuses:
            overall_status = "degraded"
        elif "unknown" in statuses:
            overall_status = "unknown"
        else:
            overall_status = "healthy"
        
        return {
            "timestamp": current.timestamp.isoformat(),
            "overall_status": overall_status,
            "component_status": {
                "api_sources": current.api_health.get("status", "unknown"),
                "cache": current.cache_health.get("status", "unknown"),
                "system": current.system_health.get("status", "unknown")
            },
            "performance": {
                "request_rate": current.performance_metrics.get("request_rate_per_second", 0),
                "error_rate": current.performance_metrics.get("error_rate_percent", 0),
                "avg_response_time": current.performance_metrics.get("avg_response_time_ms", 0)
            },
            "alerts": {
                "total": len(current.alerts),
                "critical": alert_counts["critical"],
                "warning": alert_counts["warning"],
                "info": alert_counts["info"]
            },
            "dashboard_active": self._dashboard_active
        }
    
    def get_api_status_overview(self) -> Dict[str, Any]:
        """Get overview of API source statuses"""
        if not self.current_metrics:
            return {"status": "no_data"}
        
        api_components = self.current_metrics.api_health.get("components", {})
        
        overview = {
            "timestamp": self.current_metrics.timestamp.isoformat(),
            "total_apis": len(api_components),
            "status_summary": {"healthy": 0, "degraded": 0, "unhealthy": 0, "unknown": 0},
            "apis": {}
        }
        
        for api_name, api_data in api_components.items():
            status = api_data.get("status", "unknown")
            overview["status_summary"][status] += 1
            
            overview["apis"][api_name] = {
                "status": status,
                "response_time_ms": api_data.get("response_time_ms"),
                "message": api_data.get("message", ""),
                "last_check": api_data.get("timestamp")
            }
        
        return overview
    
    def export_dashboard_data(self, hours: int = 24) -> str:
        """Export dashboard data as JSON"""
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "export_period_hours": hours,
            "current_metrics": self.current_metrics.to_dict() if self.current_metrics else None,
            "metrics_history": self.get_dashboard_history(hours),
            "dashboard_info": {
                "active": self._dashboard_active,
                "update_interval": self.update_interval,
                "total_history_points": len(self.metrics_history)
            }
        }
        
        return json.dumps(export_data, indent=2)


# Dashboard middleware for FastAPI
class DashboardMiddleware:
    """Middleware to collect request metrics for dashboard"""
    
    def __init__(self, dashboard: MonitoringDashboard):
        self.dashboard = dashboard
    
    async def __call__(self, request, call_next):
        """Process request and collect metrics"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Determine if request was successful
            success = 200 <= response.status_code < 400
            
            # Record metrics
            self.dashboard.record_request(success, response_time_ms)
            
            return response
            
        except Exception as e:
            # Record failed request
            response_time_ms = (time.time() - start_time) * 1000
            self.dashboard.record_request(False, response_time_ms)
            raise e


def create_monitoring_dashboard(
    health_checker=None,
    cache_monitor=None,
    update_interval: int = 30
) -> MonitoringDashboard:
    """Create monitoring dashboard with default configuration"""
    return MonitoringDashboard(health_checker, cache_monitor, update_interval)