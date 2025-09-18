# NFL Predictions API Documentation

## Overview

The NFL Predictions API serves **375+ comprehensive predictions** for each NFL game through a high-performance FastAPI backend. The system features 15 expert models, each generating 25+ prediction categories, with real-time capabilities and sub-second response times.

## Features

- **375+ Predictions per Game**: 15 experts × 25+ categories each
- **Real-time Updates**: WebSocket streaming for live game predictions
- **Sub-second Performance**: Optimized caching and parallel processing
- **Rate Limiting**: Tiered API access with security measures
- **Expert Consensus**: Top-5 expert weighted consensus system
- **Comprehensive Categories**: Core game, player props, live betting, and advanced analytics

## API Endpoints

### Base URL
```
https://api.nfl-predictor.com/api/v2
```

### Authentication
```http
Authorization: Bearer <your_api_key>
```

## Core Endpoints

### 1. All Predictions for a Game
```http
GET /api/v2/predictions/{game_id}
```

**Description**: Returns all 375+ predictions from 15 experts across 25+ categories.

**Parameters**:
- `game_id` (string): Game identifier (e.g., "KC@BUF_2024")

**Response Structure**:
```json
{
  "game_id": "KC@BUF_2024",
  "home_team": "KC",
  "away_team": "BUF",
  "game_time": "2024-01-15T20:00:00Z",
  "predictions": [
    {
      "expert_id": "expert_001",
      "expert_name": "Sharp Bettor",
      "game_id": "KC@BUF_2024",
      "game_outcome": {
        "winner": "KC",
        "home_win_prob": 0.65,
        "away_win_prob": 0.35,
        "confidence": 0.72,
        "reasoning": "Line moved 0.5, public on 65%"
      },
      "exact_score": {
        "home_score": 27,
        "away_score": 24,
        "confidence": 0.45,
        "reasoning": "Based on market-implied scoring expectations"
      },
      "against_the_spread": {
        "pick": "KC",
        "spread_line": -2.5,
        "confidence": 0.68,
        "edge": 1.0
      },
      "totals": {
        "pick": "over",
        "total_line": 54.5,
        "predicted_total": 51,
        "confidence": 0.55
      },
      "player_props": {
        "passing_props": {
          "qb_yards": {
            "home_qb": {
              "over_under": 267.5,
              "pick": "over",
              "confidence": 0.68
            }
          }
        },
        "rushing_props": { /* ... */ },
        "receiving_props": { /* ... */ },
        "fantasy_points": { /* ... */ }
      },
      "live_predictions": {
        "real_time_win_probability": {
          "opening_drive": {"home": 0.52, "away": 0.48},
          "halftime": {"home": 0.58, "away": 0.42}
        },
        "next_score_probability": {
          "team": "KC",
          "score_type": "touchdown",
          "probability": 0.35
        }
      },
      "confidence_overall": 0.72,
      "reasoning": "Analysis shows line movement, public betting 65% favor KC based on Sharp Bettor methodology",
      "key_factors": ["Line movement", "Public betting", "Market inefficiencies"],
      "prediction_timestamp": "2024-01-15T18:00:00Z"
    }
    // ... 14 more expert predictions
  ],
  "total_predictions": 375,
  "categories_covered": ["core_game", "live_game", "player_props", "game_segments", "environmental", "advanced"],
  "consensus_summary": {
    "game_outcome": {
      "home_wins": 9,
      "away_wins": 6,
      "consensus_winner": "KC"
    },
    "average_scores": {"home": 25.3, "away": 22.1},
    "ats_consensus": "KC",
    "totals_consensus": "over"
  },
  "last_updated": "2024-01-15T18:30:00Z"
}
```

**Performance**: < 1 second response time for 375+ predictions

### 2. Predictions by Category
```http
GET /api/v2/predictions/{game_id}/category/{category}
```

**Categories**:
- `core_game`: Game outcome, spread, totals, moneyline
- `player_props`: Passing, rushing, receiving, fantasy props
- `live_game`: Real-time probabilities, drive outcomes
- `game_segments`: Quarter analysis, half winners
- `environmental`: Weather and injury impact
- `advanced`: Special teams, coaching, situational

