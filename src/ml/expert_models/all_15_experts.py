#!/usr/bin/env python3
"""
Complete 15-Expert Council - All Personality Models

Maps to expertPersonalities.ts frontend definitions.
"""

import sys
import os
import random
from typing import Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from .base_model import BaseExpertModel, Prediction
from services.expert_data_access_layer import GameData

# Experts 1-4 already exist in separate files:
# 1. AnalystModel (conservative_analyzer)
# 2. GamblerModel (risk_taking_gambler)
# 3. ContrarianModel (contrarian_rebel)
# 4. GutInstinctModel (gut_instinct_expert) - mapped as "The Intuition"

# Creating experts 5-15 below:

class HunterModel(BaseExpertModel):
    """The Hunter (value_hunter) - Value-seeking expert"""

    def __init__(self):
        super().__init__(expert_id='value_hunter')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})
        odds = game_data.odds

        # Look for value vs Vegas lines
        spread_line = odds.get('spread', {}).get('home') if odds else None

        if spread_line and home_stats and away_stats:
            # Calculate true value
            home_ppg = self._safe_get(home_stats, 'points_avg', 20)
            away_ppg = self._safe_get(away_stats, 'points_avg', 20)

            true_diff = (home_ppg - away_ppg) + 2.5  # Home field
            value = abs(true_diff - spread_line)

            # Take value side
            if true_diff > spread_line + 2:
                prediction.winner = game_data.home_team
                prediction.winner_confidence = self._calculate_confidence(0.58 + value/10, prediction.data_completeness)
            else:
                prediction.winner = game_data.away_team
                prediction.winner_confidence = self._calculate_confidence(0.58 + value/10, prediction.data_completeness)

            prediction.spread_pick = prediction.winner
            prediction.spread_confidence = prediction.winner_confidence
            prediction.reasoning = f"Found {value:.1f} points of value vs Vegas line"
        else:
            prediction.reasoning = "Need odds to find value"

        return prediction


class RiderModel(BaseExpertModel):
    """The Rider (momentum_rider) - Momentum specialist"""

    def __init__(self):
        super().__init__(expert_id='momentum_rider')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})

        # Ride the hot team (higher PPG = momentum)
        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        if home_ppg > away_ppg + 3:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(0.62, prediction.data_completeness)
            prediction.reasoning = f"{game_data.home_team} riding hot streak at {home_ppg:.1f} PPG"
        elif away_ppg > home_ppg + 3:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(0.62, prediction.data_completeness)
            prediction.reasoning = f"{game_data.away_team} riding hot streak at {away_ppg:.1f} PPG"
        else:
            prediction.winner = game_data.home_team  # Default home
            prediction.winner_confidence = 0.53
            prediction.reasoning = "No clear momentum edge"

        return prediction


class ScholarModel(BaseExpertModel):
    """The Scholar (fundamentalist_scholar) - Fundamentals expert"""

    def __init__(self):
        super().__init__(expert_id='fundamentalist_scholar')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})

        # Pure fundamentals: yards, turnovers, efficiency
        home_yards = self._safe_get(home_stats, 'total_yards_avg', 350)
        away_yards = self._safe_get(away_stats, 'total_yards_avg', 350)

        home_to = self._safe_get(home_stats, 'turnovers_avg', 1)
        away_to = self._safe_get(away_stats, 'turnovers_avg', 1)

        home_score = (home_yards / 50) - (home_to * 7) + 2.5
        away_score = (away_yards / 50) - (away_to * 7)

        if home_score > away_score:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(0.65, prediction.data_completeness)
        else:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(0.65, prediction.data_completeness)

        prediction.reasoning = "Based on fundamental metrics: yards and turnovers"
        return prediction


class ChaosModel(BaseExpertModel):
    """The Chaos (chaos_theory_believer) - Embraces randomness"""

    def __init__(self):
        super().__init__(expert_id='chaos_theory_believer')
        self.random = random.Random()

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = 0.1  # Uses minimal data

        # Seed for consistency but embrace chaos
        self.random.seed(game_data.game_id + "chaos")

        # Deliberately contrarian to conventional wisdom
        chaos_factor = self.random.random()

        if chaos_factor < 0.5:
            prediction.winner = game_data.away_team  # Favor road team
            prediction.winner_confidence = self._calculate_confidence(0.48 + self.random.random() * 0.2, 0.1)
            prediction.reasoning = "Chaos favors the unexpected road team"
        else:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(0.48 + self.random.random() * 0.2, 0.1)
            prediction.reasoning = "Embracing the chaos of home field"

        return prediction


