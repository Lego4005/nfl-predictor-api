"""
Integration Module

Provides complete integration of all real-time data pipeline components
including WebSocket connections, caching, validation, rate limiting, and error handling.
"""

from .pipeline_integration import (
    PipelineIntegration,
    pipeline_integration,
    create_app,
    run_development_server
)

__all__ = [
    'PipelineIntegration',
    'pipeline_integration',
    'create_app',
    'run_development_server'
]