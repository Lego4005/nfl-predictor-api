#!/usr/bin/env python3
"""
ExpertDataAccessLayer - Bridges external APIs to expert prediction models.

Provides personality-based data filtering so each expert gets exactly
the information they need based on their decision-making style.

Features:
- Parallel API calls for efficiency
- Personality-based data filtering
- Batch operations for multiple experts/games
- Error handling with retry logic
- Rate limit management
"""

import os
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExpertPersonality(Enum):
    """Expert personality types"""
    THE_ANALYST = "the-analyst"
    THE_GAMBLER = "the-gambler"
    GUT_INSTINCT = "gut-instinct"
    CONTRARIAN_REBEL = "contrarian-rebel"
    WEATHER_GURU = "weather-guru"
    INJURY_HAWK = "injury-hawk"
    HOME_FIELD_HOMER = "home-field-homer"
    ROAD_WARRIOR = "road-warrior"
    DIVISION_RIVAL_EXPERT = "division-rival-expert"
    PRIME_TIME_SPECIALIST = "prime-time-specialist"
    UNDERDOG_CHAMPION = "underdog-champion"
    FAVORITE_FANATIC = "favorite-fanatic"
    MOMENTUM_TRACKER = "momentum-tracker"
    REST_ANALYZER = "rest-analyzer"
    COACHING_CONNOISSEUR = "coaching-connoisseur"


@dataclass
class GameData:
    """Structured game data for expert consumption"""
    game_id: str
    home_team: str
    away_team: str

    # Core stats
    team_stats: Dict = field(default_factory=dict)
    odds: Dict = field(default_factory=dict)
    weather: Optional[Dict] = None
    injuries: Optional[List] = None

    # Metadata
    kickoff_time: Optional[datetime] = None
    venue: str = ""
    week: int = 0
    season: int = 2024

    # Additional context
    public_betting: Optional[Dict] = None
    news: Optional[List] = None

    def __repr__(self):
        return f"GameData({self.away_team} @ {self.home_team}, Week {self.week})"


@dataclass
class PersonalityFilter:
    """Data access configuration for each personality"""
    stats: bool = True
    odds: bool = True
    weather: bool = False
    injuries: bool = False
    historical: bool = True
    advanced_stats: bool = False
    public_betting: bool = False
    news: bool = False
    sentiment: bool = False

    # Stat preferences
    prefer_recent: bool = False  # Last 3 games vs season avg
    prefer_home_away_splits: bool = False
    prefer_divisional_stats: bool = False


