"""
Expert Prediction Models - Complete 15-Expert Council

Maps to frontend expertPersonalities.ts definitions.
All experts use rule-based logic (will upgrade to ML later).
"""

from .base_model import BaseExpertModel, Prediction

# Core 4 experts (detailed implementations)
from .analyst_model import AnalystModel
from .gambler_model import GamblerModel
from .contrarian_model import ContrarianModel
from .gut_instinct_model import GutInstinctModel

# Remaining 11 experts
from .all_15_experts import (
    HunterModel,
    RiderModel,
    ScholarModel,
    ChaosModel,
    QuantModel,
    ReversalModel,
    FaderModel,
    SharpModel,
    UnderdogModel,
    ConsensusModel,
    ExploiterModel
)

# Export all 15 experts
__all__ = [
    'BaseExpertModel',
    'Prediction',
    # The complete 15-expert council
    'AnalystModel',        # 1. conservative_analyzer
    'GamblerModel',        # 2. risk_taking_gambler
    'ContrarianModel',     # 3. contrarian_rebel
    'HunterModel',         # 4. value_hunter
    'RiderModel',          # 5. momentum_rider
    'ScholarModel',        # 6. fundamentalist_scholar
    'ChaosModel',          # 7. chaos_theory_believer
    'GutInstinctModel',    # 8. gut_instinct_expert (The Intuition)
    'QuantModel',          # 9. statistics_purist
    'ReversalModel',       # 10. trend_reversal_specialist
    'FaderModel',          # 11. popular_narrative_fader
    'SharpModel',          # 12. sharp_money_follower
    'UnderdogModel',       # 13. underdog_champion
    'ConsensusModel',      # 14. consensus_follower
    'ExploiterModel',      # 15. market_inefficiency_exploiter
]

# Expert ID to model class mapping
EXPERT_MODELS = {
    'conservative_analyzer': AnalystModel,
    'risk_taking_gambler': GamblerModel,
    'contrarian_rebel': ContrarianModel,
    'value_hunter': HunterModel,
    'momentum_rider': RiderModel,
    'fundamentalist_scholar': ScholarModel,
    'chaos_theory_believer': ChaosModel,
    'gut_instinct_expert': GutInstinctModel,
    'statistics_purist': QuantModel,
    'trend_reversal_specialist': ReversalModel,
    'popular_narrative_fader': FaderModel,
    'sharp_money_follower': SharpModel,
    'underdog_champion': UnderdogModel,
    'consensus_follower': ConsensusModel,
    'market_inefficiency_exploiter': ExploiterModel,
}

def get_expert_model(expert_id: str) -> BaseExpertModel:
    """Get expert model instance by ID"""
    model_class = EXPERT_MODELS.get(expert_id)
    if not model_class:
        raise ValueError(f"Unknown expert_id: {expert_id}")
    return model_class()