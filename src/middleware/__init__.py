"""
Middleware Module

Provides middleware components for the NFL prediction API including
rate limiting, authentication, and request processing.
"""

from .rate_limiting import (
    AdvancedRateLimiter,
    RateLimitMiddleware,
    RateLimitStrategy,
    RateLimitScope,
    RateLimitRule,
    RateLimitResult,
    rate_limiter
)

__all__ = [
    'AdvancedRateLimiter',
    'RateLimitMiddleware',
    'RateLimitStrategy',
    'RateLimitScope',
    'RateLimitRule',
    'RateLimitResult',
    'rate_limiter'
]