# Expert Council Betting System - Deployment & Startup Guide

## Overview

This guide walks you through deploying and starting the complete Expert Council Betting System, from initial setup through running your first predictions.

## Prerequisites

### Required Sof
- **Node.js**: 18.x or 20.x
- **Python**: 3.9+
- **Docker**: Latest version with Docker Compose
- **Git**: For repository management

### External Services
- **Supabase Project**: PostgreSQL database with pgvector extension
- **Neo4j Database**: For provenance tracking (optional but recommended)
- **Redis**: For caching (optional but recommended for performance)

### API Keys Required
- **OpenAI API Key**: For LLM calls
- **Anthropic API Key**: For Claude models
- **DeepSeek API Key**: For DeepSeek models (free tier available)
- **ESPN API Key**: For NFL data
- **SportsData.io API Key**: For additional sports data
- **Odds API Key**: For betting odds data

## Phase 1: Environment Setup

### 1.1 Clone and Setup Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd nfl-predictor-api

# Install Node.js dependencies
npm install

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

### 1.2 Environment Configuration

Create your environment files:

```bash
# Copy environment templates
cp .env.example .env
cp .env.production.template .env.production
```

Edit `.env` with your configuration:

```bash
# Database Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# LLM API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
DEEPSEEK_API_KEY=your-deepseek-key

# Sports Data APIs
ESPN_API_KEY=your-espn-key
SPORTSDATA_IO_KEY=your-sportsdata-key
ODDS_API_KEY=your-odds-key

# System Configuration
RUN_ID=run_2025_pilot4
NODE_ENV=development

# Optional Services
REDIS_URL=redis://localhost:6379
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-neo4j-password
```

## Phase 2: Database Setup

### 2.1 Supabase Database Migration

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Run all migrations
supabase db push

# Verify migrations
supabase db diff
```

### 2.2 Initialize Expert Data

```bash
# Run the expert initialization script
python scripts/initialize_expert_system.py

# Verify expert bankrolls
python -c "
from src.services.supabase_service import SupabaseService
supabase = SupabaseService()
result = supabase.table('expert_bankroll').select('*').eq('run_id', 'run_2025_pilot4').execute()
print(f'Initialized {len(result.data)} expert bankrolls')
"
```

### 2.3 Populate Initial Data

```bash
# Fetch current NFL season data
node scripts/fetch_2025_nfl_season.mjs

# Populate historical data (optional, for better predictions)
python scripts/populate_database.py --years 2020-2023

# Verify data population
python scripts/check_games_count.mjs
```

## Phase 3: Service Deployment

### 3.1 Start Core Services

#### Option A: Docker Compose (Recommended)

```bash
# Start all services with Docker
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Option B: Manual Service Startup

```bash
# Terminal 1: Start FastAPI backend
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Start WebSocket server
node src/websocket/server.js

# Terminal 3: Start frontend (if applicable)
npm run dev

# Terminal 4: Start Redis (if not using Docker)
redis-server

# Terminal 5: Start Neo4j (if not using Docker)
neo4j start
```

### 3.2 Verify Service Health

```bash
# Check API health
curl http://localhost:8000/health

# Check WebSocket connection
wscat -c ws://localhost:8080/ws/live-updates

# Check database connectivity
python -c "
from src.services.supabase_service import SupabaseService
supabase = SupabaseService()
result = supabase.table('games').select('count', count='exact').limit(1).execute()
print(f'Database connected: {result.count} games available')
"
```

## Phase 4: Agentuity Setup (Expert Orchestration)

### 4.1 Configure Agentuity Project

```bash
# Navigate to Agentuity directory
cd agentuity

# Install dependencies
npm install

# Configure agents
cp agents/game-orchestrator/config.example.json agents/game-orchestrator/config.json
cp agents/reflection-agent/config.example.json agents/reflection-agent/config.json

# Update configuration with your API endpoints
# Edit config.json files to point to your FastAPI server
```

### 4.2 Deploy Agents

```bash
# Build and deploy orchestrator agent
cd agents/game-orchestrator
npm run build
npm run deploy

# Build and deploy reflection agent
cd ../reflection-agent
npm run build
npm run deploy

# Verify agent deployment
agentuity status
```

## Phase 5: System Validation

### 5.1 Run Smoke Test

```bash
# Run comprehensive smoke test
curl -X POST http://localhost:8000/api/smoke-test/run \
  -H "Content-Type: application/json" \
  -d '{
    "test_games_count": 5,
    "test_experts": ["conservative_analyzer", "momentum_rider", "contrarian_rebel", "value_hunter"],
    "async_execution": false
  }'

# Check test results
curl http://localhost:8000/api/smoke-test/history?limit=1
```

### 5.2 Validate System Components

```bash
# Check schema validation
curl http://localhost:8000/api/smoke-test/validate/schema

# Check performance targets
curl http://localhost:8000/api/smoke-test/validate/performance

# Check coherence constraints
curl http://localhost:8000/api/smoke-test/validate/coherence

# Check bankroll integrity
curl -X POST http://localhost:8000/api/smoke-test/validate/bankroll
```

