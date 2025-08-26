"""
Health check system for NFL Predictor API data sources.
Provides comprehensive health monitoring for all APIs, cache, and system components.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import psutil
import aiohttp

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ComponentType(Enum):
    """Types of system components"""
    API_SOURCE = "api_source"
    CACHE = "cache"
    SYSTEM = "system"
    DATABASE = "database"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    component: str
    component_type: ComponentType
    status: HealthStatus
    response_time_ms: Optional[float]
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "component": self.component,
            "component_type": self.component_type.value,
            "status": self.status.value,
            "response_time_ms": self.response_time_ms,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    load_average: Tuple[float, float, float]
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_percent": self.disk_percent,
            "load_average": {
                "1min": self.load_average[0],
                "5min": self.load_average[1],
                "15min": self.load_average[2]
            },
            "uptime_seconds": self.uptime_seconds
        }


class APIHealthChecker:
    """Health checker for external API sources"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def check_odds_api(self, api_key: Optional[str] = None) -> HealthCheckResult:
        """Check The Odds API health"""
        start_time = time.time()
        
        try:
            headers = {}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            
            # Use a lightweight endpoint for health check
            url = "https://api.the-odds-api.com/v4/sports"
            params = {"apiKey": api_key} if api_key else {}
            
            async with self.session.get(url, headers=headers, params=params) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return HealthCheckResult(
                        component="odds_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="The Odds API is responding normally",
                        details={
                            "status_code": response.status,
                            "sports_available": len(data) if isinstance(data, list) else 0,
                            "rate_limit_remaining": response.headers.get("x-requests-remaining"),
                            "rate_limit_used": response.headers.get("x-requests-used")
                        },
                        timestamp=datetime.utcnow()
                    )
                elif response.status == 401:
                    return HealthCheckResult(
                        component="odds_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message="The Odds API authentication failed",
                        details={"status_code": response.status, "error": "Invalid API key"},
                        timestamp=datetime.utcnow()
                    )
                elif response.status == 429:
                    return HealthCheckResult(
                        component="odds_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        message="The Odds API rate limit exceeded",
                        details={
                            "status_code": response.status,
                            "rate_limit_remaining": response.headers.get("x-requests-remaining", "0")
                        },
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        component="odds_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"The Odds API returned status {response.status}",
                        details={"status_code": response.status},
                        timestamp=datetime.utcnow()
                    )
                    
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="odds_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                message="The Odds API request timed out",
                details={"error": "timeout", "timeout_seconds": self.timeout},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                component="odds_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"The Odds API health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def check_sportsdata_io(self, api_key: Optional[str] = None) -> HealthCheckResult:
        """Check SportsDataIO API health"""
        start_time = time.time()
        
        try:
            headers = {}
            if api_key:
                headers["Ocp-Apim-Subscription-Key"] = api_key
            
            # Use a lightweight endpoint for health check
            url = "https://api.sportsdata.io/v3/nfl/scores/json/CurrentSeason"
            
            async with self.session.get(url, headers=headers) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return HealthCheckResult(
                        component="sportsdata_io",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="SportsDataIO API is responding normally",
                        details={
                            "status_code": response.status,
                            "current_season": data if isinstance(data, (int, str)) else "unknown",
                            "rate_limit_remaining": response.headers.get("x-ratelimit-remaining"),
                            "rate_limit_limit": response.headers.get("x-ratelimit-limit")
                        },
                        timestamp=datetime.utcnow()
                    )
                elif response.status == 401 or response.status == 403:
                    return HealthCheckResult(
                        component="sportsdata_io",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message="SportsDataIO API authentication failed",
                        details={"status_code": response.status, "error": "Invalid API key"},
                        timestamp=datetime.utcnow()
                    )
                elif response.status == 429:
                    return HealthCheckResult(
                        component="sportsdata_io",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.DEGRADED,
                        response_time_ms=response_time,
                        message="SportsDataIO API rate limit exceeded",
                        details={
                            "status_code": response.status,
                            "rate_limit_remaining": response.headers.get("x-ratelimit-remaining", "0")
                        },
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        component="sportsdata_io",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"SportsDataIO API returned status {response.status}",
                        details={"status_code": response.status},
                        timestamp=datetime.utcnow()
                    )
                    
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="sportsdata_io",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                message="SportsDataIO API request timed out",
                details={"error": "timeout", "timeout_seconds": self.timeout},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                component="sportsdata_io",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"SportsDataIO API health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def check_espn_api(self) -> HealthCheckResult:
        """Check ESPN API health"""
        start_time = time.time()
        
        try:
            url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
            
            async with self.session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return HealthCheckResult(
                        component="espn_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="ESPN API is responding normally",
                        details={
                            "status_code": response.status,
                            "events_available": len(data.get("events", [])) if isinstance(data, dict) else 0
                        },
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        component="espn_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"ESPN API returned status {response.status}",
                        details={"status_code": response.status},
                        timestamp=datetime.utcnow()
                    )
                    
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="espn_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                message="ESPN API request timed out",
                details={"error": "timeout", "timeout_seconds": self.timeout},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                component="espn_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"ESPN API health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    async def check_nfl_api(self) -> HealthCheckResult:
        """Check NFL.com API health"""
        start_time = time.time()
        
        try:
            url = "https://api.nfl.com/v1/games"
            
            async with self.session.get(url) as response:
                response_time = (time.time() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return HealthCheckResult(
                        component="nfl_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.HEALTHY,
                        response_time_ms=response_time,
                        message="NFL API is responding normally",
                        details={
                            "status_code": response.status,
                            "games_available": len(data) if isinstance(data, list) else 0
                        },
                        timestamp=datetime.utcnow()
                    )
                else:
                    return HealthCheckResult(
                        component="nfl_api",
                        component_type=ComponentType.API_SOURCE,
                        status=HealthStatus.UNHEALTHY,
                        response_time_ms=response_time,
                        message=f"NFL API returned status {response.status}",
                        details={"status_code": response.status},
                        timestamp=datetime.utcnow()
                    )
                    
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component="nfl_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=self.timeout * 1000,
                message="NFL API request timed out",
                details={"error": "timeout", "timeout_seconds": self.timeout},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                component="nfl_api",
                component_type=ComponentType.API_SOURCE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"NFL API health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )


class CacheHealthChecker:
    """Health checker for Redis cache"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
    
    def check_redis_health(self) -> HealthCheckResult:
        """Check Redis cache health"""
        if not REDIS_AVAILABLE:
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message="Redis Python client not available",
                details={"error": "redis package not installed"},
                timestamp=datetime.utcnow()
            )
        
        if not self.redis_client:
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNKNOWN,
                response_time_ms=None,
                message="Redis client not configured",
                details={"error": "no redis client provided"},
                timestamp=datetime.utcnow()
            )
        
        start_time = time.time()
        
        try:
            # Test basic connectivity
            self.redis_client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Test read/write operations
            test_key = "nfl_predictor:health_check"
            test_value = f"health_check_{int(time.time())}"
            
            self.redis_client.set(test_key, test_value, ex=60)
            retrieved_value = self.redis_client.get(test_key)
            self.redis_client.delete(test_key)
            
            if retrieved_value != test_value:
                raise Exception("Read/write test failed")
            
            # Get Redis info
            info = self.redis_client.info()
            
            # Check memory usage
            used_memory = info.get("used_memory", 0)
            max_memory = info.get("maxmemory", 0)
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            # Determine status based on memory usage
            if memory_usage_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = f"Redis memory usage critical: {memory_usage_percent:.1f}%"
            elif memory_usage_percent > 80:
                status = HealthStatus.DEGRADED
                message = f"Redis memory usage high: {memory_usage_percent:.1f}%"
            else:
                status = HealthStatus.HEALTHY
                message = "Redis cache is operating normally"
            
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=status,
                response_time_ms=ping_time,
                message=message,
                details={
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory_human": info.get("used_memory_human"),
                    "memory_usage_percent": round(memory_usage_percent, 2),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0)
                },
                timestamp=datetime.utcnow()
            )
            
        except redis.ConnectionError as e:
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"Redis connection failed: {str(e)}",
                details={"error": "connection_failed", "details": str(e)},
                timestamp=datetime.utcnow()
            )
        except redis.AuthenticationError as e:
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"Redis authentication failed: {str(e)}",
                details={"error": "authentication_failed", "details": str(e)},
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return HealthCheckResult(
                component="redis_cache",
                component_type=ComponentType.CACHE,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=None,
                message=f"Redis health check failed: {str(e)}",
                details={"error": "health_check_failed", "details": str(e)},
                timestamp=datetime.utcnow()
            )


class SystemHealthChecker:
    """Health checker for system resources"""
    
    def check_system_health(self) -> HealthCheckResult:
        """Check system resource health"""
        try:
            metrics = self.get_system_metrics()
            
            # Determine status based on resource usage
            critical_issues = []
            warnings = []
            
            if metrics.cpu_percent > 90:
                critical_issues.append(f"CPU usage critical: {metrics.cpu_percent:.1f}%")
            elif metrics.cpu_percent > 80:
                warnings.append(f"CPU usage high: {metrics.cpu_percent:.1f}%")
            
            if metrics.memory_percent > 90:
                critical_issues.append(f"Memory usage critical: {metrics.memory_percent:.1f}%")
            elif metrics.memory_percent > 80:
                warnings.append(f"Memory usage high: {metrics.memory_percent:.1f}%")
            
            if metrics.disk_percent > 95:
                critical_issues.append(f"Disk usage critical: {metrics.disk_percent:.1f}%")
            elif metrics.disk_percent > 85:
                warnings.append(f"Disk usage high: {metrics.disk_percent:.1f}%")
            
            # Load average check (for Unix systems)
            if hasattr(metrics, 'load_average') and metrics.load_average[0] > psutil.cpu_count() * 2:
                critical_issues.append(f"Load average critical: {metrics.load_average[0]:.2f}")
            elif hasattr(metrics, 'load_average') and metrics.load_average[0] > psutil.cpu_count():
                warnings.append(f"Load average high: {metrics.load_average[0]:.2f}")
            
            # Determine overall status
            if critical_issues:
                status = HealthStatus.UNHEALTHY
                message = f"System resources critical: {'; '.join(critical_issues)}"
            elif warnings:
                status = HealthStatus.DEGRADED
                message = f"System resources elevated: {'; '.join(warnings)}"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources are within normal limits"
            
            return HealthCheckResult(
                component="system_resources",
                component_type=ComponentType.SYSTEM,
                status=status,
                response_time_ms=None,
                message=message,
                details=metrics.to_dict(),
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="system_resources",
                component_type=ComponentType.SYSTEM,
                status=HealthStatus.UNKNOWN,
                response_time_ms=None,
                message=f"System health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow()
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage (root partition)
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Load average (Unix systems only)
        try:
            load_avg = psutil.getloadavg()
        except AttributeError:
            # Windows doesn't have load average
            load_avg = (0.0, 0.0, 0.0)
        
        # System uptime
        boot_time = psutil.boot_time()
        uptime_seconds = time.time() - boot_time
        
        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            load_average=load_avg,
            uptime_seconds=uptime_seconds
        )


class ComprehensiveHealthChecker:
    """
    Comprehensive health checker for all system components.
    Coordinates health checks across APIs, cache, and system resources.
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        api_keys: Optional[Dict[str, str]] = None,
        timeout: int = 10
    ):
        self.redis_client = redis_client
        self.api_keys = api_keys or {}
        self.timeout = timeout
        
        # Initialize component checkers
        self.cache_checker = CacheHealthChecker(redis_client)
        self.system_checker = SystemHealthChecker()
        
        # Health check history
        self.health_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
    
    async def check_all_components(self) -> Dict[str, Any]:
        """Run health checks on all components"""
        results = []
        
        # Check APIs
        async with APIHealthChecker(self.timeout) as api_checker:
            # Primary APIs
            if "odds_api" in self.api_keys:
                result = await api_checker.check_odds_api(self.api_keys["odds_api"])
                results.append(result)
            
            if "sportsdata_io" in self.api_keys:
                result = await api_checker.check_sportsdata_io(self.api_keys["sportsdata_io"])
                results.append(result)
            
            # Fallback APIs
            espn_result = await api_checker.check_espn_api()
            results.append(espn_result)
            
            nfl_result = await api_checker.check_nfl_api()
            results.append(nfl_result)
        
        # Check cache
        cache_result = self.cache_checker.check_redis_health()
        results.append(cache_result)
        
        # Check system resources
        system_result = self.system_checker.check_system_health()
        results.append(system_result)
        
        # Compile overall health report
        health_report = self._compile_health_report(results)
        
        # Store in history
        self._store_health_history(health_report)
        
        return health_report
    
    def _compile_health_report(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Compile individual results into overall health report"""
        timestamp = datetime.utcnow()
        
        # Categorize results
        components = {}
        for result in results:
            components[result.component] = result.to_dict()
        
        # Calculate overall status
        statuses = [result.status for result in results]
        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        elif HealthStatus.UNKNOWN in statuses:
            overall_status = HealthStatus.UNKNOWN
        else:
            overall_status = HealthStatus.HEALTHY
        
        # Count statuses
        status_counts = {
            "healthy": sum(1 for s in statuses if s == HealthStatus.HEALTHY),
            "degraded": sum(1 for s in statuses if s == HealthStatus.DEGRADED),
            "unhealthy": sum(1 for s in statuses if s == HealthStatus.UNHEALTHY),
            "unknown": sum(1 for s in statuses if s == HealthStatus.UNKNOWN)
        }
        
        # Calculate average response time for APIs
        api_response_times = [
            result.response_time_ms for result in results
            if result.component_type == ComponentType.API_SOURCE and result.response_time_ms is not None
        ]
        avg_api_response_time = sum(api_response_times) / len(api_response_times) if api_response_times else None
        
        return {
            "timestamp": timestamp.isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total_components": len(results),
                "status_counts": status_counts,
                "avg_api_response_time_ms": round(avg_api_response_time, 2) if avg_api_response_time else None
            },
            "components": components,
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: List[HealthCheckResult]) -> List[str]:
        """Generate recommendations based on health check results"""
        recommendations = []
        
        for result in results:
            if result.status == HealthStatus.UNHEALTHY:
                if result.component_type == ComponentType.API_SOURCE:
                    if "authentication" in result.message.lower():
                        recommendations.append(f"Check {result.component} API key configuration")
                    elif "timeout" in result.message.lower():
                        recommendations.append(f"Check network connectivity to {result.component}")
                    else:
                        recommendations.append(f"Investigate {result.component} service status")
                
                elif result.component_type == ComponentType.CACHE:
                    recommendations.append("Check Redis server status and configuration")
                
                elif result.component_type == ComponentType.SYSTEM:
                    if "memory" in result.message.lower():
                        recommendations.append("Consider increasing system memory or optimizing memory usage")
                    elif "cpu" in result.message.lower():
                        recommendations.append("Investigate high CPU usage and consider scaling")
                    elif "disk" in result.message.lower():
                        recommendations.append("Free up disk space or expand storage")
            
            elif result.status == HealthStatus.DEGRADED:
                if result.component_type == ComponentType.API_SOURCE:
                    if "rate limit" in result.message.lower():
                        recommendations.append(f"Implement caching or reduce {result.component} request frequency")
                
                elif result.component_type == ComponentType.CACHE:
                    if "memory" in result.message.lower():
                        recommendations.append("Consider increasing Redis memory limit or implementing cache eviction")
                
                elif result.component_type == ComponentType.SYSTEM:
                    recommendations.append("Monitor system resources and consider scaling if usage continues to increase")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _store_health_history(self, health_report: Dict[str, Any]):
        """Store health report in history"""
        self.health_history.append(health_report)
        
        # Limit history size
        if len(self.health_history) > self.max_history_size:
            self.health_history = self.health_history[-self.max_history_size:]
    
    def get_health_trends(self, hours: int = 24) -> Dict[str, Any]:
        """Get health trends over specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Filter history by time
        recent_history = [
            report for report in self.health_history
            if datetime.fromisoformat(report["timestamp"]) > cutoff_time
        ]
        
        if not recent_history:
            return {"message": "No health data available for specified time period"}
        
        # Calculate trends
        status_timeline = []
        component_trends = {}
        
        for report in recent_history:
            status_timeline.append({
                "timestamp": report["timestamp"],
                "overall_status": report["overall_status"],
                "healthy_count": report["summary"]["status_counts"]["healthy"],
                "degraded_count": report["summary"]["status_counts"]["degraded"],
                "unhealthy_count": report["summary"]["status_counts"]["unhealthy"]
            })
            
            # Track individual component trends
            for component_name, component_data in report["components"].items():
                if component_name not in component_trends:
                    component_trends[component_name] = []
                
                component_trends[component_name].append({
                    "timestamp": report["timestamp"],
                    "status": component_data["status"],
                    "response_time_ms": component_data.get("response_time_ms")
                })
        
        return {
            "time_period_hours": hours,
            "total_reports": len(recent_history),
            "status_timeline": status_timeline,
            "component_trends": component_trends,
            "summary": {
                "most_recent_status": recent_history[-1]["overall_status"],
                "status_changes": len(set(report["overall_status"] for report in recent_history)),
                "avg_healthy_components": sum(
                    report["summary"]["status_counts"]["healthy"] for report in recent_history
                ) / len(recent_history)
            }
        }
    
    def export_health_data(self, format: str = "json") -> str:
        """Export health data in specified format"""
        if format.lower() == "json":
            return json.dumps({
                "export_timestamp": datetime.utcnow().isoformat(),
                "health_history": self.health_history
            }, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")


def create_health_checker(
    redis_client: Optional[redis.Redis] = None,
    api_keys: Optional[Dict[str, str]] = None
) -> ComprehensiveHealthChecker:
    """Create comprehensive health checker with default configuration"""
    return ComprehensiveHealthChecker(redis_client, api_keys)