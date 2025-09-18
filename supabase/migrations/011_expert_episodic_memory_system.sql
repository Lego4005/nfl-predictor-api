-- Expert Episodic Memory System - Schema Alignment Migration
-- Adds missing tables for belief revision and episodic memory services
-- Compatible with existing 20250116_expert_competition_tables.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- 1. Expert Belief Revisions Table
-- ========================================
CREATE TABLE IF NOT EXISTS expert_belief_revisions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    revision_type VARCHAR(50) NOT NULL, -- prediction_change, confidence_shift, reasoning_update, complete_reversal, nuanced_adjustment
    trigger_type VARCHAR(50) NOT NULL,  -- new_information, injury_report, weather_update, line_movement, public_sentiment, expert_influence, self_reflection, pattern_recognition

    -- Prediction Data
    original_prediction JSONB NOT NULL,
    revised_prediction JSONB NOT NULL,
    causal_chain JSONB NOT NULL,

    -- Analysis Metrics
    confidence_delta DECIMAL(5,4) NOT NULL,
    impact_score DECIMAL(5,4) NOT NULL,

    -- Reasoning and State
    reasoning_before TEXT,
    reasoning_after TEXT,
    emotional_state VARCHAR(50), -- confident_pivot, increasingly_confident, adaptive_recalibration, reluctant_acceptance, cognitive_dissonance, cautious_adjustment, decisive_shift, growing_conviction, emerging_doubt, measured_revision

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key constraint (soft reference to expert_models if it exists)
    CONSTRAINT fk_expert_belief_revisions_expert FOREIGN KEY (expert_id)
        REFERENCES expert_models(expert_id) ON DELETE CASCADE
);

-- Indexes for belief revisions
CREATE INDEX IF NOT EXISTS idx_belief_revisions_expert ON expert_belief_revisions(expert_id);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_game ON expert_belief_revisions(game_id);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_created_at ON expert_belief_revisions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_type ON expert_belief_revisions(revision_type);
CREATE INDEX IF NOT EXISTS idx_belief_revisions_trigger ON expert_belief_revisions(trigger_type);

-- ========================================
-- 2. Expert Episodic Memories Table
-- ========================================
CREATE TABLE IF NOT EXISTS expert_episodic_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id VARCHAR(32) UNIQUE NOT NULL, -- Short hash for memory identification
    expert_id VARCHAR(50) NOT NULL,
    game_id VARCHAR(100) NOT NULL,

    -- Memory Classification
    memory_type VARCHAR(50) NOT NULL, -- prediction_outcome, pattern_recognition, upset_detection, consensus_deviation, learning_moment, failure_analysis
    emotional_state VARCHAR(50) NOT NULL, -- euphoria, satisfaction, neutral, disappointment, devastation, surprise, confusion, vindication

    -- Memory Content
    prediction_data JSONB NOT NULL,
    actual_outcome JSONB NOT NULL,
    contextual_factors JSONB DEFAULT '[]'::jsonb,
    lessons_learned JSONB DEFAULT '[]'::jsonb,

    -- Memory Characteristics
    emotional_intensity DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    memory_vividness DECIMAL(5,4) NOT NULL DEFAULT 0.5,
    memory_decay DECIMAL(5,4) NOT NULL DEFAULT 1.0,
    retrieval_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key constraint (soft reference to expert_models if it exists)
    CONSTRAINT fk_expert_episodic_memories_expert FOREIGN KEY (expert_id)
        REFERENCES expert_models(expert_id) ON DELETE CASCADE
);

