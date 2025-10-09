# SPARC Methodology - Microbiome Platform

**Systematic Test-Driven Development with Claude Flow orchestration**

> **Quick Reference**: See [CLAUDE.md](../CLAUDE.md) for essential workflow  
> **Related**: [VECTORCODE_GUIDE.md](./VECTORCODE_GUIDE.md) | [CLAUDE_FLOW_AGENTS.md](./CLAUDE_FLOW_AGENTS.md)

---

## 📋 SPARC Overview

SPARC (Specification, Pseudocode, Architecture, Refinement, Completion) is a systematic methodology for Test-Driven Development with Claude-Flow orchestration.

---

## 🚀 SPARC Commands

### Core Commands

```bash
# List available modes
npx claude-flow sparc modes

# Execute specific mode
npx claude-flow sparc run <mode> "<task>"

# Run complete TDD workflow
npx claude-flow sparc tdd "<feature>"

# Get mode details
npx claude-flow sparc info <mode>
```

### Batchtools Commands

```bash
# Parallel execution
npx claude-flow sparc batch <modes> "<task>"

# Full pipeline processing
npx claude-flow sparc pipeline "<task>"

# Multi-task processing
npx claude-flow sparc concurrent <mode> "<tasks-file>"
```

### Build Commands

```bash
# Build project
npm run build

# Run tests
npm run test

# Linting
npm run lint

# Type checking
npm run typecheck
```

---

## 🔄 SPARC Workflow Phases

### 1. Specification - Requirements Analysis

**Command**: `sparc run spec-pseudocode`

**Purpose**: Define clear requirements and acceptance criteria

**Activities**:
- Gather requirements
- Define acceptance criteria
- Identify constraints
- Document assumptions

### 2. Pseudocode - Algorithm Design

**Command**: `sparc run spec-pseudocode`

**Purpose**: Design algorithms and data structures

**Activities**:
- Design algorithms
- Define data structures
- Plan control flow
- Identify edge cases

### 3. Architecture - System Design

**Command**: `sparc run architect`

**Purpose**: Design system architecture and components

**Activities**:
- Design system architecture
- Define component interfaces
- Plan data flow
- Identify dependencies

### 4. Refinement - TDD Implementation

**Command**: `sparc tdd`

**Purpose**: Implement with test-driven development

**Activities**:
- Write failing tests
- Implement minimal code
- Refactor for quality
- Iterate until complete

### 5. Completion - Integration

**Command**: `sparc run integration`

**Purpose**: Integrate and validate complete system

**Activities**:
- Integration testing
- Performance validation
- Documentation updates
- Deployment preparation

---

## 🎯 Concurrent Execution Examples

### ✅ CORRECT WORKFLOW: MCP Coordinates, Claude Code Executes

**Step 1: MCP tools set up coordination (optional, for complex tasks)**

```javascript
[Single Message - Coordination Setup]:
  mcp__claude-flow__swarm_init { topology: "mesh", maxAgents: 6 }
  mcp__claude-flow__agent_spawn { type: "researcher" }
  mcp__claude-flow__agent_spawn { type: "coder" }
  mcp__claude-flow__agent_spawn { type: "tester" }
```

**Step 2: Claude Code Task tool spawns ACTUAL agents that do the work**

```javascript
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
```

---

## ⚡ GOLDEN RULE: "1 MESSAGE = ALL RELATED OPERATIONS"

**MANDATORY PATTERNS:**

- **TodoWrite**: ALWAYS batch ALL todos in ONE call (5-10+ todos minimum)
- **Task tool (Claude Code)**: ALWAYS spawn ALL agents in ONE message with full instructions
- **File operations**: ALWAYS batch ALL reads/writes/edits in ONE message
- **Bash commands**: ALWAYS batch ALL terminal operations in ONE message
- **Memory operations**: ALWAYS batch ALL memory store/retrieve in ONE message

---

## 📊 Performance Benefits

### Speed Improvements

- **2.8-4.4x faster** than sequential execution
- **32.3% token reduction** through batching
- **84.8% SWE-Bench solve rate**

### Quality Improvements

- **Systematic approach** reduces errors
- **Test-first** ensures correctness
- **Parallel execution** maintains quality
- **Continuous refinement** improves code

---

## 🔧 Code Style & Best Practices

### Modular Design

- **Files under 500 lines** - Keep components focused
- **Single responsibility** - One purpose per module
- **Clear interfaces** - Well-defined contracts
- **Minimal coupling** - Reduce dependencies