**Example Response** (core_game category):
```json
{
  "game_id": "KC@BUF_2024",
  "category": "core_game",
  "predictions": [
    {
      "expert": "Sharp Bettor",
      "game_outcome": { /* ... */ },
      "exact_score": { /* ... */ },
      "against_the_spread": { /* ... */ },
      "totals": { /* ... */ },
      "moneyline": { /* ... */ }
    }
    // ... other experts
  ],
  "expert_count": 15,
  "consensus": {
    "category": "core_game",
    "expert_agreement": 15
  },
  "confidence_range": {
    "min": 0.45,
    "max": 0.85,
    "avg": 0.67
  }
}
```

### 3. Player Props Predictions
```http
GET /api/v2/player-props/{game_id}
```

**Response Structure**:
```json
{
  "game_id": "KC@BUF_2024",
  "passing_props": {
    "qb_yards": {
      "home_qb": [
        {
          "expert": "Sharp Bettor",
          "prediction": {
            "over_under": 267.5,
            "pick": "over",
            "confidence": 0.68
          }
        }
        // ... 14 more expert predictions
      ]
    },
    "qb_touchdowns": { /* ... */ },
    "completions": { /* ... */ },
    "interceptions": { /* ... */ }
  },
  "rushing_props": {
    "rb_yards": { /* ... */ },
    "rb_attempts": { /* ... */ },
    "rb_touchdowns": { /* ... */ }
  },
  "receiving_props": {
    "wr_yards": { /* ... */ },
    "receptions": { /* ... */ },
    "targets": { /* ... */ }
  },
  "fantasy_props": {
    "qb_points": { /* ... */ },
    "rb_points": { /* ... */ },
    "wr_points": { /* ... */ }
  },
  "expert_count": 15,
  "consensus_confidence": 0.71
}
```

### 4. Live Predictions
```http
GET /api/v2/live/{game_id}
```

**Real-time Updates** (15-second cache):
```json
{
  "game_id": "KC@BUF_2024",
  "current_quarter": 2,
  "time_remaining": "5:23",
  "current_score": {"home": 14, "away": 10},
  "live_win_probability": {"home": 0.67, "away": 0.33},
  "next_score_predictions": [
    {
      "expert": "Sharp Bettor",
      "prediction": {
        "team": "KC",
        "score_type": "touchdown",
        "probability": 0.35,
        "expected_points": 6.2
      }
    }
    // ... other experts
  ],
  "drive_predictions": {
    "Sharp Bettor": {
      "touchdown_prob": 0.28,
      "field_goal_prob": 0.22,
      "punt_prob": 0.35,
      "turnover_prob": 0.12
    }
    // ... other experts
  },
  "game_state_analysis": {
    "possession": "home",
    "down_and_distance": "2 & 7",
    "field_position": 35
  },
  "last_updated": "2024-01-15T21:15:00Z"
}
```

### 5. Expert Consensus (Top 5)
```http
GET /api/v2/consensus/{game_id}/top5
```

**Weighted by Performance**:
```json
{
  "game_id": "KC@BUF_2024",
  "top_experts": [
    "Analytics Guru",
    "Sharp Bettor",
    "Weather Wizard",
    "Injury Analyst",
    "Road Warrior"
  ],
  "consensus_predictions": {
    "game_winner": "KC",
    "ats_pick": "KC",
    "totals_pick": "over",
    "home_win_probability": 0.64
  },
  "confidence_score": 0.73,
  "prediction_weights": {
    "expert_004": 0.23,  // Analytics Guru
    "expert_001": 0.22,  // Sharp Bettor
    "expert_002": 0.20,  // Weather Wizard
    "expert_003": 0.18,  // Injury Analyst
    "expert_005": 0.17   // Road Warrior
  },
  "category_consensus": {
    "core_game": {
      "winner": "KC",
      "ats_pick": "KC",
      "confidence": 0.64
    },
    "totals": {
      "pick": "over",
      "confidence": 0.68
    }
  }
}
```

### 6. Expert Performance Tracking
```http
GET /api/v2/expert/{expert_id}/performance
```

