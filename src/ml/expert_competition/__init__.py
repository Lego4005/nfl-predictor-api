"""
Expert Competition System
Manages 15 competing AI experts with dynamic ranking and council selection
"""

from .competition_framework import ExpertCompetitionFramework, ExpertPerformanceMetrics, CompetitionRound
from .mock_expert import MockExpert

__all__ = [
    'ExpertCompetitionFramework',
    'ExpertPerformanceMetrics', 
    'CompetitionRound',
    'MockExpert'
]