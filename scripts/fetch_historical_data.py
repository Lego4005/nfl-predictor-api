"""
Historical NFL data fetcher for ML model training.
Downloads and processes 3+ seasons of NFL data from SportsData.io API.
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from dataclasses import dataclass
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GameData:
    """Container for game data from API"""
    game_info: Dict[str, Any]
    box_score: Dict[str, Any]
    team_stats: List[Dict[str, Any]]
    player_stats: List[Dict[str, Any]]
    weather: Optional[Dict[str, Any]]
    injuries: List[Dict[str, Any]]
    betting_data: Optional[Dict[str, Any]]

class HistoricalDataFetcher:
    """Fetches and processes historical NFL data for ML training"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('SPORTSDATA_API_KEY')
        if not self.api_key:
            raise ValueError("SportsData.io API key required. Set SPORTSDATA_API_KEY environment variable.")

        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.headers = {"Ocp-Apim-Subscription-Key": self.api_key}

        # Rate limiting
        self.request_delay = 1.1  # Slightly over 1 second to respect rate limits
        self.last_request_time = 0

        # Database connection
        self.db_type = os.getenv('DB_TYPE', 'sqlite')  # sqlite or postgresql
        self.db_connection = None

    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()

    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make API request with rate limiting and error handling"""
        self._rate_limit()

        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.get(url, headers=self.headers, params=params or {})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {e}")
            return None

    def get_seasons_to_fetch(self, num_seasons: int = 3) -> List[int]:
        """Get list of seasons to fetch (last N completed seasons)"""
        current_year = datetime.now().year
        current_month = datetime.now().month

        # If it's before February, current NFL season might not be complete
        if current_month < 2:
            current_year -= 1

        seasons = []
        for i in range(num_seasons):
            seasons.append(current_year - i)

        logger.info(f"Fetching data for seasons: {seasons}")
        return seasons

    def fetch_games_for_season(self, season: int) -> List[Dict]:
        """Fetch all games for a specific season"""
        logger.info(f"Fetching games for season {season}")

        # Get regular season games
        regular_games = self._make_request(f"scores/json/Scores/{season}") or []

        # Get playoff games
        playoff_games = self._make_request(f"scores/json/Scores/{season}POST") or []

        all_games = regular_games + playoff_games
        logger.info(f"Found {len(all_games)} games for season {season}")
        return all_games

    def fetch_box_score(self, season: int, week: int, game_key: str) -> Optional[Dict]:
        """Fetch detailed box score for a specific game"""
        endpoint = f"stats/json/BoxScore/{season}/{week}/{game_key}"
        return self._make_request(endpoint)

    def fetch_play_by_play(self, season: int, week: int, game_key: str) -> Optional[Dict]:
        """Fetch play-by-play data for a specific game"""
        endpoint = f"pbp/json/PlayByPlay/{season}/{week}/{game_key}"
        return self._make_request(endpoint)

    def fetch_team_season_stats(self, season: int) -> List[Dict]:
        """Fetch team statistics for entire season"""
        endpoint = f"stats/json/TeamSeasonStats/{season}"
        return self._make_request(endpoint) or []

    def fetch_player_season_stats(self, season: int) -> List[Dict]:
        """Fetch player statistics for entire season"""
        endpoint = f"stats/json/PlayerSeasonStats/{season}"
        return self._make_request(endpoint) or []

    def fetch_weather_data(self, season: int, week: int) -> List[Dict]:
        """Fetch weather data for games in a specific week"""
        endpoint = f"weather/json/Weather/{season}/{week}"
        return self._make_request(endpoint) or []

    def fetch_injury_reports(self, season: int, week: int) -> List[Dict]:
        """Fetch injury reports for a specific week"""
        endpoint = f"injuries/json/Injuries/{season}/{week}"
        return self._make_request(endpoint) or []

    def fetch_betting_data(self, season: int, week: int) -> List[Dict]:
        """Fetch betting lines and data for a specific week"""
        endpoint = f"odds/json/GameOdds/{season}/{week}"
        return self._make_request(endpoint) or []

    def fetch_comprehensive_game_data(self, game: Dict) -> GameData:
        """Fetch all available data for a single game"""
        season = game.get('Season')
        week = game.get('Week')
        game_key = game.get('GameKey')

        logger.info(f"Fetching comprehensive data for {game_key} (Season {season}, Week {week})")

        # Fetch all data types
        box_score = self.fetch_box_score(season, week, game_key) or {}
        play_by_play = self.fetch_play_by_play(season, week, game_key) or {}

        # Weather and injuries are by week, not individual game
        weather_data = self.fetch_weather_data(season, week) or []
        injury_data = self.fetch_injury_reports(season, week) or []
        betting_data = self.fetch_betting_data(season, week) or []

        # Find weather for this specific game
        game_weather = None
        for weather in weather_data:
            if weather.get('GameKey') == game_key:
                game_weather = weather
                break

        # Find betting data for this game
        game_betting = None
        for betting in betting_data:
            if betting.get('GameKey') == game_key:
                game_betting = betting
                break

        # Extract team and player stats from box score
        team_stats = []
        player_stats = []

        if box_score:
            if 'TeamStats' in box_score:
                team_stats = box_score['TeamStats']
            if 'PlayerStats' in box_score:
                player_stats = box_score['PlayerStats']

        return GameData(
            game_info=game,
            box_score=box_score,
            team_stats=team_stats,
            player_stats=player_stats,
            weather=game_weather,
            injuries=injury_data,
            betting_data=game_betting
        )

    def setup_database_connection(self):
        """Setup database connection based on configuration"""
        if self.db_type.lower() == 'postgresql':
            try:
                self.db_connection = psycopg2.connect(
                    host=os.getenv('DB_HOST', 'localhost'),
                    port=os.getenv('DB_PORT', 5432),
                    database=os.getenv('DB_NAME', 'nfl_predictor'),
                    user=os.getenv('DB_USER', 'postgres'),
                    password=os.getenv('DB_PASSWORD', '')
                )
                logger.info("Connected to PostgreSQL database")
            except psycopg2.Error as e:
                logger.error(f"PostgreSQL connection failed: {e}")
                raise
        else:
            # SQLite for development
            db_path = os.getenv('DB_PATH', 'data/nfl_historical.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            self.db_connection = sqlite3.connect(db_path)
            logger.info(f"Connected to SQLite database at {db_path}")

    def save_raw_data(self, season: int, game_data: GameData, output_dir: str = "data/raw"):
        """Save raw JSON data for backup and debugging"""
        os.makedirs(output_dir, exist_ok=True)

        game_key = game_data.game_info.get('GameKey', 'unknown')
        filename = f"{output_dir}/{season}_{game_key}_raw.json"

        raw_data = {
            'game_info': game_data.game_info,
            'box_score': game_data.box_score,
            'team_stats': game_data.team_stats,
            'player_stats': game_data.player_stats,
            'weather': game_data.weather,
            'injuries': game_data.injuries,
            'betting_data': game_data.betting_data,
            'fetched_at': datetime.now().isoformat()
        }

        with open(filename, 'w') as f:
            json.dump(raw_data, f, indent=2, default=str)

    def fetch_all_historical_data(self, seasons: List[int] = None, save_raw: bool = True) -> List[GameData]:
        """Main method to fetch all historical data"""
        if seasons is None:
            seasons = self.get_seasons_to_fetch()

        all_game_data = []

        for season in seasons:
            logger.info(f"Processing season {season}")

            # Get all games for the season
            games = self.fetch_games_for_season(season)

            for i, game in enumerate(games):
                try:
                    logger.info(f"Processing game {i+1}/{len(games)} for season {season}")
                    game_data = self.fetch_comprehensive_game_data(game)

                    if save_raw:
                        self.save_raw_data(season, game_data)

                    all_game_data.append(game_data)

                    # Progress logging
                    if (i + 1) % 10 == 0:
                        logger.info(f"Completed {i+1}/{len(games)} games for season {season}")

                except Exception as e:
                    logger.error(f"Error processing game {game.get('GameKey', 'unknown')}: {e}")
                    continue

        logger.info(f"Fetched data for {len(all_game_data)} games across {len(seasons)} seasons")
        return all_game_data

def main():
    """Main execution function"""
    try:
        # Initialize fetcher
        fetcher = HistoricalDataFetcher()

        # Fetch historical data
        logger.info("Starting historical data fetch...")
        historical_data = fetcher.fetch_all_historical_data()

        logger.info(f"Successfully fetched {len(historical_data)} games of historical data")
        logger.info("Raw data saved to data/raw/ directory")
        logger.info("Run populate_database.py to process and store in database")

    except Exception as e:
        logger.error(f"Historical data fetch failed: {e}")
        raise

if __name__ == "__main__":
    main()