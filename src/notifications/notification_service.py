"""
Notification service for generating user-friendly error messages and API status updates.
Handles API status tracking, user notification formatting, and retry status communication.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

# Import types from the TypeScript definitions (we'll need Python equivalents)
class NotificationType(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"

class DataSource(Enum):
    ODDS_API = "odds_api"
    SPORTSDATA_IO = "sportsdata_io"
    ESPN_API = "espn_api"
    NFL_API = "nfl_api"
    RAPID_API = "rapid_api"
    CACHE = "cache"

class ErrorType(Enum):
    API_UNAVAILABLE = "api_unavailable"
    RATE_LIMITED = "rate_limited"
    INVALID_DATA = "invalid_data"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    CACHE_ERROR = "cache_error"

class Notification:
    def __init__(
        self,
        type: NotificationType,
        message: str,
        source: Optional[DataSource] = None,
        retryable: bool = False,
        timestamp: Optional[str] = None
    ):
        self.type = type
        self.message = message
        self.source = source
        self.retryable = retryable
        self.timestamp = timestamp or datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "message": self.message,
            "source": self.source.value if self.source else None,
            "retryable": self.retryable,
            "timestamp": self.timestamp
        }

class NotificationService:
    """
    Service for generating user-friendly notifications and tracking API status.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._api_status: Dict[DataSource, Dict[str, Any]] = {}
        self._retry_attempts: Dict[str, int] = {}
        
    def create_api_unavailable_notification(
        self, 
        source: DataSource, 
        trying_backup: bool = True
    ) -> Notification:
        """Create notification for API unavailability."""
        source_names = {
            DataSource.ODDS_API: "The Odds API",
            DataSource.SPORTSDATA_IO: "SportsDataIO API",
            DataSource.ESPN_API: "ESPN API",
            DataSource.NFL_API: "NFL.com API",
            DataSource.RAPID_API: "RapidAPI"
        }
        
        source_name = source_names.get(source, source.value)
        
        if trying_backup:
            message = f"{source_name} is currently unavailable. Trying backup sources..."
        else:
            message = f"{source_name} is currently unavailable."
            
        return Notification(
            type=NotificationType.WARNING,
            message=message,
            source=source,
            retryable=True
        )
    
    def create_all_sources_failed_notification(self) -> Notification:
        """Create notification when all data sources have failed."""
        return Notification(
            type=NotificationType.ERROR,
            message="Live data is temporarily unavailable. Please try again in a few minutes.",
            retryable=True
        )
    
    def create_rate_limited_notification(
        self, 
        source: DataSource, 
        retry_minutes: int
    ) -> Notification:
        """Create notification for rate limiting."""
        source_names = {
            DataSource.ODDS_API: "The Odds API",
            DataSource.SPORTSDATA_IO: "SportsDataIO API",
            DataSource.ESPN_API: "ESPN API",
            DataSource.NFL_API: "NFL.com API",
            DataSource.RAPID_API: "RapidAPI"
        }
        
        source_name = source_names.get(source, source.value)
        message = f"{source_name} rate limit reached. Data will refresh in {retry_minutes} minutes."
        
        return Notification(
            type=NotificationType.WARNING,
            message=message,
            source=source,
            retryable=True
        )
    
    def create_partial_data_notification(
        self, 
        available_sources: List[DataSource],
        failed_sources: List[DataSource]
    ) -> Notification:
        """Create notification for partial data availability."""
        failed_count = len(failed_sources)
        total_count = len(available_sources) + failed_count
        
        message = f"Some data sources are unavailable ({failed_count}/{total_count}). Showing available predictions."
        
        return Notification(
            type=NotificationType.INFO,
            message=message,
            retryable=True
        )
    
    def create_cache_served_notification(self, minutes_old: int) -> Notification:
        """Create notification when serving cached data."""
        message = f"Showing recent data (updated {minutes_old} minutes ago) while fetching latest."
        
        return Notification(
            type=NotificationType.INFO,
            message=message,
            source=DataSource.CACHE,
            retryable=False
        )
    
    def create_retry_attempt_notification(
        self, 
        source: DataSource, 
        attempt: int, 
        max_attempts: int
    ) -> Notification:
        """Create notification for retry attempts."""
        source_names = {
            DataSource.ODDS_API: "The Odds API",
            DataSource.SPORTSDATA_IO: "SportsDataIO API",
            DataSource.ESPN_API: "ESPN API",
            DataSource.NFL_API: "NFL.com API",
            DataSource.RAPID_API: "RapidAPI"
        }
        
        source_name = source_names.get(source, source.value)
        message = f"Retrying {source_name} (attempt {attempt}/{max_attempts})..."
        
        return Notification(
            type=NotificationType.INFO,
            message=message,
            source=source,
            retryable=True
        )
    
    def create_api_recovered_notification(self, source: DataSource) -> Notification:
        """Create notification when API service is restored."""
        source_names = {
            DataSource.ODDS_API: "The Odds API",
            DataSource.SPORTSDATA_IO: "SportsDataIO API",
            DataSource.ESPN_API: "ESPN API",
            DataSource.NFL_API: "NFL.com API",
            DataSource.RAPID_API: "RapidAPI"
        }
        
        source_name = source_names.get(source, source.value)
        message = f"{source_name} is back online. Live data restored."
        
        return Notification(
            type=NotificationType.SUCCESS,
            message=message,
            source=source,
            retryable=False
        )
    
    def create_error_notification(
        self, 
        error_type: ErrorType, 
        source: DataSource,
        context: Optional[str] = None
    ) -> Notification:
        """Create notification for specific error types."""
        error_messages = {
            ErrorType.API_UNAVAILABLE: "API service is currently unavailable",
            ErrorType.RATE_LIMITED: "API rate limit exceeded",
            ErrorType.INVALID_DATA: "Received invalid data from API",
            ErrorType.NETWORK_ERROR: "Network connection error",
            ErrorType.AUTHENTICATION_ERROR: "API authentication failed",
            ErrorType.CACHE_ERROR: "Cache system error"
        }
        
        base_message = error_messages.get(error_type, "Unknown error occurred")
        
        if context:
            message = f"{base_message}: {context}"
        else:
            message = base_message
            
        notification_type = NotificationType.ERROR
        if error_type in [ErrorType.RATE_LIMITED, ErrorType.CACHE_ERROR]:
            notification_type = NotificationType.WARNING
            
        return Notification(
            type=notification_type,
            message=message,
            source=source,
            retryable=error_type not in [ErrorType.AUTHENTICATION_ERROR]
        )
    
    def track_api_status(
        self, 
        source: DataSource, 
        is_healthy: bool, 
        last_error: Optional[str] = None
    ) -> None:
        """Track the health status of an API source."""
        self._api_status[source] = {
            "healthy": is_healthy,
            "last_checked": datetime.now().isoformat(),
            "last_error": last_error
        }
        
        if is_healthy:
            self.logger.info(f"{source.value} API is healthy")
        else:
            self.logger.warning(f"{source.value} API is unhealthy: {last_error}")
    
    def get_api_status(self, source: DataSource) -> Optional[Dict[str, Any]]:
        """Get the current status of an API source."""
        return self._api_status.get(source)
    
    def get_all_api_status(self) -> Dict[DataSource, Dict[str, Any]]:
        """Get status of all tracked API sources."""
        return self._api_status.copy()
    
    def increment_retry_count(self, key: str) -> int:
        """Increment and return retry count for a given key."""
        self._retry_attempts[key] = self._retry_attempts.get(key, 0) + 1
        return self._retry_attempts[key]
    
    def reset_retry_count(self, key: str) -> None:
        """Reset retry count for a given key."""
        if key in self._retry_attempts:
            del self._retry_attempts[key]
    
    def get_retry_count(self, key: str) -> int:
        """Get current retry count for a given key."""
        return self._retry_attempts.get(key, 0)
    
    def format_api_status_update(self) -> List[Notification]:
        """Format current API status as notifications."""
        notifications = []
        
        healthy_sources = []
        unhealthy_sources = []
        
        for source, status in self._api_status.items():
            if status["healthy"]:
                healthy_sources.append(source)
            else:
                unhealthy_sources.append(source)
        
        if unhealthy_sources and healthy_sources:
            notifications.append(
                self.create_partial_data_notification(healthy_sources, unhealthy_sources)
            )
        elif unhealthy_sources and not healthy_sources:
            notifications.append(self.create_all_sources_failed_notification())
        
        return notifications
    
    def clear_old_retry_attempts(self, max_age_minutes: int = 60) -> None:
        """Clear old retry attempt records."""
        # This is a simple implementation - in production you might want to track timestamps
        # For now, we'll just clear all if called
        if max_age_minutes <= 0:
            self._retry_attempts.clear()