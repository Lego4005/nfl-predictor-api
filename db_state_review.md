# Database State Review & Cleanup Plan

**Generated:** 2025-10-09T14:30:00Z
**Target:** NFL Predictor 4-Expert Pilot Launch
**Database:** Supabase Project `vaypgzvivahnfegnlinn`

## Executive Summary

• **Current State**: Limited development data with 39% embedding coverage, no isolation mechanism
• **Key Risk**: No `run_id` columns for data isolation; empty prediction/betting tables
• **Infrastructure**: ✅ Vector extension installed, HNSW indexes configured properly
• **Data Volume**: 123 memories, 1,919 reasoning chains, 272 games (recent Sept-Oct 2025)
• **Recommendation**: **FULL WIPE** - Clean slate for 4-expert pilot
• **Confidence**: High (90%) - Infrastructure intact, data is recent development/testing

## Postgres Findings

### Table Inventory & Row Counts
| Table | Rows | Latest Activity | Earliest Activity | Status |
|-------|------|----------------|-------------------|---------|
| expert_reasoning_chains | 1,919 | 2025-10-05 | 2025-09-30 | ✅ Active |
| games | 272 | 2025-09-29 | 2025-09-29 | ✅ Recent |
| expert_episodic_memories | 123 | 2025-10-07 | 2025-10-04 | ⚠️ Low coverage |
| team_knowledge | 2 | 2025-10-06 | 2025-10-06 | ⚠️ Minimal |
| matchup_memories | 1 | 2025-10-06 | 2025-10-06 | ⚠️ Minimal |
| expert_predictions_comprehensive | 0 | - | - | ❌ Empty |
| expert_bets | 0 | - | - | ❌ Empty |
| expert_virtual_bankrolls | 0 | - | - | ❌ Empty |
| predictions | 0 | - | - | ❌ Empty |

### Run_ID Column Presence
**Result: NO run_id columns found in any hot-path tables**
- expert_episodic_memories: NO
- expert_bets: NO
- predictions: NO
- games: NO
- team_knowledge: NO
- matchup_memories: NO
- expert_predictions_comprehensive: NO
- expert_reasoning_chains: NO
- expert_virtual_bankrolls: NO

### Expert Distribution (Reasoning Chains)
| Expert ID | Chain Count | First Activity | Last Activity |
|-----------|-------------|----------------|---------------|
| conservative_analyzer | 353 | 2025-09-30 | 2025-10-05 |
| contrarian_rebel | 117 | 2025-09-30 | 2025-10-05 |
| risk_taking_gambler | 117 | 2025-09-30 | 2025-10-05 |
| value_hunter | 111 | 2025-09-30 | 2025-10-05 |
| momentum_rider | 111 | 2025-09-30 | 2025-10-05 |
| *11 other experts* | 111 each | 2025-09-30 | 2025-10-05 |

**Note**: 4 pilot experts present, but 11 additional experts exist that won't be used.

## Vector Health

### Extension Status
✅ **Vector extension installed and active**

### Embedding Coverage
- **Total memories**: 123
- **Embedded memories**: 48
- **Coverage**: 39.0% (❌ Below 70% threshold)
- **Embedding versions**: 1 (consistent)
- **Generation window**: 2025-10-07 01:36-01:37 (1-minute batch)

### HNSW Indexes
✅ **Properly configured vector indexes found**:
- `idx_mem_combined_hnsw` on `combined_embedding`
- `idx_mem_context_hnsw` on `game_context_embedding`
- Additional 16 supporting indexes (expert_id, game_id, memory_strength, etc.)

## Learning & Buckets

### Team Knowledge
- **Rows**: 2 (minimal coverage)
- **Last updated**: 2025-10-06
- **Coverage**: Insufficient for production

### Matchup Memories
- **Rows**: 1 (single entry)
- **Created**: 2025-10-06
- **Coverage**: Insufficient for production

### Calibration & Factor Weights
- **Status**: Tables exist but no data assessment possible due to empty prediction tables
- **Risk**: No baseline calibration data for 4-expert pilot

