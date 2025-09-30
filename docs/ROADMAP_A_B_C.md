# AI Council Confidence Pool - A→B→C Roadmap

**Strategy**: Quick Win → Expert AI → Polish
**Timeline**: 6.5 weeks to production-ready system
**Last Updated**: 2025-09-29

---

## 🎯 Strategy Overview

### **Phase A: Quick Win (2 days)**
Get the entire system running end-to-end with real data flow.

**Goal**: Validate all infrastructure, identify integration issues, generate training data for Phase B.

### **Phase B: Expert AI (3 weeks)**
Build reinforcement learning agents that learn from outcomes and improve over time.

**Goal**: Transform static experts into learning AI agents with personality-consistent behavior.

### **Phase C: Polish (2 weeks)**
Add calibration, monitoring, performance optimization, and security hardening.

**Goal**: Production-ready system with high reliability and user trust.

### **Phase D: Deployment (1 week)**
Production infrastructure setup and launch.

**Goal**: Live system serving real users.

---

## 📋 Phase A: Quick Win (2 Days = 16 Hours)

### **Objective**: Validate Infrastructure & Enable Training Data Generation

**Why Phase A First?**
- Identifies integration bugs before Phase B complexity
- Generates real prediction data for RL training
- Validates API performance under load
- Confirms database schema correctness

### **A.1: Database Migrations (3 hours)**

#### **Step 1: Test in Local Environment (1 hour)**
```bash
# Setup local PostgreSQL + Redis
docker-compose up -d postgres redis

# Test migrations locally first (safety!)
psql postgresql://localhost:5432/nfl_test -f migrations/001_create_betting_tables.sql

# Verify all tables created
psql postgresql://localhost:5432/nfl_test -c "
  SELECT table_name,
         pg_size_pretty(pg_total_relation_size(quote_ident(table_name))) AS size
  FROM information_schema.tables
  WHERE table_schema = 'public'
  ORDER BY table_name;
"

# Expected output: 6 new tables (expert_virtual_bets, weather_conditions,
# vegas_lines, injury_reports, social_sentiment, advanced_stats)
```

**Validation Checklist**:
- [ ] All 6 new tables created
- [ ] Triggers working (update_elimination_risk_level)
- [ ] Helper functions exist (calculate_payout)
- [ ] Indexes created for performance
- [ ] No SQL errors in logs

#### **Step 2: Apply to Supabase Production (1 hour)**
```bash
# Backup existing database first!
pg_dump $SUPABASE_DATABASE_URL > backup_before_migration.sql

# Apply migrations to Supabase
psql $SUPABASE_DATABASE_URL -f migrations/001_create_betting_tables.sql

# Verify in Supabase dashboard
# Navigate to: Table Editor → Verify 6 new tables visible
```

#### **Step 3: Seed Initial Data (1 hour)**
```sql
-- Insert 15 expert models if not exist
-- Insert initial bankrolls ($10,000 starting balance)
-- Insert sample predictions for current week
-- Verify data integrity
```

---

### **A.2: API Key Configuration (1 hour)**

#### **Step 1: Create .env File**
```bash
cp .env.example .env
```

#### **Step 2: Configure All Keys**
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_or_service_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Redis (local or cloud)
REDIS_URL=redis://localhost:6379
# OR Redis Cloud:
# REDIS_URL=redis://default:password@host:port

# OpenWeatherMap API
OPENWEATHER_API_KEY=get_from_openweathermap.org
# Free tier: 1000 calls/day

# The Odds API
ODDS_API_KEY=get_from_theoddsapi.com
# Free tier: 500 requests/day

# Optional: For future phases
# TWITTER_API_KEY=...
# ESPN_API_KEY=...
```

#### **Step 3: Test API Keys (30 min)**
```bash
# Test weather API
python -c "
import os
from src.services.weather_ingestion_service import WeatherIngestionService
ws = WeatherIngestionService()
result = await ws.fetch_weather('BUF')  # Test for Buffalo
print('Weather API:', 'OK' if result else 'FAILED')
"

# Test odds API
python -c "
import os
from src.services.vegas_odds_service import VegasOddsService
vs = VegasOddsService()
result = await vs.fetch_odds('americanfootball_nfl')
print('Odds API:', 'OK' if result else 'FAILED')
"
```

---

### **A.3: Build ExpertDataAccessLayer (3 hours)**

**WHY CRITICAL**: Data ingestion services exist, but experts can't consume the data yet!

#### **New File**: `/src/services/expert_data_access_layer.py`

```python
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

