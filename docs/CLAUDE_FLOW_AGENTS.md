# Claude Flow Agents & MCP Tools - Microbiome Platform

**Complete guide for agent orchestration and swarm coordination**

> **Quick Reference**: See [CLAUDE.md](../CLAUDE.md) for essential workflow  
> **Related**: [VECTORCODE_GUIDE.md](./VECTORCODE_GUIDE.md) | [SPARC_METHODOLOGY.md](./SPARC_METHODOLOGY.md)

---

## 🚀 Available Agents (54 Total)

### Core Development Agents

**Primary agents for day-to-day development:**

- `coder` - General-purpose coding agent
- `reviewer` - Code review and quality assurance
- `tester` - Test creation and execution
- `planner` - Task planning and breakdown
- `researcher` - Information gathering and analysis

### Swarm Coordination Agents

**Agents for managing multi-agent workflows:**

- `hierarchical-coordinator` - Tree-based coordination
- `mesh-coordinator` - Peer-to-peer coordination
- `adaptive-coordinator` - Dynamic coordination
- `collective-intelligence-coordinator` - Swarm intelligence
- `swarm-memory-manager` - Shared memory management

### Consensus & Distributed Agents

**Agents for distributed decision-making:**

- `byzantine-coordinator` - Byzantine fault tolerance
- `raft-manager` - Raft consensus protocol
- `gossip-coordinator` - Gossip protocol coordination
- `consensus-builder` - Consensus mechanism
- `crdt-synchronizer` - CRDT synchronization
- `quorum-manager` - Quorum-based decisions
- `security-manager` - Security coordination

### Performance & Optimization Agents

**Agents for performance analysis:**

- `perf-analyzer` - Performance analysis
- `performance-benchmarker` - Benchmarking
- `task-orchestrator` - Task orchestration
- `memory-coordinator` - Memory optimization
- `smart-agent` - Intelligent agent

### GitHub & Repository Agents

**Agents for GitHub integration:**

- `github-modes` - GitHub operations
- `pr-manager` - Pull request management
- `code-review-swarm` - Collaborative code review
- `issue-tracker` - Issue management
- `release-manager` - Release coordination
- `workflow-automation` - GitHub Actions automation
- `project-board-sync` - Project board synchronization
- `repo-architect` - Repository architecture
- `multi-repo-swarm` - Multi-repository coordination

### SPARC Methodology Agents

**Agents for SPARC workflow:**

- `sparc-coord` - SPARC coordination
- `sparc-coder` - SPARC-based coding
- `specification` - Requirements specification
- `pseudocode` - Algorithm design
- `architecture` - System architecture
- `refinement` - Code refinement

### Specialized Development Agents

**Domain-specific agents:**

- `backend-dev` - Backend development
- `mobile-dev` - Mobile development
- `ml-developer` - Machine learning
- `cicd-engineer` - CI/CD pipeline
- `api-docs` - API documentation
- `system-architect` - System architecture
- `code-analyzer` - Code analysis
- `base-template-generator` - Template generation

### Testing & Validation Agents

**Agents for testing:**

- `tdd-london-swarm` - TDD London school
- `production-validator` - Production validation

### Migration & Planning Agents

**Agents for migrations:**

- `migration-planner` - Migration planning
- `swarm-init` - Swarm initialization

---

## 🎯 Claude Code vs MCP Tools

### Claude Code Handles ALL EXECUTION

**Claude Code's Task tool spawns agents that do actual work:**

- File operations (Read, Write, Edit, MultiEdit, Glob, Grep)
- Code generation and programming
- Bash commands and system operations
- Implementation work
- Project navigation and analysis
- TodoWrite and task management
- Git operations
- Package management
- Testing and debugging

### MCP Tools ONLY COORDINATE

**MCP tools set up coordination topology:**

- Swarm initialization (topology setup)
- Agent type definitions (coordination patterns)
- Task orchestration (high-level planning)
- Memory management
- Neural features
- Performance tracking
- GitHub integration

**KEY**: MCP coordinates the strategy, Claude Code's Task tool executes with real agents.

---

## 📋 Agent Coordination Protocol

### Every Agent Spawned via Task Tool MUST

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

---

## 🔧 MCP Tool Categories

### Coordination Tools