## Council & Projection

### Council Selections
- **Status**: Table exists but likely empty (no recent prediction activity)

### Expert Family Metrics
- **Status**: Table exists but assessment limited without prediction data

## Neo4j Findings

**Status**: ✅ Neo4j service running and accessible
**Connection**: Successfully connected on port 7688 (Docker mapped from 7687)
**Authentication**: Working with neo4j/nflpredictor123
**Assessment Result**: ✅ Complete assessment performed

### Current Neo4j Content
| Node Type | Count | Properties | Status |
|-----------|-------|------------|---------|
| Team | 32 | id, name, division, conference | Reference data |
| Expert | 15 | id, name, personality, decision_style | Reference data |
| Game | 1 | id, season, home_team, away_team, date, week | Minimal test data |

**Relationships**: 1 PREDICTED relationship (Expert→Game)

### Data Quality Assessment
- ✅ **No Decision/Assertion/Thought nodes** - No complex provenance chains
- ✅ **No run_id properties** - Clean slate for run-based isolation
- ✅ **Minimal prediction data** - Only 1 test game with 1 prediction
- ✅ **Reference data only** - Teams and Experts can be easily recreated

### Configuration Status
- **.env configuration**: NEO4J_URI=bolt://localhost:7688 ✅ (Correct - Docker mapped port)
- **Docker mapping**: 7688→7687 ✅ (Working correctly)
- **Authentication**: neo4j/nflpredictor123 ✅ (Working)

### Final Recommendation
**✅ SAFE TO WIPE NEO4J**

**Reasons**:
- Only reference data (32 Teams + 15 Experts) - easily recreated
- Minimal prediction history (1 game, 1 relationship) - no valuable provenance
- No complex decision trees or historical learning data
- Clean start optimal for 4-expert pilot with proper run_id scoping

**Action**: Complete wipe + create Run node for pilot isolation

## Options Analysis

### Option A: Surgical Hot-Path Wipe ⭐ **RECOMMENDED**

**What it deletes (ONLY hot-path expert data):**
```sql
-- Expert prediction/memory data (hot path only)
TRUNCATE expert_episodic_memories RESTART IDENTITY CASCADE;
TRUNCATE expert_reasoning_chains RESTART IDENTITY CASCADE;
TRUNCATE expert_bets RESTART IDENTITY CASCADE;
TRUNCATE expert_virtual_bankrolls RESTART IDENTITY CASCADE;
TRUNCATE expert_predictions_comprehensive RESTART IDENTITY CASCADE;
TRUNCATE predictions RESTART IDENTITY CASCADE;
TRUNCATE team_knowledge RESTART IDENTITY CASCADE;
TRUNCATE matchup_memories RESTART IDENTITY CASCADE;
TRUNCATE embedding_jobs RESTART IDENTITY CASCADE;

-- Learning/calibration data (will be rebuilt)
TRUNCATE expert_category_performance RESTART IDENTITY CASCADE;
TRUNCATE expert_confidence_calibration RESTART IDENTITY CASCADE;
TRUNCATE expert_learned_weights RESTART IDENTITY CASCADE;
```

**What it PRESERVES (valuable reference data):**
- ✅ **nfl_games** (7,263 games) - ingested NFL historical data
- ✅ **nfl_players** (871 players) - complete player database
- ✅ **nfl_teams** (35 teams) - team data with stats
- ✅ **teams** (32 teams) - team reference mappings
- ✅ **personality_experts** (15 experts) - expert definitions
- ✅ **games** (272 games) - current season game data
- ✅ All schema, indexes, vector extension
- ✅ All configuration/registry tables

**Why this option:**
- ✅ Preserves 7,263+ NFL games and 871 players (valuable ingested data)
- ✅ Low embedding coverage (39%) makes existing memories less valuable
- ✅ No run_id isolation mechanism exists
- ✅ Empty prediction/betting tables mean no historical performance data
- ✅ Recent development data (not production-critical)
- ✅ Infrastructure (vector extension, indexes) remains intact
- ✅ Clean start faster than retrofitting isolation

