-- Vector Memory Embeddings Migration
-- Adds vector embedding support to existing memory tables for semantic similarity search
-- Requires pgvector extension (already enabled in 011_expert_episodic_memory_s.sql)

-- ========================================
-- 1. Add Vector Embedding Columns
-- ========================================

-- Add embedding columns to expert_episodic_memories table
ALTER TABLE expert_episodic_memories
ADD COLUMN IF NOT EXISTS game_context_embedding vector(1536),
ADD COLUMN IF NOT EXISTS prediction_embedding vector(1536),
ADD COLUMN IF NOT EXISTS outcome_embedding vector(1536),
ADD COLUMN IF NOT EXISTS combined_embedding vector(1536);

-- Add metadata for embedding generation
ALTER TABLE expert_episodic_memories
ADD COLUMN IF NOT EXISTS embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS embedding_version INTEGER DEFAULT 1;

-- ========================================
-- 2. Memory Embeddings Metadata Table
-- ========================================

CREATE TABLE IF NOT EXISTS memory_embeddings_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id VARCHAR(32) NOT NULL,
    embedding_type VARCHAR(50) NOT NULL, -- game_context, prediction, outcome, combined

    -- Embedding characteristics
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    embedding_dimensions INTEGER NOT NULL,

    -- Generation metadata
    source_text_length INTEGER,
    generation_time_ms INTEGER,
    generation_cost_tokens INTEGER,

    -- Quality metrics
    confidence_score DECIMAL(5,4),
    semantic_density DECIMAL(5,4),

    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (memory_id) REFERENCES expert_episodic_memories(memory_id) ON DELETE CASCADE
);

