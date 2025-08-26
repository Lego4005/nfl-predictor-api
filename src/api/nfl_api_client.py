"""
NFL.com API client for fetching official NFL data as fallback source.
Handles game information, player statistics, and official NFL data.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .client_manager import APIClientManager, DataSource, APIResponse

logger = logging.getLogger(__name__)


@dataclass
class NFLGame:
    """Structured representation of NFL.com game data"""
    home_team: str
    away_team: str
    matchup: str
    game_date: datetime
    week: int
    season: int
    game_type: str
    status: str
    home_score: int = 0
    away_score: int = 0
    completed: bool = False
    game_id: str = None


@dataclass
class NFLPlayerStats:
    """Structured representation of NFL player statistics"""
    player_id: str
    player_name: str
    team: str
    position: str
    stats: Dict[str, Any]
    week: int
    season: int


class NFLAPIClient:
    """
    Client for NFL.com API integration as fallback data source.
    Fetches official NFL game data, player statistics, and team information.
    """
    
    def __init__(self, client_manager: APIClientManager):
        self.client_manager = client_manager
        self.base_url = "https://api.nfl.com/v1"
        self.season = 2025
        self.season_type = "REG"  # Regular season
    
    def _get_week_parameter(self, week: int) -> str:
        """
        Convert week number to NFL API format.
        NFL.com API uses string week numbers.
        """
        return str(max(1, min(week, 18)))
    
    def _parse_team_abbreviation(self, team_data: Any) -> str:
        """
        Extract and standardize team abbreviation from NFL API data.
        NFL.com uses standard abbreviations but may have variations.
        """
        if isinstance(team_data, dict):
            # Try different possible fields
            abbr = team_data.get("abbr") or team_data.get("abbreviation") or team_data.get("teamAbbr")
        elif isinstance(team_data, str):
            abbr = team_data
        else:
            abbr = str(team_data)
        
        return self._standardize_nfl_abbreviation(abbr)
    
    def _standardize_nfl_abbreviation(self, abbr: str) -> str:
        """Standardize NFL.com team abbreviations to our format"""
        if not abbr:
            return ""
        
        abbr_mapping = {
            "NE": "NE",
            "NYJ": "NYJ",
            "BUF": "BUF",
            "MIA": "MIA",
            "PIT": "PIT",
            "CLE": "CLE",
            "BAL": "BAL",
            "CIN": "CIN",
            "HOU": "HOU",
            "IND": "IND",
            "JAX": "JAX",
            "JAC": "JAX",  # NFL.com sometimes uses JAC
            "TEN": "TEN",
            "KC": "KC",
            "KAN": "KC",   # NFL.com sometimes uses KAN
            "LV": "LV",
            "LVR": "LV",   # NFL.com sometimes uses LVR
            "OAK": "LV",   # Legacy Oakland
            "LAC": "LAC",
            "SD": "LAC",   # Legacy San Diego
            "DEN": "DEN",
            "DAL": "DAL",
            "NYG": "NYG",
            "PHI": "PHI",
            "WAS": "WAS",
            "WSH": "WAS",  # NFL.com sometimes uses WSH
            "CHI": "CHI",
            "DET": "DET",
            "GB": "GB",
            "GNB": "GB",   # NFL.com sometimes uses GNB
            "MIN": "MIN",
            "ATL": "ATL",
            "CAR": "CAR",
            "NO": "NO",
            "NOR": "NO",   # NFL.com sometimes uses NOR
            "TB": "TB",
            "TAM": "TB",   # NFL.com sometimes uses TAM
            "ARI": "ARI",
            "LAR": "LAR",
            "STL": "LAR",  # Legacy St. Louis
            "SF": "SF",
            "SFO": "SF",   # NFL.com sometimes uses SFO
            "SEA": "SEA"
        }
        
        return abbr_mapping.get(abbr.upper(), abbr.upper())
    
    def _parse_game_status(self, status_data: Any) -> tuple[str, bool]:
        """
        Parse game status from NFL API data.
        Returns (status_string, is_completed)
        """
        if isinstance(status_data, dict):
            status = status_data.get("phase", "scheduled")
        else:
            status = str(status_data).lower()
        
        # NFL.com status mapping
        status_mapping = {
            "scheduled": ("Scheduled", False),
            "pregame": ("Pre-Game", False),
            "ingame": ("In Progress", False),
            "halftime": ("Halftime", False),
            "final": ("Final", True),
            "final_overtime": ("Final OT", True),
            "postponed": ("Postponed", False),
            "canceled": ("Canceled", True)
        }
        
        return status_mapping.get(status.lower(), (status.title(), False))
    
    def _extract_game_data(self, game_data: Dict[str, Any]) -> NFLGame:
        """Extract and structure game data from NFL API response"""
        # Extract basic game info
        game_id = game_data.get("gameId") or game_data.get("id", "")
        
        # Extract date/time
        game_time = game_data.get("gameTime") or game_data.get("gameDate", "")
        try:
            if isinstance(game_time, str):
                # Handle various date formats from NFL.com
                if "T" in game_time:
                    game_date = datetime.fromisoformat(game_time.replace("Z", "+00:00"))
                else:
                    game_date = datetime.strptime(game_time, "%Y-%m-%d")
            else:
                game_date = datetime.utcnow()
        except:
            game_date = datetime.utcnow()
        
        # Extract teams
        home_team_data = game_data.get("homeTeam") or game_data.get("home", {})
        away_team_data = game_data.get("awayTeam") or game_data.get("away", {})
        
        home_team = self._parse_team_abbreviation(home_team_data)
        away_team = self._parse_team_abbreviation(away_team_data)
        matchup = f"{away_team} @ {home_team}"
        
        # Extract scores
        home_score = 0
        away_score = 0
        
        if isinstance(home_team_data, dict):
            home_score = int(home_team_data.get("score", 0))
        if isinstance(away_team_data, dict):
            away_score = int(away_team_data.get("score", 0))
        
        # Extract week and season
        week = int(game_data.get("week", 1))
        season = int(game_data.get("season", self.season))
        
        # Extract game type
        game_type = game_data.get("seasonType", self.season_type)
        
        # Extract status
        status_data = game_data.get("gameStatus") or game_data.get("status", "scheduled")
        status, completed = self._parse_game_status(status_data)
        
        return NFLGame(
            home_team=home_team,
            away_team=away_team,
            matchup=matchup,
            game_date=game_date,
            week=week,
            season=season,
            game_type=game_type,
            status=status,
            home_score=home_score,
            away_score=away_score,
            completed=completed,
            game_id=game_id
        )
    
    def _extract_player_stats(self, player_data: Dict[str, Any], week: int) -> NFLPlayerStats:
        """Extract player statistics from NFL API response"""
        player_id = player_data.get("playerId") or player_data.get("id", "")
        player_name = player_data.get("displayName") or player_data.get("name", "")
        team = self._parse_team_abbreviation(player_data.get("team", ""))
        position = player_data.get("position", "")
        
        # Extract stats (structure varies by position)
        stats = {}
        stats_data = player_data.get("stats", {})
        
        if isinstance(stats_data, dict):
            # Common stats
            stats.update({
                "passing_yards": stats_data.get("passingYards", 0),
                "passing_tds": stats_data.get("passingTouchdowns", 0),
                "rushing_yards": stats_data.get("rushingYards", 0),
                "rushing_tds": stats_data.get("rushingTouchdowns", 0),
                "receiving_yards": stats_data.get("receivingYards", 0),
                "receiving_tds": stats_data.get("receivingTouchdowns", 0),
                "receptions": stats_data.get("receptions", 0),
                "targets": stats_data.get("targets", 0)
            })
        
        return NFLPlayerStats(
            player_id=player_id,
            player_name=player_name,
            team=team,
            position=position,
            stats=stats,
            week=week,
            season=self.season
        )
    
    def _validate_games_response(self, data: Any) -> bool:
        """Validate NFL API games response structure"""
        if isinstance(data, dict):
            # Check for games array
            games = data.get("games") or data.get("data", [])
            if not isinstance(games, list):
                logger.error("Expected 'games' list in NFL API response")
                return False
            
            if len(games) == 0:
                logger.warning("No games found in NFL API response")
                return False
            
            # Validate first game structure
            first_game = games[0]
            required_fields = ["gameId", "homeTeam", "awayTeam"]
            
            for field in required_fields:
                if field not in first_game:
                    logger.error(f"Missing required field '{field}' in NFL API game")
                    return False
            
            return True
        
        elif isinstance(data, list):
            # Direct list of games
            if len(data) == 0:
                logger.warning("Empty games list from NFL API")
                return False
            
            return True
        
        else:
            logger.error("Unexpected NFL API response format")
            return False
    
    def _validate_stats_response(self, data: Any) -> bool:
        """Validate NFL API stats response structure"""
        if isinstance(data, dict):
            players = data.get("players") or data.get("data", [])
        elif isinstance(data, list):
            players = data
        else:
            logger.error("Unexpected NFL API stats response format")
            return False
        
        if not isinstance(players, list):
            logger.error("Expected players list in NFL API stats response")
            return False
        
        if len(players) == 0:
            logger.warning("No players found in NFL API stats response")
            return False
        
        return True   
 
    async def fetch_games_by_week(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch NFL games for specified week from NFL.com API.
        Returns official NFL game information and scores.
        """
        try:
            week_str = self._get_week_parameter(week)
            
            # NFL.com games endpoint
            endpoint = f"/games"
            params = {
                "season": year,
                "seasonType": self.season_type,
                "week": week_str
            }
            
            # Make API request through client manager with caching
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=week,
                cache_key_prefix="nfl_games"
            )
            
            # Validate response
            if not self._validate_games_response(response.data):
                raise ValueError("Invalid response structure from NFL API")
            
            # Parse and structure the data
            structured_games = []
            
            # Handle different response formats
            if isinstance(response.data, dict):
                games_data = response.data.get("games", response.data.get("data", []))
            else:
                games_data = response.data
            
            for game_data in games_data:
                try:
                    game = self._extract_game_data(game_data)
                    structured_games.append(game)
                except Exception as e:
                    logger.warning(f"Failed to parse NFL game data: {str(e)}")
                    continue
            
            if not structured_games:
                raise ValueError("No valid games found in NFL API response")
            
            # Update response with structured data
            response.data = structured_games
            
            logger.info(f"Successfully fetched {len(structured_games)} games from NFL API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching games from NFL API: {str(e)}")
            raise
    
    async def fetch_player_stats(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch player statistics for specified week from NFL.com API.
        Returns official NFL player performance data.
        """
        try:
            week_str = self._get_week_parameter(week)
            
            # NFL.com player stats endpoint
            endpoint = f"/stats/players"
            params = {
                "season": year,
                "seasonType": self.season_type,
                "week": week_str
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=week,
                cache_key_prefix="nfl_player_stats"
            )
            
            if not self._validate_stats_response(response.data):
                raise ValueError("Invalid stats response from NFL API")
            
            # Parse and structure player stats
            structured_players = []
            
            # Handle different response formats
            if isinstance(response.data, dict):
                players_data = response.data.get("players", response.data.get("data", []))
            else:
                players_data = response.data
            
            for player_data in players_data:
                try:
                    player_stats = self._extract_player_stats(player_data, week)
                    structured_players.append(player_stats)
                except Exception as e:
                    logger.warning(f"Failed to parse NFL player stats: {str(e)}")
                    continue
            
            response.data = structured_players
            logger.info(f"Successfully fetched stats for {len(structured_players)} players from NFL API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching player stats from NFL API: {str(e)}")
            raise
    
    async def fetch_team_stats(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch team statistics for specified week from NFL.com API.
        Returns official NFL team performance data.
        """
        try:
            week_str = self._get_week_parameter(week)
            
            # NFL.com team stats endpoint
            endpoint = f"/stats/teams"
            params = {
                "season": year,
                "seasonType": self.season_type,
                "week": week_str
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=week,
                cache_key_prefix="nfl_team_stats"
            )
            
            # NFL team stats have different structure, return raw for now
            # The transformer will handle specific formatting
            
            logger.info(f"Successfully fetched team stats from NFL API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching team stats from NFL API: {str(e)}")
            raise
    
    async def fetch_standings(self, year: int = 2025) -> APIResponse:
        """
        Fetch current NFL standings from NFL.com API.
        Returns official NFL standings and team records.
        """
        try:
            # NFL.com standings endpoint
            endpoint = f"/standings"
            params = {
                "season": year,
                "seasonType": self.season_type
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=0,  # Standings are not week-specific
                cache_key_prefix="nfl_standings",
                cache_ttl_minutes=60  # Cache standings for 1 hour
            )
            
            logger.info("Successfully fetched NFL standings from NFL API")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching standings from NFL API: {str(e)}")
            raise
    
    async def fetch_injuries(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch injury report for specified week from NFL.com API.
        Returns official NFL injury information.
        """
        try:
            week_str = self._get_week_parameter(week)
            
            # NFL.com injuries endpoint
            endpoint = f"/injuries"
            params = {
                "season": year,
                "seasonType": self.season_type,
                "week": week_str
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=week,
                cache_key_prefix="nfl_injuries",
                cache_ttl_minutes=30  # Cache injuries for 30 minutes
            )
            
            logger.info(f"Successfully fetched injury report from NFL API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching injuries from NFL API: {str(e)}")
            raise
    
    async def fetch_schedule(self, team_abbr: Optional[str] = None, year: int = 2025) -> APIResponse:
        """
        Fetch NFL schedule from NFL.com API.
        Can fetch full league schedule or team-specific schedule.
        """
        try:
            # NFL.com schedule endpoint
            if team_abbr:
                endpoint = f"/teams/{team_abbr.upper()}/schedule"
                cache_key = f"nfl_schedule_{team_abbr}"
            else:
                endpoint = f"/schedule"
                cache_key = "nfl_schedule_full"
            
            params = {
                "season": year,
                "seasonType": self.season_type
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.NFL_API,
                endpoint=endpoint,
                params=params,
                week=0,  # Schedule is not week-specific
                cache_key_prefix=cache_key,
                cache_ttl_minutes=120  # Cache schedule for 2 hours
            )
            
            target = f"team {team_abbr}" if team_abbr else "full league"
            logger.info(f"Successfully fetched {target} schedule from NFL API")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching schedule from NFL API: {str(e)}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get NFL.com API information and available endpoints.
        """
        return {
            "base_url": self.base_url,
            "season": self.season,
            "season_type": self.season_type,
            "endpoints": {
                "games": "/games",
                "player_stats": "/stats/players",
                "team_stats": "/stats/teams",
                "standings": "/standings",
                "injuries": "/injuries",
                "schedule": "/schedule",
                "team_schedule": "/teams/{team}/schedule"
            },
            "supported_data": [
                "official_game_data",
                "player_statistics",
                "team_statistics",
                "injury_reports",
                "standings",
                "schedules"
            ],
            "data_quality": {
                "accuracy": "Official NFL data",
                "completeness": "Comprehensive",
                "timeliness": "Real-time updates"
            },
            "limitations": [
                "No betting odds",
                "No player props",
                "No fantasy projections",
                "May have rate limiting"
            ],
            "rate_limits": {
                "estimated": "~500 requests/hour",
                "authentication": "May require API key for higher limits"
            },
            "advantages": [
                "Official NFL data source",
                "High reliability",
                "Comprehensive statistics",
                "Real-time updates",
                "Historical data available"
            ]
        }