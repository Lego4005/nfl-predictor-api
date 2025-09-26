"""
Enhanced API Client Collection
Integrates multiple data sources for comprehensive NFL prediction data
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
import asyncio
import aiohttp
import json
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class GameData:
    """Standardized game data structure"""
    game_id: str
    home_team: str
    away_team: str
    week: int
    season: int
    game_date: datetime
    spread: Optional[float] = None
    total: Optional[float] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    weather: Dict[str, Any] = field(default_factory=dict)
    injuries: Dict[str, List[Dict]] = field(default_factory=dict)
    team_stats: Dict[str, Any] = field(default_factory=dict)
    player_stats: Dict[str, Any] = field(default_factory=dict)
    betting_data: Dict[str, Any] = field(default_factory=dict)

class BaseAPIClient(ABC):
    """Base class for all API clients"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = ""):
        self.api_key = api_key
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_delay = 1.0  # seconds between requests
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def fetch_games(self, week: int, season: int) -> List[GameData]:
        """Fetch games for a specific week and season"""
        pass
    
    @abstractmethod
    async def fetch_team_stats(self, team_id: str, season: int) -> Dict[str, Any]:
        """Fetch team statistics"""
        pass

class ESPNAPIClient(BaseAPIClient):
    """ESPN API client for game data and statistics"""
    
    def __init__(self):
        super().__init__(base_url="https://site.api.espn.com/apis/site/v2/sports/football/nfl")
    
    async def fetch_games(self, week: int, season: int) -> List[GameData]:
        """Fetch games from ESPN API"""
        try:
            url = f"{self.base_url}/scoreboard"
            params = {
                'seasontype': 2,  # Regular season
                'week': week,
                'season': season
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"ESPN API error: {response.status}")
                    return []
                
                data = await response.json()
                games = []
                
                for event in data.get('events', []):
                    game_data = self._parse_espn_game(event, week, season)
                    if game_data:
                        games.append(game_data)
                
                await asyncio.sleep(self.rate_limit_delay)
                return games
                
        except Exception as e:
            logger.error(f"ESPN API fetch error: {e}")
            return []
    
    def _parse_espn_game(self, event: Dict, week: int, season: int) -> Optional[GameData]:
        """Parse ESPN game data"""
        try:
            competitions = event.get('competitions', [])
            if not competitions:
                return None
                
            competition = competitions[0]
            competitors = competition.get('competitors', [])
            
            if len(competitors) != 2:
                return None
            
            home_team = away_team = None
            home_score = away_score = None
            
            for competitor in competitors:
                if competitor.get('homeAway') == 'home':
                    home_team = competitor['team']['abbreviation']
                    home_score = int(competitor.get('score', 0))
                else:
                    away_team = competitor['team']['abbreviation']
                    away_score = int(competitor.get('score', 0))
            
            game_date = datetime.fromisoformat(event['date'].replace('Z', '+00:00'))
            
            # Extract betting data if available
            betting_data = {}
            odds = competition.get('odds', [])
            if odds:
                betting_data = {
                    'spread': odds[0].get('spread'),
                    'total': odds[0].get('overUnder')
                }
            
            return GameData(
                game_id=event['id'],
                home_team=home_team,
                away_team=away_team,
                week=week,
                season=season,
                game_date=game_date,
                spread=betting_data.get('spread'),
                total=betting_data.get('total'),
                home_score=home_score,
                away_score=away_score,
                betting_data=betting_data
            )
            
        except Exception as e:
            logger.error(f"Error parsing ESPN game: {e}")
            return None
    
    async def fetch_team_stats(self, team_id: str, season: int) -> Dict[str, Any]:
        """Fetch team statistics from ESPN"""
        try:
            url = f"{self.base_url}/teams/{team_id}/statistics"
            params = {'season': season}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                await asyncio.sleep(self.rate_limit_delay)
                return data
                
        except Exception as e:
            logger.error(f"ESPN team stats error: {e}")
            return {}

