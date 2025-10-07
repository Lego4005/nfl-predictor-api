#!/usr/bin/env python3
"""
Temporal Decay Service for Expert Memory System
s expert-specific temporal decay calculations for episodic memory retrieval.
Different experts have different memory decay rates based on their analytical personalities.

Requirements: 5.1, 5.2, 5.3, 5.6
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import math

logger = logging.getLogger(__name__)


class ExpertType(Enum):
    """Expert types with different temporal decay characteristics"""
    # Fast decay experts (value recent performance)
    MOMENTUM_TRACKER = "momentum_rider"
    MARKET_READER = "sharp_money_follower"
    AGGRESSIVE_GAMBLER = "risk_taking_gambler"

    # Moderate decay experts
    INJURY_TRACKER = "gut_instinct_expert"
    DIVISIONAL_SPECIALIST = "contrarian_rebel"

    # Slow decay experts (value historical patterns)
    STATISTICAL_PURIST = "statistics_purist"
    CONSERVATIVE_ANALYZER = "conservative_analyzer"
    WEATHER_SPECIALIST = "fundamentalist_scholar"

    # Additional experts
    VALUE_HUNTER = "value_hunter"
    CHAOS_BELIEVER = "chaos_theory_believer"
    TREND_REVERSAL = "trend_reversal_specialist"
    NARRATIVE_FADER = "popular_narrative_fader"
    UNDERDOG_CHAMPION = "underdog_champion"
    CONSENSUS_FOLLOWER = "consensus_follower"
    MARKET_EXPLOITER = "market_inefficiency_exploiter"


@dataclass
class TemporalDecayConfig:
    """Configuration for temporal decay calculation"""
    expert_type: ExpertType
    default_half_life: int  # Days for memory strength to decay to 50%
    similarity_weight: float  # Weight given to similarity score (0-1)
    temporal_weight: float  # Weight given to temporal decay (0-1)
    base_learning_rate: float  # Base learning rate for belief updates
    memory_category_half_lives: Dict[str, int]  # Category-specific half-lives

    def __post_init__(self):
        """Validate configuration"""
        if abs(self.similarity_weight + self.temporal_weight - 1.0) > 0.01:
            raise ValueError("similarity_weight + temporal_weight must equal 1.0")


@dataclass
class MemoryScore:
    """Result of temporal decay calculation"""
    memory_id: str
    similarity_score: float
    temporal_decay_score: float
    final_score: float
    days_old: int
    half_life_used: int
    category: Optional[str] = None


class TemporalDecayService:
    """Service for calculating temporal decay of expert memories"""

    def __init__(self):
        self.decay_configs = self._initialize_decay_configs()

    def _initialize_decay_configs(self) -> Dict[ExpertType, TemporalDecayConfig]:
        """Initialize decay configurations for all expert types"""
        configs = {}

        # Fast decay experts (30-120 days half-life)
        configs[ExpertType.MOMENTUM_TRACKER] = TemporalDecayConfig(
            expert_type=ExpertType.MOMENTUM_TRACKER,
            default_half_life=45,  # Very fast decay - recent momentum matters most
            similarity_weight=0.3,
            temporal_weight=0.7,  # Heavy emphasis on recency
            base_learning_rate=0.15,
            memory_category_half_lives={
                'team_momentum_patterns': 30,
                'recent_performance_trends': 21,
                'streak_analysis': 35
            }
        )

        configs[ExpertType.MARKET_READER] = TemporalDecayConfig(
            expert_type=ExpertType.MARKET_READER,
            default_half_life=90,
            similarity_weight=0.4,
            temporal_weight=0.6,
            base_learning_rate=0.12,
            memory_category_half_lives={
                'line_movement_patterns': 60,
                'sharp_money_indicators': 45,
                'public_betting_trends': 75
            }
        )

        configs[ExpertType.AGGRESSIVE_GAMBLER] = TemporalDecayConfig(
            expert_type=ExpertType.AGGRESSIVE_GAMBLER,
            default_half_life=120,
            similarity_weight=0.5,
            temporal_weight=0.5,
            base_learning_rate=0.18,  # High learning rate - adapts quickly
            memory_category_half_lives={
                'high_risk_outcomes': 90,
                'upset_predictions': 100,
                'confidence_calibration': 110
            }
        )

        # Moderate decay experts (180-270 days half-life)
        configs[ExpertType.INJURY_TRACKER] = TemporalDecayConfig(
            expert_type=ExpertType.INJURY_TRACKER,
            default_half_life=180,
            similarity_weight=0.6,
            temporal_weight=0.4,
            base_learning_rate=0.10,
            memory_category_half_lives={
                'injury_impact_patterns': 150,
                'player_replacement_effects': 200,
                'recovery_timelines': 365  # Longer for medical patterns
            }
        )

        configs[ExpertType.DIVISIONAL_SPECIALIST] = TemporalDecayConfig(
            expert_type=ExpertType.DIVISIONAL_SPECIALIST,
            default_half_life=270,
            similarity_weight=0.7,
            temporal_weight=0.3,
            base_learning_rate=0.08,
            memory_category_half_lives={
                'divisional_rivalry_patterns': 365,
                'coaching_matchup_history': 450,
                'team_familiarity_effects': 300
            }
        )

        # Slow decay experts (365-730 days half-life)
        configs[ExpertType.STATISTICAL_PURIST] = TemporalDecayConfig(
            expert_type=ExpertType.STATISTICAL_PURIST,
            default_half_life=365,
            similarity_weight=0.8,
            temporal_weight=0.2,  # Low emphasis on recency
            base_learning_rate=0.05,  # Conservative learning
            memory_category_half_lives={
                'statistical_correlations': 730,
                'regression_patterns': 545,
                'sample_size_learnings': 365
            }
        )

        configs[ExpertType.CONSERVATIVE_ANALYZER] = TemporalDecayConfig(
            expert_type=ExpertType.CONSERVATIVE_ANALYZER,
            default_half_life=450,
            similarity_weight=0.8,
            temporal_weight=0.2,
            base_learning_rate=0.04,  # Very conservative learning
            memory_category_half_lives={
                'fundamental_analysis_patterns': 730,
                'long_term_trends': 900,
                'systematic_approaches': 600
            }
        )

        configs[ExpertType.WEATHER_SPECIALIST] = TemporalDecayConfig(
            expert_type=ExpertType.WEATHER_SPECIALIST,
            default_half_life=730,  # Very slow decay - weather patterns are stable
            similarity_weight=0.9,
            temporal_weight=0.1,
            base_learning_rate=0.03,
            memory_category_half_lives={
                'weather_impact_patterns': 1095,  # 3 years
                'stadium_specific_conditions': 1460,  # 4 years
                'team_adaptation_to_weather': 730
            }
        )

        # Additional experts with balanced configurations
        configs[ExpertType.VALUE_HUNTER] = TemporalDecayConfig(
            expert_type=ExpertType.VALUE_HUNTER,
            default_half_life=200,
            similarity_weight=0.6,
            temporal_weight=0.4,
            base_learning_rate=0.08,
            memory_category_half_lives={
                'value_identification_patterns': 180,
                'market_inefficiency_detection': 150,
                'contrarian_opportunities': 220
            }
        )

        configs[ExpertType.CHAOS_BELIEVER] = TemporalDecayConfig(
            expert_type=ExpertType.CHAOS_BELIEVER,
            default_half_life=100,
            similarity_weight=0.4,
            temporal_weight=0.6,
            base_learning_rate=0.20,  # High adaptability to chaos
            memory_category_half_lives={
                'chaos_theory_applications': 80,
                'unpredictable_outcomes': 60,
                'butterfly_effect_examples': 90
            }
        )

        configs[ExpertType.TREND_REVERSAL] = TemporalDecayConfig(
            expert_type=ExpertType.TREND_REVERSAL,
            default_half_life=160,
            similarity_weight=0.5,
            temporal_weight=0.5,
            base_learning_rate=0.12,
            memory_category_half_lives={
                'trend_reversal_signals': 120,
                'momentum_exhaustion_patterns': 140,
                'contrarian_timing': 180
            }
        )

        configs[ExpertType.NARRATIVE_FADER] = TemporalDecayConfig(
            expert_type=ExpertType.NARRATIVE_FADER,
            default_half_life=130,
            similarity_weight=0.5,
            temporal_weight=0.5,
            base_learning_rate=0.10,
            memory_category_half_lives={
                'narrative_fade_patterns': 100,
                'media_hype_cycles': 90,
                'public_perception_shifts': 150
            }
        )

        configs[ExpertType.UNDERDOG_CHAMPION] = TemporalDecayConfig(
            expert_type=ExpertType.UNDERDOG_CHAMPION,
            default_half_life=240,
            similarity_weight=0.6,
            temporal_weight=0.4,
            base_learning_rate=0.09,
            memory_category_half_lives={
                'underdog_success_patterns': 200,
                'upset_prediction_accuracy': 180,
                'value_in_underdogs': 260
            }
        )

        configs[ExpertType.CONSENSUS_FOLLOWER] = TemporalDecayConfig(
            expert_type=ExpertType.CONSENSUS_FOLLOWER,
            default_half_life=180,
            similarity_weight=0.7,
            temporal_weight=0.3,
            base_learning_rate=0.06,
            memory_category_half_lives={
                'consensus_accuracy_tracking': 200,
                'expert_agreement_patterns': 220,
                'crowd_wisdom_validation': 160
            }
        )

        configs[ExpertType.MARKET_EXPLOITER] = TemporalDecayConfig(
            expert_type=ExpertType.MARKET_EXPLOITER,
            default_half_life=150,
            similarity_weight=0.5,
            temporal_weight=0.5,
            base_learning_rate=0.11,
            memory_category_half_lives={
                'market_inefficiency_patterns': 120,
                'arbitrage_opportunities': 100,
                'pricing_error_detection': 140
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
        Calculate temporal decay score using exponential decay formula.

        Formula: 0.5^(age_days / half_life_days)

        Requirements: 5.1, 5.2
        """
        try:
            config = self.decay_configs.get(expert_type)
            if not config:
                logger.warning(f"No decay config for expert type: {expert_type}")
                return 0.5  # Default fallback

            # Get appropriate half-life
            if memory_category and memory_category in config.memory_category_half_lives:
                half_life = config.memory_category_half_lives[memory_category]
            else:
                half_life = config.default_half_life

            # Calculate exponential decay
            decay_score = math.pow(0.5, memory_age_days / half_life)

            return max(0.01, min(1.0, decay_score))  # Clamp between 0.01 and 1.0

        except Exception as e:
            logger.error(f"Error calculating temporal decay: {e}")
            return 0.5

    def calculate_combined_memory_score(
        self,
        expert_type: ExpertType,
        similarity_score: float,
        memory_age_days: int,
        memory_category: Optional[str] = None
    ) -> MemoryScore:
        """
        Calculate combined memory score using similarity and temporal decay.

        Requirements: 5.3, 8.3
        """
        try:
            config = self.decay_configs.get(expert_type)
            if not config:
                logger.warning(f"No decay config for expert type: {expert_type}")
                config = self.decay_configs[ExpertType.CONSERVATIVE_ANALYZER]  # Fallback

            # Calculate temporal decay
            temporal_decay_score = self.calculate_temporal_decay_score(
                expert_type, memory_age_days, memory_category
            )

            # Get half-life used
            if memory_category and memory_category in config.memory_category_half_lives:
                half_life_used = config.memory_category_half_lives[memory_category]
            else:
                half_life_used = config.default_half_life

            # Combine scores using expert-specific weights
            final_score = (
                similarity_score * config.similarity_weight +
                temporal_decay_score * config.temporal_weight
            )

            return MemoryScore(
                memory_id="",  # Will be set by caller
                similarity_score=similarity_score,
                temporal_decay_score=temporal_decay_score,
                final_score=final_score,
                days_old=memory_age_days,
                half_life_used=half_life_used,
                category=memory_category
            )

        except Exception as e:
            logger.error(f"Error calculating combined memory score: {e}")
            return MemoryScore("", similarity_score, 0.5, similarity_score * 0.5, memory_age_days, 365)

    def calculate_adjusted_learning_rate(
        self,
        expert_type: ExpertType,
        days_since_outcome: int
    ) -> float:
        """
        Calculate learning rate adjusted for outcome recency.
        More recent outcomes should have higher learning rates.

        Requirements: 5.6
        """
        try:
            config = self.decay_configs.get(expert_type)
            if not config:
                return 0.05  # Default learning rate

            base_rate = config.base_learning_rate

            # Apply temporal adjustment - more recent outcomes get higher learning rates
            temporal_multiplier = self.calculate_temporal_decay_score(
                expert_type, days_since_outcome
            )

            # Boost learning rate for recent outcomes
            adjusted_rate = base_rate * (0.5 + temporal_multiplier * 1.5)

            return max(0.01, min(0.25, adjusted_rate))  # Clamp between 1% and 25%

        except Exception as e:
            logger.error(f"Error calculating adjusted learning rate: {e}")
            return 0.05

    def rank_memories_by_relevance(
        self,
        expert_type: ExpertType,
        memories: List[Dict[str, Any]],
        current_date: Optional[datetime] = None
    ) -> List[MemoryScore]:
        """
        Rank memories by relevance using temporal decay and similarity.

        Requirements: 8.4
        """
        try:
            if current_date is None:
                current_date = datetime.now()

            scored_memories = []

            for memory in memories:
                # Calculate memory age
                created_at = memory.get('created_at')
                if isinstance(created_at, str):
                    try:
                        memory_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if memory_date.tzinfo is None:
                            memory_date = memory_date.replace(tzinfo=current_date.tzinfo)
                    except:
                        memory_date = current_date - timedelta(days=30)  # Default fallback
                elif isinstance(created_at, datetime):
                    memory_date = created_at
                else:
                    memory_date = current_date - timedelta(days=30)  # Default fallback

                days_old = (current_date - memory_date).days

                # Get similarity score
                similarity_score = memory.get('similarity_score', 0.5)

                # Get memory category
                memory_category = memory.get('memory_category') or memory.get('memory_type')

                # Calculate combined score
                score = self.calculate_combined_memory_score(
                    expert_type=expert_type,
                    similarity_score=similarity_score,
                    memory_age_days=days_old,
                    memory_category=memory_category
                )

                # Set memory ID
                score.memory_id = memory.get('memory_id', memory.get('id', ''))

                scored_memories.append(score)

            # Sort by final score (descending)
            scored_memories.sort(key=lambda x: x.final_score, reverse=True)

            return scored_memories

        except Exception as e:
            logger.error(f"Error ranking memories by relevance: {e}")
            return []

    def get_expert_decay_summary(self, expert_type: ExpertType) -> Dict[str, Any]:
        """Get summary of expert's decay configuration"""
        try:
            config = self.decay_configs.get(expert_type)
            if not config:
                return {}

            # Determine decay speed category
            if config.default_half_life < 100:
                decay_speed = "Very Fast"
            elif config.default_half_life < 200:
                decay_speed = "Fast"
            elif config.default_half_life < 300:
                decay_speed = "Moderate"
            elif config.default_half_life < 500:
                decay_speed = "Slow"
            else:
                decay_speed = "Very Slow"

            return {
                'expert_type': expert_type.value,
                'default_half_life_days': config.default_half_life,
                'decay_speed': decay_speed,
                'similarity_weight': config.similarity_weight,
                'temporal_weight': config.temporal_weight,
                'base_learning_rate': config.base_learning_rate,
                'category_specific_half_lives': config.memory_category_half_lives
            }

        except Exception as e:
            logger.error(f"Error getting expert decay summary: {e}")
            return {}

    def apply_temporal_filtering(
        self,
        expert_type: ExpertType,
        max_age_days: Optional[int] = None
    ) -> int:
        """
        Get maximum age for memory filtering to optimize performance.

        Requirements: 5.6 (performance optimization)
        """
        try:
            config = self.decay_configs.get(expert_type)
            if not config:
                return 365  # Default fallback

            if max_age_days is not None:
                return max_age_days

            # Use 3x half-life as cutoff (memory strength < 12.5%)
            cutoff_age = config.default_half_life * 3

            # Cap at reasonable limits
            return min(cutoff_age, 1095)  # Max 3 years

        except Exception as e:
            logger.error(f"Error applying temporal filtering: {e}")
            return 365

    def get_expert_type_from_id(self, expert_id: str) -> ExpertType:
        """Convert expert_id string to ExpertType enum"""
        try:
            # Direct mapping from expert_id to ExpertType
            for expert_type in ExpertType:
                if expert_type.value == expert_id:
                    return expert_type

            # Fallback mapping for common variations
            fallback_mapping = {
                'the_analyst': ExpertType.CONSERVATIVE_ANALYZER,
                'the_gambler': ExpertType.AGGRESSIVE_GAMBLER,
                'the_rider': ExpertType.MOMENTUM_TRACKER,
                'the_sharp': ExpertType.MARKET_READER,
                'the_hunter': ExpertType.VALUE_HUNTER,
                'the_chaos': ExpertType.CHAOS_BELIEVER,
                'the_reversal': ExpertType.TREND_REVERSAL,
                'the_fader': ExpertType.NARRATIVE_FADER,
                'the_underdog': ExpertType.UNDERDOG_CHAMPION,
                'the_consensus': ExpertType.CONSENSUS_FOLLOWER,
                'the_exploiter': ExpertType.MARKET_EXPLOITER
            }

            if expert_id in fallback_mapping:
                return fallback_mapping[expert_id]

            logger.warning(f"Unknown expert_id: {expert_id}, using conservative analyzer")
            return ExpertType.CONSERVATIVE_ANALYZER

        except Exception as e:
            logger.error(f"Error converting expert_id to ExpertType: {e}")
            return ExpertType.CONSERVATIVE_ANALYZER
