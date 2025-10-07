-- Optimized Schema Surgical Patches
-- Safe, idempotent patches to tighten database design and avoid foot-guns

-- ========================================
-- A) Add vector columns directly to expert_episodic_memories (better cache locality)
-- ========================================

ALTER TABLE expert_episodic_memories
ADD COLUMN IF NOT EXISTS game_context_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS prediction_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS outcome_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS combined_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS embedding_model TEXT,
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS embedding_version INT,
ADD COLUMN IF NOT EXISTS embedding_status TEXT
    CHECK (embedding_status IN ('pending','ready','failed')) DEFAULT 'pending';

-- HNSW indexes for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_mem_combined_hnsw
    ON expert_episodic_memories USING hnsw (combined_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_mem_context_hnsw
    ON expert_episodic_memories USING hnsw (game_context_embedding vector_cosine_ops);

-- ========================================
-- B) Embedding job queue system (trigger → enqueue, worker drains)
-- ========================================

CREATE TABLE IF NOT EXISTS embedding_jobs (
    id BIGSERIAL PRIMARY KEY,
    memory_id TEXT NOT NULL,
    enqueued_at TIMESTAMPTZ DEFAULT NOW(),
    tries INT DEFAULT 0,
    UNIQUE (memory_id)
);

CREATE OR REPLACE FUNCTION queue_embedding_job()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO embedding_jobs (memory_id)
    VALUES (NEW.memory_id)
    ON CONFLICT (memory_id) DO NOTHING;

    UPDATE expert_episodic_memories
    SET embedding_status = 'pending'
    WHERE memory_id = NEW.memory_id;

    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS trg_queue_embedding ON expert_episodic_memories;
CREATE TRIGGER trg_queue_embedding
    AFTER INSERT ON expert_episodic_memories
    FOR EACH ROW EXECUTE FUNCTION queue_embedding_job();

-- ========================================
-- C) Recency-aware search function with alpha blending
-- ========================================

CREATE OR REPLACE FUNCTION search_expert_memories(
    p_expert_id TEXT,
    p_query_embedding VECTOR(1536),
    p_match_threshold FLOAT DEFAULT 0.7,
    p_match_count INT DEFAULT 10,
    p_alpha FLOAT DEFAULT 0.8
)
RETURNS TABLE (
    memory_id TEXT,
    game_id TEXT,
    home_team TEXT,
    away_team TEXT,
    game_date DATE,
    similarity_score FLOAT,
    recency_score FLOAT,
    combined_score FLOAT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.memory_id,
        m.game_id,
        m.home_team,
        m.away_team,
        m.game_date,
        (1 - (m.combined_embedding <=> p_query_embedding)) AS similarity_score,
        EXP(-GREATEST(0, EXTRACT(EPOCH FROM (NOW() - m.game_date))/86400.0)/90.0) AS recency_score,
        (p_alpha * (1 - (m.combined_embedding <=> p_query_embedding)) +
         (1 - p_alpha) * EXP(-GREATEST(0, EXTRACT(EPOCH FROM (NOW() - m.game_date))/86400.0)/90.0)) AS combined_score
    FROM expert_episodic_memories m
    WHERE m.expert_id = p_expert_id
        AND m.combined_embedding IS NOT NULL
        AND (1 - (m.combined_embedding <=> p_query_embedding)) >= p_match_threshold
    ORDER BY combined_score DESC
    LIMIT p_match_count;
END $$;

-- ========================================
-- D) Dual keying strategy for matchup memories
-- ========================================

ALTER TABLE matchup_memories
ADD COLUMN IF NOT EXISTS matchup_key_sorted TEXT GENERATED ALWAYS AS (
    CASE WHEN home_team < away_team
    THEN home_team || '|' || away_team
    ELSE away_team || '|' || home_team END
) STORED;

-- Role-aware constraint (prevents home/away duplicates)
ALTER TABLE matchup_memories
ADD CONSTRAINT IF NOT EXISTS ux_mm_role UNIQUE (expert_id, home_team, away_team);

-- Sorted key index for aggregates
CREATE INDEX IF NOT EXISTS idx_mm_sorted
    ON matchup_memories(expert_id, matchup_key_sorted);

-- ========================================
-- E) Predicted winner constraints on predictions table
-- ========================================

-- Note: Adjust table name based on actual predictions table
-- ALTER TABLE expert_predictions
-- ALTER COLUMN predicted_winner SET NOT NULL;

-- ALTER TABLE expert_predictions
-- ADD CONSTRAINT IF NOT EXISTS fk_predicted_winner
--     FOREIGN KEY (predicted_winner) REFERENCES teams(team_id);

-- ========================================
-- F) Performance indexes for common query patterns
-- ========================================

-- Index for expert + team queries
CREATE INDEX IF NOT EXISTS idx_episodic_expert_teams
    ON expert_episodic_memories(expert_id, home_team, away_team);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_episodic_game_date
    ON expert_episodic_memories(game_date DESC);

-- Index for embedding status queries
CREATE INDEX IF NOT EXISTS idx_episodic_embedding_status
    ON expert_episodic_memories(embedding_status) WHERE embedding_status != 'ready';

-- ========================================
-- G) Validation queries
-- ========================================

-- Check embedding coverage
-- SELECT
--     embedding_status,
--     COUNT(*) as count,
--     ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
-- FROM expert_episodic_memories
-- GROUP BY embedding_status;

-- Check team canonicalization
-- SELECT COUNT(*) as canonical_team_refs
-- FROM expert_episodic_memories
-- WHERE home_team IS NOT NULL AND away_team IS NOT NULL;

COMMENT ON TABLE embedding_jobs IS 'Lightweight job queue for embedding generation';
COMMENT ON FUNCTION search_expert_memories IS 'Recency-aware semantic search with alpha blending';
COMMENT ON COLUMN matchup_memories.matchup_key_sorted IS 'Generated sorted key for aggregate queries';
