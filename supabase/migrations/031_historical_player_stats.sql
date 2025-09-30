-- Historical Player Stats Table
-- Migration: 031_historical_player_stats.sql
-- Creates table for storing historical NFL player performance data

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================
-- Historical Player Statistics Table
-- ========================================
CREATE TABLE IF NOT EXISTS historical_player_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Player identification
    player_id VARCHAR(20) NOT NULL,
    player_name VARCHAR(100) NOT NULL,
    team VARCHAR(10) NOT NULL,
    opponent VARCHAR(10) NOT NULL,
    position VARCHAR(10) NOT NULL,
    
    -- Game context
    game_date TIMESTAMP NOT NULL,
    week INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    -- Passing statistics
    passing_yards DECIMAL(7,2) DEFAULT 0,
    passing_tds DECIMAL(5,2) DEFAULT 0,
    passing_attempts DECIMAL(5,2) DEFAULT 0,
    passing_completions DECIMAL(5,2) DEFAULT 0,
    
    -- Rushing statistics
    rushing_yards DECIMAL(7,2) DEFAULT 0,
    rushing_tds DECIMAL(5,2) DEFAULT 0,
    rushing_attempts DECIMAL(5,2) DEFAULT 0,
    
    -- Receiving statistics
    receiving_yards DECIMAL(7,2) DEFAULT 0,
    receiving_tds DECIMAL(5,2) DEFAULT 0,
    receptions DECIMAL(5,2) DEFAULT 0,
    targets INTEGER DEFAULT 0,
    
    -- Snap count data
    snap_count DECIMAL(7,2) DEFAULT 0,
    snap_percentage DECIMAL(5,2) DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- Indexes for Performance
-- ========================================
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_player_id ON historical_player_stats(player_id);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_player_name ON historical_player_stats(player_name);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_team ON historical_player_stats(team);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_position ON historical_player_stats(position);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_season_week ON historical_player_stats(season, week);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_game_date ON historical_player_stats(game_date);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_player_season ON historical_player_stats(player_id, season);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_player_team_season ON historical_player_stats(player_id, team, season);
CREATE INDEX IF NOT EXISTS idx_historical_player_stats_position_season ON historical_player_stats(position, season);

-- ========================================
-- Row Level Security (RLS)
-- ========================================
ALTER TABLE historical_player_stats ENABLE ROW LEVEL SECURITY;

-- Create public read access policy
CREATE POLICY "Public read access for historical player stats" 
ON historical_player_stats FOR SELECT 
USING (true);

-- ========================================
-- Comments for Documentation
-- ========================================
COMMENT ON TABLE historical_player_stats IS 'Historical NFL player performance statistics by game';
COMMENT ON COLUMN historical_player_stats.player_id IS 'Unique player identifier';
COMMENT ON COLUMN historical_player_stats.player_name IS 'Player full name';
COMMENT ON COLUMN historical_player_stats.team IS 'Team abbreviation (3 letters)';
COMMENT ON COLUMN historical_player_stats.opponent IS 'Opponent team abbreviation';
COMMENT ON COLUMN historical_player_stats.position IS 'Player position (QB, RB, WR, etc.)';
COMMENT ON COLUMN historical_player_stats.game_date IS 'Date when the game was played';
COMMENT ON COLUMN historical_player_stats.week IS 'NFL week number';
COMMENT ON COLUMN historical_player_stats.season IS 'NFL season year';
COMMENT ON COLUMN historical_player_stats.snap_count IS 'Total snaps played in the game';
COMMENT ON COLUMN historical_player_stats.snap_percentage IS 'Percentage of team snaps played';