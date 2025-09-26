-- Performance Analytics and Tracking System Database Schema
-- Comprehensive schema for expert performance monitoring and analysis
-- Migration: 022_performance_analytics_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 1. Multi-Dimensional Accuracy Tracking
-- ========================================
CREATE TABLE accuracy_tracking_detailed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    tracking_period VARCHAR(50) NOT NULL, -- daily, weekly, monthly, seasonal
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Overall Accuracy Metrics
    total_predictions INTEGER DEFAULT 0,
    correct_predictions INTEGER DEFAULT 0,
    overall_accuracy DECIMAL(6,5) NOT NULL DEFAULT 0,
    accuracy_confidence_interval DECIMAL(6,5),
    
    -- Category-Specific Accuracy
    game_outcome_accuracy DECIMAL(6,5),
    spread_accuracy DECIMAL(6,5),
    total_accuracy DECIMAL(6,5),
    player_props_accuracy DECIMAL(6,5),
    situational_accuracy DECIMAL(6,5),
    
    -- Advanced Accuracy Metrics
    brier_score DECIMAL(6,5),                    -- Probability accuracy score
    log_loss DECIMAL(6,5),                       -- Logarithmic loss
    calibration_score DECIMAL(6,5),              -- Confidence calibration
    sharpness_score DECIMAL(6,5),                -- Prediction sharpness
    
    -- Accuracy by Game Context
    favorite_accuracy DECIMAL(6,5),              -- Accuracy when picking favorites
    underdog_accuracy DECIMAL(6,5),              -- Accuracy when picking underdogs
    close_game_accuracy DECIMAL(6,5),            -- Games with spread < 3 points
    blowout_accuracy DECIMAL(6,5),               -- Games with spread > 10 points
    
    -- Accuracy by Situational Factors
    weather_game_accuracy DECIMAL(6,5),          -- Outdoor/weather games
    primetime_accuracy DECIMAL(6,5),             -- National TV games
    divisional_game_accuracy DECIMAL(6,5),       -- Division games
    playoff_accuracy DECIMAL(6,5),               -- Playoff games
    
    -- Streak Analysis
    current_correct_streak INTEGER DEFAULT 0,
    current_incorrect_streak INTEGER DEFAULT 0,
    longest_correct_streak INTEGER DEFAULT 0,
    longest_incorrect_streak INTEGER DEFAULT 0,
    
    -- Improvement Metrics
    accuracy_trend VARCHAR(20),                  -- improving, declining, stable
    trend_strength DECIMAL(6,5),                 -- Strength of trend
    period_over_period_change DECIMAL(6,5),      -- Change from previous period
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for accuracy tracking
CREATE INDEX idx_accuracy_tracking_expert_period ON accuracy_tracking_detailed(expert_id, tracking_period, period_start);
CREATE INDEX idx_accuracy_tracking_overall ON accuracy_tracking_detailed(overall_accuracy DESC);
CREATE INDEX idx_accuracy_tracking_trend ON accuracy_tracking_detailed(accuracy_trend);
CREATE INDEX idx_accuracy_tracking_brier ON accuracy_tracking_detailed(brier_score);

-- ========================================
-- 2. Performance Trend Analysis
-- ========================================
CREATE TABLE performance_trend_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    analysis_type VARCHAR(50) NOT NULL,        -- rolling_average, regression, seasonal
    
    -- Trend Detection
    trend_direction VARCHAR(20) NOT NULL,      -- improving, declining, stable, volatile
    trend_strength DECIMAL(6,5) NOT NULL,      -- 0-1 strength of trend
    trend_duration_days INTEGER,               -- How long trend has been active
    trend_significance DECIMAL(6,5),           -- Statistical significance
    
    -- Performance Trajectory
    performance_velocity DECIMAL(6,5),         -- Rate of performance change
    performance_acceleration DECIMAL(6,5),     -- Change in velocity
    projected_performance DECIMAL(6,5),        -- Projected future performance
    confidence_in_projection DECIMAL(6,5),     -- Confidence in projection
    
    -- Comparison Metrics
    peer_ranking_trend VARCHAR(20),            -- improving, declining, stable
    relative_performance_change DECIMAL(6,5),  -- vs peer group
    market_performance_correlation DECIMAL(6,5), -- Correlation with market accuracy
    
    -- Volatility Analysis
    performance_volatility DECIMAL(6,5),       -- Standard deviation of performance
    volatility_trend VARCHAR(20),              -- increasing, decreasing, stable
    risk_adjusted_performance DECIMAL(6,5),    -- Performance / volatility
    
    -- Seasonal Analysis
    seasonal_pattern JSONB DEFAULT '{}',       -- Performance by time of season
    monthly_performance JSONB DEFAULT '{}',    -- Performance by month
    day_of_week_performance JSONB DEFAULT '{}', -- Performance by day of week
    
    -- Statistical Metrics
    r_squared DECIMAL(6,5),                    -- Trend fit quality
    p_value DECIMAL(6,5),                      -- Statistical significance
    confidence_interval_lower DECIMAL(6,5),    -- Lower CI bound
    confidence_interval_upper DECIMAL(6,5),    -- Upper CI bound
    
    -- Analysis Metadata
    data_points_analyzed INTEGER,
    analysis_method VARCHAR(50),
    analysis_parameters JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for trend analysis
