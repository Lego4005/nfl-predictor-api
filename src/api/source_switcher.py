"""
Intelligent source switching logic for fallback data source management.
Handles priority management, health tracking, and user notifications for source switching.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

from .client_manager import APIClientManager, DataSource, APIResponse, ErrorType
from ..notifications.notification_service import NotificationService

logger = logging.getLogger(__name__)


class SourcePriority(Enum):
    """Priority levels for data sources"""
    PRIMARY = 1
    SECONDARY = 2
    FALLBACK = 3
    EMERGENCY = 4


class SourceHealth(Enum):
    """Health status for data sources"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"


@dataclass
class SourceMetrics:
    """Metrics for tracking source performance"""
    success_count: int = 0
    error_count: int = 0
    total_requests: int = 0
    avg_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None
    consecutive_errors: int = 0
    consecutive_successes: int = 0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.success_count / self.total_requests) * 100
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.error_count / self.total_requests) * 100


@dataclass
class SourceConfig:
    """Configuration for source switching behavior"""
    source: DataSource
    priority: SourcePriority
    max_consecutive_errors: int = 3
    health_check_interval: int = 300  # seconds
    degraded_threshold: float = 70.0  # success rate percentage
    unhealthy_threshold: float = 50.0  # success rate percentage
    timeout_threshold: float = 10.0  # seconds
    enabled: bool = True