**Response**:
```json
{
  "expert_id": "expert_001",
  "expert_name": "Sharp Bettor",
  "performance_metrics": {
    "overall_accuracy": 0.73,
    "category_accuracy": {
      "core_game": 0.75,
      "player_props": 0.71,
      "live_game": 0.69,
      "totals": 0.78
    },
    "recent_form": "improving",
    "total_predictions": 245,
    "correct_predictions": 179,
    "last_updated": "2024-01-15T18:00:00Z"
  },
  "recent_predictions": [
    {
      "prediction_id": "pred_1",
      "expert_name": "Sharp Bettor",
      "category": "core_game",
      "confidence": 0.72,
      "key_prediction": "KC -2.5 (line movement edge)",
      "timestamp": "2024-01-15T17:00:00Z"
    }
    // ... more recent predictions
  ],
  "specialty_areas": ["sharp_money", "line_movement", "market_inefficiencies"],
  "ranking": 3,
  "trend": "improving"
}
```

## WebSocket Real-time Streaming

### Live Prediction Updates
```javascript
// WebSocket URL
wss://api.nfl-predictor.com/api/v2/live/{game_id}/stream

// Connection
const ws = new WebSocket('wss://api.nfl-predictor.com/api/v2/live/KC@BUF_2024/stream');

// Message types received:
{
  "message_type": "live_update",
  "game_id": "KC@BUF_2024",
  "data": {
    "current_quarter": 2,
    "time_remaining": "3:45",
    "live_win_probability": {"home": 0.72, "away": 0.28},
    "next_score_predictions": [/* ... */]
  },
  "timestamp": "2024-01-15T21:20:00Z"
}
```

## Rate Limiting

### API Key Tiers

| Tier | Requests/Minute | Requests/Hour | Features |
|------|----------------|---------------|----------|
| Anonymous | 30 | 500 | Basic access |
| Basic | 60 | 1,000 | API key required |
| Premium | 300 | 10,000 | Priority support |
| Enterprise | 1,000 | 50,000 | Custom features |

### Rate Limit Headers
```http
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 832
X-RateLimit-Tier: basic
```

## Error Handling

### Error Response Format
```json
{
  "error_code": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded",
  "details": {
    "requests_per_minute": 60,
    "retry_after": 60
  },
  "timestamp": "2024-01-15T18:00:00Z"
}
```

### HTTP Status Codes
- `200`: Success
- `400`: Bad Request (invalid game_id format)
- `401`: Unauthorized (invalid API key)
- `404`: Not Found (expert or game not found)
- `429`: Too Many Requests (rate limit exceeded)
- `500`: Internal Server Error

## Performance Metrics

### Response Time Benchmarks
- All predictions: < 1.0 second
- Category filtering: < 0.5 seconds
- Player props: < 0.8 seconds
- Live predictions: < 0.5 seconds
- Expert consensus: < 1.0 second
- Expert performance: < 0.3 seconds

### Caching Strategy
- Game predictions: 60 seconds
- Category predictions: 45 seconds
- Player props: 90 seconds
- Live predictions: 15 seconds
- Consensus: 120 seconds
- Expert performance: 300 seconds

## SDKs and Integration

### Python SDK Example
```python
import requests
from datetime import datetime

class NFLPredictionsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.nfl-predictor.com/api/v2"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    def get_all_predictions(self, game_id):
        response = requests.get(
            f"{self.base_url}/predictions/{game_id}",
            headers=self.headers
        )
        return response.json()

    def get_live_predictions(self, game_id):
        response = requests.get(
            f"{self.base_url}/live/{game_id}",
            headers=self.headers
        )
        return response.json()

# Usage
api = NFLPredictionsAPI("your_api_key")
predictions = api.get_all_predictions("KC@BUF_2024")
print(f"Total predictions: {predictions['total_predictions']}")
```

