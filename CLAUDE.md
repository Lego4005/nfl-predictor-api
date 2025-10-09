# Claude Code Configuration - SPARC Development Environment

## 🚨 CRITICAL: CONCURRENT EXECUTION & FILE MANAGEMENT

**ABSOLUTE RULES**:
1. ALL operations MUST be concurrent/parallel in a single message
2. **NEVER save working files, text/mds and tests to the root folder**
3. ALWAYS organize files in appropriate subdirectories
4. **USE CLAUDE CODE'S TASK TOOL** for spawning agents concurrently, not just MCP

### ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**
- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

### 🎯 CRITICAL: Claude Code Task Tool for Agent Execution

**Claude Code's Task tool is the PRIMARY way to spawn agents:**
```javascript
// ✅ CORRECT: Use Claude Code's Task tool for parallel agent execution
[Single Message]:
  Task("Research agent", "Analyze requirements and patterns...", "researcher")
  Task("Coder agent", "Implement core features...", "coder")
  Task("Tester agent", "Create comprehensive tests...", "tester")
  Task("Reviewer agent", "Review code quality...", "reviewer")
  Task("Architect agent", "Design system architecture...", "system-architect")
```

**MCP tools are ONLY for coordination setup:**
- `mcp__claude-flow__swarm_init` - Initialize coordination topology
- `mcp__claude-flow__agent_spawn` - Define agent types for coordination
- `mcp__claude-flow__task_orchestrate` - Orchestrate high-level workflows

### 📁 File Organization Rules

**NEVER save to root folder. Use these directories:**
- `/src` - Source code files
- `/tests` - Test files
- `/docs` - Documentation and markdown files
- `/config` - Configuration files
- `/scripts` - Utility scripts
- `/examples` - Example code

## Project Overview

This project uses SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) methodology with Claude-Flow orchestration for systematic Test-Driven Development.

## SPARC Commands

### Core Commands
- `npx claude-flow sparc modes` - List available modes
- `npx claude-flow sparc run <mode> "<task>"` - Execute specific mode
- `npx claude-flow sparc tdd "<feature>"` - Run complete TDD workflow
- `npx claude-flow sparc info <mode>` - Get mode details

### Batchtools Commands
- `npx claude-flow sparc batch <modes> "<task>"` - Parallel execution
- `npx claude-flow sparc pipeline "<task>"` - Full pipeline processing
- `npx claude-flow sparc concurrent <mode> "<tasks-file>"` - Multi-task processing

### Build Commands
- `npm run build` - Build project
- `npm run test` - Run tests
- `npm run lint` - Linting
- `npm run typecheck` - Type checking

## SPARC Workflow Phases

1. **Specification** - Requirements analysis (`sparc run spec-pseudocode`)
2. **Pseudocode** - Algorithm design (`sparc run spec-pseudocode`)
3. **Architecture** - System design (`sparc run architect`)
4. **Refinement** - TDD implementation (`sparc tdd`)
5. **Completion** - Integration (`sparc run integration`)

## Code Style & Best Practices

- **Modular Design**: Files under 500 lines
- **Environment Safety**: Never hardcode secrets
- **Test-First**: Write tests before implementation
- **Clean Architecture**: Separate concerns
- **Documentation**: Keep updated

## 🚀 Available Agents (54 Total)

### Core Development
`coder`, `reviewer`, `tester`, `planner`, `researcher`

### Swarm Coordination
`hierarchical-coordinator`, `mesh-coordinator`, `adaptive-coordinator`, `collective-intelligence-coordinator`, `swarm-memory-manager`

### Consensus & Distributed
`byzantine-coordinator`, `raft-manager`, `gossip-coordinator`, `consensus-builder`, `crdt-synchronizer`, `quorum-manager`, `security-manager`

### Performance & Optimization
`perf-analyzer`, `performance-benchmarker`, `task-orchestrator`, `memory-coordinator`, `smart-agent`

### GitHub & Repository
`github-modes`, `pr-manager`, `code-review-swarm`, `issue-tracker`, `release-manager`, `workflow-automation`, `project-board-sync`, `repo-architect`, `multi-repo-swarm`

### SPARC Methodology
`sparc-coord`, `sparc-coder`, `specification`, `pseudocode`, `architecture`, `refinement`

