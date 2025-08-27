"""
Live Data Manager
Manages real NFL data integration with paid APIs as primary sources and public APIs as fallbacks
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
import os
from enum import Enum

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """Data source priority levels"""
    PRIMARY_PAID = "primary_paid"
    SECONDARY_PAID = "secondary_paid"
    PUBLIC_FALLBACK = "public_fallback"
    CACHED = "cached"

class DataType(Enum):
    """Types of NFL data"""
    GAMES = "games"
    ODDS = "odds"
    PLAYER_PROPS = "player_props"
    FANTASY = "fantasy"
    INJURIES = "injuries"
    WEATHER = "weather"

@dataclass
class APIResponse:
    """Standardized API response wrapper"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    source: Optional[DataSource] = None
    timestamp: Optional[datetime] = None
    cached: bool = False
    rate_limit_remaining: Optional[int] = None

class LiveDataManager:
    """
    Manages live NFL data integration with intelligent source prioritization
    Primary: Paid APIs (SportsData.io, The Odds API, RapidAPI)
    Fallback: Public APIs (ESPN, NFL.com)
    """
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        
        # API Configuration - Paid APIs First
        self.api_configs = {
            # PRIMARY PAID APIS
            'sportsdata_io': {
                'base_url': 'https://api.sportsdata.io/v3/nfl',
                'key': os.getenv('SPORTSDATA_IO_KEY'),
                'priority': 1,
                'source': DataSource.PRIMARY_PAID,
                'rate_limit': 1000,  # requests per month
                'supports': [DataType.GAMES, DataType.PLAYER_PROPS, DataType.FANTASY, DataType.INJURIES]
            },
            'odds_api': {
                'base_url': 'https://api.the-odds-api.com/v4',
                'key': os.getenv('ODDS_API_KEY'),
                'priority': 1,
                'source': DataSource.PRIMARY_PAID,
                'rate_limit': 500,  # requests per month
                'supports': [DataType.ODDS]
            },
            'rapid_api': {
                'base_url': 'https://api-american-football.p.rapidapi.com',
                'key': os.getenv('RAPID_API_KEY'),
                'priority': 2,
                'source': DataSource.SECONDARY_PAID,
                'rate_limit': 1000,  # requests per month
                'supports': [DataType.GAMES, DataType.ODDS, DataType.PLAYER_PROPS]
            },
            
            # PUBLIC FALLBACK APIS
            'espn': {
                'base_url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl',
                'key': None,  # No key required
                'priority': 3,
                'source': DataSource.PUBLIC_FALLBACK,
                'rate_limit': None,  # No official limit
                'supports': [DataType.GAMES, DataType.INJURIES]
            },
            'nfl_com': {
                'base_url': 'https://api.nfl.com/v1',
                'key': None,  # No key required
                'priority': 4,
                'source': DataSource.PUBLIC_FALLBACK,
                'rate_limit': None,  # No official limit
                'supports': [DataType.GAMES]
            }
        }
        
        # Cache for API responses
        self.cache = {}
        self.cache_ttl = {
            DataType.GAMES: 300,      # 5 minutes
            DataType.ODDS: 180,       # 3 minutes
            DataType.PLAYER_PROPS: 600,  # 10 minutes
            DataType.FANTASY: 3600,   # 1 hour
            DataType.INJURIES: 1800,  # 30 minutes
            DataType.WEATHER: 1800    # 30 minutes
        }
        
        # Track API usage and health
        self.api_health = {}
        self.api_usage = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'NFL-Predictor-API/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_live_data(self, data_type: DataType, week: int, season: int = 2024) -> APIResponse:
        """
        Get live NFL data with intelligent source prioritization
        """
        try:
            logger.info(f"🔍 Fetching {data_type.value} data for Week {week}, {season}")
            
            # Check cache first
            cache_key = f"{data_type.value}_{week}_{season}"
            cached_response = self._get_cached_response(cache_key, data_type)
            if cached_response:
                logger.info(f"📦 Using cached {data_type.value} data")
                return cached_response
            
            # Get prioritized API sources for this data type
            sources = self._get_prioritized_sources(data_type)
            
            # Try each source in priority order
            for api_name, config in sources:
                try:
                    logger.info(f"🎯 Trying {api_name} ({config['source'].value}) for {data_type.value}")
                    
                    # Check if API is healthy and within rate limits
                    if not self._is_api_healthy(api_name):
                        logger.warning(f"⚠️ Skipping unhealthy API: {api_name}")
                        continue
                    
                    # Make API call
                    response = await self._fetch_from_source(api_name, config, data_type, week, season)
                    
                    if response.success:
                        # Cache successful response
                        self._cache_response(cache_key, response, data_type)
                        
                        # Update API health
                        self._update_api_health(api_name, True)
                        
                        logger.info(f"✅ Successfully fetched {data_type.value} from {api_name}")
                        return response
                    else:
                        logger.warning(f"❌ Failed to fetch from {api_name}: {response.error}")
                        self._update_api_health(api_name, False)
                        
                except Exception as e:
                    logger.error(f"❌ Error with {api_name}: {e}")
                    self._update_api_health(api_name, False)
                    continue
            
            # All sources failed
            logger.error(f"❌ All sources failed for {data_type.value}")
            return APIResponse(
                success=False,
                error=f"All data sources failed for {data_type.value}",
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ Error in get_live_data: {e}")
            return APIResponse(
                success=False,
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    def _get_prioritized_sources(self, data_type: DataType) -> List[Tuple[str, Dict]]:
        """Get API sources that support the data type, sorted by priority"""
        sources = []
        
        for api_name, config in self.api_configs.items():
            if data_type in config['supports']:
                sources.append((api_name, config))
        
        # Sort by priority (lower number = higher priority)
        sources.sort(key=lambda x: x[1]['priority'])
        
        return sources
    
    async def _fetch_from_source(self, api_name: str, config: Dict, 
                                data_type: DataType, week: int, season: int) -> APIResponse:
        """Fetch data from a specific API source"""
        try:
            if api_name == 'sportsdata_io':
                return await self._fetch_sportsdata_io(config, data_type, week, season)
            elif api_name == 'odds_api':
                return await self._fetch_odds_api(config, data_type, week, season)
            elif api_name == 'rapid_api':
                return await self._fetch_rapid_api(config, data_type, week, season)
            elif api_name == 'espn':
                return await self._fetch_espn(config, data_type, week, season)
            elif api_name == 'nfl_com':
                return await self._fetch_nfl_com(config, data_type, week, season)
            else:
                return APIResponse(
                    success=False,
                    error=f"Unknown API source: {api_name}",
                    timestamp=datetime.utcnow()
                )
                
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"Error fetching from {api_name}: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def _fetch_sportsdata_io(self, config: Dict, data_type: DataType, 
                                  week: int, season: int) -> APIResponse:
        """Fetch data from SportsData.io (Primary Paid API)"""
        if not config['key']:
            return APIResponse(
                success=False,
                error="SportsData.io API key not configured",
                timestamp=datetime.utcnow()
            )
        
        try:
            base_url = config['base_url']
            api_key = config['key']
            
            # Build endpoint based on data type
            if data_type == DataType.GAMES:
                url = f"{base_url}/scores/json/ScoresByWeek/{season}REG/{week}?key={api_key}"
            elif data_type == DataType.PLAYER_PROPS:
                url = f"{base_url}/projections/json/PlayerGameProjectionStatsByWeek/{season}REG/{week}?key={api_key}"
            elif data_type == DataType.FANTASY:
                url = f"{base_url}/projections/json/DfsSlatesByWeek/{season}REG/{week}?key={api_key}"
            elif data_type == DataType.INJURIES:
                url = f"{base_url}/scores/json/Injuries/{season}REG/{week}?key={api_key}"
            else:
                return APIResponse(
                    success=False,
                    error=f"SportsData.io doesn't support {data_type.value}",
                    timestamp=datetime.utcnow()
                )
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Transform data to standard format
                    transformed_data = self._transform_sportsdata_response(data, data_type)
                    
                    return APIResponse(
                        success=True,
                        data=transformed_data,
                        source=config['source'],
                        timestamp=datetime.utcnow(),
                        rate_limit_remaining=response.headers.get('X-RateLimit-Remaining')
                    )
                else:
                    error_text = await response.text()
                    return APIResponse(
                        success=False,
                        error=f"SportsData.io API error {response.status}: {error_text}",
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"SportsData.io request failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def _fetch_odds_api(self, config: Dict, data_type: DataType, 
                             week: int, season: int) -> APIResponse:
        """Fetch data from The Odds API (Primary Paid API)"""
        if not config['key']:
            return APIResponse(
                success=False,
                error="The Odds API key not configured",
                timestamp=datetime.utcnow()
            )
        
        if data_type != DataType.ODDS:
            return APIResponse(
                success=False,
                error=f"The Odds API doesn't support {data_type.value}",
                timestamp=datetime.utcnow()
            )
        
        try:
            base_url = config['base_url']
            api_key = config['key']
            
            url = f"{base_url}/sports/americanfootball_nfl/odds"
            params = {
                'apiKey': api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Transform data to standard format
                    transformed_data = self._transform_odds_response(data, week)
                    
                    return APIResponse(
                        success=True,
                        data=transformed_data,
                        source=config['source'],
                        timestamp=datetime.utcnow(),
                        rate_limit_remaining=response.headers.get('X-Requests-Remaining')
                    )
                else:
                    error_text = await response.text()
                    return APIResponse(
                        success=False,
                        error=f"The Odds API error {response.status}: {error_text}",
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"The Odds API request failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    async def _fetch_espn(self, config: Dict, data_type: DataType, 
                         week: int, season: int) -> APIResponse:
        """Fetch data from ESPN (Public Fallback API)"""
        try:
            base_url = config['base_url']
            
            if data_type == DataType.GAMES:
                url = f"{base_url}/scoreboard"
                params = {
                    'seasontype': 2,  # Regular season
                    'week': week
                }
            elif data_type == DataType.INJURIES:
                url = f"{base_url}/teams"
                params = {}
            else:
                return APIResponse(
                    success=False,
                    error=f"ESPN API doesn't support {data_type.value}",
                    timestamp=datetime.utcnow()
                )
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Transform data to standard format
                    transformed_data = self._transform_espn_response(data, data_type)
                    
                    return APIResponse(
                        success=True,
                        data=transformed_data,
                        source=config['source'],
                        timestamp=datetime.utcnow()
                    )
                else:
                    error_text = await response.text()
                    return APIResponse(
                        success=False,
                        error=f"ESPN API error {response.status}: {error_text}",
                        timestamp=datetime.utcnow()
                    )
                    
        except Exception as e:
            return APIResponse(
                success=False,
                error=f"ESPN API request failed: {str(e)}",
                timestamp=datetime.utcnow()
            )
    
    def _transform_sportsdata_response(self, data: Any, data_type: DataType) -> Dict:
        """Transform SportsData.io response to standard format"""
        try:
            if data_type == DataType.GAMES:
                games = []
                for game in data:
                    games.append({
                        'game_id': game.get('GameKey'),
                        'home_team': game.get('HomeTeam'),
                        'away_team': game.get('AwayTeam'),
                        'home_score': game.get('HomeScore'),
                        'away_score': game.get('AwayScore'),
                        'status': game.get('Status'),
                        'date': game.get('DateTime'),
                        'week': game.get('Week'),
                        'season': game.get('Season')
                    })
                return {'games': games}
            
            elif data_type == DataType.PLAYER_PROPS:
                props = []
                for player in data:
                    props.append({
                        'player_id': player.get('PlayerID'),
                        'player_name': player.get('Name'),
                        'team': player.get('Team'),
                        'position': player.get('Position'),
                        'passing_yards': player.get('PassingYards'),
                        'rushing_yards': player.get('RushingYards'),
                        'receiving_yards': player.get('ReceivingYards'),
                        'receptions': player.get('Receptions'),
                        'touchdowns': player.get('Touchdowns')
                    })
                return {'player_props': props}
            
            return {'raw_data': data}
            
        except Exception as e:
            logger.error(f"Error transforming SportsData.io response: {e}")
            return {'raw_data': data}
    
    def _transform_odds_response(self, data: Any, week: int) -> Dict:
        """Transform The Odds API response to standard format"""
        try:
            games = []
            for game in data:
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                
                # Extract odds from bookmakers
                odds_data = {'spread': None, 'total': None, 'moneyline': None}
                
                for bookmaker in game.get('bookmakers', []):
                    for market in bookmaker.get('markets', []):
                        if market['key'] == 'spreads':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    odds_data['spread'] = {
                                        'home_spread': outcome.get('point'),
                                        'home_odds': outcome.get('price')
                                    }
                        elif market['key'] == 'totals':
                            odds_data['total'] = {
                                'total_line': market['outcomes'][0].get('point'),
                                'over_odds': market['outcomes'][0].get('price'),
                                'under_odds': market['outcomes'][1].get('price')
                            }
                        elif market['key'] == 'h2h':
                            for outcome in market['outcomes']:
                                if outcome['name'] == home_team:
                                    odds_data['moneyline'] = {
                                        'home_odds': outcome.get('price')
                                    }
                                elif outcome['name'] == away_team:
                                    if 'moneyline' not in odds_data:
                                        odds_data['moneyline'] = {}
                                    odds_data['moneyline']['away_odds'] = outcome.get('price')
                
                games.append({
                    'game_id': game.get('id'),
                    'home_team': home_team,
                    'away_team': away_team,
                    'commence_time': game.get('commence_time'),
                    'week': week,
                    'odds': odds_data
                })
            
            return {'odds': games}
            
        except Exception as e:
            logger.error(f"Error transforming Odds API response: {e}")
            return {'raw_data': data}
    
    def _transform_espn_response(self, data: Any, data_type: DataType) -> Dict:
        """Transform ESPN response to standard format"""
        try:
            if data_type == DataType.GAMES:
                games = []
                for event in data.get('events', []):
                    competition = event.get('competitions', [{}])[0]
                    competitors = competition.get('competitors', [])
                    
                    home_team = None
                    away_team = None
                    home_score = 0
                    away_score = 0
                    
                    for competitor in competitors:
                        if competitor.get('homeAway') == 'home':
                            home_team = competitor.get('team', {}).get('abbreviation')
                            home_score = int(competitor.get('score', 0))
                        else:
                            away_team = competitor.get('team', {}).get('abbreviation')
                            away_score = int(competitor.get('score', 0))
                    
                    games.append({
                        'game_id': event.get('id'),
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_score': home_score,
                        'away_score': away_score,
                        'status': event.get('status', {}).get('type', {}).get('name'),
                        'date': event.get('date'),
                        'week': event.get('week', {}).get('number')
                    })
                
                return {'games': games}
            
            return {'raw_data': data}
            
        except Exception as e:
            logger.error(f"Error transforming ESPN response: {e}")
            return {'raw_data': data}
    
    def _get_cached_response(self, cache_key: str, data_type: DataType) -> Optional[APIResponse]:
        """Get cached response if still valid"""
        if cache_key not in self.cache:
            return None
        
        cached_data, timestamp = self.cache[cache_key]
        ttl = self.cache_ttl.get(data_type, 300)
        
        if datetime.utcnow() - timestamp < timedelta(seconds=ttl):
            cached_data.cached = True
            return cached_data
        else:
            # Remove expired cache
            del self.cache[cache_key]
            return None
    
    def _cache_response(self, cache_key: str, response: APIResponse, data_type: DataType):
        """Cache API response"""
        self.cache[cache_key] = (response, datetime.utcnow())
        
        # Limit cache size
        if len(self.cache) > 100:
            # Remove oldest entries
            oldest_keys = sorted(self.cache.keys(), 
                               key=lambda k: self.cache[k][1])[:20]
            for key in oldest_keys:
                del self.cache[key]
    
    def _is_api_healthy(self, api_name: str) -> bool:
        """Check if API is healthy and within rate limits"""
        health = self.api_health.get(api_name, {'healthy': True, 'last_check': datetime.utcnow()})
        
        # If API failed recently, wait before retrying
        if not health['healthy']:
            time_since_failure = datetime.utcnow() - health['last_check']
            if time_since_failure < timedelta(minutes=5):
                return False
        
        return True
    
    def _update_api_health(self, api_name: str, success: bool):
        """Update API health status"""
        self.api_health[api_name] = {
            'healthy': success,
            'last_check': datetime.utcnow()
        }
    
    def get_api_status(self) -> Dict:
        """Get status of all APIs"""
        status = {}
        
        for api_name, config in self.api_configs.items():
            health = self.api_health.get(api_name, {'healthy': True, 'last_check': None})
            
            status[api_name] = {
                'source_type': config['source'].value,
                'priority': config['priority'],
                'healthy': health['healthy'],
                'last_check': health['last_check'].isoformat() if health['last_check'] else None,
                'supports': [dt.value for dt in config['supports']],
                'has_key': bool(config['key'])
            }
        
        return status

# Example usage
async def test_live_data_manager():
    """Test the live data manager"""
    async with LiveDataManager() as manager:
        # Test game data
        games_response = await manager.get_live_data(DataType.GAMES, week=13, season=2024)
        print(f"Games: {games_response.success}, Source: {games_response.source}")
        
        # Test odds data
        odds_response = await manager.get_live_data(DataType.ODDS, week=13, season=2024)
        print(f"Odds: {odds_response.success}, Source: {odds_response.source}")
        
        # Get API status
        status = manager.get_api_status()
        print(f"API Status: {status}")

if __name__ == "__main__":
    asyncio.run(test_live_data_manager())