- `swarm_init` - Initialize swarm topology
- `agent_spawn` - Spawn agent types
- `task_orchestrate` - Orchestrate tasks

### Monitoring Tools

- `swarm_status` - Check swarm status
- `agent_list` - List active agents
- `agent_metrics` - Agent performance metrics
- `task_status` - Task progress
- `task_results` - Task results

### Memory & Neural Tools

- `memory_usage` - Memory operations
- `neural_status` - Neural system status
- `neural_train` - Train neural patterns
- `neural_patterns` - Pattern recognition

### GitHub Integration Tools

- `github_swarm` - GitHub swarm operations
- `repo_analyze` - Repository analysis
- `pr_enhance` - PR enhancement
- `issue_triage` - Issue triage
- `code_review` - Code review

### System Tools

- `benchmark_run` - Run benchmarks
- `features_detect` - Detect features
- `swarm_monitor` - Monitor swarm

---

## 🎛️ Coordination Modes

### 1. CENTRALIZED (Default)

**Single coordinator manages all agents**

- **Use when**: Clear hierarchy needed, simple workflows
- **Tools**: `agent_assign`, `task_create`, `swarm_monitor`
- **Benefits**: Clear chain of command, consistent decisions

### 2. DISTRIBUTED

**Multiple coordinators share responsibility**

- **Use when**: Large scale tasks, fault tolerance needed
- **Tools**: `agent_coordinate`, `memory_sync`, `task_update`
- **Benefits**: Scalability, fault tolerance

### 3. HIERARCHICAL

**Tree structure with team leads**

- **Use when**: Complex projects with sub-teams
- **Tools**: `agent_spawn` (with parent), `task_create` (with subtasks)
- **Benefits**: Clear organization, delegation

### 4. MESH

**Peer-to-peer agent coordination**

- **Use when**: Maximum flexibility, self-organizing teams
- **Tools**: `agent_communicate`, `memory_store/retrieve`
- **Benefits**: Flexibility, self-organization

---

## 🚀 Agent Execution Flow

### The Correct Pattern

1. **Optional**: Use MCP tools to set up coordination topology
2. **REQUIRED**: Use Claude Code's Task tool to spawn agents that do actual work
3. **REQUIRED**: Each agent runs hooks for coordination
4. **REQUIRED**: Batch all operations in single messages

### Example Full-Stack Development

```javascript
// Single message with all agent spawning via Claude Code's Task tool
[Parallel Agent Execution]:
  Task("Backend Developer", "Build REST API with FastAPI. Use hooks for coordination.", "backend-dev")
  Task("Frontend Developer", "Create Next.js UI. Coordinate with backend via memory.", "coder")
  Task("Database Architect", "Design Supabase schema. Store schema in memory.", "code-analyzer")
  Task("Test Engineer", "Write Jest tests. Check memory for API contracts.", "tester")
  Task("DevOps Engineer", "Setup Docker and CI/CD. Document in memory.", "cicd-engineer")
  Task("Security Auditor", "Review authentication. Report findings via hooks.", "reviewer")

  // All todos batched together
  TodoWrite { todos: [...8-10 todos...] }

  // All file operations together
  Write "backend/server.py"
  Write "app/page.tsx"
  Write "supabase/schema.sql"
```

---

## 🔗 Hooks Integration

### Pre-Operation Hooks

- Auto-assign agents by file type
- Validate commands for safety
- Prepare resources automatically
- Optimize topology by complexity
- Cache searches

### Post-Operation Hooks

- Auto-format code
- Train neural patterns
- Update memory
- Analyze performance
- Track token usage

### Session Management Hooks

- Generate summaries
- Persist state
- Track metrics
- Restore context
- Export workflows

---

## 📊 Performance Benefits

- **84.8% SWE-Bench solve rate**
- **32.3% token reduction**
- **2.8-4.4x speed improvement**
- **27+ neural models**

---

## 🔗 Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Essential commands and quick reference
- **[VECTORCODE_GUIDE.md](./VECTORCODE_GUIDE.md)** - Semantic code search
- **[SPARC_METHODOLOGY.md](./SPARC_METHODOLOGY.md)** - Development workflow

---

**🤖 For quick agent spawning examples, see [CLAUDE.md](../CLAUDE.md)!**

