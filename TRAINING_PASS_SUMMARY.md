# 2020-2023 Training Pass - Current Status

**Date**: October 10, 2025  
**Status**: ⏸️ **PAUSED - TypeScript Build Issue**  
**Run ID**: run_2025_pilot4_training

---

## ⚠️ CURRENT BLOCKER

**Issue**: Agentuity TypeScript compiler picking up parent project files  
**Error**: TypeScript errors in `../../src/components/`, `../../src/data/`, `../../src/utils/`

**Root Cause**: Agentuity build process scanning outside `agentuity/pickiq/src/agents/` folder

**Solution Needed**: Update `tsconfig.json` or Agentuity build config to exclude parent project

---

## ✅ WHAT'S READY

### System Components (All Working)
- ✅ Backend Context API (port 8001) - Running
- ✅ Backend Predictions API (port 8001) - Running
- ✅ 4 Agents wired with 83-bundle pattern
- ✅ Schema validation (100% pass rate)
- ✅ pgvector verified (p95=20.1ms)
- ✅ Neo4j verified (1332 edges)
- ✅ Training script created (`scripts/seed_ingest_runner.py`)

### Successful Tests (Before Build Issue)
```json
Single Agent: {
  "assertions": 83,
  "ctxK": 12,
  "schemaOk": true,
  "iterations": 0
}

Orchestrator: {
  "total_predictions": 332,  // 4 × 83
  "successful_experts": 4
}
```

---

## 🔧 WORKAROUND OPTIONS

### Option 1: Fix TypeScript Config (Recommended)
Update `agentuity/pickiq/tsconfig.json` to exclude parent directories:
```json
{
  "exclude": ["../../src/**", "../../node_modules/**"]
}
```

### Option 2: Run Agents Standalone
Instead of `agentuity dev`, run the compiled agents directly:
```bash
cd agentuity/pickiq
bun run .agentuity/index.js
```

### Option 3: Use Existing Training Scripts
The system already has training scripts that bypass Agentuity:
```bash
python scripts/train_models.py --seasons 2020-2023
python scripts/prove_learning_15_experts.py
```

---

## 🚀 RECOMMENDED NEXT STEPS

### Immediate (Unblock Training)
1. Fix `tsconfig.json` to exclude parent project
2. Restart Agentuity dev server
3. Run training pass
4. Monitor memory corpus growth

### Alternative (Use Existing Infrastructure)
1. Run backend-only training with existing scripts
2. Use `train_models.py` or `prove_learning_15_experts.py`
3. Then test Agentuity agents against trained memories

---

## 📊 TRAINING PASS PARAMETERS

**Command** (once unblocked):
```bash
python scripts/seed_ingest_runner.py \
  --run-id run_2025_pilot4_training \
  --seasons 2020-2023 \
  --experts the-analyst,the-rebel,the-rider,the-hunter \
  --stakes 0 \
  --reflections off
```

**Expected Outcome**:
- Process ~1000 games (2020-2023 seasons × ~256 games each)
- Generate 4000 expert experiences (1000 games × 4 experts)
- Fill pgvector with episodic memories
- Populate calibration buckets
- Embedding coverage >80%

**Estimated Time**: 30-60 minutes at 2-3 games/minute

---

## ✅ CURRENT SYSTEM STATUS

**Backend Services**: 🟢 Running  
**Agent Logic**: 🟢 83-Bundle Working  
**Schema Validation**: 🟢 100% Pass Rate  
**Build Process**: 🔴 TypeScript Config Issue  

**Blocker**: TypeScript build scanning parent project  
**Impact**: Can't start Agentuity dev server  
**Severity**: Medium (workarounds available)  

---

**Next Command**: Fix tsconfig or use existing training scripts

Say:
- **"fix the typescript config"** to update tsconfig.json
- **"use existing training scripts"** to bypass Agentuity for training
- **"show me the alternatives"** to see other training options
