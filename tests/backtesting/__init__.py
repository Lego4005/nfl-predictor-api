"""
Backtesting Framework for NFL Expert Prediction System

This package provides comprehensive backtesting capabilities to validate
expert predictions against historical data.

Modules:
- historical_data_loader: Load and manage historical NFL game data
- metrics: Calculate accuracy, ROI, Sharpe ratio, calibration scores
- backtest_runner: Replay historical seasons to validate expert performance
"""

from tests.backtesting.historical_data_loader import HistoricalDataLoader, NFLGame
from tests.backtesting.metrics import MetricsCalculator, Prediction, PredictionResult
from tests.backtesting.backtest_runner import BacktestRunner, ExpertConfig

__all__ = [
    'HistoricalDataLoader',
    'NFLGame',
    'MetricsCalculator',
    'Prediction',
    'PredictionResult',
    'BacktestRunner',
    'ExpertConfig',
]