-- Fix game_time column to use proper timestamptz for timezone-aware storage
-- This will convert all existing timestamps to UTC and change the column type

BEGIN;

-- Step 1: Add a new temporary column with timestamptz type
ALTER TABLE games ADD COLUMN game_time_tz timestamptz;

-- Step 2: Convert existing game_time values to timestamptz
-- Since game_time is stored without timezone info, we need to treat it as UTC
UPDATE games
SET game_time_tz = game_time AT TIME ZONE 'UTC'
WHERE game_time IS NOT NULL;

-- Step 3: Drop the old column
ALTER TABLE games DROP COLUMN game_time;

-- Step 4: Rename the new column to game_time
ALTER TABLE games RENAME COLUMN game_time_tz TO game_time;

-- Step 5: Create index for performance
CREATE INDEX IF NOT EXISTS idx_games_game_time ON games(game_time);

COMMIT;

-- Verify the change
SELECT
  home_team || ' vs ' || away_team as matchup,
  game_time as utc_time,
  game_time AT TIME ZONE 'America/New_York' as est_time,
  timezone as stadium_tz
FROM games
WHERE season = 2025 AND week = 1
ORDER BY game_time
LIMIT 5;