class ExpertDataAccessLayer:
    """
    Bridges data ingestion services and expert prediction models.
    Provides personality-based data filtering.
    """

    def __init__(self):
        self.weather_service = WeatherIngestionService()
        self.odds_service = VegasOddsService()
        self.data_coordinator = DataCoordinator()

    async def get_expert_data_view(
        self,
        expert_id: str,
        game_id: str
    ) -> Dict:
        """
        Get data tailored to expert's personality and access level.

        Examples:
        - "The Analyst" gets FULL data (all stats, weather, odds)
        - "Gut Instinct" gets LIMITED data (basic stats only)
        - "Contrarian Rebel" gets PUBLIC SENTIMENT (to fade)
        """
        # Get expert profile
        expert = await self._get_expert_profile(expert_id)

        # Gather all available data
        all_data = await self.data_coordinator.gather_game_data(game_id)

        # Filter based on personality
        filtered_data = self._filter_by_personality(
            expert.personality,
            all_data
        )

        return filtered_data

    def _filter_by_personality(
        self,
        personality: str,
        data: Dict
    ) -> Dict:
        """Apply personality-specific data filters"""

        filters = {
            'data_driven': {
                'weather': True,
                'odds': True,
                'stats': True,
                'sentiment': True,
                'news': True
            },
            'intuition': {
                'weather': False,
                'odds': True,  # Basic odds only
                'stats': False,
                'sentiment': False,
                'news': True  # Breaking news only
            },
            'contrarian': {
                'weather': True,
                'odds': True,
                'stats': True,
                'sentiment': True,  # PRIORITY: Need public % to fade
                'news': True
            },
            # ... define for all 15 personalities
        }

        filter_config = filters.get(personality, filters['data_driven'])

        filtered = {}
        if filter_config['weather']:
            filtered['weather'] = data.get('weather')
        if filter_config['odds']:
            filtered['odds'] = data.get('odds')
        # ... apply all filters

        return filtered

    async def batch_get_expert_data(
        self,
        expert_ids: List[str],
        game_ids: List[str]
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Efficiently fetch data for multiple experts and games.
        Returns: {expert_id: {game_id: data}}
        """
        tasks = []
        for expert_id in expert_ids:
            for game_id in game_ids:
                tasks.append(
                    self.get_expert_data_view(expert_id, game_id)
                )

        results = await asyncio.gather(*tasks)

        # Organize results by expert and game
        organized = {}
        idx = 0
        for expert_id in expert_ids:
            organized[expert_id] = {}
            for game_id in game_ids:
                organized[expert_id][game_id] = results[idx]
                idx += 1

        return organized
```

**Deliverable**:
- File created: `/src/services/expert_data_access_layer.py` (300 lines)
- Unit tests: `/tests/services/test_expert_data_access.py` (20 tests)
- Documentation: Updated `/docs/DATA_INGESTION_SETUP.md`

---

### **A.4: Basic Monitoring Setup (2 hours)**

#### **Why Now?**: Need observability for debugging Phases B & C

#### **Tool**: Simple Python logging + optional Grafana

**Create**: `/src/monitoring/basic_monitor.py`

```python
import logging
import time
from functools import wraps
from typing import Dict
import json

class BasicMonitor:
    """Lightweight monitoring for development"""

    def __init__(self):
        self.metrics = {
            'api_calls': {},
            'db_queries': {},
            'errors': []
        }

    def track_api_call(self, endpoint: str):
        """Decorator for API endpoint timing"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start

                    # Track metrics
                    if endpoint not in self.metrics['api_calls']:
                        self.metrics['api_calls'][endpoint] = {
                            'count': 0,
                            'total_time': 0,
                            'errors': 0
                        }

                    self.metrics['api_calls'][endpoint]['count'] += 1
                    self.metrics['api_calls'][endpoint]['total_time'] += duration

                    # Log slow queries
                    if duration > 0.5:
                        logging.warning(
                            f"SLOW API: {endpoint} took {duration:.2f}s"
                        )

                    return result

                except Exception as e:
                    self.metrics['api_calls'][endpoint]['errors'] += 1
                    self.metrics['errors'].append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'timestamp': time.time()
                    })
                    raise

            return wrapper
        return decorator

    def get_summary(self) -> Dict:
        """Get performance summary"""
        summary = {}
        for endpoint, data in self.metrics['api_calls'].items():
            avg_time = data['total_time'] / data['count'] if data['count'] > 0 else 0
            summary[endpoint] = {
                'calls': data['count'],
                'avg_response_time': round(avg_time, 3),
                'error_rate': data['errors'] / data['count'] if data['count'] > 0 else 0
            }
        return summary

# Global monitor instance
monitor = BasicMonitor()
```

**Integration**:
```python
# In src/api/routers/experts.py
from src.monitoring.basic_monitor import monitor

@app.get("/api/v1/experts")
@monitor.track_api_call("GET /api/v1/experts")
async def get_experts():
    ...
```

**Dashboard Endpoint**:
```python
# Add to src/api/main.py
@app.get("/api/v1/monitoring/summary")
async def get_monitoring_summary():
    return monitor.get_summary()
```

---

### **A.5: API Smoke Tests (2 hours)**

#### **Test All 11 Endpoints**

Create: `/tests/integration/test_api_smoke.py`

```python
import pytest
from httpx import AsyncClient
from src.api.main import app

@pytest.mark.asyncio
async def test_all_endpoints():
    """Smoke test every API endpoint"""

    async with AsyncClient(app=app, base_url="http://test") as client:

        # 1. GET /api/v1/experts
        response = await client.get("/api/v1/experts")
        assert response.status_code == 200
        data = response.json()
        assert len(data['experts']) == 15

        # 2. GET /api/v1/experts/{id}/bankroll
        response = await client.get("/api/v1/experts/the-analyst/bankroll")
        assert response.status_code == 200
        assert 'current_balance' in response.json()

        # 3. GET /api/v1/experts/{id}/predictions
        response = await client.get(
            "/api/v1/experts/the-analyst/predictions",
            params={'week': 5}
        )
        assert response.status_code == 200

        # 4. GET /api/v1/experts/{id}/memories
        response = await client.get(
            "/api/v1/experts/the-gambler/memories",
            params={'limit': 10}
        )
        assert response.status_code == 200

        # 5. GET /api/v1/council/current
        response = await client.get("/api/v1/council/current")
        assert response.status_code == 200
        council = response.json()
        assert len(council['council_members']) == 5

        # 6. GET /api/v1/council/consensus/{game_id}
        response = await client.get(
            "/api/v1/council/consensus/2025_05_KC_BUF"
        )
        assert response.status_code == 200
        assert 'consensus' in response.json()

        # 7. GET /api/v1/bets/live
        response = await client.get("/api/v1/bets/live")
        assert response.status_code == 200
        assert 'bets' in response.json()

        # 8. GET /api/v1/bets/expert/{id}/history
        response = await client.get(
            "/api/v1/bets/expert/the-analyst/history"
        )
        assert response.status_code == 200

        # 9. GET /api/v1/games/week/{week}
        response = await client.get("/api/v1/games/week/5")
        assert response.status_code == 200
        assert 'games' in response.json()

        # 10. GET /api/v1/games/battles/active
        response = await client.get("/api/v1/games/battles/active")
        assert response.status_code == 200

        # 11. Health check
        response = await client.get("/health")
        assert response.status_code == 200