class SourceSwitcher:
    """
    Intelligent source switching logic with health tracking and priority management.
    Manages fallback routing between data sources based on performance and availability.
    """
    
    def __init__(self, client_manager: APIClientManager, notification_service: NotificationService):
        self.client_manager = client_manager
        self.notification_service = notification_service
        self.source_configs: Dict[DataSource, SourceConfig] = {}
        self.source_metrics: Dict[DataSource, SourceMetrics] = {}
        self.source_health: Dict[DataSource, SourceHealth] = {}
        self.last_health_check: Dict[DataSource, datetime] = {}
        self.active_notifications: Dict[DataSource, List[str]] = {}
        self._initialize_source_configs()
    
    def _initialize_source_configs(self):
        """Initialize source configurations with priorities and thresholds"""
        # Primary sources (betting data)
        self.source_configs[DataSource.ODDS_API] = SourceConfig(
            source=DataSource.ODDS_API,
            priority=SourcePriority.PRIMARY,
            max_consecutive_errors=2,
            degraded_threshold=80.0,
            unhealthy_threshold=60.0
        )
        
        self.source_configs[DataSource.SPORTSDATA_IO] = SourceConfig(
            source=DataSource.SPORTSDATA_IO,
            priority=SourcePriority.PRIMARY,
            max_consecutive_errors=2,
            degraded_threshold=80.0,
            unhealthy_threshold=60.0
        )
        
        # Secondary sources (official data)
        self.source_configs[DataSource.NFL_API] = SourceConfig(
            source=DataSource.NFL_API,
            priority=SourcePriority.SECONDARY,
            max_consecutive_errors=3,
            degraded_threshold=75.0,
            unhealthy_threshold=55.0
        )
        
        # Fallback sources (basic data)
        self.source_configs[DataSource.ESPN_API] = SourceConfig(
            source=DataSource.ESPN_API,
            priority=SourcePriority.FALLBACK,
            max_consecutive_errors=4,
            degraded_threshold=70.0,
            unhealthy_threshold=50.0
        )
        
        self.source_configs[DataSource.RAPID_API] = SourceConfig(
            source=DataSource.RAPID_API,
            priority=SourcePriority.EMERGENCY,
            max_consecutive_errors=5,
            degraded_threshold=65.0,
            unhealthy_threshold=45.0
        )
        
        # Initialize metrics and health for all sources
        for source in self.source_configs:
            self.source_metrics[source] = SourceMetrics()
            self.source_health[source] = SourceHealth.HEALTHY
            self.last_health_check[source] = datetime.utcnow()
            self.active_notifications[source] = []
    
    def _calculate_source_health(self, source: DataSource) -> SourceHealth:
        """Calculate health status based on metrics and configuration"""
        config = self.source_configs[source]
        metrics = self.source_metrics[source]
        
        # Check if source is disabled
        if not config.enabled:
            return SourceHealth.OFFLINE
        
        # Check consecutive errors
        if metrics.consecutive_errors >= config.max_consecutive_errors:
            return SourceHealth.OFFLINE
        
        # Check success rate thresholds
        if metrics.total_requests >= 5:  # Need minimum requests for meaningful stats
            if metrics.success_rate < config.unhealthy_threshold:
                return SourceHealth.UNHEALTHY
            elif metrics.success_rate < config.degraded_threshold:
                return SourceHealth.DEGRADED
        
        # Check response time
        if metrics.avg_response_time > config.timeout_threshold:
            return SourceHealth.DEGRADED
        
        # Check recent errors
        if metrics.last_error and metrics.last_success:
            if metrics.last_error > metrics.last_success:
                time_since_error = datetime.utcnow() - metrics.last_error
                if time_since_error < timedelta(minutes=5):
                    return SourceHealth.DEGRADED
        
        return SourceHealth.HEALTHY
    
    def _update_source_metrics(self, source: DataSource, success: bool, response_time: float = 0.0):
        """Update metrics for a source based on request outcome"""
        metrics = self.source_metrics[source]
        metrics.total_requests += 1
        
        if success:
            metrics.success_count += 1
            metrics.consecutive_successes += 1
            metrics.consecutive_errors = 0
            metrics.last_success = datetime.utcnow()
        else:
            metrics.error_count += 1
            metrics.consecutive_errors += 1
            metrics.consecutive_successes = 0
            metrics.last_error = datetime.utcnow()
        
        # Update average response time (simple moving average)
        if metrics.total_requests == 1:
            metrics.avg_response_time = response_time
        else:
            # Weighted average favoring recent requests
            weight = 0.2
            metrics.avg_response_time = (
                (1 - weight) * metrics.avg_response_time + 
                weight * response_time
            )
        
        # Update health status
        old_health = self.source_health[source]
        new_health = self._calculate_source_health(source)
        self.source_health[source] = new_health
        
        # Generate notifications for health changes
        if old_health != new_health:
            self._notify_health_change(source, old_health, new_health)
    
    def _notify_health_change(self, source: DataSource, old_health: SourceHealth, new_health: SourceHealth):
        """Generate notifications for source health changes"""
        source_name = source.value.replace('_', ' ').title()
        
        if new_health == SourceHealth.OFFLINE:
            message = f"{source_name} is currently offline. Switching to backup sources."
            notification_type = "error"
        elif new_health == SourceHealth.UNHEALTHY:
            message = f"{source_name} is experiencing issues. Using alternative sources when possible."
            notification_type = "warning"
        elif new_health == SourceHealth.DEGRADED:
            message = f"{source_name} performance is degraded. Monitoring closely."
            notification_type = "warning"
        elif new_health == SourceHealth.HEALTHY and old_health != SourceHealth.HEALTHY:
            message = f"{source_name} has recovered and is operating normally."
            notification_type = "success"
        else:
            return  # No notification needed
        
        notification = self.notification_service.create_source_notification(
            source=source.value,
            message=message,
            notification_type=notification_type,
            retryable=new_health != SourceHealth.OFFLINE
        )
        
        # Track active notifications to avoid spam
        notification_key = f"{source.value}:{new_health.value}"
        if notification_key not in self.active_notifications[source]:
            self.active_notifications[source].append(notification_key)
            logger.info(f"Source health change: {source_name} {old_health.value} -> {new_health.value}")
    
    def get_sources_by_priority(self, data_type: str = "game_predictions") -> List[DataSource]:
        """
        Get sources ordered by priority and health for specific data type.
        Filters out offline sources and orders by priority and health.
        """
        # Define which sources support which data types
        source_capabilities = {
            "game_predictions": [
                DataSource.ODDS_API, DataSource.SPORTSDATA_IO, 
                DataSource.NFL_API, DataSource.ESPN_API, DataSource.RAPID_API
            ],
            "ats_predictions": [
                DataSource.ODDS_API, DataSource.NFL_API, 
                DataSource.ESPN_API, DataSource.RAPID_API
            ],
            "totals_predictions": [
                DataSource.ODDS_API, DataSource.NFL_API, 
                DataSource.ESPN_API, DataSource.RAPID_API
            ],
            "prop_bets": [
                DataSource.SPORTSDATA_IO, DataSource.RAPID_API
            ],
            "fantasy_picks": [
                DataSource.SPORTSDATA_IO, DataSource.RAPID_API
            ]
        }
        
        # Get sources that support this data type
        capable_sources = source_capabilities.get(data_type, list(self.source_configs.keys()))
        
        # Filter and sort sources
        available_sources = []
        
        for source in capable_sources:
            if source not in self.source_configs:
                continue
                
            config = self.source_configs[source]
            health = self.source_health[source]
            
            # Skip offline sources
            if health == SourceHealth.OFFLINE or not config.enabled:
                continue
            
            # Add source with priority and health score
            health_score = {
                SourceHealth.HEALTHY: 3,
                SourceHealth.DEGRADED: 2,
                SourceHealth.UNHEALTHY: 1
            }.get(health, 0)
            
            priority_score = {
                SourcePriority.PRIMARY: 4,
                SourcePriority.SECONDARY: 3,
                SourcePriority.FALLBACK: 2,
                SourcePriority.EMERGENCY: 1
            }.get(config.priority, 0)
            
            # Combined score for sorting
            combined_score = (priority_score * 10) + health_score
            
            available_sources.append((source, combined_score))
        
        # Sort by combined score (descending) and return sources
        available_sources.sort(key=lambda x: x[1], reverse=True)
        return [source for source, _ in available_sources]
    
    async def fetch_with_intelligent_fallback(
        self,
        data_type: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        week: int = 1,
        cache_key_prefix: str = "api_data"
    ) -> APIResponse:
        """
        Fetch data using intelligent source switching based on health and priority.
        Automatically falls back through sources based on their current status.
        """
        sources = self.get_sources_by_priority(data_type)
        
        if not sources:
            # No sources available
            return APIResponse(
                data=None,
                source=DataSource.CACHE,
                cached=False,
                timestamp=datetime.utcnow(),
                notifications=[{
                    "type": "error",
                    "message": f"No data sources available for {data_type}. Please try again later.",
                    "source": "all",
                    "retryable": True
                }]
            )
        
        errors = []
        
        for i, source in enumerate(sources):
            start_time = datetime.utcnow()
            
            try:
                logger.info(f"Attempting {data_type} from {source.value} (priority {i+1}/{len(sources)})")
                
                response = await self.client_manager.fetch_with_cache(
                    source=source,
                    endpoint=endpoint,
                    params=params,
                    week=week,
                    cache_key_prefix=cache_key_prefix
                )
                
                # Record successful request
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self._update_source_metrics(source, success=True, response_time=response_time)
                
                # Add notification if using fallback source
                if i > 0:  # Not the first (primary) source
                    source_name = source.value.replace('_', ' ').title()
                    response.notifications.append({
                        "type": "info",
                        "message": f"Using {source_name} as backup data source",
                        "source": source.value,
                        "retryable": False
                    })
                
                # Add data quality notification for fallback sources
                if source in [DataSource.ESPN_API, DataSource.NFL_API]:
                    if data_type in ["ats_predictions", "totals_predictions"]:
                        response.notifications.append({
                            "type": "warning",
                            "message": f"Using calculated {data_type.replace('_', ' ')} - betting lines not available from {source.value.replace('_', ' ').title()}",
                            "source": source.value,
                            "retryable": False
                        })
                
                return response
                
            except Exception as e:
                # Record failed request
                response_time = (datetime.utcnow() - start_time).total_seconds()
                self._update_source_metrics(source, success=False, response_time=response_time)
                
                error_msg = f"{source.value}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Failed to fetch {data_type} from {source.value}: {str(e)}")
                
                # Continue to next source
                continue
        
        # All sources failed - try emergency cache fallback
        logger.error(f"All sources failed for {data_type}. Errors: {'; '.join(errors)}")
        
        # Try to get any cached data as absolute last resort
        try:
            cache_response = await self._emergency_cache_fallback(data_type, week, cache_key_prefix)
            if cache_response:
                return cache_response
        except Exception as cache_error:
            logger.error(f"Emergency cache fallback failed: {str(cache_error)}")
        
        # Absolutely no data available
        return APIResponse(
            data=None,
            source=DataSource.CACHE,
            cached=False,
            timestamp=datetime.utcnow(),
            notifications=[{
                "type": "error",
                "message": f"All data sources for {data_type} are currently unavailable. Please try again in a few minutes.",
                "source": "all",
                "retryable": True
            }]
        )
    
    async def _emergency_cache_fallback(
        self, 
        data_type: str, 
        week: int, 
        cache_key_prefix: str
    ) -> Optional[APIResponse]:
        """
        Emergency fallback to any available cached data, regardless of age.
        Used when all API sources have failed.
        """
        cache_key_base = self.client_manager.cache_manager.get_cache_key_for_predictions(
            week=week,
            prediction_type=cache_key_prefix,
            year=2025
        )
        
        # Try to find any cached data from any source
        for source in self.source_configs:
            cache_key = f"{cache_key_base}:{source.value}:*"
            
            try:
                # This is simplified - in production you'd want pattern matching
                cached_data = self.client_manager.cache_manager.get(cache_key)
                if cached_data:
                    logger.warning(f"Emergency cache fallback: serving stale data from {source.value}")
                    return APIResponse(
                        data=cached_data['data'],
                        source=source,
                        cached=True,
                        timestamp=datetime.fromisoformat(cached_data['timestamp']),
                        notifications=[{
                            "type": "warning",
                            "message": f"Emergency fallback: showing cached {data_type.replace('_', ' ')} (may be outdated)",
                            "source": source.value,
                            "retryable": True
                        }]
                    )
            except Exception:
                continue
        
        return None
    
    def perform_health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all sources and update their status.
        Returns comprehensive health report.
        """
        health_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": {},
            "summary": {
                "healthy": 0,
                "degraded": 0,
                "unhealthy": 0,
                "offline": 0
            }
        }
        
        for source, config in self.source_configs.items():
            # Update health status
            health = self._calculate_source_health(source)
            self.source_health[source] = health
            self.last_health_check[source] = datetime.utcnow()
            
            # Get metrics
            metrics = self.source_metrics[source]
            
            # Build source report
            source_report = {
                "health": health.value,
                "priority": config.priority.value,
                "enabled": config.enabled,
                "metrics": {
                    "success_rate": f"{metrics.success_rate:.1f}%",
                    "error_rate": f"{metrics.error_rate:.1f}%",
                    "total_requests": metrics.total_requests,
                    "consecutive_errors": metrics.consecutive_errors,
                    "consecutive_successes": metrics.consecutive_successes,
                    "avg_response_time": f"{metrics.avg_response_time:.2f}s",
                    "last_success": metrics.last_success.isoformat() if metrics.last_success else None,
                    "last_error": metrics.last_error.isoformat() if metrics.last_error else None
                },
                "thresholds": {
                    "degraded_threshold": f"{config.degraded_threshold}%",
                    "unhealthy_threshold": f"{config.unhealthy_threshold}%",
                    "max_consecutive_errors": config.max_consecutive_errors,
                    "timeout_threshold": f"{config.timeout_threshold}s"
                }
            }
            
            health_report["sources"][source.value] = source_report
            health_report["summary"][health.value] += 1
        
        return health_report
    
    def get_source_recommendations(self, data_type: str) -> Dict[str, Any]:
        """
        Get recommendations for data source usage based on current health.
        Provides guidance on which sources to use for different data types.
        """
        sources = self.get_sources_by_priority(data_type)
        
        recommendations = {
            "data_type": data_type,
            "timestamp": datetime.utcnow().isoformat(),
            "recommended_sources": [],
            "avoid_sources": [],
            "warnings": []
        }
        
        for source in sources:
            config = self.source_configs[source]
            health = self.source_health[source]
            metrics = self.source_metrics[source]
            
            source_info = {
                "source": source.value,
                "priority": config.priority.value,
                "health": health.value,
                "success_rate": f"{metrics.success_rate:.1f}%",
                "avg_response_time": f"{metrics.avg_response_time:.2f}s"
            }
            
            if health in [SourceHealth.HEALTHY, SourceHealth.DEGRADED]:
                recommendations["recommended_sources"].append(source_info)
            else:
                recommendations["avoid_sources"].append(source_info)
        
        # Add warnings based on source availability
        healthy_primary = sum(1 for s in sources if 
                            self.source_configs[s].priority == SourcePriority.PRIMARY and 
                            self.source_health[s] == SourceHealth.HEALTHY)
        
        if healthy_primary == 0:
            recommendations["warnings"].append(
                "No primary sources are healthy. Data quality may be reduced."
            )
        
        if len(sources) < 2:
            recommendations["warnings"].append(
                f"Limited fallback options available for {data_type}."
            )
        
        return recommendations
    
    def reset_source_metrics(self, source: DataSource):
        """Reset metrics for a specific source"""
        self.source_metrics[source] = SourceMetrics()
        self.source_health[source] = SourceHealth.HEALTHY
        self.active_notifications[source] = []
        logger.info(f"Reset metrics for {source.value}")
    
    def disable_source(self, source: DataSource, reason: str = "Manual disable"):
        """Disable a source temporarily"""
        if source in self.source_configs:
            self.source_configs[source].enabled = False
            self.source_health[source] = SourceHealth.OFFLINE
            logger.info(f"Disabled {source.value}: {reason}")
    
    def enable_source(self, source: DataSource):
        """Re-enable a disabled source"""
        if source in self.source_configs:
            self.source_configs[source].enabled = True
            self.source_health[source] = SourceHealth.HEALTHY
            logger.info(f"Enabled {source.value}")