"""
Advanced Temporal Orchestrator with Meta-Learning andaptation

This orchestrator has temporal awareness about its own decisions and implements
dynamic half-life adjustment based on seasonal data availability.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math

from services.temporal_decay_service import TemporalDecayService, ExpertType


@dataclass
class OrchestratorDecision:
    """Record of orchestrator's past model selection decisions"""
    decision_id: str
    expert_type: ExpertType
    decision_type: str  # 'model_switch', 'keep_production', 'continue_testing'
    decision_date: datetime
    context: Dict[str, Any]  # Performance data, confidence, etc.
    outcome_quality: Optional[float] = None  # How well did this decision work out?
    outcome_evaluated_date: Optional[datetime] = None


@dataclass
class SeasonalContext:
    """Context about current NFL season state"""
    current_week: int
    total_weeks_played: int
    games_this_season: int
    data_richness_score: float  # 0-1 scale of how much current season data we have
    recent_volatility: float    # How much recent performance differs from historical


@dataclass
class CouncilDeliberationContext:
    """Context for council deliberations including temporal perspectives"""
    expert_predictions: Dict[ExpertType, Dict[str, Any]]
    temporal_perspectives: Dict[ExpertType, Dict[str, Any]]
    consensus_confidence: float
    temporal_disagreement_score: float
    recommended_weighting_adjustments: Dict[ExpertType, float]