-- Indexes for episodic memories
CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert ON expert_episodic_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_game ON expert_episodic_memories(game_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_memory_id ON expert_episodic_memories(memory_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_created_at ON expert_episodic_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_type ON expert_episodic_memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_emotional_state ON expert_episodic_memories(emotional_state);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_vividness ON expert_episodic_memories(memory_vividness DESC);

-- Composite index for memory retrieval with decay
CREATE INDEX IF NOT EXISTS idx_episodic_memories_retrieval ON expert_episodic_memories(expert_id, memory_vividness, memory_decay);

-- ========================================
-- 3. Supporting Tables for Context
-- ========================================

-- Weather Conditions (referenced by episodic memory manager)
CREATE TABLE IF NOT EXISTS weather_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(100) NOT NULL,
    condition VARCHAR(50), -- clear, rain, snow, wind, dome
    temperature INTEGER, -- fahrenheit
    wind_speed INTEGER, -- mph
    precipitation_chance INTEGER, -- percentage
    humidity INTEGER, -- percentage

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(game_id)
);

CREATE INDEX IF NOT EXISTS idx_weather_game ON weather_conditions(game_id);

-- Injury Reports (referenced by episodic memory manager)
CREATE TABLE IF NOT EXISTS injury_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    position VARCHAR(10),
    injury_type VARCHAR(50),
    severity VARCHAR(20), -- questionable, doubtful, out, probable

    reported_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_injury_reports_game ON injury_reports(game_id);
CREATE INDEX IF NOT EXISTS idx_injury_reports_player ON injury_reports(player_name);
CREATE INDEX IF NOT EXISTS idx_injury_reports_severity ON injury_reports(severity);

-- ========================================
-- 4. Functions for Memory Management
-- ========================================

-- Function to update memory decay over time
CREATE OR REPLACE FUNCTION decay_episodic_memories()
RETURNS void AS $$
BEGIN
    -- Gradually decay memories older than 30 days
    UPDATE expert_episodic_memories
    SET
        memory_decay = GREATEST(0.1, memory_decay * 0.99),
        updated_at = NOW()
    WHERE created_at < NOW() - INTERVAL '30 days'
    AND memory_decay > 0.1;

    -- Strengthen frequently accessed memories
    UPDATE expert_episodic_memories
    SET
        memory_vividness = LEAST(1.0, memory_vividness * 1.05),
        memory_decay = LEAST(1.0, memory_decay * 1.02),
        updated_at = NOW()
    WHERE retrieval_count >= 5
    AND memory_vividness < 1.0;
END;
$$ LANGUAGE plpgsql;

-- Function to calculate belief revision impact
CREATE OR REPLACE FUNCTION calculate_revision_impact(
    original_pred JSONB,
    revised_pred JSONB,
    revision_type VARCHAR
)
RETURNS DECIMAL AS $$
DECLARE
    impact DECIMAL := 0.0;
    conf_delta DECIMAL;
BEGIN
    -- Base impact by type
    CASE revision_type
        WHEN 'complete_reversal' THEN impact := 1.0;
        WHEN 'prediction_change' THEN impact := 0.7;
        WHEN 'confidence_shift' THEN impact := 0.5;
        WHEN 'reasoning_update' THEN impact := 0.3;
        WHEN 'nuanced_adjustment' THEN impact := 0.2;
        ELSE impact := 0.1;
    END CASE;

    -- Confidence change modifier
    conf_delta := ABS((revised_pred->>'confidence')::DECIMAL - (original_pred->>'confidence')::DECIMAL);
    impact := impact + (conf_delta * 0.5);

    RETURN LEAST(1.0, impact);
END;
$$ LANGUAGE plpgsql;

-- ========================================
-- 5. Views for Service Integration
-- ========================================

-- Expert Memory Summary View
CREATE OR REPLACE VIEW expert_memory_summary AS
SELECT
    e.expert_id,
    e.name,
    COUNT(em.id) as total_memories,
    AVG(em.emotional_intensity) as avg_emotional_intensity,
    AVG(em.memory_vividness) as avg_memory_vividness,
    SUM(em.retrieval_count) as total_retrievals,
    COUNT(br.id) as total_revisions,
    AVG(br.impact_score) as avg_revision_impact
FROM expert_models e
LEFT JOIN expert_episodic_memories em ON e.expert_id = em.expert_id
LEFT JOIN expert_belief_revisions br ON e.expert_id = br.expert_id
GROUP BY e.expert_id, e.name;

-- Recent Memory Activity View
CREATE OR REPLACE VIEW recent_memory_activity AS
SELECT
    expert_id,
    'memory' as activity_type,
    memory_type as activity_subtype,
    emotional_state as activity_detail,
    created_at
FROM expert_episodic_memories
WHERE created_at > NOW() - INTERVAL '7 days'

UNION ALL

SELECT
    expert_id,
    'revision' as activity_type,
    revision_type as activity_subtype,
    emotional_state as activity_detail,
    created_at
FROM expert_belief_revisions
WHERE created_at > NOW() - INTERVAL '7 days'

ORDER BY created_at DESC;

-- ========================================
-- 6. Triggers for Automatic Updates
-- ========================================

-- Update timestamps on belief revisions
CREATE OR REPLACE FUNCTION update_belief_revision_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_belief_revision_timestamp
    BEFORE UPDATE ON expert_belief_revisions
    FOR EACH ROW
    EXECUTE FUNCTION update_belief_revision_timestamp();

-- Update timestamps on episodic memories
CREATE OR REPLACE FUNCTION update_episodic_memory_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_episodic_memory_timestamp
    BEFORE UPDATE ON expert_episodic_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_episodic_memory_timestamp();

-- ========================================
-- 7. RLS Policies (if RLS is enabled)
-- ========================================

-- Enable RLS on the new tables (optional, depends on security requirements)
-- ALTER TABLE expert_belief_revisions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE expert_episodic_memories ENABLE ROW LEVEL SECURITY;

-- Create policies (if needed)
-- CREATE POLICY expert_belief_revisions_policy ON expert_belief_revisions
--     FOR ALL USING (true); -- Adjust based on security requirements

-- CREATE POLICY expert_episodic_memories_policy ON expert_episodic_memories
--     FOR ALL USING (true); -- Adjust based on security requirements

-- ========================================
-- 8. Initial Data Validation
-- ========================================

-- Verify expert_models table exists (should be created by 20250116_expert_competition_tables.sql)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'expert_models') THEN
        RAISE NOTICE 'Warning: expert_models table not found. Foreign key constraints will fail.';
        RAISE NOTICE 'Please ensure 20250116_expert_competition_tables.sql has been applied first.';
    ELSE
        RAISE NOTICE 'expert_models table found. Schema alignment complete.';
    END IF;
END;
$$;

-- ========================================
-- Migration Complete
-- ========================================

-- Log migration completion
INSERT INTO public.migrations_log (migration_name, applied_at, description)
VALUES (
    '011_expert_episodic_memory_system',
    NOW(),
    'Added expert_belief_revisions and expert_episodic_memories tables with supporting infrastructure for episodic memory services'
) ON CONFLICT (migration_name) DO NOTHING;

-- Create migrations_log table if it doesn't exist
CREATE TABLE IF NOT EXISTS migrations_log (
    id SERIAL PRIMARY KEY,
    migration_name VARCHAR(255) UNIQUE NOT NULL,
    applied_at TIMESTAMP DEFAULT NOW(),
    description TEXT
);