## Phase 6: First Prediction Run

### 6.1 Generate Predictions for Upcoming Games

```bash
# Get upcoming games
curl http://localhost:8000/api/games/upcoming

# Generate predictions for a specific game
curl -X POST http://localhost:8000/api/expert/predictions \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "your-game-id",
    "expert_ids": ["conservative_analyzer", "momentum_rider", "contrarian_rebel", "value_hunter"]
  }'

# Check prediction results
curl http://localhost:8000/api/expert/predictions/your-game-id
```

### 6.2 Council Selection and Platform Slate

```bash
# Select council for game
curl -X POST http://localhost:8000/api/council/select/your-game-id

# Get coherent platform slate
curl http://localhost:8000/api/platform/slate/your-game-id

# Check leaderboard
curl http://localhost:8000/api/leaderboard
```

## Phase 7: Monitoring and Operations

### 7.1 Setup Monitoring

```bash
# Check performance monitoring
curl http://localhost:8000/api/monitoring/metrics

# View expert performance dashboard
curl http://localhost:8000/api/expert-scaling/dashboard

# Check baseline testing status
curl http://localhost:8000/api/baseline-testing/health
```

### 7.2 Regular Operations

```bash
# Daily: Run system health check
curl http://localhost:8000/api/smoke-test/health

# Weekly: Run comprehensive smoke test
curl -X POST http://localhost:8000/api/smoke-test/run

# After games: Run settlement
curl -X POST http://localhost:8000/api/settle/your-game-id

# Monitor expert performance
curl http://localhost:8000/api/baseline-testing/switching/recommendations
```

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check Supabase connection
python -c "
from src.services.supabase_service import SupabaseService
try:
    supabase = SupabaseService()
    result = supabase.table('games').select('count', count='exact').limit(1).execute()
    print('✅ Database connected')
except Exception as e:
    print(f'❌ Database error: {e}')
"
```

#### API Key Issues
```bash
# Test LLM API keys
python -c "
import os
print('OpenAI Key:', '✅' if os.getenv('OPENAI_API_KEY') else '❌')
print('Anthropic Key:', '✅' if os.getenv('ANTHROPIC_API_KEY') else '❌')
print('DeepSeek Key:', '✅' if os.getenv('DEEPSEEK_API_KEY') else '❌')
"
```

#### Performance Issues
```bash
# Check vector index status
python scripts/check_vector_indexes.py

# Verify HNSW indexes
python -c "
from src.services.memory_retrieval_service import MemoryRetrievalService
from src.services.supabase_service import SupabaseService
service = MemoryRetrievalService(SupabaseService())
# Test vector retrieval performance
"
```

#### Schema Validation Issues
```bash
# Test schema validator
python -c "
from src.services.schema_validator import validate_expert_prediction
test_prediction = {
    'game_id': 'test',
    'expert_id': 'test',
    'predictions': [],
    'overall_confidence': 0.5
}
result = validate_expert_prediction(test_prediction)
print('Schema validator:', '✅' if result else '❌')
"
```

### Service Restart Commands

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api

# Restart with fresh build
docker-compose down
docker-compose up --build -d

# Manual service restart
pkill -f "uvicorn"
uvicorn src.api.main:app --reload --port 8000 &
```

## Production Deployment

### Additional Production Steps

1. **SSL/TLS Setup**: Configure HTTPS with proper certificates
2. **Load Balancing**: Setup nginx or similar for load balancing
3. **Process Management**: Use PM2 for Node.js process management
4. **Monitoring**: Setup comprehensive monitoring with alerts
5. **Backup Strategy**: Implement database backup and recovery
6. **Security**: Configure firewalls, rate limiting, and security headers

### Production Environment Variables

```bash
# Production-specific settings
NODE_ENV=production
DEBUG=false
LOG_LEVEL=info

# Performance settings
DB_POOL_SIZE=20
REDIS_MAX_CONNECTIONS=100
VECTOR_RETRIEVAL_TIMEOUT=5000

# Security settings
CORS_ORIGINS=https://yourdomain.com
API_RATE_LIMIT=100
AUTH_REQUIRED=true
```

## Next Steps

Once your system is running:

1. **Monitor Performance**: Watch the dashboards for performance metrics
2. **Review Predictions**: Analyze expert predictions and council selections
3. **Track ROI**: Monitor bankroll changes and betting performance
4. **Optimize**: Use baseline testing to optimize expert performance
5. **Scale**: Add more experts or increase prediction frequency as needed

## Support

For issues or questions:
- Check the troubleshooting section above
- Review service logs: `docker-compose logs -f`
- Run smoke tests to identify issues
- Check the comprehensive documentation in `/docs`

The Expert Council Betting System is now ready for operation! 🚀
