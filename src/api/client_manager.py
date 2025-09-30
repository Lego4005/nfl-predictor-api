"""
API Client Manager for handling multiple data sources with failover logic.
Manages primary and fallback API clients with error handling and retry logic.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import aiohttp
import json
import os

from ..cache.cache_manager import CacheManager
from ..cache.health_monitor import CacheHealthMonitor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Enumeration of available data sources"""
    ODDS_API = "odds_api"
    SPORTSDATA_IO = "sportsdata_io"
    ESPN_API = "espn_api"
    NFL_API = "nfl_api"
    RAPID_API = "rapid_api"
    CACHE = "cache"


class ErrorType(Enum):
    """Classification of API errors"""
    API_UNAVAILABLE = "api_unavailable"
    RATE_LIMITED = "rate_limited"
    INVALID_DATA = "invalid_data"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    CACHE_ERROR = "cache_error"


@dataclass
class APIConfig:
    """Configuration for API endpoints and settings"""
    base_url: str
    api_key: Optional[str] = None
    rate_limit: int = 100  # requests per hour
    timeout: int = 30  # seconds
    max_retries: int = 3
    backoff_factor: float = 2.0


@dataclass
class ErrorContext:
    """Context information for API errors"""
    source: DataSource
    endpoint: str
    week: int
    retry_count: int
    timestamp: datetime
    error_type: ErrorType
    message: str


@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    data: Any
    source: DataSource
    cached: bool = False
    timestamp: datetime = None
    notifications: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        if self.notifications is None:
            self.notifications = []


