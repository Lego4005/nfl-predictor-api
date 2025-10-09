# Claude Code Configuration - NFL Predictor API

## 🚨 CRITICAL: PACKAGE MANAGER - USE NPM

**THIS PROJECT USES NPM, NOT YARN!**

- ALWAYS use `npm` commands, NEVER `yarn`
- Use `npm install` for dependencies
- Use `npm run` for scripts
- The project has a package-lock.json file that must be kept in sync

## 🔍 VECTORCODE INTEGRATION - PRIMARY TOOL FOR CODE & DOCUMENTATION

**VECTORCODE IS YOUR PRIMARY SEARCH AND DISCOVERY TOOL**:

1. **ALWAYS use VectorCode first** before starting any coding task
2. **Search existing code patterns** before implementing new features
3. **Find documentation** using semantic search across all markdown files in `.qoder/repowiki/en/content/`
4. **Discover related implementations** across the entire codebase
5. **Use domain-specific queries** for NFL Predictor features

### 🚨 CRITICAL: VECTORCODE TOKEN MANAGEMENT - PREVENT OVERFLOW

**TOKEN OVERFLOW EMERGENCY PROTOCOL**:

If VectorCode queries exceed 25k tokens (you get 29420+ tokens), follow this protocol:

1. **IMMEDIATELY STOP** current search approach
2. **Switch to 3-Phase Progressive Search** methodology
3. **Use domain-specific patterns** instead of vague queries
4. **Limit results to 1-2 per phase** maximum

### 🎯 3-PHASE PROGRESSIVE SEARCH METHODOLOGY

**Phase 1: Exploration (2-3 results max)**
```bash
# Purpose: Understand what exists in the codebase
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council voting"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing learning loop"
# Analyze results → Plan Phase 2
```

**Phase 2: Targeted Search (3 results max)**
```bash
# Purpose: Focus on specific areas discovered in Phase 1
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 3 --query "weighted consensus voting mechanism"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 3 --query "expert performance tracking metrics"
# Identify specific implementations → Plan Phase 3
```

**Phase 3: Deep Dive (1-2 results max)**
```bash
# Purpose: Get exact implementation details
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "merit based expert rotation algorithm"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"
# Get actionable code details
```

### ⚡ SAFE TOKEN LIMITS

**Maximum Safe Limits:**
- **Phase 1**: 2-3 results = ~3,000 tokens
- **Phase 2**: 3 results = ~4,000 tokens  
- **Phase 3**: 1-2 results = ~2,000 tokens
- **Total per search session**: ~9,000 tokens maximum

**Emergency Procedures:**
- Token overflow → Reduce to `-n 1`
- Slow queries → Use specific domain terms
- Irrelevant results → Add more context to query

### 🎯 VectorCode Usage Patterns

**Before ANY coding work:**

```bash
# ✅ GOOD - Domain-specific, limited results
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council weighted voting"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing S3L performance monitoring"
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "SportsData.io connector caching"

# ❌ BAD - Vague, too many results
query_vectorcode -n 10 --query "function"
query_vectorcode -n 8 --query "data processing"
query_vectorcode -n 15 --query "api"
```

### 🏈 NFL Predictor API Specific Queries

**Domain-specific searches (ALWAYS use these patterns):**

- `"AI expert council weighted voting consensus"` - Find voting algorithms
- `"self-healing learning loop S3L monitoring"` - Find S³L system
- `"merit based expert rotation performance"` - Find expert management
- `"SportsData.io connector rate limiting"` - Find API integrations
- `"WebSocket real-time prediction updates"` - Find live update system
- `"personality driven expert models"` - Find expert personalities
- `"comprehensive prediction categories"` - Find prediction types

**Architecture searches:**

- `"Supabase PostgreSQL schema design"` - Find database patterns
- `"Trigger.dev workflow orchestration"` - Find task automation
- `"FastAPI backend endpoints"` - Find API patterns
- `"OpenRouter AI integration"` - Find AI model usage

**Documentation searches:**

- `"Project Overview architecture"` - Find system design docs
- `"Expert System Architecture council"` - Find expert system docs
- `"Self-Healing System adaptation"` - Find S³L documentation
- `"Database Schema Design migrations"` - Find schema docs

### 🚨 QUERY FORMULATION RULES

**DO:**
- Use 2-4 specific keywords per query
- Include domain context ("expert council", "S3L", "WebSocket")
- Limit results with `-n 1` to `-n 3`
- Start narrow, expand if needed
- Use progressive search methodology

**DON'T:**
- Use single generic words ("function", "data", "api")
- Search without context
- Use more than `-n 5` results
- Make vague queries like "error" or "system"
- Skip domain-specific terms