class QuantModel(BaseExpertModel):
    """The Quant (statistics_purist) - Pure statistical model"""

    def __init__(self):
        super().__init__(expert_id='statistics_purist')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})

        # Pure math: expected value calculation
        home_ev = (
            self._safe_get(home_stats, 'points_avg', 20) * 0.4 +
            self._safe_get(home_stats, 'total_yards_avg', 350) / 20 * 0.3 +
            (100 - self._safe_get(home_stats, 'points_allowed_avg', 20) * 2) / 20 * 0.3 +
            2.5  # Home field
        )

        away_ev = (
            self._safe_get(away_stats, 'points_avg', 20) * 0.4 +
            self._safe_get(away_stats, 'total_yards_avg', 350) / 20 * 0.3 +
            (100 - self._safe_get(away_stats, 'points_allowed_avg', 20) * 2) / 20 * 0.3
        )

        diff = home_ev - away_ev

        if diff > 1:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(min(0.5 + diff/20, 0.85), prediction.data_completeness)
        else:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(min(0.5 + abs(diff)/20, 0.85), prediction.data_completeness)

        prediction.reasoning = f"Statistical EV differential: {diff:.2f}"
        return prediction


class ReversalModel(BaseExpertModel):
    """The Reversal (trend_reversal_specialist) - Mean reversion"""

    def __init__(self):
        super().__init__(expert_id='trend_reversal_specialist')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})

        # Fade extremes (mean reversion)
        home_ppg = self._safe_get(home_stats, 'points_avg', 20)
        away_ppg = self._safe_get(away_stats, 'points_avg', 20)

        # If team scoring way above average, expect regression
        if home_ppg > 28:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(0.58, prediction.data_completeness)
            prediction.reasoning = f"{game_data.home_team} due for regression from {home_ppg:.1f} PPG"
        elif away_ppg > 28:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(0.58, prediction.data_completeness)
            prediction.reasoning = f"{game_data.away_team} due for regression from {away_ppg:.1f} PPG"
        else:
            # No extreme, take underdog
            prediction.winner = game_data.away_team
            prediction.winner_confidence = 0.53
            prediction.reasoning = "No clear mean reversion signal"

        return prediction


class FaderModel(BaseExpertModel):
    """The Fader (popular_narrative_fader) - Anti-narrative"""

    def __init__(self):
        super().__init__(expert_id='popular_narrative_fader')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        odds = game_data.odds
        spread_line = odds.get('spread', {}).get('home') if odds else None

        # Fade big favorites (public loves favorites)
        if spread_line and spread_line <= -7:
            prediction.winner = game_data.away_team
            prediction.winner_confidence = self._calculate_confidence(0.60, prediction.data_completeness)
            prediction.reasoning = f"Fading public favorite at {spread_line}"
        elif spread_line and spread_line >= 7:
            prediction.winner = game_data.home_team
            prediction.winner_confidence = self._calculate_confidence(0.60, prediction.data_completeness)
            prediction.reasoning = f"Fading public favorite at +{spread_line}"
        else:
            # Default: fade home team (public loves home teams)
            prediction.winner = game_data.away_team
            prediction.winner_confidence = 0.54
            prediction.reasoning = "Fading public's home team bias"

        return prediction


class SharpModel(BaseExpertModel):
    """The Sharp (sharp_money_follower) - Follows smart money"""

    def __init__(self):
        super().__init__(expert_id='sharp_money_follower')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        odds = game_data.odds

        # Look for line movement (sharp money indicator)
        # For now, use Vegas line as sharp indicator
        spread_line = odds.get('spread', {}).get('home') if odds else None

        if spread_line:
            # Sharp money usually on underdogs with value
            if abs(spread_line) > 3:
                # Take underdog
                if spread_line < 0:
                    prediction.winner = game_data.away_team
                else:
                    prediction.winner = game_data.home_team

                prediction.winner_confidence = self._calculate_confidence(0.62, prediction.data_completeness)
                prediction.reasoning = "Following sharp money on underdog"
            else:
                # Small spread - take favorite
                if spread_line < 0:
                    prediction.winner = game_data.home_team
                else:
                    prediction.winner = game_data.away_team

                prediction.winner_confidence = 0.58
                prediction.reasoning = "Sharp money respects small favorite"
        else:
            prediction.reasoning = "Need lines to follow sharp money"

        return prediction


