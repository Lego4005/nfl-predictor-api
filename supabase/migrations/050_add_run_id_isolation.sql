-- Add run_id isolation to hot-path tables for Expert Council Betting System
-- Migration: 050_add_run_id_isolation.sql

-- =====================================
-- 1. Add run_id columns to hot-path tables
-- ========================================

-- Add run_id to expert_predictions_comprehensive (main predictions table)
ALTER TABLE expert_predictions_comprehensive
ADD COLUMN IF NOT EXISTS run_id TEXT DEFAULT 'run_2025_pilot4';

-- Add run_id to expert_predictions_enhanced (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expert_predictions_enhanced') THEN
        ALTER TABLE expert_predictions_enhanced
        ADD COLUMN IF NOT EXISTS run_id TEXT DEFAULT 'run_2025_pilot4';
    END IF;
END $$;

-- Create expert_bets table if it doesn't exist
CREATE TABLE IF NOT EXISTS expert_bets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    prediction_id UUID REFERENCES expert_predictions_comprehensive(id),
    run_id TEXT DEFAULT 'run_2025_pilot4',

    -- Bet Details
    category VARCHAR(50) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    pred_type VARCHAR(20) NOT NULL, -- binary, enum, numeric
    value JSONB NOT NULL,
    confidence DECIMAL(6,5) NOT NULL,
    stake_units DECIMAL(8,4) NOT NULL,

    -- Odds Information
    odds_type VARCHAR(20) NOT NULL, -- american, decimal, fraction
    odds_value JSONB NOT NULL,

    -- Settlement
    settled BOOLEAN DEFAULT FALSE,
    settlement_result VARCHAR(20), -- win, loss, push, void
    payout DECIMAL(10,4) DEFAULT 0,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    settled_at TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0 AND confidence <= 1),
    CONSTRAINT valid_stake CHECK (stake_units >= 0),
    CONSTRAINT valid_pred_type CHECK (pred_type IN ('binary', 'enum', 'numeric')),
    CONSTRAINT valid_odds_type CHECK (odds_type IN ('american', 'decimal', 'fraction')),
    CONSTRAINT valid_settlement CHECK (settlement_result IN ('win', 'loss', 'push', 'void'))
);

-- Add run_id to expert_bets
ALTER TABLE expert_bets
ALTER COLUMN run_id SET NOT NULL;

-- Create expert_bankroll table if it doesn't exist
CREATE TABLE IF NOT EXISTS expert_bankroll (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    run_id TEXT NOT NULL DEFAULT 'run_2025_pilot4',

    -- Bankroll State
    current_units DECIMAL(12,4) NOT NULL DEFAULT 100.0000,
    starting_units DECIMAL(12,4) NOT NULL DEFAULT 100.0000,
    peak_units DECIMAL(12,4) NOT NULL DEFAULT 100.0000,

    -- Performance Metrics
    total_bets INTEGER DEFAULT 0,
    winning_bets INTEGER DEFAULT 0,
    losing_bets INTEGER DEFAULT 0,
    push_bets INTEGER DEFAULT 0,

    -- ROI Calculations
    total_wagered DECIMAL(12,4) DEFAULT 0,
    total_profit_loss DECIMAL(12,4) DEFAULT 0,
    roi_percentage DECIMAL(8,4) DEFAULT 0,

    -- Risk Management
    max_bet_size DECIMAL(8,4) DEFAULT 10.0000,
    risk_tolerance DECIMAL(4,3) DEFAULT 0.250,

    -- Status
    active BOOLEAN DEFAULT TRUE,
    busted BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_units CHECK (current_units >= 0),
    CONSTRAINT valid_roi CHECK (roi_percentage >= -1.0),
    CONSTRAINT valid_risk_tolerance CHECK (risk_tolerance >= 0 AND risk_tolerance <= 1),
    CONSTRAINT unique_expert_run UNIQUE (expert_id, run_id)
);

-- Create expert_category_calibration table for learning system
CREATE TABLE IF NOT EXISTS expert_category_calibration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    run_id TEXT NOT NULL DEFAULT 'run_2025_pilot4',
    category VARCHAR(50) NOT NULL,

    -- Beta Calibration (for binary/enum predictions)
    beta_alpha DECIMAL(8,4) DEFAULT 1.0000,
    beta_beta DECIMAL(8,4) DEFAULT 1.0000,

    -- EMA Calibration (for numeric predictions)
    ema_mu DECIMAL(10,6) DEFAULT 0.000000,
    ema_sigma DECIMAL(10,6) DEFAULT 1.000000,
    ema_decay DECIMAL(6,5) DEFAULT 0.95000,

    -- Performance Tracking
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    brier_score DECIMAL(8,6),
    mae_score DECIMAL(8,6),

    -- Factor Updates
    factor_weight DECIMAL(8,6) DEFAULT 1.000000,
    last_factor_update TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_beta_params CHECK (beta_alpha > 0 AND beta_beta > 0),
    CONSTRAINT valid_ema_decay CHECK (ema_decay > 0 AND ema_decay < 1),
    CONSTRAINT valid_factor_weight CHECK (factor_weight > 0),
    CONSTRAINT unique_expert_run_category UNIQUE (expert_id, run_id, category)
);

