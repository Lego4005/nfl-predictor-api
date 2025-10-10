# ExpertBetting System - 4-Expert Pilot Runbook

## Overview

This runbook gets the 4-expert pilot running today with real results. Two execution paths available:
- **Plan A (Recommended)**: Train on 2020-2023, then backtest 2024 "for real"
- **Plan B**: Predict all 4 seasons in one sweep

## Start-Up Order (15-20 minutes)

### 1. Set Run Isolation

```bash
# Export clean run ID (keep consistent everywhere)
export RUN_ID=run_2025_pilot4

# Set in all service environments
echo "RUN_ID=run_2025_pilot4" >> .env

# Verify run_id filtering is active
curl "http://localhost:8000/api/context/conservative_analyzer/test_game_1" | grep run_id
```

### 2. Bring Services Up

```bash
# Start FastAPI (maintenance off)
uvicorn src.api.main:app --reload --port 8000 &

# Start embedding worker (idle until predictions exist)
python src/workers/embedding_worker.py &

# Start Neo4j write-behind (idempotent merges)
python src/services/neo4j_provenance_service.py &

# Start Agentuity orchestrator
cd agentuity && npm run start &

# System smoke test
python3 scripts/system_status.py

# Health check
curl http://localhost:8000/api/smoke-test/health
```

### 3. Set Expert Cohort (4 Experts Only)

```bash
# Configure 4-expert pilot cohort
python3 -c "
from src.services.supabase_service import SupabaseService

experts = ['conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter']
run_id = 'run_2025_pilot4'
supabase = SupabaseService()

# Initialize bankrolls
for expert_id in experts:
    supabase.table('expert_bankroll').upsert({
        'expert_id': expert_id,
        'run_id': run_id,
        'current_bankroll': 100.0,
        'total_wagered': 0.0,
        'total_winnings': 0.0,
        'games_played': 0
    }).execute()
    print(f'✅ Initialized {expert_id}')

# Initialize calibration priors
for expert_id in experts:
    supabase.table('expert_category_calibration').upsert({
        'expert_id': expert_id,
        'run_id': run_id,
        'category': 'default',
        'alpha': 1.0,
        'beta': 1.0,
        'ema_mean': 0.0,
        'ema_variance': 1.0
    }).execute()

print('✅ Expert cohort initialized')
"
```

### 4. Model Router Configuration (OpenRouter)

```bash
# Test OpenRouter connection and set initial model assignments
python3 -c "
from src.services.openrouter_llm_service import get_llm_service

llm_service = get_llm_service()

# Test connection
import asyncio
test_result = asyncio.run(llm_service.test_connection())

if test_result['success']:
    print('✅ OpenRouter connection successful')
    print('📋 Model Assignments:')
    for expert_id, model in test_result['current_assignments'].items():
        print(f'   {expert_id} → {model}')

    print('🔧 Critic/Repair: Claude 3.5 Sonnet (≤2 loops)')
    print('👥 Shadow Models: Gemini Pro, Grok Beta (10-20% traffic)')
    print('⚡ All models accessible through single OpenRouter API')
else:
    print(f'❌ OpenRouter connection failed: {test_result[\"error\"]}')
    print('Please check your OPENROUTER_API_KEY in .env')
"
```

## Plan A (Recommended): Train 2020-2023 → Backtest 2024

### A1) 2020-2023 Training Pass (Stakes Low/Zero)

**Goal**: Build episodic memories, team/matchup buckets, and calibration

```bash
# Run training pass with stakes=0, reflections=off, tools=off
python3 scripts/pilot_training_runner.py \
  --run-id run_2025_pilot4 \
  --seasons 2020-2023 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --stakes 0 \
  --reflections off \
  --tools off

# Alternative: Orchestrate per game via Agentuity
# POST http://localhost:8000/api/orchestrate/game/{game_id}
# Body: {"expert_ids": ["conservative_analyzer", "momentum_rider", "contrarian_rebel", "value_hunter"]}
```

