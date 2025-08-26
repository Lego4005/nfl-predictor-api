"""
Retry handler with exponential backoff for API calls.
Implements configurable retry limits, timeout handling, and user feedback for retry attempts.
"""

import asyncio
import logging
from typing import Callable, Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from functools import wraps
import random

from .notification_service import (
    NotificationService, 
    DataSource, 
    ErrorType, 
    Notification
)
from .error_handler import ErrorHandler, APIError

class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.timeout = timeout

class RetryHandler:
    """
    Handles retry logic with exponential backoff and user feedback.
    """
    
    def __init__(
        self, 
        notification_service: NotificationService,
        error_handler: ErrorHandler,
        default_config: Optional[RetryConfig] = None
    ):
        self.notification_service = notification_service
        self.error_handler = error_handler
        self.logger = logging.getLogger(__name__)
        self.default_config = default_config or RetryConfig()
        
        # Track retry attempts per source/endpoint
        self._retry_tracking: Dict[str, Dict[str, Any]] = {}
    
    def _get_retry_key(self, source: DataSource, endpoint: str, week: Optional[int] = None) -> str:
        """Generate unique key for tracking retries."""
        key_parts = [source.value, endpoint]
        if week is not None:
            key_parts.append(str(week))
        return "_".join(key_parts)
    
    def _calculate_delay(
        self, 
        attempt: int, 
        config: RetryConfig,
        error_type: Optional[ErrorType] = None
    ) -> float:
        """Calculate delay for retry attempt with exponential backoff."""
        
        # Base delay calculation
        delay = config.base_delay * (config.backoff_factor ** attempt)
        
        # Apply maximum delay limit
        delay = min(delay, config.max_delay)
        
        # Add jitter to prevent thundering herd
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
        
        # Special handling for rate limiting
        if error_type == ErrorType.RATE_LIMITED:
            # For rate limiting, use longer delays
            delay = max(delay, 60.0)  # At least 1 minute for rate limits
        
        return max(0, delay)
    
    def _should_retry(
        self, 
        error: Exception, 
        source: DataSource,
        attempt: int,
        config: RetryConfig
    ) -> bool:
        """Determine if we should retry based on error and attempt count."""
        
        # Check max attempts
        if attempt >= config.max_retries:
            return False
        
        # Use error handler to determine if error is retryable
        return self.error_handler.should_retry(error, source, attempt, config.max_retries)
    
    def _track_retry_attempt(
        self, 
        retry_key: str, 
        source: DataSource,
        attempt: int,
        error: Exception,
        delay: float
    ) -> None:
        """Track retry attempt for monitoring and feedback."""
        
        self._retry_tracking[retry_key] = {
            "source": source,
            "attempt": attempt,
            "last_error": str(error),
            "last_attempt": datetime.now(),
            "next_retry": datetime.now() + timedelta(seconds=delay),
            "total_delay": delay
        }
    
    def _create_retry_notification(
        self, 
        source: DataSource, 
        attempt: int, 
        max_attempts: int,
        delay: float
    ) -> Notification:
        """Create notification for retry attempt."""
        
        return self.notification_service.create_retry_attempt_notification(
            source, attempt, max_attempts
        )
    
    async def retry_async(
        self,
        func: Callable,
        source: DataSource,
        endpoint: str,
        config: Optional[RetryConfig] = None,
        week: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute async function with retry logic and exponential backoff.
        """
        
        config = config or self.default_config
        retry_key = self._get_retry_key(source, endpoint, week)
        
        last_error = None
        
        for attempt in range(config.max_retries + 1):
            try:
                # Set timeout for the operation
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=config.timeout
                )
                
                # Success - clear retry tracking and notify if recovered
                if retry_key in self._retry_tracking:
                    del self._retry_tracking[retry_key]
                    
                    # If this was a retry (attempt > 0), notify of recovery
                    if attempt > 0:
                        recovery_notification = self.notification_service.create_api_recovered_notification(source)
                        self.logger.info(f"API recovered after {attempt} retries: {source.value}")
                
                return result
                
            except Exception as error:
                last_error = error
                
                # Log the error
                self.error_handler.log_error(
                    error, 
                    source, 
                    {
                        "endpoint": endpoint,
                        "week": week,
                        "attempt": attempt + 1,
                        "max_attempts": config.max_retries + 1
                    },
                    level=logging.WARNING if attempt < config.max_retries else logging.ERROR
                )
                
                # Check if we should retry
                if not self._should_retry(error, source, attempt, config):
                    break
                
                # Calculate delay for next attempt
                error_type = self.error_handler.classify_error(error, source)
                delay = self._calculate_delay(attempt, config, error_type)
                
                # Track retry attempt
                self._track_retry_attempt(retry_key, source, attempt + 1, error, delay)
                
                # Create retry notification
                retry_notification = self._create_retry_notification(
                    source, attempt + 1, config.max_retries, delay
                )
                
                self.logger.info(
                    f"Retrying {source.value} in {delay:.1f}s (attempt {attempt + 1}/{config.max_retries + 1})"
                )
                
                # Wait before retry
                await asyncio.sleep(delay)
        
        # All retries exhausted - raise the last error
        if last_error:
            # Clean up retry tracking
            if retry_key in self._retry_tracking:
                del self._retry_tracking[retry_key]
            
            raise last_error
        
        # This shouldn't happen, but just in case
        raise RuntimeError("Retry logic failed unexpectedly")
    
    def retry_sync(
        self,
        func: Callable,
        source: DataSource,
        endpoint: str,
        config: Optional[RetryConfig] = None,
        week: Optional[int] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute synchronous function with retry logic and exponential backoff.
        """
        
        config = config or self.default_config
        retry_key = self._get_retry_key(source, endpoint, week)
        
        last_error = None
        
        for attempt in range(config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # Success - clear retry tracking and notify if recovered
                if retry_key in self._retry_tracking:
                    del self._retry_tracking[retry_key]
                    
                    # If this was a retry (attempt > 0), notify of recovery
                    if attempt > 0:
                        recovery_notification = self.notification_service.create_api_recovered_notification(source)
                        self.logger.info(f"API recovered after {attempt} retries: {source.value}")
                
                return result
                
            except Exception as error:
                last_error = error
                
                # Log the error
                self.error_handler.log_error(
                    error, 
                    source, 
                    {
                        "endpoint": endpoint,
                        "week": week,
                        "attempt": attempt + 1,
                        "max_attempts": config.max_retries + 1
                    },
                    level=logging.WARNING if attempt < config.max_retries else logging.ERROR
                )
                
                # Check if we should retry
                if not self._should_retry(error, source, attempt, config):
                    break
                
                # Calculate delay for next attempt
                error_type = self.error_handler.classify_error(error, source)
                delay = self._calculate_delay(attempt, config, error_type)
                
                # Track retry attempt
                self._track_retry_attempt(retry_key, source, attempt + 1, error, delay)
                
                # Create retry notification
                retry_notification = self._create_retry_notification(
                    source, attempt + 1, config.max_retries, delay
                )
                
                self.logger.info(
                    f"Retrying {source.value} in {delay:.1f}s (attempt {attempt + 1}/{config.max_retries + 1})"
                )
                
                # Wait before retry (synchronous sleep)
                import time
                time.sleep(delay)
        
        # All retries exhausted - raise the last error
        if last_error:
            # Clean up retry tracking
            if retry_key in self._retry_tracking:
                del self._retry_tracking[retry_key]
            
            raise last_error
        
        # This shouldn't happen, but just in case
        raise RuntimeError("Retry logic failed unexpectedly")
    
    def get_retry_status(self, source: DataSource, endpoint: str, week: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Get current retry status for a specific source/endpoint."""
        
        retry_key = self._get_retry_key(source, endpoint, week)
        return self._retry_tracking.get(retry_key)
    
    def get_all_retry_status(self) -> Dict[str, Dict[str, Any]]:
        """Get retry status for all tracked operations."""
        
        return {
            key: {
                **status,
                "source": status["source"].value,
                "last_attempt": status["last_attempt"].isoformat(),
                "next_retry": status["next_retry"].isoformat()
            }
            for key, status in self._retry_tracking.items()
        }
    
    def clear_retry_tracking(self, source: Optional[DataSource] = None) -> None:
        """Clear retry tracking data."""
        
        if source:
            # Clear tracking for specific source
            keys_to_remove = [
                key for key in self._retry_tracking.keys()
                if key.startswith(source.value)
            ]
            for key in keys_to_remove:
                del self._retry_tracking[key]
        else:
            # Clear all tracking
            self._retry_tracking.clear()

def with_retry(
    source: DataSource,
    endpoint: str,
    config: Optional[RetryConfig] = None,
    retry_handler: Optional[RetryHandler] = None
):
    """Decorator for adding retry logic to async functions."""
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if retry_handler is None:
                # If no retry handler provided, execute without retry
                return await func(*args, **kwargs)
            
            return await retry_handler.retry_async(
                func, source, endpoint, config, kwargs.get('week'), *args, **kwargs
            )
        
        return wrapper
    return decorator

def with_sync_retry(
    source: DataSource,
    endpoint: str,
    config: Optional[RetryConfig] = None,
    retry_handler: Optional[RetryHandler] = None
):
    """Decorator for adding retry logic to synchronous functions."""
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if retry_handler is None:
                # If no retry handler provided, execute without retry
                return func(*args, **kwargs)
            
            return retry_handler.retry_sync(
                func, source, endpoint, config, kwargs.get('week'), *args, **kwargs
            )
        
        return wrapper
    return decorator

# Predefined retry configurations for different scenarios
RETRY_CONFIGS = {
    "default": RetryConfig(max_retries=3, base_delay=1.0, backoff_factor=2.0),
    "aggressive": RetryConfig(max_retries=5, base_delay=0.5, backoff_factor=1.5),
    "conservative": RetryConfig(max_retries=2, base_delay=2.0, backoff_factor=3.0),
    "rate_limited": RetryConfig(max_retries=3, base_delay=60.0, backoff_factor=1.5, max_delay=300.0),
    "network_issues": RetryConfig(max_retries=4, base_delay=2.0, backoff_factor=2.0, timeout=60.0)
}