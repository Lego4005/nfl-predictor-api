"""
Temporal Decay Calculator for NFL Prediction Training System
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Any

from training.expert_configuration import ExpertType, ExpertConfiguration, ExpertConfigurationManager


@dataclass
class DecayScore:
    """Represents a temporal decay score calculation"""
    age_days: int
    half_life_days: int
    decay_score: float
    similarity_score: float
    final_weighted_score: float
    expert_type: ExpertType


class TemporalDecayCalculator:
    """Calculates temporal decay scores using exponential decay formula"""

    def __init__(self, config_manager: ExpertConfigurationManager):
        self.config_manager = config_manager
        self.configurations = config_manager.get_all_configurations()

    def calculate_decay_score(self, age_days: int, half_life_days: int) -> float:
        """Calculate pure temporal decay score using exponential decay"""
        if age_days < 0:
            return 1.0

        if half_life_days <= 0:
            raise ValueError(f"Invalid half_life_days: {half_life_days}")

        # Exponential decay: score = 0.5^(age / half_life)
        decay_score = math.pow(0.5, age_days / half_life_days)
        return decay_score

    def calculate_weighted_score(
        self,
        expert_type: ExpertType,
        age_days: int,
        similarity_score: float,
        current_week: int = 10,
        data_richness_score: float = 0.5
    ) -> DecayScore:
        """Calculate final weighted score combining temporal decay and similarity"""
        config = self.configurations.get(expert_type)
        if not config:
            raise ValueError(f"No configuration found for expert type: {expert_type}")

        # Get seasonally adjusted half-life
        adjusted_half_life = self.config_manager.get_seasonal_adjusted_half_life(
            expert_type, current_week, data_richness_score
        )

        # Calculate temporal decay score
        decay_score = self.calculate_decay_score(age_days, adjusted_half_life)

        # Calculate final weighted score
        final_score = (
            config.similarity_weight * similarity_score +
            config.temporal_weight * decay_score
        )

        return DecayScore(
            age_days=age_days,
            half_life_days=adjusted_half_life,
            decay_score=decay_score,
            similarity_score=similarity_score,
            final_weighted_score=final_score,
            expert_type=expert_type
        )


def test_temporal_decay_calculator():
    """Test function for the temporal decay calculator"""

    print("Testing Temporal Decay Calculator")
    print("=" * 50)

    # Initialize
    config_manager = ExpertConfigurationManager()
    calculator = TemporalDecayCalculator(config_manager)

    # Test basic decay calculation
    print("Basic Decay Tests:")
    test_cases = [
        (0, 180, 1.0),      # Age 0 should be 1.0
        (180, 180, 0.5),    # At half-life should be 0.5
        (360, 180, 0.25),   # At 2x half-life should be 0.25
    ]

    for age, half_life, expected in test_cases:
        actual = calculator.calculate_decay_score(age, half_life)
        status = "PASS" if abs(actual - expected) < 0.001 else "FAIL"
        print(f"  {status}: Age {age}d, Half-life {half_life}d: {actual:.4f} (expected {expected})")

    # Test expert comparisons
    print("Expert Temporal Behavior:")
    test_experts = [
        ExpertType.MOMENTUM_RIDER,        # 45d half-life
        ExpertType.CONSERVATIVE_ANALYZER, # 450d half-life
        ExpertType.FUNDAMENTALIST_SCHOLAR # 600d half-life
    ]

    similarity = 0.8
    test_ages = [7, 30, 90, 180]

    print(f"{'Expert':<20} {'7d':<8} {'30d':<8} {'90d':<8} {'180d':<8}")
    print("-" * 60)

    for expert_type in test_experts:
        config = config_manager.get_configuration(expert_type)
        scores = []

        for age in test_ages:
            score = calculator.calculate_weighted_score(expert_type, age, similarity)
            scores.append(f"{score.final_weighted_score:.3f}")

        expert_name = config.name.replace('The ', '')[:19]
        print(f"{expert_name:<20} {' '.join(f'{score:<8}' for score in scores)}")

    return calculator


if __name__ == "__main__":
    test_temporal_decay_calculator()
