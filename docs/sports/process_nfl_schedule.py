#!/usr/bin/env python3
"""
NFL Schedule Data Processor for Supabase
Converts raw NFL schedule data into a structured format suitable for Supabase database
"""

import json
import re
from datetime import datetime
from typing import List, Dict, Any

def parse_schedule_data() -> List[Dict[str, Any]]:
    """Parse the raw NFL schedule data and convert to structured format"""
    
    # Sample data structure - this will be expanded with full schedule
    games = []
    
    # Week 1 games
    week1_games = [
        {
            "game_id": "2025090401",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-04",
            "game_time": "20:20:00",
            "game_datetime": "2025-09-04T20:20:00",
            "day_of_week": "Thursday",
            "away_team": "DAL",
            "away_team_name": "Dallas Cowboys",
            "home_team": "PHI", 
            "home_team_name": "Philadelphia Eagles",
            "network": "NBC",
            "stadium": "Lincoln Financial Field",
            "city": "Philadelphia",
            "state": "PA",
            "timezone": "ET",
            "is_primetime": True,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "20:20:00",
            "kickoff_time_local": "20:20:00"
        },
        {
            "game_id": "2025090501",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-05",
            "game_time": "20:00:00",
            "game_datetime": "2025-09-05T20:00:00",
            "day_of_week": "Friday",
            "away_team": "KC",
            "away_team_name": "Kansas City Chiefs",
            "home_team": "LAC",
            "home_team_name": "Los Angeles Chargers",
            "network": "YouTube",
            "stadium": "Neo Química Arena",
            "city": "São Paulo",
            "state": None,
            "timezone": "BRT",
            "is_primetime": True,
            "is_playoff": False,
            "is_international": True,
            "international_location": "Brazil",
            "kickoff_time_et": "20:00:00",
            "kickoff_time_local": "21:00:00"
        },
        {
            "game_id": "2025090701",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-07",
            "game_time": "13:00:00",
            "game_datetime": "2025-09-07T13:00:00",
            "day_of_week": "Sunday",
            "away_team": "PIT",
            "away_team_name": "Pittsburgh Steelers",
            "home_team": "NYJ",
            "home_team_name": "New York Jets",
            "network": "CBS",
            "stadium": "MetLife Stadium",
            "city": "East Rutherford",
            "state": "NJ",
            "timezone": "ET",
            "is_primetime": False,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "13:00:00",
            "kickoff_time_local": "13:00:00"
        },
        {
            "game_id": "2025090702",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-07",
            "game_time": "13:00:00",
            "game_datetime": "2025-09-07T13:00:00",
            "day_of_week": "Sunday",
            "away_team": "WSH",
            "away_team_name": "Washington Commanders",
            "home_team": "NYG",
            "home_team_name": "New York Giants",
            "network": "FOX",
            "stadium": "MetLife Stadium",
            "city": "East Rutherford",
            "state": "NJ",
            "timezone": "ET",
            "is_primetime": False,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "13:00:00",
            "kickoff_time_local": "13:00:00"
        },
        {
            "game_id": "2025090715",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-07",
            "game_time": "20:20:00",
            "game_datetime": "2025-09-07T20:20:00",
            "day_of_week": "Sunday",
            "away_team": "BUF",
            "away_team_name": "Buffalo Bills",
            "home_team": "BAL",
            "home_team_name": "Baltimore Ravens",
            "network": "NBC",
            "stadium": "M&T Bank Stadium",
            "city": "Baltimore",
            "state": "MD",
            "timezone": "ET",
            "is_primetime": True,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "20:20:00",
            "kickoff_time_local": "20:20:00"
        },
        {
            "game_id": "2025090801",
            "season": 2025,
            "week": 1,
            "game_type": "REG",
            "game_date": "2025-09-08",
            "game_time": "20:15:00",
            "game_datetime": "2025-09-08T20:15:00",
            "day_of_week": "Monday",
            "away_team": "MIN",
            "away_team_name": "Minnesota Vikings",
            "home_team": "CHI",
            "home_team_name": "Chicago Bears",
            "network": "ESPN",
            "stadium": "Soldier Field",
            "city": "Chicago",
            "state": "IL",
            "timezone": "CT",
            "is_primetime": True,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "20:15:00",
            "kickoff_time_local": "19:15:00"
        }
    ]
    
    games.extend(week1_games)
    
    # Week 2 games
    week2_games = [
        {
            "game_id": "2025091101",
            "season": 2025,
            "week": 2,
            "game_type": "REG",
            "game_date": "2025-09-11",
            "game_time": "20:15:00",
            "game_datetime": "2025-09-11T20:15:00",
            "day_of_week": "Thursday",
            "away_team": "WSH",
            "away_team_name": "Washington Commanders",
            "home_team": "GB",
            "home_team_name": "Green Bay Packers",
            "network": "Prime Video",
            "stadium": "Lambeau Field",
            "city": "Green Bay",
            "state": "WI",
            "timezone": "CT",
            "is_primetime": True,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "20:15:00",
            "kickoff_time_local": "19:15:00"
        },
        {
            "game_id": "2025091413",
            "season": 2025,
            "week": 2,
            "game_type": "REG",
            "game_date": "2025-09-14",
            "game_time": "16:25:00",
            "game_datetime": "2025-09-14T16:25:00",
            "day_of_week": "Sunday",
            "away_team": "PHI",
            "away_team_name": "Philadelphia Eagles",
            "home_team": "KC",
            "home_team_name": "Kansas City Chiefs",
            "network": "FOX",
            "stadium": "Arrowhead Stadium",
            "city": "Kansas City",
            "state": "MO",
            "timezone": "CT",
            "is_primetime": False,
            "is_playoff": False,
            "is_international": False,
            "international_location": None,
            "kickoff_time_et": "16:25:00",
            "kickoff_time_local": "15:25:00"
        }
    ]
    
    games.extend(week2_games)
    
    return games