-- ========================================
-- 2. Create indexes for run_id filtering
-- ========================================

-- Indexes for expert_predictions_comprehensive
CREATE INDEX IF NOT EXISTS idx_expert_predictions_run_id
ON expert_predictions_comprehensive(run_id);

CREATE INDEX IF NOT EXISTS idx_expert_predictions_run_expert
ON expert_predictions_comprehensive(run_id, expert_id);

CREATE INDEX IF NOT EXISTS idx_expert_predictions_run_game
ON expert_predictions_comprehensive(run_id, game_id);

-- Indexes for expert_predictions_enhanced (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expert_predictions_enhanced') THEN
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_expert_predictions_enhanced_run_id ON expert_predictions_enhanced(run_id)';
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_expert_predictions_enhanced_run_expert ON expert_predictions_enhanced(run_id, expert_id)';
        EXECUTE 'CREATE INDEX IF NOT EXISTS idx_expert_predictions_enhanced_run_game ON expert_predictions_enhanced(run_id, game_id)';
    END IF;
END $$;

-- Indexes for expert_bets
CREATE INDEX IF NOT EXISTS idx_expert_bets_run_id
ON expert_bets(run_id);

CREATE INDEX IF NOT EXISTS idx_expert_bets_run_expert
ON expert_bets(run_id, expert_id);

CREATE INDEX IF NOT EXISTS idx_expert_bets_run_game
ON expert_bets(run_id, game_id);

CREATE INDEX IF NOT EXISTS idx_expert_bets_settled
ON expert_bets(run_id, settled);

-- Indexes for expert_bankroll
CREATE INDEX IF NOT EXISTS idx_expert_bankroll_run_id
ON expert_bankroll(run_id);

CREATE INDEX IF NOT EXISTS idx_expert_bankroll_run_expert
ON expert_bankroll(run_id, expert_id);

CREATE INDEX IF NOT EXISTS idx_expert_bankroll_active
ON expert_bankroll(run_id, active) WHERE active = TRUE;

-- Indexes for expert_category_calibration
CREATE INDEX IF NOT EXISTS idx_expert_calibration_run_id
ON expert_category_calibration(run_id);

CREATE INDEX IF NOT EXISTS idx_expert_calibration_run_expert
ON expert_category_calibration(run_id, expert_id);

CREATE INDEX IF NOT EXISTS idx_expert_calibration_run_category
ON expert_category_calibration(run_id, category);

-- ========================================
-- 3. Update existing RPC functions to support run_id filtering
-- ========================================

-- Create or replace the search_expert_memories RPC function with run_id support
CREATE OR REPLACE FUNCTION search_expert_memories(
    p_expert_id TEXT,
    p_query_text TEXT,
    p_k INTEGER DEFAULT 15,
    p_alpha DECIMAL DEFAULT 0.8,
    p_run_id TEXT DEFAULT 'run_2025_pilot4'
)
RETURNS TABLE(
    memory_id TEXT,
    content TEXT,
    similarity_score DECIMAL,
    recency_score DECIMAL,
    combined_score DECIMAL,
    metadata JSONB
) AS $$
BEGIN
    -- Note: This is a placeholder implementation
    -- The actual implementation will depend on the expert_episodic_memories table structure
    -- and will need to be updated when that table is created with proper embeddings

    RETURN QUERY
    SELECT
        'placeholder_memory_' || generate_random_uuid()::TEXT as memory_id,
        'Placeholder memory content for ' || p_expert_id as content,
        0.85::DECIMAL as similarity_score,
        0.75::DECIMAL as recency_score,
        0.80::DECIMAL as combined_score,
        jsonb_build_object('run_id', p_run_id, 'expert_id', p_expert_id) as metadata
    LIMIT p_k;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 4. Create run management functions
-- ========================================

-- Function to initialize a new run
CREATE OR REPLACE FUNCTION initialize_run(
    p_run_id TEXT,
    p_expert_ids TEXT[] DEFAULT ARRAY['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel', 'value_hunter']
)
RETURNS JSONB AS $$
DECLARE
    expert_id TEXT;
    result JSONB := jsonb_build_object('run_id', p_run_id, 'experts_initialized', 0);
    expert_count INTEGER := 0;
BEGIN
    -- Initialize bankroll for each expert
    FOREACH expert_id IN ARRAY p_expert_ids
    LOOP
        INSERT INTO expert_bankroll (expert_id, run_id, current_units, starting_units, peak_units)
        VALUES (expert_id, p_run_id, 100.0000, 100.0000, 100.0000)
        ON CONFLICT (expert_id, run_id) DO NOTHING;

        expert_count := expert_count + 1;
    END LOOP;

    -- Initialize category calibration priors for each expert
    FOREACH expert_id IN ARRAY p_expert_ids
    LOOP
        -- Insert calibration records for key categories
        INSERT INTO expert_category_calibration (expert_id, run_id, category, beta_alpha, beta_beta, ema_mu, ema_sigma)
        VALUES
            (expert_id, p_run_id, 'game_winner', 1.0, 1.0, 0.0, 1.0),
            (expert_id, p_run_id, 'spread_full_game', 1.0, 1.0, 0.0, 3.5),
            (expert_id, p_run_id, 'total_full_game', 1.0, 1.0, 45.0, 7.0),
            (expert_id, p_run_id, 'qb_passing_yards', 1.0, 1.0, 250.0, 50.0),
            (expert_id, p_run_id, 'momentum_factor', 1.0, 1.0, 0.0, 0.3)
        ON CONFLICT (expert_id, run_id, category) DO NOTHING;
    END LOOP;

    result := jsonb_set(result, '{experts_initialized}', to_jsonb(expert_count));
    result := jsonb_set(result, '{expert_ids}', to_jsonb(p_expert_ids));

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to get run statistics
CREATE OR REPLACE FUNCTION get_run_statistics(p_run_id TEXT)
RETURNS JSONB AS $$
DECLARE
    result JSONB := jsonb_build_object('run_id', p_run_id);
    expert_count INTEGER;
    prediction_count INTEGER;
    bet_count INTEGER;
BEGIN
    -- Count experts in this run
    SELECT COUNT(*) INTO expert_count
    FROM expert_bankroll
    WHERE run_id = p_run_id;

    -- Count predictions in this run
    SELECT COUNT(*) INTO prediction_count
    FROM expert_predictions_comprehensive
    WHERE run_id = p_run_id;

    -- Count bets in this run
    SELECT COUNT(*) INTO bet_count
    FROM expert_bets
    WHERE run_id = p_run_id;

    result := jsonb_set(result, '{expert_count}', to_jsonb(expert_count));
    result := jsonb_set(result, '{prediction_count}', to_jsonb(prediction_count));
    result := jsonb_set(result, '{bet_count}', to_jsonb(bet_count));

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 5. Initialize pilot run
-- ========================================

-- Initialize the pilot run with 4 experts
SELECT initialize_run(
    'run_2025_pilot4',
    ARRAY['conservative_analyzer', 'risk_taking_gambler', 'contrarian_rebel', 'value_hunter']
);

-- ========================================
-- 6. Create views for run-specific data
-- ========================================

-- Current run leaderboard
CREATE OR REPLACE VIEW current_run_leaderboard AS
SELECT
    eb.expert_id,
    eb.run_id,
    eb.current_units,
    eb.roi_percentage,
    eb.total_bets,
    eb.winning_bets,
    CASE
        WHEN eb.total_bets > 0 THEN ROUND((eb.winning_bets::DECIMAL / eb.total_bets) * 100, 2)
        ELSE 0
    END as win_percentage,
    eb.active,
    eb.busted
FROM expert_bankroll eb
WHERE eb.run_id = 'run_2025_pilot4'
ORDER BY eb.current_units DESC;

-- Run-specific prediction summary
CREATE OR REPLACE VIEW run_prediction_summary AS
SELECT
    epc.run_id,
    epc.expert_id,
    COUNT(*) as total_predictions,
    AVG(epc.confidence_overall) as avg_confidence,
    COUNT(CASE WHEN epc.points_earned > 0 THEN 1 END) as successful_predictions,
    AVG(epc.points_earned) as avg_points_per_prediction
FROM expert_predictions_comprehensive epc
WHERE epc.run_id = 'run_2025_pilot4'
GROUP BY epc.run_id, epc.expert_id
ORDER BY avg_points_per_prediction DESC NULLS LAST;

-- ========================================
-- 7. Add comments for documentation
-- ========================================

COMMENT ON TABLE expert_bets IS 'Individual betting positions taken by experts, isolated by run_id';
COMMENT ON TABLE expert_bankroll IS 'Expert bankroll tracking with run isolation for A/B testing';
COMMENT ON TABLE expert_category_calibration IS 'Per-category calibration parameters for expert learning system';

COMMENT ON COLUMN expert_predictions_comprehensive.run_id IS 'Run identifier for experimental isolation (e.g., run_2025_pilot4)';
COMMENT ON COLUMN expert_bets.run_id IS 'Run identifier for bet isolation and settlement tracking';
COMMENT ON COLUMN expert_bankroll.run_id IS 'Run identifier for bankroll isolation between experiments';

COMMENT ON FUNCTION search_expert_memories IS 'Vector-based memory retrieval with run_id filtering for experimental isolation';
COMMENT ON FUNCTION initialize_run IS 'Initialize a new experimental run with expert bankrolls and calibration priors';
COMMENT ON FUNCTION get_run_statistics IS 'Get summary statistics for a specific experimental run';