class AdvancedTemporalOrchestrator:
    """
    Orchestrator with temporal awareness of its own decisions and dynamic adaptation
    """

    def __init__(self, temporal_decay_service: TemporalDecayService):
        self.temporal_decay_service = temporal_decay_service
        self.logger = logging.getLogger(__name__)

        # Orchestrator's own memory of decisions
        self.decision_history: List[OrchestratorDecision] = []
        self.decision_half_life = 180  # Orchestrator remembers decisions for ~6 months

        # Seasonal adaptation parameters
        self.base_half_lives = {}  # Store original half-lives for each expert
        self._initialize_base_half_lives()

    def _initialize_base_half_lives(self):
        """Store base half-lives for seasonal adjustment calculations"""
        for expert_type in ExpertType:
            config = self.temporal_decay_service.decay_configs.get(expert_type)
            if config:
                self.base_half_lives[expert_type] = config.default_half_life

    async def make_model_selection_decision(
        self,
        expert_type: ExpertType,
        current_performance_data: Dict[str, Any],
        shadow_performance_data: Dict[str, List[Dict[str, Any]]],
        seasonal_context: SeasonalContext,
        current_date: datetime
    ) -> Dict[str, Any]:
        """
        Make model selection decision with temporal awareness of past decisions
        """

        # Get relevant past decisions for this expert type
        relevant_decisions = self._get_relevant_past_decisions(
            expert_type, current_date
        )

        # Calculate decision context with meta-learning
        decision_context = await self._calculate_decision_context(
            expert_type, current_performance_data, shadow_performance_data,
            relevant_decisions, seasonal_context
        )

        # Adjust temporal parameters based on seasonal context
        adjusted_config = self._get_seasonally_adjusted_config(
            expert_type, seasonal_context
        )

        # Make the decision
        decision = await self._make_informed_decision(
            expert_type, decision_context, adjusted_config
        )

        # Record the decision for future meta-learning
        await self._record_decision(expert_type, decision, current_date)

        return decision

    def _get_relevant_past_decisions(
        self,
        expert_type: ExpertType,
        current_date: datetime
    ) -> List[OrchestratorDecision]:
        """
        Get past decisions relevant to current decision with temporal weighting
        """

        relevant_decisions = []

        for decision in self.decision_history:
            if decision.expert_type != expert_type:
                continue

            # Calculate temporal relevance of past decision
            age_days = (current_date - decision.decision_date).days
            temporal_weight = math.pow(0.5, age_days / self.decision_half_life)

            # Only include decisions with meaningful temporal weight
            if temporal_weight > 0.1:
                decision_copy = decision
                decision_copy.temporal_weight = temporal_weight
                relevant_decisions.append(decision_copy)

        return relevant_decisions

    async def _calculate_decision_context(
        self,
        expert_type: ExpertType,
        current_performance: Dict[str, Any],
        shadow_performance: Dict[str, List[Dict[str, Any]]],
        past_decisions: List[OrchestratorDecision],
        seasonal_context: SeasonalContext
    ) -> Dict[str, Any]:
        """
        Calculate decision context incorporating meta-learning from past decisions
        """

        context = {
            'current_performance': current_performance,
            'shadow_performance': shadow_performance,
            'seasonal_context': seasonal_context.__dict__,
            'meta_learning_insights': {}
        }

        if past_decisions:
            # Analyze patterns in past decisions
            successful_switches = [
                d for d in past_decisions
                if d.decision_type == 'model_switch' and
                d.outcome_quality and d.outcome_quality > 0.6
            ]

            failed_switches = [
                d for d in past_decisions
                if d.decision_type == 'model_switch' and
                d.outcome_quality and d.outcome_quality < 0.4
            ]

            # Calculate meta-learning insights
            context['meta_learning_insights'] = {
                'recent_switch_success_rate': len(successful_switches) / len(past_decisions) if past_decisions else 0,
                'switch_confidence_calibration': self._calculate_confidence_calibration(past_decisions),
                'seasonal_switch_patterns': self._analyze_seasonal_switch_patterns(past_decisions),
                'performance_threshold_effectiveness': self._analyze_threshold_effectiveness(past_decisions)
            }

        return context

    def _get_seasonally_adjusted_config(
        self,
        expert_type: ExpertType,
        seasonal_context: SeasonalContext
    ) -> Dict[str, Any]:
        """
        Adjust temporal decay parameters based on seasonal data availability
        """

        base_half_life = self.base_half_lives.get(expert_type, 365)

        # Calculate seasonal adjustment factor
        # Early season (weeks 1-4): Longer half-lives (more historical reliance)
        # Mid season (weeks 5-12): Standard half-lives
        # Late season (weeks 13+): Shorter half-lives (current season data rich)

        if seasonal_context.current_week <= 4:
            # Early season: Extend half-lives by 25-50%
            adjustment_factor = 1.25 + (0.25 * (4 - seasonal_context.current_week) / 4)
        elif seasonal_context.current_week >= 13:
            # Late season: Reduce half-lives by 10-25% based on data richness
            reduction = 0.1 + (0.15 * seasonal_context.data_richness_score)
            adjustment_factor = 1.0 - reduction
        else:
            # Mid season: Standard half-lives with minor adjustments for volatility
            adjustment_factor = 1.0 - (0.05 * seasonal_context.recent_volatility)

        adjusted_half_life = int(base_half_life * adjustment_factor)

        # Get current config and adjust
        current_config = self.temporal_decay_service.decay_configs.get(expert_type)
        if current_config:
            adjusted_config = {
                'half_life': adjusted_half_life,
                'similarity_weight': current_config.similarity_weight,
                'temporal_weight': current_config.temporal_weight,
                'adjustment_factor': adjustment_factor,
                'seasonal_reasoning': self._get_seasonal_reasoning(
                    seasonal_context.current_week, adjustment_factor
                )
            }
        else:
            adjusted_config = {'half_life': adjusted_half_life}

        return adjusted_config

    def _get_seasonal_reasoning(self, current_week: int, adjustment_factor: float) -> str:
        """Generate human-readable reasoning for seasonal adjustments"""

        if current_week <= 4:
            return f"Early season (Week {current_week}): Extended half-life by {(adjustment_factor-1)*100:.0f}% due to limited current season data"
        elif current_week >= 13:
            return f"Late season (Week {current_week}): Reduced half-life by {(1-adjustment_factor)*100:.0f}% due to rich current season data"
        else:
            return f"Mid season (Week {current_week}): Minor adjustment ({(adjustment_factor-1)*100:+.0f}%) based on recent volatility"

    async def analyze_council_temporal_perspectives(
        self,
        expert_predictions: Dict[ExpertType, Dict[str, Any]],
        game_context: Dict[str, Any],
        seasonal_context: SeasonalContext
    ) -> CouncilDeliberationContext:
        """
        Analyze how different temporal perspectives affect council deliberations
        """

        temporal_perspectives = {}
        prediction_disagreements = []

        # Analyze each expert's temporal perspective
        for expert_type, prediction in expert_predictions.items():
            config = self.temporal_decay_service.decay_configs.get(expert_type)
            if not config:
                continue

            # Calculate what time periods this expert is primarily considering
            effective_memory_window = config.default_half_life * 2  # ~75% of memory weight

            temporal_perspectives[expert_type] = {
                'primary_memory_window_days': effective_memory_window,
                'similarity_vs_recency_ratio': config.similarity_weight / config.temporal_weight,
                'seasonal_adjustment': self._get_seasonally_adjusted_config(expert_type, seasonal_context),
                'prediction_confidence': prediction.get('confidence', 0.5),
                'key_factors': prediction.get('key_factors', []),
                'temporal_focus': self._categorize_temporal_focus(effective_memory_window)
            }

        # Identify temporal disagreements
        temporal_disagreement_score = self._calculate_temporal_disagreement(
            expert_predictions, temporal_perspectives
        )

        # Generate weighting adjustments based on temporal context
        weighting_adjustments = self._calculate_temporal_weighting_adjustments(
            expert_predictions, temporal_perspectives, game_context, seasonal_context
        )

        return CouncilDeliberationContext(
            expert_predictions=expert_predictions,
            temporal_perspectives=temporal_perspectives,
            consensus_confidence=self._calculate_consensus_confidence(expert_predictions),
            temporal_disagreement_score=temporal_disagreement_score,
            recommended_weighting_adjustments=weighting_adjustments
        )

    def _calculate_temporal_disagreement(
        self,
        expert_predictions: Dict[ExpertType, Dict[str, Any]],
        temporal_perspectives: Dict[ExpertType, Dict[str, Any]]
    ) -> float:
        """
        Calculate how much of the prediction disagreement is due to temporal perspectives
        """

        if len(expert_predictions) < 2:
            return 0.0

        # Get prediction spreads
        predicted_margins = [p.get('predicted_margin', 0) for p in expert_predictions.values()]
        margin_spread = max(predicted_margins) - min(predicted_margins)

        # Get temporal perspective spreads
        memory_windows = [tp.get('primary_memory_window_days', 365) for tp in temporal_perspectives.values()]
        window_spread = max(memory_windows) - min(memory_windows)

        # Normalize and combine
        normalized_margin_spread = min(margin_spread / 20.0, 1.0)  # 20-point spread = max disagreement
        normalized_window_spread = min(window_spread / 700.0, 1.0)  # 700-day spread = max temporal difference

        # Temporal disagreement is correlation between temporal differences and prediction differences
        temporal_disagreement = normalized_margin_spread * normalized_window_spread

        return temporal_disagreement

    def _calculate_temporal_weighting_adjustments(
        self,
        expert_predictions: Dict[ExpertType, Dict[str, Any]],
        temporal_perspectives: Dict[ExpertType, Dict[str, Any]],
        game_context: Dict[str, Any],
        seasonal_context: SeasonalContext
    ) -> Dict[ExpertType, float]:
        """
        Calculate how council weights should be adjusted based on temporal context
        """

        adjustments = {}

        # Determine if recent trends diverge from historical patterns
        recent_trend_strength = self._assess_recent_trend_strength(game_context, seasonal_context)

        for expert_type in expert_predictions.keys():
            temporal_info = temporal_perspectives.get(expert_type, {})
            memory_window = temporal_info.get('primary_memory_window_days', 365)

            # Adjust weights based on context
            if recent_trend_strength > 0.7:
                # Strong recent trends - favor short-memory experts
                if memory_window <= 60:  # Short memory (Momentum, Market Reader)
                    adjustments[expert_type] = 1.3
                elif memory_window >= 400:  # Long memory (Conservative, Weather)
                    adjustments[expert_type] = 0.8
                else:
                    adjustments[expert_type] = 1.0
            elif recent_trend_strength < 0.3:
                # Weak recent trends (noisy data) - favor long-memory experts
                if memory_window >= 400:  # Long memory
                    adjustments[expert_type] = 1.2
                elif memory_window <= 60:  # Short memory
                    adjustments[expert_type] = 0.9
                else:
                    adjustments[expert_type] = 1.0
            else:
                # Moderate trends - standard weighting
                adjustments[expert_type] = 1.0

        return adjustments

    def _assess_recent_trend_strength(
        self,
        game_context: Dict[str, Any],
        seasonal_context: SeasonalContext
    ) -> float:
        """
        Assess how strong recent trends are vs historical patterns
        """

        # This would analyze actual team performance trends
        # For now, return a placeholder based on seasonal volatility
        return seasonal_context.recent_volatility

    def _categorize_temporal_focus(self, memory_window_days: int) -> str:
        """Categorize expert's temporal focus"""

        if memory_window_days <= 90:
            return "immediate_recent"
        elif memory_window_days <= 180:
            return "recent"
        elif memory_window_days <= 365:
            return "current_season"
        elif memory_window_days <= 730:
            return "multi_season"
        else:
            return "historical_patterns"

    def _calculate_consensus_confidence(
        self,
        expert_predictions: Dict[ExpertType, Dict[str, Any]]
    ) -> float:
        """Calculate overall confidence in council consensus"""

        confidences = [p.get('confidence', 0.5) for p in expert_predictions.values()]
        return sum(confidences) / len(confidences) if confidences else 0.5

    async def _make_informed_decision(
        self,
        expert_type: ExpertType,
        decision_context: Dict[str, Any],
        adjusted_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make model selection decision with full context"""

        # This would implement the actual decision logic
        # incorporating meta-learning insights and seasonal adjustments

        return {
            'decision': 'keep_production',  # Placeholder
            'confidence': 0.8,
            'reasoning': 'Seasonally adjusted analysis with meta-learning',
            'adjusted_config': adjusted_config,
            'meta_insights': decision_context.get('meta_learning_insights', {})
        }

    async def _record_decision(
        self,
        expert_type: ExpertType,
        decision: Dict[str, Any],
        decision_date: datetime
    ):
        """Record decision for future meta-learning"""

        decision_record = OrchestratorDecision(
            decision_id=f"{expert_type.value}_{decision_date.isoformat()}",
            expert_type=expert_type,
            decision_type=decision['decision'],
            decision_date=decision_date,
            context=decision
        )

        self.decision_history.append(decision_record)

        # Keep only recent decisions (within 2 years)
        cutoff_date = decision_date - timedelta(days=730)
        self.decision_history = [
            d for d in self.decision_history
            if d.decision_date >= cutoff_date
        ]

    def _calculate_confidence_calibration(
        self,
        past_decisions: List[OrchestratorDecision]
    ) -> float:
        """Calculate how well calibrated the orchestrator's confidence has been"""

        # This would analyze whether high-confidence decisions actually worked out better
        # Placeholder implementation
        return 0.75

    def _analyze_seasonal_switch_patterns(
        self,
        past_decisions: List[OrchestratorDecision]
    ) -> Dict[str, Any]:
        """Analyze patterns in when model switches succeed by season timing"""

        # This would analyze whether switches work better in early/mid/late season
        # Placeholder implementation
        return {
            'early_season_success_rate': 0.6,
            'mid_season_success_rate': 0.7,
            'late_season_success_rate': 0.8
        }

    def _analyze_threshold_effectiveness(
        self,
        past_decisions: List[OrchestratorDecision]
    ) -> Dict[str, Any]:
        """Analyze whether performance thresholds are set appropriately"""

        # This would analyze whether the thresholds lead to good switching decisions
        # Placeholder implementation
        return {
            'threshold_too_low_rate': 0.2,
            'threshold_too_high_rate': 0.1,
            'optimal_threshold_estimate': 0.045
        }

    async def get_seasonal_adaptation_status(
        self,
        seasonal_context: SeasonalContext
    ) -> Dict[str, Any]:
        """Get current seasonal adaptation status for all experts"""

        adaptations = {}

        for expert_type in ExpertType:
            adjusted_config = self._get_seasonally_adjusted_config(expert_type, seasonal_context)
            base_half_life = self.base_half_lives.get(expert_type, 365)

            adaptations[expert_type.value] = {
                'base_half_life': base_half_life,
                'adjusted_half_life': adjusted_config.get('half_life', base_half_life),
                'adjustment_factor': adjusted_config.get('adjustment_factor', 1.0),
                'seasonal_reasoning': adjusted_config.get('seasonal_reasoning', 'No adjustment'),
                'temporal_focus': self._categorize_temporal_focus(adjusted_config.get('half_life', base_half_life) * 2)
            }

        return {
            'seasonal_context': seasonal_context.__dict__,
            'expert_adaptations': adaptations,
            'system_wide_trends': {
                'average_adjustment_factor': sum(
                    a.get('adjustment_factor', 1.0) for a in adaptations.values()
                ) / len(adaptations),
                'adaptation_reasoning': self._get_system_adaptation_reasoning(seasonal_context)
            }
        }

    def _get_system_adaptation_reasoning(self, seasonal_context: SeasonalContext) -> str:
        """Get system-wide reasoning for seasonal adaptations"""

        if seasonal_context.current_week <= 4:
            return f"Early season (Week {seasonal_context.current_week}): Extending memory windows due to limited current season data"
        elif seasonal_context.current_week >= 13:
            return f"Late season (Week {seasonal_context.current_week}): Shortening memory windows due to rich current season data"
        else:
            return f"Mid season (Week {seasonal_context.current_week}): Minor adjustments based on recent performance volatility"
