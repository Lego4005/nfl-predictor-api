-- Enhanced Expert Competition System Database Schema
-- Comprehensive schema for 15 competing experts with AI Council voting
-- Migration: 020_enhanced_expert_competition_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- 1. Enhanced Expert Models Table
-- ========================================
DROP TABLE IF EXISTS enhanced_expert_models CASCADE;
CREATE TABLE enhanced_expert_models (
    expert_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    personality VARCHAR(50) NOT NULL,
    specializations TEXT[] DEFAULT '{}',
    
    -- Performance Metrics
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    overall_accuracy DECIMAL(6,5) DEFAULT 0.50000,
    
    -- Ranking System
    leaderboard_score DECIMAL(10,4) DEFAULT 0,
    current_rank INTEGER DEFAULT 999,
    peak_rank INTEGER DEFAULT 999,
    rank_history INTEGER[] DEFAULT '{}',
    
    -- Category-Specific Performance
    category_accuracies JSONB DEFAULT '{}',
    confidence_calibration DECIMAL(6,5) DEFAULT 0.50000,
    consistency_score DECIMAL(6,5) DEFAULT 0.50000,
    specialization_strength DECIMAL(6,5) DEFAULT 0.50000,
    
    -- AI Council Participation
    council_appearances INTEGER DEFAULT 0,
    council_performance DECIMAL(6,5) DEFAULT 0.50000,
    last_council_date TIMESTAMP,
    
    -- Personality & Algorithm State
    personality_traits JSONB DEFAULT '{}',
    algorithm_parameters JSONB DEFAULT '{}',
    adaptation_history JSONB[] DEFAULT '{}',
    
    -- Status & Metadata
    status VARCHAR(20) DEFAULT 'active', -- active, adapting, suspended
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_accuracy CHECK (overall_accuracy >= 0 AND overall_accuracy <= 1),
    CONSTRAINT valid_rank CHECK (current_rank > 0),
    CONSTRAINT valid_status CHECK (status IN ('active', 'adapting', 'suspended', 'retired'))
);

-- Indexes for enhanced expert models
CREATE INDEX idx_enhanced_expert_leaderboard ON enhanced_expert_models(leaderboard_score DESC);
CREATE INDEX idx_enhanced_expert_rank ON enhanced_expert_models(current_rank);
CREATE INDEX idx_enhanced_expert_accuracy ON enhanced_expert_models(overall_accuracy DESC);
CREATE INDEX idx_enhanced_expert_status ON enhanced_expert_models(status);
CREATE INDEX idx_enhanced_expert_specializations ON enhanced_expert_models USING GIN(specializations);

-- ========================================
-- 2. AI Council Management
-- ========================================
CREATE TABLE ai_council_selections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    selection_id VARCHAR(100) UNIQUE NOT NULL, -- e.g., "2025_week_1"
    week INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    -- Council Composition
    council_members VARCHAR(50)[] NOT NULL,
    council_ranks INTEGER[] NOT NULL,
    council_scores DECIMAL(10,4)[] NOT NULL,
    
    -- Selection Criteria
    evaluation_window_weeks INTEGER DEFAULT 4,
    selection_algorithm VARCHAR(50) DEFAULT 'weighted_performance',
    selection_weights JSONB DEFAULT '{}',
    
    -- Performance Prediction
    predicted_consensus_accuracy DECIMAL(6,5),
    predicted_disagreement_rate DECIMAL(6,5),
    
    -- Metadata
    promoted_experts VARCHAR(50)[] DEFAULT '{}',
    demoted_experts VARCHAR(50)[] DEFAULT '{}',
    selection_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for AI Council selections
CREATE INDEX idx_ai_council_week ON ai_council_selections(season, week);
CREATE INDEX idx_ai_council_members ON ai_council_selections USING GIN(council_members);
CREATE INDEX idx_ai_council_created ON ai_council_selections(created_at DESC);

