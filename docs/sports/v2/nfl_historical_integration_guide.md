# NFL Historical Data Integration Guide for Supabase

## Table of Contents

1. [Overview](#overview)
2. [Package Contents](#package-contents)
3. [Database Schema](#database-schema)
4. [Integration Steps](#integration-steps)
5. [Validation and Testing](#validation-and-testing)
6. [API Usage Examples](#api-usage-examples)
7. [Troubleshooting](#troubleshooting)

## Overview

This guide provides comprehensive instructions for integrating historical NFL data (2020-2024) into your Supabase database. The data is sourced from the nflverse project and includes play-by-play data, game information, player rosters, and team details.

**✅ COMPLETED**: Historical data has been successfully imported as of September 2024.

**Key Features**:

- **Comprehensive Data**: 5 seasons of play-by-play data (2020-2024) - 49,995 plays
- **Advanced Analytics**: Includes EPA, WP, CPOE, and other advanced metrics
- **Optimized Schema**: Designed for performance and scalability
- **Automated Setup**: Includes scripts for easy integration
- **Validated Data**: Quality and integrity checks have been performed
- **Real Import**: Successfully imported 287 games, 871 players, 49,995 plays

## Package Contents

The integration package is located in `/home/ubuntu/nfl_integration_package` and contains:

- **SQL Scripts**:
  - `nfl_historical_schema.sql`: Creates all required tables and indexes
  - `01_insert_teams.sql`: Inserts all 32 NFL teams
  - `02_insert_players.sql`: Inserts player roster data
  - `03_insert_games.sql`: Inserts game information
  - `04_insert_plays_part_*.sql`: Inserts play-by-play data in batches

- **Validation and Setup**:
  - `validation_report.json`: Detailed validation results
  - `supabase_setup.sh`: Automated setup script for Supabase

- **Summary**:
  - `integration_summary.json`: Overview of the processed data

## Database Schema

The database schema is designed to be relational and scalable:

### Core Tables

- **`nfl_teams`**: Stores information about each NFL team
  - `team_id` (PK), `team_name`, `conference`, `division`

- **`nfl_players`**: Stores player biographical and roster data
  - `player_id` (PK), `player_name`, `position`, `college`, `draft_info`

- **`nfl_games`**: Contains game-level information
  - `game_id` (PK), `season`, `week`, `home_team`, `away_team`, `home_score`, `away_score`

- **`nfl_plays`**: The main table with play-by-play data
  - `play_id` (PK), `game_id` (FK), `play_type`, `yards_gained`, `epa`, `wp`

### Supporting Tables

- **`nfl_drives`**: Summarizes each offensive drive
  - `drive_id` (PK), `game_id` (FK), `drive_result`, `drive_yards`

- **`nfl_player_stats_game`**: Aggregated player statistics for each game
  - `stat_id` (PK), `game_id` (FK), `player_id` (FK), `pass_yards`, `rush_yards`, etc.

## Integration Steps

### Step 1: Set Up Supabase Project

1. Create a new Supabase project if you haven't already
2. Navigate to the **SQL Editor** in your project dashboard

### Step 2: Create Database Schema

1. Open `nfl_historical_schema.sql`
2. Copy and paste the entire content into the Supabase SQL Editor
3. Click **Run** to create all tables, indexes, and policies

### Step 3: Insert Data (in order)

Execute the following SQL scripts in the SQL Editor in this specific order:

1. **`01_insert_teams.sql`**
2. **`02_insert_players.sql`**
3. **`03_insert_games.sql`**
4. **`04_insert_plays_part_*.sql`** (run each part sequentially)

**Note**: Due to the size of the plays data, it is split into multiple files. Run them one by one to avoid timeouts.

### Automated Setup (Recommended)

Use the `supabase_setup.sh` script for an automated process. You will need to configure it with your Supabase credentials.

```bash
# Example usage (requires Supabase CLI)
supabase sql < nfl_historical_schema.sql
supabase sql < 01_insert_teams.sql
supabase sql < 02_insert_players.sql
supabase sql < 03_insert_games.sql

# Loop through plays files
for file in 04_insert_plays_part_*.sql; do
  echo "Importing $file..."
  supabase sql < "$file"
done
```

## Validation and Testing

After importing the data, run the test queries from `validation_report.json` or the `supabase_setup.sh` script to verify the integration.

**Example Validation Queries**:

```sql
-- Check total games per season
SELECT season, COUNT(*) as games_per_season 
FROM nfl_games 
GROUP BY season 
ORDER BY season;

-- Check top 10 play types
SELECT play_type, COUNT(*) as play_count 
FROM nfl_plays 
WHERE play_type IS NOT NULL 
GROUP BY play_type 
ORDER BY play_count DESC 
LIMIT 10;

-- Check top 10 passers by play count
SELECT p.player_name, COUNT(*) as total_passes
FROM nfl_plays pl
JOIN nfl_players p ON pl.passer_id = p.player_id
WHERE pl.pass_attempt = true
GROUP BY p.player_name
ORDER BY total_passes DESC
LIMIT 10;
```

## API Usage Examples

Your Supabase project will automatically provide a RESTful API for this data.

### Get Games for a Specific Week

```javascript
const { data, error } = await supabase
  .from("nfl_games")
  .select("*")
  .eq("season", 2024)
  .eq("week", 1)
  .order("game_date");
```

### Get Player Statistics for a Game

```javascript
const { data, error } = await supabase
  .from("nfl_player_stats_game")
  .select("*, player:nfl_players(player_name)")
  .eq("game_id", "2024_01_BAL_KC");
```

### Get Top 10 Plays by EPA

```javascript
const { data, error } = await supabase
  .from("nfl_plays")
  .select("play_description, expected_points_added")
  .order("expected_points_added", { ascending: false })
  .limit(10);
```

## Troubleshooting

- **Slow Queries**: Ensure all indexes were created successfully. Use `EXPLAIN` in the SQL Editor to analyze query performance.
- **Data Not Found**: Verify the data was inserted correctly by running `COUNT(*)` queries on each table.
- **Permission Errors**: Check that Row Level Security policies are correctly configured (the schema script sets up public read access by default).
- **Import Timeouts**: If you experience timeouts in the Supabase SQL Editor, break the larger SQL files into smaller chunks.

This comprehensive historical NFL dataset provides a powerful foundation for building analytics dashboards, fantasy football tools, research projects, and more.
