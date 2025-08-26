"""
Notification manager that integrates all notification, error handling, and retry components.
Provides a unified interface for managing API communications and user notifications.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from .notification_service import NotificationService, DataSource, Notification
from .error_handler import ErrorHandler, APIError
from .retry_handler import RetryHandler, RetryConfig, RETRY_CONFIGS

class NotificationManager:
    """
    Unified manager for all notification, error handling, and retry functionality.
    """
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """Initialize the notification manager with all components."""
        
        self.notification_service = NotificationService()
        self.error_handler = ErrorHandler(self.notification_service)
        self.retry_handler = RetryHandler(
            self.notification_service, 
            self.error_handler,
            retry_config or RETRY_CONFIGS["default"]
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Track active notifications
        self._active_notifications: List[Notification] = []
        
    async def execute_with_retry(
        self,
        func: Callable,
        source: DataSource,
        endpoint: str,
        week: Optional[int] = None,
        retry_config: Optional[str] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a function with full error handling, retry logic, and notifications.
        
        Args:
            func: The async function to execute
            source: Data source being accessed
            endpoint: API endpoint being called
            week: NFL week (if applicable)
            retry_config: Name of retry config to use (from RETRY_CONFIGS)
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Dict containing result data and notifications
        """
        
        config = None
        if retry_config and retry_config in RETRY_CONFIGS:
            config = RETRY_CONFIGS[retry_config]
        
        notifications = []
        
        try:
            # Execute with retry logic
            result = await self.retry_handler.retry_async(
                func, source, endpoint, config, week, *args, **kwargs
            )
            
            # Success - create success notification if this was a recovery
            retry_status = self.retry_handler.get_retry_status(source, endpoint, week)
            if retry_status and retry_status["attempt"] > 1:
                recovery_notification = self.notification_service.create_api_recovered_notification(source)
                notifications.append(recovery_notification)
            
            return {
                "success": True,
                "data": result,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications]
            }
            
        except APIError as api_error:
            # Handle API-specific errors
            error_notification = self.notification_service.create_error_notification(
                api_error.error_type, source, str(api_error)
            )
            notifications.append(error_notification)
            
            # Try fallback sources
            fallback_sources = self.error_handler.get_fallback_sources(source)
            if fallback_sources:
                fallback_notification = self.notification_service.create_api_unavailable_notification(
                    source, trying_backup=True
                )
                notifications.append(fallback_notification)
            
            return {
                "success": False,
                "data": None,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications],
                "error": {
                    "type": api_error.error_type.value,
                    "message": str(api_error),
                    "retryable": api_error.error_type.value != "authentication_error"
                }
            }
            
        except Exception as error:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in {source.value}: {str(error)}")
            
            error_notification = self.notification_service.create_error_notification(
                self.error_handler.classify_error(error, source), 
                source, 
                str(error)
            )
            notifications.append(error_notification)
            
            return {
                "success": False,
                "data": None,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications],
                "error": {
                    "type": "unknown_error",
                    "message": str(error),
                    "retryable": True
                }
            }
    
    def execute_sync_with_retry(
        self,
        func: Callable,
        source: DataSource,
        endpoint: str,
        week: Optional[int] = None,
        retry_config: Optional[str] = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a synchronous function with full error handling, retry logic, and notifications.
        """
        
        config = None
        if retry_config and retry_config in RETRY_CONFIGS:
            config = RETRY_CONFIGS[retry_config]
        
        notifications = []
        
        try:
            # Execute with retry logic
            result = self.retry_handler.retry_sync(
                func, source, endpoint, config, week, *args, **kwargs
            )
            
            # Success - create success notification if this was a recovery
            retry_status = self.retry_handler.get_retry_status(source, endpoint, week)
            if retry_status and retry_status["attempt"] > 1:
                recovery_notification = self.notification_service.create_api_recovered_notification(source)
                notifications.append(recovery_notification)
            
            return {
                "success": True,
                "data": result,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications]
            }
            
        except APIError as api_error:
            # Handle API-specific errors
            error_notification = self.notification_service.create_error_notification(
                api_error.error_type, source, str(api_error)
            )
            notifications.append(error_notification)
            
            # Try fallback sources
            fallback_sources = self.error_handler.get_fallback_sources(source)
            if fallback_sources:
                fallback_notification = self.notification_service.create_api_unavailable_notification(
                    source, trying_backup=True
                )
                notifications.append(fallback_notification)
            
            return {
                "success": False,
                "data": None,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications],
                "error": {
                    "type": api_error.error_type.value,
                    "message": str(api_error),
                    "retryable": api_error.error_type.value != "authentication_error"
                }
            }
            
        except Exception as error:
            # Handle unexpected errors
            self.logger.error(f"Unexpected error in {source.value}: {str(error)}")
            
            error_notification = self.notification_service.create_error_notification(
                self.error_handler.classify_error(error, source), 
                source, 
                str(error)
            )
            notifications.append(error_notification)
            
            return {
                "success": False,
                "data": None,
                "source": source.value,
                "cached": False,
                "timestamp": datetime.now().isoformat(),
                "notifications": [n.to_dict() for n in notifications],
                "error": {
                    "type": "unknown_error",
                    "message": str(error),
                    "retryable": True
                }
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including all APIs and retry states."""
        
        return {
            "api_status": self.notification_service.get_all_api_status(),
            "retry_status": self.retry_handler.get_all_retry_status(),
            "error_statistics": self.error_handler.get_error_statistics(),
            "active_notifications": [n.to_dict() for n in self._active_notifications],
            "timestamp": datetime.now().isoformat()
        }
    
    def add_notification(self, notification: Notification) -> None:
        """Add a notification to the active notifications list."""
        self._active_notifications.append(notification)
        
        # Keep only recent notifications (last 50)
        if len(self._active_notifications) > 50:
            self._active_notifications = self._active_notifications[-50:]
    
    def clear_notifications(self, notification_type: Optional[str] = None) -> None:
        """Clear notifications, optionally filtered by type."""
        
        if notification_type:
            self._active_notifications = [
                n for n in self._active_notifications 
                if n.type.value != notification_type
            ]
        else:
            self._active_notifications.clear()
    
    def get_notifications(self, source: Optional[DataSource] = None) -> List[Dict[str, Any]]:
        """Get active notifications, optionally filtered by source."""
        
        notifications = self._active_notifications
        
        if source:
            notifications = [n for n in notifications if n.source == source]
        
        return [n.to_dict() for n in notifications]
    
    def reset_all_tracking(self) -> None:
        """Reset all tracking data (useful for testing or maintenance)."""
        
        self.retry_handler.clear_retry_tracking()
        self.error_handler.reset_error_statistics()
        self._active_notifications.clear()
        
        self.logger.info("All notification tracking data has been reset")

# Global notification manager instance
_notification_manager: Optional[NotificationManager] = None

def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _notification_manager
    
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    
    return _notification_manager

def initialize_notification_manager(retry_config: Optional[RetryConfig] = None) -> NotificationManager:
    """Initialize the global notification manager with custom configuration."""
    global _notification_manager
    
    _notification_manager = NotificationManager(retry_config)
    return _notification_manager