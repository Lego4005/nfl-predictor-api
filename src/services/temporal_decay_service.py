"""
Temporal Decay Service for Expert Memory Systems
vice implements personality-specific temporal decay for expert memories,
ensuring each expert weights historical information according to the stability
of the factors they analyze.
"""

import math
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ExpertType(Enum):
    CONSERVATIVE_ANALYZER = "conservative_analyzer"
    AGGRESSIVE_GAMBLER = "aggressive_gambler"
    WEATHER_SPECIALIST = "weather_specialist"
    INJURY_TRACKER = "injury_tracker"
    MARKET_READER = "market_reader"
    STATISTICAL_PURIST = "statistical_purist"
    CONTRARIAN_EXPERT = "contrarian_expert"
    HOME_FIELD_GURU = "home_field_guru"
    DIVISIONAL_SPECIALIST = "divisional_specialist"
    PRIMETIME_ANALYST = "primetime_analyst"
    COACHING_EVALUATOR = "coaching_evaluator"
    MOMENTUM_TRACKER = "momentum_tracker"
    UNDERDOG_HUNTER = "underdog_hunter"
    TOTAL_PREDICTOR = "total_predictor"
    SITUATIONAL_EXPERT = "situational_expert"


@dataclass
class TemporalDecayConfig:
    """Configuration for temporal decay parameters"""
    expert_type: ExpertType
    default_half_life: int  # days
    memory_category_half_lives: Dict[str, int]
    similarity_weight: float = 0.70
    temporal_weight: float = 0.30
    base_learning_rate: float = 0.1


@dataclass
class MemoryScore:
    """Scored memory with temporal and similarity components"""
    memory_id: str
    similarity_score: float
    temporal_decay_score: float
    final_score: float
    days_old: int
    memory_category: Optional[str] = None


