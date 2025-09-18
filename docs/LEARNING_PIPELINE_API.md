# Learning Pipeline API Documentation

## Overview

The Learning Pipeline enables autonomous expert evolution by processing game results and triggering learning mechanisms for the 15 personality-driven experts.

## Base URL
```
http://localhost:8001/api/v1
```

## Authentication
Currently no authentication required (add API keys in production)

## Endpoints

### 1. Process Game Results
**POST** `/games/{game_id}/results`

Processes actual game results to trigger expert learning.

#### Request Body
```json
{
  "winner": "TB",
  "final_score": {
    "home": 24,
    "away": 21
  },
  "actual_spread": -3,
  "actual_total": 45,
  "key_events": ["Turnover in Q4", "Missed FG"],
  "weather_impact": false,
  "injuries_impact": true
}
```

#### Response (200 OK)
```json
{
  "game_id": "ATL@TB_20250115",
  "experts_updated": 15,
  "learning_tasks_created": 15,
  "peer_learning_shared": 3,
  "average_performance": 0.621,
  "best_expert": {
    "expert_id": "conservative_analyzer",
    "score": 0.89
  },
  "worst_expert": {
    "expert_id": "risk_taking_gambler",
    "score": 0.31
  },
  "consensus_accuracy": 0.621
}
```

#### How It Works
1. **Scores each expert's prediction** against actual results
2. **Updates expert weights** based on performance (learning rate varies by personality)
3. **Triggers peer learning** for predictions scoring > 0.7
4. **Records algorithm evolution** in database
5. **Updates competition rankings**

### 2. Get Expert Evolution History
**GET** `/experts/{expert_id}/evolution?limit=10`

Shows how an expert's algorithm has changed over time.

#### Response (200 OK)
```json
{
  "expert_id": "conservative_analyzer",
  "evolution_history": [
    {
      "version": 12,
      "algorithm_type": "weights",
      "previous_state": {
        "winner_confidence": 0.5,
        "spread_weight": 0.45
      },
      "new_state": {
        "winner_confidence": 0.52,
        "spread_weight": 0.48
      },
      "trigger_reason": "game_result_learning",
      "performance_before": 0.58,
      "performance_after": 0.61,
      "timestamp": "2025-01-15T10:30:00Z"
    }
  ],
  "total_versions": 12,
  "latest_version": 12
}
```

### 3. Get Performance Summary
**GET** `/experts/performance/summary`

Comprehensive performance overview of all personality experts.

#### Response (200 OK)
```json
{
  "timestamp": "2025-01-15T14:00:00Z",
  "total_experts": 15,
  "leaderboard": [
    {
      "expert_id": "statistics_purist",
      "name": "The Quant",
      "performance": {
        "games": 142,
        "avg_score": 0.684,
        "trend": "stable"
      }
    },
    {
      "expert_id": "fundamentalist_scholar",
      "name": "The Scholar",
      "performance": {
        "games": 142,
        "avg_score": 0.671,
        "trend": "improving"
      }
    }
  ],
  "strugglers": [
    {
      "expert_id": "chaos_theory_believer",
      "name": "The Chaos",
      "performance": {
        "games": 142,
        "avg_score": 0.487,
        "trend": "stable"
      }
    }
  ],
  "most_improved": {
    "expert_id": "value_hunter",
    "improvement": 0.08
  },
  "most_consistent": {
    "expert_id": "consensus_follower",
    "consistency": 0.91
  },
  "personality_performance": {
    "high_risk": {
      "avg_score": 0.523,
      "count": 3
    },
    "low_risk": {
      "avg_score": 0.641,
      "count": 3
    },
    "analytical": {
      "avg_score": 0.658,
      "count": 4
    },
    "emotional": {
      "avg_score": 0.492,
      "count": 1
    },
    "contrarian": {
      "avg_score": 0.541,
      "count": 4
    },
    "consensus": {
      "avg_score": 0.612,
      "count": 1
    }
  }
}
```

### 4. Trigger Manual Learning Cycle
**POST** `/experts/learning/trigger`