CREATE INDEX idx_performance_trend_expert_date ON performance_trend_analysis(expert_id, analysis_date DESC);
CREATE INDEX idx_performance_trend_direction ON performance_trend_analysis(trend_direction);
CREATE INDEX idx_performance_trend_strength ON performance_trend_analysis(trend_strength DESC);
CREATE INDEX idx_performance_trend_significance ON performance_trend_analysis(trend_significance DESC);

-- ========================================
-- 3. Ranking System Detailed
-- ========================================
CREATE TABLE ranking_system_detailed (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ranking_id VARCHAR(100) UNIQUE NOT NULL,
    ranking_date DATE NOT NULL,
    ranking_type VARCHAR(50) NOT NULL,         -- weekly, monthly, seasonal
    
    -- Ranking Configuration
    ranking_algorithm VARCHAR(50) DEFAULT 'weighted_composite',
    algorithm_version VARCHAR(20) DEFAULT 'v1.0',
    ranking_weights JSONB NOT NULL DEFAULT '{}',
    
    -- Expert Rankings
    expert_rankings JSONB NOT NULL DEFAULT '{}', -- Array of expert ranking data
    total_experts_ranked INTEGER,
    
    -- Ranking Component Scores
    accuracy_component_weights JSONB DEFAULT '{}',
    consistency_component_weights JSONB DEFAULT '{}',
    trend_component_weights JSONB DEFAULT '{}',
    specialization_component_weights JSONB DEFAULT '{}',
    
    -- Ranking Statistics
    score_distribution JSONB DEFAULT '{}',     -- Distribution of scores
    ranking_volatility DECIMAL(6,5),           -- How much rankings changed
    consensus_level DECIMAL(6,5),              -- Agreement between ranking methods
    
    -- Movement Analysis
    promotions INTEGER DEFAULT 0,              -- Experts moved up
    demotions INTEGER DEFAULT 0,               -- Experts moved down
    new_entrants INTEGER DEFAULT 0,            -- New experts in top ranks
    
    -- Quality Metrics
    ranking_stability DECIMAL(6,5),            -- How stable rankings are
    predictive_power DECIMAL(6,5),             -- How well rankings predict future performance
    fairness_score DECIMAL(6,5),               -- Ranking fairness assessment
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for ranking system
CREATE INDEX idx_ranking_system_date ON ranking_system_detailed(ranking_date DESC);
CREATE INDEX idx_ranking_system_type ON ranking_system_detailed(ranking_type);
CREATE INDEX idx_ranking_system_volatility ON ranking_system_detailed(ranking_volatility);

-- ========================================
-- 4. Category-Specific Performance Analysis
-- ========================================
CREATE TABLE category_performance_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    category_id VARCHAR(50) NOT NULL,
    analysis_period VARCHAR(50) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Category Performance Metrics
    category_predictions INTEGER DEFAULT 0,
    category_correct INTEGER DEFAULT 0,
    category_accuracy DECIMAL(6,5) NOT NULL,
    category_improvement DECIMAL(6,5),
    
    -- Relative Performance
    peer_average_accuracy DECIMAL(6,5),        -- Average accuracy in this category
    percentile_rank DECIMAL(5,2),              -- Percentile rank vs peers
    category_ranking INTEGER,                   -- Rank in this category
    
    -- Specialization Analysis
    specialization_strength DECIMAL(6,5),      -- How much better than average
    specialization_consistency DECIMAL(6,5),   -- Consistency in this category
    specialization_trend VARCHAR(20),          -- improving, declining, stable
    
    -- Context-Specific Performance
    high_confidence_accuracy DECIMAL(6,5),     -- Accuracy when highly confident
    low_confidence_accuracy DECIMAL(6,5),      -- Accuracy when less confident
    difficult_prediction_accuracy DECIMAL(6,5), -- Performance on hard predictions
    
    -- Game Situation Performance
    early_season_accuracy DECIMAL(6,5),        -- First 8 weeks
    late_season_accuracy DECIMAL(6,5),         -- Last 8 weeks
    high_stakes_accuracy DECIMAL(6,5),         -- Important games
    
    -- Statistical Analysis
    statistical_significance DECIMAL(6,5),     -- Significance of specialization
    confidence_interval DECIMAL(6,5),          -- CI for accuracy estimate
    sample_size_adequacy BOOLEAN,              -- Sufficient data for analysis
    
    -- Category-Specific Insights
    strengths TEXT[] DEFAULT '{}',              -- Identified strengths
    weaknesses TEXT[] DEFAULT '{}',             -- Identified weaknesses
    improvement_opportunities TEXT[] DEFAULT '{}', -- Areas for improvement
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for category performance
CREATE INDEX idx_category_performance_expert_category ON category_performance_analysis(expert_id, category_id);
CREATE INDEX idx_category_performance_accuracy ON category_performance_analysis(category_accuracy DESC);
CREATE INDEX idx_category_performance_specialization ON category_performance_analysis(specialization_strength DESC);
CREATE INDEX idx_category_performance_period ON category_performance_analysis(analysis_period, period_start);

-- ========================================
-- 5. Confidence Calibration Analysis
-- ========================================
CREATE TABLE confidence_calibration_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    analysis_period VARCHAR(50) NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Calibration Metrics
    overall_calibration_score DECIMAL(6,5) NOT NULL,
    calibration_slope DECIMAL(6,5),            -- Slope of calibration curve
    calibration_intercept DECIMAL(6,5),        -- Intercept of calibration curve
    calibration_r_squared DECIMAL(6,5),        -- Quality of calibration fit
    
    -- Calibration by Confidence Bins
    confidence_bin_10_20 JSONB DEFAULT '{}',   -- 10-20% confidence predictions
    confidence_bin_20_30 JSONB DEFAULT '{}',   -- 20-30% confidence predictions
    confidence_bin_30_40 JSONB DEFAULT '{}',   -- 30-40% confidence predictions
    confidence_bin_40_50 JSONB DEFAULT '{}',   -- 40-50% confidence predictions
    confidence_bin_50_60 JSONB DEFAULT '{}',   -- 50-60% confidence predictions
    confidence_bin_60_70 JSONB DEFAULT '{}',   -- 60-70% confidence predictions
    confidence_bin_70_80 JSONB DEFAULT '{}',   -- 70-80% confidence predictions
    confidence_bin_80_90 JSONB DEFAULT '{}',   -- 80-90% confidence predictions
    confidence_bin_90_100 JSONB DEFAULT '{}',  -- 90-100% confidence predictions
    
    -- Over/Under Confidence Analysis
    overconfidence_score DECIMAL(6,5),         -- Degree of overconfidence
    underconfidence_score DECIMAL(6,5),        -- Degree of underconfidence
    confidence_bias VARCHAR(20),               -- overconfident, underconfident, well_calibrated
    
    -- Calibration Trends
    calibration_trend VARCHAR(20),             -- improving, declining, stable
    calibration_volatility DECIMAL(6,5),       -- Volatility of calibration
    recent_calibration_change DECIMAL(6,5),    -- Recent change in calibration
    
    -- Category-Specific Calibration
    game_outcome_calibration DECIMAL(6,5),
    spread_calibration DECIMAL(6,5),
    total_calibration DECIMAL(6,5),
    player_props_calibration DECIMAL(6,5),
    situational_calibration DECIMAL(6,5),
    
    -- Reliability Metrics
    reliability_score DECIMAL(6,5),            -- How reliable confidence estimates are
    resolution_score DECIMAL(6,5),             -- Ability to discriminate outcomes
    uncertainty_score DECIMAL(6,5),            -- Appropriate uncertainty assessment
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for confidence calibration
CREATE INDEX idx_confidence_calibration_expert_period ON confidence_calibration_analysis(expert_id, analysis_period, period_start);
CREATE INDEX idx_confidence_calibration_score ON confidence_calibration_analysis(overall_calibration_score DESC);
CREATE INDEX idx_confidence_calibration_bias ON confidence_calibration_analysis(confidence_bias);

-- ========================================
-- 6. Comparative Performance Analysis
-- ========================================
CREATE TABLE comparative_performance_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id VARCHAR(100) UNIQUE NOT NULL,
    analysis_date DATE NOT NULL,
    comparison_type VARCHAR(50) NOT NULL,      -- peer_comparison, historical_comparison, market_comparison
    
    -- Comparison Configuration
    comparison_period_days INTEGER,
    experts_included VARCHAR(50)[] DEFAULT '{}',
    comparison_metrics TEXT[] DEFAULT '{}',
    
    -- Performance Comparisons
    expert_performance_matrix JSONB NOT NULL DEFAULT '{}',
    relative_rankings JSONB NOT NULL DEFAULT '{}',
    performance_gaps JSONB DEFAULT '{}',
    
    -- Statistical Analysis
    anova_results JSONB DEFAULT '{}',          -- Analysis of variance results
    correlation_matrix JSONB DEFAULT '{}',     -- Expert performance correlations
    cluster_analysis JSONB DEFAULT '{}',       -- Performance clusters
    
    -- Benchmark Comparisons
    market_consensus_comparison JSONB DEFAULT '{}',
    random_baseline_comparison JSONB DEFAULT '{}',
    simple_models_comparison JSONB DEFAULT '{}',
    
    -- Competitive Analysis
    competitive_advantages JSONB DEFAULT '{}', -- Where each expert excels
    competitive_disadvantages JSONB DEFAULT '{}', -- Where each expert struggles
    market_positioning JSONB DEFAULT '{}',     -- Position vs competition
    
    -- Insights and Recommendations
    top_performers TEXT[] DEFAULT '{}',
    improvement_candidates TEXT[] DEFAULT '{}',
    specialization_opportunities JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for comparative analysis
CREATE INDEX idx_comparative_performance_date ON comparative_performance_analysis(analysis_date DESC);
CREATE INDEX idx_comparative_performance_type ON comparative_performance_analysis(comparison_type);

-- ========================================
-- 7. Real-Time Performance Dashboard Views
-- ========================================

-- Real-Time Expert Performance Dashboard
CREATE OR REPLACE VIEW realtime_expert_performance AS
SELECT 
    em.expert_id,
    em.name,
    em.current_rank,
    em.overall_accuracy,
    em.confidence_calibration,
    em.consistency_score,
    
    -- Recent Performance (Last 7 days)
    COUNT(ep.id) FILTER (WHERE ep.prediction_timestamp > NOW() - INTERVAL '7 days') as predictions_last_7_days,
    AVG(ep.prediction_accuracy) FILTER (WHERE ep.prediction_timestamp > NOW() - INTERVAL '7 days') as accuracy_last_7_days,
    AVG(ep.confidence_overall) FILTER (WHERE ep.prediction_timestamp > NOW() - INTERVAL '7 days') as avg_confidence_last_7_days,
    
    -- Council Status
    em.council_appearances,
    (SELECT COUNT(*) FROM ai_council_selections acs WHERE em.expert_id = ANY(acs.council_members) 
     AND acs.created_at > NOW() - INTERVAL '30 days') as council_selections_last_30_days,
    
    -- Performance Trend
    (SELECT trend_direction FROM performance_trend_analysis pta 
     WHERE pta.expert_id = em.expert_id 
     ORDER BY pta.analysis_date DESC LIMIT 1) as current_trend,
     
    -- Latest Update
    em.updated_at
    
FROM enhanced_expert_models em
LEFT JOIN expert_predictions_enhanced ep ON em.expert_id = ep.expert_id
WHERE em.status = 'active'
GROUP BY em.expert_id, em.name, em.current_rank, em.overall_accuracy, 
         em.confidence_calibration, em.consistency_score, em.council_appearances, em.updated_at
ORDER BY em.current_rank;

-- Category Performance Leaderboard
CREATE OR REPLACE VIEW category_performance_leaderboard AS
SELECT 
    category_id,
    expert_id,
    category_accuracy,
    category_ranking,
    specialization_strength,
    percentile_rank,
    ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY category_accuracy DESC) as category_rank
