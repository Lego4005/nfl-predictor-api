# FastAPI Gateway Implementation Guide

## Overview

The NFL Predictor API Gateway is now fully implemented with:
- ✅ Complete REST API with all specified endpoints
- ✅ WebSocket support for real-time updates
- ✅ Supabase PostgreSQL integration
- ✅ Redis caching layer
- ✅ CORS middleware
- ✅ Request logging
- ✅ Error handling
- ✅ OpenAPI documentation

## Project Structure

```
/src/api/
├── main.py                      # FastAPI app with lifespan management
├── config.py                    # Settings and configuration
├── routers/
│   ├── experts.py               # Expert endpoints (4 routes)
│   ├── council.py               # Council endpoints (2 routes)
│   ├── bets.py                  # Betting endpoints (2 routes)
│   └── games.py                 # Game endpoints (2 routes)
├── websocket/
│   ├── manager.py               # Connection manager with subscriptions
│   └── handlers.py              # Event handlers for WS messages
├── models/
│   ├── expert.py                # Pydantic models for experts
│   ├── prediction.py            # Prediction models
│   ├── bet.py                   # Betting models
│   ├── council.py               # Council models
│   └── game.py                  # Game models
└── services/
    ├── database.py              # Supabase client wrapper
    └── cache.py                 # Redis cache service
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your credentials
nano .env
```

Required configuration:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379)

### 3. Start Redis (Optional but recommended)

```bash
# Start Redis server
redis-server

# Verify Redis is running
redis-cli ping  # Should return "PONG"
```

### 4. Run the API

```bash
# Using the startup script
./scripts/start_api.sh

# Or manually
uvicorn src.api.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **WebSocket**: ws://localhost:8000/ws/updates

## Implemented Endpoints

### Expert Endpoints

1. **GET /api/v1/experts**
   - Returns all 15 experts with current stats
   - Cache: 60 seconds
   - Rate limit: 100 req/min

2. **GET /api/v1/experts/{expert_id}/bankroll**
   - Detailed bankroll history
   - Query params: `timeframe`, `include_bets`
   - Cache: 30 seconds
   - Rate limit: 200 req/min

3. **GET /api/v1/experts/{expert_id}/predictions**
   - Expert predictions with confidence
   - Query params: `week`, `status`, `min_confidence`
   - Cache: 120 seconds
   - Rate limit: 150 req/min

4. **GET /api/v1/experts/{expert_id}/memories**
   - Episodic memories for Memory Lane
   - Query params: `limit`, `offset`, `importance_min`
   - Cache: 300 seconds
   - Rate limit: 100 req/min

### Council Endpoints

5. **GET /api/v1/council/current**
   - Top 5 council members
   - Query params: `week`
   - Cache: 1 hour
   - Rate limit: 200 req/min

6. **GET /api/v1/council/consensus/{game_id}**
   - Weighted voting consensus
   - Cache: 60 seconds
   - Rate limit: 150 req/min

### Betting Endpoints

7. **GET /api/v1/bets/live**
   - Real-time betting feed
   - Query params: `game_id`, `expert_id`, `limit`, `status`
   - Cache: 10 seconds (near real-time)
   - Rate limit: 300 req/min

8. **GET /api/v1/bets/expert/{expert_id}/history**
   - Bet history for expert
   - Query params: `limit`, `offset`, `result`
   - Cache: 60 seconds
   - Rate limit: 150 req/min

### Game Endpoints

9. **GET /api/v1/games/week/{week_number}**
   - All games for specific week
   - Query params: `include_predictions`, `include_odds`
   - Cache: 300 seconds
   - Rate limit: 200 req/min

10. **GET /api/v1/games/battles/active**
    - Active prediction battles
    - Query params: `week`, `min_difference`
    - Cache: 60 seconds
    - Rate limit: 150 req/min

### WebSocket Endpoint

11. **WS /ws/updates**
    - Real-time updates
    - Channels: `bets`, `lines`, `eliminations`, `bankroll`
    - Event types: `bet_placed`, `line_movement`, `expert_eliminated`, `bankroll_updated`

## WebSocket Usage

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Subscribe to Channels

```javascript
// Subscribe to bet and line movement updates
ws.send(JSON.stringify({
  type: 'subscribe',
  channels: ['bets', 'lines'],
  filters: {
    expert_ids: ['the-analyst', 'the-gambler'],
    game_ids: ['2025_05_KC_BUF']
  }
}));
```

### Receive Events

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case 'bet_placed':
      console.log(`${message.expert_name} placed bet: $${message.bet_amount}`);
      break;

    case 'line_movement':
      console.log(`Line moved: ${message.old_value} → ${message.new_value}`);
      break;

    case 'expert_eliminated':
      console.log(`${message.expert_name} eliminated!`);
      break;

    case 'bankroll_updated':
      console.log(`${message.expert_id} bankroll: $${message.new_balance}`);
      break;
  }
};
```

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx pytest-cov

# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/api tests/

# Run specific test file
pytest tests/api/test_experts.py -v
```

### Manual Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test experts endpoint
curl http://localhost:8000/api/v1/experts

# Test with query params
curl "http://localhost:8000/api/v1/experts/the-analyst/predictions?week=5"

# Test WebSocket (using websocat)
websocat ws://localhost:8000/ws/updates
```

## Database Schema Requirements

The API expects these Supabase tables:

### `experts` table
- `expert_id` (text, primary key)
- `name` (text)
- `emoji` (text)
- `archetype` (text)
- `current_bankroll` (numeric)
- `starting_bankroll` (numeric)
- `bankroll_change_percent` (numeric)
- `bankroll_status` (text)
- `accuracy` (numeric)
- `win_rate` (numeric)
- `total_bets` (integer)
- `roi` (numeric)
- `specialization_category` (text)
- `specialization_weight` (numeric)

### `predictions` table
- `prediction_id` (text, primary key)
- `expert_id` (text, foreign key)
- `game_id` (text)
- `category` (text)
- `prediction` (text)
- `confidence` (numeric)
- `reasoning` (text)
- `bet_placed` (boolean)
- `bet_amount` (numeric)
- `status` (text)
- `created_at` (timestamp)

### `bets` table
- `bet_id` (text, primary key)
- `expert_id` (text, foreign key)
- `game_id` (text)
- `bet_type` (text)
- `bet_amount` (numeric)
- `prediction` (text)
- `confidence` (numeric)
- `risk_level` (text)
- `status` (text)
- `placed_at` (timestamp)
- `settled_at` (timestamp)
- `potential_payout` (numeric)

### Additional tables needed:
- `council_members`
- `consensus_predictions`
- `games`
- `memories`
- `bankroll_history`
- `prediction_battles`

## Caching Strategy

The API uses Redis for caching with different TTLs:

- **Experts**: 60s (changes infrequently)
- **Bets**: 10s (near real-time)
- **Predictions**: 120s (moderate frequency)
- **Council**: 3600s (changes weekly)
- **Games**: 300s (static during week)

Cache keys format: `{prefix}:{function_name}:{args}:{kwargs}`

Example: `experts:get_experts:`

## Performance Optimization

### Database Queries
- Use indexes on `expert_id`, `game_id`, `week`
- Implement query result caching
- Use connection pooling

### Cache Invalidation
```python
# Invalidate cache when data changes
await cache_service.delete("expert_*")
```

### Rate Limiting
Currently implemented at application level. For production, consider:
- API Gateway rate limiting (Cloudflare, AWS API Gateway)
- Redis-based distributed rate limiting
- Per-user rate limits with authentication

## Deployment

### Production Checklist

- [ ] Set `DEBUG=false` in environment
- [ ] Use production Supabase URL and keys
- [ ] Configure Redis persistence
- [ ] Set up SSL/TLS for WebSocket (WSS)
- [ ] Enable logging to external service
- [ ] Set up monitoring (Sentry, DataDog)
- [ ] Configure load balancer for multiple instances
- [ ] Set up backup/failover for Redis
- [ ] Implement rate limiting at API gateway
- [ ] Enable request validation
- [ ] Set up CORS for production domains

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY .env .env

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build image
docker build -t nfl-predictor-api .

# Run container
docker run -p 8000:8000 --env-file .env nfl-predictor-api
```

## Next Steps

1. **Implement Supabase tables** - Create database schema
2. **Seed sample data** - Add 15 experts and test data
3. **Test all endpoints** - Verify with real database
4. **Frontend integration** - Connect React app
5. **Load testing** - Test with 100+ concurrent users
6. **Production deployment** - Deploy to cloud platform

## Support

- **API Docs**: http://localhost:8000/docs
- **Architecture**: `/docs/API_GATEWAY_ARCHITECTURE.md`
- **Project Root**: `/home/iris/code/experimental/nfl-predictor-api`

---

**Status**: ✅ API Gateway implementation complete and ready for testing!