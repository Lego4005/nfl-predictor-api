-- Add missing enhanced columns to the existing games table
-- Run this in Supabase SQL Editor

-- Add game_id column for CSV compatibility
ALTER TABLE public.games 
ADD COLUMN IF NOT EXISTS game_id VARCHAR(100);

-- Create unique index on game_id
CREATE UNIQUE INDEX IF NOT EXISTS idx_games_game_id_unique ON games(game_id);

-- Rest days between games (critical for fatigue analysis)
ALTER TABLE public.games 
ADD COLUMN IF NOT EXISTS away_rest INTEGER,
ADD COLUMN IF NOT EXISTS home_rest INTEGER;

-- Betting market data (for comparing expert predictions against consensus)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS spread_line NUMERIC,
ADD COLUMN IF NOT EXISTS away_spread_odds INTEGER,
ADD COLUMN IF NOT EXISTS home_spread_odds INTEGER,
ADD COLUMN IF NOT EXISTS total_line NUMERIC,
ADD COLUMN IF NOT EXISTS over_odds INTEGER,
ADD COLUMN IF NOT EXISTS under_odds INTEGER,
ADD COLUMN IF NOT EXISTS away_moneyline INTEGER,
ADD COLUMN IF NOT EXISTS home_moneyline INTEGER;

-- Quarterback matchup data (QB quality heavily influences outcomes)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS away_qb_id VARCHAR,
ADD COLUMN IF NOT EXISTS away_qb_name VARCHAR,
ADD COLUMN IF NOT EXISTS home_qb_id VARCHAR,
ADD COLUMN IF NOT EXISTS home_qb_name VARCHAR;

-- Coaching matchup data (coaching edges matter in close games)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS away_coach VARCHAR,
ADD COLUMN IF NOT EXISTS home_coach VARCHAR;

-- Game characteristics (divisional games have different dynamics)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS div_game BOOLEAN,
ADD COLUMN IF NOT EXISTS result INTEGER,  -- point differential, positive means home won
ADD COLUMN IF NOT EXISTS total INTEGER,   -- combined score
ADD COLUMN IF NOT EXISTS location VARCHAR,  -- Home, Away, Neutral
ADD COLUMN IF NOT EXISTS weekday VARCHAR,
ADD COLUMN IF NOT EXISTS referee VARCHAR;

-- Weather data (some columns might overlap with existing)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS weather_temperature INTEGER,
ADD COLUMN IF NOT EXISTS weather_wind_mph INTEGER,
ADD COLUMN IF NOT EXISTS roof VARCHAR,
ADD COLUMN IF NOT EXISTS surface VARCHAR;

-- Cross-reference IDs (for linking to other data sources)
ALTER TABLE public.games
ADD COLUMN IF NOT EXISTS old_game_id VARCHAR,
ADD COLUMN IF NOT EXISTS gsis VARCHAR,
ADD COLUMN IF NOT EXISTS nfl_detail_id VARCHAR,
ADD COLUMN IF NOT EXISTS pfr VARCHAR,
ADD COLUMN IF NOT EXISTS pff VARCHAR,
ADD COLUMN IF NOT EXISTS espn VARCHAR,
ADD COLUMN IF NOT EXISTS ftn VARCHAR,
ADD COLUMN IF NOT EXISTS stadium_id VARCHAR;