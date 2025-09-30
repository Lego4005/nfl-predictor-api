# 🚀 RUN THE API - Quick Command Reference

## Step 1: Activate Virtual Environment

```bash
cd /home/iris/code/experimental/nfl-predictor-api
source venv/bin/activate
```

## Step 2: Install Dependencies (if not done)

```bash
pip install -r requirements.txt
```

## Step 3: Start Redis (Optional but Recommended)

```bash
# Option A: Start in foreground (see logs)
redis-server

# Option B: Start in background
redis-server --daemonize yes

# Verify it's running
redis-cli ping  # Should return "PONG"
```

## Step 4: Run the API

### Method 1: Using Startup Script (RECOMMENDED)
```bash
./scripts/start_api.sh
```

### Method 2: Direct uvicorn Command
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 3: Python Module
```bash
python -m uvicorn src.api.main:app --reload --port 8000
```

## 🎯 Verify It's Running

Open browser to: http://localhost:8000/docs

Or test with curl:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "websocket_connections": 0
}
```

## 📡 Test All Endpoints

```bash
# Get all experts
curl http://localhost:8000/api/v1/experts | jq .

# Get expert bankroll
curl http://localhost:8000/api/v1/experts/the-analyst/bankroll | jq .

# Get expert predictions
curl "http://localhost:8000/api/v1/experts/the-analyst/predictions?week=5" | jq .

# Get council members
curl http://localhost:8000/api/v1/council/current | jq .

# Get live bets
curl http://localhost:8000/api/v1/bets/live | jq .

# Get week games
curl http://localhost:8000/api/v1/games/week/5 | jq .

# Get battles
curl http://localhost:8000/api/v1/games/battles/active | jq .
```

## 🔌 Test WebSocket

### JavaScript (Browser Console)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/updates');
ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log('Message:', JSON.parse(e.data));
ws.send(JSON.stringify({type: 'subscribe', channels: ['bets', 'lines']}));
```

### Using websocat (CLI)
```bash
# Install: brew install websocat
websocat ws://localhost:8000/ws/updates
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Use different port
uvicorn src.api.main:app --port 8001
```

### Import Errors
```bash
# Make sure you're in venv
source venv/bin/activate
pip install -r requirements.txt
```

### Supabase Connection Failed
```bash
# Check environment variables
cat .env | grep SUPABASE

# Update .env with your credentials
nano .env
```

### Redis Not Running
```bash
# Redis is optional - API will work without it
# To start Redis:
redis-server

# Or install it:
# Ubuntu: sudo apt install redis-server
# macOS: brew install redis
```

## 📚 Documentation

- **Quick Start**: `/docs/API_QUICKSTART.md`
- **Full Guide**: `/docs/API_IMPLEMENTATION_GUIDE.md`
- **Architecture**: `/docs/API_GATEWAY_ARCHITECTURE.md`
- **Summary**: `/docs/API_SUMMARY.md`
- **Interactive Docs**: http://localhost:8000/docs

## 🎉 You're Ready!

Your FastAPI gateway is now running and ready to serve the NFL AI Expert Prediction Platform!

Access the interactive documentation at: http://localhost:8000/docs
