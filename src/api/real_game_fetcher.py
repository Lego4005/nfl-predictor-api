"""
Real Game Data Fetcher
Fetches actual NFL game data from SportsData.io for the prediction system.
Provides current week's games with proper formatting for expert predictions.
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class NFLGame:
    """NFL Game data structure"""
    game_id: str
    home_team: str
    away_team: str
    game_time: datetime
    week: int
    season: int
    spread: Optional[float] = None
    total: Optional[float] = None
    status: str = "Scheduled"
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    weather: Optional[Dict[str, Any]] = None
    stadium: Optional[str] = None
    is_dome: bool = False
    is_divisional: bool = False
    is_primetime: bool = False

class RealGameDataFetcher:
    """Fetches real NFL game data from SportsData.io"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('SPORTSDATA_IO_KEY') or os.getenv('VITE_SPORTSDATA_IO_KEY', '')
        self.base_url = "https://api.sportsdata.io/v3/nfl"
        self.headers = {
            "Ocp-Apim-Subscription-Key": self.api_key,
            "User-Agent": "NFL-Predictor/1.0"
        }

        if not self.api_key:
            logger.warning("No SportsData.io API key provided. Using fallback mock data.")

    async def get_current_week_games(self, season: Optional[int] = None, week: Optional[int] = None) -> List[NFLGame]:
        """Get games for current NFL week"""
        if season is None:
            season = self._get_current_season()
        if week is None:
            week = self._get_current_week()

        logger.info(f"Fetching games for {season} Week {week}")

        if not self.api_key:
            logger.warning("No API key available, returning mock games")
            return self._get_fallback_games(season, week)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                # Fetch scores/schedule
                url = f"{self.base_url}/scores/{season}/{week}"

                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        games_data = await response.json()
                        games = await self._process_games_data(games_data, season, week)
                        logger.info(f"Successfully fetched {len(games)} games")
                        return games
                    else:
                        logger.error(f"API request failed: {response.status}")
                        return self._get_fallback_games(season, week)

        except asyncio.TimeoutError:
            logger.error("API request timeout")
            return self._get_fallback_games(season, week)
        except Exception as e:
            logger.error(f"Error fetching games: {e}")
            return self._get_fallback_games(season, week)

    async def get_game_details(self, game_id: str) -> Dict[str, Any]:
        """Get detailed data for a specific game"""
        logger.info(f"Fetching details for game {game_id}")

        if not self.api_key:
            return self._get_fallback_game_details(game_id)

        try:
            # Find the game in current week
            current_games = await self.get_current_week_games()
            game = next((g for g in current_games if g.game_id == game_id), None)

            if not game:
                logger.warning(f"Game {game_id} not found in current games")
                return self._get_fallback_game_details(game_id)

            # Fetch additional details
            game_data = await self._enrich_game_data(game)
            return game_data

        except Exception as e:
            logger.error(f"Error fetching game details: {e}")
            return self._get_fallback_game_details(game_id)

    async def get_team_statistics(self, team: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Get team statistics for the season"""
        if season is None:
            season = self._get_current_season()

        logger.info(f"Fetching stats for {team} in {season}")

        if not self.api_key:
            return self._get_fallback_team_stats(team)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                url = f"{self.base_url}/teamstats/{season}"

                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        teams_data = await response.json()
                        team_stats = next((t for t in teams_data if t.get('Team') == team), {})
                        return self._process_team_stats(team_stats, team)
                    else:
                        logger.error(f"Failed to fetch team stats: {response.status}")
                        return self._get_fallback_team_stats(team)

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return self._get_fallback_team_stats(team)

    async def get_player_statistics(self, team: str, season: Optional[int] = None) -> Dict[str, Any]:
        """Get player statistics for a team"""
        if season is None:
            season = self._get_current_season()

        logger.info(f"Fetching player stats for {team} in {season}")

        if not self.api_key:
            return self._get_fallback_player_stats(team)

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                # Get passing stats
                passing_url = f"{self.base_url}/playerstats/{season}"

                async with session.get(passing_url, headers=self.headers) as response:
                    if response.status == 200:
                        players_data = await response.json()
                        team_players = [p for p in players_data if p.get('Team') == team]
                        return self._process_player_stats(team_players, team)
                    else:
                        logger.error(f"Failed to fetch player stats: {response.status}")
                        return self._get_fallback_player_stats(team)

        except Exception as e:
            logger.error(f"Error fetching player stats: {e}")
            return self._get_fallback_player_stats(team)

    async def _process_games_data(self, games_data: List[Dict], season: int, week: int) -> List[NFLGame]:
        """Process raw games data from API"""
        games = []

        for game_data in games_data:
            try:
                # Parse game time
                game_time = datetime.now() + timedelta(days=1)  # Default
                if game_data.get('DateTime'):
                    try:
                        game_time = datetime.fromisoformat(
                            game_data['DateTime'].replace('Z', '+00:00')
                        )
                    except:
                        pass

                # Extract teams
                home_team = game_data.get('HomeTeam', 'HOU')
                away_team = game_data.get('AwayTeam', 'DAL')

                # Create game object
                game = NFLGame(
                    game_id=str(game_data.get('GameID', f"{away_team}@{home_team}")),
                    home_team=home_team,
                    away_team=away_team,
                    game_time=game_time,
                    week=week,
                    season=season,
                    spread=game_data.get('PointSpread'),
                    total=game_data.get('OverUnder'),
                    status=game_data.get('Status', 'Scheduled'),
                    home_score=game_data.get('HomeScore'),
                    away_score=game_data.get('AwayScore'),
                    stadium=game_data.get('StadiumDetails', {}).get('Name') if game_data.get('StadiumDetails') else None,
                    is_dome=game_data.get('StadiumDetails', {}).get('Type') == 'Dome' if game_data.get('StadiumDetails') else False,
                    is_divisional=self._is_divisional_game(home_team, away_team),
                    is_primetime=self._is_primetime_game(game_time)
                )

                games.append(game)

            except Exception as e:
                logger.error(f"Error processing game data: {e}")
                continue

        return games

    async def _enrich_game_data(self, game: NFLGame) -> Dict[str, Any]:
        """Enrich game with additional data for predictions"""
        # Get team statistics
        home_stats = await self.get_team_statistics(game.home_team, game.season)
        away_stats = await self.get_team_statistics(game.away_team, game.season)

        # Get player statistics
        home_players = await self.get_player_statistics(game.home_team, game.season)
        away_players = await self.get_player_statistics(game.away_team, game.season)

        # Build comprehensive game data
        return {
            "game_id": game.game_id,
            "home_team": game.home_team,
            "away_team": game.away_team,
            "spread": game.spread or -2.5,
            "total": game.total or 45.5,
            "game_time": game.game_time,
            "season": game.season,
            "week": game.week,
            "weather": self._get_weather_data(game),
            "injuries": self._get_injury_data(game),
            "is_dome": game.is_dome,
            "is_divisional": game.is_divisional,
            "is_primetime": game.is_primetime,
            "home_epa_per_play": home_stats.get("epa_per_play", 0.05),
            "away_epa_per_play": away_stats.get("epa_per_play", 0.04),
            "line_movement": 0.0,  # Would need betting data
            "public_betting_percentage": 60,  # Would need betting data
            "home_stats": home_stats,
            "away_stats": away_stats,
            "home_players": home_players,
            "away_players": away_players
        }

    def _process_team_stats(self, team_data: Dict, team: str) -> Dict[str, Any]:
        """Process team statistics into useful format"""
        if not team_data:
            return self._get_fallback_team_stats(team)

        return {
            "team": team,
            "avg_points": team_data.get("PointsPerGame", 21.0),
            "points_per_game": team_data.get("PointsPerGame", 21.0),
            "points_allowed": team_data.get("OpponentPointsPerGame", 22.0),
            "total_yards_per_game": team_data.get("YardsPerGame", 340.0),
            "passing_yards_per_game": team_data.get("PassingYardsPerGame", 230.0),
            "rushing_yards_per_game": team_data.get("RushingYardsPerGame", 110.0),
            "yards_allowed_per_game": team_data.get("OpponentYardsPerGame", 350.0),
            "turnover_differential": team_data.get("TurnoverDifferential", 0),
            "red_zone_percentage": team_data.get("RedZonePercentage", 0.58),
            "third_down_percentage": team_data.get("ThirdDownPercentage", 0.40),
            "recent_record": "2-1",  # Would need game-by-game data
            "epa_per_play": 0.05,  # Would need advanced stats
            "record": f"{team_data.get('Wins', 8)}-{team_data.get('Losses', 8)}"
        }

    def _process_player_stats(self, players_data: List[Dict], team: str) -> Dict[str, Any]:
        """Process player statistics into useful format"""
        if not players_data:
            return self._get_fallback_player_stats(team)

        # Find QB1 (highest passing yards)
        qbs = [p for p in players_data if p.get('Position') == 'QB' and p.get('PassingYards', 0) > 100]
        qb1 = max(qbs, key=lambda x: x.get('PassingYards', 0)) if qbs else {}

        # Find RB1 (highest rushing yards)
        rbs = [p for p in players_data if p.get('Position') == 'RB' and p.get('RushingYards', 0) > 50]
        rb1 = max(rbs, key=lambda x: x.get('RushingYards', 0)) if rbs else {}

        # Find WR1 (highest receiving yards)
        wrs = [p for p in players_data if p.get('Position') in ['WR', 'TE'] and p.get('ReceivingYards', 0) > 100]
        wr1 = max(wrs, key=lambda x: x.get('ReceivingYards', 0)) if wrs else {}

        return {
            "qb1": {
                "name": qb1.get('Name', 'Unknown QB'),
                "yards_per_game": qb1.get('PassingYardsPerGame', 250),
                "touchdowns_per_game": qb1.get('PassingTouchdownsPerGame', 1.5),
                "interceptions_per_game": qb1.get('InterceptionsPerGame', 0.8),
                "completion_percentage": qb1.get('CompletionPercentage', 0.65),
                "rating": qb1.get('PasserRating', 95.0)
            },
            "rb1": {
                "name": rb1.get('Name', 'Unknown RB'),
                "yards_per_game": rb1.get('RushingYardsPerGame', 75),
                "attempts_per_game": rb1.get('RushingAttemptsPerGame', 18),
                "touchdowns_per_game": rb1.get('RushingTouchdownsPerGame', 0.6),
                "receptions_per_game": rb1.get('ReceptionsPerGame', 3.5)
            },
            "wr1": {
                "name": wr1.get('Name', 'Unknown WR'),
                "yards_per_game": wr1.get('ReceivingYardsPerGame', 80),
                "receptions_per_game": wr1.get('ReceptionsPerGame', 6.0),
                "targets_per_game": wr1.get('TargetsPerGame', 9.0),
                "touchdowns_per_game": wr1.get('ReceivingTouchdownsPerGame', 0.5)
            }
        }

    def _get_weather_data(self, game: NFLGame) -> Dict[str, Any]:
        """Get weather data for game (simplified)"""
        if game.is_dome:
            return {
                "temperature": 72,
                "wind_speed": 0,
                "precipitation": 0.0,
                "condition": "Dome"
            }

        # Default outdoor weather
        return {
            "temperature": 55,
            "wind_speed": 8,
            "precipitation": 0.0,
            "condition": "Clear"
        }

    def _get_injury_data(self, game: NFLGame) -> Dict[str, List]:
        """Get injury data for teams (placeholder)"""
        return {
            "home": [],
            "away": []
        }

    def _is_divisional_game(self, home_team: str, away_team: str) -> bool:
        """Check if game is within same division"""
        divisions = {
            "AFC East": ["BUF", "MIA", "NE", "NYJ"],
            "AFC North": ["BAL", "CIN", "CLE", "PIT"],
            "AFC South": ["HOU", "IND", "JAX", "TEN"],
            "AFC West": ["DEN", "KC", "LV", "LAC"],
            "NFC East": ["DAL", "NYG", "PHI", "WAS"],
            "NFC North": ["CHI", "DET", "GB", "MIN"],
            "NFC South": ["ATL", "CAR", "NO", "TB"],
            "NFC West": ["ARI", "LAR", "SF", "SEA"]
        }

        for division_teams in divisions.values():
            if home_team in division_teams and away_team in division_teams:
                return True
        return False

    def _is_primetime_game(self, game_time: datetime) -> bool:
        """Check if game is primetime (SNF, MNF, TNF)"""
        hour = game_time.hour
        weekday = game_time.weekday()

        # Sunday Night Football (SNF) - Sunday after 8 PM ET
        if weekday == 6 and hour >= 20:  # Sunday
            return True

        # Monday Night Football (MNF) - Monday after 8 PM ET
        if weekday == 0 and hour >= 20:  # Monday
            return True

        # Thursday Night Football (TNF) - Thursday after 8 PM ET
        if weekday == 3 and hour >= 20:  # Thursday
            return True

        return False

    def _get_current_season(self) -> int:
        """Get current NFL season"""
        now = datetime.now()
        if now.month >= 9:  # September or later
            return now.year
        else:
            return now.year - 1

    def _get_current_week(self) -> int:
        """Get current NFL week"""
        # Simplified - in production would calculate based on season schedule
        now = datetime.now()
        if now.month == 12 and now.day > 25:
            return 17  # Week 17
        elif now.month == 1 and now.day < 10:
            return 18  # Week 18
        else:
            return 15  # Default mid-season

    # Fallback methods for when API is unavailable
    def _get_fallback_games(self, season: int, week: int) -> List[NFLGame]:
        """Return mock games when API is unavailable"""
        logger.info(f"Using fallback mock games for {season} Week {week}")

        games = [
            NFLGame(
                game_id="KC@BUF",
                home_team="BUF",
                away_team="KC",
                game_time=datetime.now() + timedelta(hours=2),
                week=week,
                season=season,
                spread=-2.5,
                total=54.5,
                is_divisional=False,
                is_primetime=True
            ),
            NFLGame(
                game_id="DAL@NYG",
                home_team="NYG",
                away_team="DAL",
                game_time=datetime.now() + timedelta(hours=5),
                week=week,
                season=season,
                spread=6.5,
                total=48.5,
                is_divisional=True,
                is_primetime=False
            ),
            NFLGame(
                game_id="GB@CHI",
                home_team="CHI",
                away_team="GB",
                game_time=datetime.now() + timedelta(hours=8),
                week=week,
                season=season,
                spread=-1.5,
                total=42.5,
                is_divisional=True,
                is_primetime=False
            )
        ]

        return games

    def _get_fallback_game_details(self, game_id: str) -> Dict[str, Any]:
        """Return mock game details when API is unavailable"""
        # Parse game_id to extract teams
        parts = game_id.split('@')
        if len(parts) == 2:
            away_team, home_team = parts
        else:
            home_team, away_team = "BUF", "KC"

        return {
            "game_id": game_id,
            "home_team": home_team,
            "away_team": away_team,
            "spread": -2.5,
            "total": 54.5,
            "game_time": datetime.now() + timedelta(hours=2),
            "season": self._get_current_season(),
            "week": self._get_current_week(),
            "weather": {
                "temperature": 45,
                "wind_speed": 8,
                "precipitation": 0.1,
                "condition": "Clear"
            },
            "injuries": {"home": [], "away": []},
            "is_dome": False,
            "is_divisional": False,
            "is_primetime": True,
            "home_epa_per_play": 0.08,
            "away_epa_per_play": 0.06,
            "line_movement": 0.5,
            "public_betting_percentage": 65,
            "home_stats": self._get_fallback_team_stats(home_team),
            "away_stats": self._get_fallback_team_stats(away_team),
            "home_players": self._get_fallback_player_stats(home_team),
            "away_players": self._get_fallback_player_stats(away_team)
        }

    def _get_fallback_team_stats(self, team: str) -> Dict[str, Any]:
        """Return mock team stats when API is unavailable"""
        # Team-specific mock data
        team_data = {
            "KC": {"points_per_game": 28.5, "points_allowed": 19.2, "recent_record": "3-0"},
            "BUF": {"points_per_game": 26.3, "points_allowed": 21.8, "recent_record": "2-1"},
            "DAL": {"points_per_game": 24.1, "points_allowed": 23.5, "recent_record": "1-2"},
            "NYG": {"points_per_game": 18.7, "points_allowed": 26.2, "recent_record": "1-2"},
            "GB": {"points_per_game": 23.8, "points_allowed": 22.1, "recent_record": "2-1"},
            "CHI": {"points_per_game": 19.5, "points_allowed": 24.3, "recent_record": "1-2"}
        }

        data = team_data.get(team, {"points_per_game": 21.0, "points_allowed": 22.0, "recent_record": "2-1"})

        return {
            "team": team,
            "avg_points": data["points_per_game"],
            "points_per_game": data["points_per_game"],
            "points_allowed": data["points_allowed"],
            "total_yards_per_game": 350.0,
            "passing_yards_per_game": 240.0,
            "rushing_yards_per_game": 110.0,
            "yards_allowed_per_game": 345.0,
            "turnover_differential": 1,
            "red_zone_percentage": 0.58,
            "third_down_percentage": 0.40,
            "recent_record": data["recent_record"],
            "epa_per_play": 0.05,
            "record": "9-7"
        }

    def _get_fallback_player_stats(self, team: str) -> Dict[str, Any]:
        """Return mock player stats when API is unavailable"""
        # Team-specific mock player data
        player_data = {
            "KC": {
                "qb1": {"name": "Patrick Mahomes", "yards_per_game": 275, "touchdowns_per_game": 2.1, "interceptions_per_game": 0.7},
                "rb1": {"name": "Isiah Pacheco", "yards_per_game": 85, "attempts_per_game": 19, "touchdowns_per_game": 0.8},
                "wr1": {"name": "Tyreek Hill", "yards_per_game": 95, "receptions_per_game": 7.2, "targets_per_game": 10.5}
            },
            "BUF": {
                "qb1": {"name": "Josh Allen", "yards_per_game": 265, "touchdowns_per_game": 2.3, "interceptions_per_game": 0.9},
                "rb1": {"name": "James Cook", "yards_per_game": 78, "attempts_per_game": 17, "touchdowns_per_game": 0.6},
                "wr1": {"name": "Stefon Diggs", "yards_per_game": 88, "receptions_per_game": 6.8, "targets_per_game": 9.8}
            }
        }

        data = player_data.get(team, {
            "qb1": {"name": "Team QB", "yards_per_game": 250, "touchdowns_per_game": 1.5, "interceptions_per_game": 0.8},
            "rb1": {"name": "Team RB", "yards_per_game": 75, "attempts_per_game": 18, "touchdowns_per_game": 0.6},
            "wr1": {"name": "Team WR", "yards_per_game": 80, "receptions_per_game": 6.0, "targets_per_game": 9.0}
        })

        return data

# Test function
async def test_real_data_fetcher():
    """Test the real data fetcher"""
    fetcher = RealGameDataFetcher()

    # Test getting current week games
    games = await fetcher.get_current_week_games()
    print(f"\nFound {len(games)} games:")

    for game in games[:3]:  # Show first 3 games
        print(f"- {game.away_team} @ {game.home_team}")
        print(f"  Spread: {game.spread}, Total: {game.total}")
        print(f"  Time: {game.game_time}")
        print()

    # Test getting game details
    if games:
        game_details = await fetcher.get_game_details(games[0].game_id)
        print(f"Game details for {games[0].game_id}:")
        print(f"- Home team stats: {game_details['home_stats']['points_per_game']} PPG")
        print(f"- Away team stats: {game_details['away_stats']['points_per_game']} PPG")
        print(f"- Weather: {game_details['weather']['condition']}, {game_details['weather']['temperature']}°F")

if __name__ == "__main__":
    asyncio.run(test_real_data_fetcher())