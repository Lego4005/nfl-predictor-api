"""
Virtual Bankroll Betting System Services

This package provides comprehensive betting system functionality for AI expert predictions:
- Kelly Criterion bet sizing with personality adjustments
- Bankroll management with risk metrics
- Automatic bet placement for high-confidence predictions
- Bet settlement with payout calculations

Author: Financial Systems Engineer
Created: 2025-09-29
"""

from .bet_sizer import BetSizer, get_bet_sizer
from .bankroll_manager import BankrollManager
from .bet_placer import BetPlacer
from .bet_settler import BetSettler

__all__ = [
    'BetSizer',
    'get_bet_sizer',
    'BankrollManager',
    'BetPlacer',
    'BetSettler'
]

__version__ = '1.0.0'