class APIClientManager:
    """
    Manages multiple API clients with failover logic and error handling.
    Handles primary/fallback source routing, rate limiting, and retry logic.
    Includes cache integration for improved performance and reduced API calls.
    """
    
    def __init__(self, cache_manager: Optional[CacheManager] = None):
        self.configs: Dict[DataSource, APIConfig] = {}
        self.clients: Dict[DataSource, aiohttp.ClientSession] = {}
        self.last_request_times: Dict[DataSource, datetime] = {}
        self.error_counts: Dict[DataSource, int] = {}
        self.circuit_breaker: Dict[DataSource, datetime] = {}
        self.cache_manager = cache_manager or CacheManager()
        self.cache_health_monitor = CacheHealthMonitor(self.cache_manager)
        self._load_configuration()
    
    def _load_configuration(self):
        """Load API configuration from environment variables"""
        # Primary sources
        self.configs[DataSource.ODDS_API] = APIConfig(
            base_url="https://api.the-odds-api.com/v4",
            api_key=os.getenv("ODDS_API_KEY"),
            rate_limit=20000,  # requests per month for premium tier
            timeout=30,
            max_retries=3
        )
        
        self.configs[DataSource.SPORTSDATA_IO] = APIConfig(
            base_url="https://api.sportsdata.io/v3/nfl",
            api_key=os.getenv("SPORTSDATA_IO_KEY"),
            rate_limit=1000,  # requests per month for free tier
            timeout=30,
            max_retries=3
        )
        
        # Fallback sources
        self.configs[DataSource.ESPN_API] = APIConfig(
            base_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl",
            rate_limit=1000,  # requests per hour (estimated)
            timeout=20,
            max_retries=2
        )
        
        self.configs[DataSource.NFL_API] = APIConfig(
            base_url="https://api.nfl.com/v1",
            rate_limit=500,  # requests per hour (estimated)
            timeout=20,
            max_retries=2
        )
        
        self.configs[DataSource.RAPID_API] = APIConfig(
            base_url="https://api-american-football.p.rapidapi.com",
            api_key=os.getenv("RAPID_API_KEY"),
            rate_limit=100,  # requests per month for free tier
            timeout=25,
            max_retries=2
        )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_clients()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._close_clients()
    
    async def _initialize_clients(self):
        """Initialize HTTP client sessions for each data source"""
        for source in DataSource:
            if source == DataSource.CACHE:
                continue
                
            config = self.configs.get(source)
            if not config:
                continue
                
            timeout = aiohttp.ClientTimeout(total=config.timeout)
            headers = {"User-Agent": "NFL-Predictor/1.0"}
            
            # Add API key headers based on source
            if source == DataSource.ODDS_API and config.api_key:
                headers["Authorization"] = f"Bearer {config.api_key}"
            elif source == DataSource.SPORTSDATA_IO and config.api_key:
                headers["Ocp-Apim-Subscription-Key"] = config.api_key
            elif source == DataSource.RAPID_API and config.api_key:
                headers["X-RapidAPI-Key"] = config.api_key
                headers["X-RapidAPI-Host"] = "api-american-football.p.rapidapi.com"
            
            self.clients[source] = aiohttp.ClientSession(
                timeout=timeout,
                headers=headers
            )
    
    async def _close_clients(self):
        """Close all HTTP client sessions"""
        for client in self.clients.values():
            await client.close()
        self.clients.clear()
    
    def _is_rate_limited(self, source: DataSource) -> bool:
        """Check if source is currently rate limited"""
        if source not in self.last_request_times:
            return False
            
        config = self.configs[source]
        last_request = self.last_request_times[source]
        time_since_last = datetime.utcnow() - last_request
        
        # Simple rate limiting: minimum time between requests
        min_interval = timedelta(hours=1) / config.rate_limit
        return time_since_last < min_interval
    
    def _is_circuit_broken(self, source: DataSource) -> bool:
        """Check if circuit breaker is active for source"""
        if source not in self.circuit_breaker:
            return False
            
        # Circuit breaker: 5 minute cooldown after multiple failures
        cooldown_end = self.circuit_breaker[source]
        return datetime.utcnow() < cooldown_end
    
    def _record_error(self, source: DataSource, error_type: ErrorType):
        """Record error and potentially trigger circuit breaker"""
        self.error_counts[source] = self.error_counts.get(source, 0) + 1
        
        # Trigger circuit breaker after 3 consecutive errors
        if self.error_counts[source] >= 3:
            self.circuit_breaker[source] = datetime.utcnow() + timedelta(minutes=5)
            logger.warning(f"Circuit breaker activated for {source.value}")
    
    def _record_success(self, source: DataSource):
        """Record successful request and reset error count"""
        self.error_counts[source] = 0
        if source in self.circuit_breaker:
            del self.circuit_breaker[source]
        self.last_request_times[source] = datetime.utcnow()
    
    def _classify_error(self, error_message: str) -> str:
        """Classify error type based on error message"""
        error_lower = error_message.lower()
        
        if "rate limit" in error_lower or "429" in error_lower:
            return "rate_limited"
        elif "authentication" in error_lower or "401" in error_lower or "403" in error_lower:
            return "authentication_error"
        elif "network" in error_lower or "connection" in error_lower or "timeout" in error_lower:
            return "network_error"
        elif "invalid" in error_lower or "malformed" in error_lower or "json" in error_lower:
            return "invalid_data"
        elif "unavailable" in error_lower or "500" in error_lower or "502" in error_lower or "503" in error_lower:
            return "api_unavailable"
        else:
            return "unknown_error"
    
    async def _make_request(
        self, 
        source: DataSource, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to specified source"""
        if source not in self.clients:
            raise ValueError(f"Client not initialized for {source.value}")
        
        if self._is_rate_limited(source):
            raise Exception(f"Rate limited for {source.value}")
        
        if self._is_circuit_broken(source):
            raise Exception(f"Circuit breaker active for {source.value}")
        
        config = self.configs[source]
        client = self.clients[source]
        url = f"{config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            async with client.get(url, params=params) as response:
                if response.status == 429:
                    self._record_error(source, ErrorType.RATE_LIMITED)
                    raise Exception(f"Rate limited by {source.value}")
                
                if response.status == 401 or response.status == 403:
                    self._record_error(source, ErrorType.AUTHENTICATION_ERROR)
                    raise Exception(f"Authentication failed for {source.value}")
                
                if response.status >= 400:
                    self._record_error(source, ErrorType.API_UNAVAILABLE)
                    raise Exception(f"API error {response.status} from {source.value}")
                
                data = await response.json()
                self._record_success(source)
                return data
                
        except aiohttp.ClientError as e:
            self._record_error(source, ErrorType.NETWORK_ERROR)
            raise Exception(f"Network error for {source.value}: {str(e)}")
        except json.JSONDecodeError as e:
            self._record_error(source, ErrorType.INVALID_DATA)
            raise Exception(f"Invalid JSON from {source.value}: {str(e)}")
    
    async def fetch_with_cache(
        self,
        source: DataSource,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        week: int = 1,
        cache_key_prefix: str = "api_data"
    ) -> APIResponse:
        """
        Fetch data with cache-first strategy and freshness validation.
        Checks cache before making external API calls.
        """
        # Generate cache key
        cache_key = self.cache_manager.get_cache_key_for_predictions(
            week=week,
            prediction_type=cache_key_prefix,
            year=2025
        )
        
        # Add source and endpoint to cache key for uniqueness
        cache_key = f"{cache_key}:{source.value}:{endpoint.replace('/', '_')}"
        
        # Check if cache should be used based on health
        if not self.cache_health_monitor.should_use_cache():
            logger.info(f"Bypassing cache for {source.value} due to health issues")
            response = await self.fetch_with_retry(source, endpoint, params, week)
            return response
        
        # Try cache first
        start_time = datetime.utcnow()
        cached_data = self.cache_manager.get(cache_key)
        cache_response_time = (datetime.utcnow() - start_time).total_seconds()
        
        if cached_data:
            self.cache_health_monitor.record_cache_hit(cache_response_time)
            logger.info(f"Cache hit for {source.value} - age: {cached_data['age_minutes']:.1f} minutes")
            return APIResponse(
                data=cached_data['data'],
                source=source,
                cached=True,
                timestamp=datetime.fromisoformat(cached_data['timestamp']),
                notifications=[{
                    "type": "info",
                    "message": f"Using cached data (updated {cached_data['age_minutes']:.0f} minutes ago)",
                    "source": source.value,
                    "retryable": False
                }]
            )
        
        # Record cache miss
        self.cache_health_monitor.record_cache_miss(cache_response_time)
        
        # Cache miss - fetch from API
        try:
            response = await self.fetch_with_retry(source, endpoint, params, week)
            
            # Cache the successful response
            if response.data:
                success = self.cache_manager.set(
                    key=cache_key,
                    data=response.data,
                    source=source.value
                )
                if success:
                    logger.info(f"Cached data for {source.value}")
                else:
                    logger.warning(f"Failed to cache data for {source.value}")
            
            return response
            
        except Exception as e:
            # Record cache error and potentially invalidate
            error_type = self._classify_error(str(e))
            self.cache_health_monitor.record_cache_error(error_type)
            
            # Invalidate cache on certain error types
            await self.cache_health_monitor.invalidate_on_api_error(
                source=source.value,
                endpoint=endpoint,
                week=week,
                error_type=error_type
            )
            
            # Try to serve stale cache data if available
            stale_data = self.cache_manager.get(cache_key)
            if stale_data:
                logger.warning(f"API failed, serving stale cache data for {source.value}")
                return APIResponse(
                    data=stale_data['data'],
                    source=source,
                    cached=True,
                    timestamp=datetime.fromisoformat(stale_data['timestamp']),
                    notifications=[{
                        "type": "warning",
                        "message": f"API unavailable, showing cached data (updated {stale_data['age_minutes']:.0f} minutes ago)",
                        "source": source.value,
                        "retryable": True
                    }]
                )
            
            # No cache available, re-raise the exception
            raise e

    async def fetch_with_retry(
        self,
        source: DataSource,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        week: int = 1
    ) -> APIResponse:
        """
        Fetch data from source with retry logic and exponential backoff
        """
        config = self.configs[source]
        last_exception = None
        
        for attempt in range(config.max_retries + 1):
            try:
                data = await self._make_request(source, endpoint, params)
                
                # Validate data is not empty
                if not data or (isinstance(data, list) and len(data) == 0):
                    raise Exception(f"Empty data returned from {source.value}")
                
                return APIResponse(
                    data=data,
                    source=source,
                    cached=False,
                    timestamp=datetime.utcnow()
                )
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1} failed for {source.value}: {str(e)}")
                
                if attempt < config.max_retries:
                    wait_time = config.backoff_factor ** attempt
                    logger.info(f"Retrying {source.value} in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
        
        # All retries failed
        error_context = ErrorContext(
            source=source,
            endpoint=endpoint,
            week=week,
            retry_count=config.max_retries,
            timestamp=datetime.utcnow(),
            error_type=ErrorType.API_UNAVAILABLE,
            message=str(last_exception)
        )
        
        raise Exception(f"All retries failed for {source.value}: {str(last_exception)}")
    
    async def fetch_with_fallback(
        self,
        primary_sources: List[DataSource],
        fallback_sources: List[DataSource],
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        week: int = 1,
        cache_key_prefix: str = "api_data"
    ) -> APIResponse:
        """
        Fetch data with primary sources first, then fallback sources.
        Uses cache-first strategy for improved performance.
        """
        all_sources = primary_sources + fallback_sources
        errors = []
        
        for source in all_sources:
            try:
                logger.info(f"Attempting to fetch from {source.value}")
                response = await self.fetch_with_cache(
                    source, endpoint, params, week, cache_key_prefix
                )
                
                # Add notification if using fallback source
                if source in fallback_sources:
                    response.notifications.append({
                        "type": "info",
                        "message": f"Using fallback data source: {source.value}",
                        "source": source.value,
                        "retryable": False
                    })
                
                return response
                
            except Exception as e:
                error_msg = f"{source.value}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"Failed to fetch from {source.value}: {str(e)}")
                continue
        
        # All sources failed - try to get any cached data as last resort
        cache_key = self.cache_manager.get_cache_key_for_predictions(
            week=week,
            prediction_type=cache_key_prefix,
            year=2025
        )
        
        # Try cache with wildcard pattern for any source
        pattern = f"{cache_key}:*"
        try:
            # This is a simplified approach - in production you'd want more sophisticated cache fallback
            for source in all_sources:
                source_cache_key = f"{cache_key}:{source.value}:{endpoint.replace('/', '_')}"
                cached_data = self.cache_manager.get(source_cache_key)
                if cached_data:
                    logger.warning(f"All APIs failed, serving stale cache from {source.value}")
                    return APIResponse(
                        data=cached_data['data'],
                        source=source,
                        cached=True,
                        timestamp=datetime.fromisoformat(cached_data['timestamp']),
                        notifications=[{
                            "type": "warning",
                            "message": f"All APIs unavailable, showing cached data (updated {cached_data['age_minutes']:.0f} minutes ago)",
                            "source": source.value,
                            "retryable": True
                        }]
                    )
        except Exception as cache_error:
            logger.error(f"Cache fallback also failed: {str(cache_error)}")
        
        # Absolutely no data available
        error_response = APIResponse(
            data=None,
            source=DataSource.CACHE,  # Indicate no source worked
            cached=False,
            timestamp=datetime.utcnow(),
            notifications=[{
                "type": "error",
                "message": "All data sources are currently unavailable. Please try again later.",
                "source": "all",
                "retryable": True
            }]
        )
        
        logger.error(f"All sources failed. Errors: {'; '.join(errors)}")
        return error_response
    
    async def warm_cache_for_week(
        self,
        week: int,
        endpoints: List[str],
        sources: List[DataSource] = None
    ) -> Dict[str, bool]:
        """
        Warm cache with popular data for specified week.
        Pre-fetches data from multiple endpoints to improve response times.
        """
        if sources is None:
            sources = [DataSource.ODDS_API, DataSource.SPORTSDATA_IO]
        
        results = {}
        
        for source in sources:
            if source not in self.clients:
                continue
                
            for endpoint in endpoints:
                cache_key_prefix = endpoint.split('/')[-1] or "api_data"
                
                try:
                    response = await self.fetch_with_cache(
                        source=source,
                        endpoint=endpoint,
                        week=week,
                        cache_key_prefix=cache_key_prefix
                    )
                    
                    key = f"{source.value}:{endpoint}"
                    results[key] = response.data is not None
                    
                    if response.data:
                        logger.info(f"Cache warmed for {key}")
                    
                except Exception as e:
                    key = f"{source.value}:{endpoint}"
                    results[key] = False
                    logger.warning(f"Cache warming failed for {key}: {str(e)}")
        
        return results
    
    def invalidate_cache_for_week(self, week: int) -> int:
        """
        Invalidate all cached data for specified week.
        Useful when fresh data is needed or on API errors.
        """
        pattern = f"nfl_predictor:predictions:*week={week}*"
        count = self.cache_manager.invalidate_pattern(pattern)
        logger.info(f"Invalidated {count} cache entries for week {week}")
        return count
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache health status and metrics"""
        base_status = self.cache_manager.get_health_status()
        health_metrics = self.cache_health_monitor.get_health_metrics()
        
        return {
            **base_status,
            'performance_metrics': {
                'hit_rate': f"{health_metrics.hit_rate:.2%}",
                'miss_rate': f"{health_metrics.miss_rate:.2%}",
                'error_rate': f"{health_metrics.error_rate:.2%}",
                'avg_response_time': f"{health_metrics.average_response_time:.3f}s",
                'total_requests': health_metrics.total_requests
            },
            'health_status': 'healthy' if self.cache_health_monitor.is_cache_healthy() else 'unhealthy',
            'fallback_recommendation': self.cache_health_monitor.get_fallback_recommendation()
        }
    
    async def perform_cache_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive cache health check"""
        return await self.cache_health_monitor.perform_health_check()

    def get_source_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all data sources"""
        status = {}
        
        for source in DataSource:
            if source == DataSource.CACHE:
                continue
                
            status[source.value] = {
                "available": source in self.clients,
                "error_count": self.error_counts.get(source, 0),
                "circuit_broken": self._is_circuit_broken(source),
                "rate_limited": self._is_rate_limited(source),
                "last_request": self.last_request_times.get(source),
                "config": {
                    "base_url": self.configs[source].base_url,
                    "has_api_key": bool(self.configs[source].api_key),
                    "rate_limit": self.configs[source].rate_limit,
                    "timeout": self.configs[source].timeout
                }
            }
        
        # Add cache status
        status["cache"] = self.get_cache_status()
        
        return status