def create_supabase_schema() -> Dict[str, Any]:
    """Create the Supabase table schema for NFL games"""
    
    schema = {
        "table_name": "nfl_games_2025",
        "columns": [
            {
                "name": "game_id",
                "type": "varchar(20)",
                "primary_key": True,
                "description": "Unique game identifier (YYYYMMDDHH format)"
            },
            {
                "name": "season",
                "type": "integer",
                "description": "NFL season year"
            },
            {
                "name": "week",
                "type": "integer", 
                "description": "Week number (1-18 for regular season)"
            },
            {
                "name": "game_type",
                "type": "varchar(10)",
                "description": "Game type: REG, WC, DIV, CONF, SB"
            },
            {
                "name": "game_date",
                "type": "date",
                "description": "Game date (YYYY-MM-DD)"
            },
            {
                "name": "game_time",
                "type": "time",
                "description": "Game time in ET (HH:MM:SS)"
            },
            {
                "name": "game_datetime",
                "type": "timestamp",
                "description": "Full game datetime in ET"
            },
            {
                "name": "day_of_week",
                "type": "varchar(10)",
                "description": "Day of the week"
            },
            {
                "name": "away_team",
                "type": "varchar(3)",
                "description": "Away team abbreviation"
            },
            {
                "name": "away_team_name",
                "type": "varchar(50)",
                "description": "Away team full name"
            },
            {
                "name": "home_team",
                "type": "varchar(3)",
                "description": "Home team abbreviation"
            },
            {
                "name": "home_team_name",
                "type": "varchar(50)",
                "description": "Home team full name"
            },
            {
                "name": "network",
                "type": "varchar(20)",
                "description": "Broadcasting network"
            },
            {
                "name": "stadium",
                "type": "varchar(100)",
                "description": "Stadium name"
            },
            {
                "name": "city",
                "type": "varchar(50)",
                "description": "City where game is played"
            },
            {
                "name": "state",
                "type": "varchar(2)",
                "description": "State abbreviation (null for international)"
            },
            {
                "name": "timezone",
                "type": "varchar(3)",
                "description": "Local timezone abbreviation"
            },
            {
                "name": "is_primetime",
                "type": "boolean",
                "description": "Whether game is primetime (Thu/Sun/Mon night)"
            },
            {
                "name": "is_playoff",
                "type": "boolean",
                "description": "Whether game is playoff game"
            },
            {
                "name": "is_international",
                "type": "boolean",
                "description": "Whether game is played internationally"
            },
            {
                "name": "international_location",
                "type": "varchar(50)",
                "description": "Country if international game"
            },
            {
                "name": "kickoff_time_et",
                "type": "time",
                "description": "Kickoff time in Eastern Time"
            },
            {
                "name": "kickoff_time_local",
                "type": "time",
                "description": "Kickoff time in local timezone"
            },
            {
                "name": "created_at",
                "type": "timestamp",
                "default": "now()",
                "description": "Record creation timestamp"
            },
            {
                "name": "updated_at",
                "type": "timestamp",
                "default": "now()",
                "description": "Record update timestamp"
            }
        ],
        "indexes": [
            {
                "name": "idx_season_week",
                "columns": ["season", "week"]
            },
            {
                "name": "idx_game_date",
                "columns": ["game_date"]
            },
            {
                "name": "idx_teams",
                "columns": ["away_team", "home_team"]
            },
            {
                "name": "idx_network",
                "columns": ["network"]
            }
        ]
    }
    
    return schema

