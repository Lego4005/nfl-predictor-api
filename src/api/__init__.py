"""
API module initialization
Exports all routers for main application
"""

from .auth_endpoints import router as auth_router
from .payment_endpoints import router as payment_router
from .subscription_endpoints import router as subscription_router

__all__ = ['auth_router', 'payment_router', 'subscription_router']