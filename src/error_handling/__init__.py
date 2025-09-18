"""
Error Handling Module

Provides comprehensive error handling, retry logic, and resilient connections
for the NFL prediction pipeline.
"""

from .resilient_connection import (
    ResilientConnection,
    ConnectionManager,
    CircuitBreaker,
    RetryHandler,
    ErrorSeverity,
    ConnectionState,
    CircuitState,
    ErrorInfo,
    RetryConfig,
    CircuitBreakerConfig,
    connection_manager
)

__all__ = [
    'ResilientConnection',
    'ConnectionManager',
    'CircuitBreaker',
    'RetryHandler',
    'ErrorSeverity',
    'ConnectionState',
    'CircuitState',
    'ErrorInfo',
    'RetryConfig',
    'CircuitBreakerConfig',
    'connection_manager'
]