"""
Error handling middleware for comprehensive error classification and graceful degradation.
Provides logging, error classification, and graceful degradation when APIs fail.
"""

import logging
import traceback
from typing import Optional, Dict, Any, List, Callable, Union
from datetime import datetime
from functools import wraps
import asyncio
import aiohttp

from .notification_service import (
    NotificationService, 
    DataSource, 
    ErrorType, 
    Notification,
    NotificationType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class APIError(Exception):
    """Custom exception for API-related errors."""
    
    def __init__(
        self, 
        message: str, 
        error_type: ErrorType,
        source: DataSource,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.error_type = error_type
        self.source = source
        self.status_code = status_code
        self.response_data = response_data
        self.timestamp = datetime.now().isoformat()

class ErrorHandler:
    """
    Comprehensive error handling middleware with classification and graceful degradation.
    """
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)
        self._error_counts: Dict[str, int] = {}
        self._last_errors: Dict[str, datetime] = {}
        
    def classify_error(
        self, 
        error: Exception, 
        source: DataSource,
        status_code: Optional[int] = None
    ) -> ErrorType:
        """Classify an error into appropriate error type."""
        
        # HTTP status code classification
        if status_code:
            if status_code == 401 or status_code == 403:
                return ErrorType.AUTHENTICATION_ERROR
            elif status_code == 429:
                return ErrorType.RATE_LIMITED
            elif 400 <= status_code < 500:
                return ErrorType.INVALID_DATA
            elif status_code >= 500:
                return ErrorType.API_UNAVAILABLE
        
        # Exception type classification
        if isinstance(error, aiohttp.ClientTimeout):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, aiohttp.ClientConnectionError):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, aiohttp.ClientResponseError):
            if error.status == 429:
                return ErrorType.RATE_LIMITED
            elif error.status >= 500:
                return ErrorType.API_UNAVAILABLE
            else:
                return ErrorType.INVALID_DATA
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorType.NETWORK_ERROR
        elif isinstance(error, ValueError):
            return ErrorType.INVALID_DATA
        elif isinstance(error, KeyError):
            return ErrorType.INVALID_DATA
        else:
            return ErrorType.API_UNAVAILABLE
    
    def log_error(
        self, 
        error: Exception, 
        source: DataSource,
        context: Optional[Dict[str, Any]] = None,
        level: int = logging.ERROR
    ) -> None:
        """Log error with comprehensive context information."""
        
        error_key = f"{source.value}_{type(error).__name__}"
        self._error_counts[error_key] = self._error_counts.get(error_key, 0) + 1
        self._last_errors[error_key] = datetime.now()
        
        log_data = {
            "source": source.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_count": self._error_counts[error_key],
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            log_data.update(context)
        
        # Include stack trace for debugging
        if level >= logging.ERROR:
            log_data["stack_trace"] = traceback.format_exc()
        
        self.logger.log(level, f"API Error - {source.value}: {str(error)}", extra=log_data)
    
    def create_error_notification(
        self, 
        error: Exception, 
        source: DataSource,
        status_code: Optional[int] = None,
        context: Optional[str] = None
    ) -> Notification:
        """Create appropriate notification for an error."""
        
        error_type = self.classify_error(error, source, status_code)
        
        # Track API status
        self.notification_service.track_api_status(source, False, str(error))
        
        return self.notification_service.create_error_notification(
            error_type, source, context
        )
    
    def handle_api_error(
        self, 
        error: Exception, 
        source: DataSource,
        endpoint: str,
        week: Optional[int] = None,
        status_code: Optional[int] = None
    ) -> Notification:
        """Handle API error with logging and notification creation."""
        
        context = {
            "endpoint": endpoint,
            "week": week,
            "status_code": status_code
        }
        
        # Log the error
        self.log_error(error, source, context)
        
        # Create notification
        notification = self.create_error_notification(
            error, source, status_code, f"Endpoint: {endpoint}"
        )
        
        return notification
    
    def should_retry(
        self, 
        error: Exception, 
        source: DataSource,
        attempt: int,
        max_attempts: int
    ) -> bool:
        """Determine if an error should trigger a retry."""
        
        error_type = self.classify_error(error, source)
        
        # Don't retry authentication errors
        if error_type == ErrorType.AUTHENTICATION_ERROR:
            return False
        
        # Don't retry if max attempts reached
        if attempt >= max_attempts:
            return False
        
        # Retry for transient errors
        retryable_errors = [
            ErrorType.NETWORK_ERROR,
            ErrorType.API_UNAVAILABLE,
            ErrorType.RATE_LIMITED
        ]
        
        return error_type in retryable_errors
    
    def get_fallback_sources(self, failed_source: DataSource) -> List[DataSource]:
        """Get list of fallback sources for a failed primary source."""
        
        fallback_map = {
            DataSource.ODDS_API: [DataSource.ESPN_API, DataSource.NFL_API],
            DataSource.SPORTSDATA_IO: [DataSource.ESPN_API, DataSource.NFL_API, DataSource.RAPID_API],
            DataSource.ESPN_API: [DataSource.NFL_API],
            DataSource.NFL_API: [DataSource.ESPN_API],
            DataSource.RAPID_API: [DataSource.ESPN_API, DataSource.NFL_API]
        }
        
        return fallback_map.get(failed_source, [])
    
    def create_graceful_degradation_response(
        self, 
        failed_sources: List[DataSource],
        available_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create response for graceful degradation scenario."""
        
        notifications = []
        
        if len(failed_sources) == 1:
            # Single source failure - suggest alternatives
            fallback_sources = self.get_fallback_sources(failed_sources[0])
            if fallback_sources:
                notifications.append(
                    self.notification_service.create_api_unavailable_notification(
                        failed_sources[0], trying_backup=True
                    )
                )
            else:
                notifications.append(
                    self.notification_service.create_api_unavailable_notification(
                        failed_sources[0], trying_backup=False
                    )
                )
        else:
            # Multiple source failures
            notifications.append(
                self.notification_service.create_all_sources_failed_notification()
            )
        
        response = {
            "success": available_data is not None,
            "data": available_data or {},
            "notifications": [n.to_dict() for n in notifications],
            "timestamp": datetime.now().isoformat(),
            "cached": False,
            "source": DataSource.CACHE.value if available_data else None
        }
        
        return response
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring."""
        
        return {
            "error_counts": self._error_counts.copy(),
            "last_errors": {
                key: timestamp.isoformat() 
                for key, timestamp in self._last_errors.items()
            },
            "total_errors": sum(self._error_counts.values()),
            "unique_error_types": len(self._error_counts)
        }
    
    def reset_error_statistics(self) -> None:
        """Reset error statistics."""
        self._error_counts.clear()
        self._last_errors.clear()

def handle_api_errors(
    source: DataSource,
    endpoint: str,
    error_handler: ErrorHandler
):
    """Decorator for handling API errors in async functions."""
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Track successful API call
                error_handler.notification_service.track_api_status(source, True)
                
                return result
                
            except Exception as error:
                # Handle the error
                notification = error_handler.handle_api_error(
                    error, source, endpoint, kwargs.get('week')
                )
                
                # Re-raise as APIError for upstream handling
                status_code = getattr(error, 'status', None)
                raise APIError(
                    str(error),
                    error_handler.classify_error(error, source, status_code),
                    source,
                    status_code
                )
        
        return wrapper
    return decorator

def handle_sync_api_errors(
    source: DataSource,
    endpoint: str,
    error_handler: ErrorHandler
):
    """Decorator for handling API errors in synchronous functions."""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Track successful API call
                error_handler.notification_service.track_api_status(source, True)
                
                return result
                
            except Exception as error:
                # Handle the error
                notification = error_handler.handle_api_error(
                    error, source, endpoint, kwargs.get('week')
                )
                
                # Re-raise as APIError for upstream handling
                status_code = getattr(error, 'status', None)
                raise APIError(
                    str(error),
                    error_handler.classify_error(error, source, status_code),
                    source,
                    status_code
                )
        
        return wrapper
    return decorator