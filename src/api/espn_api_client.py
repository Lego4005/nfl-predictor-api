"""
ESPN API client for fetching NFL game data as fallback source.
Handles basic game information, scores, and schedules.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .client_manager import APIClientManager, DataSource, APIResponse

logger = logging.getLogger(__name__)


@dataclass
class ESPNGame:
    """Structured representation of ESPN game data"""
    home_team: str
    away_team: str
    matchup: str
    game_date: datetime
    status: str
    home_score: int = 0
    away_score: int = 0
    completed: bool = False
    week: int = None


class ESPNAPIClient:
    """
    Client for ESPN API integration as fallback data source.
    Fetches basic NFL game data, scores, and schedules.
    """
    
    def __init__(self, client_manager: APIClientManager):
        self.client_manager = client_manager
        self.base_url = "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
        self.season_type = 2  # Regular season (1=preseason, 2=regular, 3=postseason)
    
    def _get_week_number(self, week: int) -> int:
        """
        Convert week number to ESPN API format.
        ESPN uses 1-18 for regular season weeks.
        """
        return max(1, min(week, 18))
    
    def _parse_team_abbreviation(self, team_data: Dict[str, Any]) -> str:
        """
        Extract team abbreviation from ESPN team data.
        ESPN provides both abbreviation and full name.
        """
        # Try abbreviation first, fallback to displayName parsing
        abbreviation = team_data.get("abbreviation", "")
        if abbreviation:
            return self._standardize_team_abbreviation(abbreviation)
        
        # Fallback to parsing display name
        display_name = team_data.get("displayName", "")
        return self._parse_team_from_name(display_name)
    
    def _standardize_team_abbreviation(self, abbr: str) -> str:
        """Standardize ESPN team abbreviations to our format"""
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
            "TEN": "TEN",
            "KC": "KC",
            "LV": "LV",
            "LAC": "LAC",
            "DEN": "DEN",
            "DAL": "DAL",
            "NYG": "NYG",
            "PHI": "PHI",
            "WSH": "WAS",  # ESPN uses WSH, we use WAS
            "WAS": "WAS",
            "CHI": "CHI",
            "DET": "DET",
            "GB": "GB",
            "MIN": "MIN",
            "ATL": "ATL",
            "CAR": "CAR",
            "NO": "NO",
            "TB": "TB",
            "ARI": "ARI",
            "LAR": "LAR",
            "SF": "SF",
            "SEA": "SEA"
        }
        
        return abbr_mapping.get(abbr.upper(), abbr.upper())
    
    def _parse_team_from_name(self, team_name: str) -> str:
        """Parse team abbreviation from full team name"""
        name_mapping = {
            "Buffalo Bills": "BUF",
            "Miami Dolphins": "MIA",
            "New England Patriots": "NE",
            "New York Jets": "NYJ",
            "Baltimore Ravens": "BAL",
            "Cincinnati Bengals": "CIN",
            "Cleveland Browns": "CLE",
            "Pittsburgh Steelers": "PIT",
            "Houston Texans": "HOU",
            "Indianapolis Colts": "IND",
            "Jacksonville Jaguars": "JAX",
            "Tennessee Titans": "TEN",
            "Denver Broncos": "DEN",
            "Kansas City Chiefs": "KC",
            "Las Vegas Raiders": "LV",
            "Los Angeles Chargers": "LAC",
            "Dallas Cowboys": "DAL",
            "New York Giants": "NYG",
            "Philadelphia Eagles": "PHI",
            "Washington Commanders": "WAS",
            "Chicago Bears": "CHI",
            "Detroit Lions": "DET",
            "Green Bay Packers": "GB",
            "Minnesota Vikings": "MIN",
            "Atlanta Falcons": "ATL",
            "Carolina Panthers": "CAR",
            "New Orleans Saints": "NO",
            "Tampa Bay Buccaneers": "TB",
            "Arizona Cardinals": "ARI",
            "Los Angeles Rams": "LAR",
            "San Francisco 49ers": "SF",
            "Seattle Seahawks": "SEA"
        }
        
        return name_mapping.get(team_name, team_name[:3].upper())
    
    def _parse_game_status(self, status_data: Dict[str, Any]) -> tuple[str, bool]:
        """
        Parse game status from ESPN status data.
        Returns (status_string, is_completed)
        """
        status_type = status_data.get("type", {})
        status_name = status_type.get("name", "scheduled")
        status_state = status_type.get("state", "pre")
        
        # Determine if game is completed
        completed = status_state in ["post", "final"]
        
        # Create readable status
        if status_state == "pre":
            status = "Scheduled"
        elif status_state == "in":
            status = "In Progress"
        elif status_state == "post":
            status = "Final"
        else:
            status = status_name.title()
        
        return status, completed
    
    def _extract_game_data(self, game_data: Dict[str, Any]) -> ESPNGame:
        """Extract and structure game data from ESPN API response"""
        # Extract basic game info
        game_id = game_data.get("id", "")
        date_str = game_data.get("date", "")
        
        # Parse game date
        try:
            game_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            game_date = datetime.utcnow()
        
        # Extract teams
        competitions = game_data.get("competitions", [])
        if not competitions:
            raise ValueError("No competition data found")
        
        competition = competitions[0]
        competitors = competition.get("competitors", [])
        
        if len(competitors) < 2:
            raise ValueError("Insufficient competitor data")
        
        # ESPN typically has home team first, away team second
        # But we need to check the homeAway field to be sure
        home_team_data = None
        away_team_data = None
        
        for competitor in competitors:
            home_away = competitor.get("homeAway", "")
            if home_away == "home":
                home_team_data = competitor
            elif home_away == "away":
                away_team_data = competitor
        
        if not home_team_data or not away_team_data:
            # Fallback: assume first is home, second is away
            home_team_data = competitors[0]
            away_team_data = competitors[1]
        
        # Extract team information
        home_team = self._parse_team_abbreviation(home_team_data.get("team", {}))
        away_team = self._parse_team_abbreviation(away_team_data.get("team", {}))
        matchup = f"{away_team} @ {home_team}"
        
        # Extract scores
        home_score = int(home_team_data.get("score", 0))
        away_score = int(away_team_data.get("score", 0))
        
        # Extract status
        status_data = competition.get("status", {})
        status, completed = self._parse_game_status(status_data)
        
        # Extract week if available
        week = None
        season_data = game_data.get("season", {})
        if season_data:
            week = season_data.get("week", None)
        
        return ESPNGame(
            home_team=home_team,
            away_team=away_team,
            matchup=matchup,
            game_date=game_date,
            status=status,
            home_score=home_score,
            away_score=away_score,
            completed=completed,
            week=week
        )
    
    def _validate_response(self, data: Any) -> bool:
        """Validate ESPN API response structure"""
        if not isinstance(data, dict):
            logger.error("Expected dict response from ESPN API")
            return False
        
        events = data.get("events", [])
        if not isinstance(events, list):
            logger.error("Expected 'events' list in ESPN API response")
            return False
        
        if len(events) == 0:
            logger.warning("No events found in ESPN API response")
            return False
        
        # Validate first event structure
        first_event = events[0]
        required_fields = ["id", "date", "competitions"]
        
        for field in required_fields:
            if field not in first_event:
                logger.error(f"Missing required field '{field}' in ESPN API response")
                return False
        
        # Validate competition structure
        competitions = first_event.get("competitions", [])
        if not competitions:
            logger.error("No competitions found in ESPN event")
            return False
        
        first_competition = competitions[0]
        if "competitors" not in first_competition:
            logger.error("Missing 'competitors' in ESPN competition")
            return False
        
        competitors = first_competition.get("competitors", [])
        if len(competitors) < 2:
            logger.error("Insufficient competitors in ESPN competition")
            return False
        
        return True    

    async def fetch_games_by_week(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch NFL games for specified week from ESPN API.
        Returns basic game information and scores.
        """
        try:
            espn_week = self._get_week_number(week)
            
            # ESPN scoreboard endpoint with week parameter
            endpoint = f"/scoreboard"
            params = {
                "seasontype": self.season_type,
                "week": espn_week
            }
            
            # Make API request through client manager with caching
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ESPN_API,
                endpoint=endpoint,
                params=params,
                week=week,
                cache_key_prefix="espn_games"
            )
            
            # Validate response
            if not self._validate_response(response.data):
                raise ValueError("Invalid response structure from ESPN API")
            
            # Parse and structure the data
            structured_games = []
            events = response.data.get("events", [])
            
            for event in events:
                try:
                    game = self._extract_game_data(event)
                    structured_games.append(game)
                except Exception as e:
                    logger.warning(f"Failed to parse ESPN game data: {str(e)}")
                    continue
            
            if not structured_games:
                raise ValueError("No valid games found in ESPN API response")
            
            # Update response with structured data
            response.data = structured_games
            
            logger.info(f"Successfully fetched {len(structured_games)} games from ESPN API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching games from ESPN API: {str(e)}")
            raise
    
    async def fetch_team_schedule(self, team_abbr: str, year: int = 2025) -> APIResponse:
        """
        Fetch team schedule from ESPN API.
        Useful for getting team-specific game information.
        """
        try:
            # ESPN team schedule endpoint
            endpoint = f"/teams/{team_abbr.lower()}/schedule"
            params = {
                "seasontype": self.season_type
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ESPN_API,
                endpoint=endpoint,
                params=params,
                week=0,  # Team schedule is not week-specific
                cache_key_prefix=f"espn_schedule_{team_abbr}"
            )
            
            # ESPN team schedule has different structure
            if not isinstance(response.data, dict):
                raise ValueError("Invalid team schedule response from ESPN API")
            
            events = response.data.get("events", [])
            structured_games = []
            
            for event in events:
                try:
                    game = self._extract_game_data(event)
                    structured_games.append(game)
                except Exception as e:
                    logger.warning(f"Failed to parse team schedule game: {str(e)}")
                    continue
            
            response.data = structured_games
            logger.info(f"Successfully fetched {len(structured_games)} games from ESPN team schedule for {team_abbr}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching team schedule from ESPN API: {str(e)}")
            raise
    
    async def fetch_live_scores(self) -> APIResponse:
        """
        Fetch current live scores from ESPN API.
        Useful for real-time game updates.
        """
        try:
            # ESPN live scoreboard endpoint
            endpoint = "/scoreboard"
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ESPN_API,
                endpoint=endpoint,
                week=0,  # Live scores are not week-specific
                cache_key_prefix="espn_live_scores",
                cache_ttl_minutes=2  # Short cache for live data
            )
            
            if not self._validate_response(response.data):
                raise ValueError("Invalid live scores response from ESPN API")
            
            # Filter for only in-progress and recently completed games
            structured_games = []
            events = response.data.get("events", [])
            
            for event in events:
                try:
                    game = self._extract_game_data(event)
                    # Only include games that are in progress or recently completed
                    if game.status in ["In Progress", "Final"]:
                        structured_games.append(game)
                except Exception as e:
                    logger.warning(f"Failed to parse live score data: {str(e)}")
                    continue
            
            response.data = structured_games
            logger.info(f"Successfully fetched {len(structured_games)} live games from ESPN API")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching live scores from ESPN API: {str(e)}")
            raise
    
    async def fetch_standings(self) -> APIResponse:
        """
        Fetch NFL standings from ESPN API.
        Provides additional context for predictions.
        """
        try:
            # ESPN standings endpoint
            endpoint = "/standings"
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ESPN_API,
                endpoint=endpoint,
                week=0,  # Standings are not week-specific
                cache_key_prefix="espn_standings",
                cache_ttl_minutes=60  # Cache standings for 1 hour
            )
            
            if not isinstance(response.data, dict):
                raise ValueError("Invalid standings response from ESPN API")
            
            # ESPN standings structure is complex, just return raw data
            # The transformer will handle the specific formatting needed
            
            logger.info("Successfully fetched NFL standings from ESPN API")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching standings from ESPN API: {str(e)}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get ESPN API information and available endpoints.
        """
        return {
            "base_url": self.base_url,
            "season_type": self.season_type,
            "endpoints": {
                "scoreboard": "/scoreboard",
                "team_schedule": "/teams/{team}/schedule",
                "standings": "/standings",
                "live_scores": "/scoreboard (live)"
            },
            "supported_data": [
                "game_scores",
                "game_schedules", 
                "team_records",
                "live_updates"
            ],
            "limitations": [
                "No betting odds",
                "No player props",
                "No fantasy projections",
                "Basic game data only"
            ],
            "rate_limits": {
                "free_tier": "~1000 requests/hour",
                "no_authentication": "Public API"
            },
            "data_freshness": {
                "live_scores": "Real-time",
                "completed_games": "Final",
                "schedules": "Updated daily"
            }
        }