### Specialized Development
`backend-dev`, `mobile-dev`, `ml-developer`, `cicd-engineer`, `api-docs`, `system-architect`, `code-analyzer`, `base-template-generator`

### Testing & Validation
`tdd-london-swarm`, `production-validator`

### Migration & Planning
`migration-planner`, `swarm-init`

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION:
- **Task tool**: Spawn and run agents concurrently for actual work
- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE:
- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

## 🚀 Quick Setup

```bash
# Add MCP servers (Claude Flow required, others optional)
claude mcp add claude-flow npx claude-flow@alpha mcp start
claude mcp add ruv-swarm npx ruv-swarm mcp start  # Optional: Enhanced coordination
claude mcp add flow-nexus npx flow-nexus@latest mcp start  # Optional: Cloud features
```

## MCP Tool Categories

### Coordination
`swarm_init`, `agent_spawn`, `task_orchestrate`

### Monitoring
`swarm_status`, `agent_list`, `agent_metrics`, `task_status`, `task_results`

### Memory & Neural
`memory_usage`, `neural_status`, `neural_train`, `neural_patterns`

### GitHub Integration
`github_swarm`, `repo_analyze`, `pr_enhance`, `issue_triage`, `code_review`

### System
`benchmark_run`, `features_detect`, `swarm_monitor`

### Flow-Nexus MCP Tools (Optional Advanced Features)
Flow-Nexus extends MCP capabilities with 70+ cloud-based orchestration tools:

**Key MCP Tool Categories:**
- **Swarm & Agents**: `swarm_init`, `swarm_scale`, `agent_spawn`, `task_orchestrate`
- **Sandboxes**: `sandbox_create`, `sandbox_execute`, `sandbox_upload` (cloud execution)
- **Templates**: `template_list`, `template_deploy` (pre-built project templates)
- **Neural AI**: `neural_train`, `neural_patterns`, `seraphina_chat` (AI assistant)
- **GitHub**: `github_repo_analyze`, `github_pr_manage` (repository management)
- **Real-time**: `execution_stream_subscribe`, `realtime_subscribe` (live monitoring)
- **Storage**: `storage_upload`, `storage_list` (cloud file management)

**Authentication Required:**
- Register: `mcp__flow-nexus__user_register` or `npx flow-nexus@latest register`
- Login: `mcp__flow-nexus__user_login` or `npx flow-nexus@latest login`
- Access 70+ specialized MCP tools for advanced orchestration

## 🚀 Agent Execution Flow with Claude Code

### The Correct Pattern:

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development:

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with Express. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create React UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design PostgreSQL schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")
  
  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }
  
  // All file operations together
  Write "backend/server.js"
  Write "frontend/App.jsx"
  Write "database/schema.sql"
```

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST:

**1️⃣ BEFORE Work:**
```bash
npx claude-flow@alpha hooks pre-task --description "[task]"
npx claude-flow@alpha hooks session-restore --session-id "swarm-[id]"
```

**2️⃣ DURING Work:**
```bash
npx claude-flow@alpha hooks post-edit --file "[file]" --memory-key "swarm/[agent]/[step]"
npx claude-flow@alpha hooks notify --message "[what was done]"
```

**3️⃣ AFTER Work:**
```bash
npx claude-flow@alpha hooks post-task --task-id "[task]"
npx claude-flow@alpha hooks session-end --export-metrics true
```

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

```javascript
// Step 1: MCP tools set up coordination (optional, for complex tasks)
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }

