-- Migration: Enhanced Episodic Memory & Causal Learning System
-- Purpose: Enable deep autonomous learning with reasoning chains and belief evolution
-- Date: 2025-01-16

-- ============================================================================
-- 1. REASONING CHAINS - Why each prediction was made
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_reasoning_chains (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    game_id TEXT NOT NULL,
    prediction_timestamp TIMESTAMP DEFAULT NOW(),

    -- The actual prediction
    prediction JSONB NOT NULL, -- {winner: "BUF", spread: -3, total: 45}
    confidence_scores JSONB NOT NULL, -- {overall: 0.75, winner: 0.8, spread: 0.65}

    -- The reasoning behind it (THIS IS KEY!)
    reasoning_factors JSONB NOT NULL,
    /* Example:
    [
        {
            "factor": "road_performance",
            "value": "Buffalo 5-1 on road",
            "weight": 0.65,
            "confidence": 0.8,
            "source": "season_stats"
        },
        {
            "factor": "primetime_history",
            "value": "Jets 2-8 in primetime",
            "weight": 0.45,
            "confidence": 0.6,
            "source": "historical_pattern"
        },
        {
            "factor": "divisional_tendency",
            "value": "Divisional games average 3.2 pts closer",
            "weight": 0.30,
            "confidence": 0.7,
            "source": "learned_principle"
        }
    ]
    */

    -- What the expert was "thinking"
    internal_monologue TEXT, -- "Jets look weak but divisional games are tricky..."

    -- Metadata
    model_version TEXT DEFAULT 'v1.0',
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_reasoning_expert_game (expert_id, game_id),
    INDEX idx_reasoning_timestamp (prediction_timestamp DESC)
);

-- ============================================================================
-- 2. BELIEF REVISIONS - How experts change their minds
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_belief_revisions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    revision_timestamp TIMESTAMP DEFAULT NOW(),

    -- What belief changed
    belief_category TEXT NOT NULL, -- 'factor_importance', 'pattern_recognition', 'correlation'
    belief_key TEXT NOT NULL, -- 'home_field_advantage', 'weather_impact', etc.

    -- The change
    old_belief JSONB NOT NULL,
    /* Example:
    {
        "statement": "Home field worth 3 points",
        "confidence": 0.8,
        "based_on": "conventional wisdom"
    }
    */

    new_belief JSONB NOT NULL,
    /* Example:
    {
        "statement": "Home field worth 2.1 points in division, 3.5 points out of division",
        "confidence": 0.85,
        "based_on": "42 games analyzed"
    }
    */

    -- Why it changed
    revision_trigger TEXT NOT NULL, -- 'prediction_failure', 'pattern_discovered', 'peer_learning'
    supporting_evidence JSONB NOT NULL, -- Game IDs and outcomes that triggered this

    -- Causal chain
    causal_reasoning TEXT,
    /* Example:
    "Previously believed all home games equal. After analyzing 42 games:
    - Division rivals know stadium quirks (less advantage)
    - Crowd energy higher for non-division games
    - Weather familiarity matters less in division (both teams adapted)"
    */

    impact_score FLOAT, -- How much this belief change affects predictions (0-1)

    INDEX idx_belief_expert (expert_id),
    INDEX idx_belief_category (belief_category),
    INDEX idx_belief_impact (impact_score DESC)
);

-- ============================================================================
-- 3. EPISODIC MEMORIES - Specific game experiences
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_episodic_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    game_id TEXT NOT NULL,
    memory_type TEXT NOT NULL, -- 'success', 'failure', 'surprise', 'validation'

    -- What happened
    prediction_summary JSONB NOT NULL,
    actual_outcome JSONB NOT NULL,
    accuracy_scores JSONB NOT NULL, -- {winner: 1.0, spread: 0.2, total: 0.8}

    -- What was learned
    lesson_learned TEXT NOT NULL,
    /* Example:
    "Underestimated Jets home crowd impact in division rivalry.
    Monday night + division game + home crowd = larger swing than model predicted"
    */

    -- Emotional encoding (for personality-driven experts)
    emotional_weight FLOAT DEFAULT 0.5, -- How "memorable" this was (0-1)
    surprise_factor FLOAT DEFAULT 0.5, -- How unexpected (0-1)

    -- For memory consolidation
    access_count INT DEFAULT 0, -- How often this memory is referenced
    last_accessed TIMESTAMP,
    memory_strength FLOAT DEFAULT 1.0, -- Decays over time unless reinforced

    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_episodic_expert (expert_id),
    INDEX idx_episodic_game (game_id),
    INDEX idx_episodic_strength (memory_strength DESC)
);