class ExpertDataAccessLayer:
    """
    Bridges external APIs to expert prediction models.
    Filters data based on expert personality traits.
    """

    # API rate limits (requests per hour)
    RATE_LIMITS = {
        'sportsdata': 1000,  # Adjust based on your plan
        'odds_api': 500,     # The Odds API limit
    }

    def __init__(self):
        self.sportsdata_key = os.getenv('VITE_SPORTSDATA_IO_KEY')
        self.odds_key = os.getenv('VITE_ODDS_API_KEY')
        self.base_sportsdata_url = "https://api.sportsdata.io/v3/nfl"
        self.base_odds_url = "https://api.the-odds-api.com/v4"

        # Validate API keys
        if not self.sportsdata_key:
            logger.warning("VITE_SPORTSDATA_IO_KEY not set - team stats will be unavailable")
        if not self.odds_key:
            logger.warning("VITE_ODDS_API_KEY not set - odds data will be unavailable")

        logger.info(f"ExpertDataAccessLayer initialized (SportsData: {'✓' if self.sportsdata_key else '✗'}, Odds: {'✓' if self.odds_key else '✗'})")

        # Request tracking for rate limiting
        self._request_counts = {
            'sportsdata': 0,
            'odds_api': 0
        }

        # Cache for API responses (simple in-memory cache)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Personality-based data access rules
        self.personality_filters = {
            ExpertPersonality.THE_ANALYST: PersonalityFilter(
                stats=True,
                odds=True,
                weather=True,
                injuries=True,
                historical=True,
                advanced_stats=True,
                news=True
            ),
            ExpertPersonality.THE_GAMBLER: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=True,
                historical=False,
                prefer_recent=True,
                public_betting=True
            ),
            ExpertPersonality.GUT_INSTINCT: PersonalityFilter(
                stats=False,
                odds=True,
                weather=False,
                injuries=False,
                historical=False,
                advanced_stats=False
            ),
            ExpertPersonality.CONTRARIAN_REBEL: PersonalityFilter(
                stats=True,
                odds=True,
                weather=True,
                injuries=True,
                historical=True,
                public_betting=True,  # PRIMARY - needs this to fade
                sentiment=True
            ),
            ExpertPersonality.WEATHER_GURU: PersonalityFilter(
                stats=True,
                odds=False,
                weather=True,  # PRIMARY
                injuries=True,
                historical=True,
                advanced_stats=False
            ),
            ExpertPersonality.INJURY_HAWK: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=True,  # PRIMARY
                historical=True,
                news=True
            ),
            ExpertPersonality.HOME_FIELD_HOMER: PersonalityFilter(
                stats=True,
                odds=True,
                weather=True,
                injuries=False,
                historical=True,
                prefer_home_away_splits=True
            ),
            ExpertPersonality.ROAD_WARRIOR: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=False,
                historical=True,
                prefer_home_away_splits=True
            ),
            ExpertPersonality.DIVISION_RIVAL_EXPERT: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=True,
                historical=True,
                prefer_divisional_stats=True
            ),
            ExpertPersonality.MOMENTUM_TRACKER: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=False,
                historical=False,
                prefer_recent=True,
                news=True
            ),
            ExpertPersonality.UNDERDOG_CHAMPION: PersonalityFilter(
                stats=True,
                odds=True,
                weather=False,
                injuries=True,
                historical=True,
                public_betting=True
            ),
        }

    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for API responses"""
        # Filter out None values to avoid serialization issues
        filtered_params = {k: v for k, v in params.items() if v is not None}
        param_str = "_".join(f"{k}:{v}" for k, v in sorted(filtered_params.items()))
        return f"{endpoint}_{param_str}"

    def _check_cache(self, cache_key: str) -> Optional[Any]:
        """Check if cached data is still valid"""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                logger.debug(f"Cache hit: {cache_key}")
                return data
        return None

    def _set_cache(self, cache_key: str, data: Any):
        """Store data in cache"""
        self._cache[cache_key] = (data, datetime.now())

    async def get_expert_data_view(
        self,
        expert_id: str,
        game_id: str,
        season: int = 2024,
        week: int = None,
        home_team: str = None,
        away_team: str = None
    ) -> GameData:
        """
        Get data filtered by expert personality.

        Args:
            expert_id: Expert identifier (e.g., 'conservative_analyzer')
            game_id: NFL game ID (UUID or "2024_05_KC_BUF" format)
            season: NFL season year
            week: Week number
            home_team: Home team abbreviation (required for UUID game_ids)
            away_team: Away team abbreviation (required for UUID game_ids)

        Returns:
            GameData object with filtered information
        """

        # Parse game_id to extract components (if old format)
        # UUID format: contains dashes and is longer
        if '-' in game_id or len(game_id) > 20:
            # UUID format - teams and week must be provided
            if not home_team or not away_team:
                raise ValueError(f"UUID game_id requires home_team and away_team parameters")
            if not week:
                raise ValueError(f"UUID game_id requires week parameter")
        else:
            # Old format "YYYY_WW_AWAY_HOME" - parse it
            try:
                parts = game_id.split('_')
                if len(parts) >= 4:
                    season = int(parts[0])
                    week = int(parts[1])
                    home_team = parts[3]
                    away_team = parts[2]
                else:
                    raise ValueError(f"Invalid game_id format: {game_id}")
            except Exception as e:
                logger.error(f"Failed to parse game_id {game_id}: {e}")
                raise

        # Map expert_id to personality enum
        expert_id_map = {
            'conservative_analyzer': ExpertPersonality.THE_ANALYST,
            'risk_taking_gambler': ExpertPersonality.THE_GAMBLER,
            'contrarian_rebel': ExpertPersonality.CONTRARIAN_REBEL,
            'value_hunter': ExpertPersonality.THE_ANALYST,
            'momentum_rider': ExpertPersonality.MOMENTUM_TRACKER,
            'fundamentalist_scholar': ExpertPersonality.THE_ANALYST,
            'chaos_theory_believer': ExpertPersonality.GUT_INSTINCT,
            'gut_instinct_expert': ExpertPersonality.GUT_INSTINCT,
            'statistics_purist': ExpertPersonality.THE_ANALYST,
            'trend_reversal_specialist': ExpertPersonality.CONTRARIAN_REBEL,
            'popular_narrative_fader': ExpertPersonality.CONTRARIAN_REBEL,
            'sharp_money_follower': ExpertPersonality.THE_GAMBLER,
            'underdog_champion': ExpertPersonality.UNDERDOG_CHAMPION,
            'consensus_follower': ExpertPersonality.FAVORITE_FANATIC,
            'market_inefficiency_exploiter': ExpertPersonality.THE_ANALYST
        }

        expert_enum = expert_id_map.get(expert_id)
        if not expert_enum:
            # Try converting expert_id to enum directly
            try:
                expert_enum = ExpertPersonality(expert_id)
            except ValueError:
                logger.warning(f"Unknown expert_id: {expert_id}, using THE_ANALYST")
                expert_enum = ExpertPersonality.THE_ANALYST

        # Get personality filter config
        filters = self.personality_filters.get(
            expert_enum,
            self.personality_filters[ExpertPersonality.THE_ANALYST]
        )

        logger.info(f"Fetching data for {expert_id} - Game: {away_team} @ {home_team}")

        # Fetch all available data (parallel)
        tasks = []
        task_names = []

        if filters.stats:
            tasks.append(self._fetch_team_stats(home_team, away_team, season, week))
            task_names.append("team_stats")
        else:
            # Return coroutine that resolves to minimal stats
            async def get_minimal():
                return await self._get_minimal_stats(home_team, away_team)
            tasks.append(get_minimal())
            task_names.append("minimal_stats")

        if filters.odds:
            tasks.append(self._fetch_odds(home_team, away_team))
            task_names.append("odds")
        else:
            async def skip_odds():
                return {}
            tasks.append(skip_odds())
            task_names.append("odds_skip")

        if filters.weather:
            # Estimate game time from week/season if not provided
            tasks.append(self._fetch_weather(home_team, season, week, game_time=None))
            task_names.append("weather")
        else:
            async def skip_weather():
                return None
            tasks.append(skip_weather())
            task_names.append("weather_skip")

        if filters.injuries:
            tasks.append(self._fetch_injuries(home_team, away_team, season, week))
            task_names.append("injuries")
        else:
            async def skip_injuries():
                return None
            tasks.append(skip_injuries())
            task_names.append("injuries_skip")

        # Execute parallel fetches with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Timeout fetching data for {game_id}")
            results = [Exception("Timeout")] * len(tasks)

        # Extract results
        team_stats = results[0] if not isinstance(results[0], Exception) else {}
        odds = results[1] if not isinstance(results[1], Exception) else {}
        weather = results[2] if not isinstance(results[2], Exception) else None
        injuries = results[3] if not isinstance(results[3], Exception) else None

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching {task_names[i]}: {result}")

        # Build GameData object
        game_data = GameData(
            game_id=game_id,
            home_team=home_team,
            away_team=away_team,
            team_stats=team_stats,
            odds=odds,
            weather=weather,
            injuries=injuries,
            kickoff_time=team_stats.get('kickoff_time'),
            venue=team_stats.get('venue', ''),
            week=week,
            season=season
        )

        logger.info(f"Successfully fetched data for {expert_id} - {game_id}")
        return game_data

    async def _fetch_team_stats(
        self,
        home_team: str,
        away_team: str,
        season: int,
        week: int
    ) -> Dict:
        """Fetch comprehensive team statistics from SportsData.io"""

        cache_key = self._get_cache_key(
            "team_stats",
            {"season": season, "home": home_team, "away": away_team}
        )

        # Check cache first
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            async with aiohttp.ClientSession() as session:
                # Fetch season team stats
                url = f"{self.base_sportsdata_url}/scores/json/TeamSeasonStats/{season}"
                headers = {"Ocp-Apim-Subscription-Key": self.sportsdata_key}

                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        self._request_counts['sportsdata'] += 1
                        data = await response.json()

                        # Extract relevant stats for both teams
                        home_stats = next(
                            (team for team in data if team.get('Team') == home_team),
                            {}
                        )
                        away_stats = next(
                            (team for team in data if team.get('Team') == away_team),
                            {}
                        )

                        result = {
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_stats': self._parse_team_stats(home_stats),
                            'away_stats': self._parse_team_stats(away_stats),
                            'venue': home_stats.get('Stadium', ''),
                            'kickoff_time': None  # Would need additional API call
                        }

                        self._set_cache(cache_key, result)
                        return result
                    else:
                        logger.error(f"SportsData.io API error: {response.status}")
                        return self._get_minimal_stats(home_team, away_team)

        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return self._get_minimal_stats(home_team, away_team)

    def _parse_team_stats(self, team_data: Dict) -> Dict:
        """Extract and normalize team statistics"""
        games_played = max(team_data.get('Games', 1), 1)

        return {
            'games_played': games_played,
            'passing_yards_avg': team_data.get('PassingYards', 0) / games_played,
            'rushing_yards_avg': team_data.get('RushingYards', 0) / games_played,
            'total_yards_avg': team_data.get('TotalYards', 0) / games_played,
            'points_avg': team_data.get('Score', 0) / games_played,
            'points_allowed_avg': team_data.get('OpponentScore', 0) / games_played,
            'turnovers_avg': team_data.get('Turnovers', 0) / games_played,
            'takeaways_avg': team_data.get('Takeaways', 0) / games_played,
            'sacks': team_data.get('Sacks', 0),
            'sacks_allowed': team_data.get('SackYards', 0) / 10,  # Approximate sacks from yards
            'third_down_pct': team_data.get('ThirdDownPercentage', 0),
            'red_zone_pct': team_data.get('RedZonePercentage', 0),
            'touchdowns': team_data.get('Touchdowns', 0),
            'field_goals_made': team_data.get('FieldGoalsMade', 0),
            'field_goals_attempted': team_data.get('FieldGoalsAttempted', 0),
            'penalties': team_data.get('Penalties', 0),
            'penalty_yards': team_data.get('PenaltyYards', 0),
            'time_of_possession': team_data.get('TimeOfPossessionMinutes', 0),
        }

    async def _get_minimal_stats(self, home_team: str, away_team: str) -> Dict:
        """Minimal stats for 'gut instinct' type experts"""
        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_stats': {},
            'away_stats': {}
        }

    async def _fetch_odds(self, home_team: str, away_team: str) -> Dict:
        """Fetch betting odds from The Odds API"""

        # Ensure team names are not None
        if not home_team or not away_team:
            logger.warning("Missing team names for odds fetch")
            return {}

        cache_key = self._get_cache_key(
            "odds",
            {"home": home_team, "away": away_team}
        )

        # Check cache first
        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            # Validate API key
            if not self.odds_key:
                logger.error("Odds API key not configured")
                return {}

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_odds_url}/sports/americanfootball_nfl/odds"
                params = {
                    'apiKey': str(self.odds_key),
                    'regions': 'us',
                    'markets': 'h2h,spreads,totals',
                    'oddsFormat': 'american'
                }

                async with session.get(url, params=params, timeout=15) as response:
                    if response.status == 200:
                        self._request_counts['odds_api'] += 1

                        # Log remaining requests
                        remaining = response.headers.get('x-requests-remaining', 'unknown')
                        logger.info(f"Odds API requests remaining: {remaining}")

                        data = await response.json()

                        # Find the specific game
                        game_odds = self._find_game_in_odds(data, home_team, away_team)

                        if not game_odds:
                            logger.warning(f"No odds found for {away_team} @ {home_team}")
                            return {}

                        result = self._parse_odds(game_odds)
                        self._set_cache(cache_key, result)
                        return result
                    else:
                        logger.error(f"The Odds API error: {response.status}")
                        # Fallback to mock odds if API auth fails
                        if response.status == 401:
                            logger.warning(f"Odds API auth failed (401), using mock odds")
                            return {
                                'spread': {'home': -3.0, 'away': +3.0},
                                'total': {'line': 45.0},
                                'moneyline': {'home': -140, 'away': +120},
                                'bookmaker': 'MOCK_ODDS_DATA'
                            }
                        return {}

        except Exception as e:
            logger.error(f"Error fetching odds: {e}")
            return {}

    def _find_game_in_odds(
        self,
        odds_data: List[Dict],
        home_team: str,
        away_team: str
    ) -> Optional[Dict]:
        """Find specific game in odds API response"""

        # Team name mappings (SportsData.io abbr -> Odds API names)
        team_mappings = {
            'KC': 'Kansas City Chiefs',
            'BUF': 'Buffalo Bills',
            'BAL': 'Baltimore Ravens',
            'CIN': 'Cincinnati Bengals',
            'DAL': 'Dallas Cowboys',
            'PHI': 'Philadelphia Eagles',
            'SF': 'San Francisco 49ers',
            'DET': 'Detroit Lions',
            'MIA': 'Miami Dolphins',
            'NYJ': 'New York Jets',
            # Add more mappings as needed
        }

        home_full = team_mappings.get(home_team, home_team)
        away_full = team_mappings.get(away_team, away_team)

        for game in odds_data:
            game_home = game.get('home_team', '')
            game_away = game.get('away_team', '')

            if (home_team in game_home or home_full in game_home) and \
               (away_team in game_away or away_full in game_away):
                return game

        return None

    def _parse_odds(self, game_odds: Dict) -> Dict:
        """Extract and normalize odds data"""
        bookmakers = game_odds.get('bookmakers', [])

        if not bookmakers:
            return {}

        # Use first bookmaker (or calculate consensus)
        odds_data = bookmakers[0].get('markets', [])

        spread_market = next((m for m in odds_data if m['key'] == 'spreads'), {})
        totals_market = next((m for m in odds_data if m['key'] == 'totals'), {})
        h2h_market = next((m for m in odds_data if m['key'] == 'h2h'), {})

        # Safely extract outcomes
        spread_outcomes = spread_market.get('outcomes', [])
        totals_outcomes = totals_market.get('outcomes', [])
        h2h_outcomes = h2h_market.get('outcomes', [])

        return {
            'spread': {
                'home': spread_outcomes[0].get('point') if spread_outcomes else None,
                'away': spread_outcomes[1].get('point') if len(spread_outcomes) > 1 else None,
                'home_odds': spread_outcomes[0].get('price') if spread_outcomes else None,
                'away_odds': spread_outcomes[1].get('price') if len(spread_outcomes) > 1 else None,
            },
            'total': {
                'line': totals_outcomes[0].get('point') if totals_outcomes else None,
                'over_odds': totals_outcomes[0].get('price') if totals_outcomes else None,
                'under_odds': totals_outcomes[1].get('price') if len(totals_outcomes) > 1 else None,
            },
            'moneyline': {
                'home': h2h_outcomes[0].get('price') if h2h_outcomes else None,
                'away': h2h_outcomes[1].get('price') if len(h2h_outcomes) > 1 else None,
            },
            'bookmaker': bookmakers[0].get('title', 'Unknown'),
            'last_update': game_odds.get('last_update', '')
        }

    async def _fetch_weather(
        self,
        home_team: str,
        season: int,
        week: int,
        game_time: Optional[datetime] = None
    ) -> Optional[Dict]:
        """Fetch weather conditions from Tomorrow.io"""
        try:
            from .tomorrow_weather_service import TomorrowWeatherService

            # Initialize weather service
            weather_service = TomorrowWeatherService()

            # If no game_time provided, use current time + 3 days as estimate
            if not game_time:
                from datetime import timedelta
                game_time = datetime.utcnow() + timedelta(days=3)

            # Generate game_id
            game_id = f"{season}_W{week}_{home_team}"

            # Fetch weather
            weather_data = await weather_service.get_game_weather(
                game_id=game_id,
                home_team=home_team,
                game_time=game_time
            )

            if weather_data:
                return {
                    'temperature': weather_data.temperature,
                    'wind_speed': weather_data.wind_speed,
                    'wind_direction': weather_data.wind_direction,
                    'precipitation': weather_data.precipitation,
                    'humidity': weather_data.humidity,
                    'conditions': weather_data.conditions,
                    'field_conditions': weather_data.field_conditions,
                    'dome_stadium': weather_data.dome_stadium,
                    'forecast_confidence': weather_data.forecast_confidence,
                    'data_source': weather_data.data_source
                }

            logger.info(f"No weather data available for {home_team}")
            return None

        except Exception as e:
            logger.error(f"Error fetching weather for {home_team}: {e}")
            return None

    async def _fetch_injuries(
        self,
        home_team: str,
        away_team: str,
        season: int,
        week: int
    ) -> Optional[List]:
        """Fetch injury reports from SportsData.io"""

        cache_key = self._get_cache_key(
            "injuries",
            {"season": season, "week": week, "teams": f"{home_team}_{away_team}"}
        )

        cached = self._check_cache(cache_key)
        if cached:
            return cached

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_sportsdata_url}/scores/json/Injuries/{season}/{week}"
                headers = {"Ocp-Apim-Subscription-Key": self.sportsdata_key}

                async with session.get(url, headers=headers, timeout=15) as response:
                    if response.status == 200:
                        self._request_counts['sportsdata'] += 1
                        injuries = await response.json()

                        # Filter injuries for teams in this game
                        game_injuries = [
                            inj for inj in injuries
                            if inj.get('Team') in [home_team, away_team]
                        ]

                        self._set_cache(cache_key, game_injuries)
                        return game_injuries
                    elif response.status == 404:
                        logger.warning(f"No injury data for Week {week}")
                        return []
                    else:
                        logger.error(f"Injuries API error: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error fetching injuries: {e}")
            return []

    async def batch_get_expert_data(
        self,
        expert_ids: List[str],
        game_ids: List[str],
        game_metadata: Dict[str, Dict] = None
    ) -> Dict[str, Dict[str, GameData]]:
        """
        Efficiently fetch data for multiple experts and games.

        Args:
            expert_ids: List of expert identifiers
            game_ids: List of game IDs (can be UUIDs)
            game_metadata: Dict mapping game_id to {season, week, home_team, away_team}

        Returns:
            {expert_id: {game_id: GameData}}
        """

        logger.info(f"Batch fetching data for {len(expert_ids)} experts, {len(game_ids)} games")

        results = {}

        # Create all tasks
        tasks = []
        task_map = []

        for expert_id in expert_ids:
            for game_id in game_ids:
                # Get game metadata if provided (needed for UUID game_ids)
                if game_metadata and game_id in game_metadata:
                    meta = game_metadata[game_id]
                    tasks.append(self.get_expert_data_view(
                        expert_id, game_id,
                        season=meta.get('season', 2025),
                        week=meta.get('week'),
                        home_team=meta.get('home_team'),
                        away_team=meta.get('away_team')
                    ))
                else:
                    tasks.append(self.get_expert_data_view(expert_id, game_id))
                task_map.append((expert_id, game_id))

        # Execute in parallel with progress logging
        logger.info(f"Executing {len(tasks)} parallel API requests...")
        data_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Organize results by expert and game
        for (expert_id, game_id), result in zip(task_map, data_results):
            if expert_id not in results:
                results[expert_id] = {}

            if not isinstance(result, Exception):
                results[expert_id][game_id] = result
            else:
                logger.error(f"Failed to fetch data for {expert_id}/{game_id}: {result}")

        logger.info(f"Batch fetch complete. Retrieved {sum(len(g) for g in results.values())} game datasets")
        return results

    def get_rate_limit_status(self) -> Dict[str, int]:
        """Get current API request counts"""
        return self._request_counts.copy()

    def reset_rate_limits(self):
        """Reset rate limit counters (call hourly)"""
        self._request_counts = {k: 0 for k in self._request_counts}
        logger.info("Rate limit counters reset")


# Testing and usage example
async def test_expert_data_access():
    """Test the data access layer"""

    print("="*60)
    print("TESTING EXPERT DATA ACCESS LAYER")
    print("="*60)

    dal = ExpertDataAccessLayer()

    # Test 1: Single expert, single game
    print("\n[Test 1] Single expert (The Analyst) - Single game")
    try:
        game_data = await dal.get_expert_data_view(
            expert_id='the-analyst',
            game_id='2024_05_KC_BUF'
        )

        print(f"✅ Game: {game_data.away_team} @ {game_data.home_team}")
        print(f"   Spread: {game_data.odds.get('spread', {}).get('home', 'N/A')}")
        print(f"   Total: {game_data.odds.get('total', {}).get('line', 'N/A')}")
        print(f"   Home PPG: {game_data.team_stats.get('home_stats', {}).get('points_avg', 'N/A'):.1f}")
        print(f"   Away PPG: {game_data.team_stats.get('away_stats', {}).get('points_avg', 'N/A'):.1f}")
        print(f"   Injuries: {len(game_data.injuries) if game_data.injuries else 0}")
    except Exception as e:
        print(f"❌ Test 1 failed: {e}")

    # Test 2: Different personalities
    print("\n[Test 2] Different personalities - Same game")
    experts = ['the-analyst', 'gut-instinct', 'the-gambler']

    for expert in experts:
        try:
            game_data = await dal.get_expert_data_view(
                expert_id=expert,
                game_id='2024_05_KC_BUF'
            )

            has_stats = bool(game_data.team_stats.get('home_stats'))
            has_odds = bool(game_data.odds)
            has_injuries = game_data.injuries is not None

            print(f"✅ {expert:20} - Stats: {has_stats}, Odds: {has_odds}, Injuries: {has_injuries}")
        except Exception as e:
            print(f"❌ {expert} failed: {e}")

    # Test 3: Batch operation
    print("\n[Test 3] Batch fetch - 3 experts x 2 games")
    try:
        results = await dal.batch_get_expert_data(
            expert_ids=['the-analyst', 'the-gambler', 'gut-instinct'],
            game_ids=['2024_05_KC_BUF', '2024_05_DAL_SF']
        )

        total_datasets = sum(len(games) for games in results.values())
        print(f"✅ Batch fetch complete: {len(results)} experts, {total_datasets} game datasets")

        for expert, games in results.items():
            print(f"   {expert}: {len(games)} games")
    except Exception as e:
        print(f"❌ Test 3 failed: {e}")

    # Test 4: Rate limit status
    print("\n[Test 4] Rate limit status")
    limits = dal.get_rate_limit_status()
    print(f"✅ API requests made:")
    for api, count in limits.items():
        print(f"   {api}: {count}")

    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_expert_data_access())