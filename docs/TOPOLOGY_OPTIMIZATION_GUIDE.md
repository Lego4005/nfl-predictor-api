# Automatic Topology Optimization Guide

## Overview

This guide documents the automatic topology selection system for Claude Flow swarm coordination in the NFL Predictor API project.

## Quick Reference

### Topology Decision Matrix

| Task Complexity | File Count | Agents | Recommended Topology | Example Tasks |
|----------------|------------|--------|---------------------|---------------|
| **Simple** | 1-3 | 1-2 | Star | Bug fixes, config updates, typos |
| **Moderate** | 3-8 | 2-4 | Star/Hierarchical | New endpoint, component, minor refactor |
| **Complex** | 8-20 | 4-8 | Hierarchical | ML model updates, WebSocket features |
| **Very Complex** | 20-50 | 6-12 | Mesh | Full-stack features, ensemble redesign |
| **Critical Infrastructure** | 50+ | 8-15 | Mesh/Adaptive | Platform migrations, architecture overhauls |

---

## Project Complexity Profile

### Codebase Scale
- **244,307** total lines of code
- **617** Python files
- **150+** TypeScript/React files
- **77** test files
- **96** script files

### Architecture Layers
1. **ML Models** (47 files) - VERY HIGH complexity
   - Ensemble predictors, expert systems, belief revision
   - Personality-driven experts, competition frameworks
   - Adaptive learning, episodic memory

2. **API Layer** (29 files) - HIGH complexity
   - Multiple external API clients (SportsData.io, ESPN, RapidAPI)
   - Live data management, source switching
   - WebSocket API, accuracy endpoints

3. **Frontend** (150+ files) - HIGH complexity
   - React + TypeScript with 18+ component directories
   - Tanstack Router/Query, Radix UI, Framer Motion
   - Real-time WebSocket integration

4. **Supporting Systems** - MEDIUM complexity
   - Database, Cache, Monitoring, Analytics, WebSocket handlers

**Overall Complexity Score: 9.2/10** - Production-grade system requiring sophisticated coordination

---

## Topology Selection Algorithm

### Decision Tree (6 Steps)

#### Step 1: Agent Count Filter
```
≤2 agents   → Star only
≤4 agents   → Star, Mesh, Ring
≤8 agents   → Mesh, Hierarchical, Ring
>8 agents   → Hierarchical only
```

#### Step 2: Complexity Filter
```
Simple      → Star (if ≤3 agents)
Medium      → Mesh, Ring
Complex     → Mesh, Hierarchical
Enterprise  → Hierarchical
```

#### Step 3: Coordination Pattern Analysis
```
Centralized → Boost Star (+20), Hierarchical (+10)
Distributed → Boost Mesh (+20)
Sequential  → Boost Ring (+20)
Parallel    → Boost Mesh (+15), Hierarchical (+10)
```

#### Step 4: Dependency Structure
```
None       → Boost Mesh (+15)
Linear     → Boost Ring (+20)
Tree/DAG   → Boost Hierarchical (+20)
Cyclic     → Boost Mesh (+15)
```

#### Step 5: Resource Constraints
```
Low memory  → Penalize Mesh (-10), Hierarchical (-15)
Low CPU     → Penalize Hierarchical (-10)
Low latency → Boost Mesh (+10)
```

#### Step 6: Weighted Final Scoring
```
Return highest scoring topology with:
- Confidence percentage
- Reasoning list
- Alternative recommendation
- Warnings
```

---

## Topology Profiles

### Star Topology ⭐
**Best For:**
- Simple, centralized tasks
- 1-3 agents
- Clear single coordinator
- Rapid prototyping/MVPs

**Performance:**
- 2-hop latency (~40ms)
- 5-20 agent maximum
- 95% availability
- Single point of failure

**Example:** Fix bug in single endpoint

### Mesh Topology 🕸️
**Best For:**
- Medium-complex tasks
- 3-8 agents
- Peer-to-peer collaboration
- High reliability needs

**Performance:**
- 1-hop latency (~20ms) - FASTEST
- 10-15 agent maximum
- 99.9% availability
- O(n²) communication overhead

**Example:** Full-stack feature with backend + frontend + database coordination

### Hierarchical Topology 🌳
**Best For:**
- Complex, multi-layered tasks
- 5-100+ agents
- Clear task decomposition
- Large-scale coordination

**Performance:**
- O(log n) hops (~80ms for 15 agents)
- Unlimited agent count
- 95-98% availability
- Coordinator bottleneck at root

**Example:** Platform migration, ML pipeline redesign