// Step 2: Claude Code Task tool spawns ACTUAL agents that do the work
[Single Message - Parallel Agent Execution]:
  // Claude Code's Task tool spawns real agents concurrently
  Task("Research agent", "Analyze API requirements and best practices. Check memory for prior decisions.", "researcher")
  Task("Coder agent", "Implement REST endpoints with authentication. Coordinate via hooks.", "coder")
  Task("Database agent", "Design and implement database schema. Store decisions in memory.", "code-analyzer")
  Task("Tester agent", "Create comprehensive test suite with 90% coverage.", "tester")
  Task("Reviewer agent", "Review code quality and security. Document findings.", "reviewer")
  
  // Batch ALL todos in ONE call
  TodoWrite { todos: [
    {id: "1", content: "Research API patterns", status: "in_progress", priority: "high"},
    {id: "2", content: "Design database schema", status: "in_progress", priority: "high"},
    {id: "3", content: "Implement authentication", status: "pending", priority: "high"},
    {id: "4", content: "Build REST endpoints", status: "pending", priority: "high"},
    {id: "5", content: "Write unit tests", status: "pending", priority: "medium"},
    {id: "6", content: "Integration tests", status: "pending", priority: "medium"},
    {id: "7", content: "API documentation", status: "pending", priority: "low"},
    {id: "8", content: "Performance optimization", status: "pending", priority: "low"}
  ]}
  
  // Parallel file operations
  Bash "mkdir -p app/{src,tests,docs,config}"
  Write "app/package.json"
  Write "app/src/server.js"
  Write "app/tests/server.test.js"
  Write "app/docs/API.md"
```

### ❌ WRONG (Multiple Messages):
```javascript
Message 1: mcp__claude-flow__swarm_init
Message 2: Task("agent 1")
Message 3: TodoWrite { todos: [single todo] }
Message 4: Write "file.js"
// This breaks parallel coordination!
```

## Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

## Hooks Integration

### Pre-Operation
- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation
- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management
- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

## Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

## Integration Tips

1. Start with basic swarm init
2. Scale agents gradually
3. Use memory for context
4. Monitor progress regularly
5. Train patterns from success
6. Enable hooks automation
7. Use GitHub tools first

## Support

- Documentation: https://github.com/ruvnet/claude-flow
- Issues: https://github.com/ruvnet/claude-flow/issues
- Flow-Nexus Platform: https://flow-nexus.ruv.io (registration required for cloud features)

---

Remember: **Claude Flow coordinates, Claude Code creates!**

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.
Never save working files, text/mds and tests to the root folder.
- check with playwright every time after you make the changes and think your done
- when using playwright check console and if im aksing about colors or gradient you need to use advanced playwright tools to verify
---

## 🔍 VECTORCODE INTEGRATION - PRIMARY TOOL FOR NFL PREDICTOR API

**VECTORCODE IS YOUR PRIMARY SEARCH AND DISCOVERY TOOL**:

1. **ALWAYS use VectorCode first** before starting any coding task
2. **Search existing code patterns** before implementing new features
3. **Find documentation** using semantic search across `.qoder/repowiki/en/content/` (58 docs)
4. **Discover related implementations** across the entire codebase
5. **Use domain-specific queries** for NFL Predictor features

### 🚨 CRITICAL: VECTORCODE TOKEN MANAGEMENT - PREVENT OVERFLOW

**TOKEN OVERFLOW EMERGENCY PROTOCOL**:

If VectorCode queries exceed 25k tokens, follow this protocol:

1. **IMMEDIATELY STOP** current search approach
2. **Switch to 3-Phase Progressive Search** methodology
3. **Use domain-specific patterns** instead of vague queries
4. **Limit results to 1-2 per phase** maximum

### 🎯 3-PHASE PROGRESSIVE SEARCH METHODOLOGY

**Phase 1: Exploration (2-3 results max)**
```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council voting"
```

**Phase 2: Targeted Search (3 results max)**
```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 3 --query "weighted consensus voting mechanism"
```

**Phase 3: Deep Dive (1-2 results max)**
```bash
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "merit based expert rotation algorithm"
```

### ⚡ SAFE TOKEN LIMITS

- **Phase 1**: 2-3 results = ~3,000 tokens
- **Phase 2**: 3 results = ~4,000 tokens  
- **Phase 3**: 1-2 results = ~2,000 tokens
- **Total per session**: ~9,000 tokens maximum

### 🏈 NFL Predictor API Specific Queries

**Domain-specific searches (ALWAYS use these patterns):**

```bash
# Expert Council System
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "AI expert council weighted voting consensus"

# S³L (Self-Healing Learning Loop)
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing learning loop S3L monitoring"

# Real-time Predictions
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"

# Data Integration
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "SportsData.io connector intelligent caching"

# Expert Performance
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "merit based expert rotation performance"

