-- Add missing columns to the games table for enhanced NFL data
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/vaypgzvivahnfegnlinn/editor/sql

-- Add stadium information
ALTER TABLE games
ADD COLUMN IF NOT EXISTS stadium VARCHAR(100);

-- Add location information
ALTER TABLE games
ADD COLUMN IF NOT EXISTS city VARCHAR(50);

ALTER TABLE games
ADD COLUMN IF NOT EXISTS state VARCHAR(2);

ALTER TABLE games
ADD COLUMN IF NOT EXISTS timezone VARCHAR(10);

-- Add network/broadcasting information
ALTER TABLE games
ADD COLUMN IF NOT EXISTS network VARCHAR(20);

-- Add game type information
ALTER TABLE games
ADD COLUMN IF NOT EXISTS day_of_week VARCHAR(10);

ALTER TABLE games
ADD COLUMN IF NOT EXISTS is_primetime BOOLEAN DEFAULT FALSE;

ALTER TABLE games
ADD COLUMN IF NOT EXISTS is_playoff BOOLEAN DEFAULT FALSE;

ALTER TABLE games
ADD COLUMN IF NOT EXISTS is_international BOOLEAN DEFAULT FALSE;

ALTER TABLE games
ADD COLUMN IF NOT EXISTS international_location VARCHAR(50);

-- Add indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_games_network ON games(network);
CREATE INDEX IF NOT EXISTS idx_games_stadium ON games(stadium);
CREATE INDEX IF NOT EXISTS idx_games_primetime ON games(is_primetime);
CREATE INDEX IF NOT EXISTS idx_games_playoff ON games(is_playoff);

-- Verify columns were added
SELECT
    column_name,
    data_type,
    is_nullable
FROM
    information_schema.columns
WHERE
    table_name = 'games'
    AND column_name IN (
        'stadium', 'city', 'state', 'timezone', 'network',
        'day_of_week', 'is_primetime', 'is_playoff',
        'is_international', 'international_location'
    )
ORDER BY
    column_name;