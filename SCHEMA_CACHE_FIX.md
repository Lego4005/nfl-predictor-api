# 🔧 PostgREST Schema Cache Issue - Solution

## The Problem

After running the SQL migration, PostgREST's schema cache hasn't refreshed yet. This causes:
```
Could not find the 'emotional_state' column of 'expert_episodic_memories' in the schema cache
```

## ✅ Solution: Restart Supabase Database (RECOMMENDED)

This is the most reliable method:

### Step 1: Restart Database
1. Go to: https://supabase.com/dashboard/project/xthjqprcpubinyzupsir
2. Click: **Settings** (left sidebar)
3. Click: **Database**
4. Click: **Restart database** button
5. Wait: ~30 seconds for restart to complete

### Step 2: Run Tests
```bash
bash scripts/run_memory_tests.sh
```

**Expected**: All 6 tests pass (100%)

---

## Alternative: Wait for Cache to Refresh

If you don't want to restart, you can wait:

```bash
# This will retry every few seconds (up to 10 attempts)
bash scripts/wait_for_cache.sh

# If successful, run tests
bash scripts/run_memory_tests.sh
```

⚠️ **Note**: Waiting can take 1-5 minutes and may not always work.

---

## Why This Happens

1. **SQL migration runs** → Columns added to PostgreSQL ✅
2. **NOTIFY command sent** → PostgreSQL receives it ✅
3. **PostgREST receives NOTIFY** → But may be delayed ⏳
4. **PostgREST reloads schema** → Can take 10-60 seconds ⏳
5. **Python client uses PostgREST** → Still sees old schema ❌

**Database restart** forces PostgREST to reload immediately. ✅

---

## How to Verify Fix Worked

```bash
# Quick verification (5 seconds)
scripts/quick_test.sh
```

Should show:
```
2. Testing memory storage...
   ✅ Memory storage works!
```

---

## After Cache is Refreshed

Run the complete test suite:

```bash
bash scripts/run_memory_tests.sh
```

**Expected Results**:
- ✅ Schema Verification: PASS
- ✅ Memory Storage: PASS
- ✅ Memory Retrieval: PASS
- ✅ Lesson Extraction: PASS
- ✅ Principle Storage: PASS
- ✅ Full Learning Cycle: PASS

**Success Rate**: 100% (6/6 tests)

---

## Still Not Working?

### Check 1: Verify SQL Ran Successfully

Run this in Supabase SQL Editor:
```sql
-- Check if column exists
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'expert_episodic_memories'
AND column_name = 'emotional_state';
```

**Should return**: 1 row with 'emotional_state'

### Check 2: Verify Migration Applied

```sql
-- Check table structure
SELECT * FROM expert_episodic_memories LIMIT 0;
```

**Should succeed** with no errors

### Check 3: Force Cache Reload

```sql
-- Run multiple times
NOTIFY pgrst, 'reload schema';
SELECT pg_sleep(5);
NOTIFY pgrst, 'reload schema';
```

Then retry tests after 30 seconds.

---

## Summary

**Fastest Solution**: Restart database (30 seconds)
**Alternative**: Wait for cache (1-5 minutes)
**Last Resort**: Check SQL actually ran

Once cache is refreshed, all tests should pass! 🎉