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
├── config/                 # Configuration files
├── supabase/               # Supabase migrations and config
├── .qoder/                 # Qoder documentation and specs
└── .kiro/                  # Kiro steering and configuration
```

## Source Code Structure (`src/`)

### Frontend Components
- `src/components/` - Reusable React components with TypeScript
- `src/pages/` - Page-level components and routing
- `src/hooks/` - Custom React hooks for data fetching and state
- `src/lib/` - Utility libraries and helper functions
- `src/styles/` - CSS and Tailwind styling files
- `src/types/` - TypeScript type definitions and interfaces

### Backend API Services
- `src/api/` - FastAPI routes, endpoints, and middleware
- `src/services/` - Business logic services and data access layers
- `src/database/` - Database models, connections, and migrations
- `src/websocket/` - WebSocket server for real-time updates
- `src/cache/` - Redis caching layer and cache management
- `src/storage/` - Supabase storage service integration

### AI/ML System
- `src/ml/` - Core machine learning and AI components
- `src/ml/expert_competition/` - AI expert system and competition framework
- `src/ml/prediction_engine/` - Comprehensive prediction categories (83 types)
- `src/ml/self_healing/` - Adaptive learning and performance monitoring
- `src/ml/models/` - ML model implementations (XGBoost, RandomForest, Neural Networks)
- `src/prompts/` - LLM prompts and templates for expert personalities

### Analytics & Betting Tools
- `src/analytics/` - Betting engine, value detection, and ROI analysis
- `src/formatters/` - Report generation and output formatting
- `src/notifications/` - Multi-channel notification system

### Data Processing
- `src/data/` - Data fetching, processing, and validation
- `src/integrations/` - External API integrations (ESPN, SportsData.io)

## Key Directories

### Scripts (`scripts/`)
Comprehensive automation and utility scripts:

**Data Management**
- `fetch_2025_nfl_season.mjs` - NFL season data synchronization
- `populate_database.py` - Historical data population
- `check_games_count.mjs` - Data validation and coverage checks

**AI & Expert System**
- `test_all_15_experts.py` - Expert system validation
- `generate_weekly_predictions.py` - Prediction generation
- `run_memory_tests.sh` - Episodic memory system testing
- `supabase_memory_journey.py` - Memory system demonstration

**Database Operations**
- `add_performance_indexes.py` - Database optimization
- `fix_rls_and_migrate.js` - Schema fixes and migrations
- `check_database_schema.mjs` - Schema validation

**System Validation**
- `validate_system.py` - System health checks
- `show_all_predictions.py` - Prediction display and verification

### Documentation (`docs/`)
Comprehensive system documentation:
- `betting_categories_logic.md` - Complete guide to 83 betting categories
- `expert_personalities_betting_guide.md` - AI expert personality profiles
- Implementation guides and API documentation
- System architecture and design decisions
- Testing procedures and deployment guides

### Configuration Files

**Core Configuration**
- `package.json` - Node.js dependencies and npm scripts
- `requirements.txt` - Core Python dependencies
- `requirements-ml.txt` - Machine learning specific dependencies
- `requirements-production.txt` - Production environment packages

**Infrastructure**
- `docker-compose.yml` - Development container orchestration
- `docker-compose.prod.yml` - Production container configuration
- `Dockerfile` - Multi-stage container build
- `nginx.conf` - Reverse proxy and SSL configuration

**Process Management**
- `ecosystem.config.js` - PM2 process management for Node.js services
- `deploy.sh` - Automated production deployment script

**Build & Development**
- `vite.config.js` - Frontend build configuration with hot reload
- `tailwind.config.js` - Styling and theme configuration
- `playwright.config.js` - End-to-end testing configuration

## Supabase Integration (`supabase/`)

### Database Schema
- `supabase/migrations/` - Versioned database migrations
- `supabase/config.toml` - Supabase project configuration
- Schema files for expert competition, AI council voting, and self-healing systems

### Key Migration Files
- `020_enhanced_expert_competition_schema.sql` - Expert system tables
- `021_ai_council_voting_schema.sql` - Voting and consensus mechanisms
- `023_self_healing_system_schema.sql` - Adaptive learning infrastructure
- `030_production_database_optimization.sql` - Performance optimizations

## Qoder Documentation (`.qoder/`)

### Repository Wiki
- `.qoder/repowiki/` - Comprehensive system documentation
- Organized by categories: API Reference, Expert System, Analytics, etc.
- Markdown files with cross-references and technical details

### Quests & Specifications
- `.qoder/quests/` - Implementation roadmaps and feature specifications
- `.qoder/specs/` - Detailed technical specifications for major features

## Kiro Configuration (`.kiro/`)

### Steering Documents
- `.kiro/steering/product.md` - Product overview and features
- `.kiro/steering/tech.md` - Technology stack and commands
- `.kiro/steering/structure.md` - Project structure guide

### Specifications
- `.kiro/specs/` - Feature specifications and requirements
- Expert council betting system specifications and task definitions

## File Naming Conventions

### Frontend (TypeScript/React)
- Components: PascalCase (`NFLDashboard.tsx`, `ExpertLeaderboard.tsx`)
- Hooks: camelCase with `use` prefix (`useGameData.ts`, `useExpertPredictions.ts`)
- Utilities: camelCase (`formatGameTime.ts`, `calculateROI.ts`)
- Types: PascalCase (`GameData.ts`, `ExpertPrediction.ts`)
- Pages: PascalCase (`Dashboard.tsx`, `Analytics.tsx`)

### Backend (Python)
- Services: snake_case (`expert_system_api.py`, `betting_engine.py`)
- Models: snake_case (`game_prediction.py`, `expert_performance.py`)
- Scripts: snake_case (`fetch_nfl_data.py`, `generate_predictions.py`)
- Tests: `test_` prefix (`test_expert_system.py`, `test_betting_engine.py`)
- Configuration: snake_case (`production_config.py`, `database_settings.py`)

### Database & Migrations
- Migration files: numbered with descriptive names (`020_enhanced_expert_competition_schema.sql`)
- Table names: snake_case (`expert_predictions`, `ai_council_selections`)
- Column names: snake_case (`prediction_confidence`, `expert_accuracy`)

## Import Path Conventions

### Frontend (TypeScript)
```typescript
// Use @ alias for src imports
import { GameCard } from '@/components/GameCard'
import { useGameData } from '@/hooks/useGameData'
import { ExpertPrediction } from '@/types/ExpertPrediction'
import { formatCurrency } from '@/lib/utils'
```

### Backend (Python)
```python
# Relative imports within src/
from src.ml.expert_competition import ExpertCompetitionFramework
from src.services.supabase_service import SupabaseService
from src.analytics.betting_engine import BettingEngine
from src.ml.personality_driven_experts import PersonalityDrivenExpert
```

## Environment Configuration

### Environment Files
- `.env` - Development environment configuration
- `.env.example` - Template with all required variables
- `.env.production` - Production-specific settings
- `.env.production.template` - Production deployment template

### Key Environment Variables
```bash
# Database
SUPABASE_URL=https://project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# External APIs
ODDS_API_KEY=your-odds-api-key
SPORTSDATA_IO_KEY=your-sportsdata-key
ESPN_API_KEY=your-espn-api-key