class WeatherAPIClient(BaseAPIClient):
    """Weather API client for game conditions"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, base_url="https://api.openweathermap.org/data/2.5")
    
    async def fetch_weather_for_game(self, game_data: GameData, venue_location: Dict[str, float]) -> Dict[str, Any]:
        """Fetch weather data for a specific game"""
        try:
            lat = venue_location.get('lat')
            lon = venue_location.get('lon')
            
            if not lat or not lon:
                return {}
            
            # For historical games, use historical weather API
            if game_data.game_date < datetime.now():
                return await self._fetch_historical_weather(lat, lon, game_data.game_date)
            else:
                return await self._fetch_forecast_weather(lat, lon, game_data.game_date)
                
        except Exception as e:
            logger.error(f"Weather API error: {e}")
            return {}
    
    async def _fetch_historical_weather(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """Fetch historical weather data"""
        try:
            timestamp = int(date.timestamp())
            url = f"{self.base_url}/onecall/timemachine"
            params = {
                'lat': lat,
                'lon': lon,
                'dt': timestamp,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                current = data.get('current', {})
                
                return {
                    'temperature': current.get('temp'),
                    'humidity': current.get('humidity'),
                    'wind_speed': current.get('wind_speed'),
                    'wind_direction': current.get('wind_deg'),
                    'precipitation': current.get('rain', {}).get('1h', 0),
                    'conditions': current.get('weather', [{}])[0].get('main', '')
                }
                
        except Exception as e:
            logger.error(f"Historical weather error: {e}")
            return {}
    
    async def _fetch_forecast_weather(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """Fetch weather forecast"""
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'lat': lat,
                'lon': lon,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                
                # Find forecast closest to game time
                forecasts = data.get('list', [])
                target_timestamp = date.timestamp()
                
                closest_forecast = min(
                    forecasts,
                    key=lambda f: abs(f['dt'] - target_timestamp)
                )
                
                return {
                    'temperature': closest_forecast['main']['temp'],
                    'humidity': closest_forecast['main']['humidity'],
                    'wind_speed': closest_forecast['wind']['speed'],
                    'wind_direction': closest_forecast['wind'].get('deg'),
                    'precipitation': closest_forecast.get('rain', {}).get('3h', 0),
                    'conditions': closest_forecast['weather'][0]['main']
                }
                
        except Exception as e:
            logger.error(f"Forecast weather error: {e}")
            return {}

class InjuryReportClient(BaseAPIClient):
    """Mock injury report client - would integrate with real injury data source"""
    
    async def fetch_injury_report(self, team_id: str, week: int, season: int) -> List[Dict[str, Any]]:
        """Fetch injury report for a team"""
        try:
            # Mock injury data - replace with real API
            mock_injuries = [
                {
                    'player_name': 'John Doe',
                    'position': 'QB',
                    'injury_status': 'questionable',
                    'injury_type': 'shoulder',
                    'is_starter': True
                },
                {
                    'player_name': 'Jane Smith',
                    'position': 'RB',
                    'injury_status': 'out',
                    'injury_type': 'knee',
                    'is_starter': False
                }
            ]
            
            await asyncio.sleep(0.5)  # Simulate API delay
            return mock_injuries
            
        except Exception as e:
            logger.error(f"Injury report error: {e}")
            return []

class BettingOddsClient(BaseAPIClient):
    """Betting odds aggregation client"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, base_url="https://api.the-odds-api.com/v4")
    
    async def fetch_odds(self, game_id: str) -> Dict[str, Any]:
        """Fetch betting odds for a game"""
        try:
            url = f"{self.base_url}/sports/americanfootball_nfl/odds"
            params = {
                'apiKey': self.api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                
                # Find odds for specific game
                for game in data:
                    if game['id'] == game_id:
                        return self._parse_betting_odds(game)
                
                await asyncio.sleep(self.rate_limit_delay)
                return {}
                
        except Exception as e:
            logger.error(f"Betting odds error: {e}")
            return {}
    
    def _parse_betting_odds(self, game_data: Dict) -> Dict[str, Any]:
        """Parse betting odds data"""
        try:
            odds_data = {
                'moneyline': {},
                'spread': {},
                'total': {}
            }
            
            bookmakers = game_data.get('bookmakers', [])
            
            for bookmaker in bookmakers:
                for market in bookmaker.get('markets', []):
                    market_key = market['key']
                    
                    if market_key == 'h2h':
                        odds_data['moneyline'][bookmaker['title']] = {
                            outcome['name']: outcome['price']
                            for outcome in market['outcomes']
                        }
                    elif market_key == 'spreads':
                        odds_data['spread'][bookmaker['title']] = {
                            outcome['name']: {
                                'price': outcome['price'],
                                'point': outcome.get('point')
                            }
                            for outcome in market['outcomes']
                        }
                    elif market_key == 'totals':
                        odds_data['total'][bookmaker['title']] = {
                            outcome['name']: {
                                'price': outcome['price'],
                                'point': outcome.get('point')
                            }
                            for outcome in market['outcomes']
                        }
            
            return odds_data
            
        except Exception as e:
            logger.error(f"Error parsing betting odds: {e}")
            return {}

class EnhancedDataPipeline:
    """Orchestrates multiple API clients for comprehensive data collection"""
    
    def __init__(self, weather_api_key: Optional[str] = None, odds_api_key: Optional[str] = None):
        self.espn_client = ESPNAPIClient()
        self.weather_client = WeatherAPIClient(weather_api_key) if weather_api_key else None
        self.injury_client = InjuryReportClient()
        self.odds_client = BettingOddsClient(odds_api_key) if odds_api_key else None
        
        # NFL venue locations (simplified)
        self.venue_locations = {
            'KC': {'lat': 39.0489, 'lon': -94.4839},  # Arrowhead Stadium
            'BUF': {'lat': 42.7738, 'lon': -78.7870},  # Highmark Stadium
            'NE': {'lat': 42.0909, 'lon': -71.2643},   # Gillette Stadium
            # Add more venues as needed
        }
    
    async def collect_comprehensive_data(self, week: int, season: int) -> List[GameData]:
        """Collect comprehensive data from all sources"""
        try:
            enhanced_games = []
            
            # Start with ESPN game data
            async with self.espn_client:
                games = await self.espn_client.fetch_games(week, season)
            
            # Enhance each game with additional data
            for game in games:
                enhanced_game = await self._enhance_game_data(game)
                enhanced_games.append(enhanced_game)
            
            logger.info(f"Collected comprehensive data for {len(enhanced_games)} games")
            return enhanced_games
            
        except Exception as e:
            logger.error(f"Data collection error: {e}")
            return []
    
    async def _enhance_game_data(self, game: GameData) -> GameData:
        """Enhance game data with additional sources"""
        try:
            # Collect data from multiple sources concurrently
            tasks = []
            
            # Weather data
            if self.weather_client and game.home_team in self.venue_locations:
                tasks.append(self._fetch_weather_data(game))
            
            # Injury reports
            tasks.append(self._fetch_injury_data(game))
            
            # Betting odds
            if self.odds_client:
                tasks.append(self._fetch_odds_data(game))
            
            # Team statistics
            tasks.append(self._fetch_team_stats(game))
            
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, dict) and not isinstance(result, Exception):
                    if 'weather' in result:
                        game.weather = result['weather']
                    elif 'injuries' in result:
                        game.injuries = result['injuries']
                    elif 'betting_data' in result:
                        game.betting_data.update(result['betting_data'])
                    elif 'team_stats' in result:
                        game.team_stats = result['team_stats']
            
            return game
            
        except Exception as e:
            logger.error(f"Error enhancing game data: {e}")
            return game
    
    async def _fetch_weather_data(self, game: GameData) -> Dict[str, Any]:
        """Fetch weather data for game"""
        try:
            if not self.weather_client:
                return {}
            
            venue_location = self.venue_locations.get(game.home_team)
            if not venue_location:
                return {}
            
            async with self.weather_client:
                weather_data = await self.weather_client.fetch_weather_for_game(game, venue_location)
                return {'weather': weather_data}
                
        except Exception as e:
            logger.error(f"Weather fetch error: {e}")
            return {}
    
    async def _fetch_injury_data(self, game: GameData) -> Dict[str, Any]:
        """Fetch injury data for both teams"""
        try:
            async with self.injury_client:
                home_injuries = await self.injury_client.fetch_injury_report(
                    game.home_team, game.week, game.season
                )
                away_injuries = await self.injury_client.fetch_injury_report(
                    game.away_team, game.week, game.season
                )
                
                return {
                    'injuries': {
                        'home': home_injuries,
                        'away': away_injuries
                    }
                }
                
        except Exception as e:
            logger.error(f"Injury fetch error: {e}")
            return {}
    
    async def _fetch_odds_data(self, game: GameData) -> Dict[str, Any]:
        """Fetch betting odds data"""
        try:
            if not self.odds_client:
                return {}
            
            async with self.odds_client:
                odds_data = await self.odds_client.fetch_odds(game.game_id)
                return {'betting_data': odds_data}
                
        except Exception as e:
            logger.error(f"Odds fetch error: {e}")
            return {}
    
    async def _fetch_team_stats(self, game: GameData) -> Dict[str, Any]:
        """Fetch team statistics"""
        try:
            async with self.espn_client:
                home_stats = await self.espn_client.fetch_team_stats(game.home_team, game.season)
                away_stats = await self.espn_client.fetch_team_stats(game.away_team, game.season)
                
                return {
                    'team_stats': {
                        'home': home_stats,
                        'away': away_stats
                    }
                }
                
        except Exception as e:
            logger.error(f"Team stats fetch error: {e}")
            return {}

# Usage example
async def test_enhanced_pipeline():
    """Test the enhanced data pipeline"""
    try = EnhancedDataPipeline()
        
        # Collect data for current week
        games = await pipeline.collect_comprehensive_data(week=1, season=2024)
        
        print(f"Collected {len(games)} games with enhanced data")
        
        for game in games[:1]:  # Show first game
            print(f"\nGame: {game.away_team} @ {game.home_team}")
            print(f"Weather: {game.weather}")
            print(f"Injuries: {len(game.injuries.get('home', []))} home, {len(game.injuries.get('away', []))} away")
            print(f"Betting data available: {bool(game.betting_data)}")
        
        return True
        
    except Exception as e:
        print(f"Pipeline test failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_enhanced_pipeline())