**Live Monitoring During Training**:
```bash
# Watch vector retrieval performance (p95 < 100ms)
curl http://localhost:8000/api/monitoring/vector-retrieval

# Check schema pass rate (≥98.5%)
curl http://localhost:8000/api/smoke-test/validate/schema

# Monitor embedding jobs draining
curl http://localhost:8000/api/monitoring/embedding-jobs

# Check calibration filling
python3 -c "
from src.services.supabase_service import SupabaseService
supabase = SupabaseService()
result = supabase.table('expert_category_calibration').select('*').eq('run_id', 'run_2025_pilot4').execute()
print(f'Calibration records: {len(result.data)}')
"
```

**Training Gate Check**:
```bash
# Verify memories present for all 4 experts
python3 scripts/check_training_completion.py --run-id run_2025_pilot4

# Expected output:
# ✅ Memories: 500+ per expert
# ✅ Beta/EMA populated
# ✅ Vector p95 < 100ms
# ✅ Schema pass rate ≥98.5%
```

### A2) 2024 Backtest (Real Stage with Baselines)

**Run One Week First (Small Batch)**:
```bash
# Get first week of 2024 games
python3 scripts/get_week_games.py --season 2024 --week 1

# Run with all baselines in parallel
python3 scripts/pilot_backtest_runner.py \
  --run-id run_2025_pilot4 \
  --season 2024 \
  --week 1 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --baselines coin_flip,market_only,one_shot,deliberate \
  --stakes 1.0 \
  --reflections off

# Compare results
curl http://localhost:8000/api/baseline-testing/compare \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"game_ids": ["week1_games"], "expert_ids": ["conservative_analyzer","momentum_rider","contrarian_rebel","value_hunter"]}'
```

**Baseline Comparison Metrics**:
- **Quality**: Brier (binary/enum), MAE/RMSE (numeric)
- **ROI/Bankroll**: Return on investment tracking
- **Coherence Deltas**: Projection movement analysis

**Promotion Rule**:
```bash
# Check if Deliberate beats One-shot by ≥2-4% Brier or ROI ≥ market-only
python3 scripts/evaluate_promotion.py --run-id run_2025_pilot4 --week 1

# If promotion criteria met, continue with Deliberate
# If not, route expert to One-shot until tuned
```

**Full 2024 Season** (if week 1 successful):
```bash
python3 scripts/pilot_backtest_runner.py \
  --run-id run_2025_pilot4 \
  --season 2024 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --baselines coin_flip,market_only,one_shot,deliberate \
  --stakes 1.0
```

## Plan B: Predict All 4 Seasons in One Go

```bash
# Single pass for all seasons 2020-2024
python3 scripts/pilot_full_runner.py \
  --run-id run_2025_pilot4 \
  --seasons 2020-2024 \
  --experts conservative_analyzer,momentum_rider,contrarian_rebel,value_hunter \
  --stakes 1.0

# Still run baselines for one week of 2024 as checkpoint
python3 scripts/pilot_backtest_runner.py \
  --run-id run_2025_pilot4 \
  --season 2024 \
  --week 1 \
  --baselines coin_flip,market_only,one_shot
```

## Live Ops Checklist (Monitor During Runs)

### Performance Monitoring
```bash
# Vector retrieval p95 < 100ms
curl http://localhost:8000/api/monitoring/vector-retrieval | jq '.p95_ms'

# K auto-reduction if breached
curl http://localhost:8000/api/monitoring/memory-retrieval | jq '.k_reductions'

# Cache hit rate
curl http://localhost:8000/api/monitoring/cache | jq '.hit_rate'
```

### LLM Performance
```bash
# Draft durations & Repair loops (avg ≤1.2 loops)
curl http://localhost:8000/api/monitoring/llm-performance

# Schema pass rate ≥98.5%
curl http://localhost:8000/api/smoke-test/validate/schema | jq '.schema_pass_rate'
```

### Storage Validation
```bash
# 83 assertions per expert per game
python3 -c "
from src.services.supabase_service import SupabaseService
supabase = SupabaseService()
result = supabase.table('expert_predictions').select('*').eq('run_id', 'run_2025_pilot4').execute()
print(f'Predictions stored: {len(result.data)}')
"

# Bets created with run_id
python3 -c "
from src.services.supabase_service import SupabaseService
supabase = SupabaseService()
result = supabase.table('expert_bets').select('*').eq('run_id', 'run_2025_pilot4').execute()
print(f'Bets created: {len(result.data)}')
"
```

