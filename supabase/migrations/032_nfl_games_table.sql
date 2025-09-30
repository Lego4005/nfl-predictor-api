-- Create nfl_games table for historical games data
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS nfl_games (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(100) UNIQUE NOT NULL,
    season INTEGER,
    week INTEGER, 
    game_type VARCHAR(20),
    game_date DATE,
    game_datetime TIMESTAMP WITH TIME ZONE,
    
    -- Teams
    home_team VARCHAR(10),
    away_team VARCHAR(10),
    home_score INTEGER,
    away_score INTEGER,
    
    -- Game Details
    overtime BOOLEAN DEFAULT false,
    stadium VARCHAR(100),
    roof VARCHAR(20),
    surface VARCHAR(20),
    weather_temperature INTEGER,
    weather_wind_mph INTEGER,
    
    -- Rest and Preparation
    away_rest INTEGER,
    home_rest INTEGER,
    
    -- Betting Lines
    spread_line DECIMAL(5,2),
    away_spread_odds INTEGER,
    home_spread_odds INTEGER,
    total_line DECIMAL(5,2),
    over_odds INTEGER,
    under_odds INTEGER,
    away_moneyline INTEGER,
    home_moneyline INTEGER,
    
    -- Personnel
    away_qb_id VARCHAR(20),
    away_qb_name VARCHAR(100),
    home_qb_id VARCHAR(20),
    home_qb_name VARCHAR(100),
    away_coach VARCHAR(100),
    home_coach VARCHAR(100),
    
    -- Additional Game Info
    div_game BOOLEAN DEFAULT false,
    result INTEGER,
    total INTEGER,
    location VARCHAR(10),
    weekday VARCHAR(15),
    referee VARCHAR(100),
    
    -- Legacy IDs and References
    old_game_id VARCHAR(50),
    gsis VARCHAR(50),
    nfl_detail_id VARCHAR(50),
    pfr VARCHAR(50),
    pff VARCHAR(50),
    espn VARCHAR(50),
    ftn VARCHAR(50),
    stadium_id VARCHAR(50),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_nfl_games_game_id ON nfl_games(game_id);
CREATE INDEX IF NOT EXISTS idx_nfl_games_season_week ON nfl_games(season, week);
CREATE INDEX IF NOT EXISTS idx_nfl_games_teams ON nfl_games(home_team, away_team);
CREATE INDEX IF NOT EXISTS idx_nfl_games_date ON nfl_games(game_date);

-- Add Row Level Security (RLS) but allow public read access
ALTER TABLE nfl_games ENABLE ROW LEVEL SECURITY;

-- Create policy for public read access to historical games data
CREATE POLICY "Public read access" ON nfl_games FOR SELECT USING (true);