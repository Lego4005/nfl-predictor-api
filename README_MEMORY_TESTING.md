# 🚀 Quick Start: Test Episodic Memory System

## TL;DR (3 Minutes)

```bash
# 1. Reload schema cache (via Supabase Dashboard SQL Editor)
#    Run: NOTIFY pgrst, 'reload schema';

# 2. Run all tests
bash scripts/run_memory_tests.sh
```

That's it! The script will:
- ✅ Verify database schema
- ✅ Create test expert
- ✅ Run 6 comprehensive tests
- ✅ Demonstrate learning journey
- ✅ Validate system diagnostics
- ✅ Generate final report

---

## 📋 Manual Testing (Step-by-Step)

### Step 1: Reload Schema Cache (REQUIRED)

**Option A - SQL Editor (Recommended)**:
```sql
NOTIFY pgrst, 'reload schema';
```

**Option B - Dashboard**:
Settings → Database → Restart database

---

### Step 2: Verify Schema

```bash
python3 scripts/check_database_schema.py
```

Expected: `✅ All tables exist with correct columns`

---

### Step 3: Create Test Expert

```bash
python3 scripts/create_test_expert.py
```

Expected: `✅ Test expert created successfully`

---

### Step 4: Run Test Suite

```bash
python3 tests/test_episodic_memory_system.py
```

Expected: `🎉 ALL TESTS PASSED! (6/6)`

Tests:
1. ✅ Schema verification
2. ✅ Memory storage
3. ✅ Memory retrieval
4. ✅ Lesson extraction
5. ✅ Principle storage
6. ✅ Full learning cycle

---

### Step 5: Watch Learning Journey

```bash
python3 scripts/supabase_memory_journey.py
```

Expected output:
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
   Learned 2 lessons

💾 STORING EPISODIC MEMORY...
   ✅ Memory stored with satisfaction emotion

[... continues for 5 games ...]

🏆 FINAL SUMMARY
   Total Games: 5
   Episodic Memories Stored: 5 ✅
   Lessons Learned: 10 ✅

🎉 SUCCESS! Memory system is fully functional!
```

---

### Step 6: Run Diagnostics

```bash
python3 scripts/diagnose_memory_system.py
```

Expected:
```
TEST 1: Episodic Memories
✅ Found 5 episodic memories

TEST 2: Learned Principles
✅ Found 2+ active learned principles

🎯 VERDICT: ✅ HYPOTHESIS 1: GENUINE LEARNING
```

---

## 🐛 Troubleshooting

### "Could not find column" errors
**Fix**: Reload schema cache
```sql
NOTIFY pgrst, 'reload schema';
```

### "Foreign key constraint" errors
**Fix**: Create test expert
```bash
python3 scripts/create_test_expert.py
```

### "Connection refused" errors
**Fix**: Check `.env` file
```bash
grep SUPABASE .env
```

---

## 📚 Documentation

- **Complete Guide**: `docs/TEST_EPISODIC_MEMORY_GUIDE.md`
- **Test Summary**: `docs/MEMORY_TEST_SUMMARY.md`
- **Audit Report**: `docs/EPISODIC_MEMORY_AUDIT_REPORT.md`

---

## ✅ Success Criteria

Tests PASS if you see:

1. ✅ 6/6 tests passed in test suite
2. ✅ "Memory stored" messages in journey demo
3. ✅ "X memories in database" where X > 0
4. ✅ "GENUINE LEARNING" verdict in diagnostics

---

## 🎯 What You're Testing

The episodic memory system enables experts to:

1. **Store experiences** - Save game outcomes with emotional context
2. **Retrieve memories** - Recall relevant past experiences
3. **Extract lessons** - Learn from prediction outcomes
4. **Build principles** - Accumulate reusable knowledge patterns
5. **Improve over time** - Get better with more experience

---

**Ready?** Run `bash scripts/run_memory_tests.sh` to start! 🚀