FROM category_performance_analysis cpa
WHERE analysis_period = 'monthly'
AND period_end = (SELECT MAX(period_end) FROM category_performance_analysis WHERE analysis_period = 'monthly')
ORDER BY category_id, category_rank;

-- ========================================
-- 8. Performance Analytics Functions
-- ========================================

-- Function to calculate comprehensive performance score
CREATE OR REPLACE FUNCTION calculate_comprehensive_performance_score(
    p_expert_id VARCHAR(50),
    p_period_days INTEGER DEFAULT 30
)
RETURNS TABLE(
    performance_score DECIMAL(8,4),
    score_components JSONB,
    score_explanation TEXT
) AS $$
DECLARE
    accuracy_score DECIMAL(6,5);
    consistency_score DECIMAL(6,5);
    trend_score DECIMAL(6,5);
    calibration_score DECIMAL(6,5);
    specialization_score DECIMAL(6,5);
    final_score DECIMAL(8,4);
    components JSONB;
    explanation TEXT;
BEGIN
    -- Get component scores (simplified calculation)
    SELECT COALESCE(overall_accuracy, 0.5) INTO accuracy_score
    FROM enhanced_expert_models WHERE expert_id = p_expert_id;
    
    SELECT COALESCE(em.consistency_score, 0.5) INTO consistency_score
    FROM enhanced_expert_models em WHERE em.expert_id = p_expert_id;
    
    SELECT COALESCE(em.confidence_calibration, 0.5) INTO calibration_score
    FROM enhanced_expert_models em WHERE em.expert_id = p_expert_id;
    
    SELECT COALESCE(em.specialization_strength, 0.5) INTO specialization_score
    FROM enhanced_expert_models em WHERE em.expert_id = p_expert_id;
    
    -- Calculate trend score from recent analysis
    SELECT COALESCE(trend_strength, 0.5) INTO trend_score
    FROM performance_trend_analysis 
    WHERE expert_id = p_expert_id 
    ORDER BY analysis_date DESC 
    LIMIT 1;
    
    -- Calculate weighted final score
    final_score := (accuracy_score * 0.35) + (consistency_score * 0.25) + 
                   (trend_score * 0.20) + (calibration_score * 0.10) + 
                   (specialization_score * 0.10);
    
    -- Build components JSON
    components := jsonb_build_object(
        'accuracy_score', accuracy_score,
        'consistency_score', consistency_score,
        'trend_score', trend_score,
        'calibration_score', calibration_score,
        'specialization_score', specialization_score,
        'weights', jsonb_build_object(
            'accuracy', 0.35,
            'consistency', 0.25,
            'trend', 0.20,
            'calibration', 0.10,
            'specialization', 0.10
        )
    );
    
    explanation := format('Performance score %.4f calculated from accuracy (%.3f), consistency (%.3f), trend (%.3f), calibration (%.3f), and specialization (%.3f)',
                         final_score, accuracy_score, consistency_score, trend_score, calibration_score, specialization_score);
    
    RETURN QUERY SELECT final_score, components, explanation;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 9. Sample Data for Testing
-- ========================================

-- Insert sample accuracy tracking data
INSERT INTO accuracy_tracking_detailed (
    expert_id, tracking_period, period_start, period_end, total_predictions, correct_predictions,
    overall_accuracy, game_outcome_accuracy, spread_accuracy, total_accuracy
) VALUES
('conservative_analyzer', 'weekly', '2025-01-01', '2025-01-07', 15, 9, 0.60000, 0.65000, 0.58000, 0.62000),
('statistics_purist', 'weekly', '2025-01-01', '2025-01-07', 15, 10, 0.66667, 0.70000, 0.62000, 0.68000),
('sharp_money_follower', 'weekly', '2025-01-01', '2025-01-07', 15, 8, 0.53333, 0.58000, 0.55000, 0.50000);

-- Migration completion log
INSERT INTO migrations_log (migration_name, completed_at) 
VALUES ('022_performance_analytics_schema', NOW())
ON CONFLICT (migration_name) DO UPDATE SET completed_at = NOW();

SELECT 'Performance Analytics Schema migration completed successfully' as status;