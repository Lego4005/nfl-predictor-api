#!/usr/bin/env python3
"""
Graceful Degradation System

Implements partial predineration and graceful degradation
when some prediction categories fail.

Requirements: 1.5, 2.6, 10.5
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from .comprehensive_expert_predictions import (
    ComprehensiveExpertPrediction, GameContext, PredictionWithConfidence,
    QuarterPrediction, PlayerPropPrediction, MemoryInfluence
)

logger = logging.getLogger(__name__)


class PredictionPriority(Enum):
    """Priority levels for prediction categories"""
    CRITICAL = "critical"      # Must have for basic functionality
    HIGH = "high"             # Important for comprehensive analysis
    MEDIUM = "medium"         # Nice to have for complete picture
    LOW = "low"              # Optional enhancements


@dataclass
class PredictionCategoryInfo:
    """Information about a prediction category"""
    name: str
    priority: PredictionPriority
    dependencies: List[str] = field(default_factory=list)
    fallback_available: bool = True
    description: str = ""


@dataclass
class DegradationResult:
    """Result of graceful degradation process"""
    successful_categories: Set[str]
    failed_categories: Set[str]
    degraded_categories: Set[str]
    fallback_categories: Set[str]
    overall_success_rate: float
    degradation_level: str
    warnings: List[str] = field(default_factory=list)


class PredictionCategoryManager:
    """Manages prediction categories and their priorities"""

    def __init__(self):
        self.categories = self._initialize_categories()
        logger.info("✅ Prediction Category Manager initialized")

    def _initialize_categories(self) -> Dict[str, PredictionCategoryInfo]:
        """Initialize prediction categories with priorities and dependencies"""
        categories = {}

        # Critical predictions - must have for basic functionality
        categories['game_winner'] = PredictionCategoryInfo(
            name='game_winner',
            priority=PredictionPriority.CRITICAL,
            description='Game winner prediction'
        )

        categories['point_spread'] = PredictionCategoryInfo(
            name='point_spread',
            priority=PredictionPriority.CRITICAL,
            description='Point spread prediction'
        )

        categories['total_points'] = PredictionCategoryInfo(
            name='total_points',
            priority=PredictionPriority.CRITICAL,
            description='Total points prediction'
        )

        # High priority predictions
        categories['exact_score'] = PredictionCategoryInfo(
            name='exact_score',
            priority=PredictionPriority.HIGH,
            dependencies=['game_winner', 'total_points'],
            description='Exact score prediction'
        )

        categories['margin_of_victory'] = PredictionCategoryInfo(
            name='margin_of_victory',
            priority=PredictionPriority.HIGH,
            dependencies=['game_winner'],
            description='Margin of victory prediction'
        )

        categories['moneyline'] = PredictionCategoryInfo(
            name='moneyline',
            priority=PredictionPriority.HIGH,
            dependencies=['game_winner'],
            description='Moneyline value assessment'
        )

        # Quarter predictions - medium priority
        for quarter in ['q1_score', 'q2_score', 'q3_score', 'q4_score']:
            categories[quarter] = PredictionCategoryInfo(
                name=quarter,
                priority=PredictionPriority.MEDIUM,
                dependencies=['total_points'],
                description=f'Quarter {quarter[-1]} score prediction'
            )

        categories['first_half_winner'] = PredictionCategoryInfo(
            name='first_half_winner',
            priority=PredictionPriority.MEDIUM,
            dependencies=['q1_score', 'q2_score'],
            description='First half winner prediction'
        )

        categories['highest_scoring_quarter'] = PredictionCategoryInfo(
            name='highest_scoring_quarter',
            priority=PredictionPriority.MEDIUM,
            dependencies=['q1_score', 'q2_score', 'q3_score', 'q4_score'],
            description='Highest scoring quarter prediction'
        )

        # Situational predictions - medium priority
        situational_categories = [
            'turnover_differential', 'red_zone_efficiency', 'third_down_conversion',
            'time_of_possession', 'sacks', 'penalties'
        ]

        for category in situational_categories:
            categories[category] = PredictionCategoryInfo(
                name=category,
                priority=PredictionPriority.MEDIUM,
                description=f'{category.replace("_", " ").title()} prediction'
            )

        # Environmental/advanced predictions - low priority
        advanced_categories = [
            'weather_impact', 'injury_impact', 'momentum_analysis',
            'special_teams', 'coaching_matchup'
        ]

        for category in advanced_categories:
            categories[category] = PredictionCategoryInfo(
                name=category,
                priority=PredictionPriority.LOW,
                description=f'{category.replace("_", " ").title()} analysis'
            )

        # Player props - low priority (many categories)
        player_prop_categories = [
            'qb_passing_yards', 'qb_touchdowns', 'qb_completions', 'qb_interceptions',
            'rb_rushing_yards', 'rb_attempts', 'rb_touchdowns',
            'wr_receiving_yards', 'wr_receptions', 'wr_touchdowns'
        ]

        for category in player_prop_categories:
            categories[category] = PredictionCategoryInfo(
                name=category,
                priority=PredictionPriority.LOW,
                fallback_available=False,  # Player props are harder to fallback
                description=f'{category.replace("_", " ").title()} prediction'
            )

        return categories

    def get_categories_by_priority(self, priority: PredictionPriority) -> List[str]:
        """Get all categories with the specified priority"""
        return [name for name, info in self.categories.items() if info.priority == priority]

    def get_critical_categories(self) -> List[str]:
        """Get all critical prediction categories"""
        return self.get_categories_by_priority(PredictionPriority.CRITICAL)

    def can_satisfy_dependencies(self, category_name: str, available_categories: Set[str]) -> bool:
        """Check if dependencies for a category are satisfied"""
        if category_name not in self.categories:
            return False

        dependencies = self.categories[category_name].dependencies
        return all(dep in available_categories for dep in dependencies)


class GracefulDegradationManager:
    """
    Manages graceful degradation of prediction generation.

    When some prediction categories fail, this system ensures that
    the most important predictions are still generated and the system
    continues to operate with reduced functionality.
    """

    def __init__(self):
        self.category_manager = PredictionCategoryManager()
        self.degradation_history: List[DegradationResult] = []

        logger.info("✅ Graceful Degradation Manager initialized")

    async def create_partial_prediction(
        self,
        expert_id: str,
        expert_name: str,
        game_context: GameContext,
        successful_predictions: Dict[str, Any],
        failed_categories: Set[str],
        memory_influences: List[MemoryInfluence] = None
    ) -> ComprehensiveExpertPrediction:
        """
        Create a comprehensive prediction with partial data and fallbacks.

        Args:
            expert_id: Expert identifier
            expert_name: Expert name
            game_context: Game context
            successful_predictions: Successfully generated predictions
            failed_categories: Categories that failed to generate
            memory_influences: Memory influences (optional)

        Returns:
            ComprehensiveExpertPrediction with available data and fallbacks
        """
        if memory_influences is None:
            memory_influences = []

        logger.info(f"🔧 Creating partial prediction for {expert_name}: "
                   f"{len(successful_predictions)} successful, {len(failed_categories)} failed")

        # Determine degradation level
        degradation_result = self._assess_degradation_level(successful_predictions, failed_categories)

        # Generate fallbacks for critical missing categories
        fallback_predictions = await self._generate_fallback_predictions(
            failed_categories, successful_predictions, game_context
        )

        # Combine successful and fallback predictions
        all_predictions = {**successful_predictions, **fallback_predictions}

        # Create prediction components with fallbacks
        prediction_components = await self._create_prediction_components(
            all_predictions, failed_categories, game_context
        )

        # Calculate overall confidence (reduced for partial predictions)
        overall_confidence = self._calculate_degraded_confidence(
            successful_predictions, failed_categories, degradation_result
        )

        # Generate reasoning with degradation explanation
        reasoning = self._generate_degraded_reasoning(
            expert_name, successful_predictions, failed_categories, degradation_result
        )

        # Create comprehensive prediction
        prediction = ComprehensiveExpertPrediction(
            expert_id=expert_id,
            expert_name=expert_name,
            game_context=game_context,

            # Core predictions (with fallbacks)
            game_winner=prediction_components['game_winner'],
            point_spread=prediction_components['point_spread'],
            total_points=prediction_components['total_points'],
            moneyline=prediction_components['moneyline'],
            exact_score=prediction_components['exact_score'],
            margin_of_victory=prediction_components['margin_of_victory'],

            # Quarter predictions
            q1_score=prediction_components['q1_score'],
            q2_score=prediction_components['q2_score'],
            q3_score=prediction_components['q3_score'],
            q4_score=prediction_components['q4_score'],
            first_half_winner=prediction_components['first_half_winner'],
            highest_scoring_quarter=prediction_components['highest_scoring_quarter'],

            # Player props (may be empty lists)
            qb_passing_yards=prediction_components.get('qb_passing_yards', []),
            qb_touchdowns=prediction_components.get('qb_touchdowns', []),
            qb_completions=prediction_components.get('qb_completions', []),
            qb_interceptions=prediction_components.get('qb_interceptions', []),
            rb_rushing_yards=prediction_components.get('rb_rushing_yards', []),
            rb_attempts=prediction_components.get('rb_attempts', []),
            rb_touchdowns=prediction_components.get('rb_touchdowns', []),
            wr_receiving_yards=prediction_components.get('wr_receiving_yards', []),
            wr_receptions=prediction_components.get('wr_receptions', []),
            wr_touchdowns=prediction_components.get('wr_touchdowns', []),

            # Situational predictions
            turnover_differential=prediction_components['turnover_differential'],
            red_zone_efficiency=prediction_components['red_zone_efficiency'],
            third_down_conversion=prediction_components['third_down_conversion'],
            time_of_possession=prediction_components['time_of_possession'],
            sacks=prediction_components['sacks'],
            penalties=prediction_components['penalties'],

            # Environmental/advanced
            weather_impact=prediction_components['weather_impact'],
            injury_impact=prediction_components['injury_impact'],
            momentum_analysis=prediction_components['momentum_analysis'],
            special_teams=prediction_components['special_teams'],
            coaching_matchup=prediction_components['coaching_matchup'],

            # Meta information
            confidence_overall=overall_confidence,
            reasoning=reasoning,
            key_factors=self._generate_degraded_key_factors(successful_predictions, failed_categories),
            prediction_timestamp=datetime.now(),
            memory_influences=memory_influences
        )

        # Store degradation result
        self.degradation_history.append(degradation_result)

        logger.info(f"✅ Partial prediction created for {expert_name} "
                   f"(degradation level: {degradation_result.degradation_level})")

        return prediction

    def _assess_degradation_level(
        self,
        successful_predictions: Dict[str, Any],
        failed_categories: Set[str]
    ) -> DegradationResult:
        """Assess the level of degradation based on failed categories"""
        successful_categories = set(successful_predictions.keys())
        total_categories = successful_categories | failed_categories

        # Check critical categories
        critical_categories = set(self.category_manager.get_critical_categories())
        critical_failures = failed_categories & critical_categories

        # Determine degradation level
        if not critical_failures:
            if len(failed_categories) == 0:
                degradation_level = "none"
            elif len(failed_categories) <= 3:
                degradation_level = "minimal"
            else:
                degradation_level = "moderate"
        else:
            if len(critical_failures) >= 2:
                degradation_level = "severe"
            else:
                degradation_level = "significant"

        success_rate = len(successful_categories) / len(total_categories) if total_categories else 0

        return DegradationResult(
            successful_categories=successful_categories,
            failed_categories=failed_categories,
            degraded_categories=set(),  # Will be populated with fallbacks
            fallback_categories=set(),
            overall_success_rate=success_rate,
            degradation_level=degradation_level,
            warnings=self._generate_degradation_warnings(critical_failures, failed_categories)
        )

    async def _generate_fallback_predictions(
        self,
        failed_categories: Set[str],
        successful_predictions: Dict[str, Any],
        game_context: GameContext
    ) -> Dict[str, Any]:
        """Generate intelligent fallback predictions for failed categories"""
        fallback_predictions = {}

        # Get category priorities for intelligent fallback generation
        critical_categories = set(self.category_manager.get_critical_categories())
        high_priority_categories = set(self.category_manager.get_categories_by_priority(PredictionPriority.HIGH))
        medium_priority_categories = set(self.category_manager.get_categories_by_priority(PredictionPriority.MEDIUM))

        # Generate fallbacks for ALL failed categories, not just critical ones
        for category in failed_categories:
            fallback_prediction = None

            # Critical categories - must have high-quality fallbacks
            if category in critical_categories:
                fallback_prediction = self._generate_critical_fallback(category, successful_predictions, game_context)

            # High priority categories - derive from successful predictions when possible
            elif category in high_priority_categories:
                fallback_prediction = self._generate_high_priority_fallback(category, successful_predictions, game_context)

            # Medium priority categories - use reasonable defaults
            elif category in medium_priority_categories:
                fallback_prediction = self._generate_medium_priority_fallback(category, successful_predictions, game_context)

            # Low priority categories - basic fallbacks
            else:
                fallback_prediction = self._generate_low_priority_fallback(category, successful_predictions, game_context)

            if fallback_prediction:
                fallback_predictions[category] = fallback_prediction

        logger.info(f"Generated {len(fallback_predictions)} intelligent fallbacks for failed categories")
        return fallback_predictions

    def _generate_critical_fallback(self, category: str, successful_predictions: Dict[str, Any], game_context: GameContext) -> Dict[str, Any]:
        """Generate high-quality fallbacks for critical categories"""
        if category == 'game_winner':
            # Use spread if available, otherwise home field advantage
            if 'point_spread' in successful_predictions:
                spread_pred = successful_predictions['point_spread']
                winner = 'home' if spread_pred.get('prediction', 0) < 0 else 'away'
                confidence = max(0.55, spread_pred.get('confidence', 0.5))
                reasoning = 'Derived from point spread prediction'
            else:
                winner = 'home'
                confidence = 0.52
                reasoning = 'Home field advantage fallback'

            return {
                'prediction': winner,
                'confidence': confidence,
                'reasoning': reasoning,
                'key_factors': ['Intelligent fallback', 'Home field advantage']
            }

        elif category == 'point_spread':
            # Use game winner if available, otherwise use game context
            if 'game_winner' in successful_predictions:
                winner_pred = successful_predictions['game_winner']
                spread = -3.0 if winner_pred.get('prediction') == 'home' else 3.0
                confidence = max(0.50, winner_pred.get('confidence', 0.5) - 0.05)
                reasoning = 'Derived from game winner prediction'
            else:
                spread = game_context.current_spread or -2.5
                confidence = 0.48
                reasoning = 'Using current betting line or home advantage'

            return {
                'prediction': spread,
                'confidence': confidence,
                'reasoning': reasoning,
                'key_factors': ['Intelligent fallback', 'Betting line analysis']
            }

        elif category == 'total_points':
            # Use game context total line if available
            total_line = game_context.total_line or 45.5
            return {
                'prediction': 'over' if total_line < 47 else 'under',
                'confidence': 0.50,
                'reasoning': f'Based on total line of {total_line}',
                'key_factors': ['Betting line analysis', 'NFL scoring average']
            }

        return None

    def _generate_high_priority_fallback(self, category: str, successful_predictions: Dict[str, Any], game_context: GameContext) -> Dict[str, Any]:
        """Generate fallbacks for high priority categories using successful predictions"""
        if category == 'exact_score':
            # Derive from game_winner and total_points if available
            winner = successful_predictions.get('game_winner', {}).get('prediction', 'home')
            total_line = game_context.total_line or 45.5

            if winner == 'home':
                home_score = int(total_line * 0.55)
                away_score = int(total_line * 0.45)
            else:
                home_score = int(total_line * 0.45)
                away_score = int(total_line * 0.55)

            return {
                'prediction': f'{home_score}-{away_score}',
                'confidence': 0.45,
                'reasoning': 'Derived from winner and total predictions',
                'key_factors': ['Intelligent derivation', 'Score distribution']
            }

        elif category == 'margin_of_victory':
            # Derive from point spread if available
            if 'point_spread' in successful_predictions:
                spread = abs(successful_predictions['point_spread'].get('prediction', 3))
                return {
                    'prediction': int(spread),
                    'confidence': 0.50,
                    'reasoning': 'Derived from point spread',
                    'key_factors': ['Spread analysis', 'Margin calculation']
                }
            else:
                return {
                    'prediction': 3,
                    'confidence': 0.45,
                    'reasoning': 'Average NFL margin of victory',
                    'key_factors': ['Historical average', 'NFL statistics']
                }

        elif category == 'moneyline':
            # Use game_winner if available
            if 'game_winner' in successful_predictions:
                winner_pred = successful_predictions['game_winner']
                return {
                    'prediction': winner_pred.get('prediction', 'home'),
                    'confidence': winner_pred.get('confidence', 0.5),
                    'reasoning': 'Same as game winner prediction',
                    'key_factors': ['Game winner analysis', 'Moneyline value']
                }

        return self._generate_medium_priority_fallback(category, successful_predictions, game_context)

    def _generate_medium_priority_fallback(self, category: str, successful_predictions: Dict[str, Any], game_context: GameContext) -> Dict[str, Any]:
        """Generate reasonable fallbacks for medium priority categories"""
        # Quarter predictions
        if category.startswith('q') and category.endswith('_score'):
            quarter_num = int(category[1])
            home_score = 6 + quarter_num
            away_score = 5 + quarter_num
            return {
                'home_score': home_score,
                'away_score': away_score,
                'total_points': home_score + away_score,  # Fix: Add total_points
                'confidence': 0.40,
                'reasoning': f'Quarter {quarter_num} scoring pattern fallback',
                'key_factors': ['Scoring patterns', 'Quarter analysis']
            }

        # Situational predictions
        situational_fallbacks = {
            'turnover_differential': {'prediction': 0, 'confidence': 0.45, 'reasoning': 'Even turnover expectation'},
            'red_zone_efficiency': {'prediction': 0.6, 'confidence': 0.42, 'reasoning': 'NFL average red zone efficiency'},
            'third_down_conversion': {'prediction': 0.4, 'confidence': 0.41, 'reasoning': 'NFL average third down rate'},
            'time_of_possession': {'prediction': 30.0, 'confidence': 0.43, 'reasoning': 'Even possession split'},
            'sacks': {'prediction': 3, 'confidence': 0.39, 'reasoning': 'Average sack total'},
            'penalties': {'prediction': 8, 'confidence': 0.38, 'reasoning': 'Average penalty count'},
            'first_half_winner': {'prediction': 'home', 'confidence': 0.53, 'reasoning': 'Home first half advantage'},
            'highest_scoring_quarter': {'prediction': 2, 'confidence': 0.48, 'reasoning': 'Second quarter typically highest'}
        }

        if category in situational_fallbacks:
            fallback = situational_fallbacks[category].copy()
            fallback['key_factors'] = ['NFL averages', 'Statistical fallback']
            return fallback

        return self._generate_low_priority_fallback(category, successful_predictions, game_context)

    def _generate_low_priority_fallback(self, category: str, successful_predictions: Dict[str, Any], game_context: GameContext) -> Dict[str, Any]:
        """Generate basic fallbacks for low priority categories"""
        # Environmental/advanced predictions
        environmental_fallbacks = {
            'weather_impact': {'prediction': 0.3, 'confidence': 0.35, 'reasoning': 'Minimal weather impact expected'},
            'injury_impact': {'prediction': 0.4, 'confidence': 0.36, 'reasoning': 'Moderate injury impact'},
            'momentum_analysis': {'prediction': 0.5, 'confidence': 0.37, 'reasoning': 'Neutral momentum'},
            'special_teams': {'prediction': 0.5, 'confidence': 0.38, 'reasoning': 'Even special teams'},
            'coaching_matchup': {'prediction': 0.5, 'confidence': 0.39, 'reasoning': 'Even coaching matchup'}
        }

        if category in environmental_fallbacks:
            fallback = environmental_fallbacks[category].copy()
            fallback['key_factors'] = ['Basic fallback', 'System default']
            return fallback

        # Player props - return empty list (will be handled in component creation)
        if any(prop in category for prop in ['qb_', 'rb_', 'wr_']):
            return {'prediction': [], 'confidence': 0.30, 'reasoning': 'Player props unavailable', 'key_factors': ['Data unavailable']}

        # Default fallback
        return {
            'prediction': 0.5,
            'confidence': 0.35,
            'reasoning': f'Default fallback for {category}',
            'key_factors': ['System default', 'Fallback prediction']
        }

    async def _create_prediction_components(
        self,
        all_predictions: Dict[str, Any],
        failed_categories: Set[str],
        game_context: GameContext
    ) -> Dict[str, Any]:
        """Create prediction components with proper types and fallbacks"""
        components = {}

        # Core predictions
        components['game_winner'] = self._create_prediction_with_confidence(
            all_predictions.get('game_winner'), 'home', 0.52, 'Fallback: Home field advantage'
        )

        components['point_spread'] = self._create_prediction_with_confidence(
            all_predictions.get('point_spread'), -2.5, 0.48, 'Fallback: Average home spread'
        )

        components['total_points'] = self._create_prediction_with_confidence(
            all_predictions.get('total_points'), 'over', 0.50, 'Fallback: Average scoring'
        )

        components['moneyline'] = self._create_prediction_with_confidence(
            all_predictions.get('moneyline'), 'home', 0.51, 'Fallback: Slight home value'
        )

        components['exact_score'] = self._create_prediction_with_confidence(
            all_predictions.get('exact_score'), '24-21', 0.45, 'Fallback: Average score'
        )

        components['margin_of_victory'] = self._create_prediction_with_confidence(
            all_predictions.get('margin_of_victory'), 3, 0.47, 'Fallback: Average margin'
        )

        # Quarter predictions
        for i, quarter in enumerate(['q1_score', 'q2_score', 'q3_score', 'q4_score'], 1):
            quarter_data = all_predictions.get(quarter)
            if quarter_data:
                components[quarter] = QuarterPrediction(
                    quarter=i,
                    home_score=quarter_data.get('home_score', 7),
                    away_score=quarter_data.get('away_score', 6),
                    total_points=quarter_data.get('total_points', 13),
                    confidence=quarter_data.get('confidence', 0.45)
                )
            else:
                # Fallback quarter prediction
                components[quarter] = QuarterPrediction(
                    quarter=i,
                    home_score=6,
                    away_score=5,
                    total_points=11,
                    confidence=0.40,
                    key_factors=['Fallback quarter prediction']
                )

        # Game segment predictions
        components['first_half_winner'] = self._create_prediction_with_confidence(
            all_predictions.get('first_half_winner'), 'home', 0.53, 'Fallback: Home first half'
        )

        components['highest_scoring_quarter'] = self._create_prediction_with_confidence(
            all_predictions.get('highest_scoring_quarter'), 2, 0.48, 'Fallback: Second quarter'
        )

        # Situational predictions with fallbacks
        situational_fallbacks = {
            'turnover_differential': (0, 0.40, 'Fallback: Even turnovers'),
            'red_zone_efficiency': (0.6, 0.42, 'Fallback: Average red zone'),
            'third_down_conversion': (0.4, 0.41, 'Fallback: Average third down'),
            'time_of_possession': (30.0, 0.43, 'Fallback: Even possession'),
            'sacks': (3, 0.39, 'Fallback: Average sacks'),
            'penalties': (8, 0.38, 'Fallback: Average penalties')
        }

        for category, (fallback_value, fallback_confidence, fallback_reasoning) in situational_fallbacks.items():
            components[category] = self._create_prediction_with_confidence(
                all_predictions.get(category), fallback_value, fallback_confidence, fallback_reasoning
            )

        # Environmental/advanced predictions
        environmental_fallbacks = {
            'weather_impact': (0.3, 0.35, 'Fallback: Minimal weather impact'),
            'injury_impact': (0.4, 0.36, 'Fallback: Moderate injury impact'),
            'momentum_analysis': (0.5, 0.37, 'Fallback: Neutral momentum'),
            'special_teams': (0.5, 0.38, 'Fallback: Even special teams'),
            'coaching_matchup': (0.5, 0.39, 'Fallback: Even coaching')
        }

        for category, (fallback_value, fallback_confidence, fallback_reasoning) in environmental_fallbacks.items():
            components[category] = self._create_prediction_with_confidence(
                all_predictions.get(category), fallback_value, fallback_confidence, fallback_reasoning
            )

        return components

    def _create_prediction_with_confidence(
        self,
        prediction_data: Optional[Dict[str, Any]],
        fallback_prediction: Any,
        fallback_confidence: float,
        fallback_reasoning: str
    ) -> PredictionWithConfidence:
        """Create a PredictionWithConfidence with fallback if needed"""
        if prediction_data:
            return PredictionWithConfidence(
                prediction=prediction_data.get('prediction', fallback_prediction),
                confidence=prediction_data.get('confidence', fallback_confidence),
                reasoning=prediction_data.get('reasoning', fallback_reasoning),
                key_factors=prediction_data.get('key_factors', [])
            )
        else:
            return PredictionWithConfidence(
                prediction=fallback_prediction,
                confidence=fallback_confidence,
                reasoning=fallback_reasoning,
                key_factors=['Fallback prediction - AI analysis failed']
            )

    def _calculate_degraded_confidence(
        self,
        successful_predictions: Dict[str, Any],
        failed_categories: Set[str],
        degradation_result: DegradationResult
    ) -> float:
        """Calculate overall confidence adjusted for degradation"""
        # Start with confidence from successful predictions
        if successful_predictions:
            successful_confidences = []
            for pred_data in successful_predictions.values():
                if isinstance(pred_data, dict) and 'confidence' in pred_data:
                    successful_confidences.append(pred_data['confidence'])

            if successful_confidences:
                base_confidence = sum(successful_confidences) / len(successful_confidences)
            else:
                base_confidence = 0.6
        else:
            base_confidence = 0.5  # No successful predictions

        # Check if critical categories are successful
        critical_categories = set(self.category_manager.get_critical_categories())
        successful_critical = len(critical_categories & set(successful_predictions.keys()))
        total_critical = len(critical_categories)

        # Bonus for having critical predictions
        if successful_critical > 0:
            critical_bonus = (successful_critical / total_critical) * 0.1
            base_confidence += critical_bonus

        # Reduce confidence based on degradation level, but less severely
        degradation_penalties = {
            'none': 0.0,
            'minimal': 0.02,    # Reduced from 0.05
            'moderate': 0.08,   # Reduced from 0.15
            'significant': 0.15, # Reduced from 0.25
            'severe': 0.25      # Reduced from 0.40
        }

        penalty = degradation_penalties.get(degradation_result.degradation_level, 0.10)

        # Don't penalize as much if we have good core predictions
        if successful_critical >= 2:  # Have at least 2 critical predictions
            penalty *= 0.5  # Reduce penalty by half

        adjusted_confidence = max(0.25, base_confidence - penalty)  # Higher minimum confidence

        return adjusted_confidence

    def _generate_degraded_reasoning(
        self,
        expert_name: str,
        successful_predictions: Dict[str, Any],
        failed_categories: Set[str],
        degradation_result: DegradationResult
    ) -> str:
        """Generate reasoning text explaining the degradation"""
        reasoning_parts = [
            f"Partial analysis by {expert_name} due to system limitations."
        ]

        if degradation_result.degradation_level != 'none':
            reasoning_parts.append(
                f"Degradation level: {degradation_result.degradation_level} "
                f"({len(failed_categories)} categories failed)."
            )

        reasoning_parts.append(
            f"Successfully generated {len(successful_predictions)} prediction categories "
            f"with fallbacks for critical missing data."
        )

        if degradation_result.warnings:
            reasoning_parts.append(f"Warnings: {'; '.join(degradation_result.warnings)}")

        return ' '.join(reasoning_parts)

    def _generate_degraded_key_factors(
        self,
        successful_predictions: Dict[str, Any],
        failed_categories: Set[str]
    ) -> List[str]:
        """Generate key factors list for degraded prediction"""
        factors = ['Partial prediction system']

        if len(successful_predictions) > 0:
            factors.append(f'{len(successful_predictions)} successful categories')

        if len(failed_categories) > 0:
            factors.append(f'{len(failed_categories)} failed categories')

        factors.append('Fallback predictions used')

        return factors

    def _generate_degradation_warnings(
        self,
        critical_failures: Set[str],
        failed_categories: Set[str]
    ) -> List[str]:
        """Generate warnings for degradation"""
        warnings = []

        if critical_failures:
            warnings.append(f"Critical prediction categories failed: {', '.join(critical_failures)}")

        if len(failed_categories) > 10:
            warnings.append(f"High number of failed categories: {len(failed_categories)}")

        return warnings

    def get_degradation_statistics(self) -> Dict[str, Any]:
        """Get degradation statistics"""
        if not self.degradation_history:
            return {'total_degradations': 0}

        total_degradations = len(self.degradation_history)
        degradation_levels = {}

        for result in self.degradation_history:
            level = result.degradation_level
            degradation_levels[level] = degradation_levels.get(level, 0) + 1

        avg_success_rate = sum(r.overall_success_rate for r in self.degradation_history) / total_degradations

        return {
            'total_degradations': total_degradations,
            'degradation_levels': degradation_levels,
            'average_success_rate': avg_success_rate,
            'recent_degradations': [
                {
                    'level': r.degradation_level,
                    'success_rate': r.overall_success_rate,
                    'failed_count': len(r.failed_categories)
                }
                for r in self.degradation_history[-10:]
            ]
        }


# Global degradation manager instance
_global_degradation_manager: Optional[GracefulDegradationManager] = None


def get_degradation_manager() -> GracefulDegradationManager:
    """Get the global graceful degradation manager instance"""
    global _global_degradation_manager
    if _global_degradation_manager is None:
        _global_degradation_manager = GracefulDegradationManager()
    return _global_degradation_manager
