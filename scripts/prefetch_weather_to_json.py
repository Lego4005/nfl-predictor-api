#!/usr/bin/env python3
"""
Prefetch Weather Data to JSON File

Fetches weather for all unique stadiums and saves to JSON:
- Tomorrow.io: 25 calls/hour
- 3-minute delays between calls
- Saves to weather_cache.json for reuse
- Much simpler than database storage
"""

import asyncio
import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.tomorrow_weather_service import TomorrowWeatherService

load_dotenv()

SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

CACHE_FILE = Path(__file__).parent.parent / "weather_cache.json"


async def get_unique_home_teams():
    """Get all unique home teams from Weeks 1-4"""
    response = supabase.table('games') \
        .select('home_team, game_time, id, week') \
        .eq('season', 2025) \
        .in_('week', [1, 2, 3, 4]) \
        .order('game_time') \
        .execute()

    teams_with_games = {}
    for game in response.data:
        team = game['home_team']
        if team not in teams_with_games:
            teams_with_games[team] = []
        teams_with_games[team].append({
            'game_id': game['id'],
            'game_time': game['game_time'],
            'week': game['week']
        })

    return teams_with_games


async def prefetch_weather_to_json():
    """Slowly fetch weather and save to JSON"""

    print("=" * 90)
    print("☁️  WEATHER PREFETCH TO JSON")
    print("=" * 90)
    print(f"\n📁 Cache file: {CACHE_FILE}")
    print("\n📊 Rate Limiting:")
    print("   • Tomorrow.io: 25 calls/hour")
    print("   • Delay: 180 seconds between API calls")
    print("   • Dome stadiums: instant (no API call)\n")

    # Load existing cache
    weather_cache = {}
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            weather_cache = json.load(f)
        print(f"✅ Loaded {len(weather_cache)} cached weather entries\n")
    else:
        print("✅ Starting fresh weather cache\n")

    weather_service = TomorrowWeatherService()
    teams_with_games = await get_unique_home_teams()

    print(f"✅ Found {len(teams_with_games)} unique home teams")
    print(f"✅ Total games to process: {sum(len(games) for games in teams_with_games.values())}\n")

    print("=" * 90)
    print("FETCHING WEATHER DATA")
    print("=" * 90)

    success_count = 0
    skip_count = 0
    error_count = 0
    api_calls = 0

    for team_idx, (team, games) in enumerate(teams_with_games.items(), 1):
        print(f"\n[{team_idx}/{len(teams_with_games)}] {team} ({len(games)} games)")

        for game_idx, game_info in enumerate(games, 1):
            game_id = game_info['game_id']
            game_time_str = game_info['game_time']
            week = game_info['week']

            # Check cache first
            if game_id in weather_cache:
                cached = weather_cache[game_id]
                print(f"   [{game_idx}] Week {week} ✅ CACHED: {cached.get('temperature', 'N/A')}°F, {cached.get('conditions', 'N/A')}")
                skip_count += 1
                continue

            # Parse game time
            if 'T' in game_time_str:
                game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
            else:
                game_time = datetime.fromisoformat(game_time_str)
                if game_time.tzinfo is None:
                    game_time = game_time.replace(tzinfo=timezone.utc)

            print(f"   [{game_idx}] Week {week} @ {game_time_str[:16]}", end=" ")

            try:
                # Fetch weather
                weather_data = await weather_service.get_game_weather(
                    game_id=game_id,
                    home_team=team,
                    game_time=game_time
                )

                if weather_data:
                    # Convert to dict
                    weather_dict = {
                        'game_id': game_id,
                        'temperature': weather_data.temperature,
                        'wind_speed': weather_data.wind_speed,
                        'wind_direction': weather_data.wind_direction,
                        'precipitation': weather_data.precipitation,
                        'humidity': weather_data.humidity,
                        'conditions': weather_data.conditions,
                        'field_conditions': weather_data.field_conditions,
                        'dome_stadium': weather_data.dome_stadium,
                        'forecast_confidence': weather_data.forecast_confidence,
                        'data_source': 'Tomorrow.io',
                        'fetched_at': datetime.now(timezone.utc).isoformat(),
                        'game_time': game_time.isoformat(),
                        'hours_before_game': weather_data.hours_before_game,
                        'week': week,
                        'home_team': team
                    }

                    # Save to cache
                    weather_cache[game_id] = weather_dict

                    # Save file after each fetch
                    with open(CACHE_FILE, 'w') as f:
                        json.dump(weather_cache, f, indent=2)

                    if weather_data.dome_stadium:
                        print(f"→ ✅ DOME (72°F)")
                    else:
                        print(f"→ ✅ {weather_data.temperature}°F, {weather_data.wind_speed}mph, {weather_data.conditions}")
                        api_calls += 1

                    success_count += 1

                    # Rate limit: wait 3 minutes between API calls (not for domes)
                    if not weather_data.dome_stadium:
                        remaining = sum(len(g) for g in list(teams_with_games.values())[team_idx:]) + len(games) - game_idx
                        if remaining > 0:
                            print(f"      ⏳ Waiting 180s... ({api_calls} API calls so far, {remaining} games remaining)")
                            await asyncio.sleep(180)
                else:
                    print(f"→ ⚠️  No data")
                    error_count += 1

            except Exception as e:
                print(f"→ ❌ {str(e)[:50]}")
                error_count += 1

                if "429" in str(e):
                    print(f"      ⏳ Rate limited! Waiting 1 hour...")
                    await asyncio.sleep(3600)

    # Summary
    print("\n" + "=" * 90)
    print("📊 WEATHER PREFETCH COMPLETE")
    print("=" * 90)
    print(f"\n✅ Successfully fetched: {success_count}")
    print(f"♻️  Already cached: {skip_count}")
    print(f"❌ Errors: {error_count}")
    print(f"🌐 Total API calls made: {api_calls}")
    print(f"\n💾 Cache saved to: {CACHE_FILE}")
    print(f"📦 Total entries: {len(weather_cache)}")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(prefetch_weather_to_json())