# Cache & Performance
REDIS_URL=redis://redis:6379
DB_MIN_POOL_SIZE=10
DB_MAX_POOL_SIZE=50
```

## Data Organization

### Data Storage
- `data/historical/` - Historical NFL game data and statistics
- `data/raw/` - Raw data files from external APIs
- `data/processed/` - Cleaned and processed datasets
- `data/exports/` - Generated reports and analysis exports

### Model Storage
- `models/experts/` - AI expert model files and configurations
- `models/ml/` - Traditional ML model artifacts (XGBoost, etc.)
- `models/metadata/` - Model performance metrics and metadata

### Static Assets
- `public/logos/` - NFL team logos and branding assets
- `public/images/` - UI images and graphics
- `public/icons/` - Application icons and favicons

## Testing Structure

### Test Organization
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for system components
- `tests/e2e/` - End-to-end tests with Playwright
- `src/__tests__/` - Component-level tests co-located with source

### Test Files
- Frontend: `*.test.tsx` for React components
- Backend: `test_*.py` for Python modules
- Integration: `*_integration.test.py` for cross-system tests
- E2E: `*.spec.ts` for Playwright tests

## Archive Policy

### Deprecated Code (`archive/`)
The archive directory contains legacy implementations that should not be modified:
- `archive/dashboard/` - Old dashboard implementations
- `archive/api/` - Legacy backend services
- `archive/migrations/` - Outdated migration scripts
- `archive/models/` - Previous ML model implementations

### Archive Guidelines
- Never modify files in `archive/`
- Check archive before implementing new features
- Use archived code as reference only
- Document reasons for archiving in commit messages

## Development Workflow

### Branch Structure
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - Individual feature branches
- `hotfix/*` - Critical production fixes

### Code Organization Principles
- **Separation of Concerns**: Clear boundaries between frontend, backend, AI, and analytics
- **Modular Design**: Independent components that can be developed and tested separately
- **Configuration Management**: Environment-specific settings externalized
- **Documentation**: Comprehensive docs co-located with code
- **Testing**: Test files organized alongside source code where appropriate