class TemporalDecayService:
    """
    Service for applying personality-specific temporal decay to expert memories.

    Each expert has different half-life parameters based on the stability of
    the factors they analyze, from momentum (45 days) to weather (730 days).
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.decay_configs = self._initialize_decay_configs()

    def _initialize_decay_configs(self) -> Dict[ExpertType, TemporalDecayConfig]:
        """Initialize temporal decay configurations for all expert types"""

        configs = {}

        # 1. Conservative Analyzer - Values proven, stable patterns
        configs[ExpertType.CONSERVATIVE_ANALYZER] = TemporalDecayConfig(
            expert_type=ExpertType.CONSERVATIVE_ANALYZER,
            default_half_life=450,
            similarity_weight=0.80,  # Heavily weights pattern similarity
            temporal_weight=0.20,    # Less concerned with recency
            memory_category_half_lives={
                'team_quality_assessments': 540,
                'historical_matchup_patterns': 450,
                'coaching_tendencies': 270,
                'fundamental_analysis': 450,
                'proven_patterns': 540
            }
        )

        # 2. Aggressive Gambler - Chases emerging opportunities
        configs[ExpertType.AGGRESSIVE_GAMBLER] = TemporalDecayConfig(
            expert_type=ExpertType.AGGRESSIVE_GAMBLER,
            default_half_life=120,
            similarity_weight=0.60,  # Moderate similarity weight
            temporal_weight=0.40,    # High recency weight - what's hot now matters
            memory_category_half_lives={
                'recent_upset_patterns': 90,
                'emotional_narrative_memories': 120,
                'value_betting_opportunities': 150,
                'contrarian_plays': 120,
                'upset_potential': 90
            }
        )

        # 3. Weather Specialist - Physics doesn't change
        configs[ExpertType.WEATHER_SPECIALIST] = TemporalDecayConfig(
            expert_type=ExpertType.WEATHER_SPECIALIST,
            default_half_life=730,
            similarity_weight=0.85,  # Highest similarity weight - physics is consistent
            temporal_weight=0.15,    # Lowest recency weight - weather patterns persist
            memory_category_half_lives={
                'weather_impact_patterns': 900,
                'stadium_specific_conditions': 730,
                'team_adaptation_to_weather': 365,
                'environmental_factors': 730,
                'climate_patterns': 900
            }
        )

        # 4. Injury Tracker - Player and context specific
        configs[ExpertType.INJURY_TRACKER] = TemporalDecayConfig(
            expert_type=ExpertType.INJURY_TRACKER,
            default_half_life=180,
            memory_category_half_lives={
                'position_specific_injury_impacts': 270,
                'individual_player_injury_patterns': 180,
                'depth_chart_quality_assessments': 120,
                'injury_recovery_patterns': 180,
                'backup_performance': 120
            }
        )

        # 5. Market Reader - Markets evolve rapidly
        configs[ExpertType.MARKET_READER] = TemporalDecayConfig(
            expert_type=ExpertType.MARKET_READER,
            default_half_life=90,
            similarity_weight=0.50,  # Balanced but favoring recency
            temporal_weight=0.50,    # Equal weight - current market dynamics crucial
            memory_category_half_lives={
                'line_movement_patterns': 60,
                'sharp_vs_square_indicators': 90,
                'public_betting_tendencies': 120,
                'market_inefficiencies': 75,
                'betting_market_evolution': 60
            }
        )

        # 6. Statistical Purist - Mathematical relationships persist
        configs[ExpertType.STATISTICAL_PURIST] = TemporalDecayConfig(
            expert_type=ExpertType.STATISTICAL_PURIST,
            default_half_life=365,
            memory_category_half_lives={
                'metric_to_outcome_correlations': 450,
                'team_performance_metrics': 270,
                'algorithm_validation_results': 365,
                'statistical_relationships': 450,
                'advanced_analytics': 365
            }
        )

        # 7. Contrarian Expert - Public biases shift moderately
        configs[ExpertType.CONTRARIAN_EXPERT] = TemporalDecayConfig(
            expert_type=ExpertType.CONTRARIAN_EXPERT,
            default_half_life=150,
            memory_category_half_lives={
                'public_overreaction_patterns': 120,
                'media_narrative_impacts': 150,
                'contrarian_success_rates': 180,
                'fade_opportunities': 150,
                'public_bias_patterns': 120
            }
        )

        # 8. Home Field Guru - Venue advantages very stable
        configs[ExpertType.HOME_FIELD_GURU] = TemporalDecayConfig(
            expert_type=ExpertType.HOME_FIELD_GURU,
            default_half_life=540,
            memory_category_half_lives={
                'venue_specific_advantages': 730,
                'team_specific_home_performance': 365,
                'travel_impact_patterns': 540,
                'stadium_factors': 730,
                'geographic_advantages': 540
            }
        )

        # 9. Divisional Specialist - Familiarity has persistence
        configs[ExpertType.DIVISIONAL_SPECIALIST] = TemporalDecayConfig(
            expert_type=ExpertType.DIVISIONAL_SPECIALIST,
            default_half_life=270,
            memory_category_half_lives={
                'coaching_matchup_history': 180,
                'divisional_rivalry_patterns': 365,
                'head_to_head_results': 270,
                'familiarity_effects': 270,
                'division_dynamics': 365
            }
        )

        # 10. Primetime Analyst - Performance under pressure somewhat stable
        configs[ExpertType.PRIMETIME_ANALYST] = TemporalDecayConfig(
            expert_type=ExpertType.PRIMETIME_ANALYST,
            default_half_life=365,
            memory_category_half_lives={
                'franchise_primetime_tendencies': 540,
                'individual_player_primetime_performance': 270,
                'coaching_primetime_records': 365,
                'pressure_performance': 365,
                'spotlight_game_patterns': 365
            }
        )

        # 11. Coaching Evaluator - Coaching evolves moderately
        configs[ExpertType.COACHING_EVALUATOR] = TemporalDecayConfig(
            expert_type=ExpertType.COACHING_EVALUATOR,
            default_half_life=240,
            memory_category_half_lives={
                'head_coach_decision_making': 365,
                'coordinator_tendencies': 180,
                'coach_vs_coach_matchups': 240,
                'strategic_adjustments': 240,
                'game_planning': 180
            }
        )

        # 12. Momentum Tracker - Shortest memory, momentum is short-term
        configs[ExpertType.MOMENTUM_TRACKER] = TemporalDecayConfig(
            expert_type=ExpertType.MOMENTUM_TRACKER,
            default_half_life=45,
            similarity_weight=0.40,  # Low similarity weight
            temporal_weight=0.60,    # Maximum recency weight - only recent matters
            memory_category_half_lives={
                'win_loss_streak_patterns': 30,
                'confidence_psychology_indicators': 45,
                'recent_performance_trends': 60,
                'momentum_shifts': 30,
                'hot_cold_streaks': 45
            }
        )

        # 13. Underdog Hunter - Balance pattern exploitation and adaptation
        configs[ExpertType.UNDERDOG_HUNTER] = TemporalDecayConfig(
            expert_type=ExpertType.UNDERDOG_HUNTER,
            default_half_life=180,
            memory_category_half_lives={
                'underdog_coverage_patterns': 270,
                'point_spread_value_analysis': 150,
                'underdog_situation_identification': 180,
                'value_opportunities': 150,
                'dog_scenarios': 180
            }
        )

        # 14. Total Predictor - Scoring relationships fairly stable
        configs[ExpertType.TOTAL_PREDICTOR] = TemporalDecayConfig(
            expert_type=ExpertType.TOTAL_PREDICTOR,
            default_half_life=300,
            memory_category_half_lives={
                'pace_to_scoring_relationships': 450,
                'league_scoring_trends': 270,
                'team_specific_totals_patterns': 300,
                'over_under_analysis': 300,
                'scoring_environment': 270
            }
        )

        # 15. Situational Expert - Motivation patterns moderately stable
        configs[ExpertType.SITUATIONAL_EXPERT] = TemporalDecayConfig(
            expert_type=ExpertType.SITUATIONAL_EXPERT,
            default_half_life=210,
            memory_category_half_lives={
                'motivation_impact_patterns': 300,
                'team_specific_situational_response': 180,
                'playoff_scenario_impacts': 210,
                'must_win_games': 210,
                'pressure_situations': 240
            }
        )

        return configs

    def calculate_temporal_decay_score(
        self,
        expert_type: ExpertType,
        memory_age_days: int,
        memory_category: Optional[str] = None
    ) -> float:
        """
        Calculate temporal decay score for a memory.

        Args:
            expert_type: Type of expert analyzing the memory
            memory_age_days: Age of memory in days
            memory_category: Specific category of memory (optional)

        Returns:
            float: Decay score between 0 and 1 (1 = fresh, 0.5 = one half-life old)
        """
        config = self.decay_configs.get(expert_type)
        if not config:
            self.logger.warning(f"No decay config found for expert type: {expert_type}")
            return 0.5  # Default moderate decay

        # Use category-specific half-life if available
        if memory_category and memory_category in config.memory_category_half_lives:
            half_life = config.memory_category_half_lives[memory_category]
        else:
            half_life = config.default_half_life

        # Calculate exponential decay: 0.5^(age / half_life)
        decay_score = math.pow(0.5, memory_age_days / half_life)

        return decay_score

    def calculate_combined_memory_score(
        self,
        expert_type: ExpertType,
        similarity_score: float,
        memory_age_days: int,
        memory_category: Optional[str] = None
    ) -> MemoryScore:
        """
        Calculate combined memory score using similarity and temporal decay.

        Args:
            expert_type: Type of expert analyzing the memory
            similarity_score: Similarity score (0-1)
            memory_age_days: Age of memory in days
            memory_category: Specific category of memory (optional)

        Returns:
            MemoryScore: Complete scoring breakdown
        """
        config = self.decay_configs.get(expert_type, self.decay_configs[ExpertType.CONSERVATIVE_ANALYZER])

        # Calculate temporal decay
        temporal_decay_score = self.calculate_temporal_decay_score(
            expert_type, memory_age_days, memory_category
        )

        # Combine similarity and temporal scores
        final_score = (
            config.similarity_weight * similarity_score +
            config.temporal_weight * temporal_decay_score
        )

        return MemoryScore(
            memory_id="",  # To be filled by caller
            similarity_score=similarity_score,
            temporal_decay_score=temporal_decay_score,
            final_score=final_score,
            days_old=memory_age_days,
            memory_category=memory_category
        )

    def calculate_adjusted_learning_rate(
        self,
        expert_type: ExpertType,
        days_since_outcome: int,
        memory_category: Optional[str] = None
    ) -> float:
        """
        Calculate adjusted learning rate based on temporal decay.

        Recent outcomes should influence belief updates more than old outcomes.

        Args:
            expert_type: Type of expert
            days_since_outcome: Days since the prediction outcome
            memory_category: Category of memory being updated

        Returns:
            float: Adjusted learning rate (0-1)
        """
        config = self.decay_configs.get(expert_type)
        if not config:
            return 0.05  # Default low learning rate

        # Calculate temporal decay for learning
        temporal_decay = self.calculate_temporal_decay_score(
            expert_type, days_since_outcome, memory_category
        )

        # Scale base learning rate by temporal decay
        adjusted_rate = config.base_learning_rate * temporal_decay

        return adjusted_rate

    def rank_memories_by_relevance(
        self,
        expert_type: ExpertType,
        memories: List[Dict[str, Any]],
        current_date: datetime
    ) -> List[MemoryScore]:
        """
        Rank memories by combined similarity and temporal relevance.

        Args:
            expert_type: Type of expert
            memories: List of memory dictionaries with similarity_score and created_at
            current_date: Current date for age calculation

        Returns:
            List[MemoryScore]: Ranked memories with scores
        """
        scored_memories = []

        for memory in memories:
            # Calculate memory age
            memory_date = memory.get('created_at')
            if isinstance(memory_date, str):
                memory_date = datetime.fromisoformat(memory_date.replace('Z', '+00:00'))

            age_days = (current_date - memory_date).days

            # Get similarity score
            similarity_score = memory.get('similarity_score', memory.get('similarity', 0.0))

            # Get memory category
            memory_category = memory.get('memory_category', memory.get('category'))

            # Calculate combined score
            memory_score = self.calculate_combined_memory_score(
                expert_type=expert_type,
                similarity_score=similarity_score,
                memory_age_days=age_days,
                memory_category=memory_category
            )

            # Set memory ID
            memory_score.memory_id = memory.get('id', memory.get('memory_id', ''))

            scored_memories.append(memory_score)

        # Sort by final score (highest first)
        scored_memories.sort(key=lambda x: x.final_score, reverse=True)

        return scored_memories

    def get_expert_decay_summary(self, expert_type: ExpertType) -> Dict[str, Any]:
        """Get summary of decay configuration for an expert"""
        config = self.decay_configs.get(expert_type)
        if not config:
            return {}

        return {
            'expert_type': expert_type.value,
            'default_half_life_days': config.default_half_life,
            'memory_category_half_lives': config.memory_category_half_lives,
            'similarity_weight': config.similarity_weight,
            'temporal_weight': config.temporal_weight,
            'base_learning_rate': config.base_learning_rate,
            'decay_speed': self._categorize_decay_speed(config.default_half_life)
        }

    def _categorize_decay_speed(self, half_life_days: int) -> str:
        """Categorize decay speed based on half-life"""
        if half_life_days <= 60:
            return "Extremely Fast"
        elif half_life_days <= 120:
            return "Very Fast"
        elif half_life_days <= 180:
            return "Fast"
        elif half_life_days <= 240:
            return "Moderately Fast"
        elif half_life_days <= 300:
            return "Moderate"
        elif half_life_days <= 400:
            return "Moderate-Slow"
        elif half_life_days <= 500:
            return "Slow"
        elif half_life_days <= 600:
            return "Very Slow"
        else:
            return "Extremely Slow"

    def optimize_half_life_for_expert(
        self,
        expert_type: ExpertType,
        performance_data: List[Dict[str, Any]],
        test_half_lives: List[int] = None
    ) -> int:
        """
        Optimize half-life parameter for an expert based on performance data.

        This allows the orchestrator to tune temporal decay parameters
        based on actual prediction accuracy.

        Args:
            expert_type: Type of expert to optimize
            performance_data: Historical performance data
            test_half_lives: List of half-lives to test (optional)

        Returns:
            int: Optimal half-life in days
        """
        if test_half_lives is None:
            current_half_life = self.decay_configs[expert_type].default_half_life
            test_half_lives = [
                int(current_half_life * 0.5),
                int(current_half_life * 0.75),
                current_half_life,
                int(current_half_life * 1.25),
                int(current_half_life * 1.5)
            ]

        best_half_life = self.decay_configs[expert_type].default_half_life
        best_accuracy = 0.0

        for test_half_life in test_half_lives:
            # Simulate performance with this half-life
            accuracy = self._simulate_performance_with_half_life(
                expert_type, performance_data, test_half_life
            )

            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_half_life = test_half_life

        self.logger.info(f"Optimized half-life for {expert_type.value}: {best_half_life} days (accuracy: {best_accuracy:.3f})")

        return best_half_life

    def _simulate_performance_with_half_life(
        self,
        expert_type: ExpertType,
        performance_data: List[Dict[str, Any]],
        test_half_life: int
    ) -> float:
        """Simulate expert performance with a specific half-life parameter"""
        # This is a simplified simulation - in practice, you'd run the full
        # memory retrieval and prediction pipeline with the test half-life

        correct_predictions = 0
        total_predictions = len(performance_data)

        for prediction in performance_data:
            # Calculate what the temporal weighting would have been
            prediction_date = prediction.get('prediction_date')
            memory_dates = prediction.get('memory_dates', [])

            # Simulate memory weighting with test half-life
            weighted_accuracy = self._calculate_weighted_memory_accuracy(
                prediction_date, memory_dates, test_half_life
            )

            # Simple heuristic: higher weighted accuracy = more likely correct
            if weighted_accuracy > 0.6:  # Threshold for "good" memory support
                if prediction.get('was_correct', False):
                    correct_predictions += 1

        return correct_predictions / total_predictions if total_predictions > 0 else 0.0

    def _calculate_weighted_memory_accuracy(
        self,
        prediction_date: datetime,
        memory_dates: List[datetime],
        half_life: int
    ) -> float:
        """Calculate weighted accuracy of supporting memories"""
        if not memory_dates:
            return 0.5  # Neutral

        total_weight = 0.0
        weighted_accuracy_sum = 0.0

        for memory_date in memory_dates:
            age_days = (prediction_date - memory_date).days
            weight = math.pow(0.5, age_days / half_life)

            # Assume memories have some baseline accuracy
            memory_accuracy = 0.65  # Placeholder - would use actual memory accuracy

            total_weight += weight
            weighted_accuracy_sum += weight * memory_accuracy

        return weighted_accuracy_sum / total_weight if total_weight > 0 else 0.5
