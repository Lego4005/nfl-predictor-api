"""
Database models package for NFL predictor.
"""

from .historical_games import (
    Base,
    HistoricalGame,
    TeamStats,
    PlayerStats,
    BettingData,
    Injury,
    create_all_tables,
    drop_all_tables,
    get_performance_indexes
)

__all__ = [
    'Base',
    'HistoricalGame',
    'TeamStats',
    'PlayerStats',
    'BettingData',
    'Injury',
    'create_all_tables',
    'drop_all_tables',
    'get_performance_indexes'
]