-- Indexes for embeddings metadata
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_memory ON memory_embeddings_metadata(memory_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_type ON memory_embeddings_metadata(embedding_type);
CREATE INDEX IF NOT EXISTS idx_embeddings_metadata_model ON memory_embeddings_metadata(model_name);

-- ========================================
-- 3. Vector Similarity Search Indexes
-- ========================================

-- HNSW indexes for fast vector similarity search
CREATE INDEX IF NOT EXISTS idx_episodic_memories_game_context_embedding
ON expert_episodic_memories USING hnsw (game_context_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_prediction_embedding
ON expert_episodic_memories USING hnsw (prediction_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_outcome_embedding
ON expert_episodic_memories USING hnsw (outcome_embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_episodic_memories_combined_embedding
ON expert_episodic_memories USING hnsw (combined_embedding vector_cosine_ops);

-- ========================================
-- 4. Memory Similarity Search Functions
-- ========================================

-- Function to find similar memories by game context
CREATE OR REPLACE FUNCTION find_similar_game_contexts(
    target_embedding vector(1536),
    expert_id_filter VARCHAR(50) DEFAULT NULL,
    similarity_threshold DECIMAL DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    memory_id VARCHAR(32),
    expert_id VARCHAR(50),
    game_id VARCHAR(100),
    memory_type VARCHAR(50),
    similarity_score DECIMAL,
    memory_vividness DECIMAL,
    memory_decay DECIMAL,
    created_at TIMESTAMP
) AS $
BEGIN
    RETURN QUERY
    SELECT
        em.memory_id,
        em.expert_id,
        em.game_id,
        em.memory_type,
        (1 - (em.game_context_embedding <=> target_embedding))::DECIMAL as similarity_score,
        em.memory_vividness,
        em.memory_decay,
        em.created_at
    FROM expert_episodic_memories em
    WHERE em.game_context_embedding IS NOT NULL
    AND (expert_id_filter IS NULL OR em.expert_id = expert_id_filter)
    AND (1 - (em.game_context_embedding <=> target_embedding)) >= similarity_threshold
    ORDER BY em.game_context_embedding <=> target_embedding
    LIMIT max_results;
END;
$ LANGUAGE plpgsql;

-- Function to find similar predictions
CREATE OR REPLACE FUNCTION find_similar_predictions(
    target_embedding vector(1536),
    expert_id_filter VARCHAR(50) DEFAULT NULL,
    similarity_threshold DECIMAL DEFAULT 0.7,
    max_results INTEGER DEFAULT 10
)
RETURNS TABLE (
    memory_id VARCHAR(32),
    expert_id VARCHAR(50),
    game_id VARCHAR(100),
    prediction_data JSONB,
    similarity_score DECIMAL,
    emotional_intensity DECIMAL,
    created_at TIMESTAMP
) AS $
BEGIN
    RETURN QUERY
    SELECT
        em.memory_id,
        em.expert_id,
        em.game_id,
        em.prediction_data,
        (1 - (em.prediction_embedding <=> target_embedding))::DECIMAL as similarity_score,
        em.emotional_intensity,
        em.created_at
    FROM expert_episodic_memories em
    WHERE em.prediction_embedding IS NOT NULL
    AND (expert_id_filter IS NULL OR em.expert_id = expert_id_filter)
    AND (1 - (em.prediction_embedding <=> target_embedding)) >= similarity_threshold
    ORDER BY em.prediction_embedding <=> target_embedding
    LIMIT max_results;
END;
$ LANGUAGE plpgsql;

-- Function for comprehensive memory search with relevance scoring
CREATE OR REPLACE FUNCTION search_relevant_memories(
    target_embedding vector(1536),
    expert_id_filter VARCHAR(50),
    embedding_type VARCHAR(50) DEFAULT 'combined',
    recency_weight DECIMAL DEFAULT 0.3,
    vividness_weight DECIMAL DEFAULT 0.4,
    similarity_weight DECIMAL DEFAULT 0.3,
    max_results INTEGER DEFAULT 20
)
RETURNS TABLE (
    memory_id VARCHAR(32),
    expert_id VARCHAR(50),
    game_id VARCHAR(100),
    memory_type VARCHAR(50),
    similarity_score DECIMAL,
    relevance_score DECIMAL,
    memory_vividness DECIMAL,
    memory_decay DECIMAL,
    retrieval_count INTEGER,
    created_at TIMESTAMP
) AS $
DECLARE
    embedding_column TEXT;
BEGIN
    -- Determine which embedding column to use
    CASE embedding_type
        WHEN 'game_context' THEN embedding_column := 'game_context_embedding';
        WHEN 'prediction' THEN embedding_column := 'prediction_embedding';
        WHEN 'outcome' THEN embedding_column := 'outcome_embedding';
        ELSE embedding_column := 'combined_embedding';
    END CASE;

    -- Dynamic query with relevance scoring
    RETURN QUERY EXECUTE format('
        SELECT
            em.memory_id,
            em.expert_id,
            em.game_id,
            em.memory_type,
            (1 - (em.%I <=> $1))::DECIMAL as similarity_score,
            (
                ($4 * (1 - (em.%I <=> $1))) +
                ($5 * em.memory_vividness) +
                ($6 * (1.0 - EXTRACT(EPOCH FROM (NOW() - em.created_at)) / (86400 * 365)))
            )::DECIMAL as relevance_score,
            em.memory_vividness,
            em.memory_decay,
            em.retrieval_count,
            em.created_at
        FROM expert_episodic_memories em
        WHERE em.%I IS NOT NULL
        AND em.expert_id = $2
        AND em.memory_decay > 0.1
        ORDER BY relevance_score DESC
        LIMIT $3',
        embedding_column, embedding_column, embedding_column
    ) USING target_embedding, expert_id_filter, max_results, similarity_weight, vividness_weight, recency_weight;
END;
$ LANGUAGE plpgsql;

-- ========================================
-- 5. Memory Retrieval Tracking
-- ========================================

-- Function to track memory retrieval and update statistics
CREATE OR REPLACE FUNCTION track_memory_retrieval(
    memory_id_param VARCHAR(32),
    retrieval_context VARCHAR(100) DEFAULT 'prediction_generation'
)
RETURNS void AS $
BEGIN
    -- Update retrieval count and strengthen memory
    UPDATE expert_episodic_memories
    SET
        retrieval_count = retrieval_count + 1,
        memory_vividness = LEAST(1.0, memory_vividness * 1.02),
        updated_at = NOW()
    WHERE memory_id = memory_id_param;

    -- Log retrieval for analytics
    INSERT INTO memory_retrieval_log (memory_id, retrieval_context, retrieved_at)
    VALUES (memory_id_param, retrieval_context, NOW());
END;
$ LANGUAGE plpgsql;

-- Memory retrieval log table
CREATE TABLE IF NOT EXISTS memory_retrieval_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_id VARCHAR(32) NOT NULL,
    retrieval_context VARCHAR(100),
    retrieved_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (memory_id) REFERENCES expert_episodic_memories(memory_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_memory_retrieval_log_memory ON memory_retrieval_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_retrieval_log_retrieved_at ON memory_retrieval_log(retrieved_at DESC);

-- ========================================
-- 6. Embedding Quality Analysis Views
-- ========================================

-- View for embedding coverage analysis
CREATE OR REPLACE VIEW embedding_coverage_analysis AS
SELECT
    expert_id,
    COUNT(*) as total_memories,
    COUNT(game_context_embedding) as game_context_embeddings,
    COUNT(prediction_embedding) as prediction_embeddings,
    COUNT(outcome_embedding) as outcome_embeddings,
    COUNT(combined_embedding) as combined_embeddings,
    ROUND(
        (COUNT(combined_embedding)::DECIMAL / COUNT(*)) * 100, 2
    ) as embedding_coverage_percent
FROM expert_episodic_memories
GROUP BY expert_id;

-- View for memory retrieval analytics
CREATE OR REPLACE VIEW memory_retrieval_analytics AS
SELECT
    em.expert_id,
    em.memory_type,
    COUNT(mrl.id) as total_retrievals,
    COUNT(DISTINCT em.memory_id) as unique_memories_retrieved,
    AVG(em.memory_vividness) as avg_vividness,
    AVG(em.retrieval_count) as avg_retrieval_count,
    MAX(mrl.retrieved_at) as last_retrieval
FROM expert_episodic_memories em
LEFT JOIN memory_retrieval_log mrl ON em.memory_id = mrl.memory_id
GROUP BY em.expert_id, em.memory_type;

-- ========================================
-- 7. Maintenance Functions
-- ========================================

-- Function to rebuild vector indexes (for maintenance)
CREATE OR REPLACE FUNCTION rebuild_vector_indexes()
RETURNS void AS $
BEGIN
    -- Reindex all vector indexes
    REINDEX INDEX idx_episodic_memories_game_context_embedding;
    REINDEX INDEX idx_episodic_memories_prediction_embedding;
    REINDEX INDEX idx_episodic_memories_outcome_embedding;
    REINDEX INDEX idx_episodic_memories_combined_embedding;

    RAISE NOTICE 'Vector indexes rebuilt successfully';
END;
$ LANGUAGE plpgsql;

-- Function to clean up old embeddings
CREATE OR REPLACE FUNCTION cleanup_old_embeddings(
    days_old INTEGER DEFAULT 365
)
RETURNS INTEGER AS $
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Delete embeddings for memories older than specified days with low decay
    UPDATE expert_episodic_memories
    SET
        game_context_embedding = NULL,
        prediction_embedding = NULL,
        outcome_embedding = NULL,
        combined_embedding = NULL,
        embedding_generated_at = NULL
    WHERE created_at < NOW() - (days_old || ' days')::INTERVAL
    AND memory_decay < 0.2
    AND retrieval_count < 2;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$ LANGUAGE plpgsql;

-- ========================================
-- Migration Complete
-- ========================================

-- Log migration completion
INSERT INTO migrations_log (migration_name, applied_at, description)
VALUES (
    '024_vector_memory_embeddings',
    NOW(),
    'Added vector embedding support to expert_episodic_memories with similarity search functions and analytics'
) ON CONFLICT (migration_name) DO NOTHING;

-- Verify vector extension is available
DO $
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        RAISE EXCEPTION 'pgvector extension is not installed. Please install it first.';
    ELSE
        RAISE NOTICE 'Vector embeddings migration completed successfully';
    END IF;
END;
$;
