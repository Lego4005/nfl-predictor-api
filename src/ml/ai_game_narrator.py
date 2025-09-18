#!/usr/bin/env python3
"""
AI Game Narrator for Live NFL Games
Provides context-aware insights, predictive analysis, and intelligent commentary
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import json
import math
from enum import Enum

from .ensemble_predictor import AdvancedEnsemblePredictor
from .enhanced_game_models import EnhancedGamePredictor

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GameSituation(Enum):
    """Game situation types for contextual analysis"""
    OPENING_DRIVE = "opening_drive"
    RED_ZONE = "red_zone"
    TWO_MINUTE_WARNING = "two_minute_warning"
    FOURTH_DOWN = "fourth_down"
    GOAL_LINE = "goal_line"
    HAIL_MARY = "hail_mary"
    COMEBACK_ATTEMPT = "comeback_attempt"
    GARBAGE_TIME = "garbage_time"
    OVERTIME = "overtime"
    CRITICAL_THIRD_DOWN = "critical_third_down"


class MomentumShift(Enum):
    """Momentum shift types"""
    MASSIVE_POSITIVE = "massive_positive"
    MODERATE_POSITIVE = "moderate_positive"
    SLIGHT_POSITIVE = "slight_positive"
    NEUTRAL = "neutral"
    SLIGHT_NEGATIVE = "slight_negative"
    MODERATE_NEGATIVE = "moderate_negative"
    MASSIVE_NEGATIVE = "massive_negative"


@dataclass
class GameState:
    """Current game state information"""
    quarter: int
    time_remaining: str  # "MM:SS" format
    down: int
    yards_to_go: int
    yard_line: int  # 0-100, home team's perspective
    home_score: int
    away_score: int
    possession: str  # "home" or "away"
    last_play: Dict[str, Any]
    drive_info: Dict[str, Any]
    game_id: str
    week: int
    season: int


@dataclass
class PredictionConfidence:
    """Prediction confidence levels"""
    probability: float
    confidence_interval: Tuple[float, float]
    confidence_level: str  # "very_high", "high", "medium", "low"
    factors: List[str]


@dataclass
class ScoringProbability:
    """Next scoring prediction"""
    team: str
    score_type: str  # "touchdown", "field_goal", "safety", "none"
    probability: float
    expected_points: float
    confidence: PredictionConfidence


@dataclass
class GameOutcomeLikelihood:
    """Game outcome prediction"""
    home_win_prob: float
    away_win_prob: float
    tie_prob: float
    expected_home_score: float
    expected_away_score: float
    confidence: PredictionConfidence


@dataclass
class ContextualInsight:
    """Contextual insight about current situation"""
    insight_type: str
    message: str
    historical_comparison: Optional[Dict[str, Any]]
    statistical_backing: Dict[str, float]
    relevance_score: float


@dataclass
class MomentumAnalysis:
    """Momentum shift analysis"""
    current_momentum: MomentumShift
    shift_magnitude: float
    shift_reason: str
    key_factors: List[str]
    trend_direction: str  # "increasing", "decreasing", "stable"


@dataclass
class DecisionRecommendation:
    """4th down or critical decision recommendation"""
    situation: str
    recommendation: str
    success_probability: float
    expected_value: float
    alternative_options: List[Dict[str, Any]]
    reasoning: str


@dataclass
class NarratorInsight:
    """Complete narrator insight package"""
    timestamp: datetime
    game_state: GameState
    scoring_probability: ScoringProbability
    game_outcome: GameOutcomeLikelihood
    contextual_insights: List[ContextualInsight]
    momentum_analysis: MomentumAnalysis
    decision_recommendation: Optional[DecisionRecommendation]
    weather_impact: Optional[Dict[str, Any]]
    key_matchup_analysis: Dict[str, Any]


class HistoricalComparator:
    """Compares current situations to historical games"""

    def __init__(self):
        self.historical_database = {}
        self.situation_patterns = {}

    def find_similar_situations(self, game_state: GameState, limit: int = 5) -> List[Dict[str, Any]]:
        """Find historically similar situations"""

        # Mock historical comparisons - in production, query historical database
        similar_situations = [
            {
                "game_id": "2023_week15_chiefs_patriots",
                "similarity_score": 0.92,
                "context": "4th quarter comeback attempt, similar field position",
                "outcome": "Successful drive, touchdown with 1:47 remaining",
                "key_factors": ["elite quarterback", "home crowd", "weather conditions"],
                "final_result": "Home team victory by 3 points"
            },
            {
                "game_id": "2022_week8_bills_packers",
                "similarity_score": 0.87,
                "context": "Red zone possession, similar down and distance",
                "outcome": "Field goal attempt, successful",
                "key_factors": ["strong defense", "kicking conditions", "pressure situation"],
                "final_result": "Away team victory by 1 point"
            },
            {
                "game_id": "2023_week3_cowboys_giants",
                "similarity_score": 0.83,
                "context": "Two-minute warning, trailing by similar margin",
                "outcome": "Turnover on downs, game over",
                "key_factors": ["elite defense", "quarterback pressure", "crowd noise"],
                "final_result": "Home team victory by 7 points"
            }
        ]

        return similar_situations[:limit]

    def calculate_situation_success_rate(self, situation_type: GameSituation, context: Dict[str, Any]) -> float:
        """Calculate success rate for similar historical situations"""

        # Mock calculation - in production, analyze historical database
        base_success_rates = {
            GameSituation.FOURTH_DOWN: 0.45,
            GameSituation.RED_ZONE: 0.67,
            GameSituation.TWO_MINUTE_WARNING: 0.32,
            GameSituation.GOAL_LINE: 0.78,
            GameSituation.CRITICAL_THIRD_DOWN: 0.42,
            GameSituation.COMEBACK_ATTEMPT: 0.23,
            GameSituation.HAIL_MARY: 0.03
        }

        base_rate = base_success_rates.get(situation_type, 0.50)

        # Adjust based on context factors
        adjustments = 0.0

        if context.get('home_field', False):
            adjustments += 0.05
        if context.get('elite_qb', False):
            adjustments += 0.08
        if context.get('poor_weather', False):
            adjustments -= 0.12
        if context.get('strong_defense', False):
            adjustments -= 0.06

        return max(0.01, min(0.99, base_rate + adjustments))


class SituationAnalyzer:
    """Analyzes current game situation"""

    def __init__(self):
        self.situation_weights = {
            'time_pressure': 0.25,
            'field_position': 0.20,
            'score_differential': 0.20,
            'down_distance': 0.15,
            'momentum': 0.10,
            'weather': 0.10
        }

    def identify_situation(self, game_state: GameState) -> List[GameSituation]:
        """Identify current game situation(s)"""

        situations = []

        # Time-based situations
        quarter = game_state.quarter
        time_parts = game_state.time_remaining.split(':')
        minutes = int(time_parts[0])
        seconds = int(time_parts[1])
        total_seconds = minutes * 60 + seconds

        if quarter <= 2 and total_seconds <= 120:
            situations.append(GameSituation.TWO_MINUTE_WARNING)
        elif quarter >= 4 and total_seconds <= 120:
            situations.append(GameSituation.TWO_MINUTE_WARNING)
        elif quarter == 5:
            situations.append(GameSituation.OVERTIME)

        # Down and distance situations
        if game_state.down == 4:
            situations.append(GameSituation.FOURTH_DOWN)
        elif game_state.down == 3 and game_state.yards_to_go >= 8:
            situations.append(GameSituation.CRITICAL_THIRD_DOWN)

        # Field position situations
        if game_state.yard_line <= 20:
            situations.append(GameSituation.RED_ZONE)
        if game_state.yard_line <= 5:
            situations.append(GameSituation.GOAL_LINE)

        # Score differential situations
        score_diff = abs(game_state.home_score - game_state.away_score)
        if score_diff >= 21 and quarter >= 4:
            situations.append(GameSituation.GARBAGE_TIME)
        elif score_diff <= 8 and quarter >= 4 and total_seconds <= 300:
            situations.append(GameSituation.COMEBACK_ATTEMPT)

        # Special situations
        if quarter >= 4 and total_seconds <= 8 and score_diff <= 7:
            situations.append(GameSituation.HAIL_MARY)

        return situations if situations else [GameSituation.OPENING_DRIVE]

    def calculate_situation_pressure(self, game_state: GameState, situations: List[GameSituation]) -> float:
        """Calculate pressure level (0-1) of current situation"""

        pressure_scores = {
            GameSituation.HAIL_MARY: 1.0,
            GameSituation.OVERTIME: 0.95,
            GameSituation.FOURTH_DOWN: 0.85,
            GameSituation.TWO_MINUTE_WARNING: 0.80,
            GameSituation.COMEBACK_ATTEMPT: 0.75,
            GameSituation.CRITICAL_THIRD_DOWN: 0.65,
            GameSituation.RED_ZONE: 0.60,
            GameSituation.GOAL_LINE: 0.70,
            GameSituation.GARBAGE_TIME: 0.20,
            GameSituation.OPENING_DRIVE: 0.30
        }

        if not situations:
            return 0.30

        max_pressure = max([pressure_scores.get(sit, 0.30) for sit in situations])

        # Adjust based on score differential
        score_diff = abs(game_state.home_score - game_state.away_score)
        if score_diff <= 3:
            max_pressure += 0.1
        elif score_diff <= 7:
            max_pressure += 0.05
        elif score_diff >= 21:
            max_pressure -= 0.2

        return max(0.0, min(1.0, max_pressure))


class WeatherImpactAnalyzer:
    """Analyzes weather impact on current game"""

    def __init__(self):
        self.weather_factors = {
            'wind_speed': {'high_threshold': 15, 'extreme_threshold': 25},
            'temperature': {'cold_threshold': 32, 'hot_threshold': 85},
            'precipitation': {'light_threshold': 0.1, 'heavy_threshold': 0.3},
            'visibility': {'poor_threshold': 5, 'very_poor_threshold': 2}
        }

    def analyze_weather_impact(self, weather_data: Dict[str, Any], game_state: GameState) -> Dict[str, Any]:
        """Analyze weather impact on current game situation"""

        if weather_data.get('dome_game', False):
            return {
                'impact_level': 'none',
                'impact_score': 0.0,
                'affected_aspects': [],
                'recommendations': ['Indoor game - weather not a factor'],
                'narrative': "Playing indoors, weather conditions have no impact on this game."
            }

        impact_analysis = {
            'impact_level': 'minimal',
            'impact_score': 0.0,
            'affected_aspects': [],
            'recommendations': [],
            'narrative': ""
        }

        wind_speed = weather_data.get('wind_speed', 0)
        temperature = weather_data.get('temperature', 70)
        precipitation = weather_data.get('precipitation', 0)
        visibility = weather_data.get('visibility', 10)

        total_impact = 0.0
        narrative_parts = []

        # Wind impact
        if wind_speed > self.weather_factors['wind_speed']['extreme_threshold']:
            total_impact += 0.4
            impact_analysis['affected_aspects'].extend(['passing', 'kicking'])
            impact_analysis['recommendations'].append('Favor running game and avoid long field goals')
            narrative_parts.append(f"Extreme winds at {wind_speed} mph will significantly impact passing and kicking")
        elif wind_speed > self.weather_factors['wind_speed']['high_threshold']:
            total_impact += 0.2
            impact_analysis['affected_aspects'].extend(['passing', 'kicking'])
            narrative_parts.append(f"Strong winds at {wind_speed} mph affecting aerial game")

        # Temperature impact
        if temperature < self.weather_factors['temperature']['cold_threshold']:
            total_impact += 0.15
            impact_analysis['affected_aspects'].extend(['handling', 'kicking'])
            narrative_parts.append(f"Freezing conditions at {temperature}°F affecting ball handling")
        elif temperature > self.weather_factors['temperature']['hot_threshold']:
            total_impact += 0.1
            impact_analysis['affected_aspects'].append('endurance')
            narrative_parts.append(f"Hot conditions at {temperature}°F may impact player endurance")

        # Precipitation impact
        if precipitation > self.weather_factors['precipitation']['heavy_threshold']:
            total_impact += 0.3
            impact_analysis['affected_aspects'].extend(['handling', 'footing', 'passing'])
            narrative_parts.append("Heavy precipitation creating slippery conditions")
        elif precipitation > self.weather_factors['precipitation']['light_threshold']:
            total_impact += 0.15
            impact_analysis['affected_aspects'].extend(['handling', 'footing'])
            narrative_parts.append("Light precipitation may affect ball handling")

        # Visibility impact
        if visibility < self.weather_factors['visibility']['very_poor_threshold']:
            total_impact += 0.25
            impact_analysis['affected_aspects'].extend(['passing', 'vision'])
            narrative_parts.append("Very poor visibility affecting downfield vision")
        elif visibility < self.weather_factors['visibility']['poor_threshold']:
            total_impact += 0.1
            impact_analysis['affected_aspects'].append('vision')
            narrative_parts.append("Reduced visibility may limit deep passing")

        # Determine impact level
        impact_analysis['impact_score'] = min(1.0, total_impact)

        if total_impact >= 0.6:
            impact_analysis['impact_level'] = 'extreme'
        elif total_impact >= 0.4:
            impact_analysis['impact_level'] = 'high'
        elif total_impact >= 0.2:
            impact_analysis['impact_level'] = 'moderate'
        elif total_impact >= 0.1:
            impact_analysis['impact_level'] = 'mild'

        impact_analysis['narrative'] = '. '.join(narrative_parts) if narrative_parts else "Weather conditions are favorable for all aspects of play."

        return impact_analysis


class DecisionEngine:
    """Makes 4th down and critical decision recommendations"""

    def __init__(self):
        self.decision_matrix = self._build_decision_matrix()

    def _build_decision_matrix(self) -> Dict[str, Dict[str, float]]:
        """Build decision success probability matrix"""

        return {
            'punt': {
                'base_success': 0.95,  # Usually successful
                'field_position_value': 0.7,
                'time_factor': 0.1
            },
            'field_goal': {
                'base_success': 0.85,  # Distance dependent
                'distance_penalty': 0.03,  # Per yard over 30
                'weather_penalty': 0.15,
                'pressure_penalty': 0.05
            },
            'go_for_it': {
                'base_success': 0.45,  # Varies greatly
                'down_distance_factor': 0.8,
                'field_position_factor': 0.3,
                'time_pressure_factor': 0.2
            }
        }

    def recommend_fourth_down_decision(self, game_state: GameState, context: Dict[str, Any]) -> DecisionRecommendation:
        """Recommend 4th down decision"""

        if game_state.down != 4:
            return None

        yard_line = game_state.yard_line
        yards_to_go = game_state.yards_to_go
        time_remaining = self._parse_time_remaining(game_state.time_remaining)
        score_diff = game_state.home_score - game_state.away_score

        # Calculate success probabilities for each option
        options = {}

        # Option 1: Punt
        if yard_line > 35:  # Not in field goal range
            punt_success = self.decision_matrix['punt']['base_success']
            punt_value = self._calculate_punt_value(yard_line, time_remaining)
            options['punt'] = {
                'success_probability': punt_success,
                'expected_value': punt_value,
                'reasoning': f"Pin opponent deep, field position advantage"
            }

        # Option 2: Field Goal
        if yard_line <= 45:  # Within reasonable field goal range
            fg_distance = 17 + (100 - yard_line)  # Add 10 yards for end zone, 7 for snap
            fg_success = self._calculate_fg_success_probability(fg_distance, context)
            fg_value = self._calculate_fg_value(fg_success, score_diff, time_remaining)
            options['field_goal'] = {
                'success_probability': fg_success,
                'expected_value': fg_value,
                'reasoning': f"{fg_distance}-yard attempt, {fg_success:.1%} historical success rate"
            }

        # Option 3: Go for it
        go_success = self._calculate_conversion_probability(yards_to_go, yard_line, context)
        go_value = self._calculate_go_for_it_value(go_success, yard_line, score_diff, time_remaining)
        options['go_for_it'] = {
            'success_probability': go_success,
            'expected_value': go_value,
            'reasoning': f"{yards_to_go} yards to convert, {go_success:.1%} estimated success rate"
        }

        # Determine best option
        best_option = max(options.items(), key=lambda x: x[1]['expected_value'])

        # Create alternative options list
        alternatives = [
            {
                'option': option,
                'success_probability': data['success_probability'],
                'expected_value': data['expected_value'],
                'reasoning': data['reasoning']
            }
            for option, data in options.items() if option != best_option[0]
        ]

        return DecisionRecommendation(
            situation=f"4th and {yards_to_go} at {yard_line}-yard line",
            recommendation=best_option[0],
            success_probability=best_option[1]['success_probability'],
            expected_value=best_option[1]['expected_value'],
            alternative_options=alternatives,
            reasoning=best_option[1]['reasoning']
        )

    def _parse_time_remaining(self, time_str: str) -> int:
        """Parse time remaining into total seconds"""
        parts = time_str.split(':')
        return int(parts[0]) * 60 + int(parts[1])

    def _calculate_fg_success_probability(self, distance: int, context: Dict[str, Any]) -> float:
        """Calculate field goal success probability"""

        # Base success rate by distance
        if distance <= 30:
            base_success = 0.95
        elif distance <= 40:
            base_success = 0.90
        elif distance <= 50:
            base_success = 0.80
        else:
            base_success = max(0.40, 0.90 - (distance - 30) * 0.03)

        # Adjust for conditions
        weather_impact = context.get('weather_impact', 0)
        pressure_impact = context.get('pressure_level', 0) * 0.1

        return max(0.1, base_success - weather_impact - pressure_impact)

    def _calculate_conversion_probability(self, yards_to_go: int, field_position: int, context: Dict[str, Any]) -> float:
        """Calculate 4th down conversion probability"""

        # Base success rates by distance
        if yards_to_go == 1:
            base_success = 0.65
        elif yards_to_go <= 3:
            base_success = 0.50
        elif yards_to_go <= 6:
            base_success = 0.35
        else:
            base_success = max(0.15, 0.50 - (yards_to_go - 3) * 0.05)

        # Adjust for field position (easier in red zone)
        if field_position <= 10:
            base_success += 0.1
        elif field_position <= 20:
            base_success += 0.05

        # Adjust for context
        offensive_strength = context.get('offensive_rating', 0.5)
        defensive_strength = context.get('defensive_rating', 0.5)

        strength_adjustment = (offensive_strength - defensive_strength) * 0.2

        return max(0.05, min(0.95, base_success + strength_adjustment))

    def _calculate_punt_value(self, field_position: int, time_remaining: int) -> float:
        """Calculate expected value of punting"""

        # Expected field position for opponent
        expected_opponent_position = max(20, field_position - 40)

        # Value based on field position gained
        field_position_value = (expected_opponent_position - 20) / 80

        # Time factor (more valuable with more time remaining)
        time_factor = min(1.0, time_remaining / 900)  # Normalize to 15 minutes

        return field_position_value * 0.7 + time_factor * 0.3

    def _calculate_fg_value(self, success_prob: float, score_diff: int, time_remaining: int) -> float:
        """Calculate expected value of field goal attempt"""

        # Points value
        points_value = success_prob * 3

        # Situational adjustments
        if score_diff <= -3:  # Trailing, need points
            points_value *= 1.3
        elif score_diff >= 7:  # Leading, less critical
            points_value *= 0.8

        # Time factor
        if time_remaining < 120:  # Last 2 minutes
            points_value *= 1.2

        return points_value / 7  # Normalize to 0-1 scale (touchdown = 1)

    def _calculate_go_for_it_value(self, success_prob: float, field_position: int, score_diff: int, time_remaining: int) -> float:
        """Calculate expected value of going for it"""

        # Expected points if successful (varies by field position)
        if field_position <= 10:
            expected_points = 6.5  # High TD probability
        elif field_position <= 20:
            expected_points = 5.5
        elif field_position <= 40:
            expected_points = 4.0
        else:
            expected_points = 3.0

        # Calculate value
        success_value = success_prob * expected_points
        failure_cost = (1 - success_prob) * 2  # Cost of giving opponent good field position

        net_value = success_value - failure_cost

        # Situational adjustments
        if score_diff <= -7:  # Trailing significantly, need to be aggressive
            net_value *= 1.4
        elif time_remaining < 300 and score_diff < 0:  # Trailing with little time
            net_value *= 1.6

        return max(0, net_value / 7)  # Normalize to 0-1 scale


class AIGameNarrator:
    """Main AI Game Narrator that provides comprehensive real-time insights"""

    def __init__(self):
        self.ensemble_predictor = AdvancedEnsemblePredictor()
        self.enhanced_predictor = EnhancedGamePredictor()
        self.historical_comparator = HistoricalComparator()
        self.situation_analyzer = SituationAnalyzer()
        self.weather_analyzer = WeatherImpactAnalyzer()
        self.decision_engine = DecisionEngine()

        # Load pre-trained models if available
        try:
            self.ensemble_predictor.load_model()
            logger.info("Loaded pre-trained ensemble predictor")
        except:
            logger.warning("No pre-trained ensemble model found")

        try:
            self.enhanced_predictor.load_model()
            logger.info("Loaded pre-trained enhanced predictor")
        except:
            logger.warning("No pre-trained enhanced model found")

    def generate_comprehensive_insight(self, game_state: GameState, context: Dict[str, Any]) -> NarratorInsight:
        """Generate comprehensive insight for current game state"""

        logger.info(f"Generating insight for game {game_state.game_id}, Q{game_state.quarter} {game_state.time_remaining}")

        # Analyze current situation
        situations = self.situation_analyzer.identify_situation(game_state)
        pressure_level = self.situation_analyzer.calculate_situation_pressure(game_state, situations)

        # Generate scoring probability
        scoring_prob = self._calculate_scoring_probability(game_state, context, situations)

        # Generate game outcome likelihood
        game_outcome = self._calculate_game_outcome_likelihood(game_state, context)

        # Generate contextual insights
        contextual_insights = self._generate_contextual_insights(game_state, context, situations)

        # Analyze momentum
        momentum_analysis = self._analyze_momentum(game_state, context)

        # Generate decision recommendation if applicable
        decision_rec = None
        if GameSituation.FOURTH_DOWN in situations:
            decision_rec = self.decision_engine.recommend_fourth_down_decision(game_state, context)

        # Analyze weather impact
        weather_impact = None
        if context.get('weather_data'):
            weather_impact = self.weather_analyzer.analyze_weather_impact(
                context['weather_data'], game_state
            )

        # Analyze key matchups
        matchup_analysis = self._analyze_key_matchups(game_state, context)

        return NarratorInsight(
            timestamp=datetime.now(),
            game_state=game_state,
            scoring_probability=scoring_prob,
            game_outcome=game_outcome,
            contextual_insights=contextual_insights,
            momentum_analysis=momentum_analysis,
            decision_recommendation=decision_rec,
            weather_impact=weather_impact,
            key_matchup_analysis=matchup_analysis
        )

    def _calculate_scoring_probability(self, game_state: GameState, context: Dict[str, Any], situations: List[GameSituation]) -> ScoringProbability:
        """Calculate next scoring probability"""

        possessing_team = game_state.possession
        field_position = game_state.yard_line
        down = game_state.down
        yards_to_go = game_state.yards_to_go

        # Base probabilities by field position
        if field_position <= 10:
            td_prob = 0.75
            fg_prob = 0.20
            no_score_prob = 0.05
        elif field_position <= 20:
            td_prob = 0.60
            fg_prob = 0.30
            no_score_prob = 0.10
        elif field_position <= 40:
            td_prob = 0.35
            fg_prob = 0.45
            no_score_prob = 0.20
        else:
            td_prob = 0.25
            fg_prob = 0.35
            no_score_prob = 0.40

        # Adjust for down and distance
        if down == 4:
            if yards_to_go > 3:
                td_prob *= 0.6
                fg_prob *= 0.8
                no_score_prob = 1 - td_prob - fg_prob
        elif down == 3 and yards_to_go > 8:
            td_prob *= 0.8
            fg_prob *= 0.9

        # Adjust for situations
        if GameSituation.RED_ZONE in situations:
            td_prob *= 1.2
            fg_prob *= 1.1
        if GameSituation.GOAL_LINE in situations:
            td_prob *= 1.5
            fg_prob *= 0.8

        # Normalize probabilities
        total = td_prob + fg_prob + no_score_prob
        td_prob /= total
        fg_prob /= total
        no_score_prob /= total

        # Determine most likely outcome
        if td_prob > fg_prob and td_prob > no_score_prob:
            score_type = "touchdown"
            probability = td_prob
            expected_points = 7.0
        elif fg_prob > no_score_prob:
            score_type = "field_goal"
            probability = fg_prob
            expected_points = 3.0
        else:
            score_type = "none"
            probability = no_score_prob
            expected_points = 0.0

        # Calculate confidence
        confidence_level = "high" if probability > 0.7 else "medium" if probability > 0.5 else "low"
        confidence_interval = (max(0, probability - 0.15), min(1, probability + 0.15))

        factors = []
        if field_position <= 20:
            factors.append("excellent field position")
        if down <= 2:
            factors.append("early down advantage")
        if GameSituation.RED_ZONE in situations:
            factors.append("red zone opportunity")

        confidence = PredictionConfidence(
            probability=probability,
            confidence_interval=confidence_interval,
            confidence_level=confidence_level,
            factors=factors
        )

        return ScoringProbability(
            team=possessing_team,
            score_type=score_type,
            probability=probability,
            expected_points=expected_points,
            confidence=confidence
        )

    def _calculate_game_outcome_likelihood(self, game_state: GameState, context: Dict[str, Any]) -> GameOutcomeLikelihood:
        """Calculate game outcome probabilities"""

        # Current score differential
        score_diff = game_state.home_score - game_state.away_score

        # Time remaining factor
        time_remaining = self._parse_time_remaining(game_state.time_remaining)
        quarter = game_state.quarter
        total_time_left = time_remaining + (4 - quarter) * 900 if quarter < 4 else time_remaining

        # Base win probabilities based on score and time
        if score_diff > 0:  # Home team leading
            if score_diff >= 21 and total_time_left < 900:  # 3+ TD lead with < 15 min
                home_win_prob = 0.95
            elif score_diff >= 14 and total_time_left < 600:  # 2+ TD lead with < 10 min
                home_win_prob = 0.88
            elif score_diff >= 7 and total_time_left < 300:  # 1+ TD lead with < 5 min
                home_win_prob = 0.78
            else:
                # Use exponential decay model
                time_factor = math.exp(-total_time_left / 1800)  # 30-minute half-life
                score_factor = 1 / (1 + math.exp(-score_diff / 7))  # Sigmoid function
                home_win_prob = 0.5 + (score_factor - 0.5) * (0.5 + time_factor * 0.5)
        else:  # Away team leading or tied
            score_diff = abs(score_diff)
            if score_diff >= 21 and total_time_left < 900:
                away_win_prob = 0.95
            elif score_diff >= 14 and total_time_left < 600:
                away_win_prob = 0.88
            elif score_diff >= 7 and total_time_left < 300:
                away_win_prob = 0.78
            else:
                time_factor = math.exp(-total_time_left / 1800)
                score_factor = 1 / (1 + math.exp(-score_diff / 7))
                away_win_prob = 0.5 + (score_factor - 0.5) * (0.5 + time_factor * 0.5)
                home_win_prob = 1 - away_win_prob

        if score_diff == 0:  # Tied game
            home_win_prob = 0.52  # Slight home field advantage
            away_win_prob = 0.48
        elif 'away_win_prob' not in locals():
            away_win_prob = 1 - home_win_prob

        # Tie probability (very rare in NFL)
        tie_prob = 0.002 if quarter >= 4 and abs(score_diff) <= 3 else 0.0

        # Normalize if tie probability added
        if tie_prob > 0:
            total = home_win_prob + away_win_prob + tie_prob
            home_win_prob /= total
            away_win_prob /= total
            tie_prob /= total

        # Expected final scores
        remaining_possessions = max(1, total_time_left / 180)  # ~3 minutes per possession
        expected_points_per_possession = 2.3  # NFL average

        expected_home_score = game_state.home_score + (remaining_possessions * expected_points_per_possession * home_win_prob)
        expected_away_score = game_state.away_score + (remaining_possessions * expected_points_per_possession * away_win_prob)

        # Confidence calculation
        confidence_level = "high" if max(home_win_prob, away_win_prob) > 0.8 else "medium" if max(home_win_prob, away_win_prob) > 0.6 else "low"
        margin = abs(home_win_prob - away_win_prob)
        confidence_interval = (max(0, home_win_prob - margin * 0.5), min(1, home_win_prob + margin * 0.5))

        factors = []
        if abs(score_diff) >= 14:
            factors.append("significant score differential")
        if total_time_left < 300:
            factors.append("limited time remaining")
        if game_state.possession == ("home" if home_win_prob > away_win_prob else "away"):
            factors.append("favorable possession")

        confidence = PredictionConfidence(
            probability=max(home_win_prob, away_win_prob),
            confidence_interval=confidence_interval,
            confidence_level=confidence_level,
            factors=factors
        )

        return GameOutcomeLikelihood(
            home_win_prob=home_win_prob,
            away_win_prob=away_win_prob,
            tie_prob=tie_prob,
            expected_home_score=expected_home_score,
            expected_away_score=expected_away_score,
            confidence=confidence
        )

    def _generate_contextual_insights(self, game_state: GameState, context: Dict[str, Any], situations: List[GameSituation]) -> List[ContextualInsight]:
        """Generate contextual insights about current situation"""

        insights = []

        # Historical comparison insight
        similar_situations = self.historical_comparator.find_similar_situations(game_state, limit=3)
        if similar_situations:
            best_match = similar_situations[0]
            insight = ContextualInsight(
                insight_type="historical_comparison",
                message=f"This situation is {best_match['similarity_score']:.0%} similar to {best_match['context']}. In that game, the outcome was: {best_match['outcome']}",
                historical_comparison=best_match,
                statistical_backing={"similarity_score": best_match['similarity_score']},
                relevance_score=best_match['similarity_score']
            )
            insights.append(insight)

        # Situation-specific insights
        for situation in situations:
            if situation == GameSituation.RED_ZONE:
                success_rate = self.historical_comparator.calculate_situation_success_rate(
                    situation, context
                )
                insight = ContextualInsight(
                    insight_type="situation_analysis",
                    message=f"Red zone possessions result in touchdowns {success_rate:.1%} of the time in similar situations. Key factors include goal line stands and red zone efficiency.",
                    historical_comparison=None,
                    statistical_backing={"red_zone_success_rate": success_rate},
                    relevance_score=0.85
                )
                insights.append(insight)

            elif situation == GameSituation.FOURTH_DOWN:
                insight = ContextualInsight(
                    insight_type="critical_decision",
                    message=f"4th down decisions in this field position are successful {self.historical_comparator.calculate_situation_success_rate(situation, context):.1%} of the time. Coaches typically favor conservative play calling here.",
                    historical_comparison=None,
                    statistical_backing={"fourth_down_success": self.historical_comparator.calculate_situation_success_rate(situation, context)},
                    relevance_score=0.90
                )
                insights.append(insight)

            elif situation == GameSituation.TWO_MINUTE_WARNING:
                insight = ContextualInsight(
                    insight_type="time_management",
                    message="Two-minute warning creates strategic timeout advantage. Teams typically accelerate pace and utilize sideline routes to preserve time.",
                    historical_comparison=None,
                    statistical_backing={"scoring_rate_final_2min": 0.42},
                    relevance_score=0.75
                )
                insights.append(insight)

        # Performance-based insights
        if context.get('team_stats'):
            home_stats = context['team_stats'].get('home', {})
            away_stats = context['team_stats'].get('away', {})

            if home_stats.get('red_zone_efficiency', 0) > 0.7:
                insight = ContextualInsight(
                    insight_type="team_strength",
                    message=f"The home team ranks in the top tier for red zone efficiency at {home_stats['red_zone_efficiency']:.1%}, making them dangerous in scoring position.",
                    historical_comparison=None,
                    statistical_backing={"red_zone_efficiency": home_stats['red_zone_efficiency']},
                    relevance_score=0.70
                )
                insights.append(insight)

        return sorted(insights, key=lambda x: x.relevance_score, reverse=True)[:5]

    def _analyze_momentum(self, game_state: GameState, context: Dict[str, Any]) -> MomentumAnalysis:
        """Analyze current momentum"""

        # Calculate momentum based on recent plays and scoring
        last_play = game_state.last_play
        recent_scoring = context.get('recent_scoring', [])
        drive_info = game_state.drive_info

        momentum_score = 0.0
        momentum_factors = []

        # Recent scoring momentum
        if recent_scoring:
            last_score = recent_scoring[-1]
            if last_score.get('team') == game_state.possession:
                momentum_score += 0.3
                momentum_factors.append("recent scoring drive")
            else:
                momentum_score -= 0.2
                momentum_factors.append("opponent just scored")

        # Drive momentum
        if drive_info:
            plays_in_drive = drive_info.get('plays', 0)
            yards_gained = drive_info.get('yards', 0)

            if plays_in_drive > 0:
                yards_per_play = yards_gained / plays_in_drive
                if yards_per_play > 6:
                    momentum_score += 0.2
                    momentum_factors.append("efficient drive")
                elif yards_per_play < 3:
                    momentum_score -= 0.2
                    momentum_factors.append("struggling drive")

        # Last play momentum
        if last_play:
            play_type = last_play.get('type', '')
            yards_gained = last_play.get('yards', 0)

            if 'touchdown' in play_type.lower():
                momentum_score += 0.4
                momentum_factors.append("touchdown scored")
            elif 'turnover' in play_type.lower():
                momentum_score -= 0.4
                momentum_factors.append("turnover committed")
            elif yards_gained > 15:
                momentum_score += 0.1
                momentum_factors.append("big play")
            elif yards_gained < 0:
                momentum_score -= 0.1
                momentum_factors.append("negative play")

        # Time and score context
        time_remaining = self._parse_time_remaining(game_state.time_remaining)
        score_diff = game_state.home_score - game_state.away_score

        if game_state.quarter >= 4:
            if score_diff > 0 and game_state.possession == 'home':
                momentum_score += 0.1  # Home team controlling late
            elif score_diff < 0 and game_state.possession == 'away':
                momentum_score += 0.1  # Away team controlling late
            elif abs(score_diff) <= 7 and time_remaining < 300:
                momentum_score += 0.15  # Close game, exciting momentum
                momentum_factors.append("close game tension")

        # Normalize momentum score
        momentum_score = max(-1.0, min(1.0, momentum_score))

        # Determine momentum level
        if momentum_score > 0.6:
            momentum_level = MomentumShift.MASSIVE_POSITIVE
        elif momentum_score > 0.3:
            momentum_level = MomentumShift.MODERATE_POSITIVE
        elif momentum_score > 0.1:
            momentum_level = MomentumShift.SLIGHT_POSITIVE
        elif momentum_score < -0.6:
            momentum_level = MomentumShift.MASSIVE_NEGATIVE
        elif momentum_score < -0.3:
            momentum_level = MomentumShift.MODERATE_NEGATIVE
        elif momentum_score < -0.1:
            momentum_level = MomentumShift.SLIGHT_NEGATIVE
        else:
            momentum_level = MomentumShift.NEUTRAL

        # Determine trend
        recent_momentum_changes = context.get('momentum_history', [])
        if len(recent_momentum_changes) >= 2:
            if recent_momentum_changes[-1] > recent_momentum_changes[-2]:
                trend = "increasing"
            elif recent_momentum_changes[-1] < recent_momentum_changes[-2]:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "stable"

        shift_reason = f"Based on {', '.join(momentum_factors[:3])}" if momentum_factors else "No significant momentum factors"

        return MomentumAnalysis(
            current_momentum=momentum_level,
            shift_magnitude=abs(momentum_score),
            shift_reason=shift_reason,
            key_factors=momentum_factors,
            trend_direction=trend
        )

    def _analyze_key_matchups(self, game_state: GameState, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze key matchups affecting current situation"""

        matchups = {
            'offensive_line_vs_pass_rush': {
                'advantage': 'neutral',
                'impact_level': 'medium',
                'description': 'Pass protection will be crucial for sustained drives'
            },
            'secondary_vs_receivers': {
                'advantage': 'neutral',
                'impact_level': 'high',
                'description': 'Coverage matchups determine big play potential'
            },
            'run_defense_vs_running_game': {
                'advantage': 'neutral',
                'impact_level': 'medium',
                'description': 'Ground game effectiveness sets up play action'
            }
        }

        # Add situation-specific matchups
        situations = self.situation_analyzer.identify_situation(game_state)

        if GameSituation.RED_ZONE in situations:
            matchups['red_zone_offense_vs_goal_line_defense'] = {
                'advantage': 'defense',
                'impact_level': 'very_high',
                'description': 'Compressed field favors defensive coverage and run stopping'
            }

        if GameSituation.FOURTH_DOWN in situations:
            matchups['conversion_offense_vs_short_yardage_defense'] = {
                'advantage': 'defense',
                'impact_level': 'critical',
                'description': 'Short yardage situations typically favor defensive fronts'
            }

        return matchups

    def _parse_time_remaining(self, time_str: str) -> int:
        """Parse time remaining string to seconds"""
        try:
            parts = time_str.split(':')
            return int(parts[0]) * 60 + int(parts[1])
        except:
            return 0

    def get_insight_summary(self, insight: NarratorInsight) -> Dict[str, Any]:
        """Generate a summary of the narrator insight for API responses"""

        return {
            'timestamp': insight.timestamp.isoformat(),
            'game_situation': {
                'quarter': insight.game_state.quarter,
                'time_remaining': insight.game_state.time_remaining,
                'down': insight.game_state.down,
                'yards_to_go': insight.game_state.yards_to_go,
                'field_position': insight.game_state.yard_line,
                'possession': insight.game_state.possession,
                'score': {
                    'home': insight.game_state.home_score,
                    'away': insight.game_state.away_score
                }
            },
            'predictions': {
                'next_score': {
                    'team': insight.scoring_probability.team,
                    'type': insight.scoring_probability.score_type,
                    'probability': round(insight.scoring_probability.probability, 3),
                    'expected_points': round(insight.scoring_probability.expected_points, 1),
                    'confidence': insight.scoring_probability.confidence.confidence_level
                },
                'game_outcome': {
                    'home_win_probability': round(insight.game_outcome.home_win_prob, 3),
                    'away_win_probability': round(insight.game_outcome.away_win_prob, 3),
                    'expected_final_score': {
                        'home': round(insight.game_outcome.expected_home_score, 1),
                        'away': round(insight.game_outcome.expected_away_score, 1)
                    },
                    'confidence': insight.game_outcome.confidence.confidence_level
                }
            },
            'insights': [
                {
                    'type': ci.insight_type,
                    'message': ci.message,
                    'relevance': round(ci.relevance_score, 2)
                }
                for ci in insight.contextual_insights[:3]  # Top 3 insights
            ],
            'momentum': {
                'current_level': insight.momentum_analysis.current_momentum.value,
                'magnitude': round(insight.momentum_analysis.shift_magnitude, 2),
                'trend': insight.momentum_analysis.trend_direction,
                'explanation': insight.momentum_analysis.shift_reason
            },
            'decision_recommendation': asdict(insight.decision_recommendation) if insight.decision_recommendation else None,
            'weather_impact': insight.weather_impact,
            'key_matchups': insight.key_matchup_analysis
        }