### Environment Safety

- **Never hardcode secrets** - Use environment variables
- **Validate inputs** - Check all external data
- **Handle errors** - Graceful degradation
- **Log appropriately** - Debug without exposing secrets

### Test-First Development

- **Write tests before implementation** - TDD approach
- **Test edge cases** - Cover boundary conditions
- **Mock external dependencies** - Isolate units
- **Maintain high coverage** - Aim for 80%+

### Clean Architecture

- **Separate concerns** - Business logic vs infrastructure
- **Dependency injection** - Invert dependencies
- **Interface segregation** - Small, focused interfaces
- **Open/closed principle** - Open for extension, closed for modification

### Documentation

- **Keep updated** - Document as you code
- **Explain why** - Not just what
- **Include examples** - Show usage
- **Link related docs** - Cross-reference

---

## 🎯 SPARC with Parallel Execution

### 1. Specification Phase (Single BatchTool)

```javascript
[BatchTool]:
  mcp__claude-flow__memory_store { key: "specs/requirements", value: {...} }
  mcp__claude-flow__task_create { name: "Requirement 1" }
  mcp__claude-flow__task_create { name: "Requirement 2" }
  mcp__claude-flow__task_create { name: "Requirement 3" }
  mcp__claude-flow__agent_spawn { type: "researcher", name: "SpecAnalyst" }
```

### 2. Pseudocode Phase (Single BatchTool)

```javascript
[BatchTool]:
  mcp__claude-flow__memory_store { key: "pseudocode/main", value: {...} }
  mcp__claude-flow__task_create { name: "Design API" }
  mcp__claude-flow__task_create { name: "Design Data Model" }
  mcp__claude-flow__agent_communicate { to: "all", message: "Review design" }
```

### 3. Architecture Phase (Single BatchTool)

```javascript
[BatchTool]:
  mcp__claude-flow__agent_spawn { type: "architect", name: "LeadArchitect" }
  mcp__claude-flow__memory_store { key: "architecture/decisions", value: {...} }
  mcp__claude-flow__task_create { name: "Backend", subtasks: [...] }
  mcp__claude-flow__task_create { name: "Frontend", subtasks: [...] }
```

### 4. Refinement Phase (Single BatchTool)

```javascript
[BatchTool]:
  mcp__claude-flow__swarm_monitor {}
  mcp__claude-flow__task_update { taskId: "1", progress: 50 }
  mcp__claude-flow__task_update { taskId: "2", progress: 75 }
  mcp__claude-flow__memory_store { key: "learnings/iteration1", value: {...} }
```

### 5. Completion Phase (Single BatchTool)

```javascript
[BatchTool]:
  mcp__claude-flow__task_complete { taskId: "1", results: {...} }
  mcp__claude-flow__task_complete { taskId: "2", results: {...} }
  mcp__claude-flow__memory_retrieve { pattern: "**/*" }
  TodoWrite { todos: [{content: "Final review", status: "completed"}] }
```

---

## 🔗 Integration Tips

1. **Start with basic swarm init** - Don't over-engineer
2. **Scale agents gradually** - Add as needed
3. **Use memory for context** - Share knowledge
4. **Monitor progress regularly** - Stay informed
5. **Train patterns from success** - Learn and improve
6. **Enable hooks automation** - Reduce manual work
7. **Use GitHub tools first** - Leverage existing integrations

---

## 📚 Advanced Features (v2.0.0)

- 🚀 Automatic Topology Selection
- ⚡ Parallel Execution (2.8-4.4x speed)
- 🧠 Neural Training
- 📊 Bottleneck Analysis
- 🤖 Smart Auto-Spawning
- 🛡️ Self-Healing Workflows
- 💾 Cross-Session Memory
- 🔗 GitHub Integration

---

## 🔗 Related Documentation

- **[CLAUDE.md](../CLAUDE.md)** - Essential commands and quick reference
- **[VECTORCODE_GUIDE.md](./VECTORCODE_GUIDE.md)** - Semantic code search
- **[CLAUDE_FLOW_AGENTS.md](./CLAUDE_FLOW_AGENTS.md)** - Agent types and coordination

---

## 📞 Support

- Documentation: <https://github.com/ruvnet/claude-flow>
- Issues: <https://github.com/ruvnet/claude-flow/issues>

---

**🚀 For quick SPARC commands, see [CLAUDE.md](../CLAUDE.md)!**

