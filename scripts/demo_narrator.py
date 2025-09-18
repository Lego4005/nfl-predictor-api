#!/usr/bin/env python3
"""
AI Game Narrator Demo
Demonstrates core functionality and API structure without external dependencies
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import json


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
    time_remaining: str
    down: int
    yards_to_go: int
    yard_line: int
    home_score: int
    away_score: int
    possession: str
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
    confidence_level: str
    factors: List[str]


@dataclass
class ScoringProbability:
    """Next scoring prediction"""
    team: str
    score_type: str
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
    trend_direction: str


@dataclass
class DecisionRecommendation:
    """4th down or critical decision recommendation"""
    situation: str
    recommendation: str
    success_probability: float
    expected_value: float
    alternative_options: List[Dict[str, Any]]
    reasoning: str


class MockNarrator:
    """Mock AI Game Narrator for demonstration"""

    def __init__(self):
        self.name = "AI Game Narrator"

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

        return situations if situations else [GameSituation.OPENING_DRIVE]

    def calculate_scoring_probability(self, game_state: GameState) -> ScoringProbability:
        """Calculate next scoring probability"""
        field_position = game_state.yard_line
        down = game_state.down

        # Base probabilities by field position
        if field_position <= 10:
            td_prob = 0.75
            fg_prob = 0.20
        elif field_position <= 20:
            td_prob = 0.60
            fg_prob = 0.30
        elif field_position <= 40:
            td_prob = 0.35
            fg_prob = 0.45
        else:
            td_prob = 0.25
            fg_prob = 0.35

        # Adjust for down
        if down == 4:
            td_prob *= 0.6
            fg_prob *= 0.8

        # Determine most likely outcome
        no_score_prob = 1 - td_prob - fg_prob
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

        confidence_level = "high" if probability > 0.7 else "medium" if probability > 0.5 else "low"
        factors = []
        if field_position <= 20:
            factors.append("excellent field position")
        if down <= 2:
            factors.append("early down advantage")

        confidence = PredictionConfidence(
            probability=probability,
            confidence_interval=(max(0, probability - 0.15), min(1, probability + 0.15)),
            confidence_level=confidence_level,
            factors=factors
        )

        return ScoringProbability(
            team=game_state.possession,
            score_type=score_type,
            probability=probability,
            expected_points=expected_points,
            confidence=confidence
        )

    def calculate_game_outcome(self, game_state: GameState) -> GameOutcomeLikelihood:
        """Calculate game outcome probabilities"""
        score_diff = game_state.home_score - game_state.away_score
        quarter = game_state.quarter

        # Simple win probability based on score and time
        if score_diff > 0:  # Home leading
            if quarter >= 4 and score_diff >= 14:
                home_win_prob = 0.85
            elif quarter >= 4 and score_diff >= 7:
                home_win_prob = 0.72
            else:
                home_win_prob = 0.55 + (score_diff / 35)  # Scale with score difference
        elif score_diff < 0:  # Away leading
            away_lead = abs(score_diff)
            if quarter >= 4 and away_lead >= 14:
                home_win_prob = 0.15
            elif quarter >= 4 and away_lead >= 7:
                home_win_prob = 0.28
            else:
                home_win_prob = 0.45 - (away_lead / 35)
        else:  # Tied
            home_win_prob = 0.52  # Slight home field advantage

        home_win_prob = max(0.05, min(0.95, home_win_prob))
        away_win_prob = 1 - home_win_prob
        tie_prob = 0.002 if quarter >= 4 and abs(score_diff) <= 3 else 0.0

        # Normalize if tie probability added
        if tie_prob > 0:
            total = home_win_prob + away_win_prob + tie_prob
            home_win_prob /= total
            away_win_prob /= total

        # Expected final scores (simple estimation)
        remaining_points = max(3, (5 - quarter) * 7)  # Rough estimate
        expected_home_score = game_state.home_score + (remaining_points * home_win_prob)
        expected_away_score = game_state.away_score + (remaining_points * away_win_prob)

        confidence_level = "high" if max(home_win_prob, away_win_prob) > 0.8 else "medium"
        factors = ["score differential", "time remaining", "field position"]

        confidence = PredictionConfidence(
            probability=max(home_win_prob, away_win_prob),
            confidence_interval=(0.4, 0.9),
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

    def analyze_momentum(self, game_state: GameState) -> MomentumAnalysis:
        """Analyze current momentum"""
        last_play = game_state.last_play
        score_diff = game_state.home_score - game_state.away_score

        momentum_score = 0.0
        key_factors = []

        # Analyze last play
        if last_play:
            play_type = last_play.get('type', '').lower()
            yards = last_play.get('yards', 0)

            if 'touchdown' in play_type:
                momentum_score += 0.4
                key_factors.append("touchdown scored")
            elif 'turnover' in play_type or 'interception' in play_type:
                momentum_score -= 0.4
                key_factors.append("turnover committed")
            elif yards > 15:
                momentum_score += 0.1
                key_factors.append("big play")
            elif yards < 0:
                momentum_score -= 0.1
                key_factors.append("negative play")

        # Score context
        if game_state.possession == 'home' and score_diff > 0:
            momentum_score += 0.1
            key_factors.append("home team controlling with lead")
        elif game_state.possession == 'away' and score_diff < 0:
            momentum_score += 0.1
            key_factors.append("away team controlling with lead")

        # Time pressure
        if game_state.quarter >= 4:
            time_parts = game_state.time_remaining.split(':')
            total_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
            if total_seconds < 300 and abs(score_diff) <= 7:
                momentum_score += 0.15
                key_factors.append("close game tension")

        # Determine momentum level
        if momentum_score > 0.3:
            momentum_level = MomentumShift.MODERATE_POSITIVE
        elif momentum_score > 0.1:
            momentum_level = MomentumShift.SLIGHT_POSITIVE
        elif momentum_score < -0.3:
            momentum_level = MomentumShift.MODERATE_NEGATIVE
        elif momentum_score < -0.1:
            momentum_level = MomentumShift.SLIGHT_NEGATIVE
        else:
            momentum_level = MomentumShift.NEUTRAL

        shift_reason = f"Based on {', '.join(key_factors[:3])}" if key_factors else "No significant factors"

        return MomentumAnalysis(
            current_momentum=momentum_level,
            shift_magnitude=abs(momentum_score),
            shift_reason=shift_reason,
            key_factors=key_factors,
            trend_direction="stable"
        )

    def generate_contextual_insights(self, game_state: GameState, situations: List[GameSituation]) -> List[ContextualInsight]:
        """Generate contextual insights"""
        insights = []

        # Historical comparison insight
        insight = ContextualInsight(
            insight_type="historical_comparison",
            message="This situation is 87% similar to Chiefs vs Patriots 2023 Week 15. In that game, the home team scored a touchdown with 1:47 remaining and won by 3 points.",
            historical_comparison={
                "game": "2023_week15_chiefs_patriots",
                "similarity_score": 0.87,
                "outcome": "Home team victory"
            },
            statistical_backing={"similarity_score": 0.87},
            relevance_score=0.87
        )
        insights.append(insight)

        # Situation-specific insights
        for situation in situations:
            if situation == GameSituation.RED_ZONE:
                insight = ContextualInsight(
                    insight_type="situation_analysis",
                    message="Red zone possessions result in touchdowns 67% of the time in similar weather conditions and field position. The home team has been particularly effective in the red zone this season at 72%.",
                    historical_comparison=None,
                    statistical_backing={"red_zone_td_rate": 0.67, "team_red_zone_efficiency": 0.72},
                    relevance_score=0.85
                )
                insights.append(insight)

            elif situation == GameSituation.FOURTH_DOWN:
                insight = ContextualInsight(
                    insight_type="critical_decision",
                    message="4th down conversions in this field position succeed 45% of the time. Teams typically favor field goal attempts from this distance, with an 82% success rate.",
                    historical_comparison=None,
                    statistical_backing={"fourth_down_success": 0.45, "fg_success_rate": 0.82},
                    relevance_score=0.90
                )
                insights.append(insight)

            elif situation == GameSituation.TWO_MINUTE_WARNING:
                insight = ContextualInsight(
                    insight_type="time_management",
                    message="Two-minute drill scenarios like this result in scores 42% of the time. Clock management and sideline routes become critical for preserving timeouts.",
                    historical_comparison=None,
                    statistical_backing={"two_minute_score_rate": 0.42},
                    relevance_score=0.75
                )
                insights.append(insight)

        return sorted(insights, key=lambda x: x.relevance_score, reverse=True)[:5]

    def recommend_fourth_down_decision(self, game_state: GameState) -> Optional[DecisionRecommendation]:
        """Recommend 4th down decision"""
        if game_state.down != 4:
            return None

        yard_line = game_state.yard_line
        yards_to_go = game_state.yards_to_go

        # Simple decision logic
        if yard_line <= 35 and yards_to_go <= 5:  # Field goal range, short yardage
            recommendation = "field_goal"
            success_prob = 0.82
            reasoning = f"High percentage field goal from {17 + (100 - yard_line)} yards"
            alternatives = [
                {"option": "go_for_it", "success_probability": 0.45, "reasoning": "Risky but keeps drive alive"},
                {"option": "punt", "success_probability": 0.95, "reasoning": "Conservative field position play"}
            ]
        elif yards_to_go <= 2:  # Short yardage situation
            recommendation = "go_for_it"
            success_prob = 0.65
            reasoning = f"Short yardage situation with {yards_to_go} yards to convert"
            alternatives = [
                {"option": "punt", "success_probability": 0.95, "reasoning": "Give up possession but pin opponent"},
                {"option": "field_goal", "success_probability": 0.68, "reasoning": "Long field goal attempt"}
            ]
        else:  # Difficult conversion
            recommendation = "punt"
            success_prob = 0.95
            reasoning = f"Difficult {yards_to_go}-yard conversion, better to punt"
            alternatives = [
                {"option": "go_for_it", "success_probability": 0.25, "reasoning": "Low percentage conversion attempt"},
                {"option": "field_goal", "success_probability": 0.55, "reasoning": "Long field goal attempt"}
            ]

        return DecisionRecommendation(
            situation=f"4th and {yards_to_go} at {yard_line}-yard line",
            recommendation=recommendation,
            success_probability=success_prob,
            expected_value=success_prob * 3.5,  # Simplified expected value
            alternative_options=alternatives,
            reasoning=reasoning
        )

    def generate_comprehensive_insight(self, game_state: GameState, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive insight for current game state"""
        if context is None:
            context = {}

        # Analyze current situation
        situations = self.identify_situation(game_state)

        # Generate predictions
        scoring_prob = self.calculate_scoring_probability(game_state)
        game_outcome = self.calculate_game_outcome(game_state)
        momentum_analysis = self.analyze_momentum(game_state)
        contextual_insights = self.generate_contextual_insights(game_state, situations)
        decision_rec = self.recommend_fourth_down_decision(game_state)

        # Weather impact (simplified)
        weather_impact = None
        if context.get('weather_data'):
            weather_data = context['weather_data']
            if weather_data.get('dome_game'):
                weather_impact = {
                    'impact_level': 'none',
                    'narrative': 'Indoor game - weather conditions have no impact.'
                }
            else:
                temp = weather_data.get('temperature', 70)
                wind = weather_data.get('wind_speed', 5)
                if temp < 32 or wind > 15:
                    weather_impact = {
                        'impact_level': 'moderate',
                        'narrative': f'Cold temperatures ({temp}°F) and wind ({wind} mph) may affect passing and kicking accuracy.'
                    }
                else:
                    weather_impact = {
                        'impact_level': 'minimal',
                        'narrative': 'Weather conditions are favorable for all aspects of play.'
                    }

        return {
            'timestamp': datetime.now().isoformat(),
            'game_situation': {
                'quarter': game_state.quarter,
                'time_remaining': game_state.time_remaining,
                'down': game_state.down,
                'yards_to_go': game_state.yards_to_go,
                'field_position': game_state.yard_line,
                'possession': game_state.possession,
                'score': {'home': game_state.home_score, 'away': game_state.away_score},
                'situations': [s.value for s in situations]
            },
            'predictions': {
                'next_score': {
                    'team': scoring_prob.team,
                    'type': scoring_prob.score_type,
                    'probability': round(scoring_prob.probability, 3),
                    'expected_points': round(scoring_prob.expected_points, 1),
                    'confidence': scoring_prob.confidence.confidence_level
                },
                'game_outcome': {
                    'home_win_probability': round(game_outcome.home_win_prob, 3),
                    'away_win_probability': round(game_outcome.away_win_prob, 3),
                    'expected_final_score': {
                        'home': round(game_outcome.expected_home_score, 1),
                        'away': round(game_outcome.expected_away_score, 1)
                    },
                    'confidence': game_outcome.confidence.confidence_level
                }
            },
            'insights': [
                {
                    'type': ci.insight_type,
                    'message': ci.message,
                    'relevance': round(ci.relevance_score, 2)
                }
                for ci in contextual_insights[:3]
            ],
            'momentum': {
                'current_level': momentum_analysis.current_momentum.value,
                'magnitude': round(momentum_analysis.shift_magnitude, 2),
                'trend': momentum_analysis.trend_direction,
                'explanation': momentum_analysis.shift_reason
            },
            'decision_recommendation': asdict(decision_rec) if decision_rec else None,
            'weather_impact': weather_impact
        }


