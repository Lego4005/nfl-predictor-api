"""
Model Switching Policy Service

Implements intelligent model switching with eligibility gates and bandit a
Routes underperforming experts to baseline models until performance improves.
"""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import numpy as np

from src.services.supabase_service import SupabaseService
from src.services.baseline_models_service import BaselineModelsService

logger = logging.getLogger(__name__)

class ModelType(Enum):
    EXPERT = "expert"
    COIN_FLIP = "coin_flip"
    MARKET_ONLY = "market_only"
    ONE_SHOT = "one_shot"
    DELIBERATE = "deliberate"

@dataclass
class ModelPerformance:
    """Performance metrics for a model"""
    model_id: str
    model_type: ModelType
    brier_score: float
    mae_score: float
    roi: float
    accuracy: float
    json_validity: float
    latency_p95: float
    prediction_count: int
    last_updated: datetime
    eligibility_score: float

@dataclass
class SwitchingDecision:
    """Decision about model switching"""
    expert_id: str
    current_model: str
    recommended_model: str
    reason: str
    confidence: float
    switch_recommended: bool
    dwell_time_remaining: int

class ModelSwitchingService:
    """Service for intelligent model switching and performance-based routing"""

    def __init__(self, supabase_service: SupabaseService, baseline_service: BaselineModelsService):
        self.supabase = supabase_service
        self.baseline_service = baseline_service

        # Switching policy configuration
        self.config = {
            'eligibility_thresholds': {
                'json_validity_min': 0.985,  # 98.5% validity required
                'latency_p95_max': 6.0,      # 6 second SLO
                'min_predictions': 10         # Minimum predictions for evaluation
            },
            'performance_weights': {
                'brier_weight': 0.35,
                'mae_weight': 0.35,
                'roi_weight': 0.20,
                'coherence_weight': 0.10
            },
            'bandit_config': {
                'exploration_rate': 0.15,    # 15% exploration minimum
                'exploration_decay': 0.95,   # Decay exploration over time
                'confidence_threshold': 0.8   # Switch confidence threshold
            },
            'dwell_time': {
                'min_games': 3,              # Minimum games before re-evaluation
                'max_games': 10,             # Maximum games before forced evaluation
                'performance_window': 20      # Games to consider for performance
            },
            'degradation_thresholds': {
                'brier_degradation': 0.05,   # 5% increase triggers review
                'roi_degradation': 0.10,     # 10% decrease triggers review
                'consecutive_failures': 3     # Consecutive poor performances
            }
        }

        # Model performance tracking
        self.model_performance = {}
        self.switching_history = {}
        self.exploration_rates = {}

    async def evaluate_model_switching(self, expert_id: str, game_id: str) -> SwitchingDecision:
        """Evaluate whether an expert should switch models"""
        try:
            # Get current model assignment
            current_model = await self._get_current_model(expert_id)

            # Check dwell time
            dwell_remaining = await self._check_dwell_time(expert_id)
            if dwell_remaining > 0:
                return SwitchingDecision(
                    expert_id=expert_id,
                    current_model=current_model,
                    recommended_model=current_model,
                    reason=f"Dwell time: {dwell_remaining} games remaining",
                    confidence=1.0,
                    switch_recommended=False,
                    dwell_time_remaining=dwell_remaining
                )

            # Get performance metrics
            performance = await self._get_model_performance(expert_id, current_model)

            # Check eligibility gates
            eligibility_check = self._check_eligibility_gates(performance)
            if not eligibility_check['eligible']:
                # Route to baseline model
                recommended_model = self._select_baseline_model(expert_id, performance)
                return SwitchingDecision(
                    expert_id=expert_id,
                    current_model=current_model,
                    recommended_model=recommended_model,
                    reason=f"Eligibility failure: {eligibility_check['reason']}",
                    confidence=0.9,
                    switch_recommended=True,
                    dwell_time_remaining=0
                )

            # Check for performance degradation
            degradation_check = await self._check_performance_degradation(expert_id, performance)
            if degradation_check['degraded']:
                recommended_model = await self._select_alternative_model(expert_id, performance)
                return SwitchingDecision(
                    expert_id=expert_id,
                    current_model=current_model,
                    recommended_model=recommended_model,
                    reason=f"Performance degradation: {degradation_check['reason']}",
                    confidence=degradation_check['confidence'],
                    switch_recommended=True,
                    dwell_time_remaining=0
                )

            # Multi-armed bandit exploration
            exploration_decision = await self._bandit_exploration(expert_id, performance)
            if exploration_decision['explore']:
                return SwitchingDecision(
                    expert_id=expert_id,
                    current_model=current_model,
                    recommended_model=exploration_decision['model'],
                    reason=f"Bandit exploration: {exploration_decision['reason']}",
                    confidence=exploration_decision['confidence'],
                    switch_recommended=True,
                    dwell_time_remaining=0
                )

            # No switch recommended
            return SwitchingDecision(
                expert_id=expert_id,
                current_model=current_model,
                recommended_model=current_model,
                reason="Performance satisfactory, no switch needed",
                confidence=0.8,
                switch_recommended=False,
                dwell_time_remaining=0
            )

        except Exception as e:
            logger.error(f"Model switching evaluation failed for expert {expert_id}: {e}")
            raise

    async def implement_model_switch(self, expert_id: str, new_model: str, reason: str) -> bool:
        """Implement a model switch for an expert"""
        try:
            # Record the switch
            switch_record = {
                'expert_id': expert_id,
                'old_model': await self._get_current_model(expert_id),
                'new_model': new_model,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
                'game_id': None  # Will be set when used
            }

            # Update expert model assignment
            await self.supabase.table('expert_model_assignments').upsert({
                'expert_id': expert_id,
                'model_type': new_model,
                'assigned_at': datetime.now().isoformat(),
                'reason': reason,
                'status': 'active'
            }).execute()

            # Record in switching history
            await self.supabase.table('model_switching_history').insert(switch_record).execute()

            # Reset dwell time
            await self._reset_dwell_time(expert_id)

            logger.info(f"Model switch implemented: {expert_id} -> {new_model} ({reason})")
            return True

        except Exception as e:
            logger.error(f"Failed to implement model switch for {expert_id}: {e}")
            return False

    async def get_switching_recommendations(self, expert_ids: List[str]) -> Dict[str, SwitchingDecision]:
        """Get switching recommendations for multiple experts"""
        recommendations = {}

        try:
            for expert_id in expert_ids:
                recommendations[expert_id] = await self.evaluate_model_switching(expert_id, None)

            return recommendations

        except Exception as e:
            logger.error(f"Failed to get switching recommendations: {e}")
            return {}

    async def update_model_performance(self, expert_id: str, model_type: str, metrics: Dict[str, float]):
        """Update performance metrics for a model"""
        try:
            performance_record = {
                'expert_id': expert_id,
                'model_type': model_type,
                'brier_score': metrics.get('brier_score', 0.0),
                'mae_score': metrics.get('mae_score', 0.0),
                'roi': metrics.get('roi', 0.0),
                'accuracy': metrics.get('accuracy', 0.0),
                'json_validity': metrics.get('json_validity', 1.0),
                'latency_p95': metrics.get('latency_p95', 0.0),
                'prediction_count': metrics.get('prediction_count', 0),
                'updated_at': datetime.now().isoformat()
            }

            # Calculate eligibility score
            performance_record['eligibility_score'] = self._calculate_eligibility_score(performance_record)

            # Upsert performance record
            await self.supabase.table('model_performance_metrics').upsert(performance_record).execute()

            logger.debug(f"Updated performance metrics for {expert_id} ({model_type})")

        except Exception as e:
            logger.error(f"Failed to update model performance: {e}")

    async def _get_current_model(self, expert_id: str) -> str:
        """Get current model assignment for expert"""
        try:
            response = await self.supabase.table('expert_model_assignments')\
                .select('model_type')\
                .eq('expert_id', expert_id)\
                .eq('status', 'active')\
                .order('assigned_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data:
                return response.data[0]['model_type']
            else:
                # Default to expert model
                return 'expert'

        except Exception as e:
            logger.error(f"Failed to get current model for {expert_id}: {e}")
            return 'expert'

    async def _check_dwell_time(self, expert_id: str) -> int:
        """Check remaining dwell time for expert"""
        try:
            response = await self.supabase.table('expert_model_assignments')\
                .select('assigned_at')\
                .eq('expert_id', expert_id)\
                .eq('status', 'active')\
                .order('assigned_at', desc=True)\
                .limit(1)\
                .execute()

            if not response.data:
                return 0

            assigned_at = datetime.fromisoformat(response.data[0]['assigned_at'])
            games_since_switch = await self._count_games_since(expert_id, assigned_at)

            min_games = self.config['dwell_time']['min_games']
            return max(0, min_games - games_since_switch)

        except Exception as e:
            logger.error(f"Failed to check dwell time for {expert_id}: {e}")
            return 0

    async def _get_model_performance(self, expert_id: str, model_type: str) -> ModelPerformance:
        """Get performance metrics for a model"""
        try:
            response = await self.supabase.table('model_performance_metrics')\
                .select('*')\
                .eq('expert_id', expert_id)\
                .eq('model_type', model_type)\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data:
                data = response.data[0]
                return ModelPerformance(
                    model_id=f"{expert_id}_{model_type}",
                    model_type=ModelType(model_type),
                    brier_score=data.get('brier_score', 0.25),
                    mae_score=data.get('mae_score', 5.0),
                    roi=data.get('roi', 0.0),
                    accuracy=data.get('accuracy', 0.5),
                    json_validity=data.get('json_validity', 1.0),
                    latency_p95=data.get('latency_p95', 3.0),
                    prediction_count=data.get('prediction_count', 0),
                    last_updated=datetime.fromisoformat(data['updated_at']),
                    eligibility_score=data.get('eligibility_score', 0.5)
                )
            else:
                # Return default performance
                return ModelPerformance(
                    model_id=f"{expert_id}_{model_type}",
                    model_type=ModelType(model_type),
                    brier_score=0.25,
                    mae_score=5.0,
                    roi=0.0,
                    accuracy=0.5,
                    json_validity=1.0,
                    latency_p95=3.0,
                    prediction_count=0,
                    last_updated=datetime.now(),
                    eligibility_score=0.5
                )

        except Exception as e:
            logger.error(f"Failed to get model performance: {e}")
            return ModelPerformance(
                model_id=f"{expert_id}_{model_type}",
                model_type=ModelType(model_type),
                brier_score=0.25,
                mae_score=5.0,
                roi=0.0,
                accuracy=0.5,
                json_validity=1.0,
                latency_p95=3.0,
                prediction_count=0,
                last_updated=datetime.now(),
                eligibility_score=0.5
            )

    def _check_eligibility_gates(self, performance: ModelPerformance) -> Dict[str, Any]:
        """Check if model meets eligibility requirements"""
        thresholds = self.config['eligibility_thresholds']

        # Check JSON validity
        if performance.json_validity < thresholds['json_validity_min']:
            return {
                'eligible': False,
                'reason': f"JSON validity {performance.json_validity:.3f} < {thresholds['json_validity_min']}"
            }

        # Check latency SLO
        if performance.latency_p95 > thresholds['latency_p95_max']:
            return {
                'eligible': False,
                'reason': f"Latency p95 {performance.latency_p95:.1f}s > {thresholds['latency_p95_max']}s"
            }

        # Check minimum predictions
        if performance.prediction_count < thresholds['min_predictions']:
            return {
                'eligible': False,
                'reason': f"Insufficient predictions {performance.prediction_count} < {thresholds['min_predictions']}"
            }

        return {'eligible': True, 'reason': 'All eligibility gates passed'}

    def _select_baseline_model(self, expert_id: str, performance: ModelPerformance) -> str:
        """Select appropriate baseline model for underperforming expert"""
        # Route to one-shot for schema failures
        if performance.json_validity < 0.95:
            return 'one_shot'

        # Route to market-only for poor ROI
        if performance.roi < -0.15:
            return 'market_only'

        # Route to deliberate for high latency
        if performance.latency_p95 > 8.0:
            return 'deliberate'

        # Default to one-shot
        return 'one_shot'

    async def _check_performance_degradation(self, expert_id: str, current_performance: ModelPerformance) -> Dict[str, Any]:
        """Check for performance degradation"""
        try:
            # Get historical performance
            window_days = 14
            cutoff_date = datetime.now() - timedelta(days=window_days)

            response = await self.supabase.table('model_performance_metrics')\
                .select('*')\
                .eq('expert_id', expert_id)\
                .eq('model_type', current_performance.model_type.value)\
                .gte('updated_at', cutoff_date.isoformat())\
                .order('updated_at', desc=True)\
                .execute()

            if len(response.data) < 3:
                return {'degraded': False, 'reason': 'Insufficient historical data'}

            # Calculate trend
            recent_brier = np.mean([r['brier_score'] for r in response.data[:3]])
            older_brier = np.mean([r['brier_score'] for r in response.data[-3:]])

            recent_roi = np.mean([r['roi'] for r in response.data[:3]])
            older_roi = np.mean([r['roi'] for r in response.data[-3:]])

            # Check degradation thresholds
            brier_degradation = (recent_brier - older_brier) / older_brier if older_brier > 0 else 0
            roi_degradation = (older_roi - recent_roi) / abs(older_roi) if older_roi != 0 else 0

            thresholds = self.config['degradation_thresholds']

            if brier_degradation > thresholds['brier_degradation']:
                return {
                    'degraded': True,
                    'reason': f"Brier score degraded by {brier_degradation:.1%}",
                    'confidence': 0.8
                }

            if roi_degradation > thresholds['roi_degradation']:
                return {
                    'degraded': True,
                    'reason': f"ROI degraded by {roi_degradation:.1%}",
                    'confidence': 0.7
                }

            return {'degraded': False, 'reason': 'Performance stable'}

        except Exception as e:
            logger.error(f"Failed to check performance degradation: {e}")
            return {'degraded': False, 'reason': 'Error checking degradation'}

    async def _select_alternative_model(self, expert_id: str, performance: ModelPerformance) -> str:
        """Select alternative model for degraded performance"""
        # Get available models and their performance
        available_models = ['expert', 'one_shot', 'market_only', 'deliberate']
        current_model = performance.model_type.value

        # Remove current model from options
        alternatives = [m for m in available_models if m != current_model]

        # Simple selection based on performance characteristics
        if performance.brier_score > 0.3:
            return 'market_only'  # Use market odds for poor predictions
        elif performance.latency_p95 > 5.0:
            return 'deliberate'   # Use fast rule-based for slow models
        else:
            return 'one_shot'     # Use simplified LLM approach

    async def _bandit_exploration(self, expert_id: str, performance: ModelPerformance) -> Dict[str, Any]:
        """Multi-armed bandit exploration decision"""
        try:
            # Get current exploration rate
            exploration_rate = self.exploration_rates.get(expert_id, self.config['bandit_config']['exploration_rate'])

            # Decay exploration rate over time
            exploration_rate *= self.config['bandit_config']['exploration_decay']
            self.exploration_rates[expert_id] = exploration_rate

            # Random exploration decision
            if random.random() < exploration_rate:
                # Select exploration model
                available_models = ['expert', 'one_shot', 'market_only', 'deliberate']
                current_model = performance.model_type.value
                alternatives = [m for m in available_models if m != current_model]

                exploration_model = random.choice(alternatives)

                return {
                    'explore': True,
                    'model': exploration_model,
                    'reason': f"Bandit exploration ({exploration_rate:.1%} rate)",
                    'confidence': 0.6
                }

            return {'explore': False}

        except Exception as e:
            logger.error(f"Bandit exploration failed: {e}")
            return {'explore': False}

    def _calculate_eligibility_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall eligibility score"""
        try:
            weights = self.config['performance_weights']

            # Normalize metrics (lower is better for brier/mae, higher for roi)
            brier_norm = max(0, 1 - metrics.get('brier_score', 0.25) / 0.5)
            mae_norm = max(0, 1 - metrics.get('mae_score', 5.0) / 10.0)
            roi_norm = max(0, min(1, (metrics.get('roi', 0.0) + 0.2) / 0.4))
            coherence_norm = metrics.get('json_validity', 1.0)

            score = (
                weights['brier_weight'] * brier_norm +
                weights['mae_weight'] * mae_norm +
                weights['roi_weight'] * roi_norm +
                weights['coherence_weight'] * coherence_norm
            )

            return max(0, min(1, score))

        except Exception as e:
            logger.error(f"Failed to calculate eligibility score: {e}")
            return 0.5

    async def _count_games_since(self, expert_id: str, since_date: datetime) -> int:
        """Count games since a specific date"""
        try:
            response = await self.supabase.table('expert_predictions')\
                .select('game_id', count='exact')\
                .eq('expert_id', expert_id)\
                .gte('created_at', since_date.isoformat())\
                .execute()

            return response.count or 0

        except Exception as e:
            logger.error(f"Failed to count games since {since_date}: {e}")
            return 0

    async def _reset_dwell_time(self, expert_id: str):
        """Reset dwell time tracking for expert"""
        try:
            # This would update dwell time tracking
            # For now, just log the reset
            logger.info(f"Dwell time reset for expert {expert_id}")

        except Exception as e:
            logger.error(f"Failed to reset dwell time: {e}")

    async def get_switching_analytics(self) -> Dict[str, Any]:
        """Get analytics on model switching performance"""
        try:
            # Get switching history
            response = await self.supabase.table('model_switching_history')\
                .select('*')\
                .order('timestamp', desc=True)\
                .limit(100)\
                .execute()

            switching_data = response.data or []

            # Calculate analytics
            analytics = {
                'total_switches': len(switching_data),
                'switches_by_reason': {},
                'switches_by_model': {},
                'recent_switches': switching_data[:10],
                'switch_success_rate': 0.0,
                'average_dwell_time': 0.0
            }

            # Group by reason
            for switch in switching_data:
                reason = switch.get('reason', 'unknown')
                analytics['switches_by_reason'][reason] = analytics['switches_by_reason'].get(reason, 0) + 1

                new_model = switch.get('new_model', 'unknown')
                analytics['switches_by_model'][new_model] = analytics['switches_by_model'].get(new_model, 0) + 1

            return analytics

        except Exception as e:
            logger.error(f"Failed to get switching analytics: {e}")
            return {}
