"""
Weather Ingestion Service
Fetches weather data from OpenWeatherMap API for NFL game predictions.
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class WeatherData(BaseModel):
    """Weather data model matching database schema"""
    game_id: str
    temperature: Optional[float] = None  # Fahrenheit
    wind_speed: Optional[float] = None  # MPH
    wind_direction: Optional[str] = None
    precipitation: Optional[float] = None  # Inches
    humidity: Optional[float] = None  # Percentage
    conditions: Optional[str] = None
    field_conditions: Optional[str] = None
    dome_stadium: bool = False
    forecast_confidence: float = 0.0
    data_source: str = "OpenWeatherMap"
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    game_time: Optional[datetime] = None
    hours_before_game: Optional[int] = None


class WeatherIngestionService:
    """
    Service for fetching weather data from OpenWeatherMap API.

    Features:
    - Free tier: 1000 calls/day (enough for 12h, 4h, 1h before each game)
    - Converts metric to imperial units
    - Handles rate limits gracefully
    - Caches results to minimize API calls
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        supabase_client: Optional[Any] = None,
        redis_client: Optional[Any] = None
    ):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key (or from env var)
            supabase_client: Supabase client for database storage
            redis_client: Redis client for caching
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key is required")

        self.supabase = supabase_client
        self.redis = redis_client
        self.base_url = "https://api.openweathermap.org/data/2.5"
        self.call_count = 0
        self.max_daily_calls = 1000

        # Stadium locations (lat, lon)
        self.stadium_locations = self._load_stadium_locations()

    def _load_stadium_locations(self) -> Dict[str, tuple]:
        """Load NFL stadium coordinates"""
        return {
            "ARI": (33.5276, -112.2626),  # State Farm Stadium
            "ATL": (33.7554, -84.4008),    # Mercedes-Benz Stadium
            "BAL": (39.2780, -76.6227),    # M&T Bank Stadium
            "BUF": (42.7738, -78.7870),    # Highmark Stadium
            "CAR": (35.2258, -80.8528),    # Bank of America Stadium
            "CHI": (41.8623, -87.6167),    # Soldier Field
            "CIN": (39.0954, -84.5160),    # Paycor Stadium
            "CLE": (41.5061, -81.6995),    # Cleveland Browns Stadium
            "DAL": (32.7473, -97.0945),    # AT&T Stadium (dome)
            "DEN": (39.7439, -105.0201),   # Empower Field
            "DET": (42.3400, -83.0456),    # Ford Field (dome)
            "GB": (44.5013, -88.0622),     # Lambeau Field
            "HOU": (29.6847, -95.4107),    # NRG Stadium (retractable)
            "IND": (39.7601, -86.1639),    # Lucas Oil Stadium (retractable)
            "JAX": (30.3239, -81.6373),    # TIAA Bank Field
            "KC": (39.0489, -94.4839),     # ARROWHEAD Stadium
            "LAC": (33.8644, -118.3392),   # SoFi Stadium (indoor-outdoor)
            "LAR": (33.8644, -118.3392),   # SoFi Stadium
            "LV": (36.0909, -115.1833),    # Allegiant Stadium (dome)
            "MIA": (25.9580, -80.2389),    # Hard Rock Stadium
            "MIN": (44.9738, -93.2577),    # U.S. Bank Stadium (dome)
            "NE": (42.0909, -71.2643),     # Gillette Stadium
            "NO": (29.9511, -90.0812),     # Caesars Superdome (dome)
            "NYG": (40.8128, -74.0742),    # MetLife Stadium
            "NYJ": (40.8128, -74.0742),    # MetLife Stadium
            "PHI": (39.9008, -75.1675),    # Lincoln Financial Field
            "PIT": (40.4468, -80.0158),    # Acrisure Stadium
            "SF": (37.4030, -121.9700),    # Levi's Stadium
            "SEA": (47.5952, -122.3316),   # Lumen Field
            "TB": (27.9759, -82.5033),     # Raymond James Stadium
            "TEN": (36.1665, -86.7713),    # Nissan Stadium
            "WAS": (38.9076, -76.8645),    # FedExField
        }

    def _is_dome_stadium(self, team: str) -> bool:
        """Check if stadium is a dome (weather doesn't matter)"""
        dome_teams = {"DAL", "DET", "LV", "MIN", "NO"}
        return team in dome_teams

    def _kelvin_to_fahrenheit(self, kelvin: float) -> float:
        """Convert Kelvin to Fahrenheit"""
        return (kelvin - 273.15) * 9/5 + 32

    def _mps_to_mph(self, mps: float) -> float:
        """Convert meters/sec to miles/hour"""
        return mps * 2.23694

    def _mm_to_inches(self, mm: float) -> float:
        """Convert millimeters to inches"""
        return mm * 0.0393701

    def _wind_degrees_to_direction(self, degrees: int) -> str:
        """Convert wind degrees to cardinal direction"""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        idx = round(degrees / 45) % 8
        return directions[idx]

    def _determine_field_conditions(
        self,
        temp: float,
        precipitation: float,
        conditions: str
    ) -> str:
        """Determine field conditions from weather"""
        if "snow" in conditions.lower():
            return "snow-covered"
        elif precipitation > 0.5:
            return "muddy"
        elif precipitation > 0.1:
            return "wet"
        elif temp < 32:
            return "frozen"
        else:
            return "dry"

    async def _fetch_weather_data(
        self,
        lat: float,
        lon: float,
        game_time: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from OpenWeatherMap API.

        Args:
            lat: Latitude
            lon: Longitude
            game_time: Scheduled game time

        Returns:
            Weather data dict or None if error
        """
        try:
            # Check rate limit
            if self.call_count >= self.max_daily_calls:
                logger.error("OpenWeatherMap API rate limit reached")
                return None

            # Determine if we need forecast or current weather
            hours_until_game = (game_time - datetime.utcnow()).total_seconds() / 3600

            if hours_until_game > 5:
                # Use forecast API for future games
                url = f"{self.base_url}/forecast"
            else:
                # Use current weather for games starting soon
                url = f"{self.base_url}/weather"

            params = {
                "lat": lat,
                "lon": lon,
                "appid": self.api_key,
                "units": "metric"  # We'll convert to imperial
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                self.call_count += 1

                data = response.json()

                # Parse based on endpoint
                if hours_until_game > 5:
                    # Find forecast closest to game time
                    forecasts = data.get("list", [])
                    if not forecasts:
                        return None

                    # Get forecast closest to game time
                    closest_forecast = min(
                        forecasts,
                        key=lambda x: abs(
                            datetime.fromtimestamp(x["dt"]) - game_time
                        )
                    )
                    weather_data = closest_forecast
                else:
                    weather_data = data

                return weather_data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching weather: {e.response.status_code}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Request error fetching weather: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            return None

    async def get_game_weather(
        self,
        game_id: str,
        home_team: str,
        game_time: datetime
    ) -> Optional[WeatherData]:
        """
        Get weather for a specific game.

        Args:
            game_id: Unique game identifier
            home_team: Home team code (e.g., 'KC')
            game_time: Scheduled game time

        Returns:
            WeatherData object or None
        """
        # Check if dome stadium (skip API call)
        if self._is_dome_stadium(home_team):
            return WeatherData(
                game_id=game_id,
                temperature=72.0,
                wind_speed=0.0,
                humidity=50.0,
                conditions="Indoor",
                field_conditions="dry",
                dome_stadium=True,
                forecast_confidence=1.0,
                game_time=game_time,
                hours_before_game=0
            )

        # Check Redis cache first
        if self.redis:
            cache_key = f"weather:{game_id}:{datetime.utcnow().hour}"
            cached = await self.redis.get(cache_key)
            if cached:
                logger.info(f"Weather cache hit for {game_id}")
                return WeatherData.model_validate_json(cached)

        # Get stadium location
        if home_team not in self.stadium_locations:
            logger.error(f"Unknown stadium location for team {home_team}")
            return None

        lat, lon = self.stadium_locations[home_team]

        # Fetch from API
        raw_data = await self._fetch_weather_data(lat, lon, game_time)
        if not raw_data:
            return None

        # Parse and convert units
        main = raw_data.get("main", {})
        wind = raw_data.get("wind", {})
        weather = raw_data.get("weather", [{}])[0]
        rain = raw_data.get("rain", {})
        snow = raw_data.get("snow", {})

        temp_f = self._kelvin_to_fahrenheit(main.get("temp", 273.15))
        wind_mph = self._mps_to_mph(wind.get("speed", 0))
        wind_deg = wind.get("deg", 0)

        # Calculate precipitation
        precip_mm = rain.get("1h", 0) + snow.get("1h", 0)
        precip_inches = self._mm_to_inches(precip_mm)

        conditions_desc = weather.get("description", "Unknown").title()
        field_conds = self._determine_field_conditions(
            temp_f,
            precip_inches,
            conditions_desc
        )

        # Calculate confidence based on hours until game
        hours_until = (game_time - datetime.utcnow()).total_seconds() / 3600
        if hours_until < 1:
            confidence = 0.95
        elif hours_until < 4:
            confidence = 0.85
        elif hours_until < 12:
            confidence = 0.75
        else:
            confidence = 0.60

        weather_data = WeatherData(
            game_id=game_id,
            temperature=round(temp_f, 1),
            wind_speed=round(wind_mph, 1),
            wind_direction=self._wind_degrees_to_direction(wind_deg),
            precipitation=round(precip_inches, 2),
            humidity=main.get("humidity", 50),
            conditions=conditions_desc,
            field_conditions=field_conds,
            dome_stadium=False,
            forecast_confidence=confidence,
            game_time=game_time,
            hours_before_game=int(hours_until)
        )

        # Cache for 1 hour
        if self.redis:
            await self.redis.setex(
                f"weather:{game_id}:{datetime.utcnow().hour}",
                3600,
                weather_data.model_dump_json()
            )

        # Store in database
        if self.supabase:
            try:
                await self._store_weather_data(weather_data)
            except Exception as e:
                logger.error(f"Failed to store weather data: {e}")

        logger.info(
            f"Fetched weather for {game_id}: {temp_f:.1f}°F, "
            f"{wind_mph:.1f} mph wind, {conditions_desc}"
        )

        return weather_data

    async def _store_weather_data(self, weather: WeatherData):
        """Store weather data in Supabase"""
        data = weather.model_dump()
        data["fetched_at"] = data["fetched_at"].isoformat()
        if data.get("game_time"):
            data["game_time"] = data["game_time"].isoformat()

        await self.supabase.table("weather_conditions").insert(data).execute()

    async def fetch_scheduled_weather(
        self,
        games: List[Dict[str, Any]],
        hours_before: List[int] = [12, 4, 1]
    ) -> List[WeatherData]:
        """
        Fetch weather for multiple games at scheduled intervals.

        Args:
            games: List of game dicts with 'game_id', 'home_team', 'game_time'
            hours_before: Hours before game to fetch weather (default: 12, 4, 1)

        Returns:
            List of WeatherData objects
        """
        results = []

        for game in games:
            game_time = game["game_time"]
            hours_until = (game_time - datetime.utcnow()).total_seconds() / 3600

            # Only fetch if we're at a scheduled checkpoint
            should_fetch = False
            for checkpoint in hours_before:
                if abs(hours_until - checkpoint) < 0.5:  # Within 30 min of checkpoint
                    should_fetch = True
                    break

            if not should_fetch:
                continue

            weather = await self.get_game_weather(
                game["game_id"],
                game["home_team"],
                game_time
            )

            if weather:
                results.append(weather)

            # Rate limiting: 1 request per second to be safe
            await asyncio.sleep(1)

        return results

    def get_api_usage(self) -> Dict[str, Any]:
        """Get current API usage statistics"""
        return {
            "calls_today": self.call_count,
            "daily_limit": self.max_daily_calls,
            "remaining": self.max_daily_calls - self.call_count,
            "percentage_used": (self.call_count / self.max_daily_calls) * 100
        }