-- ============================================================================
-- 4. LEARNED PRINCIPLES - Compressed wisdom from many games
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_learned_principles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,

    principle_category TEXT NOT NULL, -- 'weather', 'scheduling', 'matchups', 'trends'
    principle_statement TEXT NOT NULL,
    /* Example:
    "West coast teams traveling east for 1PM games underperform by 2.3 points on average"
    */

    -- Statistical backing
    supporting_games_count INT NOT NULL,
    confidence_level FLOAT NOT NULL, -- Statistical confidence (0-1)
    effect_size FLOAT, -- How much this impacts predictions

    -- Evidence
    supporting_evidence JSONB NOT NULL, -- Summary stats, not every game
    exceptions_noted JSONB, -- When this principle doesn't apply

    -- Metadata
    discovered_at TIMESTAMP DEFAULT NOW(),
    last_validated TIMESTAMP,
    times_applied INT DEFAULT 0,
    success_rate FLOAT, -- When applied, how often was it right?

    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_principles_expert (expert_id),
    INDEX idx_principles_category (principle_category),
    INDEX idx_principles_active (is_active, confidence_level DESC)
);

-- ============================================================================
-- 5. MEMORY COMPRESSION EVENTS - Hierarchical summarization
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_memory_compressions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    compression_timestamp TIMESTAMP DEFAULT NOW(),

    -- What got compressed
    memory_type TEXT NOT NULL, -- 'episodic_batch', 'season_summary', 'pattern_extraction'
    source_memory_ids JSONB NOT NULL, -- UUIDs of compressed memories
    source_date_range JSONB NOT NULL, -- {start: "2025-01-01", end: "2025-01-31"}

    -- The compressed knowledge
    compressed_summary JSONB NOT NULL,
    /* Example for season summary:
    {
        "games_analyzed": 16,
        "overall_accuracy": 0.621,
        "best_factors": ["divisional_history", "rest_advantage"],
        "worst_factors": ["weather", "injury_reports"],
        "key_learnings": [
            "Overvalued weather in outdoor stadiums",
            "Undervalued rest differential > 3 days"
        ],
        "belief_shifts": 3,
        "major_surprises": ["NYJ upset over BUF Week 2"]
    }
    */

    compression_ratio FLOAT, -- Original size / compressed size
    information_loss FLOAT, -- Estimated % of details lost (0-1)

    INDEX idx_compression_expert (expert_id),
    INDEX idx_compression_date (compression_timestamp DESC)
);

-- ============================================================================
-- 6. FACTOR DISCOVERY - New patterns experts identify
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_discovered_factors (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,

    factor_name TEXT NOT NULL,
    factor_description TEXT NOT NULL,
    /* Example:
    "Thursday games after Monday night games show 4.1 point underperformance"
    */

    -- How it was discovered
    discovery_method TEXT NOT NULL, -- 'correlation_analysis', 'pattern_mining', 'peer_suggestion'
    discovery_timestamp TIMESTAMP DEFAULT NOW(),

    -- Statistical validation
    correlation_strength FLOAT, -- -1 to 1
    p_value FLOAT, -- Statistical significance
    sample_size INT,

    -- How to use it
    calculation_formula TEXT, -- Python expression or SQL
    required_data_points JSONB, -- What data is needed to calculate

    -- Track performance
    times_used INT DEFAULT 0,
    successful_applications INT DEFAULT 0,
    current_weight FLOAT DEFAULT 0.1, -- How much this factors into predictions

    -- Adoption by other experts
    shared_with_peers BOOLEAN DEFAULT FALSE,
    adopted_by_experts JSONB DEFAULT '[]', -- List of expert_ids using this

    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_discovered_expert (expert_id),
    INDEX idx_discovered_active (is_active, correlation_strength DESC)
);

-- ============================================================================
-- 7. INTERNAL CONFIDENCE TRACKING - Meta-cognition
-- ============================================================================

CREATE TABLE IF NOT EXISTS expert_confidence_calibration (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,

    -- When expert said "I'm 80% confident", how often were they right?
    confidence_bucket FLOAT NOT NULL, -- 0.5, 0.6, 0.7, 0.8, 0.9
    predicted_count INT DEFAULT 0,
    actual_success_count INT DEFAULT 0,
    calibration_score FLOAT, -- actual_success_rate / confidence_bucket

    last_updated TIMESTAMP DEFAULT NOW(),

    UNIQUE(expert_id, confidence_bucket),
    INDEX idx_calibration_expert (expert_id)
);

-- ============================================================================
-- FUNCTIONS FOR INTELLIGENT QUERIES
-- ============================================================================

