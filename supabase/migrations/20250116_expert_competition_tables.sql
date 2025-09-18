-- Expert Competition System Database Schema
-- Tracks 15 competing expert models with multi-dimensional predictions

-- ========================================
-- 1. Expert Models Table
-- ========================================
CREATE TABLE IF NOT EXISTS expert_models (
    expert_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    personality VARCHAR(50),
    specializations TEXT[],
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    overall_accuracy DECIMAL(5,4) DEFAULT 0,
    leaderboard_score DECIMAL(10,2) DEFAULT 0,
    current_rank INTEGER,
    peak_rank INTEGER DEFAULT 999,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, retired
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_expert_leaderboard ON expert_models(leaderboard_score DESC);
CREATE INDEX idx_expert_rank ON expert_models(current_rank);

-- ========================================
-- 2. Expert Predictions Table (Comprehensive)
-- ========================================
CREATE TABLE IF NOT EXISTS expert_predictions_comprehensive (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES expert_models(expert_id),
    game_id VARCHAR(100),
    prediction_timestamp TIMESTAMP DEFAULT NOW(),

    -- Core Predictions (20+ types)
    game_outcome JSONB,  -- {winner, confidence, reasoning}
    exact_score JSONB,   -- {home_score, away_score, confidence}
    margin_of_victory JSONB,  -- {margin, winner, confidence}
    against_the_spread JSONB, -- {pick, spread, confidence}
    totals JSONB,        -- {pick, total, confidence}
    moneyline_value JSONB,    -- {pick, expected_value, confidence}

    -- Quarter/Half Predictions
    first_half_winner JSONB,
    second_half_winner JSONB,
    highest_scoring_quarter JSONB,
    quarter_scores JSONB,  -- Q1-Q4 predictions

    -- Player Props
    player_props JSONB,  -- Multiple player predictions

    -- Live Predictions
    live_win_probability JSONB[],  -- Array of updates during game
    momentum_shifts JSONB,

    -- Meta Information
    confidence_overall DECIMAL(5,4),
    reasoning TEXT,
    key_factors TEXT[],

    -- Vector embeddings for pattern matching
    prediction_embedding vector(384),
    context_embedding vector(384),

    -- Results (filled after game)
    actual_results JSONB,
    points_earned DECIMAL(10,2),
    accuracy_scores JSONB,  -- Per category accuracy

    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast retrieval
CREATE INDEX idx_predictions_expert ON expert_predictions_comprehensive(expert_id);
CREATE INDEX idx_predictions_game ON expert_predictions_comprehensive(game_id);
CREATE INDEX idx_predictions_timestamp ON expert_predictions_comprehensive(prediction_timestamp DESC);

-- Vector similarity search indexes
CREATE INDEX idx_prediction_embedding ON expert_predictions_comprehensive
    USING hnsw (prediction_embedding vector_cosine_ops);
CREATE INDEX idx_context_embedding ON expert_predictions_comprehensive
    USING hnsw (context_embedding vector_cosine_ops);

-- ========================================
-- 3. Expert Performance By Category
-- ========================================
CREATE TABLE IF NOT EXISTS expert_category_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES expert_models(expert_id),
    category VARCHAR(50), -- game_outcome, spread, totals, etc.

    -- Performance Metrics
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4) DEFAULT 0,

    -- Advanced Metrics
    mean_absolute_error DECIMAL(10,4),
    brier_score DECIMAL(5,4),
    roi_percentage DECIMAL(10,4),

    -- Trend Analysis
    last_10_accuracy DECIMAL(5,4),
    last_25_accuracy DECIMAL(5,4),
    trend VARCHAR(20), -- improving, declining, stable

    -- Confidence Calibration
    avg_confidence DECIMAL(5,4),
    confidence_correlation DECIMAL(5,4), -- How well confidence predicts success

    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_expert_category ON expert_category_performance(expert_id, category);

-- ========================================
-- 4. Expert Leaderboard History
-- ========================================
CREATE TABLE IF NOT EXISTS expert_leaderboard_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_date DATE DEFAULT CURRENT_DATE,
    expert_id VARCHAR(50) REFERENCES expert_models(expert_id),
    rank INTEGER,
    score DECIMAL(10,2),
    predictions_count INTEGER,
    accuracy DECIMAL(5,4),

    -- Category Leaders
    best_category VARCHAR(50),
    worst_category VARCHAR(50),

    -- Weekly Performance
    weekly_points DECIMAL(10,2),
    weekly_rank_change INTEGER,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_leaderboard_date ON expert_leaderboard_history(snapshot_date DESC);
CREATE INDEX idx_leaderboard_expert ON expert_leaderboard_history(expert_id);

-- ========================================
-- 5. Expert Head-to-Head Records
-- ========================================
CREATE TABLE IF NOT EXISTS expert_head_to_head (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert1_id VARCHAR(50) REFERENCES expert_models(expert_id),
    expert2_id VARCHAR(50) REFERENCES expert_models(expert_id),

    -- Overall Record
    expert1_wins INTEGER DEFAULT 0,
    expert2_wins INTEGER DEFAULT 0,
    ties INTEGER DEFAULT 0,

    -- By Category
    category_records JSONB, -- {spread: {e1: 10, e2: 5}, totals: {...}}

    -- Recent Form
    last_10_results VARCHAR(10), -- W,L,W,W,L format

    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_h2h_experts ON expert_head_to_head(expert1_id, expert2_id);

-- ========================================
-- 6. Expert Learning Patterns
-- ========================================
CREATE TABLE IF NOT EXISTS expert_learning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES expert_models(expert_id),

    -- Pattern Identification
    pattern_type VARCHAR(50), -- home_bias, weather_impact, primetime_choke, etc.
    pattern_vector vector(384),

    -- Pattern Strength
    occurrence_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,4),
    confidence_adjustment DECIMAL(5,4),

    -- Examples
    example_games TEXT[],

    discovered_at TIMESTAMP DEFAULT NOW(),
    last_seen TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_learning_expert ON expert_learning_patterns(expert_id);
CREATE INDEX idx_pattern_vector ON expert_learning_patterns
    USING hnsw (pattern_vector vector_cosine_ops);

-- ========================================
-- 7. Consensus Predictions
-- ========================================
CREATE TABLE IF NOT EXISTS consensus_predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(100),
    prediction_timestamp TIMESTAMP DEFAULT NOW(),

    -- Top 5 Experts Used
    top5_experts VARCHAR(50)[],
    expert_weights DECIMAL(5,4)[],  -- [0.30, 0.25, 0.20, 0.15, 0.10]

    -- Weighted Consensus
    consensus_winner VARCHAR(50),
    consensus_spread DECIMAL(5,2),
    consensus_total DECIMAL(5,2),
    consensus_confidence DECIMAL(5,4),

    -- All Expert Votes (for transparency)
    all_predictions JSONB,

    -- Disagreement Metrics
    disagreement_score DECIMAL(5,4),
    controversial_aspects TEXT[],

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_consensus_game ON consensus_predictions(game_id);
CREATE INDEX idx_consensus_timestamp ON consensus_predictions(prediction_timestamp DESC);

-- ========================================
-- 8. Expert Competition Rounds
-- ========================================
CREATE TABLE IF NOT EXISTS competition_rounds (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_number INTEGER,
    week INTEGER,
    season INTEGER,

    -- Round Details
    games_included TEXT[],
    participating_experts VARCHAR(50)[],

    -- Round Results
    round_winner VARCHAR(50),
    round_scores JSONB,  -- {expert_id: score}

    -- Leaderboard Changes
    rank_changes JSONB,  -- {expert_id: change}

    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_round_week ON competition_rounds(season, week);

-- ========================================
-- 9. Expert Achievements
-- ========================================
CREATE TABLE IF NOT EXISTS expert_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES expert_models(expert_id),
    achievement_type VARCHAR(50),
    achievement_name VARCHAR(100),
    description TEXT,

    -- Achievement Details
    criteria_met JSONB,
    points_awarded DECIMAL(10,2),

    earned_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_achievement_expert ON expert_achievements(expert_id);

-- ========================================
-- 10. Expert Fingerprints (Vector Intelligence)
-- ========================================
CREATE TABLE IF NOT EXISTS expert_fingerprints (
    expert_id VARCHAR(50) PRIMARY KEY REFERENCES expert_models(expert_id),

    -- Success/Failure Vectors
    success_vector vector(384),
    failure_vector vector(384),
    fingerprint_vector vector(384),  -- success - failure

    -- Category-Specific Vectors
    category_vectors JSONB,  -- {spread: vector, totals: vector, ...}

    -- Situation Vectors
    primetime_vector vector(384),
    divisional_vector vector(384),
    weather_vector vector(384),
    underdog_vector vector(384),

    updated_at TIMESTAMP DEFAULT NOW()
);

-- Vector indexes for similarity search
CREATE INDEX idx_fingerprint ON expert_fingerprints
    USING hnsw (fingerprint_vector vector_cosine_ops);
CREATE INDEX idx_success_vector ON expert_fingerprints
    USING hnsw (success_vector vector_cosine_ops);

-- ========================================
-- Views for Quick Access
-- ========================================

-- Current Leaderboard View
CREATE OR REPLACE VIEW current_leaderboard AS
SELECT
    e.expert_id,
    e.name,
    e.current_rank,
    e.leaderboard_score,
    e.overall_accuracy,
    e.total_predictions,
    e.specializations
FROM expert_models e
WHERE e.status = 'active'
ORDER BY e.leaderboard_score DESC;

-- Top 5 Experts View
CREATE OR REPLACE VIEW top5_experts AS
SELECT * FROM current_leaderboard
LIMIT 5;

-- Expert Recent Performance View
CREATE OR REPLACE VIEW expert_recent_performance AS
SELECT
    e.expert_id,
    e.name,
    COUNT(CASE WHEN p.created_at > NOW() - INTERVAL '7 days' THEN 1 END) as last_week_predictions,
    AVG(CASE WHEN p.created_at > NOW() - INTERVAL '7 days' THEN p.points_earned END) as last_week_avg_points,
    COUNT(CASE WHEN p.created_at > NOW() - INTERVAL '30 days' THEN 1 END) as last_month_predictions,
    AVG(CASE WHEN p.created_at > NOW() - INTERVAL '30 days' THEN p.points_earned END) as last_month_avg_points
FROM expert_models e
LEFT JOIN expert_predictions_comprehensive p ON e.expert_id = p.expert_id
GROUP BY e.expert_id, e.name;

-- ========================================
-- Stored Procedures
-- ========================================

-- Update Expert Rankings
CREATE OR REPLACE FUNCTION update_expert_rankings()
RETURNS void AS $$
BEGIN
    WITH ranked_experts AS (
        SELECT
            expert_id,
            leaderboard_score,
            ROW_NUMBER() OVER (ORDER BY leaderboard_score DESC) as new_rank
        FROM expert_models
        WHERE status = 'active'
    )
    UPDATE expert_models e
    SET
        current_rank = r.new_rank,
        peak_rank = LEAST(e.peak_rank, r.new_rank),
        updated_at = NOW()
    FROM ranked_experts r
    WHERE e.expert_id = r.expert_id;
END;
$$ LANGUAGE plpgsql;

-- Calculate Expert Points for Prediction
CREATE OR REPLACE FUNCTION calculate_prediction_points(
    prediction JSONB,
    actual JSONB,
    category VARCHAR
)
RETURNS DECIMAL AS $$
DECLARE
    points DECIMAL := 0;
    confidence DECIMAL;
BEGIN
    confidence := (prediction->>'confidence')::DECIMAL;

    CASE category
        WHEN 'game_outcome' THEN
            IF prediction->>'winner' = actual->>'winner' THEN
                points := 10 * (1 + confidence * 0.5);
            ELSE
                points := -5;
            END IF;

        WHEN 'against_the_spread' THEN
            IF prediction->>'pick' = actual->>'cover' THEN
                points := 15 * (1 + confidence * 0.5);
            ELSE
                points := -10;
            END IF;

        WHEN 'totals' THEN
            IF prediction->>'pick' = actual->>'result' THEN
                points := 12 * (1 + confidence * 0.5);
            ELSE
                points := -8;
            END IF;

        -- Add more categories as needed
    END CASE;

    RETURN points;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- Initial Data Load - 15 Experts
-- ========================================
INSERT INTO expert_models (expert_id, name, personality, specializations) VALUES
('expert_001', 'Statistical Savant', 'analytical', ARRAY['historical_patterns', 'regression_analysis', 'trend_identification']),
('expert_002', 'Sharp Bettor', 'aggressive', ARRAY['line_movement', 'sharp_money', 'closing_line_value']),
('expert_003', 'Weather Wizard', 'situational', ARRAY['weather_impact', 'outdoor_games', 'environmental_factors']),
('expert_004', 'Injury Analyst', 'conservative', ARRAY['injury_impact', 'player_availability', 'depth_analysis']),
('expert_005', 'Trend Tracker', 'momentum', ARRAY['winning_streaks', 'momentum', 'recent_form']),
('expert_006', 'Divisional Expert', 'specialized', ARRAY['divisional_games', 'rivalry_analysis', 'head_to_head']),
('expert_007', 'Primetime Performer', 'spotlight', ARRAY['primetime_games', 'national_tv', 'high_pressure']),
('expert_008', 'Under Expert', 'defensive', ARRAY['defensive_matchups', 'under_totals', 'low_scoring']),
('expert_009', 'Over Enthusiast', 'offensive', ARRAY['offensive_matchups', 'over_totals', 'high_scoring']),
('expert_010', 'Home Field Hawk', 'traditional', ARRAY['home_advantage', 'crowd_impact', 'travel_fatigue']),
('expert_011', 'Road Warrior', 'contrarian', ARRAY['road_teams', 'underdog_value', 'contrarian_angles']),
('expert_012', 'Coaching Connoisseur', 'strategic', ARRAY['coaching_matchups', 'game_planning', 'adjustments']),
('expert_013', 'QB Whisperer', 'quarterback-focused', ARRAY['quarterback_analysis', 'passing_game', 'qb_matchups']),
('expert_014', 'Situational Specialist', 'situational', ARRAY['revenge_games', 'letdown_spots', 'lookahead_games']),
('expert_015', 'Market Maven', 'value-hunting', ARRAY['market_inefficiency', 'value_identification', 'closing_line_value'])
ON CONFLICT (expert_id) DO NOTHING;