"""
Adaptive Learning Engine - Real ML-Based Expert Improvement

Replaces rule-based "learning" with actual gradient-descent optimization.
Each expert maintains learnable weights that adjust based on prediction accuracy.

Key Innovation:
- Uses historical performance to adjust expert confidence weights
- Implements simple gradient descent on prediction accuracy
- Stores learned parameters in Supabase (no direct DB connection needed)
- Enables true "learning from mistakes"
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ExpertWeights:
    """Learnable weights for an expert's decision factors"""
    expert_id: str
    weights: Dict[str, float]  # Factor name -> weight
    learning_rate: float
    accuracy_history: List[float]
    last_updated: str

    def to_dict(self) -> Dict:
        return {
            'expert_id': self.expert_id,
            'weights': self.weights,
            'learning_rate': self.learning_rate,
            'accuracy_history': self.accuracy_history,
            'last_updated': self.last_updated
        }


class AdaptiveLearningEngine:
    """
    ML-based learning engine that actually improves expert predictions over time.

    Uses gradient descent to optimize expert decision weights based on:
    1. Prediction accuracy (correct/incorrect)
    2. Confidence calibration (predicted confidence vs actual correctness)
    3. Factor importance (which factors led to correct predictions)
    """

    def __init__(self, supabase_client, learning_rate: float = 0.01):
        self.supabase = supabase_client
        self.learning_rate = learning_rate
        self.expert_weights: Dict[str, ExpertWeights] = {}

    async def initialize_expert(self, expert_id: str, initial_factors: List[str]):
        """Initialize expert with uniform weights"""
        # Try to load existing weights from Supabase
        result = self.supabase.table('expert_learned_weights') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .execute()

        if result.data and len(result.data) > 0:
            # Load existing weights
            data = result.data[0]
            self.expert_weights[expert_id] = ExpertWeights(
                expert_id=expert_id,
                weights=data['weights'],
                learning_rate=data.get('learning_rate', self.learning_rate),
                accuracy_history=data.get('accuracy_history', []),
                last_updated=data['updated_at']
            )
        else:
            # Create new uniform weights
            initial_weight = 1.0 / len(initial_factors) if initial_factors else 0.5
            self.expert_weights[expert_id] = ExpertWeights(
                expert_id=expert_id,
                weights={factor: initial_weight for factor in initial_factors},
                learning_rate=self.learning_rate,
                accuracy_history=[],
                last_updated=datetime.utcnow().isoformat()
            )

    async def update_from_prediction(
        self,
        expert_id: str,
        predicted_winner: str,
        predicted_confidence: float,
        actual_winner: str,
        factors_used: List[Dict[str, float]]  # [{'factor': 'home_advantage', 'value': 0.8}, ...]
    ):
        """
        Update expert weights based on prediction outcome using gradient descent.

        Loss function: L = (predicted_confidence - accuracy)^2
        where accuracy = 1.0 if correct, 0.0 if incorrect

        Gradient descent: weight -= learning_rate * dL/dweight
        """
        if expert_id not in self.expert_weights:
            await self.initialize_expert(expert_id, [f['factor'] for f in factors_used])

        weights = self.expert_weights[expert_id]

        # Calculate accuracy (0 or 1)
        is_correct = 1.0 if predicted_winner == actual_winner else 0.0

        # Calculate loss and gradient
        # Loss = (confidence - is_correct)^2
        # dL/dconfidence = 2 * (confidence - is_correct)
        confidence_error = predicted_confidence - is_correct
        gradient_multiplier = 2.0 * confidence_error

        # Update each factor weight based on its contribution
        for factor_data in factors_used:
            factor_name = factor_data['factor']
            factor_value = factor_data.get('value', 0.5)

            if factor_name not in weights.weights:
                weights.weights[factor_name] = 0.5

            # Gradient for this weight = gradient_multiplier * factor_value
            gradient = gradient_multiplier * factor_value

            # Update weight using gradient descent
            weights.weights[factor_name] -= weights.learning_rate * gradient

            # Clip weights to [0, 1] range
            weights.weights[factor_name] = np.clip(weights.weights[factor_name], 0.0, 1.0)

        # Track accuracy history
        weights.accuracy_history.append(is_correct)

        # Keep only last 100 games
        if len(weights.accuracy_history) > 100:
            weights.accuracy_history = weights.accuracy_history[-100:]

        weights.last_updated = datetime.utcnow().isoformat()

        # Save to Supabase
        await self._save_weights(expert_id)

    async def _save_weights(self, expert_id: str):
        """Save learned weights to Supabase"""
        weights = self.expert_weights[expert_id]

        data = {
            'expert_id': expert_id,
            'weights': weights.weights,
            'learning_rate': weights.learning_rate,
            'accuracy_history': weights.accuracy_history,
            'updated_at': weights.last_updated
        }

        # Upsert (insert or update) with on_conflict parameter
        self.supabase.table('expert_learned_weights').upsert(
            data,
            on_conflict='expert_id'  # Specify which column to use for conflict resolution
        ).execute()

    def get_adjusted_confidence(
        self,
        expert_id: str,
        base_confidence: float,
        factors: List[Dict[str, float]]
    ) -> float:
        """
        Apply learned weights to adjust expert's confidence.

        Returns: Adjusted confidence based on factor importance
        """
        if expert_id not in self.expert_weights:
            return base_confidence

        weights = self.expert_weights[expert_id]

        # Calculate weighted factor score
        factor_score = 0.0
        total_weight = 0.0

        for factor_data in factors:
            factor_name = factor_data['factor']
            factor_value = factor_data.get('value', 0.5)

            if factor_name in weights.weights:
                weight = weights.weights[factor_name]
                factor_score += weight * factor_value
                total_weight += weight

        if total_weight > 0:
            normalized_score = factor_score / total_weight
            # Blend learned score with base confidence
            adjusted = 0.7 * base_confidence + 0.3 * normalized_score
            return np.clip(adjusted, 0.0, 1.0)

        return base_confidence

    def get_learning_stats(self, expert_id: str) -> Dict:
        """Get learning statistics for an expert"""
        if expert_id not in self.expert_weights:
            return {
                'games_learned_from': 0,
                'recent_accuracy': 0.0,
                'improvement_trend': 0.0,
                'top_factors': []
            }

        weights = self.expert_weights[expert_id]
        history = weights.accuracy_history

        # Calculate recent accuracy (last 20 games)
        recent_accuracy = np.mean(history[-20:]) if len(history) >= 20 else np.mean(history) if history else 0.0

        # Calculate improvement trend (last 20 vs first 20)
        if len(history) >= 40:
            early_accuracy = np.mean(history[:20])
            recent_accuracy_trend = np.mean(history[-20:])
            improvement = recent_accuracy_trend - early_accuracy
        else:
            improvement = 0.0

        # Top factors by weight
        top_factors = sorted(
            weights.weights.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'games_learned_from': len(history),
            'recent_accuracy': float(recent_accuracy),
            'improvement_trend': float(improvement),
            'top_factors': [{'factor': f, 'weight': w} for f, w in top_factors]
        }