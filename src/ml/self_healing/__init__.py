"""
Self-Healing Module
Implements performance monitoring, decline detection, and adaptive mechanisms
"""

from .performance_decline_detector import (
    PerformanceDeclineDetector,
    DeclineType,
    DeclineSeverity,
    DeclineThresholds,
    DeclineAlert
)
from .adaptation_engine import (
    AdaptationEngine,
    AdaptationType,
    AdaptationStatus,
    AdaptationStrategy,
    AdaptationRecord
)

__all__ = [
    'PerformanceDeclineDetector',
    'DeclineType',
    'DeclineSeverity', 
    'DeclineThresholds',
    'DeclineAlert',
    'AdaptationEngine',
    'AdaptationType',
    'AdaptationStatus',
    'AdaptationStrategy',
    'AdaptationRecord'
]