# Run with: pytest tests/integration/test_api_smoke.py -v
```

---

### **A.6: WebSocket Testing (1 hour)**

Create: `/tests/integration/test_websocket.py`

```python
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

def test_websocket_connection():
    """Test WebSocket connectivity"""
    client = TestClient(app)

    with client.websocket_connect("/ws/updates") as websocket:
        # Subscribe to channels
        websocket.send_json({
            "type": "subscribe",
            "channels": ["bets", "lines", "eliminations"]
        })

        # Should receive acknowledgment
        data = websocket.receive_json()
        assert data['type'] == 'subscribed'

        # Test heartbeat
        websocket.send_json({"type": "ping"})
        data = websocket.receive_json()
        assert data['type'] == 'pong'
```

---

### **A.7: Frontend Hook Integration (3 hours)**

#### **Update ConfidencePoolPage.tsx**

```typescript
// BEFORE: Mock data
const mockExperts = [...]

// AFTER: Real hooks
import {
  useExpertBankrolls,
  useCouncilPredictions,
  useLiveBettingFeed,
  useConfidencePoolWebSocket
} from '@/hooks/confidencePool';

export function ConfidencePoolPage() {
  // Real-time data
  const { data: bankrolls, isLoading } = useExpertBankrolls();
  const { data: predictions } = useCouncilPredictions({ week: 5 });
  const { data: bets } = useLiveBettingFeed();

  // WebSocket connection
  const { isConnected } = useConfidencePoolWebSocket({
    onBetPlaced: (bet) => {
      toast.success(`${bet.expert_name} bet $${bet.bet_amount}!`);
    },
    onExpertEliminated: (expert) => {
      toast.error(`${expert.expert_name} eliminated!`);
    }
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      {/* Real-time WebSocket status */}
      <WebSocketIndicator connected={isConnected} />

      {/* Expert bankroll leaderboard */}
      <BankrollTracker experts={bankrolls} />

      {/* Live betting feed */}
      <LiveBettingFeed bets={bets} />

      {/* Council predictions */}
      <CouncilPredictions predictions={predictions} />
    </div>
  );
}
```

---

### **A.8: End-to-End Flow Test (2 hours)**

#### **Full System Integration Test**

```bash
# Terminal 1: Start Redis
docker run -d -p 6379:6379 redis:alpine

# Terminal 2: Start FastAPI
uvicorn src.api.main:app --reload --port 8000

# Terminal 3: Run data ingestion
python src/services/data_coordinator.py

# Terminal 4: Start frontend
npm run dev

# Terminal 5: Run E2E test
playwright test tests/e2e/confidence-pool.spec.ts
```

**E2E Test Script**: `/tests/e2e/confidence-pool.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test('Confidence Pool E2E Flow', async ({ page }) => {
  await page.goto('http://localhost:5173/confidence-pool');

  // 1. Wait for data to load
  await page.waitForSelector('[data-testid="expert-card"]');

  // 2. Verify 15 experts displayed
  const experts = await page.$$('[data-testid="expert-card"]');
  expect(experts.length).toBe(15);

  // 3. Check WebSocket connection
  await page.waitForSelector('[data-testid="ws-connected"]');

  // 4. Verify live betting feed updates
  const feed = page.locator('[data-testid="betting-feed"]');
  await expect(feed).toBeVisible();

  // 5. Click on expert to view details
  await page.click('[data-testid="expert-card"]:first-child');
  await expect(page.locator('[data-testid="expert-details"]')).toBeVisible();

  // 6. Verify bankroll data loaded
  const bankroll = await page.textContent('[data-testid="expert-bankroll"]');
  expect(bankroll).toContain('$');

  // 7. Test prediction consensus
  await page.click('[data-testid="view-consensus"]');
  await expect(page.locator('[data-testid="consensus-card"]')).toBeVisible();
});
```

---

### **Phase A Success Criteria** ✅

| Criterion | Target | Validation |
|-----------|--------|------------|
| Database migrations applied | 100% | All 6 tables exist |
| API endpoints working | 11/11 | Smoke tests pass |
| WebSocket connectivity | Connected | Real-time updates work |
| Frontend integration | Complete | No mock data used |
| Data ingestion | Running | Weather + odds fetching |
| End-to-end flow | Working | E2E test passes |
| Performance | < 500ms API | Monitor dashboard shows |
| Error rate | < 1% | No critical errors logged |

**Phase A Completion Time**: 2 days (16 hours with single developer)

---

## 🤖 Phase B: Expert AI (3 Weeks = 21 Days)

### **Objective**: Transform Static Experts into Learning AI Agents

**Why Phase B Critical?**
- Current experts are rule-based (no learning)
- Need RL to improve accuracy over time
- Personality-consistent behavior requires ML models
- Enables true "AI Council" with competing strategies

### **B.1: Real NFL Data Acquisition (2 days)**

#### **Data Sources**:
1. **nflfastR** (play-by-play, EPA, CPOE)
2. **ESPN API** (scores, standings, stats)
3. **Pro Football Reference** (historical matchups)

#### **Tasks**:
```python
# Create: /src/data/nfl_data_loader.py

import nfl_data_py as nfl
import pandas as pd

class NFLDataLoader:
    """Load and clean real NFL data for training"""

    def load_seasons(self, years: List[int]) -> pd.DataFrame:
        """Load complete season data"""
        # nflfastR provides:
        # - Game results (scores, winners)
        # - Play-by-play data
        # - EPA (Expected Points Added)
        # - CPOE (Completion % Over Expected)

        seasons = []
        for year in years:
            pbp = nfl.import_pbp_data([year])
            # Clean and aggregate
            games = self._aggregate_to_games(pbp)
            seasons.append(games)

        return pd.concat(seasons)

    def _aggregate_to_games(self, pbp: pd.DataFrame) -> pd.DataFrame:
        """Convert play-by-play to game-level features"""

        games = pbp.groupby('game_id').agg({
            'home_score': 'max',
            'away_score': 'max',
            'total_home_epa': 'sum',
            'total_away_epa': 'sum',
            # ... 50+ features
        })

        # Add outcomes
        games['spread_result'] = games['home_score'] - games['away_score']
        games['total_result'] = games['home_score'] + games['away_score']
        games['winner'] = games.apply(
            lambda x: 'home' if x['home_score'] > x['away_score'] else 'away',
            axis=1
        )

        return games

# Load 2023-2024 seasons
loader = NFLDataLoader()
training_data = loader.load_seasons([2023, 2024])
training_data.to_csv('training_data_2023_2024.csv', index=False)
```

**Deliverable**:
- `/src/data/nfl_data_loader.py` (400 lines)
- `/data/training_data_2023_2024.csv` (570 games)
- Data quality report

---

### **B.2: Feature Engineering Pipeline (4 days)**

#### **Challenge**: Raw data → ML-ready features

**Create**: `/src/ml/features/feature_engineer.py`

```python
from typing import Dict, List
import pandas as pd
import numpy as np

class FeatureEngineer:
    """Transform raw NFL data into ML features"""

    def engineer_game_features(self, game_data: Dict) -> np.ndarray:
        """
        Convert raw game data into feature vector for RL agent.

        Input: {
            'weather': {...},
            'odds': {...},
            'stats': {...},
            'sentiment': {...}
        }

        Output: Feature vector (100-dimensional)
        """

        features = []

        # 1. Weather features (10 dims)
        features.extend(self._weather_features(game_data['weather']))

        # 2. Odds features (20 dims)
        features.extend(self._odds_features(game_data['odds']))

        # 3. Team stats features (40 dims)
        features.extend(self._stats_features(game_data['stats']))

        # 4. Sentiment features (10 dims)
        features.extend(self._sentiment_features(game_data['sentiment']))

        # 5. Matchup features (20 dims)
        features.extend(self._matchup_features(game_data))

        return np.array(features)

    def _weather_features(self, weather: Dict) -> List[float]:
        """Extract weather features"""
        return [
            weather['temperature'] / 100.0,  # Normalize to 0-1
            weather['wind_speed'] / 30.0,
            1.0 if weather['precipitation'] > 0 else 0.0,
            weather['humidity'] / 100.0,
            1.0 if weather['dome_stadium'] else 0.0,
            # ... 5 more features
        ]

    def _odds_features(self, odds: Dict) -> List[float]:
        """Extract betting odds features"""
        return [
            odds['spread'] / 20.0,  # Normalize spread
            self._odds_to_probability(odds['moneyline_home']),
            self._odds_to_probability(odds['moneyline_away']),
            odds['total'] / 60.0,
            odds['line_movement'] / 10.0,
            1.0 if odds['sharp_money_indicator'] else 0.0,
            odds['public_bet_percentage_home'] / 100.0,
            # ... 13 more features
        ]

    def _stats_features(self, stats: Dict) -> List[float]:
        """Extract team statistics features"""
        # EPA, DVOA, success rate, etc.
        pass

    @staticmethod
    def _odds_to_probability(american_odds: int) -> float:
        """Convert American odds to implied probability"""
        if american_odds > 0:
            return 100 / (american_odds + 100)
        else:
            return abs(american_odds) / (abs(american_odds) + 100)
```

**Deliverable**:
- Feature engineering pipeline (500 lines)
- Feature documentation (what each feature means)
- Feature importance analysis
- Unit tests (50 tests)

---

### **B.3: Personality Behavioral Models (1 day)**

**Create**: `/src/ml/personalities/personality_configs.py`

```python
from typing import Dict
from dataclasses import dataclass

@dataclass
class PersonalityConfig:
    """Configuration for expert personality traits"""

    name: str
    archetype: str

    # Feature weighting (which data sources to prioritize)
    weather_weight: float  # 0-1
    odds_weight: float
    stats_weight: float
    sentiment_weight: float

    # Risk parameters
    risk_tolerance: float  # 0-1 (0=conservative, 1=aggressive)
    learning_rate: float  # How fast to adapt (0.001-0.01)
    exploration_rate: float  # Epsilon for epsilon-greedy (0-1)

    # Behavioral traits
    contrarian_tendency: float  # 0-1 (0=follow crowd, 1=fade crowd)
    momentum_bias: float  # -1 to 1 (-1=reversal, 1=momentum)
    recency_bias: float  # 0-1 (0=equal weight all games, 1=recent only)

    # Kelly Criterion multiplier
    kelly_multiplier: float  # 0.5 (fractional Kelly) to 2.0 (aggressive)

# Define all 15 personalities
PERSONALITIES = {
    'the-analyst': PersonalityConfig(
        name='The Analyst',
        archetype='data_driven',
        weather_weight=0.9,
        odds_weight=0.9,
        stats_weight=1.0,  # LOVES stats
        sentiment_weight=0.3,
        risk_tolerance=0.4,  # Conservative
        learning_rate=0.003,
        exploration_rate=0.05,
        contrarian_tendency=0.2,
        momentum_bias=0.0,
        recency_bias=0.3,
        kelly_multiplier=0.5  # Half Kelly (safe)
    ),

    'the-gambler': PersonalityConfig(
        name='The Gambler',
        archetype='risk_taking',
        weather_weight=0.5,
        odds_weight=0.7,
        stats_weight=0.6,
        sentiment_weight=0.8,  # Follows action
        risk_tolerance=0.95,  # EXTREME
        learning_rate=0.01,  # Fast learner
        exploration_rate=0.3,  # High exploration
        contrarian_tendency=0.1,
        momentum_bias=0.8,  # Rides momentum
        recency_bias=0.9,  # Only recent matters
        kelly_multiplier=1.8  # Nearly 2x Kelly (aggressive!)
    ),

    'the-rebel': PersonalityConfig(
        name='The Rebel',
        archetype='contrarian',
        weather_weight=0.6,
        odds_weight=0.8,
        stats_weight=0.7,
        sentiment_weight=1.0,  # NEEDS sentiment to fade
        risk_tolerance=0.75,
        learning_rate=0.005,
        exploration_rate=0.2,
        contrarian_tendency=0.95,  # Fades public!
        momentum_bias=-0.5,  # Reversal bias
        recency_bias=0.4,
        kelly_multiplier=1.2
    ),

    # ... define all 15 personalities
}
```

**Deliverable**:
- 15 complete personality configurations
- Behavioral trait validation
- Documentation of each personality's strategy

---

### **B.4: RL Expert Agent Architecture (5 days)**

**Create**: `/src/ml/agents/base_expert_agent.py`

```python
import torch
import torch.nn as nn
from stable_baselines3 import PPO
from stable_baselines3.common.policies import ActorCriticPolicy

class ExpertAgentPolicy(ActorCriticPolicy):
    """Custom policy network for expert agents"""

    def __init__(self, observation_space, action_space, lr_schedule, **kwargs):
        super().__init__(observation_space, action_space, lr_schedule, **kwargs)

        # Custom architecture for NFL prediction
        self.shared_net = nn.Sequential(
            nn.Linear(100, 256),  # 100 input features
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU()
        )

        # Policy head (outputs action: pick, confidence, bet_size)
        self.policy_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, action_space.shape[0])  # 3 outputs
        )

        # Value head (estimates expected return)
        self.value_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )

