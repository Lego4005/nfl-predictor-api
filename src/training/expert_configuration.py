"""
Expert Configuration for NFL Prediction Training System

This module defines the fifteen expert agents with their personality-specific
temporal parameters and analytical focus factors.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from enum import Enum


class ExpertType(Enum):
    CHAOS_THEORY_BELIEVER = "chaos_theory_believer"
    CONSENSUS_FOLLOWER = "consensus_follower"
    CONSERVATIVE_ANALYZER = "conservative_analyzer"
    CONTRARIAN_REBEL = "contrarian_rebel"
    FUNDAMENTALIST_SCHOLAR = "fundamentalist_scholar"
    GUT_INSTINCT_EXPERT = "gut_instinct_expert"
    MARKET_INEFFICIENCY_EXPLOITER = "market_inefficiency_exploiter"
    MOMENTUM_RIDER = "momentum_rider"
    POPULAR_NARRATIVE_FADER = "popular_narrative_fader"
    RISK_TAKING_GAMBLER = "risk_taking_gambler"
    SHARP_MONEY_FOLLOWER = "sharp_money_follower"
    STATISTICS_PURIST = "statistics_purist"
    TREND_REVERSAL_SPECIALIST = "trend_reversal_specialist"
    UNDERDOG_CHAMPION = "underdog_champion"
    VALUE_HUNTER = "value_hunter"


@dataclass
class ExpertConfiguration:
    """Complete configuration for an expert agent"""
    expert_type: ExpertType
    name: str
    description: str

    # Temporal parameters
    temporal_half_life_days: int
    similarity_weight: float  # 0-1, how much to weight similarity vs recency
    temporal_weight: float    # 0-1, how much to weight recency vs similarity

    # Analytical focus factors (weights 0-1)
    analytical_focus: Dict[str, float]

    # Memory retrieval configuration
    max_reasoning_memories: int = 5
    max_contextual_memories: int = 3
    max_market_memories: int = 3
    max_learning_memories: int = 2

    # Belief revision parameters
    base_learning_rate: float = 0.1
    confidence_threshold: float = 0.6
    decision_making_style: str = "analytical"

    # Performance tracking
    specialization_contexts: List[str] = None


class ExpertConfigurationManager:
    """Manages configuration for all fifteen expert agents"""

    def __init__(self):
        self.configurations = self._initialize_expert_configurations()

    def _initialize_expert_configurations(self) -> Dict[ExpertType, ExpertConfiguration]:
        """Initialize all fifteen expert configurations with personality-specific parameters"""

        configs = {}

        # 1. Chaos Theory Believer - Embraces unpredictability and randomness
        configs[ExpertType.CHAOS_THEORY_BELIEVER] = ExpertConfiguration(
            expert_type=ExpertType.CHAOS_THEORY_BELIEVER,
            name="The Chaos",
            description="Believes in unpredictability and embraces chaotic market dynamics",
            temporal_half_life_days=60,  # Short memory, chaos changes quickly
            similarity_weight=0.30,  # Low similarity weight - chaos is unique
            temporal_weight=0.70,    # High recency weight - recent chaos matters most
            analytical_focus={
                'chaos_indicators': 0.95,
                'market_volatility': 0.9,
                'unexpected_events': 0.85,
                'contrarian_opportunities': 0.9,
                'upset_potential': 0.8,
                'team_quality_metrics': 0.2,
                'historical_patterns': 0.1,
                'statistical_trends': 0.2,
                'consensus_predictions': 0.1,
                'market_efficiency': 0.1
            },
            specialization_contexts=['upset_scenarios', 'volatile_games', 'unpredictable_matchups']
        )

        # 2. Consensus Follower - Follows market consensus and popular opinion
        configs[ExpertType.CONSENSUS_FOLLOWER] = ExpertConfiguration(
            expert_type=ExpertType.CONSENSUS_FOLLOWER,
            name="The Consensus",
            description="Follows market consensus and popular betting patterns",
            temporal_half_life_days=180,
            similarity_weight=0.70,
            temporal_weight=0.30,
            analytical_focus={
                'market_consensus': 0.8,
                'public_betting_patterns': 0.8,
                'popular_narratives': 0.6,
                'expert_predictions': 0.7,
                'team_quality_metrics': 0.6,
                'historical_patterns': 0.5,
                'statistical_trends': 0.6,
                'contrarian_opportunities': 0.05,
                'chaos_indicators': 0.2,
                'upset_potential': 0.3
            },
            specialization_contexts=['consensus_plays', 'popular_picks', 'safe_bets']
        )

        # 3. Conservative Analyzer - Methodical, analytics-focused approach
        configs[ExpertType.CONSERVATIVE_ANALYZER] = ExpertConfiguration(
            expert_type=ExpertType.CONSERVATIVE_ANALYZER,
            name="The Analyst",
            description="Methodical analyst who trusts data and avoids high-risk plays",
            temporal_half_life_days=450,
            similarity_weight=0.80,
            temporal_weight=0.20,
            analytical_focus={
                'team_quality_metrics': 0.9,
                'statistical_trends': 0.9,
                'historical_patterns': 0.8,
                'market_efficiency': 0.8,
                'value_opportunities': 0.6,
                'analytical_models': 0.9,
                'data_driven_insights': 0.9,
                'contrarian_opportunities': 0.1,
                'chaos_indicators': 0.2,
                'gut_feelings': 0.1
            },
            specialization_contexts=['data_rich_games', 'statistical_edges', 'proven_systems']
        )

        # 4. Contrarian Rebel - Anti-establishment, contrarian approach
        configs[ExpertType.CONTRARIAN_REBEL] = ExpertConfiguration(
            expert_type=ExpertType.CONTRARIAN_REBEL,
            name="The Rebel",
            description="Anti-establishment contrarian who fades popular opinion",
            temporal_half_life_days=120,
            similarity_weight=0.60,
            temporal_weight=0.40,
            analytical_focus={
                'contrarian_opportunities': 0.95,
                'public_betting_bias': 0.9,
                'media_narrative_fading': 0.8,
                'market_overreactions': 0.7,
                'value_opportunities': 0.7,
                'chaos_indicators': 0.8,
                'upset_potential': 0.6,
                'consensus_predictions': 0.2,
                'popular_narratives': 0.2,
                'team_quality_metrics': 0.4
            },
            specialization_contexts=['contrarian_plays', 'fade_public', 'anti_narrative']
        )

        # 5. Fundamentalist Scholar - Research-driven, deep analysis
        configs[ExpertType.FUNDAMENTALIST_SCHOLAR] = ExpertConfiguration(
            expert_type=ExpertType.FUNDAMENTALIST_SCHOLAR,
            name="The Scholar",
            description="Research-driven analyst who dives deep into fundamentals",
            temporal_half_life_days=600,
            similarity_weight=0.85,
            temporal_weight=0.15,
            analytical_focus={
                'analytical_models': 0.95,
                'statistical_trends': 0.9,
                'historical_patterns': 0.9,
                'team_quality_metrics': 0.8,
                'value_opportunities': 0.8,
                'market_efficiency': 0.7,
                'data_driven_insights': 0.95,
                'gut_feelings': 0.1,
                'chaos_indicators': 0.1,
                'contrarian_opportunities': 0.2
            },
            specialization_contexts=['research_heavy', 'fundamental_analysis', 'deep_dives']
        )

        # 6. Gut Instinct Expert - Intuitive, feeling-based decisions
        configs[ExpertType.GUT_INSTINCT_EXPERT] = ExpertConfiguration(
            expert_type=ExpertType.GUT_INSTINCT_EXPERT,
            name="The Intuition",
            description="Intuitive expert who trusts gut feelings over data",
            temporal_half_life_days=30,
            similarity_weight=0.20,
            temporal_weight=0.80,
            analytical_focus={
                'gut_feelings': 0.9,
                'intuitive_reads': 0.85,
                'emotional_factors': 0.7,
                'chaos_indicators': 0.8,
                'upset_potential': 0.6,
                'momentum_shifts': 0.5,
                'analytical_models': 0.1,
                'statistical_trends': 0.1,
                'market_efficiency': 0.3,
                'data_driven_insights': 0.1
            },
            specialization_contexts=['gut_plays', 'intuitive_spots', 'feeling_based']
        )

        # 7. Market Inefficiency Exploiter - Seeks market edges and value
        configs[ExpertType.MARKET_INEFFICIENCY_EXPLOITER] = ExpertConfiguration(
            expert_type=ExpertType.MARKET_INEFFICIENCY_EXPLOITER,
            name="The Exploiter",
            description="Seeks and exploits market inefficiencies for value",
            temporal_half_life_days=90,
            similarity_weight=0.50,
            temporal_weight=0.50,
            analytical_focus={
                'market_inefficiencies': 0.98,
                'value_opportunities': 0.95,
                'line_movement_analysis': 0.9,
                'sharp_money_indicators': 0.9,
                'market_timing': 0.8,
                'analytical_models': 0.9,
                'contrarian_opportunities': 0.7,
                'statistical_edges': 0.8,
                'consensus_predictions': 0.5,
                'gut_feelings': 0.2
            },
            specialization_contexts=['market_edges', 'value_hunting', 'inefficiency_spots']
        )

        # 8. Momentum Rider - Follows trends and hot streaks
        configs[ExpertType.MOMENTUM_RIDER] = ExpertConfiguration(
            expert_type=ExpertType.MOMENTUM_RIDER,
            name="The Rider",
            description="Rides momentum and follows trending teams",
            temporal_half_life_days=45,
            similarity_weight=0.40,
            temporal_weight=0.60,
            analytical_focus={
                'momentum_indicators': 0.8,
                'trending_teams': 0.7,
                'recent_performance': 0.8,
                'hot_streaks': 0.8,
                'market_momentum': 0.6,
                'team_confidence': 0.7,
                'value_opportunities': 0.4,
                'contrarian_opportunities': 0.2,
                'historical_patterns': 0.4,
                'statistical_trends': 0.5
            },
            specialization_contexts=['momentum_plays', 'trending_teams', 'hot_streaks']
        )

        # 9. Popular Narrative Fader - Fades popular stories and narratives
        configs[ExpertType.POPULAR_NARRATIVE_FADER] = ExpertConfiguration(
            expert_type=ExpertType.POPULAR_NARRATIVE_FADER,
            name="The Fader",
            description="Fades popular narratives and media storylines",
            temporal_half_life_days=150,
            similarity_weight=0.65,
            temporal_weight=0.35,
            analytical_focus={
                'narrative_fading': 0.9,
                'media_overreaction': 0.85,
                'contrarian_opportunities': 0.9,
                'public_betting_bias': 0.7,
                'value_opportunities': 0.7,
                'analytical_models': 0.6,
                'chaos_indicators': 0.7,
                'popular_narratives': 0.2,
                'consensus_predictions': 0.2,
                'market_efficiency': 0.5
            },
            specialization_contexts=['narrative_fades', 'media_contrarian', 'story_fading']
        )

        # 10. Risk Taking Gambler - High-risk, high-reward approach
        configs[ExpertType.RISK_TAKING_GAMBLER] = ExpertConfiguration(
            expert_type=ExpertType.RISK_TAKING_GAMBLER,
            name="The Gambler",
            description="High-risk gambler who chases big payouts",
            temporal_half_life_days=30,
            similarity_weight=0.30,
            temporal_weight=0.70,
            analytical_focus={
                'high_risk_plays': 0.9,
                'upset_potential': 0.9,
                'chaos_indicators': 0.9,
                'contrarian_opportunities': 0.7,
                'gut_feelings': 0.8,
                'big_payout_potential': 0.85,
                'market_inefficiencies': 0.5,
                'analytical_models': 0.3,
                'conservative_plays': 0.2,
                'statistical_trends': 0.3
            },
            specialization_contexts=['high_risk', 'upset_hunting', 'big_payouts']
        )

        # 11. Sharp Money Follower - Follows professional betting patterns
        configs[ExpertType.SHARP_MONEY_FOLLOWER] = ExpertConfiguration(
            expert_type=ExpertType.SHARP_MONEY_FOLLOWER,
            name="The Sharp",
            description="Follows sharp money and professional betting patterns",
            temporal_half_life_days=120,
            similarity_weight=0.60,
            temporal_weight=0.40,
            analytical_focus={
                'sharp_money_indicators': 0.95,
                'professional_patterns': 0.9,
                'line_movement_analysis': 0.9,
                'market_efficiency': 0.8,
                'value_opportunities': 0.8,
                'analytical_models': 0.8,
                'statistical_trends': 0.7,
                'contrarian_opportunities': 0.3,
                'public_betting_bias': 0.5,
                'gut_feelings': 0.2
            },
            specialization_contexts=['sharp_plays', 'professional_spots', 'smart_money']
        )

        # 12. Statistics Purist - Pure mathematical approach
        configs[ExpertType.STATISTICS_PURIST] = ExpertConfiguration(
            expert_type=ExpertType.STATISTICS_PURIST,
            name="The Quant",
            description="Pure mathematical analyst focused on statistical models",
            temporal_half_life_days=365,
            similarity_weight=0.80,
            temporal_weight=0.20,
            analytical_focus={
                'statistical_models': 0.98,
                'mathematical_analysis': 0.95,
                'data_driven_insights': 0.95,
                'analytical_models': 0.9,
                'team_quality_metrics': 0.85,
                'market_efficiency': 0.8,
                'historical_patterns': 0.8,
                'gut_feelings': 0.05,
                'chaos_indicators': 0.05,
                'emotional_factors': 0.1
            },
            specialization_contexts=['statistical_edges', 'mathematical_models', 'pure_quant']
        )

        # 13. Trend Reversal Specialist - Identifies trend reversals and mean reversion
        configs[ExpertType.TREND_REVERSAL_SPECIALIST] = ExpertConfiguration(
            expert_type=ExpertType.TREND_REVERSAL_SPECIALIST,
            name="The Reversal",
            description="Specializes in identifying trend reversals and mean reversion",
            temporal_half_life_days=180,
            similarity_weight=0.70,
            temporal_weight=0.30,
            analytical_focus={
                'trend_reversal_indicators': 0.8,
                'mean_reversion_signals': 0.8,
                'overextended_trends': 0.75,
                'value_opportunities': 0.8,
                'contrarian_opportunities': 0.8,
                'analytical_models': 0.7,
                'statistical_trends': 0.7,
                'momentum_indicators': 0.5,
                'trending_teams': 0.4,
                'hot_streaks': 0.3
            },
            specialization_contexts=['reversal_spots', 'mean_reversion', 'trend_breaks']
        )

        # 14. Underdog Champion - Champions underdogs and upset scenarios
        configs[ExpertType.UNDERDOG_CHAMPION] = ExpertConfiguration(
            expert_type=ExpertType.UNDERDOG_CHAMPION,
            name="The Underdog",
            description="Champions underdogs and seeks upset scenarios",
            temporal_half_life_days=90,
            similarity_weight=0.50,
            temporal_weight=0.50,
            analytical_focus={
                'underdog_value': 0.9,
                'upset_potential': 0.9,
                'value_opportunities': 0.9,
                'contrarian_opportunities': 0.8,
                'chaos_indicators': 0.9,
                'big_payout_potential': 0.85,
                'gut_feelings': 0.6,
                'analytical_models': 0.4,
                'consensus_predictions': 0.3,
                'popular_narratives': 0.3
            },
            specialization_contexts=['underdog_spots', 'upset_scenarios', 'david_vs_goliath']
        )

        # 15. Value Hunter - Seeks value in all betting markets
        configs[ExpertType.VALUE_HUNTER] = ExpertConfiguration(
            expert_type=ExpertType.VALUE_HUNTER,
            name="The Hunter",
            description="Relentlessly hunts for value across all betting markets",
            temporal_half_life_days=150,
            similarity_weight=0.65,
            temporal_weight=0.35,
            analytical_focus={
                'value_opportunities': 0.95,
                'market_inefficiencies': 0.9,
                'line_value_analysis': 0.85,
                'analytical_models': 0.8,
                'statistical_trends': 0.8,
                'contrarian_opportunities': 0.6,
                'sharp_money_indicators': 0.7,
                'market_efficiency': 0.9,
                'consensus_predictions': 0.4,
                'gut_feelings': 0.3
            },
            specialization_contexts=['value_plays', 'market_hunting', 'edge_seeking']
        )

        return configs

    def get_configuration(self, expert_type: ExpertType) -> ExpertConfiguration:
        """Get configuration for a specific expert type"""
        return self.configurations.get(expert_type)

    def get_all_configurations(self) -> Dict[ExpertType, ExpertConfiguration]:
        """Get all expert configurations"""
        return self.configurations

    def get_seasonal_adjusted_half_life(
        self,
        expert_type: ExpertType,
        current_week: int,
        data_richness_score: float = 0.5
    ) -> int:
        """
        Get seasonally adjusted half-life for an expert based on current week and data availability

        Args:
            expert_type: The expert type
            current_week: Current week of season (1-18)
            data_richness_score: How much current season data is available (0-1)

        Returns:
            Adjusted half-life in days
        """
        config = self.get_configuration(expert_type)
        if not config:
            return 365  # Default fallback

        base_half_life = config.temporal_half_life_days

        # Early season (weeks 1-4): Extend half-lives by 25-50%
        if current_week <= 4:
            adjustment_factor = 1.25 + (0.25 * (4 - current_week) / 4)
        # Late season (weeks 13+): Reduce half-lives by 10-25% based on data richness
        elif current_week >= 13:
            reduction = 0.1 + (0.15 * data_richness_score)
            adjustment_factor = 1.0 - reduction
        # Mid season: Minor adjustments based on volatility
        else:
            adjustment_factor = 1.0  # Standard half-life

        return int(base_half_life * adjustment_factor)

    def validate_configurations(self) -> Dict[str, Any]:
        """Validate all expert configurations and return summary"""

        validation_results = {
            'total_experts': len(self.configurations),
            'weight_validation': {},
            'focus_validation': {},
            'temporal_range': {},
            'errors': []
        }

        for expert_type, config in self.configurations.items():
            expert_name = expert_type.value

            # Validate similarity + temporal weights sum to 1.0
            weight_sum = config.similarity_weight + config.temporal_weight
            if abs(weight_sum - 1.0) > 0.01:
                validation_results['errors'].append(
                    f"{expert_name}: Similarity + temporal weights = {weight_sum:.3f}, should be 1.0"
                )

            validation_results['weight_validation'][expert_name] = {
                'similarity_weight': config.similarity_weight,
                'temporal_weight': config.temporal_weight,
                'sum': weight_sum
            }

            # Validate analytical focus weights are reasonable (0-1)
            invalid_focus = {k: v for k, v in config.analytical_focus.items() if v < 0 or v > 1}
            if invalid_focus:
                validation_results['errors'].append(
                    f"{expert_name}: Invalid focus weights: {invalid_focus}"
                )

            validation_results['focus_validation'][expert_name] = {
                'total_factors': len(config.analytical_focus),
                'high_focus_factors': [k for k, v in config.analytical_focus.items() if v >= 0.8],
                'low_focus_factors': [k for k, v in config.analytical_focus.items() if v <= 0.3]
            }

            validation_results['temporal_range'][expert_name] = {
                'half_life_days': config.temporal_half_life_days,
                'similarity_weight': config.similarity_weight,
                'temporal_weight': config.temporal_weight
            }

        return validation_results
