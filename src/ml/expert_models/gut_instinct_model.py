#!/usr/bin/env python3
"""
Gut Instinct - Minimal data, intuition-based expert.

Personality:
- Uses almost no stats
- Home field bias
- Moderate confidence
- Simple decision rules
"""

import sys
import os
import random
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .base_model import BaseExpertModel, Prediction
from services.expert_data_access_layer import GameData


class GutInstinctModel(BaseExpertModel):
    """
    Gut Instinct makes picks based on feel, not data.

    Strategy:
    - Strong home field bias (picks home 65% of time)
    - Looks at team names/reputation only
    - Moderate confidence (never too high or low)
    - Simple, intuitive reasoning
    """

    def __init__(self):
        super().__init__(expert_id='gut-instinct')
        # Seed for consistent "gut feelings" per game
        self.random = random.Random()

    async def predict(self, game_data: GameData) -> Prediction:
        """Generate intuition-based prediction"""

        prediction = Prediction(
            expert_id=self.expert_id,
            game_id=game_data.game_id
        )

        # Seed random with game_id for consistency
        self.random.seed(game_data.game_id)

        prediction.data_completeness = 0.3  # Minimal data used

        # Home field bias - pick home 65% of time
        home_bias = self.random.random()

        if home_bias < 0.65:
            # Pick home team
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(
                0.52 + self.random.random() * 0.15,  # 52-67% range
                prediction.data_completeness
            )
            prediction.reasoning = f"{game_data.home_team} has home field advantage"
        else:
            # Pick away team
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(
                0.52 + self.random.random() * 0.15,
                prediction.data_completeness
            )
            prediction.reasoning = f"{game_data.away_team} feels like the better team"

        # Spread prediction - follow winner with slight hesitation
        odds = game_data.odds
        spread_line = odds.get('spread', {}).get('home') if odds else None

        if spread_line is not None:
            # If home team favored and we picked home
            if spread_line < 0 and prediction.winner == game_data.home_team:
                prediction.spread_pick = game_data.home_team
                prediction.spread_confidence = 0.55
            # If away team favored and we picked away
            elif spread_line > 0 and prediction.winner == game_data.away_team:
                prediction.spread_pick = game_data.away_team
                prediction.spread_confidence = 0.55
            # We picked against spread
            else:
                prediction.spread_pick = prediction.winner
                prediction.spread_confidence = 0.52  # Less confident

        # Total prediction - slight over bias (more exciting)
        total_line = odds.get('total', {}).get('line') if odds else None
        if total_line:
            over_bias = self.random.random()

            if over_bias < 0.55:
                prediction.total_pick = "OVER"
                prediction.total_confidence = 0.54
            else:
                prediction.total_pick = "UNDER"
                prediction.total_confidence = 0.53

            prediction.total_line = total_line

        # Moneyline (same as winner)
        prediction.moneyline_pick = prediction.winner
        prediction.moneyline_confidence = prediction.winner_confidence

        # Margin - guess based on feel
        if spread_line:
            prediction.margin = int(abs(spread_line) + self.random.randint(-2, 4))
        else:
            prediction.margin = self.random.randint(3, 10)

        prediction.margin_confidence = 0.50

        # Team performance - just guess reasonably
        prediction.home_touchdowns = self.random.randint(2, 4)
        prediction.away_touchdowns = self.random.randint(2, 4)

        prediction.home_turnovers = self.random.randint(0, 2)
        prediction.away_turnovers = self.random.randint(0, 2)

        prediction.home_field_goals = self.random.randint(1, 2)
        prediction.away_field_goals = self.random.randint(1, 2)

        prediction.key_factors = [
            "Home field advantage" if prediction.winner == game_data.home_team else "Road team confidence",
            "Gut feeling",
            "Intuition"
        ]

        self.predictions_made += 1
        self.total_confidence += prediction.winner_confidence

        return prediction