-- Function to get most impactful belief revisions for an expert
CREATE OR REPLACE FUNCTION get_impactful_belief_revisions(
    p_expert_id TEXT,
    p_limit INT DEFAULT 5
) RETURNS TABLE (
    belief_key TEXT,
    old_statement TEXT,
    new_statement TEXT,
    impact_score FLOAT,
    games_analyzed INT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        br.belief_key,
        br.old_belief->>'statement' as old_statement,
        br.new_belief->>'statement' as new_statement,
        br.impact_score,
        (br.new_belief->>'based_on')::INT as games_analyzed
    FROM expert_belief_revisions br
    WHERE br.expert_id = p_expert_id
    ORDER BY br.impact_score DESC, br.revision_timestamp DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to find similar past games for learning
CREATE OR REPLACE FUNCTION find_similar_games_for_learning(
    p_expert_id TEXT,
    p_current_context JSONB,
    p_limit INT DEFAULT 5
) RETURNS TABLE (
    game_id TEXT,
    similarity_score FLOAT,
    lesson_learned TEXT,
    prediction_accuracy FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        em.game_id,
        1 - (em.prediction_summary <-> p_current_context)::FLOAT as similarity_score,
        em.lesson_learned,
        (em.accuracy_scores->>'overall')::FLOAT as prediction_accuracy
    FROM expert_episodic_memories em
    WHERE em.expert_id = p_expert_id
    AND em.memory_strength > 0.3
    ORDER BY em.prediction_summary <-> p_current_context
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to compress old memories into principles
CREATE OR REPLACE FUNCTION compress_expert_memories(
    p_expert_id TEXT,
    p_older_than_days INT DEFAULT 90
) RETURNS TEXT AS $$
DECLARE
    v_compressed_count INT;
    v_principle_extracted TEXT;
BEGIN
    -- Implementation would:
    -- 1. Find memories older than threshold
    -- 2. Group by patterns
    -- 3. Extract principles
    -- 4. Create compression record
    -- 5. Reduce memory_strength of original memories

    -- Placeholder for complex logic
    RETURN 'Compressed ' || v_compressed_count || ' memories into principles';
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTONOMOUS LEARNING
-- ============================================================================

-- Trigger to update belief revisions after game results
CREATE OR REPLACE FUNCTION trigger_belief_revision_check()
RETURNS TRIGGER AS $$
DECLARE
    v_prediction_accuracy FLOAT;
BEGIN
    -- If this game result contradicts a strong belief, trigger revision
    -- Complex logic would go here
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to decay memory strength over time
CREATE OR REPLACE FUNCTION decay_memory_strength()
RETURNS void AS $$
BEGIN
    UPDATE expert_episodic_memories
    SET memory_strength = memory_strength * 0.99
    WHERE last_accessed < NOW() - INTERVAL '7 days'
    AND memory_strength > 0.1;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

CREATE INDEX idx_reasoning_factors_gin ON expert_reasoning_chains USING GIN (reasoning_factors);
CREATE INDEX idx_principles_search ON expert_learned_principles USING GiST (
    to_tsvector('english', principle_statement)
);

-- ============================================================================
-- INITIAL SETUP FOR FUN INTERNAL BETTING POOL
-- ============================================================================

-- Track hypothetical "bets" based on expert confidence for fun
CREATE TABLE IF NOT EXISTS expert_confidence_bets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    expert_id TEXT REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    game_id TEXT NOT NULL,
    bet_type TEXT NOT NULL, -- 'winner', 'spread', 'total'
    bet_prediction JSONB NOT NULL,
    confidence_level FLOAT NOT NULL,
    hypothetical_wager FLOAT, -- Based on confidence (e.g., confidence * 100)
    hypothetical_result FLOAT, -- NULL until game completes
    created_at TIMESTAMP DEFAULT NOW()
);

-- Virtual bankroll tracking for fun
CREATE TABLE IF NOT EXISTS expert_virtual_bankrolls (
    expert_id TEXT PRIMARY KEY REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    current_balance FLOAT DEFAULT 10000.0, -- Start with $10k monopoly money
    total_wagered FLOAT DEFAULT 0,
    total_won FLOAT DEFAULT 0,
    best_bet JSONB, -- Their most successful prediction
    worst_bet JSONB, -- Their biggest failure
    last_updated TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- PERMISSIONS
-- ============================================================================

GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

INSERT INTO schema_migrations (version, description, migrated_at)
VALUES (
    '010_episodic_memory_system',
    'Deep learning system with reasoning chains, belief revision, and episodic memory',
    NOW()
) ON CONFLICT (version) DO NOTHING;