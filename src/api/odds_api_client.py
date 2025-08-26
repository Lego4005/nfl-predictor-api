"""
The Odds API client for fetching NFL game odds, spreads, and totals.
Handles authentication, response validation, and data formatting.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from .client_manager import APIClientManager, DataSource, APIResponse

logger = logging.getLogger(__name__)


@dataclass
class GameOdds:
    """Structured representation of game odds data"""
    home_team: str
    away_team: str
    matchup: str
    commence_time: datetime
    bookmakers: List[Dict[str, Any]]
    spreads: Dict[str, float] = None
    totals: Dict[str, float] = None
    moneylines: Dict[str, int] = None


class OddsAPIClient:
    """
    Client for The Odds API integration.
    Fetches NFL game odds, spreads, totals, and moneylines.
    """
    
    def __init__(self, client_manager: APIClientManager):
        self.client_manager = client_manager
        self.sport = "americanfootball_nfl"
        self.regions = "us"
        self.markets = "h2h,spreads,totals"  # moneyline, spreads, totals
        self.odds_format = "american"
        self.date_format = "iso"
    
    def _get_week_date_range(self, week: int, year: int = 2025) -> tuple[str, str]:
        """
        Calculate date range for NFL week.
        NFL season typically starts first Thursday in September.
        """
        # Approximate NFL season start (first Thursday in September)
        # This is a simplified calculation - in production, use actual NFL schedule
        season_start = datetime(year, 9, 5)  # Approximate start
        
        # Find first Thursday
        days_to_thursday = (3 - season_start.weekday()) % 7
        first_thursday = season_start + timedelta(days=days_to_thursday)
        
        # Calculate week start (Thursday to Wednesday)
        week_start = first_thursday + timedelta(weeks=week-1)
        week_end = week_start + timedelta(days=6)
        
        return (
            week_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
            week_end.strftime("%Y-%m-%dT%H:%M:%SZ")
        )
    
    def _parse_team_name(self, team_name: str) -> str:
        """
        Convert full team names to standard abbreviations.
        The Odds API returns full team names, we need abbreviations.
        """
        team_mapping = {
            # AFC East
            "Buffalo Bills": "BUF",
            "Miami Dolphins": "MIA", 
            "New England Patriots": "NE",
            "New York Jets": "NYJ",
            
            # AFC North
            "Baltimore Ravens": "BAL",
            "Cincinnati Bengals": "CIN",
            "Cleveland Browns": "CLE",
            "Pittsburgh Steelers": "PIT",
            
            # AFC South
            "Houston Texans": "HOU",
            "Indianapolis Colts": "IND",
            "Jacksonville Jaguars": "JAX",
            "Tennessee Titans": "TEN",
            
            # AFC West
            "Denver Broncos": "DEN",
            "Kansas City Chiefs": "KC",
            "Las Vegas Raiders": "LV",
            "Los Angeles Chargers": "LAC",
            
            # NFC East
            "Dallas Cowboys": "DAL",
            "New York Giants": "NYG",
            "Philadelphia Eagles": "PHI",
            "Washington Commanders": "WAS",
            
            # NFC North
            "Chicago Bears": "CHI",
            "Detroit Lions": "DET",
            "Green Bay Packers": "GB",
            "Minnesota Vikings": "MIN",
            
            # NFC South
            "Atlanta Falcons": "ATL",
            "Carolina Panthers": "CAR",
            "New Orleans Saints": "NO",
            "Tampa Bay Buccaneers": "TB",
            
            # NFC West
            "Arizona Cardinals": "ARI",
            "Los Angeles Rams": "LAR",
            "San Francisco 49ers": "SF",
            "Seattle Seahawks": "SEA"
        }
        
        return team_mapping.get(team_name, team_name)
    
    def _extract_odds_data(self, game_data: Dict[str, Any]) -> GameOdds:
        """Extract and structure odds data from API response"""
        home_team = self._parse_team_name(game_data.get("home_team", ""))
        away_team = self._parse_team_name(game_data.get("away_team", ""))
        matchup = f"{away_team} @ {home_team}"
        
        commence_time = datetime.fromisoformat(
            game_data.get("commence_time", "").replace("Z", "+00:00")
        )
        
        bookmakers = game_data.get("bookmakers", [])
        
        # Extract spreads, totals, and moneylines from bookmakers
        spreads = {}
        totals = {}
        moneylines = {}
        
        for bookmaker in bookmakers:
            book_name = bookmaker.get("title", "")
            markets = bookmaker.get("markets", [])
            
            for market in markets:
                market_key = market.get("key", "")
                outcomes = market.get("outcomes", [])
                
                if market_key == "spreads":
                    for outcome in outcomes:
                        team = self._parse_team_name(outcome.get("name", ""))
                        point = outcome.get("point", 0)
                        price = outcome.get("price", 0)
                        
                        if team == home_team:
                            spreads[f"{book_name}_home_spread"] = point
                            spreads[f"{book_name}_home_spread_price"] = price
                        elif team == away_team:
                            spreads[f"{book_name}_away_spread"] = point
                            spreads[f"{book_name}_away_spread_price"] = price
                
                elif market_key == "totals":
                    for outcome in outcomes:
                        name = outcome.get("name", "")
                        point = outcome.get("point", 0)
                        price = outcome.get("price", 0)
                        
                        if name == "Over":
                            totals[f"{book_name}_over_total"] = point
                            totals[f"{book_name}_over_price"] = price
                        elif name == "Under":
                            totals[f"{book_name}_under_total"] = point
                            totals[f"{book_name}_under_price"] = price
                
                elif market_key == "h2h":  # moneyline
                    for outcome in outcomes:
                        team = self._parse_team_name(outcome.get("name", ""))
                        price = outcome.get("price", 0)
                        
                        if team == home_team:
                            moneylines[f"{book_name}_home_ml"] = price
                        elif team == away_team:
                            moneylines[f"{book_name}_away_ml"] = price
        
        return GameOdds(
            home_team=home_team,
            away_team=away_team,
            matchup=matchup,
            commence_time=commence_time,
            bookmakers=bookmakers,
            spreads=spreads,
            totals=totals,
            moneylines=moneylines
        )
    
    def _validate_response(self, data: Any) -> bool:
        """Validate API response structure and content"""
        if not isinstance(data, list):
            logger.error("Expected list response from Odds API")
            return False
        
        if len(data) == 0:
            logger.warning("Empty response from Odds API")
            return False
        
        # Validate first game structure
        first_game = data[0]
        required_fields = ["home_team", "away_team", "commence_time", "bookmakers"]
        
        for field in required_fields:
            if field not in first_game:
                logger.error(f"Missing required field '{field}' in Odds API response")
                return False
        
        # Validate bookmakers structure
        bookmakers = first_game.get("bookmakers", [])
        if not bookmakers:
            logger.warning("No bookmakers found in Odds API response")
            return False
        
        first_bookmaker = bookmakers[0]
        if "markets" not in first_bookmaker:
            logger.error("Missing 'markets' in bookmaker data")
            return False
        
        return True
    
    async def fetch_games_odds(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch NFL game odds for specified week.
        Returns structured odds data with spreads, totals, and moneylines.
        """
        try:
            # Get date range for the week
            date_from, date_to = self._get_week_date_range(week, year)
            
            # Build API parameters
            params = {
                "sport": self.sport,
                "regions": self.regions,
                "markets": self.markets,
                "oddsFormat": self.odds_format,
                "dateFormat": self.date_format,
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
            
            # Make API request through client manager with caching
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ODDS_API,
                endpoint="/sports/americanfootball_nfl/odds",
                params=params,
                week=week,
                cache_key_prefix="game_odds"
            )
            
            # Validate response
            if not self._validate_response(response.data):
                raise ValueError("Invalid response structure from Odds API")
            
            # Parse and structure the data
            structured_games = []
            for game_data in response.data:
                try:
                    game_odds = self._extract_odds_data(game_data)
                    structured_games.append(game_odds)
                except Exception as e:
                    logger.warning(f"Failed to parse game data: {str(e)}")
                    continue
            
            if not structured_games:
                raise ValueError("No valid games found in Odds API response")
            
            # Update response with structured data
            response.data = structured_games
            
            logger.info(f"Successfully fetched {len(structured_games)} games from Odds API for week {week}")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching odds from Odds API: {str(e)}")
            raise
    
    async def fetch_game_spreads(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch only spread betting lines for NFL games.
        Optimized endpoint for spread-specific data.
        """
        try:
            date_from, date_to = self._get_week_date_range(week, year)
            
            params = {
                "sport": self.sport,
                "regions": self.regions,
                "markets": "spreads",  # Only spreads
                "oddsFormat": self.odds_format,
                "dateFormat": self.date_format,
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ODDS_API,
                endpoint="/sports/americanfootball_nfl/odds",
                params=params,
                week=week,
                cache_key_prefix="game_spreads"
            )
            
            if not self._validate_response(response.data):
                raise ValueError("Invalid spreads response from Odds API")
            
            # Extract only spread data
            spread_games = []
            for game_data in response.data:
                game_odds = self._extract_odds_data(game_data)
                if game_odds.spreads:  # Only include games with spread data
                    spread_games.append(game_odds)
            
            response.data = spread_games
            logger.info(f"Successfully fetched spreads for {len(spread_games)} games")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching spreads from Odds API: {str(e)}")
            raise
    
    async def fetch_game_totals(self, week: int, year: int = 2025) -> APIResponse:
        """
        Fetch only over/under totals for NFL games.
        Optimized endpoint for totals-specific data.
        """
        try:
            date_from, date_to = self._get_week_date_range(week, year)
            
            params = {
                "sport": self.sport,
                "regions": self.regions,
                "markets": "totals",  # Only totals
                "oddsFormat": self.odds_format,
                "dateFormat": self.date_format,
                "commenceTimeFrom": date_from,
                "commenceTimeTo": date_to
            }
            
            response = await self.client_manager.fetch_with_cache(
                source=DataSource.ODDS_API,
                endpoint="/sports/americanfootball_nfl/odds",
                params=params,
                week=week,
                cache_key_prefix="game_totals"
            )
            
            if not self._validate_response(response.data):
                raise ValueError("Invalid totals response from Odds API")
            
            # Extract only totals data
            totals_games = []
            for game_data in response.data:
                game_odds = self._extract_odds_data(game_data)
                if game_odds.totals:  # Only include games with totals data
                    totals_games.append(game_odds)
            
            response.data = totals_games
            logger.info(f"Successfully fetched totals for {len(totals_games)} games")
            return response
            
        except Exception as e:
            logger.error(f"Error fetching totals from Odds API: {str(e)}")
            raise
    
    def get_usage_info(self) -> Dict[str, Any]:
        """
        Get API usage information and limits.
        The Odds API provides usage info in response headers.
        """
        return {
            "sport": self.sport,
            "regions": self.regions,
            "markets": self.markets,
            "odds_format": self.odds_format,
            "endpoints": {
                "odds": "/sports/americanfootball_nfl/odds",
                "spreads": "/sports/americanfootball_nfl/odds?markets=spreads",
                "totals": "/sports/americanfootball_nfl/odds?markets=totals"
            },
            "rate_limits": {
                "free_tier": "500 requests/month",
                "paid_tier": "Variable based on plan"
            }
        }