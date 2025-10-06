-- Fix games table schema to match API expectations
-- Run this in Supabase SQL Editor: https://app.supabase.com/project/vaypgzvivahnfegnlinn/editor/sql

-- Add missing columns to games table that the API expects
DO $$
BEGIN
    -- Add game_id column if it doesn't exist
    BEGIN
        ALTER TABLE games ADD COLUMN game_id VARCHAR(100);
        RAISE NOTICE 'Added game_id column to games table';
    EXCEPTION
        WHEN duplicate_column THEN
            RAISE NOTICE 'game_id column already exists';
    END;

    -- Populate game_id with espn_game_id if it exists and game_id is null
    UPDATE games 
    SET game_id = espn_game_id 
    WHERE game_id IS NULL AND espn_game_id IS NOT NULL;

    -- Add other missing columns that might be expected
    BEGIN
        ALTER TABLE games ADD COLUMN season INTEGER;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;

    BEGIN
        ALTER TABLE games ADD COLUMN week INTEGER;
    EXCEPTION
        WHEN duplicate_column THEN NULL;
    END;
END $$;

-- Create index for game_id if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_games_game_id ON games(game_id);

-- Verify the schema
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'games' 
ORDER BY ordinal_position;