### JavaScript SDK Example
```javascript
class NFLPredictionsAPI {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.baseUrl = 'https://api.nfl-predictor.com/api/v2';
        this.headers = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async getAllPredictions(gameId) {
        const response = await fetch(
            `${this.baseUrl}/predictions/${gameId}`,
            { headers: this.headers }
        );
        return response.json();
    }

    connectLiveStream(gameId, onUpdate) {
        const ws = new WebSocket(
            `wss://api.nfl-predictor.com/api/v2/live/${gameId}/stream`
        );

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            onUpdate(data);
        };

        return ws;
    }
}

// Usage
const api = new NFLPredictionsAPI('your_api_key');
const predictions = await api.getAllPredictions('KC@BUF_2024');
```

## Expert Models Overview

### The 15 Expert Models

1. **Sharp Bettor** (`expert_001`): Line movement and market inefficiencies
2. **Weather Wizard** (`expert_002`): Environmental conditions specialist
3. **Injury Analyst** (`expert_003`): Player availability and depth analysis
4. **Analytics Guru** (`expert_004`): Advanced metrics (EPA, DVOA, success rates)
5. **Road Warrior** (`expert_005`): Road team advantages and travel analysis
6. **Situational Expert** (`expert_006`): Red zone, third down, and clutch situations
7. **Props Specialist** (`expert_007`): Player performance and prop betting
8. **Live Betting Pro** (`expert_008`): In-game momentum and live odds
9. **Contrarian Voice** (`expert_009`): Fade-the-public strategies
10. **Trend Tracker** (`expert_010`): Historical patterns and trends
11. **Matchup Maestro** (`expert_011`): Position-by-position analysis
12. **Pace Predictor** (`expert_012`): Game pace and possession analysis
13. **Special Teams Specialist** (`expert_013`): Kicking and return game focus
14. **Divisional Dynamo** (`expert_014`): Division rivalry and familiarity
15. **Prime Time Pro** (`expert_015`): National TV and spotlight games

### Prediction Categories (25+ per Expert)

#### Core Game Predictions (6)
1. Game Outcome (Winner & Probability)
2. Exact Score Predictions
3. Margin of Victory
4. Against The Spread (ATS)
5. Totals (Over/Under)
6. Moneyline Value Analysis

#### Live Game Predictions (4)
7. Real-Time Win Probability Updates
8. Next Score Probability
9. Drive Outcome Predictions
10. Fourth Down Decision Recommendations

#### Player Props Predictions (4)
11. Passing Props (Yards, TDs, Completions, INTs)
12. Rushing Props (Yards, Attempts, TDs, Longest)
13. Receiving Props (Yards, Receptions, TDs, Targets)
14. Fantasy Points Predictions

#### Game Segments (2)
15. First Half Winner
16. Highest Scoring Quarter

#### Environmental & Situational (4)
17. Weather Impact Analysis
18. Injury Impact Assessment
19. Momentum/Trend Analysis
20. Situational Predictions (Red Zone, 3rd Down)

#### Advanced Analysis (5+)
21. Special Teams Predictions
22. Coaching Matchup Analysis
23. Home Field Advantage Quantification
24. Travel/Rest Impact Analysis
25. Divisional Game Dynamics
26. **Additional categories based on expert specialty**

## Support and Documentation

### API Documentation
- Interactive docs: `https://api.nfl-predictor.com/docs`
- OpenAPI schema: `https://api.nfl-predictor.com/openapi.json`

### Support Channels
- Technical support: `api-support@nfl-predictor.com`
- API status page: `https://status.nfl-predictor.com`
- Rate limit increases: `billing@nfl-predictor.com`

### Webhook Integration
Contact support for webhook setup to receive real-time prediction updates pushed to your endpoints.

---

## Quick Start

1. **Get API Key**: Sign up at `https://nfl-predictor.com/api`
2. **Test Connection**: `curl -H "Authorization: Bearer YOUR_KEY" https://api.nfl-predictor.com/api/v2/health`
3. **Get Predictions**: `curl -H "Authorization: Bearer YOUR_KEY" https://api.nfl-predictor.com/api/v2/predictions/KC@BUF_2024`
4. **Integrate**: Use provided SDKs or build custom integration
5. **Monitor**: Check rate limits and performance metrics

The NFL Predictions API delivers the most comprehensive prediction system available, with 375+ predictions per game updated in real-time with sub-second performance.