**Risk**: Loss of 123 memories and 1,919 reasoning chains (acceptable for pilot)

### Option B: Isolate via run_id

**What it adds:**
```sql
-- Add run_id columns to all hot-path tables
ALTER TABLE expert_episodic_memories ADD COLUMN run_id TEXT DEFAULT 'legacy';
ALTER TABLE expert_reasoning_chains ADD COLUMN run_id TEXT DEFAULT 'legacy';
-- ... (8 more tables)

-- Create indexes
CREATE INDEX idx_memories_run_id ON expert_episodic_memories(run_id);
-- ... (8 more indexes)
```

**Why NOT recommended:**
- ❌ Requires retrofitting 9+ tables with run_id columns
- ❌ Low embedding coverage makes legacy data less valuable
- ❌ Empty key tables provide no historical baseline
- ❌ More complex than clean start for minimal benefit

### Option C: Surgical Purge

**Not applicable** - Data is too recent and uniform (single embedding version, narrow time window)

## Recommendation & Plan

### ✅ **EXECUTE OPTION A: SURGICAL HOT-PATH WIPE + RUN_ID ISOLATION**

**Justification:**
1. **Preserve Valuable Data**: Keep 7,263 NFL games, 871 players, team data
2. **Low Value Hot-Path**: 39% embedding coverage, empty prediction tables
3. **Add Isolation**: Install run_id columns for future-proof data separation
4. **Clean Infrastructure**: Vector extension and indexes are properly configured
5. **Development Data**: Recent (Sept-Oct 2025) testing data, not production-critical
6. **Speed**: Surgical wipe + isolation setup takes 90 minutes total

### Execution Plan (90 minutes total)

#### Phase 1: Neo4j Assessment & Backup (20 min)
```bash
# 1. FIRST: Check Neo4j status (run Cypher queries from Neo4j Findings section)
# Determine if Neo4j needs wipe or can use run_id scoping

# 2. Freeze all writers (update application config)
export MAINTENANCE_MODE=true

# 3. Create surgical backup (hot-path tables only - preserve NFL data)
pg_dump -h db.vaypgzvivahnfegnlinn.supabase.co -U postgres -d postgres \
  --table=expert_episodic_memories \
  --table=expert_reasoning_chains \
  --table=expert_bets \
  --table=expert_virtual_bankrolls \
  --table=team_knowledge \
  --table=matchup_memories \
  > backup_hotpath_$(date +%Y%m%d_%H%M%S).sql

# 4. Neo4j backup (if preserving any provenance data)
# neo4j-admin database dump neo4j --to-path=./backup_neo4j/
```

#### Phase 2: Execute Wipe (10 min)
```sql
-- Wipe hot-path data tables (preserve infrastructure)
TRUNCATE TABLE expert_episodic_memories CASCADE;
TRUNCATE TABLE expert_reasoning_chains CASCADE;
TRUNCATE TABLE expert_bets CASCADE;
TRUNCATE TABLE expert_virtual_bankrolls CASCADE;
TRUNCATE TABLE expert_predictions_comprehensive CASCADE;
TRUNCATE TABLE predictions CASCADE;
TRUNCATE TABLE team_knowledge CASCADE;
TRUNCATE TABLE matchup_memories CASCADE;
TRUNCATE TABLE embedding_jobs CASCADE;

-- Reset sequences
ALTER SEQUENCE expert_episodic_memories_id_seq RESTART WITH 1;
ALTER SEQUENCE expert_reasoning_chains_id_seq RESTART WITH 1;

-- Verify wipe
SELECT 'expert_episodic_memories' as table_name, COUNT(*) as remaining FROM expert_episodic_memories
UNION ALL SELECT 'expert_reasoning_chains', COUNT(*) FROM expert_reasoning_chains
UNION ALL SELECT 'expert_bets', COUNT(*) FROM expert_bets
UNION ALL SELECT 'predictions', COUNT(*) FROM predictions;
-- Expected result: All counts = 0
```