def demo_scenarios():
    """Demonstrate various game scenarios"""
    print("🏈 AI Game Narrator - Live Demo")
    print("=" * 60)

    narrator = MockNarrator()

    # Scenario 1: Red Zone Scoring Opportunity
    print("\n📍 SCENARIO 1: Red Zone Scoring Opportunity")
    print("-" * 40)

    game_state1 = GameState(
        quarter=4,
        time_remaining="2:15",
        down=3,
        yards_to_go=7,
        yard_line=18,  # Red zone
        home_score=17,
        away_score=14,
        possession="home",
        last_play={"type": "pass_complete", "yards": 12, "result": "first_down"},
        drive_info={"plays": 8, "yards": 64, "time_consumed": "4:32"},
        game_id="demo_game_1",
        week=15,
        season=2024
    )

    context1 = {
        "weather_data": {"temperature": 28, "wind_speed": 12, "dome_game": False},
        "team_stats": {"home": {"red_zone_efficiency": 0.72}}
    }

    insight1 = narrator.generate_comprehensive_insight(game_state1, context1)
    print(json.dumps(insight1, indent=2))

    # Scenario 2: Fourth Down Decision
    print("\n\n📍 SCENARIO 2: Fourth Down Decision")
    print("-" * 40)

    game_state2 = GameState(
        quarter=4,
        time_remaining="5:30",
        down=4,
        yards_to_go=2,
        yard_line=35,  # Field goal range
        home_score=14,
        away_score=17,
        possession="home",
        last_play={"type": "run", "yards": 3, "result": "short_of_first"},
        drive_info={"plays": 6, "yards": 28, "time_consumed": "2:45"},
        game_id="demo_game_2",
        week=10,
        season=2024
    )

    context2 = {
        "weather_data": {"temperature": 72, "wind_speed": 5, "dome_game": True}
    }

    insight2 = narrator.generate_comprehensive_insight(game_state2, context2)
    print(json.dumps(insight2, indent=2))

    # Scenario 3: Two-Minute Drill
    print("\n\n📍 SCENARIO 3: Two-Minute Drill Comeback")
    print("-" * 40)

    game_state3 = GameState(
        quarter=4,
        time_remaining="1:47",
        down=1,
        yards_to_go=10,
        yard_line=65,  # In opponent territory
        home_score=20,
        away_score=17,
        possession="away",  # Away team driving for potential win
        last_play={"type": "pass_complete", "yards": 25, "result": "big_play"},
        drive_info={"plays": 5, "yards": 45, "time_consumed": "1:15"},
        game_id="demo_game_3",
        week=17,
        season=2024
    )

    context3 = {
        "weather_data": {"temperature": 15, "wind_speed": 20, "dome_game": False},
        "recent_scoring": [
            {"team": "home", "points": 3, "time": "4:22", "type": "field_goal"},
            {"team": "away", "points": 7, "time": "7:15", "type": "touchdown"}
        ]
    }

    insight3 = narrator.generate_comprehensive_insight(game_state3, context3)
    print(json.dumps(insight3, indent=2))

    print("\n" + "=" * 60)
    print("🎯 Demo Complete!")
    print("\nKey Features Demonstrated:")
    print("✅ Real-time situation analysis")
    print("✅ Scoring probability predictions")
    print("✅ Game outcome likelihood")
    print("✅ Momentum shift detection")
    print("✅ Historical comparisons")
    print("✅ Weather impact analysis")
    print("✅ 4th down decision recommendations")
    print("✅ Contextual insights")

    print("\n📋 API Integration:")
    print("• POST /narrator/insight - Generate comprehensive insights")
    print("• GET /narrator/live-games - Monitor active games")
    print("• WebSocket /narrator/ws/{client_id} - Real-time updates")
    print("• GET /narrator/game/{game_id}/predictions - Specific predictions")

    print("\n🚀 Next Steps:")
    print("1. Install ML dependencies for advanced predictions")
    print("2. Set up ESPN API integration for live data")
    print("3. Deploy with Docker Compose")
    print("4. Configure monitoring and alerting")


if __name__ == "__main__":
    demo_scenarios()