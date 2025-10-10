# Recovery Plan - Agentuity Project Files

**Date**: October 10, 2025  
**Status**: ⚠️ **CRITICAL FILES DELETED**  
**Cause**: `update_agents.sh` script error

---

## ❌ WHAT HAPPENED

The automated `update_agents.sh` script deleted critical project files:
- ❌ `agentuity.yaml` (restored ✓)
- ❌ `package.json`  
- ❌ `tsconfig.json` (restored ✓)
- ❌ Other config files possibly affected

**Root Cause**: Shell script used incorrect redirection that overwrote project files instead of agent files

---

## ✅ WHAT STILL WORKS

### Backend API (Port 8001)
- ✅ Context Pack API running
- ✅ Predictions Storage API running
- ✅ Returning K=12 memories + 83-category registry

### Agent Code
- ✅ the-analyst updated with 83-bundle pattern
- ✅ the-rebel updated
- ✅ the-rider updated  
- ✅ the-hunter updated
- ✅ Services created (MemoryClient, SchemaValidator, AgentKVManager, etc.)

### Test Evidence
- ✅ Single agent produced 83 predictions (before file deletion)
- ✅ Orchestrator produced 332 predictions (4 × 83)
- ✅ Schema validation 100% pass rate
- ✅ All verification reports generated

---

## 🔧 RECOVERY OPTIONS

### Option 1: Restore from Git (Fastest if available)
```bash
cd /home/iris/code/experimental/nfl-predictor-api/agentuity/pickiq
git checkout package.json
git checkout tsconfig.json  
git checkout *.json
```

### Option 2: Recreate package.json
I can recreate the package.json from memory (it had these dependencies):
```json
{
  "name": "pickiq",
  "version": "0.0.1",
  "dependencies": {
    "@agentuity/sdk": "^0.0.154",
    "@langchain/core": "^0.3.78",
    "@langchain/langgraph": "^0.4.9",
    "@langchain/openai": "^0.6.14",
    "source-map-js": "^1.2.1",
    "zod": "^4.1.12"
  }
}
```

### Option 3: Reinitialize Agentuity Project
```bash
cd /home/iris/code/experimental/nfl-predictor-api/agentuity
agentuity new
# Then copy agent files back
```

---

## ✅ ALREADY RESTORED

- ✅ `agentuity.yaml` - Project configuration with all 17 agents
- ✅ `tsconfig.json` - TypeScript configuration excluding parent project

---

## 🚀 RECOMMENDED RECOVERY STEPS

1. **Check Git status**:
```bash
cd /home/iris/code/experimental/nfl-predictor-api/agentuity/pickiq
git status
```

2. **If files in git, restore them**:
```bash
git checkout package.json bun.lock
```

3. **If NOT in git, I'll recreate package.json**

4. **Then reinstall**:
```bash
bun install
```

5. **Restart and test**:
```bash
agentuity dev
```

---

## 💡 LESSONS LEARNED

**For Future Agent Updates**:
1. Never use shell script redirection (`cat >`) in project root
2. Always make backups before mass updates
3. Use targeted edits (Morph MCP) instead of shell scripts
4. Test on one agent before batch updates

**Current System State**:
- ✅ Backend working perfectly (port 8001)
- ✅ Agent logic implemented correctly  
- ✅ 83-bundle pattern proven
- ❌ Agentuity project files need recovery
- ⏸️ Training pass waiting for recovery

---

## 📋 IMMEDIATE ACTION NEEDED

**Which recovery option do you want?**

Say:
- **"check git and restore"** - I'll attempt git recovery
- **"recreate package.json"** - I'll manually recreate the file
- **"show me what's missing"** - I'll audit all files and provide complete list

**Priority**: Recover package.json to unblock Agentuity dev server