class ExpertAgent:
    """RL-based expert with personality-consistent behavior"""

    def __init__(self, personality_config: PersonalityConfig):
        self.config = personality_config
        self.feature_engineer = FeatureEngineer()

        # Initialize PPO agent
        self.model = PPO(
            policy=ExpertAgentPolicy,
            env=NFLPredictionEnv(personality_config),
            learning_rate=personality_config.learning_rate,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            gamma=0.99,  # Discount factor
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,  # Exploration bonus
            verbose=1,
            device='cuda' if torch.cuda.is_available() else 'cpu'
        )

    async def predict(self, game_data: Dict) -> Dict:
        """
        Generate prediction for a game.

        Returns: {
            'pick': 'KC -2.5',
            'confidence': 0.78,
            'bet_size': 850.00,
            'reasoning': 'Statistical edge in road games...'
        }
        """
        # Engineer features
        features = self.feature_engineer.engineer_game_features(game_data)

        # Get action from policy
        action, _ = self.model.predict(features, deterministic=False)

        # Parse action
        pick_idx, confidence, bet_size_fraction = action

        # Apply personality constraints
        confidence = self._apply_confidence_constraints(confidence)
        bet_size = self._calculate_bet_size(confidence, bet_size_fraction)

        # Generate reasoning (rule-based for now, LLM in future)
        reasoning = self._generate_reasoning(game_data, confidence)

        return {
            'pick': self._format_pick(pick_idx, game_data),
            'confidence': float(confidence),
            'bet_size': float(bet_size),
            'reasoning': reasoning
        }

    def learn_from_outcome(self, prediction: Dict, outcome: Dict):
        """
        Update policy based on game outcome.

        This is where RL learning happens!
        """
        # Calculate reward
        reward = self._calculate_reward(prediction, outcome)

        # Store experience in replay buffer
        self.model.replay_buffer.add(
            obs=prediction['features'],
            action=prediction['action'],
            reward=reward,
            next_obs=None,  # Terminal state
            done=True
        )

        # Update policy periodically
        if self.model.replay_buffer.size() >= self.model.batch_size:
            self.model.train()

    def _calculate_reward(self, prediction: Dict, outcome: Dict) -> float:
        """
        Reward function for RL training.

        Components:
        1. Accuracy reward (correct pick)
        2. Calibration reward (confidence matches outcome)
        3. Bankroll reward (profit/loss)
        4. Consistency penalty (strategy drift)
        """
        reward = 0.0

        # 1. Accuracy (40% weight)
        if prediction['pick'] == outcome['result']:
            reward += 0.4
        else:
            reward -= 0.4

        # 2. Calibration (30% weight)
        # If 80% confident, should win ~80% of time
        confidence_error = abs(
            prediction['confidence'] - (1.0 if prediction['pick'] == outcome['result'] else 0.0)
        )
        reward += 0.3 * (1.0 - confidence_error)

        # 3. Bankroll (30% weight)
        profit_pct = outcome['profit'] / outcome['bet_amount'] if outcome['bet_amount'] > 0 else 0
        reward += 0.3 * np.clip(profit_pct, -1, 1)

        return reward

    def save(self, path: str):
        """Save trained model"""
        self.model.save(path)

    def load(self, path: str):
        """Load trained model"""
        self.model = PPO.load(path)
