# Data Ingestion Services Setup Guide

## Overview

This guide covers setup and usage of the real-time data ingestion services for weather and Vegas odds.

## Services Included

1. **Weather Ingestion Service** - OpenWeatherMap API integration
2. **Vegas Odds Service** - The Odds API integration
3. **Data Coordinator** - Orchestrates both services with intelligent scheduling

## Prerequisites

### API Keys Required

1. **OpenWeatherMap API Key** (Free tier: 1000 calls/day)
   - Sign up: https://openweathermap.org/api
   - Copy API key from dashboard

2. **The Odds API Key** (Free tier: 500 requests/day)
   - Sign up: https://the-odds-api.com/
   - Get API key from account page

### Infrastructure

- Python 3.11+
- PostgreSQL (Supabase)
- Redis (optional but recommended for caching)

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements-services.txt
```

Or add to main requirements.txt:
```bash
httpx==0.25.2
pydantic==2.5.1
redis==5.0.1
python-dotenv==1.0.0
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
OPENWEATHER_API_KEY=your_actual_api_key_here
ODDS_API_KEY=your_actual_api_key_here

SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key_here

REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. Run Database Migrations

```bash
# Apply the migrations to create necessary tables
psql -h your-db-host -U postgres -d your-db-name -f migrations/001_create_betting_tables.sql
```

Or via Supabase dashboard:
1. Go to SQL Editor
2. Paste contents of `migrations/001_create_betting_tables.sql`
3. Run migration

## Usage Examples

### Basic Weather Fetching

```python
import asyncio
from datetime import datetime, timedelta
from src.services.weather_ingestion_service import WeatherIngestionService

async def main():
    # Initialize service
    weather_service = WeatherIngestionService(
        api_key="your_openweather_key"
    )

    # Fetch weather for a game
    game_time = datetime.utcnow() + timedelta(hours=4)
    weather = await weather_service.get_game_weather(
        game_id="2025_05_KC_BUF",
        home_team="BUF",
        game_time=game_time
    )

    print(f"Temperature: {weather.temperature}°F")
    print(f"Wind: {weather.wind_speed} mph {weather.wind_direction}")
    print(f"Conditions: {weather.conditions}")
    print(f"Confidence: {weather.forecast_confidence}")

asyncio.run(main())
```

### Basic Odds Fetching

```python
from src.services.vegas_odds_service import VegasOddsService

async def main():
    odds_service = VegasOddsService(
        api_key="your_odds_api_key"
    )

    # Fetch current lines
    lines = await odds_service.get_current_lines(
        game_id="2025_05_KC_BUF",
        home_team="BUF",
        away_team="KC"
    )

    for line in lines:
        print(f"\n{line.sportsbook}:")
        print(f"  Spread: {line.spread} ({line.spread_odds_home})")
        print(f"  Moneyline: {line.moneyline_home} / {line.moneyline_away}")
        print(f"  Total: {line.total}")

        if line.sharp_money_indicator:
            print(f"  ⚠️ SHARP MONEY DETECTED")

asyncio.run(main())
```

### Full Data Coordinator

```python
from src.services.data_coordinator import DataCoordinator
from src.services.weather_ingestion_service import WeatherIngestionService
from src.services.vegas_odds_service import VegasOddsService
from supabase import create_client
import redis.asyncio as redis

async def main():
    # Initialize services
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

    redis_client = await redis.from_url("redis://localhost:6379")

    weather_service = WeatherIngestionService(
        supabase_client=supabase,
        redis_client=redis_client
    )

    odds_service = VegasOddsService(
        supabase_client=supabase,
        redis_client=redis_client
    )

    # Create coordinator
    coordinator = DataCoordinator(
        weather_service=weather_service,
        odds_service=odds_service,
        supabase_client=supabase,
        redis_client=redis_client
    )

    # Gather all data for a game
    game_data = await coordinator.gather_game_data(
        game_id="2025_05_KC_BUF",
        home_team="BUF",
        away_team="KC",
        game_time=datetime.utcnow() + timedelta(hours=4)
    )

    print(f"Data Quality Score: {game_data['data_quality']['overall_score']:.2f}")

    # Check system health
    health = coordinator.get_system_health()
    print(f"\nSystem Health: {'Healthy' if health['overall_healthy'] else 'Issues Detected'}")

    # Detect anomalies
    anomalies = await coordinator.detect_anomalies()
    if anomalies:
        print(f"\n⚠️ {len(anomalies)} anomalies detected:")
        for anomaly in anomalies:
            print(f"  - {anomaly['type']}: {anomaly}")

asyncio.run(main())
```