# Prediction Categories
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "comprehensive prediction categories 375"
```

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

### �� VECTORCODE QUERY CHECKLIST

Before ANY VectorCode query, verify:

- [ ] Query includes domain-specific terms
- [ ] Result count is `-n 3` or less  
- [ ] Query has 2-4 specific keywords
- [ ] Following 3-phase methodology
- [ ] Emergency token limits respected

## 🧠 CLAUDE FLOW MEMORY - NFL PREDICTOR API

**Pre-stored Memory Keys (retrieve with `npx claude-flow@alpha memory query`):**

```bash
# System Overview
npx claude-flow@alpha memory query "nfl-predictor/overview"
# → 15 AI expert council, S³L, real-time predictions, 375+ predictions/game

# Technology Stack
npx claude-flow@alpha memory query "nfl-predictor/tech-stack"
# → OpenRouter, Supabase, Trigger.dev, SportsData.io, Redis, WebSocket

# Expert Council Architecture
npx claude-flow@alpha memory query "nfl-predictor/expert-council"
# → Weighted voting: accuracy 40%, recent 30%, consistency 20%, confidence 10%

# Self-Healing System
npx claude-flow@alpha memory query "nfl-predictor/s3l-system"
# → Hourly monitoring, 70% accuracy threshold, automated rotation

# Real-time Pipeline
npx claude-flow@alpha memory query "nfl-predictor/real-time-pipeline"
# → WebSocket updates, intelligent caching, dynamic predictions
```

## 📁 NFL PREDICTOR PROJECT STRUCTURE

**Key Documentation (58 files in `.qoder/repowiki/en/content/`):**

- `Project Overview.md` - System architecture, 15 AI experts, S³L
- `Expert System Architecture/` - AI council, voting, competition
- `Self-Healing System/` - S³L monitoring, adaptation triggers
- `Database Schema Design/` - Supabase schema, migrations
- `External Integrations/` - SportsData.io, ESPN, Odds API
- `Real-time Features/` - WebSocket, live updates
- `Machine Learning Models/` - Expert models, predictions
- `API Reference/` - Endpoint documentation

**Key Source Files:**

- `ai_expert_system_api.py` - Main expert system implementation
- `src/ml/` - Machine learning models and expert system
- `src/services/` - Data connectors (SportsData.io, etc.)
- `src/api/` - API endpoints and WebSocket handlers
- `src/database/` - Database migrations and schema

## 🎯 NFL PREDICTOR DEVELOPMENT WORKFLOW

### 1. Before Starting Any Task

```bash
# Step 1: Query VectorCode for relevant code
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "[specific feature]"

# Step 2: Retrieve Claude Flow memory
npx claude-flow@alpha memory query "nfl-predictor/[area]"

# Step 3: Check documentation
cat .qoder/repowiki/en/content/[relevant-doc].md
```

### 2. Common Development Patterns

**Working with Expert Council:**
```bash
# Find voting implementation
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "expert council weighted voting consensus"

# Check architecture
cat .qoder/repowiki/en/content/Expert\ System\ Architecture/*.md
```

**Working with S³L System:**
```bash
# Find monitoring code
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "self-healing learning loop performance monitoring"

# Check S³L docs
cat .qoder/repowiki/en/content/Self-Healing\ System/*.md
```

**Working with Real-time Features:**
```bash
# Find WebSocket implementation
query_vectorcode --project-root /home/iris/code/experimental/nfl-predictor-api \
  -n 2 --query "WebSocket real-time prediction updates"

# Check real-time docs
cat .qoder/repowiki/en/content/Real-time\ Features/*.md
```

## ✅ VECTORCODE SETUP VERIFICATION

**Configuration:**
- ✅ `.claude-flow-vector.json` exists in project root
- ✅ Project indexed: `/home/iris/code/experimental/nfl-predictor-api`
- ✅ 58 documentation files in `.qoder/repowiki/en/content/`

**Claude Flow Memory:**
- ✅ 5 memory entries: overview, tech-stack, expert-council, s3l-system, real-time-pipeline

**VectorCode Settings:**
- Query limit: 3 per task
- Context window: 2000 tokens
- Cache TTL: 1 hour
- Redis caching enabled

---

**🏈 NFL Predictor API is ready for intelligent development with VectorCode + Claude Flow!**
