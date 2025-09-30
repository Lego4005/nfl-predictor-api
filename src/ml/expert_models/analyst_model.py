#!/usr/bin/env python3
"""
The Analyst - Comprehensive statistical analysis expert.

Personality:
- Uses ALL available data
- Conservative confidence levels
- Multi-factor weighted model
- Emphasizes historical trends
"""

import sys
import os
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .base_model import BaseExpertModel, Prediction
from services.expert_data_access_layer import GameData


class AnalystModel(BaseExpertModel):
    """
    The Analyst uses comprehensive statistical analysis.

    Weights:
    - Offensive efficiency: 30%
    - Defensive efficiency: 30%
    - Turnover differential: 20%
    - Recent performance: 10%
    - Home field advantage: 10%
    """

    def __init__(self):
        super().__init__(expert_id='the-analyst')

        # Statistical weights
        self.weights = {
            'offense': 0.30,
            'defense': 0.30,
            'turnovers': 0.20,
            'efficiency': 0.10,
            'home_field': 0.10
        }

    async def predict(self, game_data: GameData) -> Prediction:
        """Generate comprehensive statistical prediction"""

        prediction = Prediction(
            expert_id=self.expert_id,
            game_id=game_data.game_id
        )

        # Calculate data completeness
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        # Extract stats
        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})

        if not home_stats or not away_stats:
            # Insufficient data
            prediction.reasoning = "Insufficient statistical data for analysis"
            return prediction

        # Calculate component scores
        offensive_score = self._analyze_offense(home_stats, away_stats)
        defensive_score = self._analyze_defense(home_stats, away_stats)
        turnover_score = self._analyze_turnovers(home_stats, away_stats)
        efficiency_score = self._analyze_efficiency(home_stats, away_stats)

        # Home field advantage
        home_field_bonus = 2.5

        # Weighted total differential
        total_diff = (
            offensive_score * self.weights['offense'] +
            defensive_score * self.weights['defense'] +
            turnover_score * self.weights['turnovers'] +
            efficiency_score * self.weights['efficiency'] +
            home_field_bonus * self.weights['home_field']
        )

        # Winner prediction
        if total_diff > 0:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(
                min(abs(total_diff) / 10, 0.9),
                prediction.data_completeness
            )
        else:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(
                min(abs(total_diff) / 10, 0.9),
                prediction.data_completeness
            )

        # Margin prediction
        prediction.margin = int(abs(total_diff))
        prediction.margin_confidence = prediction.winner_confidence * 0.8

        # Spread prediction
        spread = game_data.odds.get('spread', {})
        if spread.get('home') is not None:
            spread_line = spread['home']

            # Compare our prediction to Vegas line
            if total_diff > spread_line:
                # Home team covers
                prediction.spread_pick = game_data.home_team
                edge = abs(total_diff - spread_line)
            else:
                # Away team covers
                prediction.spread_pick = game_data.away_team
                edge = abs(spread_line - total_diff)

            prediction.spread_confidence = self._calculate_confidence(
                min(edge / 5, 0.85),  # Max 85% confidence on spreads
                prediction.data_completeness
            )

        # Total prediction
        predicted_total = self._predict_total_score(home_stats, away_stats)
        total_line = game_data.odds.get('total', {}).get('line')

        if total_line:
            if predicted_total > total_line + 3:
                prediction.total_pick = "OVER"
                prediction.total_confidence = self._calculate_confidence(
                    min((predicted_total - total_line) / 10, 0.8),
                    prediction.data_completeness
                )
            elif predicted_total < total_line - 3:
                prediction.total_pick = "UNDER"
                prediction.total_confidence = self._calculate_confidence(
                    min((total_line - predicted_total) / 10, 0.8),
                    prediction.data_completeness
                )
            else:
                # Too close to call
                prediction.total_pick = "UNDER"  # Slight lean to under
                prediction.total_confidence = 0.52

            prediction.total_line = total_line

        # Moneyline (same as winner for analyst)
        prediction.moneyline_pick = prediction.winner
        prediction.moneyline_confidence = prediction.winner_confidence

        # Team performance predictions
        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        prediction.home_total_yards = self._safe_get(home_stats, 'total_yards_avg', 350)
        prediction.away_total_yards = self._safe_get(away_stats, 'total_yards_avg', 350)

        prediction.home_touchdowns = max(int(home_ppg / 7), 2)
        prediction.away_touchdowns = max(int(away_ppg / 7), 2)

        prediction.home_turnovers = int(self._safe_get(home_stats, 'turnovers_avg', 1))
        prediction.away_turnovers = int(self._safe_get(away_stats, 'turnovers_avg', 1))

        prediction.home_field_goals = 1 if home_ppg % 7 > 3 else 2
        prediction.away_field_goals = 1 if away_ppg % 7 > 3 else 2

        # Reasoning
        prediction.reasoning = self._build_reasoning(
            game_data, total_diff, offensive_score, defensive_score, turnover_score
        )

        prediction.key_factors = [
            f"Point differential: {total_diff:+.1f}",
            f"Offensive edge: {offensive_score:+.1f}",
            f"Defensive edge: {defensive_score:+.1f}",
            f"Turnover factor: {turnover_score:+.1f}"
        ]

        self.predictions_made += 1
        self.total_confidence += prediction.winner_confidence

        return prediction

    def _analyze_offense(self, home_stats: Dict, away_stats: Dict) -> float:
        """Analyze offensive matchup"""
        home_offense = (
            self._safe_get(home_stats, 'points_avg', 20) * 0.4 +
            self._safe_get(home_stats, 'total_yards_avg', 350) / 50 * 0.3 +
            self._safe_get(home_stats, 'third_down_pct', 40) / 5 * 0.3
        )

        away_offense = (
            self._safe_get(away_stats, 'points_avg', 20) * 0.4 +
            self._safe_get(away_stats, 'total_yards_avg', 350) / 50 * 0.3 +
            self._safe_get(away_stats, 'third_down_pct', 40) / 5 * 0.3
        )

        return home_offense - away_offense

    def _analyze_defense(self, home_stats: Dict, away_stats: Dict) -> float:
        """Analyze defensive matchup"""
        home_defense = (
            -self._safe_get(home_stats, 'points_allowed_avg', 20) * 0.5 +
            self._safe_get(home_stats, 'takeaways_avg', 1) * 3 +
            self._safe_get(home_stats, 'sacks', 10) * 0.3
        )

        away_defense = (
            -self._safe_get(away_stats, 'points_allowed_avg', 20) * 0.5 +
            self._safe_get(away_stats, 'takeaways_avg', 1) * 3 +
            self._safe_get(away_stats, 'sacks', 10) * 0.3
        )

        return home_defense - away_defense

    def _analyze_turnovers(self, home_stats: Dict, away_stats: Dict) -> float:
        """Analyze turnover differential"""
        home_diff = (
            self._safe_get(home_stats, 'takeaways_avg', 1) -
            self._safe_get(home_stats, 'turnovers_avg', 1)
        )

        away_diff = (
            self._safe_get(away_stats, 'takeaways_avg', 1) -
            self._safe_get(away_stats, 'turnovers_avg', 1)
        )

        # Each turnover worth ~4 points
        return (home_diff - away_diff) * 4

    def _analyze_efficiency(self, home_stats: Dict, away_stats: Dict) -> float:
        """Analyze overall efficiency"""
        home_eff = (
            self._safe_get(home_stats, 'third_down_pct', 40) * 0.4 +
            self._safe_get(home_stats, 'red_zone_pct', 55) * 0.3 +
            (60 - self._safe_get(home_stats, 'penalties', 50)) * 0.3
        )

        away_eff = (
            self._safe_get(away_stats, 'third_down_pct', 40) * 0.4 +
            self._safe_get(away_stats, 'red_zone_pct', 55) * 0.3 +
            (60 - self._safe_get(away_stats, 'penalties', 50)) * 0.3
        )

        return (home_eff - away_eff) / 10

    def _build_reasoning(
        self,
        game_data: GameData,
        total_diff: float,
        offensive_score: float,
        defensive_score: float,
        turnover_score: float
    ) -> str:
        """Build human-readable reasoning"""

        home = game_data.home_team
        away = game_data.away_team

        reasoning_parts = []

        # Main prediction
        if total_diff > 0:
            reasoning_parts.append(
                f"{home} projected to win by {abs(total_diff):.1f} points"
            )
        else:
            reasoning_parts.append(
                f"{away} projected to win by {abs(total_diff):.1f} points"
            )

        # Key factors
        if abs(offensive_score) > 3:
            leader = home if offensive_score > 0 else away
            reasoning_parts.append(
                f"{leader} has significant offensive advantage"
            )

        if abs(defensive_score) > 3:
            leader = home if defensive_score > 0 else away
            reasoning_parts.append(
                f"{leader}'s defense is notably stronger"
            )

        if abs(turnover_score) > 4:
            leader = home if turnover_score > 0 else away
            reasoning_parts.append(
                f"{leader} has superior turnover differential"
            )

        return ". ".join(reasoning_parts) + "."