#!/usr/bin/env python3
"""
Analyze which teams are missing from the nfl_teams table
"""

import csv
import os
from collections import Counter

def analyze_teams():
    csv_path = "/home/iris/code/experimental/nfl-predictor-api/data/historical/games/games.csv"
    
    all_teams = set()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            home_team = row.get('home_team', '').strip()
            away_team = row.get('away_team', '').strip()
            
            if home_team:
                all_teams.add(home_team)
            if away_team:
                all_teams.add(away_team)
    
    print(f"📊 Found {len(all_teams)} unique teams in CSV:")
    for team in sorted(all_teams):
        print(f"   {team}")
    
    # Teams that exist in database (32 found earlier)
    database_teams = [
        'ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE',
        'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
        'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG',
        'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS'
    ]
    
    missing_teams = all_teams - set(database_teams)
    if missing_teams:
        print(f"\n❌ Missing teams from database ({len(missing_teams)}):")
        for team in sorted(missing_teams):
            print(f"   {team}")
    else:
        print("\n✅ All teams exist in database!")

if __name__ == "__main__":
    analyze_teams()