class UnderdogModel(BaseExpertModel):
    """The Underdog (underdog_champion) - Always backs underdogs"""

    def __init__(self):
        super().__init__(expert_id='underdog_champion')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        odds = game_data.odds
        spread_line = odds.get('spread', {}).get('home') if odds else None

        # ALWAYS take the underdog
        if spread_line:
            if spread_line < 0:
                # Home favored - take away
                prediction.winner = game_data.away_team
                edge = abs(spread_line) / 10
            else:
                # Away favored - take home
                prediction.winner = game_data.home_team
                edge = spread_line / 10

            prediction.winner_confidence = self._calculate_confidence(0.55 + edge, prediction.data_completeness)
            prediction.spread_pick = prediction.winner
            prediction.spread_confidence = prediction.winner_confidence
            prediction.reasoning = f"Backing underdog {prediction.winner} with passion"
        else:
            # No line - take road team (usually underdog)
            prediction.winner = game_data.away_team
            prediction.winner_confidence = 0.56
            prediction.reasoning = "Taking road underdog by default"

        return prediction


class ConsensusModel(BaseExpertModel):
    """The Consensus (consensus_follower) - Follows the crowd"""

    def __init__(self):
        super().__init__(expert_id='consensus_follower')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        odds = game_data.odds

        # Follow Vegas (proxy for public consensus)
        moneyline = odds.get('moneyline', {}) if odds else {}
        home_ml = moneyline.get('home')
        away_ml = moneyline.get('away')

        if home_ml and away_ml:
            # Negative = favorite = public loves them
            if home_ml < away_ml:
                prediction.winner = game_data.home_team
                prediction.winner_confidence = self._calculate_confidence(0.60, prediction.data_completeness)
                prediction.reasoning = f"Following consensus favorite {game_data.home_team}"
            else:
                prediction.winner = game_data.away_team
                prediction.winner_confidence = self._calculate_confidence(0.60, prediction.data_completeness)
                prediction.reasoning = f"Following consensus favorite {game_data.away_team}"
        else:
            # No odds - follow home team (public default)
            prediction.winner = game_data.home_team
            prediction.winner_confidence = 0.58
            prediction.reasoning = "Following public's home team bias"

        return prediction


class ExploiterModel(BaseExpertModel):
    """The Exploiter (market_inefficiency_exploiter) - Finds market mistakes"""

    def __init__(self):
        super().__init__(expert_id='market_inefficiency_exploiter')

    async def predict(self, game_data: GameData) -> Prediction:
        prediction = Prediction(expert_id=self.expert_id, game_id=game_data.game_id)
        prediction.data_completeness = self._calculate_data_completeness(game_data)

        home_stats = game_data.team_stats.get('home_stats', {})
        away_stats = game_data.team_stats.get('away_stats', {})
        odds = game_data.odds

        spread_line = odds.get('spread', {}).get('home') if odds else None

        if spread_line and home_stats and away_stats:
            # Calculate "true" line
            home_ppg = self._safe_get(home_stats, 'points_avg', 20)
            away_ppg = self._safe_get(away_stats, 'points_avg', 20)

            true_line = (home_ppg - away_ppg) + 2.5

            # Find inefficiency
            inefficiency = abs(true_line - spread_line)

            if inefficiency > 3:
                # Significant inefficiency found
                if true_line > spread_line:
                    prediction.winner = game_data.home_team
                else:
                    prediction.winner = game_data.away_team

                prediction.winner_confidence = self._calculate_confidence(0.65 + inefficiency/20, prediction.data_completeness)
                prediction.reasoning = f"Exploiting {inefficiency:.1f} point market inefficiency"
            else:
                # No inefficiency - pass
                prediction.winner = game_data.home_team
                prediction.winner_confidence = 0.52
                prediction.reasoning = "No significant market inefficiency found"
        else:
            prediction.reasoning = "Need odds to find inefficiencies"

        return prediction