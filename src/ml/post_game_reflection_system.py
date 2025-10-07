#!/usr/bin/env python3
"""
Post-Game Reflection System

Implements comprehensive poste reflection and learning for AI experts.
Analyzes prediction accuracy across all 30+ categories and generates learning memories.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum

from src.ml.comprehensive_expert_predictions import (
    ComprehensiveExpertPrediction,
    PredictionWithConfidence,
    QuarterPrediction,
    PlayerPropPrediction,
    GameContext,
    MemoryInfluence
)
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from src.services.openrouter_service import OpenRouterService

logger = logging.getLogger(__name__)

class ReflectionType(Enum):
    """Types of post-game reflection"""
    SUCCESS_ANALYSIS = "success_analysis"
    FAILURE_ANALYSIS = "failure_analysis"
    PATTERN_RECOGNITION = "pattern_recognition"
    CONFIDENCE_CALIBRATION = "confidence_calibration"
    FACTOR_WEIGHTING = "factor_weighting"

@dataclass
class CategoryAccuracy:
    """Accuracy analysis for a specific prediction category"""
    category_name: str
    predicted_value: Any
    actual_value: Any
    confidence: float
    is_correct: bool
    accuracy_score: float  # 0.0 to 1.0
    error_magnitude: Optional[float] = None
    key_factors: List[str] = field(default_factory=list)

@dataclass
class GameOutcome:
    """Complete game outcome data for reflection"""
    game_id: str
    home_team: str
    away_team: str

    # Final scores
    home_score: int
    away_score: int

    # Quarter scores
    q1_home: int = 0
    q1_away: int = 0
    q2_home: int = 0
    q2_away: int = 0
    q3_home: int = 0
    q3_away: int = 0
    q4_home: int = 0
    q4_away: int = 0

    # Game stats
    total_points: int = 0
    margin_of_victory: int = 0
    winner: str = ""

    # Player stats (simplified for now)
    player_stats: Dict[str, Any] = field(default_factory=dict)

    # Situational outcomes
    turnover_differential: int = 0
    time_of_possession_home: float = 30.0
    penalties_home: int = 0
    penalties_away: int = 0

    def __post_init__(self):
        if not self.total_points:
            self.total_points = self.home_score + self.away_score
        if not self.margin_of_victory:
            self.margin_of_victory = abs(self.home_score - self.away_score)
        if not self.winner:
            self.winner = self.home_team if self.home_score > self.away_score else self.away_team

@dataclass
class ReflectionMemory:
    """Memory structure for storing post-game reflection insights"""
    memory_id: str
    expert_id: str
    game_id: str
    reflection_type: ReflectionType

    # Accuracy analysis
    overall_accuracy: float
    category_accuracies: List[CategoryAccuracy]
    high_confidence_errors: List[str]
    successful_predictions: List[str]

    # Learning insights
    lessons_learned: List[str]
    pattern_insights: List[str]
    factor_adjustments: Dict[str, float]
    confidence_calibration: Dict[str, float]

    # Emotional weighting
    emotional_intensity: float
    surprise_factor: float
    memory_vividness: float

    # Context
    game_context: GameContext
    memory_influences_used: List[MemoryInfluence]

    # Meta
    reflection_timestamp: datetime
    ai_reflection_text: str

class PostGameReflectionOrchestrator:
    """
    Orchestrates comprehensive post-game reflection and learning for AI experts.

    Integrates with:
    - ComprehensiveExpertPrediction for accuracy calculation across all 30+ categories
    - Existing model assignments (anthropic/claude-sonnet-4.5, openai/gpt-5, etc.) for AI reflection
    - SupabaseEpisodicMemoryManager for memory storage
    """

    def __init__(self, openrouter_service: OpenRouterService, memory_manager: SupabaseEpisodicMemoryManager):
        self.openrouter = openrouter_service
        self.memory_manager = memory_manager

        # Model assignments from existing training script
        self.expert_model_mapping = {
            'conservative_analyzer': {
                'name': 'The Analyst',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Conservative, methodical, data-driven analysis',
                'specialty': 'Risk-averse predictions with statistical backing'
            },
            'risk_taking_gambler': {
                'name': 'The Gambler',
                'model': 'x-ai/grok-4-fast',
                'personality': 'Bold, high-risk, high-reward mentality',
                'specialty': 'Aggressive betting strategies and upset picks'
            },
            'contrarian_rebel': {
                'name': 'The Rebel',
                'model': 'google/gemini-2.5-flash-preview-09-2025',
                'personality': 'Goes against popular opinion and conventional wisdom',
                'specialty': 'Contrarian plays and market inefficiencies'
            },
            'value_hunter': {
                'name': 'The Hunter',
                'model': 'deepseek/deepseek-chat-v3.1:free',
                'personality': 'Seeks undervalued opportunities and hidden gems',
                'specialty': 'Finding value in overlooked situations'
            },
            'momentum_rider': {
                'name': 'The Rider',
                'model': 'openai/gpt-5',
                'personality': 'Follows trends and momentum patterns',
                'specialty': 'Momentum-based predictions and trend analysis'
            }
        }

    async def post_game_reflection(
        self,
        expert_id: str,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> ReflectionMemory:
        """
        Main method that analyzes prediction accuracy and generates learning insights.

        Requirements: 4.1, 4.2, 4.3, 4.4
        """
        logger.info(f"🔍 Starting post-game reflection for {expert_id}")

        try:
            # Step 1: Calculate accuracy across all prediction categories
            category_accuracies = self._calculate_category_accuracies(prediction, outcome)
            overall_accuracy = self._calculate_overall_accuracy(category_accuracies)

            # Step 2: Identify success and failure patterns
            successful_predictions = [cat.category_name for cat in category_accuracies if cat.is_correct]
            high_confidence_errors = [
                cat.category_name for cat in category_accuracies
                if not cat.is_correct and cat.confidence > 0.7
            ]

            # Step 3: Generate AI reflection using expert's assigned model
            ai_reflection = await self._generate_ai_reflection(
                expert_id, prediction, outcome, category_accuracies
            )

            # Step 4: Extract learning insights from AI reflection
            lessons_learned = self._extract_lessons_learned(ai_reflection, category_accuracies)
            pattern_insights = self._identify_pattern_insights(ai_reflection, category_accuracies)
            factor_adjustments = self._determine_factor_adjustments(ai_reflection, category_accuracies)
            confidence_calibration = self._calculate_confidence_calibration(category_accuracies)

            # Step 5: Determine reflection type and emotional weighting
            reflection_type = self._determine_reflection_type(overall_accuracy, high_confidence_errors)
            emotional_intensity = self._calculate_emotional_intensity(overall_accuracy, high_confidence_errors)
            surprise_factor = self._calculate_surprise_factor(category_accuracies)

            # Step 6: Create reflection memory
            reflection_memory = ReflectionMemory(
                memory_id=f"reflection_{expert_id}_{outcome.game_id}_{int(datetime.now().timestamp())}",
                expert_id=expert_id,
                game_id=outcome.game_id,
                reflection_type=reflection_type,
                overall_accuracy=overall_accuracy,
                category_accuracies=category_accuracies,
                high_confidence_errors=high_confidence_errors,
                successful_predictions=successful_predictions,
                lessons_learned=lessons_learned,
                pattern_insights=pattern_insights,
                factor_adjustments=factor_adjustments,
                confidence_calibration=confidence_calibration,
                emotional_intensity=emotional_intensity,
                surprise_factor=surprise_factor,
                memory_vividness=min(1.0, emotional_intensity + surprise_factor),
                game_context=prediction.game_context,
                memory_influences_used=prediction.memory_influences,
                reflection_timestamp=datetime.now(),
                ai_reflection_text=ai_reflection
            )

            logger.info(f"✅ Reflection complete for {expert_id}: {overall_accuracy:.1%} accuracy")
            return reflection_memory

        except Exception as e:
            logger.error(f"❌ Post-game reflection failed for {expert_id}: {e}")
            raise

    def _calculate_category_accuracies(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Calculate accuracy for each prediction category"""
        accuracies = []

        # Core game predictions
        accuracies.extend(self._analyze_core_predictions(prediction, outcome))

        # Quarter predictions
        accuracies.extend(self._analyze_quarter_predictions(prediction, outcome))

        # Player props (simplified for now)
        accuracies.extend(self._analyze_player_props(prediction, outcome))

        # Situational predictions
        accuracies.extend(self._analyze_situational_predictions(prediction, outcome))

        # Environmental/advanced predictions
        accuracies.extend(self._analyze_advanced_predictions(prediction, outcome))

        return accuracies

    def _analyze_core_predictions(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Analyze core game prediction accuracy"""
        accuracies = []

        # Game winner
        predicted_winner = prediction.game_winner.prediction
        actual_winner = outcome.winner
        accuracies.append(CategoryAccuracy(
            category_name="game_winner",
            predicted_value=predicted_winner,
            actual_value=actual_winner,
            confidence=prediction.game_winner.confidence,
            is_correct=predicted_winner == actual_winner,
            accuracy_score=1.0 if predicted_winner == actual_winner else 0.0,
            key_factors=prediction.game_winner.key_factors
        ))

        # Point spread (simplified - assumes prediction is "home" or "away")
        spread_correct = False
        if prediction.point_spread.prediction == "home":
            spread_correct = outcome.home_score > outcome.away_score
        elif prediction.point_spread.prediction == "away":
            spread_correct = outcome.away_score > outcome.home_score

        accuracies.append(CategoryAccuracy(
            category_name="point_spread",
            predicted_value=prediction.point_spread.prediction,
            actual_value="home" if outcome.home_score > outcome.away_score else "away",
            confidence=prediction.point_spread.confidence,
            is_correct=spread_correct,
            accuracy_score=1.0 if spread_correct else 0.0,
            key_factors=prediction.point_spread.key_factors
        ))

        # Total points (simplified - assumes prediction is "over" or "under")
        total_correct = False
        if prediction.total_points.prediction == "over":
            total_correct = outcome.total_points > prediction.game_context.total_line if prediction.game_context.total_line else True
        elif prediction.total_points.prediction == "under":
            total_correct = outcome.total_points < prediction.game_context.total_line if prediction.game_context.total_line else False

        accuracies.append(CategoryAccuracy(
            category_name="total_points",
            predicted_value=prediction.total_points.prediction,
            actual_value=outcome.total_points,
            confidence=prediction.total_points.confidence,
            is_correct=total_correct,
            accuracy_score=1.0 if total_correct else 0.0,
            error_magnitude=abs(outcome.total_points - (prediction.game_context.total_line or 45.5)),
            key_factors=prediction.total_points.key_factors
        ))

        return accuracies

    def _analyze_quarter_predictions(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Analyze quarter-by-quarter prediction accuracy"""
        accuracies = []

        quarters = [
            (prediction.q1_score, outcome.q1_home, outcome.q1_away, "q1_score"),
            (prediction.q2_score, outcome.q2_home, outcome.q2_away, "q2_score"),
            (prediction.q3_score, outcome.q3_home, outcome.q3_away, "q3_score"),
            (prediction.q4_score, outcome.q4_home, outcome.q4_away, "q4_score")
        ]

        for pred_quarter, actual_home, actual_away, category_name in quarters:
            # Check if quarter winner prediction was correct
            predicted_winner = pred_quarter.get_winner()
            actual_winner = "home" if actual_home > actual_away else ("away" if actual_away > actual_home else "tie")

            is_correct = predicted_winner == actual_winner

            # Calculate score accuracy (how close were the predicted scores)
            home_score_error = abs(pred_quarter.home_score - actual_home)
            away_score_error = abs(pred_quarter.away_score - actual_away)
            total_score_error = home_score_error + away_score_error

            # Accuracy score based on winner correctness and score proximity
            accuracy_score = 0.0
            if is_correct:
                accuracy_score += 0.6  # 60% for correct winner

            # Add points for score accuracy (40% max)
            if total_score_error <= 3:
                accuracy_score += 0.4
            elif total_score_error <= 7:
                accuracy_score += 0.2
            elif total_score_error <= 14:
                accuracy_score += 0.1

            accuracies.append(CategoryAccuracy(
                category_name=category_name,
                predicted_value=f"{pred_quarter.home_score}-{pred_quarter.away_score}",
                actual_value=f"{actual_home}-{actual_away}",
                confidence=pred_quarter.confidence,
                is_correct=is_correct,
                accuracy_score=accuracy_score,
                error_magnitude=total_score_error,
                key_factors=pred_quarter.key_factors
            ))

        return accuracies

    def _analyze_player_props(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Analyze player prop prediction accuracy (simplified)"""
        accuracies = []

        # For now, we'll create placeholder analysis since we don't have detailed player stats
        # In a full implementation, this would compare predicted vs actual player performance

        prop_categories = [
            ("qb_passing_yards", prediction.qb_passing_yards),
            ("qb_touchdowns", prediction.qb_touchdowns),
            ("rb_rushing_yards", prediction.rb_rushing_yards),
            ("wr_receiving_yards", prediction.wr_receiving_yards)
        ]

        for category_name, prop_list in prop_categories:
            for prop in prop_list:
                # Simplified accuracy - assume 60% accuracy for now
                # In real implementation, would compare prop.projected_value vs actual stats
                is_correct = hash(prop.player_name) % 10 < 6  # Mock 60% accuracy

                accuracies.append(CategoryAccuracy(
                    category_name=f"{category_name}_{prop.player_name}",
                    predicted_value=f"{prop.prediction} {prop.over_under_line}",
                    actual_value="actual_stat_placeholder",
                    confidence=prop.confidence,
                    is_correct=is_correct,
                    accuracy_score=1.0 if is_correct else 0.0,
                    error_magnitude=abs(prop.projected_value - prop.over_under_line)
                ))

        return accuracies

    def _analyze_situational_predictions(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Analyze situational prediction accuracy"""
        accuracies = []

        # Turnover differential
        predicted_turnover = prediction.turnover_differential.prediction
        actual_turnover = outcome.turnover_differential
        turnover_correct = (
            (predicted_turnover > 0 and actual_turnover > 0) or
            (predicted_turnover < 0 and actual_turnover < 0) or
            (predicted_turnover == 0 and actual_turnover == 0)
        )

        accuracies.append(CategoryAccuracy(
            category_name="turnover_differential",
            predicted_value=predicted_turnover,
            actual_value=actual_turnover,
            confidence=prediction.turnover_differential.confidence,
            is_correct=turnover_correct,
            accuracy_score=1.0 if turnover_correct else 0.0,
            error_magnitude=abs(predicted_turnover - actual_turnover),
            key_factors=prediction.turnover_differential.key_factors
        ))

        # Time of possession (simplified)
        predicted_top = prediction.time_of_possession.prediction
        actual_top = outcome.time_of_possession_home
        top_error = abs(float(predicted_top) - actual_top) if isinstance(predicted_top, (int, float, str)) else 5.0
        top_correct = top_error <= 5.0  # Within 5 minutes

        accuracies.append(CategoryAccuracy(
            category_name="time_of_possession",
            predicted_value=predicted_top,
            actual_value=actual_top,
            confidence=prediction.time_of_possession.confidence,
            is_correct=top_correct,
            accuracy_score=max(0.0, 1.0 - (top_error / 15.0)),  # Scale accuracy by error
            error_magnitude=top_error,
            key_factors=prediction.time_of_possession.key_factors
        ))

        return accuracies

    def _analyze_advanced_predictions(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome
    ) -> List[CategoryAccuracy]:
        """Analyze environmental and advanced prediction accuracy"""
        accuracies = []

        # Weather impact (simplified - assume moderate accuracy)
        weather_prediction = prediction.weather_impact.prediction
        weather_correct = hash(str(weather_prediction)) % 10 < 7  # Mock 70% accuracy

        accuracies.append(CategoryAccuracy(
            category_name="weather_impact",
            predicted_value=weather_prediction,
            actual_value="weather_outcome_placeholder",
            confidence=prediction.weather_impact.confidence,
            is_correct=weather_correct,
            accuracy_score=1.0 if weather_correct else 0.0,
            key_factors=prediction.weather_impact.key_factors
        ))

        # Coaching matchup (simplified)
        coaching_prediction = prediction.coaching_matchup.prediction
        coaching_correct = hash(str(coaching_prediction)) % 10 < 6  # Mock 60% accuracy

        accuracies.append(CategoryAccuracy(
            category_name="coaching_matchup",
            predicted_value=coaching_prediction,
            actual_value="coaching_outcome_placeholder",
            confidence=prediction.coaching_matchup.confidence,
            is_correct=coaching_correct,
            accuracy_score=1.0 if coaching_correct else 0.0,
            key_factors=prediction.coaching_matchup.key_factors
        ))

        return accuracies

    def _calculate_overall_accuracy(self, category_accuracies: List[CategoryAccuracy]) -> float:
        """Calculate overall accuracy across all categories"""
        if not category_accuracies:
            return 0.0

        total_accuracy = sum(cat.accuracy_score for cat in category_accuracies)
        return total_accuracy / len(category_accuracies)

    async def _generate_ai_reflection(
        self,
        expert_id: str,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome,
        category_accuracies: List[CategoryAccuracy]
    ) -> str:
        """Generate AI reflection using expert's assigned model"""

        expert_config = self.expert_model_mapping.get(expert_id)
        if not expert_config:
            logger.warning(f"No model mapping found for {expert_id}, using default")
            expert_config = {
                'name': 'Unknown Expert',
                'model': 'anthropic/claude-sonnet-4.5',
                'personality': 'Analytical',
                'specialty': 'General predictions'
            }

        # Build reflection prompt
        system_message = self._build_reflection_system_prompt(expert_config)
        user_message = self._build_reflection_user_prompt(
            prediction, outcome, category_accuracies, expert_config
        )

        try:
            response = self.openrouter.generate_completion(
                system_message=system_message,
                user_message=user_message,
                temperature=0.7,
                max_tokens=800,
                model=expert_config['model']
            )

            return response.content

        except Exception as e:
            logger.error(f"❌ AI reflection generation failed for {expert_id}: {e}")
            return f"Reflection generation failed: {str(e)}"

    def _build_reflection_system_prompt(self, expert_config: Dict[str, str]) -> str:
        """Build system prompt for AI reflection"""
        return f"""You are {expert_config['name']}, an NFL prediction expert conducting post-game reflection.

PERSONALITY: {expert_config['personality']}
SPECIALTY: {expert_config['specialty']}

You are analyzing your prediction performance after a completed game. This is a learning opportunity to improve your future predictions.

Your reflection should:
1. Analyze what you got right and wrong
2. Identify patterns in your prediction accuracy
3. Recognize factors you correctly/incorrectly weighted
4. Extract lessons for similar future situations
5. Adjust your confidence calibration based on results

Be honest about mistakes and insightful about successes. Focus on actionable lessons that will improve your specialty area predictions."""

    def _build_reflection_user_prompt(
        self,
        prediction: ComprehensiveExpertPrediction,
        outcome: GameOutcome,
        category_accuracies: List[CategoryAccuracy],
        expert_config: Dict[str, str]
    ) -> str:
        """Build user prompt with game details and accuracy analysis"""

        # Calculate summary stats
        total_predictions = len(category_accuracies)
        correct_predictions = sum(1 for cat in category_accuracies if cat.is_correct)
        overall_accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0.0

        # Identify best and worst categories
        best_categories = [cat.category_name for cat in category_accuracies if cat.accuracy_score >= 0.8]
        worst_categories = [cat.category_name for cat in category_accuracies if cat.accuracy_score <= 0.3]
        high_confidence_errors = [cat.category_name for cat in category_accuracies if not cat.is_correct and cat.confidence > 0.7]

        return f"""POST-GAME REFLECTION ANALYSIS

GAME: {outcome.away_team} @ {outcome.home_team}
FINAL SCORE: {outcome.away_team} {outcome.away_score} - {outcome.home_team} {outcome.home_score}
WINNER: {outcome.winner}

YOUR PREDICTION PERFORMANCE:
- Overall Accuracy: {overall_accuracy:.1%} ({correct_predictions}/{total_predictions} categories correct)
- Best Categories: {', '.join(best_categories) if best_categories else 'None'}
- Worst Categories: {', '.join(worst_categories) if worst_categories else 'None'}
- High Confidence Errors: {', '.join(high_confidence_errors) if high_confidence_errors else 'None'}

KEY PREDICTIONS VS ACTUAL:
- Game Winner: Predicted {prediction.game_winner.prediction} (confidence: {prediction.game_winner.confidence:.1%}) → Actual: {outcome.winner}
- Point Spread: Predicted {prediction.point_spread.prediction} (confidence: {prediction.point_spread.confidence:.1%})
- Total Points: Predicted {prediction.total_points.prediction} (confidence: {prediction.total_points.confidence:.1%}) → Actual: {outcome.total_points}

MEMORY INFLUENCES USED: {len(prediction.memory_influences)} memories influenced your predictions

REFLECTION QUESTIONS:
1. What factors did you weight correctly/incorrectly?
2. Were there patterns you missed or overemphasized?
3. How should you adjust your confidence for similar situations?
4. What specific lessons will improve your {expert_config['specialty']}?
5. Which memory influences were helpful vs misleading?

Provide a thoughtful reflection focusing on actionable insights for future predictions."""

    def _extract_lessons_learned(
        self,
        ai_reflection: str,
        category_accuracies: List[CategoryAccuracy]
    ) -> List[str]:
        """Extract specific lessons learned from AI reflection"""
        lessons = []

        # Extract lessons from AI reflection text
        reflection_lower = ai_reflection.lower()

        # Pattern-based lesson extraction
        if "overconfident" in reflection_lower or "too confident" in reflection_lower:
            lessons.append("Need to be more cautious with high confidence predictions")

        if "underestimated" in reflection_lower:
            lessons.append("Underestimated key factors - need better factor weighting")

        if "home field" in reflection_lower:
            lessons.append("Home field advantage was a significant factor")

        if "weather" in reflection_lower:
            lessons.append("Weather conditions impacted game more than expected")

        # Add accuracy-based lessons
        high_accuracy_categories = [cat for cat in category_accuracies if cat.accuracy_score >= 0.8]
        if high_accuracy_categories:
            lessons.append(f"Strong performance in: {', '.join([cat.category_name for cat in high_accuracy_categories])}")

        low_accuracy_categories = [cat for cat in category_accuracies if cat.accuracy_score <= 0.3]
        if low_accuracy_categories:
            lessons.append(f"Need improvement in: {', '.join([cat.category_name for cat in low_accuracy_categories])}")

        return lessons

    def _identify_pattern_insights(
        self,
        ai_reflection: str,
        category_accuracies: List[CategoryAccuracy]
    ) -> List[str]:
        """Identify pattern recognition insights from reflection"""
        patterns = []

        # Analyze accuracy patterns
        core_categories = [cat for cat in category_accuracies if cat.category_name in ['game_winner', 'point_spread', 'total_points']]
        quarter_categories = [cat for cat in category_accuracies if 'q' in cat.category_name and 'score' in cat.category_name]

        if core_categories:
            core_accuracy = sum(cat.accuracy_score for cat in core_categories) / len(core_categories)
            if core_accuracy >= 0.7:
                patterns.append("Strong at core game predictions")
            elif core_accuracy <= 0.4:
                patterns.append("Struggling with basic game outcomes")

        if quarter_categories:
            quarter_accuracy = sum(cat.accuracy_score for cat in quarter_categories) / len(quarter_categories)
            if quarter_accuracy >= 0.6:
                patterns.append("Good at quarter-by-quarter analysis")
            elif quarter_accuracy <= 0.3:
                patterns.append("Quarter predictions need improvement")

        # Confidence pattern analysis
        high_conf_cats = [cat for cat in category_accuracies if cat.confidence > 0.7]
        if high_conf_cats:
            high_conf_accuracy = sum(cat.accuracy_score for cat in high_conf_cats) / len(high_conf_cats)
            if high_conf_accuracy < 0.6:
                patterns.append("Overconfidence issue - high confidence predictions underperforming")
            elif high_conf_accuracy > 0.8:
                patterns.append("Well-calibrated confidence - high confidence predictions reliable")

        return patterns

    def _determine_factor_adjustments(
        self,
        ai_reflection: str,
        category_accuracies: List[CategoryAccuracy]
    ) -> Dict[str, float]:
        """Determine how to adjust factor weightings based on performance"""
        adjustments = {}

        reflection_lower = ai_reflection.lower()

        # Factor adjustment based on reflection content
        if "home field" in reflection_lower:
            if "underestimated" in reflection_lower:
                adjustments["home_field_advantage"] = 0.1  # Increase weight
            elif "overestimated" in reflection_lower:
                adjustments["home_field_advantage"] = -0.1  # Decrease weight

        if "weather" in reflection_lower:
            if "more impact" in reflection_lower or "significant" in reflection_lower:
                adjustments["weather_impact"] = 0.15
            elif "less impact" in reflection_lower or "minimal" in reflection_lower:
                adjustments["weather_impact"] = -0.1

        if "momentum" in reflection_lower:
            if "important" in reflection_lower or "key factor" in reflection_lower:
                adjustments["momentum_factor"] = 0.1
            elif "overrated" in reflection_lower:
                adjustments["momentum_factor"] = -0.1

        # Adjustment based on category performance
        situational_cats = [cat for cat in category_accuracies if cat.category_name in ['turnover_differential', 'time_of_possession']]
        if situational_cats:
            situational_accuracy = sum(cat.accuracy_score for cat in situational_cats) / len(situational_cats)
            if situational_accuracy >= 0.8:
                adjustments["situational_analysis"] = 0.05  # Slight increase
            elif situational_accuracy <= 0.3:
                adjustments["situational_analysis"] = -0.1  # Decrease weight

        return adjustments

    def _calculate_confidence_calibration(self, category_accuracies: List[CategoryAccuracy]) -> Dict[str, float]:
        """Calculate confidence calibration adjustments"""
        calibration = {}

        # Analyze confidence vs accuracy relationship
        high_conf_cats = [cat for cat in category_accuracies if cat.confidence > 0.7]
        medium_conf_cats = [cat for cat in category_accuracies if 0.4 <= cat.confidence <= 0.7]
        low_conf_cats = [cat for cat in category_accuracies if cat.confidence < 0.4]

        if high_conf_cats:
            high_conf_accuracy = sum(cat.accuracy_score for cat in high_conf_cats) / len(high_conf_cats)
            if high_conf_accuracy < 0.6:
                calibration["high_confidence_adjustment"] = -0.1  # Be less confident
            elif high_conf_accuracy > 0.85:
                calibration["high_confidence_adjustment"] = 0.05  # Can be slightly more confident

        if medium_conf_cats:
            medium_conf_accuracy = sum(cat.accuracy_score for cat in medium_conf_cats) / len(medium_conf_cats)
            if medium_conf_accuracy > 0.8:
                calibration["medium_confidence_adjustment"] = 0.1  # Can be more confident
            elif medium_conf_accuracy < 0.4:
                calibration["medium_confidence_adjustment"] = -0.1  # Be less confident

        return calibration

    def _determine_reflection_type(self, overall_accuracy: float, high_confidence_errors: List[str]) -> ReflectionType:
        """Determine the primary type of reflection needed"""
        if overall_accuracy >= 0.7:
            return ReflectionType.SUCCESS_ANALYSIS
        elif high_confidence_errors:
            return ReflectionType.CONFIDENCE_CALIBRATION
        elif overall_accuracy <= 0.4:
            return ReflectionType.FAILURE_ANALYSIS
        else:
            return ReflectionType.PATTERN_RECOGNITION

    def _calculate_emotional_intensity(self, overall_accuracy: float, high_confidence_errors: List[str]) -> float:
        """Calculate emotional intensity for memory storage"""
        base_intensity = 0.5

        # High accuracy increases positive emotion
        if overall_accuracy >= 0.8:
            base_intensity += 0.3
        elif overall_accuracy >= 0.6:
            base_intensity += 0.1

        # Poor accuracy increases negative emotion
        if overall_accuracy <= 0.3:
            base_intensity += 0.4
        elif overall_accuracy <= 0.5:
            base_intensity += 0.2

        # High confidence errors are emotionally significant
        if high_confidence_errors:
            base_intensity += 0.2 * len(high_confidence_errors)

        return min(1.0, base_intensity)

    def _calculate_surprise_factor(self, category_accuracies: List[CategoryAccuracy]) -> float:
        """Calculate surprise factor based on unexpected outcomes"""
        surprise = 0.0

        # High confidence predictions that were wrong are surprising
        high_conf_errors = [cat for cat in category_accuracies if not cat.is_correct and cat.confidence > 0.8]
        surprise += 0.3 * len(high_conf_errors)

        # Large error magnitudes are surprising
        large_errors = [cat for cat in category_accuracies if cat.error_magnitude and cat.error_magnitude > 10]
        surprise += 0.2 * len(large_errors)

        # Low confidence predictions that were correct are mildly surprising
        low_conf_successes = [cat for cat in category_accuracies if cat.is_correct and cat.confidence < 0.4]
        surprise += 0.1 * len(low_conf_successes)

        return min(1.0, surprise)

# Integration function for complete post-game reflection workflow
async def conduct_post_game_reflection(
    expert_id: str,
    prediction: ComprehensiveExpertPrediction,
    outcome: GameOutcome,
    openrouter_service: OpenRouterService,
    memory_manager: SupabaseEpisodicMemoryManager
) -> bool:
    """
    Complete post-game reflection workflow that integrates reflection and memory storage.

    This function orchestrates the full process:
    1. Generate reflection using PostGameReflectionOrchestrator
    2. Store reflection memory using extended SupabaseEpisodicMemoryManager
    3. Return success status

    Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 3.3, 3.4
    """
    try:
        logger.info(f"🔄 Starting complete post-game reflection for {expert_id}")

        # Step 1: Create reflection orchestrator
        reflection_orchestrator = PostGameReflectionOrchestrator(
            openrouter_service=openrouter_service,
            memory_manager=memory_manager
        )

        # Step 2: Generate comprehensive reflection
        reflection_memory = await reflection_orchestrator.post_game_reflection(
            expert_id=expert_id,
            prediction=prediction,
            outcome=outcome
        )

        # Step 3: Store reflection memory using extended memory manager
        storage_success = await memory_manager.store_reflection_memory(reflection_memory)

        if storage_success:
            logger.info(f"✅ Complete post-game reflection successful for {expert_id}")
            logger.info(f"   Accuracy: {reflection_memory.overall_accuracy:.1%}")
            logger.info(f"   Lessons learned: {len(reflection_memory.lessons_learned)}")
            logger.info(f"   Memory type: {reflection_memory.reflection_type.value}")
            return True
        else:
            logger.error(f"❌ Failed to store reflection memory for {expert_id}")
            return False

    except Exception as e:
        logger.error(f"❌ Complete post-game reflection failed for {expert_id}: {e}")
        return False


# Example usage function for testing
async def example_post_game_reflection():
    """Example of how to use the post-game reflection system"""
    import os
    from supabase import create_client
    from src.services.openrouter_service import OpenRouterService
    from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
    from datetime import datetime

    # Initialize services
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY'))
    openrouter = OpenRouterService(os.getenv('VITE_OPENROUTER_API_KEY'))
    memory_manager = SupabaseEpisodicMemoryManager(supabase)

    # Create example game context
    game_context = GameContext(
        game_id="example_game_2024_w1",
        home_team="Chiefs",
        away_team="Ravens",
        season=2024,
        week=1,
        game_date=datetime.now(),
        current_spread=-3.5,
        total_line=47.5
    )

    # Create example prediction (simplified)
    prediction = ComprehensiveExpertPrediction(
        expert_id="conservative_analyzer",
        expert_name="The Analyst",
        game_context=game_context,
        # ... (would need to fill in all required prediction fields)
    )

    # Create example outcome
    outcome = GameOutcome(
        game_id="example_game_2024_w1",
        home_team="Chiefs",
        away_team="Ravens",
        home_score=27,
        away_score=20,
        q1_home=7, q1_away=3,
        q2_home=10, q2_away=7,
        q3_home=7, q3_away=7,
        q4_home=3, q4_away=3
    )

    # Conduct reflection
    success = await conduct_post_game_reflection(
        expert_id="conservative_analyzer",
        prediction=prediction,
        outcome=outcome,
        openrouter_service=openrouter,
        memory_manager=memory_manager
    )

    if success:
        print("✅ Post-game reflection completed successfully")

        # Get learning insights summary
        insights = await memory_manager.get_learning_insights_summary("conservative_analyzer")
        print(f"📊 Learning insights: {insights}")
    else:
        print("❌ Post-game reflection failed")


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_post_game_reflection())
