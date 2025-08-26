"""
SportsDataIO API client for fetching NFL prop bets and fantasy data.
Handles player props, DFS salaries, and fantasy projections.
"""

import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .client_manager import APIClientManager, DataSource, APIResponse

logger = logging.getLogger(__name__)


class PropType(Enum):
    """Types of player prop bets"""
    PASSING_YARDS = "Passing Yards"
    RUSHING_YARDS = "Rushing Yards"
    RECEIVING_YARDS = "Receiving Yards"
    RECEPTIONS = "Receptions"
    TOUCHDOWNS = "Touchdowns"
    FANTASY_POINTS = "Fantasy Points"


class Position(Enum):
    """Player positions"""
    QB = "QB"
    RB = "RB"
    WR = "WR"
    TE = "TE"
    K = "K"
    DST = "DST"


@dataclass
class PropBet:
    """Structured representation of player prop bet"""
    player: str
    prop_type: PropType
    units: str
    line: float
    pick: str  # "Over" or "Under"
    confidence: float
    bookmaker: str
    team: str
    opponent: str
    game_date: datetime = None
    market_id: str = None


@dataclass
class FantasyPlayer:
    """Structured representation of fantasy player data"""
    player: str
    position: Position
    team: str
    salary: int
    projected_points: float
    value_score: float
    opponent: str = None
    game_date: datetime = None
    injury_status: str = None