```

**Deliverable**:
- Base expert agent class (600 lines)
- Custom RL environment for NFL (400 lines)
- Reward function design
- Training utilities
- Model checkpointing

---

### **B.5: Training Pipeline (3 days)**

**Create**: `/src/ml/training/train_experts.py`

```python
import asyncio
from typing import List
import pandas as pd

class ExpertTrainingPipeline:
    """Train all 15 experts on historical data"""

    def __init__(self, training_data: pd.DataFrame):
        self.data = training_data
        self.experts = self._initialize_experts()

    def _initialize_experts(self) -> List[ExpertAgent]:
        """Create 15 expert agents with different personalities"""
        experts = []
        for personality_id, config in PERSONALITIES.items():
            expert = ExpertAgent(config)
            experts.append(expert)
        return experts

    async def train_all_experts(self, epochs: int = 100):
        """
        Train all experts simultaneously on historical games.

        Training strategy:
        - Replay 2023-2024 seasons week-by-week
        - Each expert makes predictions for each game
        - Calculate rewards based on outcomes
        - Update policies via PPO
        """

        for epoch in range(epochs):
            print(f"Epoch {epoch + 1}/{epochs}")

            # Shuffle games for variety
            games = self.data.sample(frac=1.0)

            for idx, game in games.iterrows():
                # Get data for this game
                game_data = self._prepare_game_data(game)

                # Each expert makes prediction
                predictions = []
                for expert in self.experts:
                    pred = await expert.predict(game_data)
                    predictions.append(pred)

                # Get actual outcome
                outcome = self._get_outcome(game)

                # Update each expert based on outcome
                for expert, pred in zip(self.experts, predictions):
                    expert.learn_from_outcome(pred, outcome)

            # Evaluate after each epoch
            accuracy = self._evaluate_experts()
            print(f"Epoch {epoch + 1} Accuracy: {accuracy:.1%}")

            # Save checkpoints
            if (epoch + 1) % 10 == 0:
                self._save_checkpoints(epoch + 1)

    def _evaluate_experts(self) -> float:
        """Evaluate all experts on validation set"""
        # Hold out 20% of games for validation
        val_data = self.data.sample(frac=0.2)

        correct = 0
        total = 0

        for idx, game in val_data.iterrows():
            game_data = self._prepare_game_data(game)

            # Get council consensus
            predictions = []
            for expert in self.experts:
                pred = expert.predict(game_data)
                predictions.append(pred)

            consensus = self._calculate_consensus(predictions)
            outcome = self._get_outcome(game)

            if consensus['pick'] == outcome['result']:
                correct += 1
            total += 1

        return correct / total if total > 0 else 0.0

    def _save_checkpoints(self, epoch: int):
        """Save all expert models"""
        for i, expert in enumerate(self.experts):
            path = f"models/expert_{i}_epoch_{epoch}.zip"
            expert.save(path)

