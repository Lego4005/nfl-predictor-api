#!/usr/bin/env python3
"""
NFL Data Loader for Training Loop

Transforms NFL database records into game contexts for expert prediction generation.
Handles chronological ordering, data validation, and missing field handling.
"""

import sys
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio
sys.path.append('src')

from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GameContext:
    """Standardized game context for expert prediction generation"""
    game_id: str
    home_team: str
    away_team: str
    season: int
    week: int
    game_date: date
    game_datetime: Optional[datetime] = None

    # Weather conditions
    weather: Optional[Dict[str, Any]] = None

    # Betting lines
    spread_line: Optional[float] = None
    total_line: Optional[float] = None
    home_moneyline: Optional[int] = None
    away_moneyline: Optional[int] = None

    # Team preparation
    home_rest: Optional[int] = None
    away_rest: Optional[int] = None

    # Game characteristics
    division_game: bool = False
    stadium: Optional[str] = None
    surface: Optional[str] = None
    roof: Optional[str] = None

    # Coaching
    home_coach: Optional[str] = None
    away_coach: Optional[str] = None

    # Quarterbacks
    home_qb: Optional[str] = None
    away_qb: Optional[str] = None

    # Actual results (for post-game analysis)
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    overtime: bool = False

    # Additional metadata
    raw_data: Optional[Dict[str, Any]] = None

@dataclass
class SeasonGameSet:
    """Collection of games for a season with metadata"""
    season: int
    games: List[GameContext]
    total_games: int
    completed_games: int
    date_range: Tuple[date, date]

