-- Enable pgvector if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Team Knowledge Table
CREATE TABLE team_knowledge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id VARCHAR(50) NOT NULL,
    team_id VARCHAR(10) NOT NULL,

    -- Aggregated insights from multiple games
    overall_assessment TEXT,
    strengths TEXT[],
    weaknesses TEXT[],
    key_patterns JSONB,

    -- Performance tracking
    games_analyzed INTEGER DEFAULT 0,
    predictions_made INTEGER DEFAULT 0,
    predictions_correct INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4),

    -- Context-specific patterns
    home_performance JSONB,
    away_performance JSONB,
    weather_impact JSONB,

    -- Vector embedding for semantic search
    knowledge_embedding VECTOR(1536),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(expert_id, team_id)
);

CREATE INDEX idx_team_knowledge_expert ON team_knowledge(expert_id);
CREATE INDEX idx_team_knowledge_team ON team_knowledge(team_id);
CREATE INDEX idx_team_knowledge_embedding ON team_knowledge USING ivfflat (knowledge_embedding vector_cosine_ops) WITH (lists = 100);

-- Matchup Memories Table
CREATE TABLE matchup_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id VARCHAR(50) NOT NULL,
    team_a VARCHAR(10) NOT NULL,
    team_b VARCHAR(10) NOT NULL,
    matchup_key VARCHAR(25) NOT NULL, -- Alphabetically sorted: 'BUF_KC'

    -- Historical patterns
    games_analyzed INTEGER DEFAULT 0,
    predictions_made INTEGER DEFAULT 0,
    predictions_correct INTEGER DEFAULT 0,
    accuracy DECIMAL(5,4),

    -- Observed patterns
    typical_margin DECIMAL(5,2),
    scoring_pattern TEXT,
    key_factors TEXT[],

    -- Vector embedding
    matchup_embedding VECTOR(1536),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(expert_id, matchup_key)
);

CREATE INDEX idx_matchup_expert ON matchup_memories(expert_id);
CREATE INDEX idx_matchup_key ON matchup_memories(matchup_key);
CREATE INDEX idx_matchup_embedding ON matchup_memories USING ivfflat (matchup_embedding vector_cosine_ops) WITH (lists = 100);

-- Memory Embeddings Table (add vectors to existing memories)
CREATE TABLE expert_memory_embeddings (
    memory_id VARCHAR(32) PRIMARY KEY,
    expert_id VARCHAR(50) NOT NULL,

    -- Vector for semantic search
    memory_embedding VECTOR(1536),

    -- Quick reference data
    teams_involved VARCHAR(10)[],
    memory_summary TEXT,
    memory_type VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (memory_id) REFERENCES expert_episodic_memories(memory_id)
);

CREATE INDEX idx_memory_embedding_expert ON expert_memory_embeddings(expert_id);
CREATE INDEX idx_memory_embedding_teams ON expert_memory_embeddings USING GIN(teams_involved);
CREATE INDEX idx_memory_embedding_vector ON expert_memory_embeddings USING ivfflat (memory_embedding vector_cosine_ops) WITH (lists = 100);

-- Vector similarity search function
CREATE OR REPLACE FUNCTION search_expert_memories(
    p_expert_id VARCHAR(50),
    p_query_embedding VECTOR(1536),
    p_match_threshold FLOAT DEFAULT 0.7,
    p_match_count INT DEFAULT 5
)
RETURNS TABLE (
    memory_id VARCHAR(32),
    similarity FLOAT,
    memory_summary TEXT,
    teams_involved VARCHAR(10)[]
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        e.memory_id,
        1 - (e.memory_embedding <=> p_query_embedding) AS similarity,
        e.memory_summary,
        e.teams_involved
    FROM expert_memory_embeddings e
    WHERE e.expert_id = p_expert_id
    AND 1 - (e.memory_embedding <=> p_query_embedding) > p_match_threshold
    ORDER BY e.memory_embedding <=> p_query_embedding
    LIMIT p_match_count;
END;
$$;

-- Function to get team knowledge with similarity search
CREATE OR REPLACE FUNCTION search_team_knowledge(
    p_expert_id VARCHAR(50),
    p_team_id VARCHAR(10),
    p_query_embedding VECTOR(1536),
    p_match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    overall_assessment TEXT,
    strengths TEXT[],
    weaknesses TEXT[],
    accuracy DECIMAL(5,4),
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tk.id,
        tk.overall_assessment,
        tk.strengths,
        tk.weaknesses,
        tk.accuracy,
        1 - (tk.knowledge_embedding <=> p_query_embedding) AS similarity
    FROM team_knowledge tk
    WHERE tk.expert_id = p_expert_id
    AND tk.team_id = p_team_id
    AND tk.knowledge_embedding IS NOT NULL
    AND 1 - (tk.knowledge_embedding <=> p_query_embedding) > p_match_threshold
    ORDER BY tk.knowledge_embedding <=> p_query_embedding
    LIMIT 1;
END;
$$;

-- Function to get matchup memories with similarity search
CREATE OR REPLACE FUNCTION search_matchup_memories(
    p_expert_id VARCHAR(50),
    p_matchup_key VARCHAR(25),
    p_query_embedding VECTOR(1536),
    p_match_threshold FLOAT DEFAULT 0.7
)
RETURNS TABLE (
    id UUID,
    typical_margin DECIMAL(5,2),
    scoring_pattern TEXT,
    key_factors TEXT[],
    accuracy DECIMAL(5,4),
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        mm.id,
        mm.typical_margin,
        mm.scoring_pattern,
        mm.key_factors,
        mm.accuracy,
        1 - (mm.matchup_embedding <=> p_query_embedding) AS similarity
    FROM matchup_memories mm
    WHERE mm.expert_id = p_expert_id
    AND mm.matchup_key = p_matchup_key
    AND mm.matchup_embedding IS NOT NULL
    AND 1 - (mm.matchup_embedding <=> p_query_embedding) > p_match_threshold
    ORDER BY mm.matchup_embedding <=> p_query_embedding
    LIMIT 1;
END;
$$;
