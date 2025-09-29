# API Gateway Architecture - FastAPI Implementation

**System**: NFL AI Expert Prediction Platform
**Framework**: FastAPI (Python 3.11+)
**Created**: 2025-09-29

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (TypeScript)               │
│  • TanStack Query for data fetching                         │
│  • WebSocket client for real-time updates                   │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTPS + WSS
               ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Gateway (Port 8000)                     │
│  ┌────────────────────┐  ┌──────────────────────┐          │
│  │  REST API Routes   │  │  WebSocket Routes    │          │
│  │  /api/v1/*         │  │  /ws/*               │          │
│  └────────┬───────────┘  └──────────┬───────────┘          │
│           │                         │                        │
│  ┌────────▼─────────────────────────▼───────────┐          │
│  │         Middleware Layer                      │          │
│  │  • CORS • Auth • Rate Limiting • Logging     │          │
│  └────────┬──────────────────────────────────────┘          │
└───────────┼──────────────────────────────────────────────────┘
            │
    ┌───────┴───────┐
    │               │
    ▼               ▼
┌────────────┐  ┌──────────────┐
│ Redis      │  │ Supabase DB  │
│ Cache      │  │ PostgreSQL   │
└────────────┘  └──────────────┘
```

---

## Core Endpoints Specification

### 1. Expert Endpoints

#### GET /api/v1/experts
List all 15 AI experts with current stats.

**Response**:
```json
{
  "experts": [
    {
      "expert_id": "the-analyst",
      "name": "The Analyst",
      "emoji": "📊",
      "archetype": "data_driven",
      "bankroll": {
        "current": 12450.00,
        "starting": 10000.00,
        "change_percent": 24.5,
        "status": "safe"
      },
      "performance": {
        "accuracy": 0.625,
        "win_rate": 0.615,
        "total_bets": 42,
        "roi": 0.245
      },
      "specialization": {
        "category": "statistical_analysis",
        "weight": 0.90
      }
    }
  ],
  "timestamp": "2025-09-29T19:30:00Z"
}
```

**Caching**: 60 seconds
**Rate Limit**: 100 requests/minute

---

#### GET /api/v1/experts/{expert_id}/bankroll
Get detailed bankroll history for specific expert.

**Path Parameters**:
- `expert_id`: Expert identifier (e.g., "the-analyst")

**Query Parameters**:
- `timeframe`: "week" | "month" | "season" (default: "week")
- `include_bets`: boolean (default: false)

**Response**:
```json
{
  "expert_id": "the-analyst",
  "current_balance": 12450.00,
  "starting_balance": 10000.00,
  "peak_balance": 13200.00,
  "lowest_balance": 9200.00,
  "total_wagered": 45600.00,
  "total_won": 28300.00,
  "total_lost": 15500.00,
  "history": [
    {
      "timestamp": "2025-09-29T14:00:00Z",
      "balance": 12450.00,
      "change": 850.00,
      "reason": "bet_won"
    }
  ],
  "risk_metrics": {
    "volatility": 0.12,
    "sharpe_ratio": 1.85,
    "max_drawdown": 0.08
  }
}
```

**Caching**: 30 seconds
**Rate Limit**: 200 requests/minute

---

#### GET /api/v1/experts/{expert_id}/predictions
Get expert's predictions with confidence levels.

**Query Parameters**:
- `week`: Week number (default: current week)
- `status`: "pending" | "completed" | "all" (default: "all")
- `min_confidence`: 0.0 - 1.0 (filter by minimum confidence)

**Response**:
```json
{
  "expert_id": "the-analyst",
  "week": 5,
  "predictions": [
    {
      "prediction_id": "pred_123",
      "game_id": "2025_05_KC_BUF",
      "category": "spread",
      "prediction": "KC -2.5",
      "confidence": 0.78,
      "reasoning": "Statistical edge in road games, sharp money on Chiefs",
      "bet_placed": true,
      "bet_amount": 850.00,
      "status": "pending",
      "created_at": "2025-09-29T10:00:00Z"
    }
  ]
}
```

**Caching**: 120 seconds
**Rate Limit**: 150 requests/minute

---

#### GET /api/v1/experts/{expert_id}/memories
Get episodic memories for Memory Lane feature.

**Query Parameters**:
- `limit`: Number of memories (default: 20, max: 100)
- `offset`: Pagination offset
- `importance_min`: Filter by importance score (0.0 - 1.0)

**Response**:
```json
{
  "expert_id": "the-gambler",
  "memories": [
    {
      "memory_id": "mem_456",
      "game_id": "2023_03_BUF_MIA",
      "memory_type": "lesson_learned",
      "content": "Similar weather conditions, same spread. I picked underdog and was WRONG. Lost $1,200.",
      "emotional_valence": -0.7,
      "importance_score": 0.85,
      "recalled_count": 3,
      "created_at": "2023-09-24T18:00:00Z"
    }
  ],
  "total_count": 156,
  "pagination": {
    "offset": 0,
    "limit": 20,
    "has_more": true
  }
}
```

**Caching**: 300 seconds (memories don't change often)
**Rate Limit**: 100 requests/minute

---

### 2. Council Endpoints

#### GET /api/v1/council/current
Get current week's top 5 council members.

**Query Parameters**:
- `week`: Week number (default: current week)

**Response**:
```json
{
  "week": 5,
  "council_members": [
    {
      "expert_id": "the-analyst",
      "rank": 1,
      "selection_score": 0.892,
      "vote_weight": 0.25,
      "reason_selected": "Top accuracy (62.5%) + strong recent performance"
    },
    {
      "expert_id": "sharp-money-follower",
      "rank": 2,
      "selection_score": 0.875,
      "vote_weight": 0.22,
      "reason_selected": "Excellent line movement detection"
    }
  ],
  "selection_criteria": {
    "accuracy_weight": 0.35,
    "recent_performance_weight": 0.25,
    "consistency_weight": 0.20,
    "calibration_weight": 0.10,
    "specialization_weight": 0.10
  }
}
```

**Caching**: 1 hour (council changes weekly)
**Rate Limit**: 200 requests/minute

---

#### GET /api/v1/council/consensus/{game_id}
Get weighted voting consensus for specific game.

**Path Parameters**:
- `game_id`: Game identifier (e.g., "2025_05_KC_BUF")

**Response**:
```json
{
  "game_id": "2025_05_KC_BUF",
  "consensus": {
    "spread": {
      "prediction": "KC -2.5",
      "confidence": 0.72,
      "agreement_level": 0.85,
      "vote_breakdown": {
        "KC -2.5": 0.72,
        "BUF +2.5": 0.28
      }
    },
    "winner": {
      "prediction": "KC",
      "confidence": 0.68,
      "agreement_level": 0.75
    }
  },
  "expert_votes": [
    {
      "expert_id": "the-analyst",
      "vote_weight": 0.25,
      "prediction": "KC -2.5",
      "confidence": 0.78
    }
  ],
  "disagreements": [
    {
      "expert_a": "the-gambler",
      "expert_b": "the-rebel",
      "category": "spread",
      "difference": "5 points"
    }
  ]
}
```

**Caching**: 60 seconds
**Rate Limit**: 150 requests/minute

---

### 3. Betting Endpoints

#### GET /api/v1/bets/live
Get real-time betting feed showing recent expert bets.

**Query Parameters**:
- `game_id`: Filter by specific game (optional)
- `expert_id`: Filter by specific expert (optional)
- `limit`: Number of bets (default: 50, max: 200)
- `status`: "pending" | "won" | "lost" | "push" (default: "pending")

**Response**:
```json
{
  "bets": [
    {
      "bet_id": "bet_789",
      "expert_id": "the-gambler",
      "expert_name": "The Gambler",
      "expert_emoji": "🎲",
      "game_id": "2025_05_KC_BUF",
      "bet_type": "spread",
      "prediction": "KC -2.5",
      "bet_amount": 2400.00,
      "bankroll_percentage": 0.38,
      "vegas_odds": "-110",
      "confidence": 0.92,
      "risk_level": "extreme",
      "reasoning": "I'm all in on this one - KC road dominance is REAL",
      "potential_payout": 4581.82,
      "placed_at": "2025-09-29T17:30:00Z",
      "status": "pending"
    }
  ],
  "summary": {
    "total_at_risk": 8450.00,
    "potential_payout": 16231.50,
    "avg_confidence": 0.81
  }
}
```

**Caching**: 10 seconds (near real-time)
**Rate Limit**: 300 requests/minute

---

#### GET /api/v1/bets/expert/{expert_id}/history
Get bet history for specific expert.

**Path Parameters**:
- `expert_id`: Expert identifier

**Query Parameters**:
- `limit`: Number of bets (default: 50)
- `offset`: Pagination offset
- `result`: "won" | "lost" | "push" | "all" (default: "all")

**Response**:
```json
{
  "expert_id": "the-analyst",
  "bet_history": [
    {
      "bet_id": "bet_123",
      "game_id": "2025_04_SF_LAR",
      "bet_amount": 600.00,
      "result": "won",
      "payout": 1145.45,
      "profit": 545.45,
      "settled_at": "2025-09-22T20:00:00Z"
    }
  ],
  "statistics": {
    "total_bets": 42,
    "wins": 26,
    "losses": 14,
    "pushes": 2,
    "win_rate": 0.619,
    "roi": 0.245,
    "avg_bet_size": 1085.71
  }
}
```

**Caching**: 60 seconds
**Rate Limit**: 150 requests/minute

---

### 4. Game Endpoints

#### GET /api/v1/games/week/{week_number}
Get all games for specific week with predictions.

**Path Parameters**:
- `week_number`: NFL week number (1-18)

**Query Parameters**:
- `include_predictions`: boolean (default: true)
- `include_odds`: boolean (default: true)

**Response**:
```json
{
  "week": 5,
  "games": [
    {
      "game_id": "2025_05_KC_BUF",
      "home_team": "BUF",
      "away_team": "KC",
      "game_time": "2025-10-06T16:25:00Z",
      "venue": "Highmark Stadium",
      "weather": {
        "temperature": 52,
        "wind_speed": 12,
        "conditions": "Partly Cloudy"
      },
      "vegas_lines": {
        "spread": -2.5,
        "moneyline_home": -130,
        "moneyline_away": +110,
        "total": 47.5
      },
      "council_consensus": {
        "spread": "KC -2.5",
        "confidence": 0.72
      },
      "expert_count": {
        "predictions": 15,
        "bets_placed": 12
      }
    }
  ]
}
```

**Caching**: 300 seconds
**Rate Limit**: 200 requests/minute

---

### 5. Prediction Battle Endpoints

#### GET /api/v1/battles/active
Get active prediction battles where experts disagree.

**Query Parameters**:
- `week`: Week number (default: current)
- `min_difference`: Minimum prediction difference to qualify as battle (default: 3.0)

**Response**:
```json
{
  "battles": [
    {
      "battle_id": "battle_456",
      "game_id": "2025_05_KC_BUF",
      "category": "spread",
      "expert_a": {
        "expert_id": "the-analyst",
        "prediction": "KC -2.5",
        "confidence": 0.78,
        "bet_amount": 850.00,
        "reasoning": "Statistical edge in road games"
      },
      "expert_b": {
        "expert_id": "the-gambler",
        "prediction": "BUF +2.5",
        "confidence": 0.92,
        "bet_amount": 2400.00,
        "reasoning": "Home underdog value, playoff atmosphere"
      },
      "head_to_head_record": {
        "expert_a_wins": 23,
        "expert_b_wins": 15,
        "last_5": "AABAA"
      },
      "user_votes": {
        "expert_a": 234,
        "expert_b": 189
      }
    }
  ]
}
```

**Caching**: 60 seconds
**Rate Limit**: 150 requests/minute

---

## WebSocket Routes

### WS /ws/updates
Real-time updates for betting feed, line movements, eliminations.

**Connection**: WebSocket (WSS in production)
**Authentication**: Optional token in query params

**Message Types**:

```typescript
// Client → Server (Subscribe)
{
  "type": "subscribe",
  "channels": ["bets", "lines", "eliminations"],
  "filters": {
    "expert_ids": ["the-analyst", "the-gambler"],
    "game_ids": ["2025_05_KC_BUF"]
  }
}

// Server → Client (Bet Placed)
{
  "type": "bet_placed",
  "bet_id": "bet_789",
  "expert_id": "the-gambler",
  "expert_name": "The Gambler",
  "game_id": "2025_05_KC_BUF",
  "bet_amount": 2400.00,
  "prediction": "KC -2.5",
  "confidence": 0.92,
  "timestamp": "2025-09-29T17:30:00Z"
}

// Server → Client (Line Movement)
{
  "type": "line_movement",
  "game_id": "2025_05_KC_BUF",
  "line_type": "spread",
  "old_value": -2.5,
  "new_value": -3.0,
  "movement": 0.5,
  "timestamp": "2025-09-29T18:00:00Z"
}

// Server → Client (Expert Eliminated)
{
  "type": "expert_eliminated",
  "expert_id": "the-chaos",
  "expert_name": "The Chaos",
  "final_bankroll": 0.00,
  "elimination_reason": "bankrupt",
  "final_bet": {
    "game_id": "2025_05_TEN_IND",
    "bet_amount": 2100.00,
    "result": "lost"
  },
  "season_stats": {
    "total_bets": 89,
    "win_rate": 0.38,
    "roi": -1.0
  },
  "timestamp": "2025-09-29T20:00:00Z"
}

// Server → Client (Bankroll Update)
{
  "type": "bankroll_updated",
  "expert_id": "the-analyst",
  "old_balance": 11600.00,
  "new_balance": 12450.00,
  "change": 850.00,
  "reason": "bet_settled",
  "bet_id": "bet_123",
  "timestamp": "2025-09-29T20:15:00Z"
}
```

**Heartbeat**: Every 30 seconds
**Reconnection**: Exponential backoff (1s, 2s, 4s, 8s, 16s max)

---

## Middleware Stack

### 1. CORS Middleware
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Rate Limiting Middleware
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Usage in routes:
@app.get("/api/v1/experts")
@limiter.limit("100/minute")
async def get_experts(request: Request):
    ...
```

### 3. Authentication Middleware (Optional)
```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials: HTTPBearer = Depends(security)):
    token = credentials.credentials
    # Validate JWT token with Supabase
    # Return user if valid, raise 401 if invalid
```

### 4. Logging Middleware
```python
import logging
from fastapi import Request
import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logging.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={duration:.3f}s"
    )
    return response
```

---

## Caching Strategy

### Redis Cache Implementation

```python
import redis.asyncio as redis
from functools import wraps
import json

# Initialize Redis
redis_client = redis.from_url("redis://localhost:6379")

def cache(ttl: int = 60):
    """Decorator for caching responses"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # Try to get from cache
            cached = await redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Call function
            result = await func(*args, **kwargs)

            # Store in cache
            await redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )

            return result
        return wrapper
    return decorator

# Usage:
@app.get("/api/v1/experts")
@cache(ttl=60)
async def get_experts():
    # Query database
    ...
```

### Cache Invalidation

```python
async def invalidate_expert_cache(expert_id: str):
    """Invalidate all cache entries for an expert"""
    pattern = f"*expert*{expert_id}*"
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)
```

---

## Project Structure

```
/src/api/
├── main.py                  # FastAPI app initialization
├── config.py                # Configuration and settings
├── dependencies.py          # Dependency injection
├── middleware/
│   ├── __init__.py
│   ├── cors.py
│   ├── rate_limit.py
│   ├── auth.py
│   └── logging.py
├── routers/
│   ├── __init__.py
│   ├── experts.py           # Expert endpoints
│   ├── council.py           # Council endpoints
│   ├── bets.py              # Betting endpoints
│   ├── games.py             # Game endpoints
│   └── battles.py           # Prediction battle endpoints
├── websocket/
│   ├── __init__.py
│   ├── connection_manager.py
│   └── handlers.py
├── models/
│   ├── __init__.py
│   ├── expert.py            # Pydantic models
│   ├── prediction.py
│   ├── bet.py
│   └── game.py
├── services/
│   ├── __init__.py
│   ├── expert_service.py    # Business logic
│   ├── prediction_service.py
│   ├── betting_service.py
│   └── cache_service.py
└── utils/
    ├── __init__.py
    ├── database.py          # Supabase client
    └── redis_client.py      # Redis client
```

---

## Implementation Checklist

### Phase 1: Core Setup (Day 1-2)
- [ ] Initialize FastAPI project structure
- [ ] Setup Supabase client connection
- [ ] Setup Redis client connection
- [ ] Configure CORS and middleware
- [ ] Create Pydantic models for responses

### Phase 2: Expert Endpoints (Day 2-3)
- [ ] Implement GET /api/v1/experts
- [ ] Implement GET /api/v1/experts/{id}/bankroll
- [ ] Implement GET /api/v1/experts/{id}/predictions
- [ ] Implement GET /api/v1/experts/{id}/memories
- [ ] Add caching to all endpoints

### Phase 3: Council & Betting (Day 3-4)
- [ ] Implement GET /api/v1/council/current
- [ ] Implement GET /api/v1/council/consensus/{game_id}
- [ ] Implement GET /api/v1/bets/live
- [ ] Implement GET /api/v1/bets/expert/{id}/history

### Phase 4: Games & Battles (Day 4)
- [ ] Implement GET /api/v1/games/week/{week}
- [ ] Implement GET /api/v1/battles/active

### Phase 5: WebSocket (Day 5)
- [ ] Setup WebSocket connection manager
- [ ] Implement bet_placed event
- [ ] Implement line_movement event
- [ ] Implement expert_eliminated event
- [ ] Implement bankroll_updated event

### Phase 6: Testing (Day 5)
- [ ] Write unit tests for all endpoints
- [ ] Write integration tests
- [ ] Load test with 100 concurrent users
- [ ] Document API with OpenAPI

---

**Next Step**: Create `/src/api/main.py` with FastAPI initialization