# Technology Stack

## Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite 4.5+ with hot reload
- **Styling**: Tailwind CSS with custom NFL theme
- **UI Components**: Radix UI primitives with shadcn/ui
- **State Management**: TanStack Query for server state
- **Charts**: Recharts for data visualization
- **Animations**: Framer Motion

## Backend
- **API**: FastAPI (Python) + Node.js services
- **Database**: Supabase (PostgreSQL) with Row Level Security
- **Caching**: Redis for performance optimization
- **Real-time**: WebSocket server for live updates
- **Authentication**: Supabase Auth

## AI/ML Stack
- **Models**: Multiple LLM integration (Claude, GPT-4, Gemini)
- **ML Libraries**: scikit-learn, XGBoost, TensorFlow
- **Data Processing**: pandas, numpy
- **Expert System**: Custom competition framework with episodic memory

## Infrastructure
- **Containerization**: Docker with multi-stage builds
- **Process Management**: PM2 ecosystem
- **Deployment**: Vercel (frontend), cloud hosting (backend)
- **Monitoring**: Health checks and logging

## Development Tools
- **Testing**: Vitest, Playwright for E2E
- **Linting**: ESLint, Prettier, Ruff (Python)
- **Type Checking**: TypeScript, mypy (Python)

## Common Commands

### Development
```bash
# Frontend development
npm run dev              # Start dev server (port 5173)
npm run dev-full         # Start frontend + WebSocket

# Backend development
python quick_api.py      # Start FastAPI server (port 8080)
uvicorn src.api.main:app --reload  # Full API with reload

# Database
bash scripts/run_memory_tests.sh   # Test episodic memory system
python scripts/supabase_memory_journey.py  # Memory demo
```

### Build & Deploy
```bash
npm run build           # Build for production
npm run preview         # Preview production build
docker-compose up       # Full stack with Docker
pm2 start ecosystem.config.js  # Production deployment
```

### Testing
```bash
npm test               # Frontend tests
pytest tests/          # Backend tests
playwright test        # E2E tests
python scripts/validate_system.py  # System validation
```

### Data & AI
```bash
python scripts/fetch_2025_nfl_season.mjs  # Sync NFL data
python scripts/test_all_15_experts.py     # Test AI experts
python scripts/generate_weekly_predictions.py  # Generate predictions
```

## Environment Setup
- Node.js 18+ required
- Python 3.11+ with virtual environment
- Redis server (optional but recommended)
- Supabase project with configured database
