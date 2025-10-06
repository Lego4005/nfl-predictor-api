"""
Orchestrator Shadow Testing Service with Temporal Decay Integration

This service ensures that shadow model testing applies the same temporal decay
as production models, enabling fair comparison and rapid adaptation for
fasperts like Market Reader.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from services.temporal_decay_service import TemporalDecayService, ExpertType


@dataclass
class ShadowModelPerformance:
    """Performance tracking for shadow models with temporal awareness"""
    model_id: str
    expert_type: ExpertType
    total_predictions: int
    recent_accuracy: float  # Temporally weighted accuracy
    raw_accuracy: float     # Unweighted accuracy
    temporal_score: float   # Combined temporal performance score
    last_updated: datetime
    performance_trend: str  # 'improving', 'declining', 'stable'


@dataclass
class ModelComparisonResult:
    """Result of comparing production vs shadow models"""
    expert_type: ExpertType
    production_score: float
    shadow_scores: Dict[str, float]
    recommended_action: str  # 'keep_production', 'switch_to_shadow', 'continue_testing'
    confidence: float
    reasoning: str


class OrchestratorShadowTestingService:
    """
    Enhanced orchestrator that applies temporal decay to shadow model evaluation,
    ensuring model selection decisions are based on recent performance data.
    """

    def __init__(self, temporal_decay_service: TemporalDecayService):
        self.temporal_decay_service = temporal_decay_service
        self.logger = logging.getLogger(__name__)

        # Shadow testing configuration per expert type
        self.shadow_configs = self._initialize_shadow_configs()

    def _initialize_shadow_configs(self) -> Dict[ExpertType, Dict[str, Any]]:
        """Initialize shadow testing configurations based on expert temporal characteristics"""

        configs = {}

        # Fast-decay experts need more aggressive shadow testing
        fast_decay_experts = [
            ExpertType.MOMENTUM_TRACKER,
            ExpertType.MARKET_READER,
            ExpertType.AGGRESSIVE_GAMBLER
        ]

        # Slow-decay experts can use longer evaluation periods
        slow_decay_experts = [
            ExpertType.WEATHER_SPECIALIST,
            ExpertType.CONSERVATIVE_ANALYZER,
            ExpertType.HOME_FIELD_GURU
        ]

        for expert_type in ExpertType:
            if expert_type in fast_decay_experts:
                configs[expert_type] = {
                    'evaluation_window_days': 30,      # Short evaluation window
                    'min_predictions_for_switch': 15,   # Quick decision threshold
                    'performance_threshold': 0.05,      # 5% improvement needed
                    'shadow_model_count': 3,            # Test multiple alternatives
                    'reeval_frequency_days': 7           # Weekly re-evaluation
                }
            elif expert_type in slow_decay_experts:
                configs[expert_type] = {
                    'evaluation_window_days': 90,       # Longer evaluation window
                    'min_predictions_for_switch': 30,   # More data needed
                    'performance_threshold': 0.03,      # 3% improvement needed
                    'shadow_model_count': 2,            # Fewer alternatives
                    'reeval_frequency_days': 21          # Monthly re-evaluation
                }
            else:
                # Moderate decay experts
                configs[expert_type] = {
                    'evaluation_window_days': 60,       # Medium evaluation window
                    'min_predictions_for_switch': 20,   # Moderate data requirement
                    'performance_threshold': 0.04,      # 4% improvement needed
                    'shadow_model_count': 2,            # Standard alternatives
                    'reeval_frequency_days': 14          # Bi-weekly re-evaluation
                }

        return configs

    async def evaluate_shadow_models(
        self,
        expert_type: ExpertType,
        production_predictions: List[Dict[str, Any]],
        shadow_predictions: Dict[str, List[Dict[str, Any]]],
        current_date: datetime
    ) -> ModelComparisonResult:
        """
        Evaluate shadow models against production using temporal decay weighting.

        Args:
            expert_type: Type of expert being evaluated
            production_predictions: Production model predictions with outcomes
            shadow_predictions: Dict of shadow_model_id -> predictions
            current_date: Current date for temporal calculations

        Returns:
            ModelComparisonResult: Comparison with recommendation
        """

        config = self.shadow_configs[expert_type]
        evaluation_window = timedelta(days=config['evaluation_window_days'])
        cutoff_date = current_date - evaluation_window

        # Filter predictions to evaluation window
        recent_production = [
            p for p in production_predictions
            if self._get_prediction_date(p) >= cutoff_date
        ]

        recent_shadow = {}
        for model_id, predictions in shadow_predictions.items():
            recent_shadow[model_id] = [
                p for p in predictions
                if self._get_prediction_date(p) >= cutoff_date
            ]

        # Calculate temporally weighted performance scores
        production_score = await self._calculate_temporal_performance_score(
            expert_type, recent_production, current_date
        )

        shadow_scores = {}
        for model_id, predictions in recent_shadow.items():
            if len(predictions) >= config['min_predictions_for_switch']:
                shadow_scores[model_id] = await self._calculate_temporal_performance_score(
                    expert_type, predictions, current_date
                )

        # Determine recommendation
        recommendation = self._generate_model_recommendation(
            expert_type, production_score, shadow_scores, config
        )

        return recommendation

    async def _calculate_temporal_performance_score(
        self,
        expert_type: ExpertType,
        predictions: List[Dict[str, Any]],
        current_date: datetime
    ) -> float:
        """
        Calculate performance score with temporal decay weighting.

        More recent predictions have higher weight in the performance calculation,
        with weighting based on the expert's temporal decay characteristics.
        """

        if not predictions:
            return 0.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for prediction in predictions:
            # Get prediction accuracy (1.0 for correct, 0.0 for incorrect)
            accuracy = 1.0 if prediction.get('was_correct', False) else 0.0

            # Calculate temporal weight based on prediction age
            prediction_date = self._get_prediction_date(prediction)
            age_days = (current_date - prediction_date).days

            temporal_weight = self.temporal_decay_service.calculate_temporal_decay_score(
                expert_type=expert_type,
                memory_age_days=age_days
            )

            # Weight the accuracy by temporal relevance
            total_weighted_score += accuracy * temporal_weight
            total_weight += temporal_weight

        # Return weighted average accuracy
        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def _generate_model_recommendation(
        self,
        expert_type: ExpertType,
        production_score: float,
        shadow_scores: Dict[str, float],
        config: Dict[str, Any]
    ) -> ModelComparisonResult:
        """Generate model switching recommendation based on temporal performance"""

        if not shadow_scores:
            return ModelComparisonResult(
                expert_type=expert_type,
                production_score=production_score,
                shadow_scores=shadow_scores,
                recommended_action='keep_production',
                confidence=1.0,
                reasoning="No shadow models have sufficient data for evaluation"
            )

        # Find best shadow model
        best_shadow_id = max(shadow_scores.keys(), key=lambda k: shadow_scores[k])
        best_shadow_score = shadow_scores[best_shadow_id]

        # Calculate improvement
        improvement = best_shadow_score - production_score
        threshold = config['performance_threshold']

        # Generate recommendation
        if improvement >= threshold:
            action = 'switch_to_shadow'
            confidence = min(0.95, 0.5 + (improvement / threshold) * 0.4)
            reasoning = f"Shadow model {best_shadow_id} shows {improvement:.3f} improvement " \
                       f"(threshold: {threshold:.3f}) with temporal weighting"
        elif improvement >= threshold * 0.5:
            action = 'continue_testing'
            confidence = 0.6
            reasoning = f"Shadow model {best_shadow_id} shows promising {improvement:.3f} improvement " \
                       f"but below threshold. Continue testing."
        else:
            action = 'keep_production'
            confidence = 0.8
            reasoning = f"Production model outperforms shadows. Best shadow improvement: {improvement:.3f}"

        return ModelComparisonResult(
            expert_type=expert_type,
            production_score=production_score,
            shadow_scores=shadow_scores,
            recommended_action=action,
            confidence=confidence,
            reasoning=reasoning
        )

    async def update_shadow_model_performance(
        self,
        expert_type: ExpertType,
        model_id: str,
        new_predictions: List[Dict[str, Any]],
        current_date: datetime
    ) -> ShadowModelPerformance:
        """
        Update shadow model performance tracking with temporal awareness.

        This ensures that performance metrics reflect the expert's temporal
        characteristics - fast-decay experts focus on very recent performance.
        """

        # Calculate recent performance with temporal weighting
        recent_score = await self._calculate_temporal_performance_score(
            expert_type, new_predictions, current_date
        )

        # Calculate raw accuracy for comparison
        raw_accuracy = sum(1 for p in new_predictions if p.get('was_correct', False)) / len(new_predictions) \
                      if new_predictions else 0.0

        # Determine performance trend
        trend = self._calculate_performance_trend(expert_type, model_id, recent_score)

        return ShadowModelPerformance(
            model_id=model_id,
            expert_type=expert_type,
            total_predictions=len(new_predictions),
            recent_accuracy=recent_score,
            raw_accuracy=raw_accuracy,
            temporal_score=recent_score,
            last_updated=current_date,
            performance_trend=trend
        )

    def _calculate_performance_trend(
        self,
        expert_type: ExpertType,
        model_id: str,
        current_score: float
    ) -> str:
        """Calculate performance trend for shadow model"""

        # This would typically look up historical performance data
        # For now, return a placeholder
        return 'stable'

    def _get_prediction_date(self, prediction: Dict[str, Any]) -> datetime:
        """Extract prediction date from prediction dictionary"""

        date_field = prediction.get('prediction_date', prediction.get('created_at'))

        if isinstance(date_field, str):
            return datetime.fromisoformat(date_field.replace('Z', '+00:00'))
        elif isinstance(date_field, datetime):
            return date_field
        else:
            # Fallback to current date if no date available
            return datetime.now()

    async def should_trigger_model_switch(
        self,
        expert_type: ExpertType,
        comparison_result: ModelComparisonResult
    ) -> bool:
        """
        Determine if a model switch should be triggered based on expert characteristics.

        Fast-decay experts (Market Reader, Momentum Tracker) should switch more
        aggressively than slow-decay experts (Weather Specialist, Conservative Analyzer).
        """

        if comparison_result.recommended_action != 'switch_to_shadow':
            return False

        # Get expert's temporal characteristics
        decay_config = self.temporal_decay_service.decay_configs.get(expert_type)
        if not decay_config:
            return False

        # Fast-decay experts switch with lower confidence thresholds
        if decay_config.default_half_life <= 90:  # Very fast decay
            confidence_threshold = 0.6
        elif decay_config.default_half_life <= 180:  # Fast decay
            confidence_threshold = 0.7
        elif decay_config.default_half_life <= 365:  # Moderate decay
            confidence_threshold = 0.75
        else:  # Slow decay
            confidence_threshold = 0.8

        return comparison_result.confidence >= confidence_threshold

    async def get_shadow_testing_status(
        self,
        expert_type: ExpertType
    ) -> Dict[str, Any]:
        """Get current shadow testing status for an expert"""

        config = self.shadow_configs[expert_type]
        decay_config = self.temporal_decay_service.decay_configs.get(expert_type)

        return {
            'expert_type': expert_type.value,
            'evaluation_window_days': config['evaluation_window_days'],
            'min_predictions_for_switch': config['min_predictions_for_switch'],
            'performance_threshold': config['performance_threshold'],
            'reeval_frequency_days': config['reeval_frequency_days'],
            'temporal_characteristics': {
                'half_life_days': decay_config.default_half_life if decay_config else None,
                'similarity_weight': decay_config.similarity_weight if decay_config else None,
                'temporal_weight': decay_config.temporal_weight if decay_config else None
            },
            'adaptation_speed': self._get_adaptation_speed(expert_type)
        }

    def _get_adaptation_speed(self, expert_type: ExpertType) -> str:
        """Get adaptation speed category for expert"""

        decay_config = self.temporal_decay_service.decay_configs.get(expert_type)
        if not decay_config:
            return 'unknown'

        half_life = decay_config.default_half_life

        if half_life <= 60:
            return 'extremely_fast'
        elif half_life <= 120:
            return 'very_fast'
        elif half_life <= 240:
            return 'fast'
        elif half_life <= 365:
            return 'moderate'
        else:
            return 'slow'
