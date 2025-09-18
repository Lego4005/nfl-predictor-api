-- Comprehensive NFL Data Storage Tables
-- Creates tables for storing 2025 NFL data with vector embeddings
-- Required for supabase_storage_service.py

-- Table: team_stats
-- Stores team season statistics
CREATE TABLE IF NOT EXISTS team_stats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    season INTEGER NOT NULL,
    team VARCHAR(10) NOT NULL,
    points_per_game DECIMAL(5,2) DEFAULT 0,
    opponent_points_per_game DECIMAL(5,2) DEFAULT 0,
    total_yards_per_game DECIMAL(7,2) DEFAULT 0,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint for season/team
    UNIQUE(season, team)
);

-- Table: injuries
-- Stores injury reports
CREATE TABLE IF NOT EXISTS injuries (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    player VARCHAR(200) NOT NULL,
    team VARCHAR(10) NOT NULL,
    position VARCHAR(20),
    injury VARCHAR(200),
    status VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table: betting_odds
-- Stores betting odds and lines
CREATE TABLE IF NOT EXISTS betting_odds (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    game_id VARCHAR(100) NOT NULL,
    home_team VARCHAR(10) NOT NULL,
    away_team VARCHAR(10) NOT NULL,
    spread DECIMAL(5,2),
    total DECIMAL(5,2),
    home_odds INTEGER,
    away_odds INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint for season/week/game
    UNIQUE(season, week, game_id)
);

-- Table: player_props
-- Stores player prop bets
CREATE TABLE IF NOT EXISTS player_props (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    season INTEGER NOT NULL,
    week INTEGER NOT NULL,
    player VARCHAR(200) NOT NULL,
    team VARCHAR(10) NOT NULL,
    prop_type VARCHAR(100),
    value DECIMAL(8,2),
    odds INTEGER,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add embedding column to existing games table if it doesn't exist
DO $$
BEGIN
    BEGIN
        ALTER TABLE games ADD COLUMN embedding VECTOR(10);
        ALTER TABLE games ADD COLUMN game_id VARCHAR(100);
        ALTER TABLE games ADD COLUMN season INTEGER;
        ALTER TABLE games ADD COLUMN week INTEGER;
        ALTER TABLE games ADD COLUMN game_status VARCHAR(50);
    EXCEPTION
        WHEN duplicate_column THEN
            -- Column already exists, do nothing
            NULL;
    END;
END $$;

-- Update games table to match storage service expectations
DO $$
BEGIN
    -- Add missing columns that might not exist
    BEGIN
        ALTER TABLE games ADD COLUMN game_time TIMESTAMP WITH TIME ZONE;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_team_stats_season_team ON team_stats(season, team);
CREATE INDEX IF NOT EXISTS idx_injuries_season_week ON injuries(season, week);
CREATE INDEX IF NOT EXISTS idx_injuries_team ON injuries(team);
CREATE INDEX IF NOT EXISTS idx_betting_odds_season_week ON betting_odds(season, week);
CREATE INDEX IF NOT EXISTS idx_betting_odds_game_id ON betting_odds(game_id);
CREATE INDEX IF NOT EXISTS idx_player_props_season_week ON player_props(season, week);
CREATE INDEX IF NOT EXISTS idx_player_props_player ON player_props(player);
CREATE INDEX IF NOT EXISTS idx_games_embedding ON games USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX IF NOT EXISTS idx_games_game_id ON games(game_id);
CREATE INDEX IF NOT EXISTS idx_games_season_week ON games(season, week);

-- Enable RLS on new tables
ALTER TABLE team_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE injuries ENABLE ROW LEVEL SECURITY;
ALTER TABLE betting_odds ENABLE ROW LEVEL SECURITY;
ALTER TABLE player_props ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (allow all for now, can be restricted later)
CREATE POLICY "Allow all operations on team_stats" ON team_stats
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on injuries" ON injuries
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on betting_odds" ON betting_odds
    FOR ALL USING (true);

CREATE POLICY "Allow all operations on player_props" ON player_props
    FOR ALL USING (true);

-- Update existing games policies to allow vector operations
DROP POLICY IF EXISTS "Enable read access for games" ON games;
CREATE POLICY "Allow all operations on games" ON games
    FOR ALL USING (true);

-- Comments
COMMENT ON TABLE team_stats IS 'NFL team season statistics from SportsData.io';
COMMENT ON TABLE injuries IS 'NFL injury reports by week';
COMMENT ON TABLE betting_odds IS 'NFL betting odds and lines';
COMMENT ON TABLE player_props IS 'NFL player prop bets';
COMMENT ON COLUMN games.embedding IS 'Vector embedding for game similarity search';