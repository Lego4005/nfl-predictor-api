# Database Verification Report - Critical Issues Found

**Date**: 2025-09-29
**Status**: ❌ **MULTIPLE MISMATCHES DETECTED**

## 🚨 Critical Issues

### Issue 1: Expert ID Mismatch

**Database has OLD expert IDs:**
```
✅ Current Database:
- the_analyst
- the_veteran
- the_contrarian
- the_gambler
- the_momentum_rider
(Only 5 experts found!)
```

**ML Models expect NEW expert IDs:**
```
❌ Expected (from EXPERT_MODELS dict):
- conservative_analyzer
- risk_taking_gambler
- contrarian_rebel
- value_hunter
- momentum_rider
- fundamentalist_scholar
- chaos_theory_believer
- gut_instinct_expert
- statistics_purist
- trend_reversal_specialist
- popular_narrative_fader
- sharp_money_follower
- underdog_champion
- consensus_follower
- market_inefficiency_exploiter
(15 experts total)
```

**Frontend expects:**
```
✅ Frontend (expertPersonalities.ts):
- conservative_analyzer
- risk_taking_gambler
- contrarian_rebel
... (matches ML models)
```

**Root Cause**: Migration `021_expert_naming_standardization.sql` has NOT been applied to the database.

---

### Issue 2: Game ID Format Mismatch

**Database uses:**
```
✅ games.id = UUID string
Example: "b14a7012-133b-435d-86fa-472c40c966f0"
```

**Data Access Layer expects:**
```
❌ game_id format: "YYYY_WW_AWAY_HOME"
Example: "2025_03_KC_BUF"

See: expert_data_access_layer.py:273
parts = game_id.split('_')
season = int(parts[0])
week = int(parts[1])
away_team = parts[2]
home_team = parts[3]
```

**Impact**: The data access layer will FAIL when trying to parse UUID game IDs.

---

### Issue 3: Missing Experts in Database

**Database has**: 5 experts
**System needs**: 15 experts

**Missing experts**:
1. value_hunter (The Hunter)
2. fundamentalist_scholar (The Scholar)
3. chaos_theory_believer (The Chaos)
4. gut_instinct_expert (The Intuition)
5. statistics_purist (The Quant)
6. trend_reversal_specialist (The Reversal)
7. popular_narrative_fader (The Fader)
8. sharp_money_follower (The Sharp)
9. underdog_champion (The Underdog)
10. consensus_follower (The Consensus)
11. market_inefficiency_exploiter (The Exploiter)

---

## ✅ What's Working

1. **Episodic Memory Tables Exist**:
   - `expert_reasoning_chains` ✅
   - `expert_belief_revisions` ✅
   - `expert_episodic_memories` ✅

2. **Games Table Has Scores**:
   - `home_score` column exists ✅
   - `away_score` column exists ✅
   - Actual game results are available ✅

3. **Games Table Has All Data**:
   - 64 games from 2025 Weeks 1-4 ✅
   - Chronological ordering available ✅
   - Game status (final/scheduled) tracked ✅

---

## 🔧 Required Fixes

### Fix 1: Apply Expert Naming Migration

```bash
# Apply migration 021 to update expert IDs
psql $DATABASE_URL -f src/database/migrations/021_expert_naming_standardization.sql
```

This will:
- Update expert IDs from `the_analyst` → `conservative_analyzer`
- Add missing 10 experts
- Update all related tables (reasoning_chains, episodic_memories, etc.)

### Fix 2: Game ID Format Adapter

**Option A**: Modify data access layer to accept UUID game IDs
```python
# In expert_data_access_layer.py
def _parse_game_id(self, game_id: str, game_data: dict):
    # If UUID format, extract from game_data
    if len(game_id) > 20 and '-' in game_id:
        return {
            'season': game_data.get('season'),
            'week': game_data.get('week'),
            'home_team': game_data.get('home_team'),
            'away_team': game_data.get('away_team')
        }
    # Otherwise parse standard format
    else:
        parts = game_id.split('_')
        return {
            'season': int(parts[0]),
            'week': int(parts[1]),
            'away_team': parts[2],
            'home_team': parts[3]
        }
```

**Option B**: Pass team info separately instead of parsing game_id
```python
# Modify get_expert_data_view signature
async def get_expert_data_view(
    self,
    expert_id: str,
    game_id: str,
    season: int,
    week: int,
    home_team: str,
    away_team: str
) -> GameData:
    # Don't parse game_id, use parameters directly
```

### Fix 3: Verify Expert Models Match Database

After applying migration 021, verify:
```bash
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
from src.ml.expert_models import EXPERT_MODELS

load_dotenv()
supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

# Get DB experts
result = supabase.table('personality_experts').select('expert_id').execute()
db_experts = {e['expert_id'] for e in result.data}

# Get model experts
model_experts = set(EXPERT_MODELS.keys())

print('DB experts:', db_experts)
print('Model experts:', model_experts)
print('Match:', db_experts == model_experts)
"
```

---

## 📋 Testing Checklist

Before running `test_2025_sequential_learning.py`:

- [ ] Apply migration 021 to database
- [ ] Verify 15 experts exist in `personality_experts` table
- [ ] Expert IDs match between database and `EXPERT_MODELS`
- [ ] Fix game_id format handling in data access layer
- [ ] Test data access layer with UUID game IDs
- [ ] Verify episodic memory tables can store predictions
- [ ] Check reasoning chain logger integration
- [ ] Verify belief revision service integration

---

## 🎯 Recommended Action Plan

1. **Immediate**: Apply migration 021 to get 15 experts with correct IDs
2. **Quick Fix**: Modify data access layer to handle UUID game IDs
3. **Verify**: Test with 1-2 games before running full 64-game learning test
4. **Run**: Execute `test_2025_sequential_learning.py`
5. **Monitor**: Track expert accuracy improvements over 64 games

---

## 📊 Summary

| Component | Status | Issue |
|-----------|--------|-------|
| Expert IDs | ❌ | Only 5/15 experts, using old naming |
| Game ID Format | ❌ | UUID vs expected "YYYY_WW_AWAY_HOME" |
| Episodic Memory Tables | ✅ | All tables exist and working |
| Game Scores | ✅ | Available for all 64 games |
| Expert Models | ✅ | All 15 implemented correctly |
| Frontend | ✅ | Using correct expert IDs |

**Conclusion**: System is ready for learning tests AFTER applying migration 021 and fixing game_id format handling.