### 📋 VECTORCODE QUERY CHECKLIST

Before ANY VectorCode query, verify:

- [ ] Query includes domain-specific terms
- [ ] Result count is `-n 3` or less  
- [ ] Query has 2-4 specific keywords
- [ ] Following 3-phase methodology
- [ ] Previous phase results analyzed
- [ ] Emergency token limits respected

## 🧠 CLAUDE FLOW MEMORY INTEGRATION

**Pre-stored Memory Keys:**

```bash
# Retrieve project context
npx claude-flow@alpha memory query "nfl-predictor/overview"
npx claude-flow@alpha memory query "nfl-predictor/tech-stack"
npx claude-flow@alpha memory query "nfl-predictor/expert-council"
npx claude-flow@alpha memory query "nfl-predictor/s3l-system"
npx claude-flow@alpha memory query "nfl-predictor/real-time-pipeline"
```

**Memory Contents:**

- **nfl-predictor/overview**: 15 AI expert council, S³L, real-time predictions, 375+ predictions/game
- **nfl-predictor/tech-stack**: OpenRouter, Supabase, Trigger.dev, SportsData.io, Redis, WebSocket
- **nfl-predictor/expert-council**: Weighted voting (accuracy 40%, recent 30%, consistency 20%, confidence 10%)
- **nfl-predictor/s3l-system**: Hourly monitoring, 70% accuracy threshold, automated rotation
- **nfl-predictor/real-time-pipeline**: WebSocket updates, intelligent caching, dynamic predictions

## 📁 PROJECT STRUCTURE

**Key Directories:**

- `.qoder/repowiki/en/content/` - **58 comprehensive documentation files**
  - `Project Overview.md` - System architecture and core features
  - `Expert System Architecture/` - AI council and voting system
  - `Self-Healing System/` - S³L monitoring and adaptation
  - `Database Schema Design/` - Supabase schema and migrations
  - `External Integrations/` - SportsData.io, ESPN, Odds API
  - `Real-time Features/` - WebSocket and live updates
  - `Machine Learning Models/` - Expert models and predictions
  - `API Reference/` - Endpoint documentation

- `src/` - Source code
  - `src/ml/` - Machine learning models and expert system
  - `src/services/` - Data connectors and services
  - `src/api/` - API endpoints and WebSocket handlers
  - `src/database/` - Database migrations and schema

- `ai_expert_system_api.py` - Main expert system implementation
- `test_ai_council_voting.py` - Expert voting tests
- `test_expert_competition_framework.py` - Competition framework tests

## 🎯 DEVELOPMENT WORKFLOW

### 1. Before Starting Any Task

```bash
# Step 1: Query VectorCode for relevant code
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "[specific feature you're working on]"

# Step 2: Retrieve Claude Flow memory
npx claude-flow@alpha memory query "nfl-predictor/[relevant-area]"

# Step 3: Check documentation
cat .qoder/repowiki/en/content/[relevant-doc].md
```

### 2. During Development

- Use VectorCode to find similar implementations
- Reference Claude Flow memory for architecture decisions
- Follow existing patterns from documentation
- Test with real data from SportsData.io

### 3. After Implementation

- Update documentation if architecture changes
- Store new patterns in Claude Flow memory
- Verify with existing tests

## 🚀 QUICK REFERENCE

### Most Common VectorCode Queries

```bash
# Expert Council System
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council weighted voting consensus"

# S³L System
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing learning loop performance monitoring"

# Real-time Predictions
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"

# Data Integration
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "SportsData.io connector intelligent caching"
```

### Documentation Quick Access

```bash
# System Overview
cat .qoder/repowiki/en/content/Project\ Overview.md

# Expert System
cat .qoder/repowiki/en/content/Expert\ System\ Architecture/*.md

# S³L System
cat .qoder/repowiki/en/content/Self-Healing\ System/*.md

# Database Schema
cat .qoder/repowiki/en/content/Database\ Schema\ Design/*.md
```

## ✅ SETUP VERIFICATION

**VectorCode Configuration:**
- ✅ `.claude-flow-vector.json` exists in project root
- ✅ Project indexed: `/home/iris/code/experimental/nfl-predictor-api`
- ✅ 58 documentation files in `.qoder/repowiki/en/content/`

**Claude Flow Memory:**
- ✅ 5 memory entries stored under `nfl-predictor/*`
- ✅ Overview, tech-stack, expert-council, s3l-system, real-time-pipeline

**Ready for Development:** 🏈🤖

---

**Remember:** Always use VectorCode first, limit queries to 3 results max, and leverage Claude Flow memory for context!
