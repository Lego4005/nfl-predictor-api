# FastAPI Gateway - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites

- Python 3.11+
- Redis (optional, but recommended)
- Supabase account with configured database

### 1. Install Dependencies

```bash
cd /home/iris/code/experimental/nfl-predictor-api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env.api

# Edit with your credentials
nano .env.api
```

Minimum required configuration:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
REDIS_URL=redis://localhost:6379
```

### 3. Start Redis (Optional)

```bash
# Start Redis in background
redis-server --daemonize yes

# Verify it's running
redis-cli ping  # Should return "PONG"
```

### 4. Run the API

**Option A: Using the startup script (recommended)**
```bash
./scripts/start_api.sh
```

**Option B: Direct uvicorn command**
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Option C: Python directly**
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

### 5. Verify It's Working

Open your browser to:
- **API Root**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Interactive Swagger UI)
- **Health Check**: http://localhost:8000/health

## 📡 Test the Endpoints

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Get all experts
curl http://localhost:8000/api/v1/experts

# Get expert bankroll
curl http://localhost:8000/api/v1/experts/the-analyst/bankroll

# Get council
curl http://localhost:8000/api/v1/council/current

# Get live bets
curl http://localhost:8000/api/v1/bets/live
```

### Using httpie (prettier output)

```bash
# Install httpie
pip install httpie

# Test endpoints
http localhost:8000/api/v1/experts
http localhost:8000/api/v1/council/current
http localhost:8000/api/v1/bets/live
```

### Using the Interactive Docs

1. Go to http://localhost:8000/docs
2. Click on any endpoint
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See the response!

## 🔌 Test WebSocket Connection

### Using JavaScript (Browser Console)

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/updates');

ws.onopen = () => {
  console.log('Connected!');

  // Subscribe to channels
  ws.send(JSON.stringify({
    type: 'subscribe',
    channels: ['bets', 'lines', 'eliminations']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

### Using websocat (CLI tool)

```bash
# Install websocat
# macOS: brew install websocat
# Ubuntu: snap install websocat

# Connect to WebSocket
websocat ws://localhost:8000/ws/updates

# Send subscription message
{"type": "subscribe", "channels": ["bets", "lines"]}
```

## 📊 API Endpoints Summary

| Endpoint | Method | Description | Cache |
|----------|--------|-------------|-------|
| `/api/v1/experts` | GET | All 15 experts | 60s |
| `/api/v1/experts/{id}/bankroll` | GET | Bankroll history | 30s |
| `/api/v1/experts/{id}/predictions` | GET | Expert predictions | 120s |
| `/api/v1/experts/{id}/memories` | GET | Episodic memories | 300s |
| `/api/v1/council/current` | GET | Top 5 council | 1h |
| `/api/v1/council/consensus/{game_id}` | GET | Voting consensus | 60s |
| `/api/v1/bets/live` | GET | Live betting feed | 10s |
| `/api/v1/bets/expert/{id}/history` | GET | Bet history | 60s |
| `/api/v1/games/week/{week}` | GET | Week games | 300s |
| `/api/v1/games/battles/active` | GET | Prediction battles | 60s |
| `/ws/updates` | WS | Real-time updates | N/A |

## 🎯 Example Requests

### Get Expert Predictions for Week 5

```bash
curl "http://localhost:8000/api/v1/experts/the-analyst/predictions?week=5&status=pending&min_confidence=0.7"
```

Response:
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
      "reasoning": "Statistical edge in road games",
      "bet_placed": true,
      "bet_amount": 850.00,
      "status": "pending"
    }
  ]
}
```

### Get Live Bets for Specific Game

```bash
curl "http://localhost:8000/api/v1/bets/live?game_id=2025_05_KC_BUF&limit=10"
```

### Get Council Consensus

```bash
curl "http://localhost:8000/api/v1/council/consensus/2025_05_KC_BUF"
```

## 🐛 Troubleshooting

### Issue: Import errors

**Solution**: Make sure you're in the virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Redis connection failed

**Solution**: Redis is optional. The API will work without it (no caching).
```bash
# Start Redis
redis-server

# Or disable Redis by setting
REDIS_URL=redis://localhost:6379  # Leave as is, API will handle failures gracefully
```

### Issue: Supabase connection failed

**Solution**: Check your environment variables
```bash
# Verify .env file has correct credentials
cat .env | grep SUPABASE
```

### Issue: Port 8000 already in use

**Solution**: Use a different port
```bash
uvicorn src.api.main:app --port 8001
```

### Issue: CORS errors from frontend

**Solution**: Add your frontend URL to CORS_ORIGINS in .env
```env
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://your-domain.com
```

## 📝 Development Tips

### Hot Reload

The `--reload` flag enables automatic restart on code changes:
```bash
uvicorn src.api.main:app --reload
```

### View Logs

Logs are printed to console. To save to file:
```bash
uvicorn src.api.main:app --log-config logging.conf > api.log 2>&1
```

### Debug Mode

Enable debug mode in .env:
```env
DEBUG=true
LOG_LEVEL=DEBUG
```

### Run Tests

```bash
# Run all tests
pytest tests/api/

# Run with coverage
pytest --cov=src/api tests/api/

# Run specific test
pytest tests/api/test_experts.py::test_get_experts -v
```

## 🔒 Security Notes

### For Development
- Using `DEBUG=true` is fine
- HTTP (not HTTPS) is acceptable
- CORS can be permissive

### For Production
- Set `DEBUG=false`
- Use HTTPS/WSS (not HTTP/WS)
- Restrict CORS to your domain only
- Use environment secrets management
- Enable rate limiting at API gateway level
- Add authentication to sensitive endpoints

## 🚀 Next Steps

1. **Connect Frontend**: Update frontend to use `http://localhost:8000`
2. **Seed Database**: Add test data to Supabase tables
3. **Test WebSocket**: Verify real-time updates work
4. **Load Test**: Use locust or k6 for performance testing
5. **Deploy**: Deploy to cloud platform (Vercel, AWS, etc.)

## 📚 Additional Resources

- **Full API Docs**: `/docs/API_GATEWAY_ARCHITECTURE.md`
- **Implementation Guide**: `/docs/API_IMPLEMENTATION_GUIDE.md`
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

## 💡 Pro Tips

### Use jq for Pretty JSON

```bash
curl http://localhost:8000/api/v1/experts | jq .
```

### Monitor Redis Cache

```bash
# Watch Redis commands
redis-cli monitor

# Check cache keys
redis-cli keys "*"

# Get cache stats
redis-cli info stats
```

### Check API Performance

```bash
# Add timing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/experts

# Create curl-format.txt:
time_total: %{time_total}s
```

---

**Ready to build!** 🎉

Your FastAPI gateway is now running and ready to serve the NFL AI Expert Prediction Platform!