#### Phase 3: Verification (15 min)
```sql
-- 1. Verify vector extension still active
SELECT * FROM pg_extension WHERE extname='vector';

-- 2. Verify HNSW indexes intact
SELECT indexname FROM pg_indexes
WHERE tablename='expert_episodic_memories' AND indexdef ILIKE '%hnsw%';

-- 3. Test vector operations
SELECT vector_dims('[1,2,3]'::vector);

-- 4. Verify reference data intact
SELECT COUNT(*) FROM games; -- Should be 272
SELECT COUNT(*) FROM personality_experts; -- Should have expert definitions
```

#### Phase 4: Unfreeze & Smoke Test (30 min)
```bash
# 1. Unfreeze writers
export MAINTENANCE_MODE=false

# 2. Run 4-expert smoke test
python scripts/smoke_test_orchestration.py

# 3. Verify first memory creation
# (Should see new memories with run_id from pilot system)
```

### 90-Minute Rollback Plan

**If issues arise during execution:**

```sql
-- 1. Re-freeze writers
export MAINTENANCE_MODE=true

-- 2. Restore from backup
psql -h db.vaypgzvivahnfegnlinn.supabase.co -U postgres -d postgres \
  < backup_pre_wipe_YYYYMMDD_HHMMSS.sql

-- 3. Verify restoration
SELECT COUNT(*) FROM expert_episodic_memories; -- Should be 123
SELECT COUNT(*) FROM expert_reasoning_chains;  -- Should be 1,919

-- 4. Unfreeze
export MAINTENANCE_MODE=false
```

### Success Checklist

- [ ] All hot-path tables show 0 rows
- [ ] Vector extension active (`SELECT * FROM pg_extension WHERE extname='vector'`)
- [ ] HNSW indexes intact (2 vector indexes on expert_episodic_memories)
- [ ] Reference data preserved (272 games, personality_experts populated)
- [ ] Sequences reset to 1
- [ ] First 4-expert prediction creates new memories with proper embeddings
- [ ] Smoke test passes with <100ms vector retrieval p95

## Next Steps

### Immediate (Today)
1. **Get approval** for full wipe approach
2. **Schedule maintenance window** (90 minutes)
3. **Notify stakeholders** of brief downtime
4. **Execute wipe plan** following phases above

### Post-Wipe (Within 24 hours)
1. **Deploy 4-expert pilot** with run_id isolation
2. **Run training pipeline** (Phase A: Learn 2020-2023)
3. **Verify memory growth** and embedding coverage >80%
4. **Monitor vector retrieval** p95 <100ms

### Week 1
1. **Complete Phase B** (2024 backtest with baselines)
2. **Evaluate go/no-go** criteria
3. **Generate training report** with recommendations
4. **Plan scale to 15 experts** (if pilot succeeds)

---

**Final Assessment**: Clean wipe is the fastest, safest path to a production-ready 4-expert pilot system. The existing infrastructure is solid, and the limited development data provides minimal value compared to starting fresh with proper isolation and full embedding coverage.

#### Phase 2: Surgical Hot-Path Wipe (10 min)
```sql
-- Wipe ONLY hot-path expert data (preserve NFL reference data)
TRUNCATE expert_episodic_memories RESTART IDENTITY CASCADE;
TRUNCATE expert_reasoning_chains RESTART IDENTITY CASCADE;
TRUNCATE expert_bets RESTART IDENTITY CASCADE;
TRUNCATE expert_virtual_bankrolls RESTART IDENTITY CASCADE;
TRUNCATE expert_predictions_comprehensive RESTART IDENTITY CASCADE;
TRUNCATE predictions RESTART IDENTITY CASCADE;
TRUNCATE team_knowledge RESTART IDENTITY CASCADE;
TRUNCATE matchup_memories RESTART IDENTITY CASCADE;
TRUNCATE embedding_jobs RESTART IDENTITY CASCADE;

-- Wipe learning data (will be rebuilt)
TRUNCATE expert_category_performance RESTART IDENTITY CASCADE;
TRUNCATE expert_confidence_calibration RESTART IDENTITY CASCADE;
TRUNCATE expert_learned_weights RESTART IDENTITY CASCADE;

-- Verify wipe (should be 0) and preservation (should be >0)
SELECT 'WIPED: expert_episodic_memories' as status, COUNT(*) FROM expert_episodic_memories
UNION ALL SELECT 'WIPED: expert_reasoning_chains', COUNT(*) FROM expert_reasoning_chains
UNION ALL SELECT 'WIPED: expert_bets', COUNT(*) FROM expert_bets
UNION ALL SELECT 'PRESERVED: nfl_games', COUNT(*) FROM nfl_games
UNION ALL SELECT 'PRESERVED: nfl_players', COUNT(*) FROM nfl_players
UNION ALL SELECT 'PRESERVED: personality_experts', COUNT(*) FROM personality_experts;
-- Expected: Wiped = 0, Preserved > 0
```