### Settlement & Learning
```bash
# Bankroll monotonic (no negative ledger)
curl http://localhost:8000/api/smoke-test/validate/bankroll

# Neo4j provenance trails
curl http://localhost:8000/api/smoke-test/validate/provenance
```

## Safety Rails (If Something Goes Wrong)

### Schema Failure > 3%
```bash
# Switch expert to more structured primary
python3 -c "
from src.services.model_switching_service import ModelSwitchingService
from src.services.supabase_service import SupabaseService

switching_service = ModelSwitchingService(SupabaseService(), None)
switching_service.implement_model_switch(
    'failing_expert_id',
    'anthropic/claude-sonnet-4.5',
    'Schema failure > 3%'
)
print('✅ Switched to structured model')
"

# Enable one-shot for a few games
curl -X POST http://localhost:8000/api/baseline-testing/switching/implement \
  -H "Content-Type: application/json" \
  -d '{"expert_id": "failing_expert", "new_model": "one_shot", "reason": "Schema recovery"}'
```

### Retrieval p95 > 100ms
```bash
# Reduce K: 20→12→10→7
python3 -c "
from src.services.memory_retrieval_service import MemoryRetrievalService
from src.services.supabase_service import SupabaseService

service = MemoryRetrievalService(SupabaseService())
service.reduce_k_for_performance()
print('✅ K reduced for performance')
"

# Check HNSW index and cache
curl http://localhost:8000/api/monitoring/vector-index-status
```

### Slow Provider/Errors
```bash
# Router reassigns primary to next best eligible model
curl http://localhost:8000/api/baseline-testing/switching/recommendations

# Critic/Repair stays on Claude
python3 -c "
print('🔧 Critic/Repair remains on Claude Sonnet for reliability')
"
```

### Runaway Agent (Tools)
```bash
# Enforce tool budget (≤10 calls, ≤30-45s)
curl -X POST http://localhost:8000/api/expert/predictions \
  -H "Content-Type: application/json" \
  -d '{"mode": "degraded", "tool_budget": 10, "time_budget": 45}'
```

## Quick Verification Commands

```bash
# API Status
curl http://localhost:8000

# API Documentation
open http://localhost:8000/docs

# System Health
curl http://localhost:8000/api/smoke-test/health

# Comprehensive Status
python3 scripts/system_status.py

# Expert Leaderboard
curl http://localhost:8000/api/leaderboard

# Recent Predictions
curl http://localhost:8000/api/expert/predictions/recent

# Performance Metrics
curl http://localhost:8000/api/monitoring/metrics
```

## TL;DR "Do This Now" Sequence

1. **Set `RUN_ID=run_2025_pilot4`** ✅
2. **Start FastAPI → workers → Agentuity orchestrator** ✅
3. **Confirm 4 experts enabled; router configured** ✅
4. **Run 2020-2023 train pass** (stakes=0; tools off) ⏳
5. **Run 2024 one week with baselines** → compare ⏳
6. **If Deliberate lifts, continue full 2024**; else set expert to One-shot ⏳
7. **When happy, run 2025 YTD** the same way ⏳

## Expected Timeline

- **Setup**: 15-20 minutes
- **2020-2023 Training**: 2-4 hours (depending on game count)
- **2024 Week 1 Backtest**: 30-60 minutes
- **Full 2024 Season**: 4-8 hours
- **Analysis & Optimization**: Ongoing

## Success Metrics

- **Schema Pass Rate**: ≥98.5% ✅
- **Vector Retrieval**: p95 < 100ms ✅
- **End-to-End**: p95 < 6s ✅
- **Baseline Comparison**: Deliberate > One-shot by ≥2-4% Brier
- **ROI**: Positive ROI vs market-only baseline
- **System Stability**: No crashes, graceful degradation

**🚀 You've got all green lights - this will get you learning curves and side-by-side baselines fast!**
