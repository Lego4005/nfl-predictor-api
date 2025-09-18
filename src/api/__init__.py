"""
API module initialization
Exports all routers for main application
"""

from .clean_predictions_endpoints import router as predictions_router
from .real_data_endpoints import router as real_data_router
from .performance_endpoints import router as performance_router

__all__ = ['predictions_router', 'real_data_router', 'performance_router']