# Run training
if __name__ == "__main__":
    # Load training data
    training_data = pd.read_csv('data/training_data_2023_2024.csv')

    # Initialize pipeline
    pipeline = ExpertTrainingPipeline(training_data)

    # Train for 100 epochs (2-3 days on GPU)
    asyncio.run(pipeline.train_all_experts(epochs=100))
```

**Deliverable**:
- Training pipeline (500 lines)
- Evaluation metrics
- Model checkpoints
- Training logs and charts

---

### **B.6: Post-Game Learning Loop (2 days)**

**Integration with Existing System**:

```python
# Create: /src/ml/learning/post_game_learner.py

class PostGameLearner:
    """Process game results and update expert models"""

    async def process_completed_game(self, game_id: str):
        """
        Called after a game completes.

        Workflow:
        1. Fetch expert predictions for this game
        2. Fetch actual game outcome
        3. Calculate rewards for each expert
        4. Update expert policies
        5. Create episodic memories
        6. Detect belief revisions
        """

        # 1. Get predictions
        predictions = await self.db.fetch_expert_predictions(game_id)

        # 2. Get outcome
        outcome = await self.db.fetch_game_outcome(game_id)

        # 3. For each expert
        for pred in predictions:
            expert = self.get_expert(pred['expert_id'])

            # Calculate reward
            reward = expert._calculate_reward(pred, outcome)

            # Update policy
            expert.learn_from_outcome(pred, outcome)

            # Create episodic memory
            memory = self._create_memory(pred, outcome, reward)
            await self.db.store_episodic_memory(memory)

            # Check for belief revision
            if self._should_revise_belief(pred, outcome):
                revision = self._create_belief_revision(pred, outcome)
                await self.db.store_belief_revision(revision)
```

---

### **B.7: Validation & Backtesting (2 days)**

**Validate trained models against historical data**:

```python
# Update existing backtesting framework to use trained models