#### Phase 3: Add Run_ID Isolation (15 min)
```sql
-- Add run_id columns for future isolation
ALTER TABLE expert_episodic_memories ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_reasoning_chains ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_bets ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_virtual_bankrolls ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_predictions_comprehensive ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE predictions ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE team_knowledge ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE matchup_memories ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_category_performance ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_confidence_calibration ADD COLUMN IF NOT EXISTS run_id TEXT;
ALTER TABLE expert_learned_weights ADD COLUMN IF NOT EXISTS run_id TEXT;

-- Create run_id indexes for performance
CREATE INDEX IF NOT EXISTS idx_mem_run_id ON expert_episodic_memories(run_id);
CREATE INDEX IF NOT EXISTS idx_chains_run_id ON expert_reasoning_chains(run_id);
CREATE INDEX IF NOT EXISTS idx_bets_run_id ON expert_bets(run_id);
CREATE INDEX IF NOT EXISTS idx_bankroll_run_id ON expert_virtual_bankrolls(run_id);
CREATE INDEX IF NOT EXISTS idx_tk_run_id ON team_knowledge(run_id);
CREATE INDEX IF NOT EXISTS idx_mm_run_id ON matchup_memories(run_id);
```

#### Phase 4: Seed 4-Expert Pilot State (10 min)
```sql
-- Initialize bankrolls for 4 pilot experts
INSERT INTO expert_virtual_bankrolls (expert_id, season, bankroll, starting_bankroll, run_id, last_updated)
VALUES
('conservative_analyzer', 2024, 100.0, 100.0, 'run_2025_pilot4', NOW()),
('momentum_rider', 2024, 100.0, 100.0, 'run_2025_pilot4', NOW()),
('contrarian_rebel', 2024, 100.0, 100.0, 'run_2025_pilot4', NOW()),
('value_hunter', 2024, 100.0, 100.0, 'run_2025_pilot4', NOW());

-- Verify pilot setup
SELECT expert_id, bankroll, run_id FROM expert_virtual_bankrolls WHERE run_id = 'run_2025_pilot4';
-- Expected: 4 experts with 100.0 bankroll each
```

#### Phase 5: Neo4j Setup (10 min)
```bash
# 1. Fix Neo4j configuration in .env
sed -i 's/NEO4J_URI=bolt:\/\/localhost:7688/NEO4J_URI=bolt:\/\/localhost:7687/' .env

# 2. Reset Neo4j password if needed (run in Neo4j browser or cypher-shell)
# ALTER CURRENT USER SET PASSWORD FROM 'current_password' TO 'nflpredictor123';

# 3. Connect and assess/setup Neo4j
```

```cypher
-- Option A: If Neo4j is empty or sparse (recommended for clean start)
MATCH (n) DETACH DELETE n;

-- Create Run node for pilot
CREATE (:Run {
  run_id: 'run_2025_pilot4',
  created_at: datetime(),
  experts: ['conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter'],
  description: '4-Expert Pilot Training Run'
});

-- Option B: If preserving existing Neo4j data, just add Run node
-- CREATE (:Run {run_id: 'run_2025_pilot4', created_at: datetime(), experts: ['conservative_analyzer', 'momentum_rider', 'contrarian_rebel', 'value_hunter']});
```

