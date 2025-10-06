#!/usr/bin/env python3
"""
Fetch actual 2025 game IDs from Supabase database
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL', 'https://vaypgzvivahnfegnlinn.supabase.co')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')

if not SUPABASE_KEY:
    print("❌ Error: VITE_SUPABASE_ANON_KEY not found in .env")
    sys.exit(1)

# Create client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_2025_games(weeks=[1, 2, 3, 4]):
    """Get all game IDs from Supabase for 2025 season"""

    try:
        # Query games table
        response = supabase.table('games') \
            .select('id, season, week, home_team, away_team, game_time, status') \
            .eq('season', 2025) \
            .in_('week', weeks) \
            .order('week') \
            .order('game_time') \
            .execute()

        games = response.data

        if not games:
            print("⚠️  No games found in database for 2025 season")
            return []

        print(f"✅ Found {len(games)} games in 2025 Weeks {weeks}")
        print()

        # Group by week
        by_week = {}
        for game in games:
            week = game['week']
            if week not in by_week:
                by_week[week] = []
            by_week[week].append(game)

        # Display and collect game IDs
        all_game_ids = []

        for week in sorted(by_week.keys()):
            week_games = by_week[week]
            print(f"📅 Week {week}: {len(week_games)} games")

            for game in week_games:
                game_id = game['id']
                away = game['away_team']
                home = game['home_team']
                status = game['status']
                game_time = game['game_time'][:10] if game['game_time'] else 'TBD'

                all_game_ids.append(game_id)
                print(f"   {game_id:<20} {away} @ {home:<3} ({status}, {game_time})")

            print()

        print(f"📊 Total: {len(all_game_ids)} game IDs")
        print()
        print("Python list format:")
        print("game_ids = [")
        for game_id in all_game_ids:
            print(f"    '{game_id}',")
        print("]")

        return all_game_ids

    except Exception as e:
        print(f"❌ Error fetching games: {e}")
        return []


if __name__ == "__main__":
    get_2025_games([1, 2, 3, 4])