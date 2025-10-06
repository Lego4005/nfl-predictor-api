#!/usr/bin/env python3
"""
Prefetch Weather Data Slowly

Fetches weather for all unique stadiums in Weeks 1-4, respecting rate limits:
- Tomorrow.io: 25 calls/hour
- Adds 3-minute delays between calls
- Caches results in database for reuse
- Takes ~2 hours for 32 stadiums
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from supabase import create_client, Client
from dotenv import load_dotenv
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.services.tomorrow_weather_service import TomorrowWeatherService

load_dotenv()

# Supabase client
SUPABASE_URL = os.getenv('VITE_SUPABASE_URL')
SUPABASE_KEY = os.getenv('VITE_SUPABASE_ANON_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


async def get_unique_home_teams():
    """Get all unique home teams from Weeks 1-4"""
    response = supabase.table('games') \
        .select('home_team, game_time, id') \
        .eq('season', 2025) \
        .in_('week', [1, 2, 3, 4]) \
        .order('game_time') \
        .execute()

    # Get unique home teams with their first game time
    teams_with_times = {}
    for game in response.data:
        team = game['home_team']
        if team not in teams_with_times:
            teams_with_times[team] = {
                'game_time': game['game_time'],
                'game_id': game['id']
            }

    return teams_with_times


async def prefetch_weather_slow():
    """Slowly fetch weather for all unique stadiums"""

    print("=" * 90)
    print("☁️  WEATHER PREFETCH - SLOW MODE")
    print("=" * 90)
    print("\n📊 Rate Limiting:")
    print("   • Tomorrow.io free tier: 25 calls/hour")
    print("   • Delay: 180 seconds (3 minutes) between calls")
    print("   • Estimated time: ~2 hours for 32 stadiums")
    print("   • Results cached in database for reuse\n")

    # Initialize weather service
    weather_service = TomorrowWeatherService(supabase_client=supabase)

    # Get unique home teams
    teams_with_times = await get_unique_home_teams()
    unique_teams = list(teams_with_times.keys())

    print(f"✅ Found {len(unique_teams)} unique home stadiums")
    print(f"✅ Initialized Tomorrow.io weather service\n")

    print("=" * 90)
    print("FETCHING WEATHER DATA")
    print("=" * 90)

    success_count = 0
    skip_count = 0
    error_count = 0

    for i, team in enumerate(unique_teams, 1):
        game_info = teams_with_times[team]
        game_time_str = game_info['game_time']
        game_id = game_info['game_id']

        # Parse game time
        if 'T' in game_time_str:
            game_time = datetime.fromisoformat(game_time_str.replace('Z', '+00:00'))
        else:
            game_time = datetime.fromisoformat(game_time_str)
            if game_time.tzinfo is None:
                game_time = game_time.replace(tzinfo=timezone.utc)

        print(f"\n[{i}/{len(unique_teams)}] {team}")
        print(f"   Game: {game_id[:8]}...")
        print(f"   Time: {game_time_str[:16]}")

        try:
            # Check if already cached in database
            existing = supabase.table('weather_data') \
                .select('*') \
                .eq('game_id', game_id) \
                .execute()

            if existing.data and len(existing.data) > 0:
                weather = existing.data[0]
                print(f"   ✅ CACHED: {weather.get('temperature', 'N/A')}°F, {weather.get('conditions', 'N/A')}")
                skip_count += 1
                continue

            # Fetch weather
            weather_data = await weather_service.get_game_weather(
                game_id=game_id,
                home_team=team,
                game_time=game_time
            )

            if weather_data:
                # Store in database
                weather_dict = weather_data.model_dump()

                supabase.table('weather_data').insert({
                    'game_id': game_id,
                    'temperature': weather_dict.get('temperature'),
                    'wind_speed': weather_dict.get('wind_speed'),
                    'wind_direction': weather_dict.get('wind_direction'),
                    'precipitation': weather_dict.get('precipitation'),
                    'humidity': weather_dict.get('humidity'),
                    'conditions': weather_dict.get('conditions'),
                    'field_conditions': weather_dict.get('field_conditions'),
                    'dome_stadium': weather_dict.get('dome_stadium', False),
                    'forecast_confidence': weather_dict.get('forecast_confidence', 0.0),
                    'data_source': 'Tomorrow.io',
                    'fetched_at': datetime.now(timezone.utc).isoformat(),
                    'game_time': game_time.isoformat() if game_time else None,
                    'hours_before_game': weather_dict.get('hours_before_game')
                }).execute()

                if weather_data.dome_stadium:
                    print(f"   ✅ DOME: 72.0°F Indoor")
                else:
                    print(f"   ✅ FETCHED: {weather_data.temperature}°F, {weather_data.wind_speed}mph, {weather_data.conditions}")

                success_count += 1

                # Rate limiting: wait 3 minutes between API calls (not for dome stadiums)
                if not weather_data.dome_stadium and i < len(unique_teams):
                    print(f"   ⏳ Waiting 180 seconds to respect rate limit...")
                    await asyncio.sleep(180)
            else:
                print(f"   ⚠️  No weather data returned")
                error_count += 1

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            error_count += 1

            # If rate limited, wait longer
            if "429" in str(e) or "Too Many" in str(e):
                print(f"   ⏳ Rate limited! Waiting 1 hour...")
                await asyncio.sleep(3600)

    # Summary
    print("\n" + "=" * 90)
    print("📊 WEATHER PREFETCH COMPLETE")
    print("=" * 90)
    print(f"\n✅ Successfully fetched: {success_count}")
    print(f"♻️  Already cached: {skip_count}")
    print(f"❌ Errors: {error_count}")
    print(f"\nTotal stadiums processed: {len(unique_teams)}")
    print("\n💾 All weather data cached in database for training runs!")
    print("=" * 90)


if __name__ == "__main__":
    asyncio.run(prefetch_weather_slow())