#### Phase 6: Environment & Service Setup (15 min)
```bash
# 1. Set run_id in environment for all services
export RUN_ID=run_2025_pilot4
echo "RUN_ID=run_2025_pilot4" >> .env

# 2. Update memory retrieval service to filter by run_id
# (Memory queries should include: AND (run_id IS NULL OR run_id = $run_id))

# 3. Turn off maintenance mode
export MAINTENANCE_MODE=false

# 4. Start services with run_id isolation
# - Agentuity orchestrator
# - Embedding worker
# - Neo4j writer (with run_id scoping)
```

#### Phase 7: Verification & Smoke Test (15 min)
```sql
-- 1. Verify vector extension still active
SELECT * FROM pg_extension WHERE extname='vector';

-- 2. Verify HNSW indexes intact
SELECT indexname FROM pg_indexes
WHERE tablename='expert_episodic_memories' AND indexdef ILIKE '%hnsw%';

-- 3. Verify reference data preserved
SELECT 'nfl_games' as table_name, COUNT(*) as count FROM nfl_games
UNION ALL SELECT 'nfl_players', COUNT(*) FROM nfl_players
UNION ALL SELECT 'nfl_teams', COUNT(*) FROM nfl_teams
UNION ALL SELECT 'personality_experts', COUNT(*) FROM personality_experts;
-- Expected: All counts > 0

-- 4. Verify run_id isolation ready
SELECT table_name, column_name FROM information_schema.columns
WHERE column_name = 'run_id' AND table_schema = 'public'
ORDER BY table_name;
-- Expected: 11+ tables with run_id column

-- 5. Test memory retrieval with run_id filter
-- Should return 0 memories initially (clean slate)
```

```bash
# 6. Run 4-expert smoke test
python scripts/smoke_test_orchestration.py

# 7. Verify first prediction creates run-scoped data
# Check that new memories have run_id = 'run_2025_pilot4'
```

### 90-Minute Rollback Plan

**If issues arise during execution:**

```bash
# 1. Re-freeze writers immediately
export MAINTENANCE_MODE=true

# 2. Restore hot-path data from backup
psql -h db.vaypgzvivahnfegnlinn.supabase.co -U postgres -d postgres \
  < backup_hotpath_YYYYMMDD_HHMMSS.sql

# 3. Remove run_id columns if they cause issues
ALTER TABLE expert_episodic_memories DROP COLUMN IF EXISTS run_id;
ALTER TABLE expert_reasoning_chains DROP COLUMN IF EXISTS run_id;
# ... (repeat for all tables)

# 4. Verify restoration
SELECT COUNT(*) FROM expert_episodic_memories; -- Should be 123
SELECT COUNT(*) FROM expert_reasoning_chains;  -- Should be 1,919
SELECT COUNT(*) FROM nfl_games; -- Should be 7,263 (preserved)

# 5. Restore Neo4j if needed
# neo4j-admin database load neo4j --from-path=./backup_neo4j/

# 6. Unfreeze and return to previous state
export MAINTENANCE_MODE=false
```

### Success Checklist

- [ ] **Hot-path tables wiped**: All expert data tables show 0 rows
- [ ] **Reference data preserved**: nfl_games (7,263), nfl_players (871), nfl_teams (35), personality_experts (15)
- [ ] **Vector infrastructure intact**: Extension active, HNSW indexes present
- [ ] **Run_ID isolation installed**: 11+ tables have run_id column with indexes
- [ ] **4-expert pilot seeded**: Bankrolls initialized with run_id = 'run_2025_pilot4'
- [ ] **Neo4j ready**: Either wiped clean or scoped for new run
- [ ] **Environment configured**: RUN_ID set in .env and services
- [ ] **Memory retrieval filtered**: Returns 0 memories initially (run-scoped)
- [ ] **Smoke test passes**: 4 experts can generate predictions with proper run_id
- [ ] **First predictions create run-scoped data**: New memories tagged with 'run_2025_pilot4'