# Example usage and testing
if __name__ == "__main__":
    logger.info("AI Game Narrator for Live NFL Games initialized")

    # Create sample game state
    sample_game_state = GameState(
        quarter=4,
        time_remaining="2:15",
        down=3,
        yards_to_go=7,
        yard_line=22,  # Red zone
        home_score=17,
        away_score=14,
        possession="home",
        last_play={"type": "pass_complete", "yards": 12, "result": "first_down"},
        drive_info={"plays": 8, "yards": 64, "time_consumed": "4:32"},
        game_id="2024_week15_chiefs_bills",
        week=15,
        season=2024
    )

    # Create sample context
    sample_context = {
        'weather_data': {
            'temperature': 28,
            'wind_speed': 12,
            'precipitation': 0.0,
            'dome_game': False
        },
        'team_stats': {
            'home': {'red_zone_efficiency': 0.72, 'offensive_rating': 0.78},
            'away': {'red_zone_efficiency': 0.65, 'defensive_rating': 0.82}
        },
        'recent_scoring': [
            {'team': 'away', 'points': 7, 'time': '8:45'},
            {'team': 'home', 'points': 3, 'time': '3:22'}
        ]
    }

    # Initialize narrator
    narrator = AIGameNarrator()

    # Generate comprehensive insight
    insight = narrator.generate_comprehensive_insight(sample_game_state, sample_context)

    # Get summary for API
    summary = narrator.get_insight_summary(insight)

    print("\n=== AI Game Narrator Insight ===")
    print(json.dumps(summary, indent=2))

    logger.info("AI Game Narrator demonstration complete!")