Manually triggers a learning cycle (useful for processing backlog).

#### Response (200 OK)
```json
{
  "status": "triggered",
  "message": "Learning cycle initiated in background",
  "timestamp": "2025-01-15T14:00:00Z"
}
```

### 5. Get Learning Queue Status
**GET** `/learning/queue/status`

Shows pending learning tasks.

#### Response (200 OK)
```json
{
  "total_tasks": 45,
  "processed": 30,
  "pending": 15,
  "by_type": {
    "game_result": 10,
    "peer_success": 3,
    "pattern_detected": 2
  },
  "by_priority": {
    "9": 2,  // Very high (failures to learn from)
    "8": 3,  // High (successes to reinforce)
    "5": 10  // Normal
  }
}
```

### 6. Get Peer Learning Network
**GET** `/peer-learning/network`

Visualizes knowledge transfer between experts.

#### Response (200 OK)
```json
{
  "network": {
    "conservative_analyzer": {
      "teaches": ["consensus_follower", "fundamentalist_scholar"],
      "learns_from": ["statistics_purist"],
      "influence_score": 2,
      "learning_score": 1
    },
    "risk_taking_gambler": {
      "teaches": ["underdog_champion"],
      "learns_from": ["sharp_money_follower", "value_hunter"],
      "influence_score": 1,
      "learning_score": 2
    }
  },
  "most_influential": "conservative_analyzer",
  "most_receptive": "consensus_follower",
  "total_edges": 23
}
```

## Learning Algorithm Details

### Performance Scoring
Each prediction is scored on three components:
- **Winner (40% weight)**: Correct winner = 0.4 points
- **Spread (30% weight)**: Score decreases linearly with error (14 points error = 0)
- **Total (30% weight)**: Score decreases linearly with error (20 points error = 0)

### Weight Adjustments
```python
adjustment_factor = (performance_score - 0.5) * learning_rate
```
- Learning rates vary by personality (0.04 to 0.16)
- Weights bounded between 0.0 and 1.0
- Factor-specific adjustments based on what worked/failed

### Peer Learning Rules
Knowledge is shared when:
- **High performers** (score > 0.7): Share successful factors
- **Consensus followers**: Learn from high-agreement predictions
- **Contrarians**: Learn opposite lessons from failures (score < 0.3)
- **Value seekers**: Learn from high-value wins (spread > 7)

### Priority System
Learning tasks are prioritized:
- **9 (Very High)**: Major failures requiring immediate learning
- **8 (High)**: Exceptional successes to reinforce
- **7 (Medium-High)**: Successful peer learning opportunities
- **5 (Normal)**: Standard game result processing

## Usage Example

```python
import requests
import json

# 1. Submit game results
result = {
    "winner": "KC",
    "final_score": {"home": 31, "away": 17},
    "actual_spread": -14,
    "actual_total": 48,
    "weather_impact": False,
    "injuries_impact": True
}

response = requests.post(
    "http://localhost:8001/api/v1/games/BUF@KC_20250119/results",
    json=result
)
print(f"Learning triggered: {response.json()}")

# 2. Check expert performance
perf = requests.get("http://localhost:8001/api/v1/experts/performance/summary")
print(f"Top expert: {perf.json()['leaderboard'][0]}")

# 3. View peer learning network
network = requests.get("http://localhost:8001/api/v1/peer-learning/network")
print(f"Most influential: {network.json()['most_influential']}")
```

## Error Codes

- **400**: Invalid game_id format or bad request data
- **404**: Expert or game not found
- **500**: Internal server error
- **503**: Database connection required (running in offline mode)

## Environment Variables

```bash
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```

Without these, the system runs in offline mode with no persistent learning.

## Notes

- Learning is **asynchronous** - the API returns immediately while learning continues in background
- Peer learning preserves **personality integrity** - experts share outcomes, not methodologies
- Evolution is **incremental** - large jumps in weights are prevented to maintain stability
- The system is **self-improving** - performance typically improves over the first 50-100 games