#!/usr/bin/env python3
"""
Base Expert Model - Abstract interface for all expert prediction models.

Each expert implements their own prediction logic based on personality.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from services.expert_data_access_layer import GameData


@dataclass
class Prediction:
    """Structured prediction output from an expert"""

    # Metadata
    expert_id: str
    game_id: str
    timestamp: datetime = field(default_factory=datetime.now)

    # Core predictions (15 for MVP)
    winner: Optional[str] = None
    winner_confidence: float = 0.0

    spread_pick: Optional[str] = None  # "KC" or "BUF"
    spread_confidence: float = 0.0

    total_pick: Optional[str] = None  # "OVER" or "UNDER"
    total_line: Optional[float] = None
    total_confidence: float = 0.0

    moneyline_pick: Optional[str] = None
    moneyline_confidence: float = 0.0

    margin: Optional[int] = None  # Predicted point margin
    margin_confidence: float = 0.0

    # Team performance predictions
    home_total_yards: Optional[float] = None
    away_total_yards: Optional[float] = None

    home_touchdowns: Optional[int] = None
    away_touchdowns: Optional[int] = None

    home_turnovers: Optional[int] = None
    away_turnovers: Optional[int] = None

    home_field_goals: Optional[int] = None
    away_field_goals: Optional[int] = None

    # Reasoning
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)

    # Metadata about prediction quality
    data_completeness: float = 1.0  # 0-1, how much data was available

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'expert_id': self.expert_id,
            'game_id': self.game_id,
            'timestamp': self.timestamp.isoformat(),
            'winner': self.winner,
            'winner_confidence': self.winner_confidence,
            'spread_pick': self.spread_pick,
            'spread_confidence': self.spread_confidence,
            'total_pick': self.total_pick,
            'total_line': self.total_line,
            'total_confidence': self.total_confidence,
            'moneyline_pick': self.moneyline_pick,
            'moneyline_confidence': self.moneyline_confidence,
            'margin': self.margin,
            'margin_confidence': self.margin_confidence,
            'home_total_yards': self.home_total_yards,
            'away_total_yards': self.away_total_yards,
            'home_touchdowns': self.home_touchdowns,
            'away_touchdowns': self.away_touchdowns,
            'home_turnovers': self.home_turnovers,
            'away_turnovers': self.away_turnovers,
            'home_field_goals': self.home_field_goals,
            'away_field_goals': self.away_field_goals,
            'reasoning': self.reasoning,
            'key_factors': self.key_factors,
            'data_completeness': self.data_completeness
        }


class BaseExpertModel(ABC):
    """
    Abstract base class for all expert models.

    Each expert personality extends this and implements predict().
    """

    def __init__(self, expert_id: str):
        self.expert_id = expert_id
        self.predictions_made = 0
        self.total_confidence = 0.0

    @abstractmethod
    async def predict(self, game_data: GameData) -> Prediction:
        """
        Generate prediction based on game data.

        Args:
            game_data: Filtered data from ExpertDataAccessLayer

        Returns:
            Prediction object with all picks and confidence scores
        """
        pass

    def _calculate_data_completeness(self, game_data: GameData) -> float:
        """Calculate how complete the input data is (0-1)"""
        completeness = 0.0
        total_checks = 5

        if game_data.team_stats and game_data.team_stats.get('home_stats'):
            completeness += 0.3
        if game_data.team_stats and game_data.team_stats.get('away_stats'):
            completeness += 0.3
        if game_data.odds:
            completeness += 0.2
        if game_data.injuries:
            completeness += 0.1
        if game_data.weather:
            completeness += 0.1

        return min(completeness, 1.0)

    def _safe_get(self, data: Dict, key: str, default=0) -> float:
        """Safely get a value from dict, return default if missing"""
        try:
            return float(data.get(key, default))
        except (TypeError, ValueError):
            return default

    def _calculate_point_differential(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """
        Calculate expected point differential.
        Positive = home team favored
        """
        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        home_allowed = self._safe_get(home_stats, 'points_allowed_avg', 20)
        away_allowed = self._safe_get(away_stats, 'points_allowed_avg', 20)

        # Simple differential
        home_advantage = 2.5  # Home field worth ~2.5 points

        # Expected score differential
        diff = (home_ppg - away_allowed + away_allowed - away_ppg) / 2 + home_advantage

        return diff

    def _predict_total_score(
        self,
        home_stats: Dict,
        away_stats: Dict
    ) -> float:
        """Predict total combined score"""
        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        home_allowed = self._safe_get(home_stats, 'points_allowed_avg', 20)
        away_allowed = self._safe_get(away_stats, 'points_allowed_avg', 20)

        # Average of offense vs defense matchups
        home_expected = (home_ppg + away_allowed) / 2
        away_expected = (away_ppg + home_allowed) / 2

        return home_expected + away_expected

    def _calculate_confidence(
        self,
        prediction_strength: float,
        data_completeness: float
    ) -> float:
        """
        Calculate confidence score (0-1).

        Args:
            prediction_strength: How strong the prediction signal is (0-1)
            data_completeness: How complete the input data is (0-1)

        Returns:
            Confidence score weighted by data quality
        """
        # Weight prediction strength by data completeness
        confidence = prediction_strength * (0.5 + 0.5 * data_completeness)
        return min(max(confidence, 0.0), 1.0)  # Clamp to 0-1

    def __repr__(self):
        return f"{self.__class__.__name__}(expert_id='{self.expert_id}')"