class NFLDataLoader:
    """Loads and transforms NFL game data for training loop"""

    def __init__(self):
        """Initialize with Supabase connection"""
        self.supabase_url = os.getenv('VITE_SUPABASE_URL')
        self.supabase_key = os.getenv('VITE_SUPABASE_ANON_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing Supabase credentials in environment variables")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("✅ NFL Data Loader initialized with Supabase connection")

    async def validate_connection(self) -> bool:
        """Validate database connection and table existence"""
        try:
            # Test connection with simple query
            response = self.supabase.table('nfl_games').select('game_id').limit(1).execute()
            logger.info("✅ Database connection validated")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    def load_season_games(self, season: int, completed_only: bool = True) -> SeasonGameSet:
        """Load all games for a season in chronological order"""
        try:
            logger.info(f"📊 Loading {season} season games...")

            # Build query
            query = self.supabase.table('nfl_games').select('*').eq('season', season)

            # Filter for completed games if requested
            if completed_only:
                query = query.not_.is_('home_score', 'null').not_.is_('away_score', 'null')

            # Order chronologically (critical for training loop)
            query = query.order('game_date', desc=False).order('game_datetime', desc=False)

            response = query.execute()

            if not response.data:
                logger.warning(f"⚠️ No games found for {season} season")
                return SeasonGameSet(season=season, games=[], total_games=0, completed_games=0,
                                   date_range=(date.min, date.min))

            # Transform to GameContext objects
            games = []
            for game_data in response.data:
                try:
                    game_context = self._transform_to_game_context(game_data)
                    games.append(game_context)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to transform game {game_data.get('game_id', 'unknown')}: {e}")
                    continue

            # Calculate metadata
            total_games = len(games)
            completed_games = len([g for g in games if g.home_score is not None and g.away_score is not None])

            if games:
                date_range = (games[0].game_date, games[-1].game_date)
            else:
                date_range = (date.min, date.min)

            logger.info(f"✅ Loaded {total_games} games for {season} season ({completed_games} completed)")

            return SeasonGameSet(
                season=season,
                games=games,
                total_games=total_games,
                completed_games=completed_games,
                date_range=date_range
            )

        except Exception as e:
            logger.error(f"❌ Failed to load {season} season: {e}")
            raise

    def _transform_to_game_context(self, game_data: Dict[str, Any]) -> GameContext:
        """Transform database record to GameContext"""
        try:
            # Required fields
            game_id = game_data['game_id']
            home_team = game_data['home_team']
            away_team = game_data['away_team']
            season = game_data['season']
            week = game_data['week']

            # Parse game date
            game_date_str = game_data.get('game_date')
            if isinstance(game_date_str, str):
                game_date = datetime.strptime(game_date_str, '%Y-%m-%d').date()
            elif isinstance(game_date_str, date):
                game_date = game_date_str
            else:
                raise ValueError(f"Invalid game_date format: {game_date_str}")

            # Parse game datetime if available
            game_datetime = None
            if game_data.get('game_datetime'):
                try:
                    if isinstance(game_data['game_datetime'], str):
                        game_datetime = datetime.fromisoformat(game_data['game_datetime'].replace('Z', '+00:00'))
                    elif isinstance(game_data['game_datetime'], datetime):
                        game_datetime = game_data['game_datetime']
                except Exception as e:
                    logger.warning(f"Failed to parse game_datetime for {game_id}: {e}")

            # Weather conditions
            weather = None
            if game_data.get('weather_temperature') is not None or game_data.get('weather_wind_mph') is not None:
                weather = {
                    'temperature': game_data.get('weather_temperature'),
                    'wind_speed': game_data.get('weather_wind_mph'),
                    'conditions': 'unknown'
                }

            # Create GameContext
            return GameContext(
                game_id=game_id,
                home_team=home_team,
                away_team=away_team,
                season=season,
                week=week,
                game_date=game_date,
                game_datetime=game_datetime,
                weather=weather,
                spread_line=self._safe_float(game_data.get('spread_line')),
                total_line=self._safe_float(game_data.get('total_line')),
                home_moneyline=self._safe_int(game_data.get('home_moneyline')),
                away_moneyline=self._safe_int(game_data.get('away_moneyline')),
                home_rest=self._safe_int(game_data.get('home_rest')),
                away_rest=self._safe_int(game_data.get('away_rest')),
                division_game=bool(game_data.get('div_game', False)),
                stadium=game_data.get('stadium'),
                surface=game_data.get('surface'),
                roof=game_data.get('roof'),
                home_coach=game_data.get('home_coach'),
                away_coach=game_data.get('away_coach'),
                home_qb=game_data.get('home_qb_name'),
                away_qb=game_data.get('away_qb_name'),
                home_score=self._safe_int(game_data.get('home_score')),
                away_score=self._safe_int(game_data.get('away_score')),
                overtime=bool(game_data.get('overtime', False)),
                raw_data=game_data
            )

        except Exception as e:
            logger.error(f"❌ Failed to transform game data: {e}")
            raise

    def _safe_int(self, value: Any) -> Optional[int]:
        """Safely convert value to int"""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None


async def main():
    """Test the NFL Data Loader"""

    print("🏈 NFL Data Loader Test")
    print("=" * 50)

    # Initialize loader
    loader = NFLDataLoader()

    # Validate connection
    if not await loader.validate_connection():
        print("❌ Database connection failed")
        return

    # Test loading 2020 season
    print("\n📊 Testing 2020 Season Load...")
    season_2020 = loader.load_season_games(2020)
    print(f"Season 2020: {season_2020.total_games} total, {season_2020.completed_games} completed")
    print(f"Date range: {season_2020.date_range[0]} to {season_2020.date_range[1]}")

    if season_2020.games:
        # Show first few games
        print("\n📋 First 3 games:")
        for i, game in enumerate(season_2020.games[:3]):
            print(f"  {i+1}. {game.game_date} - {game.away_team} @ {game.home_team} (Week {game.week})")
            if game.weather:
                print(f"     Weather: {game.weather}")
            if game.spread_line:
                print(f"     Spread: {game.spread_line}")

    print("\n✅ NFL Data Loader test complete!")


if __name__ == "__main__":
    asyncio.run(main())
