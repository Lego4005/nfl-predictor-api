# Real Data Integration - SportsData.io Connector

This document describes the comprehensive SportsData.io connector that provides real NFL data for enhanced predictions.

## Overview

The Real Data Connector integrates with SportsData.io to fetch live NFL data including:
- Current week games and scores
- Team statistics (offensive/defensive rankings, EPA, DVOA-like metrics)
- Injury reports for all teams
- Weather data for outdoor games
- Betting odds and line movements
- Historical matchup data

## Files Created

### 1. Core Connector (`/src/services/real_data_connector.py`)

**SportsDataIOConnector Class:**
```python
async with SportsDataIOConnector() as connector:
    games = await connector.get_current_week_games()
    team_stats = await connector.get_team_stats('KC')
    injuries = await connector.get_injuries('KC')
    weather = await connector.get_weather(game_id)
    betting = await connector.get_betting_data(game_id)
    history = await connector.get_historical_matchup('KC', 'SF')
```

**Key Features:**
- Automatic rate limiting (100 req/min, 1000/hour, 10000/day)
- Intelligent caching with configurable TTL
- Error handling and retry logic
- Data format compatible with existing ReasoningFactors

### 2. Prediction Integration (`/src/services/prediction_integration.py`)

**PredictionDataIntegrator Class:**
```python
async with PredictionDataIntegrator() as integrator:
    # Get enhanced reasoning factors for a specific matchup
    factors = await integrator.get_enhanced_reasoning_factors('KC', 'SF', game_id)

    # Get all current games with enhanced data
    all_games = await integrator.get_all_current_games_data()
```

**Enhanced Reasoning Factors Structure:**
```json
{
  "matchup_info": {
    "home_team": "KC",
    "away_team": "SF",
    "game_id": 123456,
    "data_timestamp": "2024-01-15T10:30:00Z"
  },
  "team_performance": {
    "home_team": {
      "offensive_ranking": 5,
      "defensive_ranking": 12,
      "points_per_game": 28.5,
      "points_allowed_per_game": 21.2,
      "turnover_margin": 1.2
    },
    "away_team": { ... }
  },
  "situational_factors": {
    "home_field_advantage": 2.5,
    "injury_impact": {
      "home_team": 1.5,
      "away_team": 3.2,
      "key_injuries": [...]
    },
    "weather_impact": -2.0,
    "divisional_matchup": false
  },
  "market_factors": {
    "point_spread": -3.5,
    "total_line": 47.5,
    "implied_probability_home": 0.58
  },
  "historical_trends": {
    "head_to_head_record": {
      "total_games": 8,
      "home_team_wins": 5,
      "avg_total_points": 52.3
    }
  },
  "data_quality": {
    "confidence_level": "High",
    "quality_score": 0.9,
    "complete_dataset": true
  }
}
```

### 3. Enhanced Prediction Service (`/src/ml/real_data_prediction_service.py`)

**RealDataNFLPredictionService Class:**
```python
async with RealDataNFLPredictionService() as service:
    await service.initialize_models()

    # Get enhanced predictions
    predictions = await service.get_enhanced_game_predictions(week=15)

    # Get live updates
    live_games = await service.get_live_game_updates()

    # Get comprehensive analysis
    analysis = await service.get_comprehensive_week_analysis(week=15)
```

### 4. API Endpoints (`/src/api/real_data_endpoints.py`)

**Available Endpoints:**
- `GET /api/real-data/status` - Service status and health
- `GET /api/real-data/games/current` - Current week games
- `GET /api/real-data/teams/{team_id}/stats` - Team statistics
- `GET /api/real-data/injuries` - Injury reports
- `GET /api/real-data/betting/odds` - Betting odds
- `GET /api/real-data/predictions/enhanced` - Enhanced predictions
- `GET /api/real-data/predictions/live` - Live game updates
- `GET /api/real-data/analysis/comprehensive` - Full week analysis
- `GET /api/real-data/test/connectivity` - Test API connectivity

## Setup Instructions

### 1. Environment Variables

Add to your `.env` file:
```bash
VITE_SPORTSDATA_IO_KEY=bc297647c7aa4ef29747e6a85cb575dc
```

### 2. Install Dependencies

The following packages are required (already in requirements.txt):
```bash
aiohttp>=3.8.0
python-dotenv>=1.0.0
requests>=2.31.0
```

### 3. Test Connectivity

Run the simple connectivity test:
```bash
python3 src/services/simple_api_test.py
```

Expected output:
```
🚀 Simple SportsData.io API Test
🔌 Testing SportsData.io API with key: bc297647...
📡 Making API request...
Response status: 200
✅ API request successful!
   Returned 272 games
🎉 API test passed! The connector should work properly.
```

## Usage Examples

### Basic Usage

```python
from services.real_data_connector import SportsDataIOConnector

# Simple game data fetch
async with SportsDataIOConnector() as connector:
    games = await connector.get_current_week_games()
    print(f"Found {len(games)} current games")
```

### Enhanced Predictions

```python
from ml.real_data_prediction_service import RealDataNFLPredictionService

# Get enhanced predictions with real data
async with RealDataNFLPredictionService() as service:
    await service.initialize_models()
    predictions = await service.get_enhanced_game_predictions(week=15)

    for pred in predictions:
        print(f"{pred['away_team']} @ {pred['home_team']}: {pred['winner']} ({pred['overall_confidence']:.1%})")
```

### API Usage

```bash
# Test service status
curl http://localhost:8000/api/real-data/status

# Get current games
curl http://localhost:8000/api/real-data/games/current

# Get team stats
curl http://localhost:8000/api/real-data/teams/KC/stats

# Get enhanced predictions
curl http://localhost:8000/api/real-data/predictions/enhanced?week=15
```

