#!/usr/bin/env python3
"""
Contrarian Rebel - Fades the public, loves underdogs.

Personality:
- Takes underdogs when line is inflated
- Fades heavy public betting (when available)
- Higher confidence on contrarian plays
- Anti-consensus mindset
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .base_model import BaseExpertModel, Prediction
from services.expert_data_access_layer import GameData


class ContrarianModel(BaseExpertModel):
    """
    The Contrarian fades the public and takes underdogs.

    Strategy:
    - When spread > 7, take the underdog
    - Fade heavy favorites
    - Look for overreactions
    - Value in unpopular picks
    """

    def __init__(self):
        super().__init__(expert_id='contrarian-rebel')

    async def predict(self, game_data: GameData) -> Prediction:
        """Generate contrarian prediction"""

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
            prediction.reasoning = "Need betting lines to find contrarian value"
            return prediction

        spread_line = odds.get('spread', {}).get('home')
        total_line = odds.get('total', {}).get('line')

        if spread_line is None:
            return prediction

        # Winner prediction - fade big favorites
        if spread_line <= -7:
            # Home is heavy favorite - FADE THEM
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(
                0.62,  # Moderate contrarian confidence
                prediction.data_completeness
            )
            prediction.reasoning = f"Fading heavy favorite {game_data.home_team} ({spread_line})"

        elif spread_line >= 7:
            # Away is heavy favorite - FADE THEM
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(
                0.62,
                prediction.data_completeness
            )
            prediction.reasoning = f"Fading heavy favorite {game_data.away_team} (+{spread_line})"

        else:
            # Moderate spread - take underdog
            if spread_line < 0:
                # Home favored - take away
                prediction.winner = game_data.away_team
                underdog_value = abs(spread_line) / 10
            else:
                # Away favored - take home
                prediction.winner = game_data.home_team
                underdog_value = spread_line / 10

            prediction.winner_confidence = self._calculate_confidence(
                0.53 + underdog_value,
                prediction.data_completeness
            )
            prediction.reasoning = f"Taking underdog {prediction.winner}"

        # Spread prediction - ALWAYS take the underdog
        if spread_line < 0:
            # Home favored - take away
            prediction.spread_pick = game_data.away_team
            # More confident on bigger underdogs
            edge = abs(spread_line) / 5
        else:
            # Away favored - take home
            prediction.spread_pick = game_data.home_team
            edge = spread_line / 5

        prediction.spread_confidence = self._calculate_confidence(
            min(0.55 + edge, 0.85),
            prediction.data_completeness
        )

        # Total prediction - fade high totals, take low totals
        if total_line:
            if total_line >= 50:
                # Public loves overs on high totals - FADE
                prediction.total_pick = "UNDER"
                prediction.total_confidence = self._calculate_confidence(
                    0.64,
                    prediction.data_completeness
                )
            elif total_line <= 40:
                # Public scared of low totals - GO UNDER
                prediction.total_pick = "UNDER"
                prediction.total_confidence = self._calculate_confidence(
                    0.58,
                    prediction.data_completeness
                )
            else:
                # Moderate total - slight under lean
                prediction.total_pick = "UNDER"
                prediction.total_confidence = 0.56

            prediction.total_line = total_line

        # Moneyline - take underdog
        prediction.moneyline_pick = prediction.winner
        prediction.moneyline_confidence = prediction.winner_confidence

        # Margin - underdogs keep it close
        if spread_line:
            prediction.margin = int(abs(spread_line) * 0.6)  # Closer than line
        else:
            prediction.margin = 4

        prediction.margin_confidence = 0.60

        # Team performance
        if home_stats and away_stats:
            prediction.home_total_yards = self._safe_get(home_stats, 'total_yards_avg', 350)
            prediction.away_total_yards = self._safe_get(away_stats, 'total_yards_avg', 350)

            # Underdogs score less but keep it competitive
            if prediction.winner == game_data.home_team:
                prediction.home_touchdowns = 3
                prediction.away_touchdowns = 2
            else:
                prediction.home_touchdowns = 2
                prediction.away_touchdowns = 3

            prediction.home_turnovers = 1
            prediction.away_turnovers = 1

        prediction.key_factors = [
            f"Spread: {spread_line:+.1f} - taking underdog",
            "Fading public sentiment",
            "Contrarian value"
        ]

        self.predictions_made += 1
        self.total_confidence += prediction.winner_confidence

        return prediction