### Ring Topology 🔄
**Best For:**
- Sequential workflows
- Pipeline processing
- Bandwidth-constrained environments
- 3-8 agents

**Performance:**
- n/2 hop latency (~160ms for 15 agents) - SLOWEST
- Low bandwidth usage
- 85-90% availability
- Sequential processing only

**Example:** CI/CD pipeline, data transformation stages

---

## Task-Specific Recommendations

### NFL Predictor API Subsystems

#### 1. Data Ingestion Pipeline (5 sources)
- **Topology:** Star → Hierarchical (adaptive)
- **Agent Count:** 5-8
- **Agents:** `coordinator`, 5x `api-client` specialists, `cache-manager`, `error-handler`
- **Target:** <1s latency, 99% availability

#### 2. ML Model Training (15 experts)
- **Topology:** Ring AllReduce
- **Agent Count:** 15
- **Agents:** 15x `ml-developer` (one per expert model)
- **Target:** <5 min training/week, visible improvement in 4-6 weeks

#### 3. Expert Council Consensus (15 total, top 5 vote)
- **Topology:** Hybrid (Mesh for top 5 + Hierarchical for full 15)
- **Agent Count:** 15
- **Agents:** `consensus-coordinator`, 15x `expert-agent`, `vote-aggregator`
- **Target:** <100ms consensus, >62% accuracy, <50 messages

#### 4. Real-Time Predictions
- **Topology:** Star + Redis Cache
- **Agent Count:** 3-5
- **Agents:** `prediction-coordinator`, `cache-manager`, `ml-inference`, `api-responder`
- **Target:** <500ms P99 latency, >80% cache hit rate

#### 5. Virtual Betting System
- **Topology:** Star Centralized (NO ALTERNATIVES)
- **Agent Count:** 1-2
- **Agents:** `transaction-coordinator` (single, ACID-compliant)
- **Target:** 100% consistency, <100ms latency

#### 6. Frontend Component Development
- **Topology:** Star (simple) or Mesh (complex)
- **Agent Count:** 2-6
- **Agents:** `ui-developer`, `state-manager`, `api-integrator`, `tester`, `reviewer`
- **Target:** Depends on component complexity

---

## Agent Spawning Rules

### By Layer
- **ML:** `researcher` + `ml-developer` + `code-analyzer` + `tester` (min 3-4)
- **API:** `backend-dev` + `api-docs` + `tester` (min 3)
- **Frontend:** `coder` + `reviewer` + `tester` (min 3)
- **Full-Stack:** `backend-dev` + `frontend-dev` + `database-architect` + `tester` (min 4)

### By Task Type
- **Bug Fix:** `coder` + `tester` (2)
- **New Feature:** `researcher` + `coder` + `tester` + `reviewer` (4)
- **Performance:** `perf-analyzer` + `code-analyzer` + `optimizer` + `tester` (4)
- **Refactor:** `system-architect` + `coder` + `reviewer` + `tester` (4)

---

## Adaptive Strategies

### Dynamic Switching Triggers

**Scale Up:**
```
Star → Hierarchical:  When agent count > 8
Star → Mesh:         When hub reliability drops
Mesh → Hierarchical: When agent count > 15
```

**Optimize Performance:**
```
Ring → Hierarchical:  When P99 latency > 500ms
Star → Mesh:         When need fault tolerance
Hierarchical → Mesh: When need lower latency (and ≤15 agents)
```

**Resource Constraints:**
```
Mesh → Hierarchical:  When messages/task > 10x
Hierarchical → Star: When agent count drops to ≤3
```

### Transition Strategy
1. **Graceful Migration:** Add new connections before removing old
2. **Checkpoint & Switch:** Save state, switch topology, restore state
3. **Dual Topology:** Run both briefly during transition (< 30s)

---

## Monitoring Metrics

### Health Indicators
- **Communication Cost:** messages_sent / tasks_completed
  - Healthy: <5x
  - Warning: 5-10x
  - Alert: >10x

- **Coordination Latency:** time_to_consensus
  - Healthy: <100ms
  - Warning: 100-500ms
  - Alert: >500ms

- **Resource Utilization:** (CPU + bandwidth) / capacity
  - Healthy: 40-70%
  - Warning: 70-85%
  - Alert: >85%

- **Task Completion Rate:** completed_tasks / total_tasks
  - Healthy: >90%
  - Warning: 80-90%
  - Alert: <80%

---

## Common Patterns

### Pattern 1: Simple Bug Fix
```bash
# Topology: Star
# Agents: 2 (coder, tester)
# Duration: 5-15 minutes

Task("Fix authentication bug", "...", "coder")
Task("Test authentication fix", "...", "tester")
```

