"""
Expert ID Adapter - Handles mapping between database and model expert IDs

The database currently uses old expert IDs (the_analyst, the_gambler, etc.)
Our models use new expert IDs (conservative_analyzer, risk_taking_gambler, etc.)

This adapter provides bidirectional mapping until the database migration is complete.
"""

# Mapping from NEW (model) IDs to OLD (database) IDs
MODEL_TO_DB = {
    'conservative_analyzer': 'the_analyst',
    'risk_taking_gambler': 'the_gambler',
    'contrarian_rebel': 'the_contrarian',
    'value_hunter': 'the_upset_specialist',  # Best match available
    'momentum_rider': 'the_momentum_rider',
    'fundamentalist_scholar': 'the_matchup_expert',
    'chaos_theory_believer': 'the_chaos_theorist',
    'gut_instinct_expert': 'the_injury_tracker',
    'statistics_purist': 'the_referee_reader',
    'trend_reversal_specialist': 'the_primetime_prophet',
    'popular_narrative_fader': 'the_home_field_guru',
    'sharp_money_follower': 'the_playoff_predictor',
    'underdog_champion': 'the_upset_specialist',
    'consensus_follower': 'the_divisional_detective',
    'market_inefficiency_exploiter': 'the_analyst',  # No direct match, using analyst
}

# Reverse mapping from OLD (database) IDs to NEW (model) IDs
DB_TO_MODEL = {
    'the_analyst': 'conservative_analyzer',
    'the_veteran': 'conservative_analyzer',
    'the_gambler': 'risk_taking_gambler',
    'the_contrarian': 'contrarian_rebel',
    'the_momentum_rider': 'momentum_rider',
    'the_matchup_expert': 'fundamentalist_scholar',
    'the_chaos_theorist': 'chaos_theory_believer',
    'the_weather_watcher': 'chaos_theory_believer',
    'the_injury_tracker': 'gut_instinct_expert',
    'the_referee_reader': 'statistics_purist',
    'the_primetime_prophet': 'trend_reversal_specialist',
    'the_upset_specialist': 'underdog_champion',
    'the_home_field_guru': 'popular_narrative_fader',
    'the_divisional_detective': 'consensus_follower',
    'the_playoff_predictor': 'sharp_money_follower',
}


def model_id_to_db_id(model_id: str) -> str:
    """Convert model expert ID to database expert ID"""
    return MODEL_TO_DB.get(model_id, model_id)


def db_id_to_model_id(db_id: str) -> str:
    """Convert database expert ID to model expert ID"""
    return DB_TO_MODEL.get(db_id, db_id)


def get_available_db_experts():
    """Get list of expert IDs that exist in database"""
    return list(DB_TO_MODEL.keys())


def get_model_experts():
    """Get list of expert IDs used by models"""
    return list(MODEL_TO_DB.keys())