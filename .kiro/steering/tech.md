# Technology Stack

## Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 4.5+ with hot reload and fast development server
- **Styling**: Tailwind CSS with custom NFL theme and responsive design
- **UI Components**: Radix UI primitives with shadcn/ui for accessibility
- **State Management**: TanStack Query for server state and caching
- **Charts**: Recharts for data visualization and analytics dashboards
- **Animations**: Framer Motion for smooth UI transitions
- **Real-time**: WebSocket integration for live updates

## Backend Framework
- **API Framework**: FastAPI (Python) with automatic OpenAPI documentation
- **WebSocket Server**: Node.js on port 8080 for real-time updates
- **Async Processing**: FastAPI's async capabilities for concurrent requests
- **Data Validation**: Pydantic models for robust input/output validation
- **Middleware**: CORS handling, response compression, rate limiting
- **Health Checks**: Built-in monitoring endpoints and service validation

## Database & Storage
- **Primary Database**: Supabase (PostgreSQL) with Row Level Security (RLS)
- **Vector Search**: pgvector extension for episodic memory similarity search
- **Real-time Subscriptions**: Supabase realtime for live data synchronization
- **Connection Pooling**: 10-50 connections with query timeout (60s)
- **Migrations**: Automated schema management and version control
- **Backup Strategy**: Daily snapshots with 30-day retention policy

## Caching & Performance
- **Primary Cache**: Redis with password protection and 256MB memory limit
- **Cache Strategy**: Multi-level (Redis + in-memory) with LRU eviction
- **TTL Management**: Intelligent expiration based on data volatility
- **Cache Warming**: Pre-population of frequently accessed data
- **Performance Monitoring**: Cache hit rates and response time tracking

## AI/ML Stack
- **LLM Integration**: Multiple providers (Claude, GPT-4, Gemini)
- **ML Libraries**: scikit-learn, XGBoost, TensorFlow, PyTorch
- **Ensemble Models**: XGBoost for game winners, RandomForest for totals, Neural Networks for props
- **Data Processing**: pandas, numpy for feature engineering and analysis
- **Expert System**: 15 personality-driven experts with competition framework
- **Memory System**: Vector-based episodic memory with similarity search
- **Self-Healing**: Automatic adaptation and performance monitoring

## Analytics & Betting Tools
- **Betting Engine**: Kelly Criterion-based value betting and arbitrage detection
- **Line Movement**: Sharp money detection and reverse line movement analysis
- **ROI Tracking**: Historical performance with bankroll management
- **Notification System**: Multi-channel alerts (email, SMS, webhooks, Slack, Discord)
- **Report Generation**: Comprehensive 3000+ line analysis reports

## Infrastructure & Deployment
- **Containerization**: Docker with multi-stage builds and security best practices
- **Orchestration**: Docker Compose for service management
- **Process Management**: PM2 ecosystem for Node.js services
- **Reverse Proxy**: Nginx with SSL termination and rate limiting
- **Deployment**: Automated deployment scripts with zero-downtime updates
- **Monitoring**: Health checks, performance metrics, and alerting

## Security & Authentication
- **Authentication**: Supabase Auth with JWT tokens
- **Authorization**: Row Level Security (RLS) policies
- **API Security**: Rate limiting (10 req/s general, 5 req/s auth)
- **SSL/TLS**: Certificate management and HTTPS enforcement
- **Environment Protection**: Secure environment variable handling
- **API Key Rotation**: Scheduled rotation for external service keys

## Development Tools
- **Testing**: Vitest (frontend), pytest (backend), Playwright (E2E)
- **Linting**: ESLint, Prettier (frontend), Ruff (Python backend)
- **Type Checking**: TypeScript, mypy (Python)
- **Code Quality**: Pre-commit hooks and automated validation
- **Documentation**: Automatic API docs generation with FastAPI

## External Integrations
- **Sports Data**: ESPN API, SportsData.io for game data and statistics
- **Odds Providers**: Multiple sportsbook APIs for line movement tracking
- **Weather Data**: Weather API integration for game condition analysis
- **News Sentiment**: News API for sentiment analysis and narrative tracking

## Common Commands

### Development
```bash
# Frontend development
npm run dev              # Start dev server (port 5173)
npm run dev-full         # Start frontend + WebSocket server

# Backend development
python quick_api.py      # Start FastAPI server (port 8080)
uvicorn src.api.main:app --reload  # Full API with hot reload

# Database operations
bash scripts/run_memory_tests.sh   # Test episodic memory system
python scripts/supabase_memory_journey.py  # Memory system demo
supabase db push         # Apply database migrations
```

### Build & Deploy
```bash
npm run build           # Build frontend for production
npm run preview         # Preview production build
docker-compose up --build  # Full stack with Docker
pm2 start ecosystem.config.js  # Production process management
./deploy.sh             # Automated production deployment
```

### Testing & Validation
```bash
npm test               # Frontend unit tests
pytest tests/          # Backend unit tests
playwright test        # End-to-end tests
python scripts/validate_system.py  # System validation
python verify_comprehensive_system.py  # Full system check
```

### Data & AI Operations
```bash
node scripts/fetch_2025_nfl_season.mjs  # Sync NFL season data
python scripts/test_all_15_experts.py   # Test all AI experts
python scripts/generate_weekly_predictions.py  # Generate predictions
python scripts/populate_database.py     # Populate historical data
python scripts/show_all_predictions.py  # Display current predictions
```

### Analytics & Monitoring
```bash
curl http://localhost:8000/health       # Check API health
curl http://localhost:8000/api/experts/leaderboard  # Expert rankings
wscat -c ws://localhost:8080/ws/live-updates  # Test WebSocket
docker-compose logs -f  # View service logs
```

## Environment Setup Requirements
- **Node.js**: 18.x or 20.x for frontend and WebSocket services
- **Python**: 3.9+ with virtual environment for backend services
- **Docker**: Latest version with Docker Compose for containerization
- **Redis**: 6.x+ for caching (optional but recommended for performance)
- **Supabase**: Project with PostgreSQL and pgvector extension
- **External APIs**: Keys for ESPN, SportsData.io, odds providers

## Performance Targets
- **API Response Time**: Sub-second for 95% of requests
- **WebSocket Latency**: <100ms for real-time updates
- **Database Queries**: p95 <100ms with proper indexing
- **Cache Hit Rate**: >80% for frequently accessed data
- **Uptime**: 99.9% availability with health monitoring
- **Concurrent Users**: Support for 1000+ simultaneous connections
