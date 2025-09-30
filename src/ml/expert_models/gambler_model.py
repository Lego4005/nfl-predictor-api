#!/usr/bin/env python3
"""
The Gambler - Odds-focused, aggressive betting expert.

Personality:
- Follows Vegas lines closely
- Higher confidence levels
- Looks for value in spreads
- Recent performance weighted heavily
"""

import sys
import os
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .base_model import BaseExpertModel, Prediction
from services.expert_data_access_layer import GameData


class GamblerModel(BaseExpertModel):
    """
    The Gambler trusts Vegas and looks for value.

    Strategy:
    - Vegas line is the baseline
    - Recent performance matters most
    - Will take +value when found
    - Higher confidence (more aggressive)
    """

    def __init__(self):
        super().__init__(expert_id='the-gambler')

    async def predict(self, game_data: GameData) -> Prediction:
        """Generate odds-based prediction"""

        prediction = Prediction(
            expert_id=self.expert_id,
            game_id=game_data.game_id
        )

        prediction.data_completeness = self._calculate_data_completeness(game_data)

        # Extract data
        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})
        odds = game_data.odds

        if not odds:
            prediction.reasoning = "No odds available - passing on this game"
            return prediction

        # Moneyline tells us who Vegas favors
        moneyline = odds.get('moneyline', {})
        spread = odds.get('spread', {})
        total = odds.get('total', {})

        # Winner prediction based on moneyline
        home_ml = moneyline.get('home')
        away_ml = moneyline.get('away')

        if home_ml and away_ml:
            # Negative = favorite
            if home_ml < away_ml:
                prediction.winner = game_data.home_team
                # Convert American odds to implied probability
                implied_prob = abs(home_ml) / (abs(home_ml) + 100)
                prediction.winner_confidence = self._calculate_confidence(
                    implied_prob,
                    prediction.data_completeness
                )
            else:
                prediction.winner = game_data.away_team
                implied_prob = abs(away_ml) / (abs(away_ml) + 100)
                prediction.winner_confidence = self._calculate_confidence(
                    implied_prob,
                    prediction.data_completeness
                )

        # Spread prediction - look for value
        spread_line = spread.get('home')
        if spread_line is not None:
            # Calculate our power rating differential
            recent_form_diff = self._calculate_recent_form(home_stats, away_stats)

            # Compare to Vegas line
            if recent_form_diff > spread_line + 1.5:
                # Home team value
                prediction.spread_pick = game_data.home_team
                edge = recent_form_diff - spread_line
                prediction.spread_confidence = self._calculate_confidence(
                    min(edge / 4, 0.9),  # Gambler takes higher confidence
                    prediction.data_completeness
                )
            elif recent_form_diff < spread_line - 1.5:
                # Away team value
                prediction.spread_pick = game_data.away_team
                edge = spread_line - recent_form_diff
                prediction.spread_confidence = self._calculate_confidence(
                    min(edge / 4, 0.9),
                    prediction.data_completeness
                )
            else:
                # No clear value - side with favorite but low confidence
                if spread_line < 0:
                    prediction.spread_pick = game_data.home_team
                else:
                    prediction.spread_pick = game_data.away_team
                prediction.spread_confidence = 0.55

        # Total prediction
        total_line = total.get('line')
        if total_line and home_stats and away_stats:
            # Recent scoring trends
            home_ppg = self._safe_get(home_stats, 'points_avg', 20)
            away_ppg = self._safe_get(away_stats, 'points_avg', 20)

            projected_total = home_ppg + away_ppg + 3  # Slight over bias

            if projected_total > total_line + 4:
                prediction.total_pick = "OVER"
                prediction.total_confidence = self._calculate_confidence(
                    min((projected_total - total_line) / 8, 0.85),
                    prediction.data_completeness
                )
            elif projected_total < total_line - 4:
                prediction.total_pick = "UNDER"
                prediction.total_confidence = self._calculate_confidence(
                    min((total_line - projected_total) / 8, 0.85),
                    prediction.data_completeness
                )
            else:
                # Slight over lean (gambler bias)
                prediction.total_pick = "OVER"
                prediction.total_confidence = 0.58

            prediction.total_line = total_line

        # Moneyline (same as winner)
        prediction.moneyline_pick = prediction.winner
        prediction.moneyline_confidence = prediction.winner_confidence

        # Margin prediction based on spread
        if spread_line is not None:
            prediction.margin = int(abs(spread_line) + 2)  # Add a bit
            prediction.margin_confidence = 0.65

        # Team performance (use stats if available)
        if home_stats and away_stats:
            prediction.home_total_yards = self._safe_get(home_stats, 'total_yards_avg', 350)
            prediction.away_total_yards = self._safe_get(away_stats, 'total_yards_avg', 350)

            home_ppg = self._safe_get(home_stats, 'points_avg', 20)
            away_ppg = self._safe_get(away_stats, 'points_avg', 20)

            prediction.home_touchdowns = max(int(home_ppg / 7), 2)
            prediction.away_touchdowns = max(int(away_ppg / 7), 2)

            prediction.home_turnovers = int(self._safe_get(home_stats, 'turnovers_avg', 1))
            prediction.away_turnovers = int(self._safe_get(away_stats, 'turnovers_avg', 1))

        # Reasoning
        prediction.reasoning = self._build_reasoning(
            game_data, spread_line, total_line, home_ml, away_ml
        )

        prediction.key_factors = [
            f"Vegas spread: {spread_line:+.1f}" if spread_line else "No spread",
            f"Total line: {total_line}" if total_line else "No total",
            f"Moneyline: {home_ml}/{away_ml}" if home_ml and away_ml else "No ML"
        ]

        self.predictions_made += 1
        self.total_confidence += prediction.winner_confidence

        return prediction

    def _calculate_recent_form(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calculate power rating based on recent performance"""

        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        home_allowed = self._safe_get(home_stats, 'points_allowed_avg', 20)
        away_allowed = self._safe_get(away_stats, 'points_allowed_avg', 20)

        # Simple power rating
        home_power = home_ppg - home_allowed
        away_power = away_ppg - away_allowed

        # Home field
        home_field = 2.5

        return home_power - away_power + home_field

    def _build_reasoning(
        self,
        game_data: GameData,
        spread_line: float,
        total_line: float,
        home_ml: int,
        away_ml: int
    ) -> str:
        """Build reasoning focused on odds"""

        parts = []

        # Who's favored
        if home_ml and away_ml:
            if home_ml < 0:
                parts.append(f"{game_data.home_team} favored at {home_ml}")
            else:
                parts.append(f"{game_data.away_team} favored at {away_ml}")

        # Spread value
        if spread_line is not None:
            if spread_line < -7:
                parts.append("Large spread - looking for value on underdog")
            elif spread_line < -3:
                parts.append("Moderate favorite - following the line")
            elif abs(spread_line) <= 3:
                parts.append("Pick'em game - taking value where found")

        # Total
        if total_line:
            if total_line > 50:
                parts.append("High total - offensive matchup")
            elif total_line < 42:
                parts.append("Low total - defensive battle")

        return ". ".join(parts) + "." if parts else "Following Vegas trends"