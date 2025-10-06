-- Add missing columns to games table for ESPN data integration
-- Run this in Supabase SQL Editor

-- Add winner column to track game outcomes
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS winner VARCHAR(3);

-- Add temperature column for weather data
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS temperature INTEGER;

-- Add attendance column
ALTER TABLE games 
ADD COLUMN IF NOT EXISTS attendance INTEGER;

-- Add indexes for new columns
CREATE INDEX IF NOT EXISTS idx_games_winner ON games(winner);
CREATE INDEX IF NOT EXISTS idx_games_attendance ON games(attendance);

-- Update existing schema comments
COMMENT ON COLUMN games.winner IS 'Team abbreviation of the winning team (null if game not finished)';
COMMENT ON COLUMN games.temperature IS 'Game temperature in Fahrenheit';
COMMENT ON COLUMN games.attendance IS 'Game attendance number';

-- Verify the new columns were added
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'games' 
    AND column_name IN ('winner', 'temperature', 'attendance')
ORDER BY column_name;