## Scheduled Data Refresh

For production, set up automated refresh:

```python
async def run_scheduled_refresh():
    coordinator = DataCoordinator(...)

    # Load upcoming games from database
    games = [
        {
            "game_id": "2025_05_KC_BUF",
            "home_team": "BUF",
            "away_team": "KC",
            "game_time": datetime(2025, 10, 6, 16, 25)
        },
        # ... more games
    ]

    # Create stop event
    stop_event = asyncio.Event()

    # Run continuous refresh loop
    await coordinator.scheduled_refresh_loop(games, stop_event)
```

## Refresh Intervals

The coordinator automatically adjusts refresh frequency based on time until game:

- **1 hour before game**: Every 5 minutes
- **4 hours before game**: Every 30 minutes
- **12 hours before game**: Every 1 hour
- **>12 hours before game**: Every 4 hours

## API Usage Monitoring

Check API usage to avoid rate limits:

```python
# Weather API
weather_usage = weather_service.get_api_usage()
print(f"Weather API: {weather_usage['calls_today']}/{weather_usage['daily_limit']}")

# Odds API
odds_usage = odds_service.get_api_usage()
print(f"Odds API: {odds_usage['requests_today']}/{odds_usage['daily_limit']}")
```

## Caching Strategy

Both services use Redis caching:

- **Weather**: Cached for 1 hour per game
- **Odds**: Cached for 30 minutes per game

Benefits:
- Reduces API calls by ~80%
- Faster response times
- Better rate limit management

## Error Handling

Services include automatic retry logic:

```python
# 3 retries with exponential backoff
# Attempt 1: immediate
# Attempt 2: wait 2 seconds
# Attempt 3: wait 4 seconds
# Attempt 4: wait 8 seconds
```

Health monitoring tracks failures:
- < 3 consecutive failures: Service healthy
- ≥ 3 consecutive failures: Service unhealthy, alerts triggered

## Testing

Run unit tests:

```bash
# All tests
pytest tests/services/

# Specific service
pytest tests/services/test_weather_ingestion_service.py
pytest tests/services/test_vegas_odds_service.py
pytest tests/services/test_data_coordinator.py

# With coverage
pytest tests/services/ --cov=src/services --cov-report=html
```

## Monitoring & Alerts

Monitor data freshness:

```sql
SELECT
    data_source,
    last_successful_fetch,
    consecutive_failures,
    is_healthy
FROM data_freshness_monitor;
```

Set up alerts for:
- Data staleness > 1 hour
- Consecutive failures ≥ 3
- API usage > 90% of limit

## Cost Optimization Tips

1. **Use Redis caching** - Saves 70-80% of API calls
2. **Smart scheduling** - Only fetch when needed (avoid unnecessary calls)
3. **Batch requests** - Group games when possible
4. **Monitor usage** - Check daily usage to stay within free tiers

### Free Tier Limits
- OpenWeatherMap: 1000 calls/day → ~41 calls/hour → ~10 games with 12h/4h/1h schedule
- The Odds API: 500 requests/day → ~20 requests/hour → ~10 games with 30min refresh

## Troubleshooting

### Issue: Rate limit exceeded
**Solution**: Increase caching TTL or reduce refresh frequency

### Issue: Stale data warnings
**Solution**: Check API keys, network connectivity, service health

### Issue: Missing data for games
**Solution**: Verify game IDs match API format, check team name mappings

### Issue: Low confidence forecasts
**Solution**: Normal for games >24 hours away, increases as game approaches

## Production Deployment

1. Use environment variables (never commit API keys)
2. Enable Redis caching in production
3. Set up monitoring and alerting
4. Configure log aggregation (e.g., DataDog, CloudWatch)
5. Use production-grade Supabase tier
6. Consider upgrading to paid API tiers for higher limits

## Support

- Weather API docs: https://openweathermap.org/api
- Odds API docs: https://the-odds-api.com/liveapi/guides/v4/
- Project issues: `/docs/COMPREHENSIVE_GAP_ANALYSIS.md`