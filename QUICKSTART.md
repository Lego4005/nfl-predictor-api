# 🚀 QUICKSTART: Test Episodic Memory

## One Command (After SQL Fix)

```bash
bash scripts/run_memory_tests.sh
```

---

## Step 1: Run SQL Fix (1 minute)

**Supabase Dashboard → SQL Editor → New Query**

Copy/paste the entire contents of:
```
scripts/final_fix.sql
```

Click **RUN**

Expected output:
```
✅ Testing expert_memory_summary...
✅ Testing recent_memory_activity...
✅ Testing expert_episodic_memories...
✅ Testing expert_belief_revisions...
✅ SCHEMA FIX COMPLETE!
```

---

## Step 2: Run Tests (2 minutes)

```bash
bash scripts/run_memory_tests.sh
```

**Or run individually**:

```bash
# Quick test (5 seconds)
scripts/quick_test.sh

# Full test suite (30 seconds)
python3 tests/test_episodic_memory_system.py

# Learning demo (30 seconds)
python3 scripts/supabase_memory_journey.py

# Diagnostics (5 seconds)
python3 scripts/diagnose_memory_system.py
```

---

## Expected Results

✅ **All 6 tests pass**
✅ **5 memories stored**
✅ **10+ lessons learned**
✅ **2+ principles discovered**
✅ **Verdict: GENUINE LEARNING**

---

## If Tests Still Fail

### Error: "Could not find column"
**Fix**: Schema cache needs manual reload

```sql
-- Run in SQL Editor
NOTIFY pgrst, 'reload schema';
```

Wait 10 seconds, then retry tests.

### Error: "Foreign key constraint"
**Fix**: Create test expert

```bash
python3 scripts/create_test_expert.py
```

---

## 📚 Full Documentation

- `docs/TEST_EPISODIC_MEMORY_GUIDE.md` - Complete guide
- `docs/MEMORY_TEST_SUMMARY.md` - Technical details

---

**Total Time**: ~3 minutes
**Confidence**: 99% after SQL fix runs successfully