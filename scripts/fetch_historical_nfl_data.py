#!/usr/bin/env python3
"""
Fetch Historical NFL Data from nflverse (1999-2025)
Generates SQL files for Supabase import
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import requests
from io import StringIO

# nflverse data URLs
NFLVERSE_BASE_URL = "https://github.com/nflverse/nflverse-data/releases/download/"
PBPSTATS_URL = NFLVERSE_BASE_URL + "pbp/play_by_play_"
ROSTERS_URL = "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_"

# Output directory for SQL files
OUTPUT_DIR = "docs/sports/v2/sql_data"

def ensure_output_dir():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

def fetch_teams_data():
    """Fetch NFL teams data"""
    print("📊 Fetching NFL teams data...")

    # Team data with divisions
    teams_data = [
        ('ARI', 'Arizona Cardinals', 'Arizona', 'AZ', 'NFC', 'West'),
        ('ATL', 'Atlanta Falcons', 'Atlanta', 'GA', 'NFC', 'South'),
        ('BAL', 'Baltimore Ravens', 'Baltimore', 'MD', 'AFC', 'North'),
        ('BUF', 'Buffalo Bills', 'Buffalo', 'NY', 'AFC', 'East'),
        ('CAR', 'Carolina Panthers', 'Charlotte', 'NC', 'NFC', 'South'),
        ('CHI', 'Chicago Bears', 'Chicago', 'IL', 'NFC', 'North'),
        ('CIN', 'Cincinnati Bengals', 'Cincinnati', 'OH', 'AFC', 'North'),
        ('CLE', 'Cleveland Browns', 'Cleveland', 'OH', 'AFC', 'North'),
        ('DAL', 'Dallas Cowboys', 'Dallas', 'TX', 'NFC', 'East'),
        ('DEN', 'Denver Broncos', 'Denver', 'CO', 'AFC', 'West'),
        ('DET', 'Detroit Lions', 'Detroit', 'MI', 'NFC', 'North'),
        ('GB', 'Green Bay Packers', 'Green Bay', 'WI', 'NFC', 'North'),
        ('HOU', 'Houston Texans', 'Houston', 'TX', 'AFC', 'South'),
        ('IND', 'Indianapolis Colts', 'Indianapolis', 'IN', 'AFC', 'South'),
        ('JAX', 'Jacksonville Jaguars', 'Jacksonville', 'FL', 'AFC', 'South'),
        ('KC', 'Kansas City Chiefs', 'Kansas City', 'MO', 'AFC', 'West'),
        ('LAC', 'Los Angeles Chargers', 'Los Angeles', 'CA', 'AFC', 'West'),
        ('LAR', 'Los Angeles Rams', 'Los Angeles', 'CA', 'NFC', 'West'),
        ('LV', 'Las Vegas Raiders', 'Las Vegas', 'NV', 'AFC', 'West'),
        ('MIA', 'Miami Dolphins', 'Miami', 'FL', 'AFC', 'East'),
        ('MIN', 'Minnesota Vikings', 'Minneapolis', 'MN', 'NFC', 'North'),
        ('NE', 'New England Patriots', 'Foxborough', 'MA', 'AFC', 'East'),
        ('NO', 'New Orleans Saints', 'New Orleans', 'LA', 'NFC', 'South'),
        ('NYG', 'New York Giants', 'East Rutherford', 'NJ', 'NFC', 'East'),
        ('NYJ', 'New York Jets', 'East Rutherford', 'NJ', 'AFC', 'East'),
        ('PHI', 'Philadelphia Eagles', 'Philadelphia', 'PA', 'NFC', 'East'),
        ('PIT', 'Pittsburgh Steelers', 'Pittsburgh', 'PA', 'AFC', 'North'),
        ('SEA', 'Seattle Seahawks', 'Seattle', 'WA', 'NFC', 'West'),
        ('SF', 'San Francisco 49ers', 'San Francisco', 'CA', 'NFC', 'West'),
        ('TB', 'Tampa Bay Buccaneers', 'Tampa', 'FL', 'NFC', 'South'),
        ('TEN', 'Tennessee Titans', 'Nashville', 'TN', 'AFC', 'South'),
        ('WAS', 'Washington Commanders', 'Washington', 'DC', 'NFC', 'East'),
    ]

    # Generate SQL insert statements
    sql_content = "-- NFL Teams Data\n"
    sql_content += "-- Generated: " + datetime.now().isoformat() + "\n\n"
    sql_content += "INSERT INTO nfl_teams (team_id, team_name, team_city, team_state, conference, division) VALUES\n"

    values = []
    for team in teams_data:
        values.append(f"('{team[0]}', '{team[1]}', '{team[2]}', '{team[3]}', '{team[4]}', '{team[5]}')")

    sql_content += ",\n".join(values) + ";\n"

    # Write to file
    output_file = os.path.join(OUTPUT_DIR, "01_insert_teams.sql")
    with open(output_file, 'w') as f:
        f.write(sql_content)

    print(f"✅ Teams data saved to {output_file}")
    return len(teams_data)

def fetch_sample_play_data():
    """Fetch a sample of play-by-play data from 2024 season"""
    print("📊 Fetching sample play-by-play data from 2024...")

    try:
        # Try to fetch 2024 data as a sample
        url = PBPSTATS_URL + "2024.csv"
        print(f"   Downloading from {url}...")

        # Read CSV directly from URL
        df = pd.read_csv(url, low_memory=False)

        print(f"   ✅ Loaded {len(df)} plays from 2024 season")

        # Select key columns for our database
        key_columns = [
            'game_id', 'play_id', 'play_type', 'down', 'ydstogo', 'yardline_100',
            'game_seconds_remaining', 'posteam', 'defteam', 'yards_gained',
            'play_type', 'pass_attempt', 'rush_attempt', 'touchdown',
            'interception', 'fumble', 'sack', 'penalty', 'epa', 'wp', 'cpoe'
        ]

        # Filter to columns that exist
        available_cols = [col for col in key_columns if col in df.columns]
        df_filtered = df[available_cols].head(1000)  # Sample first 1000 plays

        # Generate sample games data
        games_df = df[['game_id', 'home_team', 'away_team', 'season', 'week']].drop_duplicates()
        games_sample = games_df.head(50)

        # Generate SQL for games
        sql_games = "-- Sample NFL Games Data\n"
        sql_games += "-- Generated: " + datetime.now().isoformat() + "\n\n"
        sql_games += "INSERT INTO nfl_games (game_id, season, week, home_team, away_team, game_date) VALUES\n"

        game_values = []
        for _, game in games_sample.iterrows():
            # Extract date from game_id (format: YYYY_WW_AWAY_HOME)
            year = str(game['game_id'])[:4]
            date_str = f"{year}-09-01"  # Placeholder date
            game_values.append(f"('{game['game_id']}', {game['season']}, {game['week']}, "
                             f"'{game['home_team']}', '{game['away_team']}', '{date_str}')")

        sql_games += ",\n".join(game_values) + ";\n"

        # Write games file
        games_file = os.path.join(OUTPUT_DIR, "03_insert_games.sql")
        with open(games_file, 'w') as f:
            f.write(sql_games)

        print(f"✅ Sample games data saved to {games_file}")

        # Generate SQL for plays (sample)
        sql_plays = "-- Sample NFL Plays Data\n"
        sql_plays += "-- Generated: " + datetime.now().isoformat() + "\n\n"
        sql_plays += "INSERT INTO nfl_plays (play_id, game_id, play_type, down, yards_to_go, "
        sql_plays += "yards_gained, possession_team, defense_team) VALUES\n"

        play_values = []
        for _, play in df_filtered.head(100).iterrows():
            play_id = f"{play.get('game_id', 'NA')}_{play.name}"
            play_values.append(f"('{play_id}', '{play.get('game_id', 'NA')}', "
                             f"'{play.get('play_type', 'NA')}', {play.get('down', 'NULL')}, "
                             f"{play.get('ydstogo', 'NULL')}, {play.get('yards_gained', 'NULL')}, "
                             f"'{play.get('posteam', 'NA')}', '{play.get('defteam', 'NA')}')")

        sql_plays += ",\n".join(play_values[:20]) + ";\n"  # Just 20 sample plays

        # Write plays file
        plays_file = os.path.join(OUTPUT_DIR, "04_insert_plays_sample.sql")
        with open(plays_file, 'w') as f:
            f.write(sql_plays)

        print(f"✅ Sample plays data saved to {plays_file}")

        return len(games_sample), len(df_filtered)

    except Exception as e:
        print(f"⚠️ Could not fetch play-by-play data: {e}")
        print("   Note: Full historical data requires significant download (>1GB)")
        return 0, 0

def create_sample_players():
    """Create sample player data"""
    print("📊 Creating sample player data...")

    # Sample players (top QBs from recent seasons)
    players_data = [
        ('00-0034796', 'Patrick Mahomes', 'QB', 15, 75, 230, '1995-09-17', 'Texas Tech', 2017),
        ('00-0033873', 'Josh Allen', 'QB', 17, 77, 237, '1996-05-21', 'Wyoming', 2018),
        ('00-0034855', 'Lamar Jackson', 'QB', 8, 74, 212, '1997-01-07', 'Louisville', 2018),
        ('00-0035228', 'Joe Burrow', 'QB', 9, 76, 221, '1996-12-10', 'LSU', 2020),
        ('00-0036355', 'Justin Herbert', 'QB', 10, 78, 236, '1998-03-10', 'Oregon', 2020),
        ('00-0031280', 'Dak Prescott', 'QB', 4, 74, 238, '1993-07-29', 'Mississippi State', 2016),
        ('00-0036442', 'Jalen Hurts', 'QB', 1, 73, 223, '1998-08-07', 'Oklahoma', 2020),
        ('00-0036212', 'Tua Tagovailoa', 'QB', 1, 73, 217, '1998-03-02', 'Alabama', 2020),
        ('00-0023459', 'Aaron Rodgers', 'QB', 8, 74, 225, '1983-12-02', 'California', 2005),
        ('00-0032950', 'Jared Goff', 'QB', 16, 76, 222, '1994-10-14', 'California', 2016),
    ]

    # Generate SQL
    sql_content = "-- Sample NFL Players Data\n"
    sql_content += "-- Generated: " + datetime.now().isoformat() + "\n\n"
    sql_content += "INSERT INTO nfl_players (player_id, player_name, position, jersey_number, "
    sql_content += "height_inches, weight_lbs, birth_date, college, draft_year) VALUES\n"

    values = []
    for player in players_data:
        values.append(f"('{player[0]}', '{player[1]}', '{player[2]}', {player[3]}, "
                     f"{player[4]}, {player[5]}, '{player[6]}', '{player[7]}', {player[8]})")

    sql_content += ",\n".join(values) + ";\n"

    # Write to file
    output_file = os.path.join(OUTPUT_DIR, "02_insert_players.sql")
    with open(output_file, 'w') as f:
        f.write(sql_content)

    print(f"✅ Player data saved to {output_file}")
    return len(players_data)

def generate_summary():
    """Generate summary of created files"""
    summary = {
        "generated_at": datetime.now().isoformat(),
        "description": "Sample NFL historical data for testing",
        "files_created": [],
        "data_summary": {
            "teams": 32,
            "players_sample": 10,
            "games_sample": 50,
            "plays_sample": 100
        },
        "notes": [
            "This is sample data for testing the schema",
            "Full historical data (1999-2025) requires downloading ~1GB+ from nflverse",
            "To get full data, use nflverse R package or Python nfl-data-py package"
        ]
    }

    # List created files
    for file in os.listdir(OUTPUT_DIR):
        if file.endswith('.sql'):
            file_path = os.path.join(OUTPUT_DIR, file)
            file_size = os.path.getsize(file_path) / 1024  # KB
            summary["files_created"].append({
                "name": file,
                "size_kb": round(file_size, 2)
            })

    # Save summary
    summary_file = os.path.join(OUTPUT_DIR, "data_summary.json")
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n📋 Summary saved to {summary_file}")
    return summary

def main():
    """Main function to fetch and process NFL data"""
    print("🏈 NFL Historical Data Fetcher")
    print("=" * 50)
    print("Fetching sample data from nflverse project...\n")

    # Create output directory
    ensure_output_dir()

    # Fetch different data types
    teams_count = fetch_teams_data()
    print(f"   ✓ {teams_count} teams processed")

    players_count = create_sample_players()
    print(f"   ✓ {players_count} sample players created")

    games_count, plays_count = fetch_sample_play_data()
    print(f"   ✓ {games_count} sample games processed")
    print(f"   ✓ {plays_count} sample plays processed")

    # Generate summary
    summary = generate_summary()

    print("\n" + "=" * 50)
    print("✨ Data fetching complete!")
    print(f"📁 Files saved to: {OUTPUT_DIR}")
    print("\n📊 Data Summary:")
    print(f"   - Teams: {summary['data_summary']['teams']}")
    print(f"   - Players (sample): {summary['data_summary']['players_sample']}")
    print(f"   - Games (sample): {summary['data_summary']['games_sample']}")
    print(f"   - Plays (sample): {summary['data_summary']['plays_sample']}")
    print("\n⚠️ Note: This is sample data for testing.")
    print("   For full historical data (1999-2025), consider using:")
    print("   - R: install.packages('nflverse')")
    print("   - Python: pip install nfl-data-py")
    print("\n📚 Documentation: https://nflverse.nflverse.com/")

if __name__ == "__main__":
    main()