# 🧪 Episodic Memory System Testing Guide

## Current Status: ⚠️ Schema Cache Issue Detected

The migration has been applied to the database, but **PostgREST's schema cache needs to be reloaded** before the tests will pass.

---

## 🚀 Quick Fix: Reload Schema Cache

### Option 1: Via Supabase Dashboard (Recommended)

1. **Go to**: https://supabase.com/dashboard/project/xthjqprcpubinyzupsir
2. **Navigate to**: SQL Editor (left sidebar)
3. **Click**: "New Query"
4. **Paste and Run**:
   ```sql
   NOTIFY pgrst, 'reload schema';
   ```
5. **Wait**: 5-10 seconds for cache to refresh

### Option 2: Restart Database

1. **Go to**: https://supabase.com/dashboard/project/xthjqprcpubinyzupsir/settings/database
2. **Click**: "Restart database" button
3. **Wait**: ~30 seconds for restart to complete

---

## 📋 Testing Workflow (After Cache Reload)

### Step 1: Verify Schema (30 seconds)

```bash
# Check that migration columns now appear
python3 scripts/check_database_schema.py
```

**Expected Output**:
```
✅ All tables exist with correct columns
```

---

### Step 2: Run Comprehensive Test Suite (1 minute)

```bash
# Full test battery - 6 tests covering all memory functions
python3 tests/test_episodic_memory_system.py
```

**What It Tests**:
1. ✅ Database schema verification
2. ✅ Memory storage (episodic memories)
3. ✅ Memory retrieval (by context)
4. ✅ Lesson extraction (from predictions)
5. ✅ Principle storage (learned patterns)
6. ✅ Full learning cycle (end-to-end)

**Expected Output**:
```
====================================================================================================
  📊 TEST SUMMARY
====================================================================================================

Total Tests: 6
✅ Passed: 6
❌ Failed: 0
Success Rate: 100.0%

🎉 ALL TESTS PASSED! Memory system is fully operational!
```

---

### Step 3: Run Memory Journey Demonstration (30 seconds)

```bash
# Watch ONE expert learn across 4 weeks with full transparency
python3 scripts/supabase_memory_journey.py
```

**What You'll See**:
- Week-by-week game predictions
- Memory retrieval before each prediction
- Lesson extraction after each game
- Memory storage with emotions
- Database verification at the end

**Expected Output**:
```
🧠 SUPABASE MEMORY-ENABLED EXPERT JOURNEY

WEEK 1
─────────────────────────────────────────
🏈 Game 1: BAL @ KC

🔍 RETRIEVING MEMORIES...
   No past experiences (first game)

💭 MAKING PREDICTION...
   Predicted Winner: KC
   Confidence: 65.2%

📊 ACTUAL RESULT: KC wins 27-20
   ✅ CORRECT PREDICTION!

📚 EXTRACTING LESSONS...
   Learned 2 lessons:
   1. [confidence_calibration] High confidence predictions are reliable
   2. [home_field_advantage] KC benefits from home field

💾 STORING EPISODIC MEMORY...
   ✅ Memory stored with satisfaction emotion

🎓 DISCOVERED PRINCIPLE...
   ✅ Principle stored: High confidence predictions are reliable

[... continues for 5 games across 4 weeks ...]

🏆 FINAL SUMMARY
═══════════════════════════════════════
📊 Overall Performance:
   Total Games: 5
   Correct Predictions: 2-3
   Overall Accuracy: 40-60%

🧠 Learning Metrics:
   Episodic Memories Stored: 5 ✅
   Lessons Learned: 10 ✅
   Belief Revisions: 1 ✅

🔍 DATABASE VERIFICATION:
   ✅ 5 memories in database
   ✅ 2 principles in database

🎉 SUCCESS! Memory system is fully functional!
```

---

### Step 4: Run Diagnostic Verification (10 seconds)

```bash
# Deep dive into what the expert learned
python3 scripts/diagnose_memory_system.py
```

**Expected Output**:
```
TEST 1: Episodic Memories
✅ Found 5 episodic memories
   Memory 1: satisfaction emotion, vividness 0.75
   Memory 2: disappointment emotion, vividness 0.60
   ...

TEST 2: Learned Principles
✅ Found 2 active learned principles
   Principle 1: High confidence predictions are reliable (80% success)
   Principle 2: Home field advantage matters (60% success)

TEST 3: Belief Revisions
✅ Found 1 belief revision
   Changed confidence approach after repeated failures

🎯 VERDICT: ✅ HYPOTHESIS 1: GENUINE LEARNING
   The memory system is fully operational!
```

---

## 🎯 Success Criteria

### All Tests PASS If:

1. ✅ `test_episodic_memory_system.py` shows **6/6 tests passed**
2. ✅ `supabase_memory_journey.py` shows:
   - "Memory stored with [emotion] emotion" after each game
   - "X memories in database" where X > 0
   - "X principles in database" where X > 0
3. ✅ `diagnose_memory_system.py` shows non-zero counts for:
   - Episodic memories
   - Learned principles
   - Belief revisions (optional)

### Tests FAIL If:

