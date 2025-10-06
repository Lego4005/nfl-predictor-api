-- Optimized Expert Memory Schema
-- Based on tecl analysis and performance requirements
-- Migration: 040_optimized_expert_memory_schema.sql

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================
-- 1. CANONICAL TEAMS + ALIASES (Critical Foundation)
-- ========================================
CREATE TABLE IF NOT EXISTS teams (
    team_id TEXT PRIMARY KEY,           -- e.g., 'KC'
    canonical_key TEXT NOT NULL UNIQUE, -- 'kansas_city_chiefs'
    display_name TEXT NOT NULL,         -- 'Kansas City Chiefs'
    division TEXT,                      -- 'AFC West'
    conference TEXT,                    -- 'AFC'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS team_aliases (
    alias TEXT PRIMARY KEY,            -- 'Chiefs', 'Kansas City', 'KC'
    team_id TEXT NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    alias_type TEXT DEFAULT 'common'   -- 'common', 'abbreviation', 'city'
);

CREATE INDEX IF NOT EXISTS idx_team_aliases_team ON team_aliases(team_id);

-- Insert NFL teams (canonical data)
INSERT INTO teams (team_id, canonical_key, display_name, division, conference) VALUES
('ARI', 'arizona_cardinals', 'Arizona Cardinals', 'NFC West', 'NFC'),
('ATL', 'atlanta_falcons', 'Atlanta Falcons', 'NFC South', 'NFC'),
('BAL', 'baltimore_ravens', 'Baltimore Ravens', 'AFC North', 'AFC'),
('BUF', 'buffalo_bills', 'Buffalo Bills', 'AFC East', 'AFC'),
('CAR', 'carolina_panthers', 'Carolina Panthers', 'NFC South', 'NFC'),
('CHI', 'chicago_bears', 'Chicago Bears', 'NFC North', 'NFC'),
('CIN', 'cincinnati_bengals', 'Cincinnati Bengals', 'AFC North', 'AFC'),
('CLE', 'cleveland_browns', 'Cleveland Browns', 'AFC North', 'AFC'),
('DAL', 'dallas_cowboys', 'Dallas Cowboys', 'NFC East', 'NFC'),
('DEN', 'denver_broncos', 'Denver Broncos', 'AFC West', 'AFC'),
('DET', 'detroit_lions', 'Detroit Lions', 'NFC North', 'NFC'),
('GB', 'green_bay_packers', 'Green Bay Packers', 'NFC North', 'NFC'),
('HOU', 'houston_texans', 'Houston Texans', 'AFC South', 'AFC'),
('IND', 'indianapolis_colts', 'Indianapolis Colts', 'AFC South', 'AFC'),
('JAX', 'jacksonville_jaguars', 'Jacksonville Jaguars', 'AFC South', 'AFC'),
('KC', 'kansas_city_chiefs', 'Kansas City Chiefs', 'AFC West', 'AFC'),
('LV', 'las_vegas_raiders', 'Las Vegas Raiders', 'AFC West', 'AFC'),
('LAC', 'los_angeles_chargers', 'Los Angeles Chargers', 'AFC West', 'AFC'),
('LAR', 'los_angeles_rams', 'Los Angeles Rams', 'NFC West', 'NFC'),
('MIA', 'miami_dolphins', 'Miami Dolphins', 'AFC East', 'AFC'),
('MIN', 'minnesota_vikings', 'Minnesota Vikings', 'NFC North', 'NFC'),
('NE', 'new_england_patriots', 'New England Patriots', 'AFC East', 'AFC'),
('NO', 'new_orleans_saints', 'New Orleans Saints', 'NFC South', 'NFC'),
('NYG', 'new_york_giants', 'New York Giants', 'NFC East', 'NFC'),
('NYJ', 'new_york_jets', 'New York Jets', 'AFC East', 'AFC'),
('PHI', 'philadelphia_eagles', 'Philadelphia Eagles', 'NFC East', 'NFC'),
('PIT', 'pittsburgh_steelers', 'Pittsburgh Steelers', 'AFC North', 'AFC'),
('SF', 'san_francisco_49ers', 'San Francisco 49ers', 'NFC West', 'NFC'),
('SEA', 'seattle_seahawks', 'Seattle Seahawks', 'NFC West', 'NFC'),
('TB', 'tampa_bay_buccaneers', 'Tampa Bay Buccaneers', 'NFC South', 'NFC'),
('TEN', 'tennessee_titans', 'Tennessee Titans', 'AFC South', 'AFC'),
('WAS', 'washington_commanders', 'Washington Commanders', 'NFC East', 'NFC')
ON CONFLICT (team_id) DO NOTHING;

-- Insert common aliases
INSERT INTO team_aliases (alias, team_id) VALUES
-- Kansas City Chiefs
('Chiefs', 'KC'), ('Kansas City', 'KC'), ('KC', 'KC'),
-- Buffalo Bills
('Bills', 'BUF'), ('Buffalo', 'BUF'), ('BUF', 'BUF'),
-- Baltimore Ravens
('Ravens', 'BAL'), ('Baltimore', 'BAL'), ('BAL', 'BAL'),
-- Add more as needed...
('Cardinals', 'ARI'), ('Arizona', 'ARI'), ('ARI', 'ARI'),
('Falcons', 'ATL'), ('Atlanta', 'ATL'), ('ATL', 'ATL'),
('Panthers', 'CAR'), ('Carolina', 'CAR'), ('CAR', 'CAR'),
('Bears', 'CHI'), ('Chicago', 'CHI'), ('CHI', 'CHI'),
('Bengals', 'CIN'), ('Cincinnati', 'CIN'), ('CIN', 'CIN'),
('Browns', 'CLE'), ('Cleveland', 'CLE'), ('CLE', 'CLE'),
('Cowboys', 'DAL'), ('Dallas', 'DAL'), ('DAL', 'DAL'),
('Broncos', 'DEN'), ('Denver', 'DEN'), ('DEN', 'DEN'),
('Lions', 'DET'), ('Detroit', 'DET'), ('DET', 'DET'),
('Packers', 'GB'), ('Green Bay', 'GB'), ('GB', 'GB'),
('Texans', 'HOU'), ('Houston', 'HOU'), ('HOU', 'HOU'),
('Colts', 'IND'), ('Indianapolis', 'IND'), ('IND', 'IND'),
('Jaguars', 'JAX'), ('Jacksonville', 'JAX'), ('JAX', 'JAX'),
('Raiders', 'LV'), ('Las Vegas', 'LV'), ('LV', 'LV'),
('Chargers', 'LAC'), ('Los Angeles Chargers', 'LAC'), ('LAC', 'LAC'),
('Rams', 'LAR'), ('Los Angeles Rams', 'LAR'), ('LAR', 'LAR'),
('Dolphins', 'MIA'), ('Miami', 'MIA'), ('MIA', 'MIA'),
('Vikings', 'MIN'), ('Minnesota', 'MIN'), ('MIN', 'MIN'),
('Patriots', 'NE'), ('New England', 'NE'), ('NE', 'NE'),
('Saints', 'NO'), ('New Orleans', 'NO'), ('NO', 'NO'),
('Giants', 'NYG'), ('New York Giants', 'NYG'), ('NYG', 'NYG'),
('Jets', 'NYJ'), ('New York Jets', 'NYJ'), ('NYJ', 'NYJ'),
('Eagles', 'PHI'), ('Philadelphia', 'PHI'), ('PHI', 'PHI'),
('Steelers', 'PIT'), ('Pittsburgh', 'PIT'), ('PIT', 'PIT'),
('49ers', 'SF'), ('San Francisco', 'SF'), ('SF', 'SF'),
('Seahawks', 'SEA'), ('Seattle', 'SEA'), ('SEA', 'SEA'),
('Buccaneers', 'TB'), ('Tampa Bay', 'TB'), ('TB', 'TB'),
('Titans', 'TEN'), ('Tennessee', 'TEN'), ('TEN', 'TEN'),
('Commanders', 'WAS'), ('Washington', 'WAS'), ('WAS', 'WAS')
ON CONFLICT (alias) DO NOTHING;

-- ========================================
-- 2. ENHANCED EPISODIC MEMORIES (Embeddings on Main Table)
-- ========================================
ALTER TABLE IF EXISTS expert_episodic_memories
ADD COLUMN IF NOT EXISTS home_team TEXT,
ADD COLUMN IF NOT EXISTS away_team TEXT,
ADD COLUMN IF NOT EXISTS season INTEGER,
ADD COLUMN IF NOT EXISTS week INTEGER,
ADD COLUMN IF NOT EXISTS game_date DATE,
ADD COLUMN IF NOT EXISTS game_context_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS prediction_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS outcome_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS combined_embedding VECTOR(1536),
ADD COLUMN IF NOT EXISTS embedding_model TEXT DEFAULT 'text-embedding-3-small',
ADD COLUMN IF NOT EXISTS embedding_generated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS embedding_version INTEGER DEFAULT 1;

-- Add foreign key constraints to teams
ALTER TABLE expert_episodic_memories
ADD CONSTRAINT IF NOT EXISTS fk_mem_home_team
    FOREIGN KEY (home_team) REFERENCES teams(team_id) ON DELETE CASCADE,
ADD CONSTRAINT IF NOT EXISTS fk_mem_away_team
    FOREIGN KEY (away_team) REFERENCES teams(team_id) ON DELETE CASCADE;

-- Optimized indexes for memory retrieval
CREATE INDEX IF NOT EXISTS idx_mem_expert ON expert_episodic_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_mem_teams ON expert_episodic_memories(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_mem_time ON expert_episodic_memories(season, week);
CREATE INDEX IF NOT EXISTS idx_mem_date ON expert_episodic_memories(game_date DESC);

-- HNSW vector indexes (preferred over IVFFLAT)
CREATE INDEX IF NOT EXISTS idx_mem_combined_hnsw
    ON expert_episodic_memories USING hnsw (combined_embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_mem_context_hnsw
    ON expert_episodic_memories USING hnsw (game_context_embedding vector_cosine_ops);

-- ========================================
-- 3. TEAM KNOWLEDGE TABLE (Single Team Insights)
-- ========================================
CREATE TABLE IF NOT EXISTS team_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    team_id TEXT NOT NULL,
    knowledge_type VARCHAR(50) NOT NULL, -- 'performance_pattern', 'weather_impact', 'home_advantage'

    -- Team-specific insights
    recent_performance JSONB DEFAULT '{}',
    team_trends JSONB DEFAULT '{}',
    situational_factors JSONB DEFAULT '{}',

    -- Learning metrics
    confidence_level DECIMAL(5,4) DEFAULT 0.5,
    sample_size INTEGER DEFAULT 0,
    accuracy_rate DECIMAL(5,4) DEFAULT 0.5,
    last_updated TIMESTAMP DEFAULT NOW(),

    -- Vector embedding for similarity search
    knowledge_embedding VECTOR(1536),

    -- Constraints
    CONSTRAINT fk_tk_expert FOREIGN KEY (expert_id) REFERENCES enhanced_expert_models(expert_id) ON DELETE CASCADE,
    CONSTRAINT fk_tk_team FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE,
    CONSTRAINT ux_tk UNIQUE (expert_id, team_id, knowledge_type)
);

-- Indexes for team knowledge
CREATE INDEX IF NOT EXISTS idx_tk_expert ON team_knowledge(expert_id);
CREATE INDEX IF NOT EXISTS idx_tk_team ON team_knowledge(team_id);
CREATE INDEX IF NOT EXISTS idx_tk_confidence ON team_knowledge(confidence_level DESC);
CREATE INDEX IF NOT EXISTS idx_tk_hnsw
    ON team_knowledge USING hnsw (knowledge_embedding vector_cosine_ops);

-- ========================================
-- 4. MATCHUP MEMORIES (Team vs Team Patterns)
-- ========================================
CREATE TABLE IF NOT EXISTS matchup_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expert_id VARCHAR(50) NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- Generated sorted key for aggregates
    matchup_key_sorted TEXT GENERATED ALWAYS AS (
        CASE
            WHEN home_team < away_team
            THEN home_team || '|' || away_team
            ELSE away_team || '|' || home_team
        END
    ) STORED,

    -- Matchup-specific patterns
    historical_outcomes JSONB DEFAULT '{}',
    rivalry_factors JSONB DEFAULT '{}',
    coaching_matchups JSONB DEFAULT '{}',
    situational_patterns JSONB DEFAULT '{}',

    -- Performance tracking
    prediction_accuracy DECIMAL(5,4) DEFAULT 0.5,
    games_analyzed INTEGER DEFAULT 0,
    home_wins INTEGER DEFAULT 0,
    away_wins INTEGER DEFAULT 0,
    last_game_date DATE,

    -- Vector embedding
    matchup_embedding VECTOR(1536),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT fk_mm_expert FOREIGN KEY (expert_id) REFERENCES enhanced_expert_models(expert_id) ON DELETE CASCADE,
    CONSTRAINT fk_mm_home FOREIGN KEY (home_team) REFERENCES teams(team_id) ON DELETE CASCADE,
    CONSTRAINT fk_mm_away FOREIGN KEY (away_team) REFERENCES teams(team_id) ON DELETE CASCADE,
    CONSTRAINT ux_mm_role UNIQUE (expert_id, home_team, away_team)
);

-- Indexes for matchup memories
CREATE INDEX IF NOT EXISTS idx_mm_expert ON matchup_memories(expert_id);
CREATE INDEX IF NOT EXISTS idx_mm_teams ON matchup_memories(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_mm_sorted ON matchup_memories(expert_id, matchup_key_sorted);
CREATE INDEX IF NOT EXISTS idx_mm_accuracy ON matchup_memories(prediction_accuracy DESC);
CREATE INDEX IF NOT EXISTS idx_mm_hnsw
    ON matchup_memories USING hnsw (matchup_embedding vector_cosine_ops);

-- ========================================
-- 5. ENHANCED PREDICTION CONSTRAINTS
-- ========================================
-- Ensure predicted_winner is not null and references teams
ALTER TABLE IF EXISTS expert_reasoning_chains
ADD CONSTRAINT IF NOT EXISTS fk_predicted_winner
    FOREIGN KEY (predicted_winner) REFERENCES teams(team_id);

-- Add team columns if they don't exist
ALTER TABLE IF EXISTS expert_reasoning_chains
ADD COLUMN IF NOT EXISTS home_team TEXT,
ADD COLUMN IF NOT EXISTS away_team TEXT;

-- Add foreign keys for home/away teams
ALTER TABLE expert_reasoning_chains
ADD CONSTRAINT IF NOT EXISTS fk_erc_home_team
    FOREIGN KEY (home_team) REFERENCES teams(team_id),
ADD CONSTRAINT IF NOT EXISTS fk_erc_away_team
    FOREIGN KEY (away_team) REFERENCES teams(team_id);

-- ========================================
-- 6. RECENCY-AWARE VECTOR SEARCH FUNCTION
-- ========================================
CREATE OR REPLACE FUNCTION search_expert_memories(
    p_expert_id TEXT,
    p_query_embedding VECTOR(1536),
    p_match_threshold FLOAT DEFAULT 0.7,
    p_match_count INT DEFAULT 10,
    p_alpha FLOAT DEFAULT 0.8  -- similarity weight vs recency
)
RETURNS TABLE (
    memory_id TEXT,
    expert_id TEXT,
    game_id TEXT,
    home_team TEXT,
    away_team TEXT,
    game_date DATE,
    similarity_score FLOAT,
    recency_score FLOAT,
    combined_score FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.memory_id,
        m.expert_id,
        m.game_id,
        m.home_team,
        m.away_team,
        m.game_date,
        (1 - (m.combined_embedding <=> p_query_embedding)) AS similarity_score,
        EXP(-GREATEST(0, EXTRACT(EPOCH FROM (NOW() - m.game_date))/86400.0) / 90.0) AS recency_score,
        (p_alpha * (1 - (m.combined_embedding <=> p_query_embedding)) +
         (1 - p_alpha) * EXP(-GREATEST(0, EXTRACT(EPOCH FROM (NOW() - m.game_date))/86400.0) / 90.0)) AS combined_score
    FROM expert_episodic_memories m
    WHERE m.expert_id = p_expert_id
      AND m.combined_embedding IS NOT NULL
      AND (1 - (m.combined_embedding <=> p_query_embedding)) >= p_match_threshold
    ORDER BY combined_score DESC
    LIMIT p_match_count;
END $$;

-- ========================================
-- 7. UTILITY FUNCTIONS
-- ========================================

-- Function to resolve team aliases to canonical team_id
CREATE OR REPLACE FUNCTION resolve_team_alias(p_alias TEXT)
RETURNS TEXT
LANGUAGE plpgsql AS $$
DECLARE
    v_team_id TEXT;
BEGIN
    -- First try direct team_id match
    SELECT team_id INTO v_team_id FROM teams WHERE team_id = UPPER(p_alias);
    IF FOUND THEN
        RETURN v_team_id;
    END IF;

    -- Then try alias lookup
    SELECT team_id INTO v_team_id FROM team_aliases WHERE alias = p_alias;
    IF FOUND THEN
        RETURN v_team_id;
    END IF;

    -- Return null if not found
    RETURN NULL;
END $$;

-- Function to get team knowledge summary
CREATE OR REPLACE FUNCTION get_team_knowledge_summary(p_expert_id TEXT, p_team_id TEXT)
RETURNS JSONB
LANGUAGE plpgsql AS $$
DECLARE
    v_result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'team_id', p_team_id,
        'expert_id', p_expert_id,
        'knowledge_types', jsonb_agg(knowledge_type),
        'avg_confidence', AVG(confidence_level),
        'total_sample_size', SUM(sample_size),
        'avg_accuracy', AVG(accuracy_rate),
        'last_updated', MAX(last_updated)
    ) INTO v_result
    FROM team_knowledge
    WHERE expert_id = p_expert_id AND team_id = p_team_id;

    RETURN COALESCE(v_result, '{}'::jsonb);
END $$;

-- ========================================
-- 8. PERFORMANCE MONITORING VIEWS
-- ========================================

-- View for memory retrieval performance
CREATE OR REPLACE VIEW memory_retrieval_stats AS
SELECT
    expert_id,
    COUNT(*) as total_memories,
    COUNT(combined_embedding) as embedded_memories,
    AVG(CASE WHEN combined_embedding IS NOT NULL THEN 1 ELSE 0 END) as embedding_coverage,
    MIN(game_date) as earliest_memory,
    MAX(game_date) as latest_memory,
    COUNT(DISTINCT home_team) + COUNT(DISTINCT away_team) as teams_covered
FROM expert_episodic_memories
GROUP BY expert_id;

-- View for team knowledge coverage
CREATE OR REPLACE VIEW team_knowledge_coverage AS
SELECT
    expert_id,
    COUNT(DISTINCT team_id) as teams_analyzed,
    COUNT(*) as knowledge_entries,
    AVG(confidence_level) as avg_confidence,
    AVG(accuracy_rate) as avg_accuracy,
    SUM(sample_size) as total_samples
FROM team_knowledge
GROUP BY expert_id;

-- ========================================
-- 9. TRIGGERS FOR AUTOMATIC UPDATES
-- ========================================

-- Update matchup memories when new episodic memories are added
CREATE OR REPLACE FUNCTION update_matchup_memory_trigger()
RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    -- Update or insert matchup memory
    INSERT INTO matchup_memories (expert_id, home_team, away_team, games_analyzed, last_game_date)
    VALUES (NEW.expert_id, NEW.home_team, NEW.away_team, 1, NEW.game_date)
    ON CONFLICT (expert_id, home_team, away_team)
    DO UPDATE SET
        games_analyzed = matchup_memories.games_analyzed + 1,
        last_game_date = GREATEST(matchup_memories.last_game_date, NEW.game_date),
        updated_at = NOW();

    RETURN NEW;
END $$;

CREATE TRIGGER IF NOT EXISTS trigger_update_matchup_memory
    AFTER INSERT ON expert_episodic_memories
    FOR EACH ROW
    EXECUTE FUNCTION update_matchup_memory_trigger();

COMMENT ON MIGRATION IS 'Optimized Expert Memory Schema with canonical teams, embeddings on main table, HNSW indexes, and recency-aware search';