## Data Quality & Caching

### Caching Strategy

The connector implements intelligent caching with different TTL values:
- **Live Scores:** 1 minute
- **Team Stats:** 1 hour
- **Injuries:** 30 minutes
- **Weather:** 30 minutes
- **Betting Odds:** 5 minutes

### Data Quality Assessment

Each prediction includes a data quality assessment:
```json
{
  "data_quality": {
    "confidence_level": "High|Medium|Low",
    "quality_score": 0.0-1.0,
    "complete_dataset": true|false,
    "sources": {
      "team_stats": true,
      "injury_reports": true,
      "betting_odds": true,
      "weather_data": false,
      "historical_data": true
    }
  }
}
```

### Rate Limiting

The connector respects SportsData.io rate limits:
- 100 requests per minute
- 1,000 requests per hour
- 10,000 requests per day

Rate limiting is handled automatically with exponential backoff.

## Integration with Existing System

### ReasoningFactors Compatibility

The real data connector formats all data to be compatible with the existing `ReasoningFactors` structure:

```python
formatted_data = connector.format_for_reasoning_factors(
    team_stats=team_stats,
    injuries=injuries,
    weather=weather,
    betting=betting
)
```

### Fallback Handling

The system gracefully falls back to existing prediction models when real data is unavailable:

```python
# Automatic fallback in enhanced service
if not self.real_data_available:
    logger.warning("Using base predictions without real data")
    return self.base_service.get_game_predictions(week, season)
```

## API Response Examples

### Enhanced Prediction Response

```json
{
  "game_id": "2024-15-SF-KC",
  "week": 15,
  "season": 2024,
  "home_team": "KC",
  "away_team": "SF",
  "winner": "KC",
  "winner_confidence": 0.73,
  "predicted_spread": -3.5,
  "predicted_total": 47.5,
  "ats_pick": "KC",
  "ats_confidence": 0.68,
  "market_data": {
    "current_spread": -3.5,
    "current_total": 47.5,
    "home_moneyline": -165,
    "away_moneyline": +145
  },
  "enhanced_factors": {
    "team_strength": {
      "home_offensive_rank": 3,
      "home_defensive_rank": 8,
      "away_offensive_rank": 12,
      "away_defensive_rank": 5
    },
    "situational_analysis": {
      "home_field_advantage": 2.5,
      "injury_impact_home": 1.2,
      "injury_impact_away": 2.8,
      "weather_impact": 0.0,
      "key_injuries": [
        {
          "player": "Christian McCaffrey",
          "team": "SF",
          "position": "RB",
          "status": "Questionable"
        }
      ]
    },
    "historical_trends": {
      "head_to_head_games": 6,
      "home_team_h2h_wins": 4,
      "avg_total_points_h2h": 51.2
    }
  },
  "data_quality": {
    "confidence_level": "High",
    "data_completeness": 0.9,
    "real_data_available": true
  },
  "key_factors": [
    "Home team has top-5 offense (#3)",
    "Away team affected by RB injury (McCaffrey questionable)",
    "KC dominates recent head-to-head matchups (4-2)"
  ],
  "overall_confidence": 0.71,
  "prediction_timestamp": "2024-01-15T10:30:00Z"
}
```

### Service Status Response

```json
{
  "service_available": true,
  "real_data_enabled": true,
  "api_key_configured": true,
  "last_updated": "2024-01-15T10:30:00Z",
  "total_games_available": 16,
  "data_sources": {
    "sportsdata_io": true,
    "prediction_integration": true,
    "enhanced_predictions": true
  }
}
```

## Error Handling

The system handles various error scenarios:

1. **API Key Issues:** Returns 401 with clear error message
2. **Rate Limiting:** Automatically retries with exponential backoff
3. **Network Issues:** Falls back to cached data or base predictions
4. **Data Format Issues:** Logs warnings and uses default values
5. **Service Unavailable:** Returns degraded service status

## Performance Considerations

### Concurrent Requests

The connector uses `asyncio.gather()` for parallel data fetching:

```python
tasks = [
    connector.get_team_stats(home_team),
    connector.get_team_stats(away_team),
    connector.get_injuries(home_team),
    connector.get_injuries(away_team),
    connector.get_weather(game_id),
    connector.get_betting_data(game_id)
]

results = await asyncio.gather(*tasks)
```

### Memory Management

- Automatic cache cleanup for expired entries
- Connection pooling for HTTP requests
- Lazy loading of prediction models

### Response Times

Expected response times:
- **Cached Data:** < 50ms
- **Fresh API Calls:** 200-500ms
- **Enhanced Predictions:** 1-3 seconds
- **Comprehensive Analysis:** 3-8 seconds

## Monitoring & Logging

The system includes comprehensive logging:

```python
# Logs include:
logger.info("✅ Fetched 16 current week games")
logger.warning("⚠️ Real data connection failed, using fallback")
logger.error("❌ API request failed with status 429")
```

Log levels:
- **INFO:** Successful operations and metrics
- **WARNING:** Fallback scenarios and degraded performance
- **ERROR:** Failed requests and system errors

## Future Enhancements

Planned improvements:
1. **Redis Integration:** Distributed caching across instances
2. **WebSocket Support:** Real-time live game updates
3. **Advanced Analytics:** Player tracking and advanced metrics
4. **Multi-Sport Support:** NBA, MLB, NHL connectors
5. **ML Feature Engineering:** Automated feature extraction from real data

## Support

For issues or questions:
1. Check the logs for specific error messages
2. Verify API key configuration
3. Test basic connectivity with simple_api_test.py
4. Check service status via `/api/real-data/status`
5. Review rate limiting and caching settings