class SportsDataIOClient:
    """
    Client for SportsDataIO API integration.
    Fetches NFL player props, DFS salaries, and fantasy projections.
    """
    
    def __init__(self, client_manager: APIClientManager):
        self.client_manager = client_manager
        self.season = "2025"
        self.season_type = "REG"  # Regular season
    
    def _get_week_games(self, week: int) -> str:
        """
        Get the week parameter for SportsDataIO API.
        SportsDataIO uses week numbers directly.
        """
        return str(week)
    
    def _parse_team_abbreviation(self, team: str) -> str:
        """
        Ensure team abbreviations are in correct format.
        SportsDataIO typically uses standard NFL abbreviations.
        """
        team_mapping = {
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
        
        return team_mapping.get(team.upper(), team.upper())
    
    def _determine_prop_type(self, market_name: str) -> PropType:
        """Determine prop type from market name"""
        market_lower = market_name.lower()
        
        if "passing" in market_lower and "yard" in market_lower:
            return PropType.PASSING_YARDS
        elif "rushing" in market_lower and "yard" in market_lower:
            return PropType.RUSHING_YARDS
        elif "receiving" in market_lower and "yard" in market_lower:
            return PropType.RECEIVING_YARDS
        elif "reception" in market_lower:
            return PropType.RECEPTIONS
        elif "touchdown" in market_lower or "td" in market_lower:
            return PropType.TOUCHDOWNS
        elif "fantasy" in market_lower:
            return PropType.FANTASY_POINTS
        else:
            return PropType.FANTASY_POINTS  # Default fallback
    
    def _extract_prop_data(self, prop_data: Dict[str, Any]) -> PropBet:
        """Extract and structure prop bet data from API response"""
        player_name = prop_data.get("PlayerName", "")
        team = self._parse_team_abbreviation(prop_data.get("Team", ""))
        opponent = self._parse_team_abbreviation(prop_data.get("Opponent", ""))
        
        # Extract market information
        market_name = prop_data.get("MarketName", "")
        prop_type = self._determine_prop_type(market_name)
        
        # Extract betting line and pick
        line = float(prop_data.get("Line", 0))
        over_under = prop_data.get("OverUnder", "Over")
        
        # Determine units based on prop type
        units_mapping = {
            PropType.PASSING_YARDS: "yds",
            PropType.RUSHING_YARDS: "yds", 
            PropType.RECEIVING_YARDS: "yds",
            PropType.RECEPTIONS: "rec",
            PropType.TOUCHDOWNS: "td",
            PropType.FANTASY_POINTS: "pts"
        }
        units = units_mapping.get(prop_type, "pts")
        
        # Calculate confidence (mock calculation based on line movement)
        # In production, this would be based on actual prediction models
        base_confidence = 0.55
        line_factor = min(abs(line) / 100, 0.15)  # Higher lines = more confidence
        confidence = base_confidence + line_factor
        
        bookmaker = prop_data.get("Sportsbook", "SportsDataIO")
        
        # Parse game date if available
        game_date = None
        if "GameDate" in prop_data:
            try:
                game_date = datetime.fromisoformat(prop_data["GameDate"].replace("Z", "+00:00"))
            except:
                pass
        
        return PropBet(
            player=player_name,
            prop_type=prop_type,
            units=units,
            line=line,
            pick=over_under,
            confidence=confidence,
            bookmaker=bookmaker,
            team=team,
            opponent=opponent,
            game_date=game_date,
            market_id=prop_data.get("MarketID")
        )
    
    def _extract_fantasy_data(self, player_data: Dict[str, Any]) -> FantasyPlayer:
        """Extract and structure fantasy player data from API response"""
        player_name = player_data.get("Name", "")
        position_str = player_data.get("Position", "")
        team = self._parse_team_abbreviation(player_data.get("Team", ""))
        
        # Parse position
        try:
            position = Position(position_str)
        except ValueError:
            position = Position.WR  # Default fallback
        
        # Extract salary and projections
        salary = int(player_data.get("DraftKingsSalary", 0))
        if salary == 0:
            salary = int(player_data.get("FanDuelSalary", 0))
        
        projected_points = float(player_data.get("FantasyPointsDraftKings", 0))
        if projected_points == 0:
            projected_points = float(player_data.get("FantasyPointsFanDuel", 0))
        
        # Calculate value score (points per $1000 of salary)
        value_score = 0.0
        if salary > 0:
            value_score = (projected_points / salary) * 1000
        
        opponent = self._parse_team_abbreviation(player_data.get("Opponent", ""))
        injury_status = player_data.get("InjuryStatus", "")
        
        # Parse game date if available
        game_date = None
        if "GameDate" in player_data:
            try:
                game_date = datetime.fromisoformat(player_data["GameDate"].replace("Z", "+00:00"))
            except:
                pass
        
        return FantasyPlayer(
            player=player_name,
            position=position,
            team=team,
            salary=salary,
            projected_points=projected_points,
            value_score=value_score,
            opponent=opponent,
            game_date=game_date,
            injury_status=injury_status
        )
    
    def _validate_props_response(self, data: Any) -> bool:
        """Validate prop bets API response"""
        if not isinstance(data, list):
            logger.error("Expected list response from SportsDataIO props API")
            return False
        
        if len(data) == 0:
            logger.warning("Empty props response from SportsDataIO")
            return False
        
        # Validate first prop structure
        first_prop = data[0]
        required_fields = ["PlayerName", "MarketName", "Line"]
        
        for field in required_fields:
            if field not in first_prop:
                logger.error(f"Missing required field '{field}' in SportsDataIO props response")
                return False
        
        return True
    
    def _validate_fantasy_response(self, data: Any) -> bool:
        """Validate fantasy data API response"""
        if not isinstance(data, list):
            logger.error("Expected list response from SportsDataIO fantasy API")
            return False
        
        if len(data) == 0:
            logger.warning("Empty fantasy response from SportsDataIO")
            return False
        
        # Validate first player structure
        first_player = data[0]
        required_fields = ["Name", "Position", "Team"]
        
        for field in required_fields:
            if field not in first_player:
                logger.error(f"Missing required field '{field}' in SportsDataIO fantasy response")
                return False
        
        return True
    
    async def fetch_player_props(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch player prop bets for specified week.
        Returns structured prop bet data with lines and predictions.
        """
        try:
            week_str = self._get_week_games(week)
            
            # SportsDataIO endpoint for player props
            endpoint = f"/scores/json/PlayerPropsByWeek/{self.season}/{week_str}"
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.SPORTSDATA_IO,
                endpoint=endpoint,
                week=week,
                cache_key_prefix="player_props"
            )
            
            if not self._validate_props_response(response.data):
                raise ValueError("Invalid props response from SportsDataIO")
            
            # Parse and structure prop data
            structured_props = []
            for prop_data in response.data:
                try:
                    prop_bet = self._extract_prop_data(prop_data)
                    structured_props.append(prop_bet)
                except Exception as e:
                    logger.warning(f"Failed to parse prop data: {str(e)}")
                    continue
            
            if not structured_props:
                raise ValueError("No valid props found in SportsDataIO response")
            
            # Sort by confidence and take top props
            structured_props.sort(key=lambda x: x.confidence, reverse=True)
            
            response.data = structured_props
            logger.info(f"Successfully fetched {len(structured_props)} props from SportsDataIO for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching props from SportsDataIO: {str(e)}")
            raise
    
    async def fetch_dfs_salaries(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch DFS salary and projection data for specified week.
        Returns structured fantasy player data with salaries and projections.
        """
        try:
            week_str = self._get_week_games(week)
            
            # SportsDataIO endpoint for DFS projections
            endpoint = f"/scores/json/DfsSlatesByWeek/{self.season}/{week_str}"
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.SPORTSDATA_IO,
                endpoint=endpoint,
                week=week,
                cache_key_prefix="dfs_salaries"
            )
            
            if not self._validate_fantasy_response(response.data):
                raise ValueError("Invalid fantasy response from SportsDataIO")
            
            # Parse and structure fantasy data
            structured_players = []
            for player_data in response.data:
                try:
                    fantasy_player = self._extract_fantasy_data(player_data)
                    if fantasy_player.salary > 0:  # Only include players with salary data
                        structured_players.append(fantasy_player)
                except Exception as e:
                    logger.warning(f"Failed to parse fantasy data: {str(e)}")
                    continue
            
            if not structured_players:
                raise ValueError("No valid fantasy players found in SportsDataIO response")
            
            # Sort by value score
            structured_players.sort(key=lambda x: x.value_score, reverse=True)
            
            response.data = structured_players
            logger.info(f"Successfully fetched {len(structured_players)} fantasy players from SportsDataIO for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching fantasy data from SportsDataIO: {str(e)}")
            raise
    
    async def fetch_player_stats(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch player statistics for specified week.
        Used for generating prop bet predictions.
        """
        try:
            week_str = self._get_week_games(week)
            
            # SportsDataIO endpoint for player stats
            endpoint = f"/stats/json/PlayerStatsByWeek/{self.season}/{self.season_type}/{week_str}"
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.SPORTSDATA_IO,
                endpoint=endpoint,
                week=week,
                cache_key_prefix="player_stats"
            )
            
            if not isinstance(response.data, list):
                raise ValueError("Invalid stats response from SportsDataIO")
            
            logger.info(f"Successfully fetched stats for {len(response.data)} players from SportsDataIO for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching stats from SportsDataIO: {str(e)}")
            raise
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get SportsDataIO API information and available endpoints.
        """
        return {
            "season": self.season,
            "season_type": self.season_type,
            "endpoints": {
                "player_props": f"/scores/json/PlayerPropsByWeek/{self.season}/{{week}}",
                "dfs_salaries": f"/scores/json/DfsSlatesByWeek/{self.season}/{{week}}",
                "player_stats": f"/stats/json/PlayerStatsByWeek/{self.season}/{self.season_type}/{{week}}",
                "games": f"/scores/json/GamesByWeek/{self.season}/{self.season_type}/{{week}}"
            },
            "supported_props": [prop.value for prop in PropType],
            "supported_positions": [pos.value for pos in Position],
            "rate_limits": {
                "free_tier": "1000 requests/month",
                "paid_tier": "Variable based on plan"
            }
        }