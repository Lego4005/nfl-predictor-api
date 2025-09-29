-- Migration: Expert Naming System Standardization
-- Purpose: Standardize expert IDs and names across all system components
-- Target: Align database, frontend, and ML models to use consistent expert identities
-- Date: 2025-01-16

-- ============================================================================
-- PHASE 1: DATA BACKUP AND MIGRATION PREPARATION
-- ============================================================================

-- Create backup table for existing expert data
CREATE TABLE IF NOT EXISTS personality_experts_backup AS 
SELECT * FROM personality_experts;

-- Create mapping table for expert ID migration
CREATE TABLE expert_id_migration_mapping (
    old_expert_id TEXT PRIMARY KEY,
    new_expert_id TEXT NOT NULL,
    old_name TEXT,
    new_name TEXT,
    personality_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert expert ID mappings based on design document
INSERT INTO expert_id_migration_mapping (old_expert_id, new_expert_id, old_name, new_name, personality_type) VALUES
-- Core personality-based experts (correct mapping)
('the_analyst', 'conservative_analyzer', 'The Analyst', 'The Analyst', 'conservative'),
('the_veteran', 'conservative_analyzer', 'The Veteran', 'The Analyst', 'conservative'),
('the_gambler', 'risk_taking_gambler', 'The Gambler', 'The Gambler', 'risk_taking'),
('the_contrarian', 'contrarian_rebel', 'The Contrarian', 'The Rebel', 'contrarian'),
('the_momentum_rider', 'momentum_rider', 'The Momentum Rider', 'The Rider', 'momentum'),
('the_matchup_expert', 'fundamentalist_scholar', 'The Matchup Expert', 'The Scholar', 'fundamentalist'),
('the_chaos_theorist', 'chaos_theory_believer', 'The Chaos Theorist', 'The Chaos', 'randomness'),
('the_weather_watcher', 'chaos_theory_believer', 'The Weather Watcher', 'The Chaos', 'randomness'),
('the_injury_tracker', 'gut_instinct_expert', 'The Injury Tracker', 'The Intuition', 'gut_feel'),
('the_referee_reader', 'statistics_purist', 'The Referee Reader', 'The Quant', 'statistics'),
('the_primetime_prophet', 'trend_reversal_specialist', 'The Primetime Prophet', 'The Reversal', 'mean_reversion'),
('the_upset_specialist', 'underdog_champion', 'The Upset Specialist', 'The Underdog', 'upset_seeker'),
('the_home_field_guru', 'popular_narrative_fader', 'The Home Field Guru', 'The Fader', 'anti_narrative'),
('the_balanced_mind', 'sharp_money_follower', 'The Balanced Mind', 'The Sharp', 'smart_money'),
('the_division_expert', 'consensus_follower', 'The Division Expert', 'The Consensus', 'crowd_following');

-- Add new experts not in old system
INSERT INTO expert_id_migration_mapping (old_expert_id, new_expert_id, old_name, new_name, personality_type) VALUES
('new_expert_1', 'value_hunter', NULL, 'The Hunter', 'value_seeking'),
('new_expert_2', 'market_inefficiency_exploiter', NULL, 'The Exploiter', 'inefficiency_hunting');

-- ============================================================================
-- PHASE 2: UPDATE EXISTING EXPERT RECORDS
-- ============================================================================

-- Update personality_experts table with standardized IDs and personality traits
UPDATE personality_experts pe
SET 
    expert_id = m.new_expert_id,
    name = m.new_name,
    personality_traits = CASE m.new_expert_id
        WHEN 'conservative_analyzer' THEN jsonb_build_object(
            'risk_tolerance', 0.2,
            'analytics_trust', 0.9,
            'contrarian_tendency', 0.1,
            'optimism', 0.4,
            'chaos_comfort', 0.2,
            'confidence_level', 0.7,
            'market_trust', 0.8,
            'value_seeking', 0.6
        )
        WHEN 'risk_taking_gambler' THEN jsonb_build_object(
            'risk_tolerance', 0.9,
            'analytics_trust', 0.3,
            'contrarian_tendency', 0.7,
            'optimism', 0.8,
            'chaos_comfort', 0.9,
            'confidence_level', 0.8,
            'market_trust', 0.2,
            'value_seeking', 0.5
        )
        WHEN 'contrarian_rebel' THEN jsonb_build_object(
            'risk_tolerance', 0.6,
            'analytics_trust', 0.4,
            'contrarian_tendency', 0.95,
            'optimism', 0.3,
            'chaos_comfort', 0.8,
            'confidence_level', 0.6,
            'market_trust', 0.2,
            'value_seeking', 0.7
        )
        WHEN 'value_hunter' THEN jsonb_build_object(
            'risk_tolerance', 0.4,
            'analytics_trust', 0.8,
            'contrarian_tendency', 0.6,
            'optimism', 0.5,
            'chaos_comfort', 0.3,
            'confidence_level', 0.7,
            'market_trust', 0.9,
            'value_seeking', 0.95
        )
        WHEN 'momentum_rider' THEN jsonb_build_object(
            'risk_tolerance', 0.7,
            'analytics_trust', 0.5,
            'contrarian_tendency', 0.2,
            'optimism', 0.8,
            'chaos_comfort', 0.6,
            'confidence_level', 0.8,
            'market_trust', 0.6,
            'value_seeking', 0.4
        )
        WHEN 'fundamentalist_scholar' THEN jsonb_build_object(
            'risk_tolerance', 0.3,
            'analytics_trust', 0.95,
            'contrarian_tendency', 0.2,
            'optimism', 0.6,
            'chaos_comfort', 0.1,
            'confidence_level', 0.9,
            'market_trust', 0.7,
            'value_seeking', 0.8
        )
        WHEN 'chaos_theory_believer' THEN jsonb_build_object(
            'risk_tolerance', 0.8,
            'analytics_trust', 0.2,
            'contrarian_tendency', 0.9,
            'optimism', 0.5,
            'chaos_comfort', 0.95,
            'confidence_level', 0.4,
            'market_trust', 0.1,
            'value_seeking', 0.3
        )
        WHEN 'gut_instinct_expert' THEN jsonb_build_object(
            'risk_tolerance', 0.6,
            'analytics_trust', 0.1,
            'contrarian_tendency', 0.4,
            'optimism', 0.7,
            'chaos_comfort', 0.8,
            'confidence_level', 0.9,
            'market_trust', 0.3,
            'value_seeking', 0.5
        )
        WHEN 'statistics_purist' THEN jsonb_build_object(
            'risk_tolerance', 0.2,
            'analytics_trust', 0.98,
            'contrarian_tendency', 0.1,
            'optimism', 0.5,
            'chaos_comfort', 0.05,
            'confidence_level', 0.8,
            'market_trust', 0.9,
            'value_seeking', 0.6
        )
        WHEN 'trend_reversal_specialist' THEN jsonb_build_object(
            'risk_tolerance', 0.5,
            'analytics_trust', 0.7,
            'contrarian_tendency', 0.8,
            'optimism', 0.4,
            'chaos_comfort', 0.6,
            'confidence_level', 0.7,
            'market_trust', 0.5,
            'value_seeking', 0.8
        )
        WHEN 'popular_narrative_fader' THEN jsonb_build_object(
            'risk_tolerance', 0.6,
            'analytics_trust', 0.6,
            'contrarian_tendency', 0.9,
            'optimism', 0.3,
            'chaos_comfort', 0.7,
            'confidence_level', 0.8,
            'market_trust', 0.2,
            'value_seeking', 0.7
        )
        WHEN 'sharp_money_follower' THEN jsonb_build_object(
            'risk_tolerance', 0.5,
            'analytics_trust', 0.8,
            'contrarian_tendency', 0.3,
            'optimism', 0.6,
            'chaos_comfort', 0.4,
            'confidence_level', 0.9,
            'market_trust', 0.95,
            'value_seeking', 0.8
        )
        WHEN 'underdog_champion' THEN jsonb_build_object(
            'risk_tolerance', 0.9,
            'analytics_trust', 0.4,
            'contrarian_tendency', 0.8,
            'optimism', 0.9,
            'chaos_comfort', 0.9,
            'confidence_level', 0.6,
            'market_trust', 0.3,
            'value_seeking', 0.9
        )
        WHEN 'consensus_follower' THEN jsonb_build_object(
            'risk_tolerance', 0.3,
            'analytics_trust', 0.6,
            'contrarian_tendency', 0.05,
            'optimism', 0.6,
            'chaos_comfort', 0.2,
            'confidence_level', 0.5,
            'market_trust', 0.8,
            'value_seeking', 0.4
        )
        WHEN 'market_inefficiency_exploiter' THEN jsonb_build_object(
            'risk_tolerance', 0.7,
            'analytics_trust', 0.9,
            'contrarian_tendency', 0.7,
            'optimism', 0.5,
            'chaos_comfort', 0.5,
            'confidence_level', 0.8,
            'market_trust', 0.95,
            'value_seeking', 0.98
        )
        ELSE pe.personality_traits
    END,
    decision_style = CASE m.new_expert_id
        WHEN 'conservative_analyzer' THEN 'methodical'
        WHEN 'risk_taking_gambler' THEN 'aggressive'
        WHEN 'contrarian_rebel' THEN 'contrarian'
        WHEN 'value_hunter' THEN 'value_focused'
        WHEN 'momentum_rider' THEN 'trend_following'
        WHEN 'fundamentalist_scholar' THEN 'research_driven'
        WHEN 'chaos_theory_believer' THEN 'chaotic'
        WHEN 'gut_instinct_expert' THEN 'intuitive'
        WHEN 'statistics_purist' THEN 'mathematical'
        WHEN 'trend_reversal_specialist' THEN 'mean_reversion'
        WHEN 'popular_narrative_fader' THEN 'anti_narrative'
        WHEN 'sharp_money_follower' THEN 'professional'
        WHEN 'underdog_champion' THEN 'upset_seeking'
        WHEN 'consensus_follower' THEN 'consensus_driven'
        WHEN 'market_inefficiency_exploiter' THEN 'edge_seeking'
        ELSE pe.decision_style
    END,
    learning_rate = CASE m.new_expert_id
        WHEN 'conservative_analyzer' THEN 0.03
        WHEN 'risk_taking_gambler' THEN 0.08
        WHEN 'contrarian_rebel' THEN 0.06
        WHEN 'value_hunter' THEN 0.04
        WHEN 'momentum_rider' THEN 0.07
        WHEN 'fundamentalist_scholar' THEN 0.02
        WHEN 'chaos_theory_believer' THEN 0.12
        WHEN 'gut_instinct_expert' THEN 0.09
        WHEN 'statistics_purist' THEN 0.03
        WHEN 'trend_reversal_specialist' THEN 0.05
        WHEN 'popular_narrative_fader' THEN 0.06
        WHEN 'sharp_money_follower' THEN 0.04
        WHEN 'underdog_champion' THEN 0.08
        WHEN 'consensus_follower' THEN 0.04
        WHEN 'market_inefficiency_exploiter' THEN 0.05
        ELSE pe.learning_rate
    END,
    updated_at = NOW()
FROM expert_id_migration_mapping m
WHERE pe.expert_id = m.old_expert_id;

-- ============================================================================
-- PHASE 3: INSERT MISSING EXPERTS (IF ANY)
-- ============================================================================

-- Insert any missing experts from the standardized 15-expert framework
INSERT INTO personality_experts (expert_id, name, personality_traits, decision_style, learning_rate)
SELECT 
    new_expert_id,
    new_name,
    CASE new_expert_id
        WHEN 'value_hunter' THEN jsonb_build_object(
            'risk_tolerance', 0.4,
            'analytics_trust', 0.8,
            'contrarian_tendency', 0.6,
            'optimism', 0.5,
            'chaos_comfort', 0.3,
            'confidence_level', 0.7,
            'market_trust', 0.9,
            'value_seeking', 0.95
        )
        WHEN 'market_inefficiency_exploiter' THEN jsonb_build_object(
            'risk_tolerance', 0.7,
            'analytics_trust', 0.9,
            'contrarian_tendency', 0.7,
            'optimism', 0.5,
            'chaos_comfort', 0.5,
            'confidence_level', 0.8,
            'market_trust', 0.95,
            'value_seeking', 0.98
        )
    END,
    CASE new_expert_id
        WHEN 'value_hunter' THEN 'value_focused'
        WHEN 'market_inefficiency_exploiter' THEN 'edge_seeking'
    END,
    CASE new_expert_id
        WHEN 'value_hunter' THEN 0.04
        WHEN 'market_inefficiency_exploiter' THEN 0.05
    END
FROM expert_id_migration_mapping m
WHERE m.old_expert_id LIKE 'new_expert_%'
ON CONFLICT (expert_id) DO NOTHING;

-- ============================================================================
-- PHASE 4: UPDATE RELATED TABLES WITH NEW EXPERT IDS
-- ============================================================================

-- Update expert_memory table
UPDATE expert_memory em
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE em.expert_id = m.old_expert_id;

-- Update expert_adaptations table if exists
UPDATE expert_adaptations ea
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE ea.expert_id = m.old_expert_id;

-- Update expert_reasoning_chains table if exists
UPDATE expert_reasoning_chains erc
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE erc.expert_id = m.old_expert_id;

-- Update expert_belief_revisions table if exists
UPDATE expert_belief_revisions ebr
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE ebr.expert_id = m.old_expert_id;

-- Update expert_episodic_memories table if exists
UPDATE expert_episodic_memories eem
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE eem.expert_id = m.old_expert_id;

-- Update expert_learned_principles table if exists
UPDATE expert_learned_principles elp
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE elp.expert_id = m.old_expert_id;

-- Update expert_confidence_calibration table if exists
UPDATE expert_confidence_calibration ecc
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE ecc.expert_id = m.old_expert_id;

-- Update expert_predictions_enhanced table if exists
UPDATE expert_predictions_enhanced epe
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE epe.expert_id = m.old_expert_id;

-- Update ai_council_selections table if exists
UPDATE ai_council_selections acs
SET expert_id = m.new_expert_id
FROM expert_id_migration_mapping m
WHERE acs.expert_id = m.old_expert_id;

-- ============================================================================
-- PHASE 5: VALIDATION AND VERIFICATION
-- ============================================================================

-- Create validation view to verify migration
CREATE OR REPLACE VIEW expert_migration_validation AS
SELECT 
    pe.expert_id,
    pe.name,
    pe.personality_traits,
    pe.decision_style,
    pe.learning_rate,
    COUNT(em.id) as memory_records,
    COUNT(DISTINCT em.game_id) as unique_games,
    pe.updated_at as last_updated
FROM personality_experts pe
LEFT JOIN expert_memory em ON pe.expert_id = em.expert_id
GROUP BY pe.expert_id, pe.name, pe.personality_traits, pe.decision_style, pe.learning_rate, pe.updated_at
ORDER BY pe.expert_id;

-- Create index for performance on new expert IDs
CREATE INDEX IF NOT EXISTS idx_personality_experts_new_id ON personality_experts(expert_id);
CREATE INDEX IF NOT EXISTS idx_expert_memory_new_expert_id ON expert_memory(expert_id);

-- ============================================================================
-- PHASE 6: DOCUMENTATION AND CLEANUP
-- ============================================================================

-- Insert migration log record
INSERT INTO expert_id_migration_mapping (old_expert_id, new_expert_id, old_name, new_name, personality_type)
VALUES ('MIGRATION_COMPLETE', 'MIGRATION_COMPLETE', 'Migration completed successfully', 'All expert IDs standardized', 'system_log');

-- Verify we have exactly 15 experts
DO $$
DECLARE
    expert_count INT;
BEGIN
    SELECT COUNT(*) INTO expert_count FROM personality_experts;
    
    IF expert_count != 15 THEN
        RAISE EXCEPTION 'Expert count validation failed: Expected 15 experts, found %', expert_count;
    END IF;
    
    RAISE NOTICE 'Expert naming standardization completed successfully. Total experts: %', expert_count;
END $$;

-- Display final expert list for verification
SELECT 
    expert_id,
    name,
    decision_style,
    (personality_traits->>'risk_tolerance')::float as risk_tolerance,
    (personality_traits->>'analytics_trust')::float as analytics_trust,
    (personality_traits->>'contrarian_tendency')::float as contrarian_tendency
FROM personality_experts
ORDER BY expert_id;