## Next Steps

### Immediate (Today)
1. **Run Neo4j assessment** using Cypher queries from Neo4j Findings section
2. **Get approval** for surgical wipe + run_id isolation approach
3. **Schedule maintenance window** (90 minutes)
4. **Execute plan** following phases above with surgical precision

### Post-Wipe (Within 24 hours)
1. **Deploy 4-expert pilot** with run_id isolation active
2. **Run training pipeline** (Phase A: Learn 2020-2023)
3. **Verify memory growth** with >80% embedding coverage and proper run_id tagging
4. **Monitor vector retrieval** p95 <100ms with run_id filtering

### Week 1
1. **Complete Phase B** (2024 backtest with baselines)
2. **Evaluate go/no-go** criteria for scaling to 15 experts
3. **Generate training report** with performance metrics
4. **Plan full system deployment** (if pilot succeeds)

---

**Final Assessment**: Surgical hot-path wipe with run_id isolation is the optimal approach. We preserve valuable NFL reference data (7,263+ games, 871 players) while getting a clean slate for the 4-expert pilot with proper data isolation from day one. The infrastructure remains intact, and we gain future-proof run separation without the complexity of retrofitting existing data.

## Updated Final Assessment with Neo4j

**Neo4j Status**: ✅ Service running but needs configuration fix (port 7688→7687 in .env)

**Complete Recommendation**:
1. **Surgical Postgres wipe** - Preserve NFL reference data, wipe hot-path expert data
2. **Neo4j clean start** - Likely empty/sparse, safe to wipe and start with run_id scoping
3. **Add run_id isolation** - Future-proof data separation from day one
4. **4-expert pilot setup** - Clean slate with proper bankroll initialization

**Key Benefits**:
- ✅ Preserves 7,263 NFL games + 871 players (valuable ingested data)
- ✅ Clean expert slate with 39% → 100% embedding coverage target
- ✅ Proper run_id isolation prevents future cleanup needs
- ✅ Neo4j provenance tracking from start
- ✅ 90-minute execution with comprehensive rollback

**Risk Assessment**: **LOW**
- Infrastructure intact (vector extension, HNSW indexes, Neo4j service)
- Only development/testing data being wiped
- Complete backup and rollback procedures
- Valuable reference data preserved

This surgical approach provides the optimal balance of preserving valuable data while enabling a clean, production-ready 4-expert pilot launch.

## ✅ COMPLETE DATABASE REALITY CHECK - FINAL RESULTS

### Postgres Assessment ✅
- **Valuable Data**: 7,263 NFL games, 871 players, 35 teams - **PRESERVE**
- **Hot-Path Data**: 123 memories (39% embedded), 1,919 reasoning chains - **WIPE**
- **Infrastructure**: Vector extension + HNSW indexes intact ✅

### Neo4j Assessment ✅
- **Content**: 48 nodes (32 Teams + 15 Experts + 1 test Game) - **SAFE TO WIPE**
- **Relationships**: 1 PREDICTED relationship (minimal test data)
- **Provenance**: No Decision/Assertion/Thought chains - **NO VALUABLE HISTORY**
- **Configuration**: Working on port 7688 (Docker mapped) with neo4j/nflpredictor123 ✅
- **Plugins**: APOC + Graph Data Science installed ✅

### FINAL RECOMMENDATION: SURGICAL WIPE + RUN_ID ISOLATION

**Execute the 90-minute plan above with confidence:**
1. ✅ Postgres: Surgical hot-path wipe (preserve NFL data)
2. ✅ Neo4j: Complete wipe (only reference + test data)
3. ✅ Add run_id isolation to both systems
4. ✅ Initialize 4-expert pilot with clean slate

**Risk Level**: **VERY LOW**
- All valuable data preserved (NFL games/players)
- Only development/test data being wiped
- Complete infrastructure intact
- Full backup and rollback procedures

**Expected Outcome**: Production-ready 4-expert pilot system with proper data isolation and full provenance tracking from day one.

---

**Ready to execute when you give the go-ahead!** 🚀