def generate_sql_create_table(schema: Dict[str, Any]) -> str:
    """Generate SQL CREATE TABLE statement for Supabase"""
    
    sql = f"CREATE TABLE {schema['table_name']} (\n"
    
    column_definitions = []
    for col in schema['columns']:
        col_def = f"  {col['name']} {col['type']}"
        
        if col.get('primary_key'):
            col_def += " PRIMARY KEY"
        
        if col.get('default'):
            col_def += f" DEFAULT {col['default']}"
            
        column_definitions.append(col_def)
    
    sql += ",\n".join(column_definitions)
    sql += "\n);\n\n"
    
    # Add indexes
    for idx in schema['indexes']:
        sql += f"CREATE INDEX {idx['name']} ON {schema['table_name']} ({', '.join(idx['columns'])});\n"
    
    return sql

def generate_insert_statements(games: List[Dict[str, Any]]) -> str:
    """Generate SQL INSERT statements for the games data"""
    
    if not games:
        return ""
    
    # Get column names from first game
    columns = list(games[0].keys())
    
    sql = f"INSERT INTO nfl_games_2025 ({', '.join(columns)}) VALUES\n"
    
    value_rows = []
    for game in games:
        values = []
        for col in columns:
            value = game[col]
            if value is None:
                values.append("NULL")
            elif isinstance(value, str):
                values.append(f"'{value}'")
            elif isinstance(value, bool):
                values.append("TRUE" if value else "FALSE")
            else:
                values.append(str(value))
        
        value_rows.append(f"  ({', '.join(values)})")
    
    sql += ",\n".join(value_rows)
    sql += ";\n"
    
    return sql

def main():
    """Main function to process NFL schedule data"""
    
    print("Processing NFL 2025 Schedule Data for Supabase...")
    
    # Parse schedule data
    games = parse_schedule_data()
    print(f"Processed {len(games)} games")
    
    # Create schema
    schema = create_supabase_schema()
    
    # Generate SQL
    create_sql = generate_sql_create_table(schema)
    insert_sql = generate_insert_statements(games)
    
    # Save to files
    with open('/home/ubuntu/nfl_schedule_schema.sql', 'w') as f:
        f.write(create_sql)
    
    with open('/home/ubuntu/nfl_schedule_data.sql', 'w') as f:
        f.write(insert_sql)
    
    # Save JSON format
    with open('/home/ubuntu/nfl_schedule_2025.json', 'w') as f:
        json.dump({
            "schema": schema,
            "games": games,
            "metadata": {
                "total_games": len(games),
                "season": 2025,
                "generated_at": datetime.now().isoformat()
            }
        }, f, indent=2)
    
    print("Files generated:")
    print("- nfl_schedule_schema.sql (Supabase table schema)")
    print("- nfl_schedule_data.sql (INSERT statements)")
    print("- nfl_schedule_2025.json (JSON format)")

if __name__ == "__main__":
    main()

