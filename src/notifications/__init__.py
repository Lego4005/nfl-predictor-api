"""
Notification services for API status communication, error handling, and retry logic.
"""

from .notification_service import (
    NotificationService,
    Notification,
    NotificationType,
    DataSource,
    ErrorType
)

from .error_handler import (
    ErrorHandler,
    APIError,
    handle_api_errors,
    handle_sync_api_errors
)

from .retry_handler import (
    RetryHandler,
    RetryConfig,
    with_retry,
    with_sync_retry,
    RETRY_CONFIGS
)

from .notification_manager import (
    NotificationManager,
    get_notification_manager,
    initialize_notification_manager
)

__all__ = [
    # Core services
    'NotificationService',
    'ErrorHandler', 
    'RetryHandler',
    'NotificationManager',
    
    # Data classes
    'Notification',
    'APIError',
    'RetryConfig',
    
    # Enums
    'NotificationType',
    'DataSource',
    'ErrorType',
    
    # Decorators
    'handle_api_errors',
    'handle_sync_api_errors',
    'with_retry',
    'with_sync_retry',
    
    # Utilities
    'get_notification_manager',
    'initialize_notification_manager',
    'RETRY_CONFIGS'
]