-- Migration 022: Adaptive Learning Engine Tables
-- Creates tables for ML-based expert improvement

-- Table for storing learned weights (gradient descent results)
CREATE TABLE IF NOT EXISTS expert_learned_weights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    weights JSONB NOT NULL DEFAULT '{}'::jsonb,  -- {factor_name: weight_value}
    learning_rate FLOAT NOT NULL DEFAULT 0.01,
    accuracy_history FLOAT[] DEFAULT ARRAY[]::FLOAT[],  -- Last 100 game accuracies
    games_learned_from INT GENERATED ALWAYS AS (array_length(accuracy_history, 1)) STORED,
    recent_accuracy FLOAT GENERATED ALWAYS AS (
        CASE
            WHEN array_length(accuracy_history, 1) >= 20 THEN
                (SELECT AVG(val) FROM unnest(accuracy_history[array_length(accuracy_history, 1)-19:]) val)
            WHEN array_length(accuracy_history, 1) > 0 THEN
                (SELECT AVG(val) FROM unnest(accuracy_history) val)
            ELSE 0.0
        END
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(expert_id)
);

-- Table for episodic memories (Supabase-compatible version)
CREATE TABLE IF NOT EXISTS expert_episodic_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL REFERENCES personality_experts(expert_id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES games(id) ON DELETE CASCADE,
    predicted_winner TEXT NOT NULL,
    actual_winner TEXT NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    was_correct BOOLEAN NOT NULL,
    surprise_level FLOAT NOT NULL CHECK (surprise_level BETWEEN 0 AND 1),
    emotional_impact TEXT NOT NULL CHECK (emotional_impact IN ('triumph', 'disappointment', 'neutral', 'vindication')),
    key_factors TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    lesson_learned TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(expert_id, game_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_learned_weights_expert ON expert_learned_weights(expert_id);
CREATE INDEX IF NOT EXISTS idx_learned_weights_updated ON expert_learned_weights(updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_expert ON expert_episodic_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_game ON expert_episodic_memories(game_id);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_created ON expert_episodic_memories(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_surprise ON expert_episodic_memories(surprise_level DESC);
CREATE INDEX IF NOT EXISTS idx_episodic_memories_factors ON expert_episodic_memories USING GIN(key_factors);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_learned_weights_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_learned_weights_timestamp
    BEFORE UPDATE ON expert_learned_weights
    FOR EACH ROW
    EXECUTE FUNCTION update_learned_weights_timestamp();

-- Grant permissions (adjust as needed for your setup)
GRANT ALL ON expert_learned_weights TO authenticated;
GRANT ALL ON expert_episodic_memories TO authenticated;
GRANT ALL ON expert_learned_weights TO anon;
GRANT ALL ON expert_episodic_memories TO anon;

COMMENT ON TABLE expert_learned_weights IS 'ML-based learned weights for expert decision factors, updated via gradient descent';
COMMENT ON TABLE expert_episodic_memories IS 'Memorable game experiences stored for pattern recognition and learning';
COMMENT ON COLUMN expert_learned_weights.weights IS 'JSONB map of factor names to learned weight values (0-1)';
COMMENT ON COLUMN expert_learned_weights.accuracy_history IS 'Array of last 100 game accuracies (1.0 = correct, 0.0 = incorrect)';
COMMENT ON COLUMN expert_episodic_memories.surprise_level IS 'How unexpected the outcome was (0 = expected, 1 = shocking)';
COMMENT ON COLUMN expert_episodic_memories.emotional_impact IS 'Emotional response to outcome: triumph, disappointment, neutral, or vindication';