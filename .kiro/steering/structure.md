# Project Structure

## Root Directory Organization

```
nfl-predictor-api/
├── src/                    # Main source code
├── scripts/                # Utility and automation scripts
├── docs/                   # Documentation and guides
├── tests/                  # Test suites
├── data/                   # Data files and exports
├── models/                 # ML models and metadata
├── public/                 # Static assets (logos, images)
├── archive/                # Legacy/deprecated code
└── config/                 # Configuration files
```

## Source Code Structure (`src/`)

### Frontend Components
- `src/components/` - Reusable React components
- `src/pages/` - Page-level components
- `src/hooks/` - Custom React hooks
- `src/lib/` - Utility libraries and helpers
- `src/styles/` - CSS and styling files
- `src/types/` - TypeScript type definitions

### Backend Services
- `src/api/` - FastAPI routes and endpoints
- `src/services/` - Business logic services
- `src/database/` - Database models and queries
- `src/ml/` - Machine learning and AI components
- `src/websocket/` - WebSocket server implementation
- `src/cache/` - Caching layer implementation

### AI/ML Components
- `src/ml/expert_competition/` - AI expert system framework
- `src/ml/models/` - ML model implementations
- `src/prompts/` - LLM prompts and templates
- `src/analytics/` - Data analysis and metrics

## Key Directories

### Scripts (`scripts/`)
Automation and utility scripts organized by function:
- Data fetching and synchronization
- Testing and validation
- Database migrations and setup
- AI model training and evaluation
- Deployment and monitoring

### Documentation (`docs/`)
- Implementation guides and API documentation
- System architecture and design decisions
- Testing procedures and memory system guides
- Deployment and production setup instructions

### Configuration Files
- `package.json` - Node.js dependencies and scripts
- `requirements.txt` - Python dependencies
- `docker-compose.yml` - Container orchestration
- `ecosystem.config.js` - PM2 process management
- `vite.config.js` - Frontend build configuration
- `tailwind.config.js` - Styling configuration

## File Naming Conventions

### Frontend
- Components: PascalCase (`NFLDashboard.jsx`)
- Hooks: camelCase with `use` prefix (`useGameData.js`)
- Utilities: camelCase (`formatGameTime.js`)
- Types: PascalCase (`GameData.ts`)

### Backend
- Services: snake_case (`expert_system_api.py`)
- Models: snake_case (`game_prediction.py`)
- Scripts: snake_case (`fetch_nfl_data.py`)
- Tests: `test_` prefix (`test_expert_system.py`)

## Import Path Conventions

### Frontend
```typescript
// Use @ alias for src imports
import { GameCard } from '@/components/GameCard'
import { useGameData } from '@/hooks/useGameData'
```

### Backend
```python
# Relative imports within src/
from src.ml.expert_competition import ExpertCompetitionFramework
from src.services.supabase_service import SupabaseService
```

## Environment Files
- `.env` - Main environment configuration
- `.env.example` - Template for required variables
- `.env.production` - Production-specific settings
- `.env.production.template` - Production template

## Data Organization
- `data/historical/` - Historical NFL data
- `data/raw/` - Raw data files
- `models/experts/` - AI expert model files
- `memory/` - Episodic memory databases
- `public/logos/` - Team logos and assets

## Testing Structure
- `tests/` - Main test directory
- `src/__tests__/` - Component-level tests
- `scripts/test_*.py` - Integration tests
- `playwright.config.js` - E2E test configuration

## Archive Policy
The `archive/` directory contains deprecated code that should not be modified:
- Old dashboard implementations
- Legacy backend services
- Outdated migration scripts
- Reference implementations

When working on the codebase, always check if similar functionality exists in `archive/` before creating new implementations.