### Pattern 2: New ML Model
```bash
# Topology: Hierarchical
# Agents: 5 (researcher, ml-developer, code-analyzer, tester, reviewer)
# Duration: 2-4 hours

Task("Research model approaches", "...", "researcher")
Task("Implement ML model", "...", "ml-developer")
Task("Analyze code quality", "...", "code-analyzer")
Task("Create test suite", "...", "tester")
Task("Review implementation", "...", "reviewer")
```

### Pattern 3: Full-Stack Feature
```bash
# Topology: Mesh
# Agents: 6-8 (backend-dev, frontend-dev, database-architect, api-docs, tester, reviewer)
# Duration: 4-8 hours

Task("Design database schema", "...", "database-architect")
Task("Build REST API", "...", "backend-dev")
Task("Create React UI", "...", "coder")
Task("Write API docs", "...", "api-docs")
Task("Integration tests", "...", "tester")
Task("Code review", "...", "reviewer")
```

### Pattern 4: Performance Optimization
```bash
# Topology: Hierarchical
# Agents: 5 (perf-analyzer, code-analyzer, optimizer, tester, reviewer)
# Duration: 2-6 hours

Task("Identify bottlenecks", "...", "perf-analyzer")
Task("Analyze code patterns", "...", "code-analyzer")
Task("Optimize critical paths", "...", "coder")
Task("Validate improvements", "...", "tester")
Task("Review changes", "...", "reviewer")
```

---

## Common Mistakes

### ❌ Wrong Topology Choices

**Mistake 1:** Using Mesh for 20+ agents
- **Problem:** O(n²) communication overhead
- **Fix:** Use Hierarchical instead

**Mistake 2:** Using Star for critical fault-tolerant systems
- **Problem:** Single point of failure
- **Fix:** Use Mesh or Hierarchical with backups

**Mistake 3:** Using Ring for real-time tasks
- **Problem:** High latency (n/2 hops)
- **Fix:** Use Star or Mesh

**Mistake 4:** Not switching topologies as project grows
- **Problem:** Inefficient coordination at scale
- **Fix:** Monitor metrics, trigger adaptive switching

**Mistake 5:** Using distributed topology for ACID transactions
- **Problem:** Consistency violations
- **Fix:** Use Star Centralized only

---

## Implementation Checklist

### Phase 1: Immediate (Week 1)
- [ ] Implement Star topology for data ingestion
- [ ] Implement Star + Cache for real-time predictions
- [ ] Implement Star (centralized) for betting system
- [ ] Set up basic monitoring metrics

### Phase 2: Short-term (Weeks 2-4)
- [ ] Implement Hierarchical for expert council
- [ ] Implement Ring AllReduce for ML training
- [ ] Add monitoring dashboards
- [ ] Document topology decisions

### Phase 3: Long-term (Months 2-3)
- [ ] Implement Mesh for top 5 expert consensus
- [ ] Build adaptive topology switching logic
- [ ] Optimize based on production metrics
- [ ] Train team on topology selection

---

## CLI Usage

### Initialize Topology
```bash
# Automatic selection
npx claude-flow optimize topology

# Manual selection
npx claude-flow swarm init --topology mesh --max-agents 8
```

### Monitor Performance
```bash
# Real-time monitoring
npx claude-flow swarm monitor --interval 5

# Get status
npx claude-flow swarm status --verbose
```

### Analyze Bottlenecks
```bash
# Performance analysis
npx claude-flow performance report --detailed

# Bottleneck detection
npx claude-flow bottleneck analyze --component swarm
```

---

## References

### Internal Documentation
- [TOPOLOGY_OPTIMIZATION_RESEARCH.md](./research/TOPOLOGY_OPTIMIZATION_RESEARCH.md) - Complete research findings
- [TOPOLOGY_TASK_MAPPING.md](./research/TOPOLOGY_TASK_MAPPING.md) - Task-specific mappings
- [CLAUDE.md](../CLAUDE.md) - Project configuration

### External Resources
- Claude Flow Documentation: https://github.com/ruvnet/claude-flow
- Distributed Systems Principles: Martin Kleppmann's "Designing Data-Intensive Applications"
- Swarm Intelligence: Kennedy & Eberhart's "Swarm Intelligence"

---

## Support

**Questions or Issues?**
- GitHub Issues: https://github.com/ruvnet/claude-flow/issues
- Project Lead: Iris (NFL Predictor API)
- Last Updated: 2025-09-30

---

*This guide is automatically maintained by the Claude Flow optimization system.*