from src.ml.agents.base_expert_agent import ExpertAgent

class RLBacktestRunner:
    """Backtest with trained RL agents (not rule-based)"""

    def __init__(self):
        # Load trained models
        self.experts = self._load_trained_experts()

    def _load_trained_experts(self) -> List[ExpertAgent]:
        """Load all 15 trained expert models"""
        experts = []
        for i in range(15):
            expert = ExpertAgent.load(f"models/expert_{i}_final.zip")
            experts.append(expert)
        return experts

    async def run_backtest(self, season: int) -> Dict:
        """
        Backtest trained experts on full season.

        Target: > 55% accuracy ATS
        """
        # Same logic as before, but using trained RL models
        # instead of rule-based predictions
```

---

### **Phase B Success Criteria** ✅

| Criterion | Target | Validation |
|-----------|--------|------------|
| Training data acquired | 570 games | nflfastR data loaded |
| Feature engineering | 100 features | Pipeline tested |
| Personality models | 15 experts | All configured |
| RL agents trained | 100 epochs | Models converged |
| Backtest accuracy | > 55% ATS | Validation passed |
| Learning loop | Working | Post-game updates |
| Model checkpoints | Saved | Can load/resume |
| Calibration | ECE < 0.10 | Well-calibrated |

**Phase B Completion Time**: 3 weeks (21 days)

---

## 🎨 Phase C: Polish (2 Weeks = 14 Days)

### **Objective**: Production-Ready System with Calibration & Monitoring

### **C.1: Calibration System (3 days)**

**Create**: `/src/ml/calibration/calibrator.py`

```python
import numpy as np
from scipy.optimize import minimize
from sklearn.isotonic import IsotonicRegression

class ConfidenceCalibrator:
    """Calibrate expert confidence to match actual outcomes"""

    def calculate_ece(
        self,
        confidences: np.ndarray,
        outcomes: np.ndarray,
        n_bins: int = 10
    ) -> float:
        """
        Expected Calibration Error.

        Measures how well confidence matches reality.
        ECE < 0.05 is excellent, < 0.10 is good.
        """
        bins = np.linspace(0, 1, n_bins + 1)
        bin_indices = np.digitize(confidences, bins) - 1

        ece = 0.0
        for i in range(n_bins):
            mask = bin_indices == i
            if mask.sum() == 0:
                continue

            bin_confidences = confidences[mask]
            bin_outcomes = outcomes[mask]

            avg_confidence = bin_confidences.mean()
            avg_accuracy = bin_outcomes.mean()

            ece += mask.sum() / len(confidences) * abs(avg_confidence - avg_accuracy)

        return ece

    def apply_platt_scaling(
        self,
        confidences: np.ndarray,
        outcomes: np.ndarray
    ) -> callable:
        """
        Platt scaling: Learn sigmoid to calibrate confidences.

        Returns calibration function.
        """
        def sigmoid(x, a, b):
            return 1 / (1 + np.exp(-(a * x + b)))

        def loss(params):
            a, b = params
            calibrated = sigmoid(confidences, a, b)
            return ((calibrated - outcomes) ** 2).mean()

        result = minimize(loss, x0=[1.0, 0.0], method='BFGS')
        a, b = result.x

        return lambda x: sigmoid(x, a, b)

    def calibrate_expert(self, expert_id: str):
        """Calibrate specific expert's confidence"""

        # Fetch historical predictions and outcomes
        history = self.db.fetch_expert_history(expert_id)

        confidences = np.array([h['confidence'] for h in history])
        outcomes = np.array([1.0 if h['correct'] else 0.0 for h in history])

        # Calculate ECE before calibration
        ece_before = self.calculate_ece(confidences, outcomes)

        # Apply Platt scaling
        calibration_fn = self.apply_platt_scaling(confidences, outcomes)

        # Calibrated confidences
        calibrated = np.array([calibration_fn(c) for c in confidences])

        # Calculate ECE after calibration
        ece_after = self.calculate_ece(calibrated, outcomes)

        print(f"{expert_id} - ECE: {ece_before:.3f} → {ece_after:.3f}")

        # Store calibration function
        self.store_calibration_function(expert_id, calibration_fn)
```

---

### **C.2: Optimized Vote Weighting (2 days)**

**Update**: `/src/ml/expert_competition/voting_consensus.py`

```python
def calculate_vote_weight_v2(
    expert_id: str,
    prediction: Dict,
    performance: Dict,
    calibration: Dict
) -> float:
    """
    Updated vote weight formula with calibration.

    NEW FORMULA:
    weight = (
        accuracy * 0.30 +
        recent_performance * 0.25 +
        calibration_score * 0.25 +  # NEW!
        specialization * 0.10 +
        consistency * 0.05 +
        confidence * 0.05  # REDUCED from 0.20
    )

    Key change: Calibration now major factor (25%)
    Confidence reduced to 5% to prevent overconfident experts dominating
    """

    accuracy = performance['accuracy']
    recent = performance['recent_performance']
    specialization = performance['specialization_weight']
    consistency = performance['consistency_score']
    confidence = prediction['confidence']

    # NEW: Calibration score
    # Rewards experts whose confidence matches outcomes
    calibration_score = 1.0 - calibration['ece']  # ECE of 0 = score of 1.0

    weight = (
        accuracy * 0.30 +
        recent * 0.25 +
        calibration_score * 0.25 +
        specialization * 0.10 +
        consistency * 0.05 +
        confidence * 0.05
    )

    return np.clip(weight, 0.0, 1.0)
