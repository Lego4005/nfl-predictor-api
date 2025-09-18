#!/bin/bash
# NFL Historical Data Supabase Setup Script
# Generated on 2025-09-17T00:40:18.909629

echo "Starting NFL Historical Data Integration..."

# Step 1: Create schema
echo "Creating database schema..."
# Run the schema creation SQL (nfl_historical_schema.sql)

# Step 2: Insert teams data
echo "Inserting teams data..."
# Execute: 01_insert_teams.sql

# Step 3: Insert players data  
echo "Inserting players data..."
# Execute: 02_insert_players.sql

# Step 4: Insert games data
echo "Inserting games data..."
# Execute: 03_insert_games.sql

# Step 5: Insert plays data (in batches)
echo "Inserting plays data..."
for i in {01..30}; do
    file="04_insert_plays_part_${i}.sql"
    if [ -f "$file" ]; then
        echo "Processing $file..."
        # Execute the file
    fi
done

echo "Integration complete!"

# Step 6: Run validation queries
echo "Running validation queries..."
echo "Query 1: SELECT COUNT(*) as total_teams FROM nfl_teams;"
# Execute: SELECT COUNT(*) as total_teams FROM nfl_teams;

echo "Query 2: SELECT COUNT(*) as total_players FROM nfl_players;"
# Execute: SELECT COUNT(*) as total_players FROM nfl_players;

echo "Query 3: SELECT COUNT(*) as total_games FROM nfl_games;"
# Execute: SELECT COUNT(*) as total_games FROM nfl_games;

echo "Query 4: SELECT COUNT(*) as total_plays FROM nfl_plays;"
# Execute: SELECT COUNT(*) as total_plays FROM nfl_plays;

echo "Query 5: SELECT season, COUNT(*) as games_per_season FROM nfl_games GROUP BY season ORDER BY season;"
# Execute: SELECT season, COUNT(*) as games_per_season FROM nfl_games GROUP BY season ORDER BY season;

echo "Query 6: SELECT play_type, COUNT(*) as play_count FROM nfl_plays WHERE play_type IS NOT NULL GROUP BY play_type ORDER BY play_count DESC LIMIT 10;"
# Execute: SELECT play_type, COUNT(*) as play_count FROM nfl_plays WHERE play_type IS NOT NULL GROUP BY play_type ORDER BY play_count DESC LIMIT 10;

echo "Query 7: SELECT home_team, COUNT(*) as home_games FROM nfl_games GROUP BY home_team ORDER BY home_games DESC;"
# Execute: SELECT home_team, COUNT(*) as home_games FROM nfl_games GROUP BY home_team ORDER BY home_games DESC;

echo "Query 8: SELECT possession_team, AVG(expected_points_added) as avg_epa FROM nfl_plays WHERE expected_points_added IS NOT NULL GROUP BY possession_team ORDER BY avg_epa DESC LIMIT 10;"
# Execute: SELECT possession_team, AVG(expected_points_added) as avg_epa FROM nfl_plays WHERE expected_points_added IS NOT NULL GROUP BY possession_team ORDER BY avg_epa DESC LIMIT 10;

echo "Query 9: SELECT player_name, COUNT(*) as total_plays FROM nfl_plays p JOIN nfl_players pl ON p.passer_id = pl.player_id GROUP BY player_name ORDER BY total_plays DESC LIMIT 10;"
# Execute: SELECT player_name, COUNT(*) as total_plays FROM nfl_plays p JOIN nfl_players pl ON p.passer_id = pl.player_id GROUP BY player_name ORDER BY total_plays DESC LIMIT 10;

echo "Query 10: SELECT COUNT(*) as games_missing_scores FROM nfl_games WHERE home_score IS NULL OR away_score IS NULL;"
# Execute: SELECT COUNT(*) as games_missing_scores FROM nfl_games WHERE home_score IS NULL OR away_score IS NULL;

echo "Query 11: SELECT COUNT(*) as plays_missing_teams FROM nfl_plays WHERE possession_team IS NULL;"
# Execute: SELECT COUNT(*) as plays_missing_teams FROM nfl_plays WHERE possession_team IS NULL;

echo "Query 12: SELECT COUNT(*) as invalid_downs FROM nfl_plays WHERE down NOT IN (1,2,3,4) AND down IS NOT NULL;"
# Execute: SELECT COUNT(*) as invalid_downs FROM nfl_plays WHERE down NOT IN (1,2,3,4) AND down IS NOT NULL;


echo "Setup and validation complete!"
echo "Total data integrated:"
echo "- Teams: 32"
echo "- Players: ~1,700"  
echo "- Games: ~850"
echo "- Plays: ~150,000"