1. ❌ Schema cache errors: `"Could not find the 'contextual_factors' column"`
   - **Fix**: Reload schema cache (see Quick Fix above)

2. ❌ Foreign key errors: `"violates foreign key constraint"`
   - **Fix**: Run `python3 scripts/initialize_experts.py` to create test experts

3. ❌ Connection errors: `"connection refused"`
   - **Fix**: Check `.env` file has correct `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`

---

## 🐛 Troubleshooting

### Issue: "Could not find column" errors

**Cause**: PostgREST schema cache is stale

**Fix**:
```sql
-- Run in Supabase Dashboard SQL Editor
NOTIFY pgrst, 'reload schema';
```

Wait 10 seconds, then rerun tests.

---

### Issue: Foreign key constraint violations

**Cause**: Test expert IDs don't exist in `expert_models` table

**Fix**:
```bash
# Create test experts
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

# Insert test expert
supabase.table('expert_models').insert({
    'expert_id': 'test_conservative_analyzer',
    'name': 'Test Conservative Analyzer',
    'type': 'conservative'
}).execute()

print('✅ Test expert created')
"
```

---

### Issue: Empty database verification

**Cause**: Memories stored but not committed

**Fix**: Check for transaction issues or restart the test script

---

## 📊 What Each Test Does

### 1. Schema Verification Test
- **Checks**: Tables exist and are accessible
- **Duration**: < 1 second
- **Critical**: Yes - all other tests depend on this

### 2. Memory Storage Test
- **Checks**: Can write episodic memories to database
- **Duration**: 1-2 seconds
- **Critical**: Yes - core functionality

### 3. Memory Retrieval Test
- **Checks**: Can query memories by context (e.g., team, game type)
- **Duration**: 1-2 seconds
- **Critical**: Yes - needed for learning

### 4. Lesson Extraction Test
- **Checks**: Can extract meaningful lessons from prediction outcomes
- **Duration**: < 1 second
- **Critical**: Yes - learning mechanism

### 5. Principle Storage Test
- **Checks**: Can store learned principles for reuse
- **Duration**: 1-2 seconds
- **Critical**: Yes - knowledge accumulation

### 6. Full Learning Cycle Test
- **Checks**: Complete workflow from prediction → outcome → memory → lesson
- **Duration**: 2-3 seconds
- **Critical**: Yes - integration test

---

## 🎉 After All Tests Pass

You'll have verified that:

1. ✅ **Schema is correct**: All required columns exist
2. ✅ **Memory storage works**: Experts can store experiences
3. ✅ **Memory retrieval works**: Experts can recall relevant memories
4. ✅ **Lesson extraction works**: Experts learn from outcomes
5. ✅ **Principle storage works**: Experts accumulate knowledge
6. ✅ **Full cycle works**: End-to-end learning is functional

---

## 📚 Next Steps After Testing

### View Stored Memories Directly

```bash
python3 -c "
from supabase import create_client
import os
from dotenv import load_dotenv
load_dotenv()

supabase = create_client(os.getenv('VITE_SUPABASE_URL'), os.getenv('VITE_SUPABASE_ANON_KEY'))

memories = supabase.table('expert_episodic_memories')\
    .select('*')\
    .eq('expert_id', 'conservative_analyzer')\
    .order('created_at', desc=True)\
    .limit(10)\
    .execute()

print(f'Found {len(memories.data)} memories:')
for m in memories.data:
    print(f\"  - {m['emotional_state']}: vividness {m['memory_vividness']:.2f}, game {m['game_id']}\")
"
```

### Compare Learning Curves

```bash
# Run baseline (no memory)
cat /tmp/one_expert_journey.log | grep "Overall Accuracy"

# Run with memory
python3 scripts/supabase_memory_journey.py | grep "Overall Accuracy"

# Compare the two to see if learning improves accuracy over time
```

---

## 🚀 Quick Start TL;DR

```bash
# 1. Reload schema cache (via Supabase Dashboard)
#    SQL Editor → Run: NOTIFY pgrst, 'reload schema';

# 2. Run tests
python3 tests/test_episodic_memory_system.py

# 3. Watch learning journey
python3 scripts/supabase_memory_journey.py

# 4. Verify database
python3 scripts/diagnose_memory_system.py
```

**Total Time**: ~3 minutes

**Result**: Complete transparency into expert learning with episodic memory! 🧠

---

## 📖 Understanding the Output

### Memory Storage Messages

- `✅ Memory stored with satisfaction emotion` → Correct prediction, positive emotion
- `✅ Memory stored with disappointment emotion` → Wrong prediction, negative emotion
- `⚠️  Memory storage failed` → Database error, check logs

### Lesson Extraction Categories

- `confidence_calibration` → Learning about prediction confidence levels
- `home_field_advantage` → Learning about home vs away performance
- `team_matchups` → Learning about specific team pairings
- `weather_impact` → Learning about weather effects
- `upset_detection` → Learning to identify potential upsets

### Memory Vividness Scores

- `0.8-1.0`: **High vividness** - very memorable experience
- `0.5-0.7`: **Moderate vividness** - normal experience
- `0.1-0.4`: **Low vividness** - fading memory

---

**Status**: Ready to test after schema cache reload! 🚀