```

---

### **C.3: Comprehensive Monitoring (3 days)**

**Create**: `/src/monitoring/production_monitor.py`

```python
from datadog import initialize, statsd
from sentry_sdk import capture_exception
import logging

class ProductionMonitor:
    """Production-grade monitoring and alerting"""

    def __init__(self):
        # Initialize Datadog
        initialize(api_key=os.getenv('DATADOG_API_KEY'))

        # Initialize Sentry
        sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))

    def track_prediction_latency(self, duration: float):
        """Track time to generate predictions"""
        statsd.histogram('nfl.prediction.latency', duration, tags=['service:expert-ai'])

    def track_api_request(self, endpoint: str, status_code: int, duration: float):
        """Track API performance"""
        statsd.increment('nfl.api.requests', tags=[f'endpoint:{endpoint}', f'status:{status_code}'])
        statsd.histogram('nfl.api.duration', duration, tags=[f'endpoint:{endpoint}'])

    def track_expert_accuracy(self, expert_id: str, accuracy: float):
        """Track expert accuracy over time"""
        statsd.gauge('nfl.expert.accuracy', accuracy, tags=[f'expert:{expert_id}'])

    def alert_expert_eliminated(self, expert_id: str, bankroll: float):
        """Alert when expert eliminated"""
        logging.critical(f"EXPERT ELIMINATED: {expert_id} - Final bankroll: ${bankroll}")
        statsd.event(
            title='Expert Eliminated',
            text=f'{expert_id} eliminated with ${bankroll} remaining',
            alert_type='error',
            tags=[f'expert:{expert_id}']
        )

    def alert_data_stale(self, data_source: str, age_hours: float):
        """Alert when data becomes stale"""
        if age_hours > 1.0:
            logging.warning(f"STALE DATA: {data_source} is {age_hours:.1f} hours old")
            statsd.event(
                title='Stale Data Detected',
                text=f'{data_source} data is {age_hours:.1f} hours old',
                alert_type='warning',
                tags=[f'source:{data_source}']
            )
```

---

### **C.4: Performance Optimization (3 days)**

#### **Database Optimization**
- Add missing indexes
- Query optimization
- Connection pooling
- Read replicas for reporting

#### **API Optimization**
- Response compression
- Pagination optimization
- Batch endpoints
- CDN for static assets

#### **Cache Strategy**
- Multi-tier caching (memory + Redis)
- Cache warming
- Intelligent invalidation
- Cache hit rate monitoring

---

### **C.5: Security Audit (2 days)**

- SQL injection prevention (parameterized queries)
- CORS configuration review
- Rate limiting enforcement
- API key rotation
- Input validation
- Error message sanitization
- DDoS protection (Cloudflare)

---

### **C.6: Load Testing (1 day)**

```python
# Create: /tests/load/load_test.py

from locust import HttpUser, task, between

class NFLPredictionUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_experts(self):
        self.client.get("/api/v1/experts")

    @task(2)
    def get_council(self):
        self.client.get("/api/v1/council/current")

    @task(2)
    def get_bets(self):
        self.client.get("/api/v1/bets/live")

    @task(1)
    def get_expert_bankroll(self):
        self.client.get("/api/v1/experts/the-analyst/bankroll")

# Run: locust -f tests/load/load_test.py --users 100 --spawn-rate 10
```

**Target**: Handle 100 concurrent users with < 500ms latency

---

### **Phase C Success Criteria** ✅

| Criterion | Target | Validation |
|-----------|--------|------------|
| Expert calibration | ECE < 0.10 | All 15 experts calibrated |
| Vote weighting | Optimized | Backtest improved |
| Monitoring | Complete | Datadog + Sentry configured |
| Performance | < 500ms API | Load test passed |
| Security | Hardened | Audit completed |
| Load capacity | 100+ users | Stress test passed |
| Error rate | < 0.1% | Production monitoring |
| Uptime | > 99.9% | Health checks working |

**Phase C Completion Time**: 2 weeks (14 days)

---

## 🚀 Phase D: Deployment (1 Week = 7 Days)

### **D.1: Docker Containerization (2 days)**
### **D.2: CI/CD Pipeline (2 days)**
### **D.3: Production Hosting (2 days)**
### **D.4: Launch & Monitoring (1 day)**

---

## 📊 Complete Timeline Summary

| Phase | Duration | Key Deliverables | Status |
|-------|----------|------------------|--------|
| **Phase A: Quick Win** | 2 days | Infrastructure validation, E2E flow | ⏳ Next |
| **Phase B: Expert AI** | 3 weeks | RL agents, training, learning loops | ⏳ Future |
| **Phase C: Polish** | 2 weeks | Calibration, monitoring, optimization | ⏳ Future |
| **Phase D: Deploy** | 1 week | Docker, CI/CD, production launch | ⏳ Future |
| **TOTAL** | **6.5 weeks** | Production-ready AI Council system | |

---

## 🎯 Next Session Checklist

### **Start Phase A.1** (First 30 minutes)

- [ ] Test migrations in local Docker Postgres
- [ ] Verify all 6 tables created
- [ ] Check triggers and functions work
- [ ] Apply to Supabase (with backup!)
- [ ] Configure .env with all API keys
- [ ] Test API key validity

### **Quick Wins to Show**

- [ ] FastAPI running at localhost:8000
- [ ] OpenAPI docs at /docs working
- [ ] First API call returns real data
- [ ] WebSocket connection established
- [ ] Frontend loads without mock data

---

**Let's execute Phase A tomorrow!** 🚀