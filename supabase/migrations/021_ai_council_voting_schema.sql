-- AI Council Voting System Database Schema
-- Detailed schema for weighted voting mechanism and consensus building
-- Migration: 021_ai_council_voting_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- 1. Vote Weight Calculation Components
-- ========================================
CREATE TABLE vote_weight_components (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    calculation_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Weight Formula Components (Design Spec: 40% + 30% + 20% + 10%)
    category_accuracy_score DECIMAL(6,5) NOT NULL,        -- 40% weight
    overall_performance_score DECIMAL(6,5) NOT NULL,      -- 30% weight  
    recent_trend_score DECIMAL(6,5) NOT NULL,             -- 20% weight
    confidence_calibration_score DECIMAL(6,5) NOT NULL,   -- 10% weight
    
    -- Component Details
    category_accuracy_data JSONB DEFAULT '{}',
    performance_window_days INTEGER DEFAULT 28,
    trend_analysis_data JSONB DEFAULT '{}',
    calibration_analysis_data JSONB DEFAULT '{}',
    
    -- Final Weight Calculation
    raw_weight DECIMAL(8,6) NOT NULL,
    normalized_weight DECIMAL(6,5) NOT NULL,
    weight_rank INTEGER,
    
    -- Metadata
    calculation_method VARCHAR(50) DEFAULT 'weighted_formula_v1',
    category_context VARCHAR(100), -- spread, total, player_props, etc.
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for vote weights
CREATE INDEX idx_vote_weight_components_expert_game ON vote_weight_components(expert_id, game_id);
CREATE INDEX idx_vote_weight_components_timestamp ON vote_weight_components(calculation_timestamp DESC);
CREATE INDEX idx_vote_weight_components_weight ON vote_weight_components(normalized_weight DESC);

-- ========================================
-- 2. Individual Expert Votes
-- ========================================
CREATE TABLE expert_council_votes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vote_id VARCHAR(100) UNIQUE NOT NULL,
    expert_id VARCHAR(50) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    voting_round VARCHAR(50) NOT NULL, -- initial, revised, final
    vote_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Vote Details by Category
    game_outcome_vote JSONB NOT NULL DEFAULT '{}',
    betting_market_vote JSONB NOT NULL DEFAULT '{}',
    player_props_vote JSONB NOT NULL DEFAULT '{}',
    situational_vote JSONB NOT NULL DEFAULT '{}',
    
    -- Vote Confidence
    vote_confidence_overall DECIMAL(6,5) NOT NULL,
    vote_confidence_by_category JSONB DEFAULT '{}',
    confidence_justification TEXT,
    
    -- Vote Weight Information
    vote_weight DECIMAL(6,5) NOT NULL,
    weight_components JSONB NOT NULL DEFAULT '{}',
    weight_justification TEXT,
    
    -- Vote Reasoning
    vote_reasoning TEXT NOT NULL,
    key_factors TEXT[] DEFAULT '{}',
    disagreement_factors TEXT[] DEFAULT '{}',
    
    -- Vote Revision Information  
    original_vote_id VARCHAR(100), -- If this is a revision
    revision_reason TEXT,
    vote_changes JSONB DEFAULT '{}',
    
    -- Metadata
    expert_rank_at_vote INTEGER,
    council_position INTEGER, -- 1-5 ranking within council
    is_final_vote BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for expert votes
CREATE INDEX idx_expert_council_votes_expert_game ON expert_council_votes(expert_id, game_id);
CREATE INDEX idx_expert_council_votes_game_round ON expert_council_votes(game_id, voting_round);
CREATE INDEX idx_expert_council_votes_timestamp ON expert_council_votes(vote_timestamp DESC);
CREATE INDEX idx_expert_council_votes_weight ON expert_council_votes(vote_weight DESC);

-- ========================================
-- 3. Consensus Building Process
-- ========================================
CREATE TABLE consensus_building_process (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    process_id VARCHAR(100) UNIQUE NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    process_start_timestamp TIMESTAMP DEFAULT NOW(),
    process_end_timestamp TIMESTAMP,
    
    -- Council Composition
    council_members VARCHAR(50)[] NOT NULL,
    council_weights DECIMAL(6,5)[] NOT NULL,
    council_ranks INTEGER[] NOT NULL,
    
    -- Consensus Algorithm Configuration
    algorithm_version VARCHAR(50) DEFAULT 'weighted_average_v1',
    minimum_agreement_threshold DECIMAL(4,3) DEFAULT 0.600, -- 60% agreement
    disagreement_resolution_method VARCHAR(50) DEFAULT 'weighted_majority',
    
    -- Initial Votes Analysis
    initial_votes JSONB NOT NULL DEFAULT '{}',
    initial_disagreement_score DECIMAL(6,5),
    controversial_categories TEXT[] DEFAULT '{}',
    
    -- Consensus Calculation Steps
    consensus_steps JSONB NOT NULL DEFAULT '{}',
    weighted_averages JSONB NOT NULL DEFAULT '{}',
    outlier_detection JSONB DEFAULT '{}',
    
    -- Final Consensus Results
    final_consensus JSONB NOT NULL DEFAULT '{}',
    consensus_confidence DECIMAL(6,5) NOT NULL,
    consensus_uncertainty DECIMAL(6,5),
    agreement_percentage DECIMAL(5,2),
    
    -- Disagreement Analysis
    final_disagreement_score DECIMAL(6,5),
    minority_opinions JSONB DEFAULT '{}',
    controversy_flags TEXT[] DEFAULT '{}',
    
    -- Process Metadata
    total_iterations INTEGER DEFAULT 1,
    convergence_achieved BOOLEAN DEFAULT TRUE,
    process_duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for consensus building
CREATE INDEX idx_consensus_building_game ON consensus_building_process(game_id);
CREATE INDEX idx_consensus_building_timestamp ON consensus_building_process(process_start_timestamp DESC);
CREATE INDEX idx_consensus_building_disagreement ON consensus_building_process(final_disagreement_score DESC);

-- ========================================
-- 4. Natural Language Explanation Generation
-- ========================================
CREATE TABLE consensus_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    explanation_id VARCHAR(100) UNIQUE NOT NULL,
    consensus_process_id VARCHAR(100) REFERENCES consensus_building_process(process_id),
    game_id VARCHAR(100) NOT NULL,
    
    -- Explanation Components
    executive_summary TEXT NOT NULL,
    detailed_reasoning TEXT NOT NULL,
    key_factors_explanation TEXT NOT NULL,
    disagreement_explanation TEXT,
    confidence_explanation TEXT NOT NULL,
    
    -- Expert Contribution Explanations
    council_member_contributions JSONB NOT NULL DEFAULT '{}',
    weight_justifications JSONB NOT NULL DEFAULT '{}',
    individual_expert_highlights TEXT[] DEFAULT '{}',
    
    -- Prediction Category Explanations
    game_outcome_explanation TEXT,
    betting_market_explanation TEXT,
    player_props_explanation TEXT,
    situational_factors_explanation TEXT,
    
    -- Uncertainty & Risk Factors
    uncertainty_factors TEXT[] DEFAULT '{}',
    risk_assessment TEXT,
    alternative_scenarios TEXT[] DEFAULT '{}',
    
    -- Template & Generation Information
    explanation_template VARCHAR(50) DEFAULT 'comprehensive_v1',
    generation_method VARCHAR(50) DEFAULT 'template_based',
    language_style VARCHAR(50) DEFAULT 'professional',
    
    -- Quality Metrics
    explanation_completeness_score DECIMAL(4,3),
    readability_score DECIMAL(4,3),
    accuracy_of_explanation DECIMAL(6,5), -- Set after game completion
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for explanations
CREATE INDEX idx_consensus_explanations_process ON consensus_explanations(consensus_process_id);
CREATE INDEX idx_consensus_explanations_game ON consensus_explanations(game_id);
CREATE INDEX idx_consensus_explanations_timestamp ON consensus_explanations(created_at DESC);

-- ========================================
-- 5. Disagreement Detection & Analysis
-- ========================================
CREATE TABLE expert_disagreements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disagreement_id VARCHAR(100) UNIQUE NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    analysis_timestamp TIMESTAMP DEFAULT NOW(),
    
    -- Disagreement Scope
    disagreement_category VARCHAR(50) NOT NULL, -- game_outcome, spread, total, etc.
    disagreement_severity VARCHAR(20) NOT NULL, -- low, medium, high, extreme
    disagreement_type VARCHAR(50) NOT NULL, -- binary_split, multi_way, outlier_detection
    
    -- Expert Positions
    expert_positions JSONB NOT NULL DEFAULT '{}',
    position_clusters JSONB DEFAULT '{}',
    outlier_experts VARCHAR(50)[] DEFAULT '{}',
    
    -- Disagreement Metrics
    disagreement_score DECIMAL(6,5) NOT NULL,
    variance_measure DECIMAL(6,5),
    confidence_spread DECIMAL(6,5),
    weight_distribution JSONB DEFAULT '{}',
    
    -- Analysis Results
    majority_position JSONB NOT NULL DEFAULT '{}',
    minority_positions JSONB DEFAULT '{}',
    consensus_difficulty_score DECIMAL(6,5),
    
    -- Context Analysis
    disagreement_factors TEXT[] DEFAULT '{}',
    historical_context JSONB DEFAULT '{}',
    market_context JSONB DEFAULT '{}',
    
    -- Resolution Information
    resolution_method VARCHAR(50), -- weighted_average, majority_rule, hybrid
    resolution_confidence DECIMAL(6,5),
    resolution_explanation TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for disagreements
CREATE INDEX idx_expert_disagreements_game ON expert_disagreements(game_id);
CREATE INDEX idx_expert_disagreements_category ON expert_disagreements(disagreement_category);
CREATE INDEX idx_expert_disagreements_severity ON expert_disagreements(disagreement_severity);
CREATE INDEX idx_expert_disagreements_score ON expert_disagreements(disagreement_score DESC);

-- ========================================
-- 6. Historical Voting Performance
-- ========================================
CREATE TABLE voting_performance_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    performance_period VARCHAR(50) NOT NULL, -- daily, weekly, monthly
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Voting Metrics
    total_votes_cast INTEGER DEFAULT 0,
    council_participations INTEGER DEFAULT 0,
    average_vote_weight DECIMAL(6,5),
    weight_consistency DECIMAL(6,5),
    
    -- Accuracy Metrics
    vote_accuracy_overall DECIMAL(6,5),
    vote_accuracy_by_category JSONB DEFAULT '{}',
    consensus_contribution_score DECIMAL(6,5),
    
    -- Influence Metrics
    vote_influence_score DECIMAL(6,5),
    disagreement_frequency DECIMAL(6,5),
    minority_opinion_frequency DECIMAL(6,5),
    successful_minority_positions INTEGER DEFAULT 0,
    
    -- Confidence Metrics
    confidence_accuracy_correlation DECIMAL(6,5),
    confidence_calibration_score DECIMAL(6,5),
    overconfidence_incidents INTEGER DEFAULT 0,
    underconfidence_incidents INTEGER DEFAULT 0,
    
    -- Trend Analysis
    performance_trend VARCHAR(20), -- improving, declining, stable
    weight_trend VARCHAR(20), -- increasing, decreasing, stable
    influence_trend VARCHAR(20), -- growing, diminishing, stable
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for voting performance
CREATE INDEX idx_voting_performance_expert_period ON voting_performance_history(expert_id, performance_period, period_start);
CREATE INDEX idx_voting_performance_accuracy ON voting_performance_history(vote_accuracy_overall DESC);
CREATE INDEX idx_voting_performance_influence ON voting_performance_history(vote_influence_score DESC);

-- ========================================
-- 7. Views for Voting System
-- ========================================

-- Current Vote Weights View
CREATE OR REPLACE VIEW current_vote_weights AS
SELECT 
    vwc.expert_id,
    em.name as expert_name,
    vwc.game_id,
    vwc.normalized_weight,
    vwc.weight_rank,
    vwc.category_accuracy_score,
    vwc.overall_performance_score,
    vwc.recent_trend_score,
    vwc.confidence_calibration_score,
    vwc.calculation_timestamp
FROM vote_weight_components vwc
JOIN enhanced_expert_models em ON vwc.expert_id = em.expert_id
WHERE vwc.calculation_timestamp > NOW() - INTERVAL '1 day'
ORDER BY vwc.normalized_weight DESC;

-- Active Council Voting Status
CREATE OR REPLACE VIEW active_council_voting_status AS
SELECT 
    acs.selection_id,
    acs.week,
    acs.season,
    unnest(acs.council_members) as expert_id,
    unnest(acs.council_ranks) as council_rank,
    em.name,
    COUNT(ecv.id) as votes_cast_today,
    AVG(ecv.vote_weight) as avg_vote_weight
FROM ai_council_selections acs
JOIN enhanced_expert_models em ON em.expert_id = ANY(acs.council_members)
LEFT JOIN expert_council_votes ecv ON em.expert_id = ecv.expert_id 
    AND ecv.vote_timestamp > CURRENT_DATE
WHERE acs.created_at = (SELECT MAX(created_at) FROM ai_council_selections)
GROUP BY acs.selection_id, acs.week, acs.season, acs.council_members, acs.council_ranks, em.name
ORDER BY council_rank;

-- ========================================
-- 8. Functions for Voting System
-- ========================================

-- Function to calculate vote weights
CREATE OR REPLACE FUNCTION calculate_vote_weights(
    p_expert_id VARCHAR(50),
    p_game_id VARCHAR(100),
    p_category VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE(
    expert_id VARCHAR(50),
    raw_weight DECIMAL(8,6),
    normalized_weight DECIMAL(6,5),
    weight_components JSONB
) AS $$
DECLARE
    category_acc DECIMAL(6,5);
    overall_perf DECIMAL(6,5);
    recent_trend DECIMAL(6,5);
    confidence_cal DECIMAL(6,5);
    final_weight DECIMAL(8,6);
    weight_data JSONB;
BEGIN
    -- Get expert performance data (simplified calculation)
    SELECT 
        COALESCE(em.overall_accuracy, 0.5),
        COALESCE(em.confidence_calibration, 0.5),
        COALESCE(em.consistency_score, 0.5)
    INTO overall_perf, confidence_cal, category_acc
    FROM enhanced_expert_models em
    WHERE em.expert_id = p_expert_id;
    
    -- Calculate recent trend (simplified)
    recent_trend := COALESCE(overall_perf + (random() - 0.5) * 0.1, 0.5);
    
    -- Apply weight formula: Category(40%) + Overall(30%) + Trend(20%) + Calibration(10%)
    final_weight := (category_acc * 0.4) + (overall_perf * 0.3) + (recent_trend * 0.2) + (confidence_cal * 0.1);
    
    -- Create weight components JSON
    weight_data := jsonb_build_object(
        'category_accuracy', category_acc,
        'overall_performance', overall_perf,
        'recent_trend', recent_trend,
        'confidence_calibration', confidence_cal,
        'formula_weights', jsonb_build_object(
            'category_weight', 0.4,
            'performance_weight', 0.3,
            'trend_weight', 0.2,
            'calibration_weight', 0.1
        )
    );
    
    RETURN QUERY SELECT 
        p_expert_id,
        final_weight,
        LEAST(1.0, GREATEST(0.0, final_weight))::DECIMAL(6,5),
        weight_data;
END;
$$ LANGUAGE plpgsql;

-- Function to build consensus
CREATE OR REPLACE FUNCTION build_consensus(
    p_game_id VARCHAR(100),
    p_council_members VARCHAR(50)[],
    p_category VARCHAR(100) DEFAULT NULL
)
RETURNS TABLE(
    consensus_result JSONB,
    disagreement_score DECIMAL(6,5),
    consensus_confidence DECIMAL(6,5)
) AS $$
DECLARE
    expert_vote RECORD;
    weighted_sum DECIMAL(8,6) := 0;
    total_weight DECIMAL(8,6) := 0;
    vote_variance DECIMAL(8,6) := 0;
    consensus JSONB;
    disagreement DECIMAL(6,5);
    confidence DECIMAL(6,5);
BEGIN
    -- Simplified consensus calculation
    -- In real implementation, this would process all prediction categories
    
    FOR expert_vote IN 
        SELECT expert_id, vote_weight, game_outcome_vote
        FROM expert_council_votes
        WHERE game_id = p_game_id
        AND expert_id = ANY(p_council_members)
        AND is_final_vote = TRUE
    LOOP
        -- Accumulate weighted votes (simplified for demo)
        total_weight := total_weight + expert_vote.vote_weight;
    END LOOP;
    
    -- Calculate consensus (placeholder)
    consensus := jsonb_build_object(
        'winner_prediction', 'home',
        'consensus_method', 'weighted_average',
        'total_weight', total_weight
    );
    
    disagreement := COALESCE(random() * 0.3, 0.15); -- Placeholder
    confidence := COALESCE(1.0 - disagreement, 0.7); -- Placeholder
    
    RETURN QUERY SELECT consensus, disagreement, confidence;
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 9. Sample Data for Testing
-- ========================================

-- Insert sample vote weight components
INSERT INTO vote_weight_components (
    expert_id, game_id, category_accuracy_score, overall_performance_score,
    recent_trend_score, confidence_calibration_score, raw_weight, normalized_weight, weight_rank
) VALUES
('conservative_analyzer', 'test_game_1', 0.65, 0.70, 0.68, 0.72, 0.6850, 0.6850, 1),
('statistics_purist', 'test_game_1', 0.68, 0.65, 0.70, 0.75, 0.6845, 0.6845, 2),
('sharp_money_follower', 'test_game_1', 0.62, 0.72, 0.65, 0.68, 0.6710, 0.6710, 3),
('value_hunter', 'test_game_1', 0.60, 0.68, 0.67, 0.70, 0.6535, 0.6535, 4),
('fundamentalist_scholar', 'test_game_1', 0.58, 0.66, 0.69, 0.73, 0.6525, 0.6525, 5);

-- Migration completion log
INSERT INTO migrations_log (migration_name, completed_at) 
VALUES ('021_ai_council_voting_schema', NOW())
ON CONFLICT (migration_name) DO UPDATE SET completed_at = NOW();

SELECT 'AI Council Voting Schema migration completed successfully' as status;