-- ========================================
-- 3. Comprehensive Prediction Categories
-- ========================================
CREATE TABLE prediction_categories (
    category_id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    category_group VARCHAR(50) NOT NULL, -- game_outcome, betting_market, player_props, situational
    data_type VARCHAR(20) NOT NULL, -- boolean, numeric, categorical, text
    validation_rules JSONB DEFAULT '{}',
    scoring_weight DECIMAL(4,3) DEFAULT 1.000,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert 25+ prediction categories
INSERT INTO prediction_categories (category_id, category_name, category_group, data_type, validation_rules, description) VALUES
-- Game Outcome Predictions (4 categories)
('winner_prediction', 'Winner Prediction', 'game_outcome', 'categorical', '{"values": ["home", "away"]}', 'Predicted game winner'),
('exact_score_home', 'Exact Score - Home Team', 'game_outcome', 'numeric', '{"min": 0, "max": 70}', 'Predicted home team final score'),
('exact_score_away', 'Exact Score - Away Team', 'game_outcome', 'numeric', '{"min": 0, "max": 70}', 'Predicted away team final score'),
('margin_of_victory', 'Margin of Victory', 'game_outcome', 'numeric', '{"min": 0, "max": 50}', 'Predicted point margin'),

-- Betting Market Predictions (4 categories)
('against_the_spread', 'Against the Spread', 'betting_market', 'categorical', '{"values": ["home", "away", "push"]}', 'ATS prediction'),
('totals_over_under', 'Totals Over/Under', 'betting_market', 'categorical', '{"values": ["over", "under", "push"]}', 'Total points over/under'),
('first_half_winner', 'First Half Winner', 'betting_market', 'categorical', '{"values": ["home", "away", "tie"]}', 'First half winner'),
('highest_scoring_quarter', 'Highest Scoring Quarter', 'betting_market', 'categorical', '{"values": ["Q1", "Q2", "Q3", "Q4"]}', 'Quarter with most points'),

-- Live Game Scenarios (4 categories)
('live_win_probability', 'Live Win Probability Updates', 'live_scenario', 'numeric', '{"min": 0, "max": 1}', 'Real-time win probability'),
('next_score_probability', 'Next Score Probability', 'live_scenario', 'categorical', '{"values": ["touchdown", "field_goal", "safety", "none"]}', 'Next scoring play'),
('drive_outcome_prediction', 'Drive Outcome Prediction', 'live_scenario', 'categorical', '{"values": ["touchdown", "field_goal", "punt", "turnover"]}', 'Current drive outcome'),
('fourth_down_decision', 'Fourth Down Decision', 'live_scenario', 'categorical', '{"values": ["punt", "field_goal", "go_for_it"]}', 'Optimal 4th down decision'),

-- Player Performance Props (8 categories)
('qb_passing_yards', 'QB Passing Yards', 'player_props', 'numeric', '{"min": 0, "max": 600}', 'Quarterback passing yards'),
('qb_touchdowns', 'QB Touchdowns', 'player_props', 'numeric', '{"min": 0, "max": 8}', 'Quarterback touchdown passes'),
('qb_interceptions', 'QB Interceptions', 'player_props', 'numeric', '{"min": 0, "max": 6}', 'Quarterback interceptions'),
('rb_rushing_yards', 'RB Rushing Yards', 'player_props', 'numeric', '{"min": 0, "max": 300}', 'Running back rushing yards'),
('rb_touchdowns', 'RB Touchdowns', 'player_props', 'numeric', '{"min": 0, "max": 5}', 'Running back touchdowns'),
('wr_receiving_yards', 'WR Receiving Yards', 'player_props', 'numeric', '{"min": 0, "max": 250}', 'Wide receiver receiving yards'),
('wr_receptions', 'WR Receptions', 'player_props', 'numeric', '{"min": 0, "max": 20}', 'Wide receiver receptions'),
('fantasy_points_projection', 'Fantasy Points', 'player_props', 'numeric', '{"min": 0, "max": 50}', 'Fantasy football points'),

-- Situational Analysis (7 categories)
('weather_impact_score', 'Weather Impact Assessment', 'situational', 'numeric', '{"min": 0, "max": 1}', 'Weather impact on game'),
('injury_impact_score', 'Injury Impact Assessment', 'situational', 'numeric', '{"min": 0, "max": 1}', 'Injury impact on performance'),
('travel_rest_factor', 'Travel/Rest Impact', 'situational', 'numeric', '{"min": -0.5, "max": 0.5}', 'Travel and rest advantage'),
('divisional_rivalry_factor', 'Divisional Game Dynamics', 'situational', 'numeric', '{"min": 0, "max": 1}', 'Divisional rivalry intensity'),
('coaching_advantage', 'Coaching Matchup Analysis', 'situational', 'categorical', '{"values": ["home", "away", "neutral"]}', 'Coaching advantage'),
('home_field_advantage', 'Home Field Advantage', 'situational', 'numeric', '{"min": 0, "max": 10}', 'Home field advantage in points'),
('momentum_factor', 'Team Momentum Analysis', 'situational', 'numeric', '{"min": -1, "max": 1}', 'Recent momentum indicator');

-- ========================================
-- 4. Comprehensive Expert Predictions
-- ========================================
CREATE TABLE expert_predictions_enhanced (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES enhanced_expert_models(expert_id),
    game_id VARCHAR(100) NOT NULL,
    prediction_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Prediction Data (25+ categories)
    game_outcome JSONB NOT NULL DEFAULT '{}',
    betting_markets JSONB NOT NULL DEFAULT '{}',
    live_scenarios JSONB NOT NULL DEFAULT '{}',
    player_props JSONB NOT NULL DEFAULT '{}',
    situational_analysis JSONB NOT NULL DEFAULT '{}',
    
    -- Confidence Scores
    confidence_overall DECIMAL(6,5) NOT NULL,
    confidence_by_category JSONB DEFAULT '{}',
    uncertainty_factors JSONB DEFAULT '{}',
    
    -- Reasoning & Context
    reasoning_chain TEXT,
    key_factors TEXT[] DEFAULT '{}',
    data_sources_used TEXT[] DEFAULT '{}',
    similar_games_referenced TEXT[] DEFAULT '{}',
    
    -- Performance Tracking
    prediction_accuracy DECIMAL(6,5), -- Set after game completion
    category_accuracies JSONB DEFAULT '{}',
    confidence_calibration_score DECIMAL(6,5),
    points_earned DECIMAL(8,4) DEFAULT 0,
    
    -- Vector Embeddings for Similarity
    prediction_embedding vector(384),
    context_embedding vector(384),
    
    -- Metadata
    expert_rank_at_prediction INTEGER,
    ai_council_member BOOLEAN DEFAULT FALSE,
    adaptation_triggered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for enhanced predictions
CREATE INDEX idx_expert_predictions_enhanced_expert ON expert_predictions_enhanced(expert_id);
CREATE INDEX idx_expert_predictions_enhanced_game ON expert_predictions_enhanced(game_id);
CREATE INDEX idx_expert_predictions_enhanced_timestamp ON expert_predictions_enhanced(prediction_timestamp DESC);
CREATE INDEX idx_expert_predictions_enhanced_council ON expert_predictions_enhanced(ai_council_member) WHERE ai_council_member = TRUE;
CREATE INDEX idx_expert_predictions_enhanced_accuracy ON expert_predictions_enhanced(prediction_accuracy DESC) WHERE prediction_accuracy IS NOT NULL;

-- Vector similarity indexes
CREATE INDEX idx_prediction_embedding_enhanced ON expert_predictions_enhanced 
    USING hnsw (prediction_embedding vector_cosine_ops);
CREATE INDEX idx_context_embedding_enhanced ON expert_predictions_enhanced 
    USING hnsw (context_embedding vector_cosine_ops);

-- ========================================
-- 5. AI Council Consensus Predictions
-- ========================================
CREATE TABLE ai_council_consensus (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(100) NOT NULL,
    consensus_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Council Composition
    council_members VARCHAR(50)[] NOT NULL,
    council_ranks INTEGER[] NOT NULL,
    vote_weights DECIMAL(6,5)[] NOT NULL,
    
    -- Weight Calculation Components
    weight_breakdown JSONB NOT NULL DEFAULT '{}', -- category_accuracy, overall_performance, recent_trend, confidence_calibration
    
    -- Individual Expert Votes
    individual_predictions JSONB NOT NULL DEFAULT '{}',
    individual_confidences JSONB NOT NULL DEFAULT '{}',
    
    -- Weighted Consensus Results
    consensus_predictions JSONB NOT NULL DEFAULT '{}',
    consensus_confidence DECIMAL(6,5) NOT NULL,
    consensus_uncertainty DECIMAL(6,5),
    
    -- Disagreement Analysis
    disagreement_score DECIMAL(6,5) NOT NULL,
    controversial_categories TEXT[] DEFAULT '{}',
    minority_opinions JSONB DEFAULT '{}',
    
    -- Natural Language Explanation
    consensus_explanation TEXT NOT NULL,
    reasoning_summary TEXT,
    key_factors_consensus TEXT[] DEFAULT '{}',
    
    -- Performance Tracking
    consensus_accuracy DECIMAL(6,5), -- Set after game completion
    consensus_points_earned DECIMAL(8,4) DEFAULT 0,
    outperformed_individual_experts BOOLEAN,
    
    -- Metadata
    algorithm_version VARCHAR(20) DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for consensus predictions
CREATE INDEX idx_ai_council_consensus_game ON ai_council_consensus(game_id);
CREATE INDEX idx_ai_council_consensus_timestamp ON ai_council_consensus(consensus_timestamp DESC);
CREATE INDEX idx_ai_council_consensus_accuracy ON ai_council_consensus(consensus_accuracy DESC) WHERE consensus_accuracy IS NOT NULL;
CREATE INDEX idx_ai_council_consensus_disagreement ON ai_council_consensus(disagreement_score DESC);

-- ========================================
-- 6. Expert Performance Analytics
-- ========================================
CREATE TABLE expert_performance_analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES enhanced_expert_models(expert_id),
    analysis_period VARCHAR(50) NOT NULL, -- weekly, monthly, seasonal
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Accuracy Metrics
    overall_accuracy DECIMAL(6,5) NOT NULL,
    category_accuracies JSONB NOT NULL DEFAULT '{}',
    confidence_calibration DECIMAL(6,5) NOT NULL,
    brier_score DECIMAL(6,5),
    
    -- Ranking Metrics
    average_rank DECIMAL(6,3),
    rank_volatility DECIMAL(6,5),
    peak_rank_achieved INTEGER,
    council_selection_rate DECIMAL(6,5),
    
    -- Consistency Metrics
    prediction_consistency DECIMAL(6,5),
    performance_stability DECIMAL(6,5),
    category_specialization_scores JSONB DEFAULT '{}',
    
    -- Trend Analysis
    performance_trend VARCHAR(20), -- improving, declining, stable
    trend_strength DECIMAL(6,5),
    momentum_score DECIMAL(6,5),
    
    -- Comparative Metrics
    peer_ranking DECIMAL(6,5),
    council_vs_individual_performance DECIMAL(6,5),
    upset_prediction_rate DECIMAL(6,5),
    
    -- Adaptation Metrics
    adaptations_triggered INTEGER DEFAULT 0,
    adaptation_success_rate DECIMAL(6,5),
    learning_velocity DECIMAL(6,5),
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance analytics
CREATE INDEX idx_expert_performance_analytics_expert ON expert_performance_analytics(expert_id);
CREATE INDEX idx_expert_performance_analytics_period ON expert_performance_analytics(analysis_period, period_start, period_end);
CREATE INDEX idx_expert_performance_analytics_accuracy ON expert_performance_analytics(overall_accuracy DESC);
CREATE INDEX idx_expert_performance_analytics_trend ON expert_performance_analytics(performance_trend);

-- ========================================
-- 7. Competition Rounds & Results
-- ========================================
CREATE TABLE competition_rounds_enhanced (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    round_id VARCHAR(100) UNIQUE NOT NULL,
    week INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    -- Round Configuration
    games_included TEXT[] NOT NULL,
    participating_experts VARCHAR(50)[] NOT NULL,
    ai_council_members VARCHAR(50)[] NOT NULL,
    
    -- Round Results
    expert_performances JSONB NOT NULL DEFAULT '{}',
    expert_rankings JSONB NOT NULL DEFAULT '{}',
    round_winner VARCHAR(50),
    council_performance JSONB DEFAULT '{}',
    
    -- Performance Changes
    rank_changes JSONB DEFAULT '{}',
    accuracy_changes JSONB DEFAULT '{}',
    adaptations_triggered JSONB DEFAULT '{}',
    
    -- Round Statistics
    total_predictions INTEGER DEFAULT 0,
    average_accuracy DECIMAL(6,5),
    consensus_vs_individual_accuracy DECIMAL(6,5),
    upset_predictions INTEGER DEFAULT 0,
    
    -- Council Changes
    new_council_members VARCHAR(50)[] DEFAULT '{}',
    promoted_experts VARCHAR(50)[] DEFAULT '{}',
    demoted_experts VARCHAR(50)[] DEFAULT '{}',
    
    -- Metadata
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for competition rounds
CREATE INDEX idx_competition_rounds_enhanced_season_week ON competition_rounds_enhanced(season, week);
CREATE INDEX idx_competition_rounds_enhanced_round_id ON competition_rounds_enhanced(round_id);
CREATE INDEX idx_competition_rounds_enhanced_completed ON competition_rounds_enhanced(completed_at DESC);

-- ========================================
-- 8. Self-Healing & Adaptation Tracking
-- ========================================
CREATE TABLE expert_adaptations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) REFERENCES enhanced_expert_models(expert_id),
    adaptation_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Trigger Information
    trigger_type VARCHAR(50) NOT NULL, -- performance_decline, rank_drop, accuracy_drop, consistency_issue
    trigger_details JSONB NOT NULL DEFAULT '{}',
    trigger_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Pre-Adaptation State
    pre_adaptation_accuracy DECIMAL(6,5),
    pre_adaptation_rank INTEGER,
    pre_adaptation_parameters JSONB DEFAULT '{}',
    
    -- Adaptation Changes
    adaptation_type VARCHAR(50) NOT NULL, -- parameter_tuning, algorithm_update, weight_adjustment, methodology_change
    changes_made JSONB NOT NULL DEFAULT '{}',
    adaptation_reasoning TEXT,
    
    -- Post-Adaptation Results
    post_adaptation_accuracy DECIMAL(6,5),
    post_adaptation_rank INTEGER,
    post_adaptation_parameters JSONB DEFAULT '{}',
    
    -- Success Metrics
    adaptation_success BOOLEAN,
    improvement_score DECIMAL(6,5),
    adaptation_duration_days INTEGER,
    
    -- Recovery Timeline
    recovery_milestones JSONB DEFAULT '{}',
    full_recovery_achieved BOOLEAN DEFAULT FALSE,
    recovery_completion_date TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for adaptations
CREATE INDEX idx_expert_adaptations_expert ON expert_adaptations(expert_id);
CREATE INDEX idx_expert_adaptations_trigger ON expert_adaptations(trigger_type);
CREATE INDEX idx_expert_adaptations_success ON expert_adaptations(adaptation_success);
CREATE INDEX idx_expert_adaptations_timestamp ON expert_adaptations(trigger_timestamp DESC);

-- ========================================
-- 9. Views for Quick Access
-- ========================================

-- Current Expert Leaderboard
CREATE OR REPLACE VIEW current_expert_leaderboard AS
SELECT 
    e.expert_id,
    e.name,
    e.personality,
    e.current_rank,
    e.leaderboard_score,
    e.overall_accuracy,
    e.total_predictions,
    e.confidence_calibration,
    e.consistency_score,
    e.council_appearances,
    e.specializations,
    e.status
FROM enhanced_expert_models e 
WHERE e.status = 'active'
ORDER BY e.leaderboard_score DESC;

-- Current AI Council
CREATE OR REPLACE VIEW current_ai_council AS
SELECT 
    acs.selection_id,
    acs.week,
    acs.season,
    unnest(acs.council_members) as expert_id,
    unnest(acs.council_ranks) as council_rank,
    unnest(acs.council_scores) as council_score,
    e.name,
    e.personality,
    e.overall_accuracy
FROM ai_council_selections acs
JOIN enhanced_expert_models e ON e.expert_id = ANY(acs.council_members)
WHERE acs.created_at = (SELECT MAX(created_at) FROM ai_council_selections)
ORDER BY council_rank;

-- Expert Performance Summary
CREATE OR REPLACE VIEW expert_performance_summary AS
SELECT 
    e.expert_id,
    e.name,
    e.current_rank,
    e.overall_accuracy,
    e.confidence_calibration,
    COUNT(ep.id) as recent_predictions,
    AVG(ep.confidence_overall) as avg_confidence,
    COUNT(CASE WHEN ep.ai_council_member = TRUE THEN 1 END) as council_predictions,
    MAX(ep.prediction_timestamp) as last_prediction
FROM enhanced_expert_models e
LEFT JOIN expert_predictions_enhanced ep ON e.expert_id = ep.expert_id 
    AND ep.prediction_timestamp > NOW() - INTERVAL '30 days'
GROUP BY e.expert_id, e.name, e.current_rank, e.overall_accuracy, e.confidence_calibration
ORDER BY e.current_rank;

-- ========================================
-- 10. Functions & Triggers
-- ========================================

-- Function to update expert performance after new predictions
CREATE OR REPLACE FUNCTION update_expert_performance()
RETURNS TRIGGER AS $$
BEGIN
    -- Update expert performance metrics
    UPDATE enhanced_expert_models 
    SET 
        total_predictions = total_predictions + 1,
        updated_at = NOW()
    WHERE expert_id = NEW.expert_id;
    
    -- If prediction has accuracy (game completed)
    IF NEW.prediction_accuracy IS NOT NULL THEN
        UPDATE enhanced_expert_models 
        SET 
            correct_predictions = correct_predictions + CASE WHEN NEW.prediction_accuracy > 0.5 THEN 1 ELSE 0 END,
            overall_accuracy = correct_predictions::DECIMAL / GREATEST(total_predictions, 1),
            updated_at = NOW()
        WHERE expert_id = NEW.expert_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for automatic expert performance updates
CREATE TRIGGER trigger_update_expert_performance
    AFTER INSERT OR UPDATE ON expert_predictions_enhanced
    FOR EACH ROW
    EXECUTE FUNCTION update_expert_performance();

-- Function to update expert rankings
CREATE OR REPLACE FUNCTION calculate_expert_rankings()
RETURNS void AS $$
DECLARE
    expert_record RECORD;
    new_rank INTEGER := 1;
BEGIN
    -- Calculate and update rankings based on leaderboard_score
    FOR expert_record IN 
        SELECT expert_id 
        FROM enhanced_expert_models 
        WHERE status = 'active'
        ORDER BY leaderboard_score DESC
    LOOP
        UPDATE enhanced_expert_models 
        SET 
            current_rank = new_rank,
            updated_at = NOW()
        WHERE expert_id = expert_record.expert_id;
        
        new_rank := new_rank + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 11. Initial Data Load
-- ========================================

-- Insert 15 expert models with personality data
INSERT INTO enhanced_expert_models (expert_id, name, personality, specializations, personality_traits) VALUES
('conservative_analyzer', 'The Conservative Analyzer', 'analytical', ARRAY['statistical_analysis', 'risk_management'], '{"risk_tolerance": 0.2, "data_reliance": 0.9, "contrarian_tendency": 0.1}'),
('risk_taking_gambler', 'The Risk Taking Gambler', 'aggressive', ARRAY['high_risk_high_reward', 'upset_detection'], '{"risk_tolerance": 0.9, "intuition_weight": 0.7, "contrarian_tendency": 0.8}'),
('contrarian_rebel', 'The Contrarian Rebel', 'contrarian', ARRAY['contrarian_plays', 'market_inefficiency'], '{"contrarian_tendency": 0.95, "crowd_skepticism": 0.9, "independent_thinking": 0.9}'),
('value_hunter', 'The Value Hunter', 'analytical', ARRAY['value_identification', 'market_analysis'], '{"value_seeking": 0.9, "patience": 0.8, "market_awareness": 0.9}'),
('momentum_rider', 'The Momentum Rider', 'trend_following', ARRAY['momentum_analysis', 'trend_identification'], '{"trend_following": 0.9, "momentum_belief": 0.9, "adaptation_speed": 0.8}'),
('fundamentalist_scholar', 'The Fundamentalist Scholar', 'research_driven', ARRAY['fundamental_analysis', 'deep_research'], '{"research_depth": 0.95, "data_quality_focus": 0.9, "methodical_approach": 0.9}'),
('chaos_theory_believer', 'The Chaos Theory Believer', 'complexity_focused', ARRAY['chaos_theory', 'complex_systems'], '{"complexity_comfort": 0.9, "pattern_recognition": 0.8, "non_linear_thinking": 0.9}'),
('gut_instinct_expert', 'The Gut Instinct Expert', 'intuitive', ARRAY['intuitive_analysis', 'instinct_based'], '{"intuition_weight": 0.9, "emotional_intelligence": 0.8, "rapid_decision": 0.9}'),
('statistics_purist', 'The Statistics Purist', 'mathematical', ARRAY['statistical_modeling', 'mathematical_analysis'], '{"mathematical_precision": 0.95, "model_trust": 0.9, "quantitative_focus": 0.95}'),
('trend_reversal_specialist', 'The Trend Reversal Specialist', 'contrarian', ARRAY['trend_reversal', 'mean_reversion'], '{"mean_reversion_belief": 0.9, "trend_skepticism": 0.8, "timing_focus": 0.9}'),
('popular_narrative_fader', 'The Popular Narrative Fader', 'contrarian', ARRAY['narrative_analysis', 'public_sentiment'], '{"narrative_skepticism": 0.9, "media_resistance": 0.9, "contrarian_tendency": 0.8}'),
('sharp_money_follower', 'The Sharp Money Follower', 'market_focused', ARRAY['sharp_action', 'line_movement'], '{"market_intelligence": 0.9, "sharp_identification": 0.9, "line_analysis": 0.9}'),
('underdog_champion', 'The Underdog Champion', 'underdog_focused', ARRAY['underdog_analysis', 'upset_detection'], '{"underdog_bias": 0.9, "upset_seeking": 0.8, "value_hunting": 0.9}'),
('consensus_follower', 'The Consensus Follower', 'consensus_driven', ARRAY['consensus_analysis', 'expert_aggregation'], '{"consensus_trust": 0.9, "expert_deference": 0.8, "crowd_wisdom_belief": 0.9}'),
('market_inefficiency_exploiter', 'The Market Inefficiency Exploiter', 'efficiency_focused', ARRAY['arbitrage_detection', 'inefficiency_identification'], '{"efficiency_analysis": 0.95, "arbitrage_seeking": 0.9, "systematic_approach": 0.9}');

-- ========================================
-- 12. RLS Policies (Optional)
-- ========================================

-- Enable RLS on sensitive tables (optional)
-- ALTER TABLE enhanced_expert_models ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE expert_predictions_enhanced ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE ai_council_consensus ENABLE ROW LEVEL SECURITY;

-- ========================================
-- 13. Performance Optimization
-- ========================================

-- Partitioning for large tables (implement if needed)
-- CREATE TABLE expert_predictions_enhanced_y2025 PARTITION OF expert_predictions_enhanced
--     FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Materialized views for expensive queries
CREATE MATERIALIZED VIEW mv_expert_weekly_performance AS
SELECT 
    e.expert_id,
    e.name,
    EXTRACT(WEEK FROM ep.prediction_timestamp) as week,
    EXTRACT(YEAR FROM ep.prediction_timestamp) as year,
    COUNT(*) as predictions_count,
    AVG(ep.prediction_accuracy) as avg_accuracy,
    AVG(ep.confidence_overall) as avg_confidence,
    COUNT(CASE WHEN ep.ai_council_member = TRUE THEN 1 END) as council_predictions
FROM enhanced_expert_models e
JOIN expert_predictions_enhanced ep ON e.expert_id = ep.expert_id
WHERE ep.prediction_accuracy IS NOT NULL
GROUP BY e.expert_id, e.name, EXTRACT(WEEK FROM ep.prediction_timestamp), EXTRACT(YEAR FROM ep.prediction_timestamp);

CREATE UNIQUE INDEX idx_mv_expert_weekly_performance ON mv_expert_weekly_performance(expert_id, year, week);

-- Refresh function for materialized view
CREATE OR REPLACE FUNCTION refresh_expert_performance_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_expert_weekly_performance;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 14. Data Validation Functions
-- ========================================

-- Function to validate prediction consistency
CREATE OR REPLACE FUNCTION validate_prediction_consistency(prediction_data JSONB)
RETURNS boolean AS $$
DECLARE
    winner TEXT;
    spread_pick TEXT;
    home_score INTEGER;
    away_score INTEGER;
BEGIN
    -- Extract key prediction components
    winner := prediction_data->>'winner_prediction';
    spread_pick := prediction_data->>'against_the_spread';
    home_score := (prediction_data->>'exact_score_home')::INTEGER;
    away_score := (prediction_data->>'exact_score_away')::INTEGER;
    
    -- Validate winner vs exact score consistency
    IF winner IS NOT NULL AND home_score IS NOT NULL AND away_score IS NOT NULL THEN
        IF (winner = 'home' AND home_score <= away_score) OR 
           (winner = 'away' AND away_score <= home_score) THEN
            RETURN FALSE;
        END IF;
    END IF;
    
    -- Add more validation rules as needed
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 15. Monitoring & Alerting
-- ========================================

-- Function to check system health
CREATE OR REPLACE FUNCTION check_expert_system_health()
RETURNS TABLE(
    metric_name TEXT,
    metric_value DECIMAL,
    status TEXT,
    details TEXT
) AS $$
BEGIN
    -- Check active expert count
    RETURN QUERY
    SELECT 
        'active_experts'::TEXT,
        COUNT(*)::DECIMAL,
        CASE WHEN COUNT(*) = 15 THEN 'healthy'::TEXT ELSE 'warning'::TEXT END,
        'Expected 15 active experts'::TEXT
    FROM enhanced_expert_models 
    WHERE status = 'active';
    
    -- Check recent prediction activity
    RETURN QUERY
    SELECT 
        'recent_predictions'::TEXT,
        COUNT(*)::DECIMAL,
        CASE WHEN COUNT(*) > 0 THEN 'healthy'::TEXT ELSE 'critical'::TEXT END,
        'Predictions in last 24 hours'::TEXT
    FROM expert_predictions_enhanced 
    WHERE prediction_timestamp > NOW() - INTERVAL '24 hours';
    
    -- Check AI Council status
    RETURN QUERY
    SELECT 
        'ai_council_size'::TEXT,
        array_length(council_members, 1)::DECIMAL,
        CASE WHEN array_length(council_members, 1) = 5 THEN 'healthy'::TEXT ELSE 'warning'::TEXT END,
        'Expected 5 council members'::TEXT
    FROM ai_council_selections 
    ORDER BY created_at DESC 
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 16. Sample Data for Testing
-- ========================================

-- Insert sample AI Council selection
INSERT INTO ai_council_selections (selection_id, week, season, council_members, council_ranks, council_scores)
VALUES (
    '2025_week_1',
    1,
    2025,
    ARRAY['conservative_analyzer', 'statistics_purist', 'sharp_money_follower', 'value_hunter', 'fundamentalist_scholar'],
    ARRAY[1, 2, 3, 4, 5],
    ARRAY[95.5, 94.2, 93.8, 93.1, 92.7]
);

-- ========================================
-- 17. Migration Completion
-- ========================================

-- Log migration completion
INSERT INTO migrations_log (migration_name, completed_at) 
VALUES ('020_enhanced_expert_competition_schema', NOW())
ON CONFLICT (migration_name) DO UPDATE SET completed_at = NOW();

SELECT 'Enhanced Expert Competition Schema migration completed successfully' as status