# Topology-Task Mapping: Quick Reference Guide

**Purpose**: Fast lookup table for selecting optimal coordination topology based on task characteristics
**Context**: NFL Predictor API multi-agent coordination
**Last Updated**: 2025-09-30

---

## Quick Decision Tree

```
START
  │
  ├─ Team Size < 5 agents?
  │   ├─ YES → Is fault tolerance critical?
  │   │   ├─ YES → MESH
  │   │   └─ NO → STAR
  │   └─ NO → Continue
  │
  ├─ Team Size 5-15 agents?
  │   ├─ YES → Is task complex/multi-stage?
  │   │   ├─ YES → HIERARCHICAL
  │   │   └─ NO → STAR or HIERARCHICAL
  │   └─ NO → Continue
  │
  └─ Team Size > 15 agents?
      └─ HIERARCHICAL (only viable option)
```

---

## Common Task Patterns with Examples

### 1. Data Aggregation Tasks

**Characteristics**: Multiple sources → Single result

**Example: NFL Predictor Data Ingestion**
```python
# Gather weather, odds, injuries, social sentiment, stats
sources = [
    WeatherService(),      # OpenWeatherMap
    OddsService(),         # The Odds API
    InjuryService(),       # ESPN
    SentimentService(),    # Reddit
    StatsService()         # nflfastR
]
```

**Recommended Topology**: **Star (5 sources) → Hierarchical (>10 sources)**

**Reasoning**:
- Simple aggregation pattern
- Central coordinator caches results
- Easy failover to cached data
- Switch to hierarchical if adding more sources

**Code Example**:
```python
class DataAggregator:
    def __init__(self, sources):
        self.topology = (
            StarTopology(sources) if len(sources) <= 10
            else HierarchicalTopology(sources)
        )

    async def gather(self, game_id):
        return await self.topology.gather_all(
            [s.fetch(game_id) for s in self.topology.nodes]
        )
```

---

### 2. Consensus/Voting Tasks

**Characteristics**: Multiple opinions → Agreement

**Example: Expert Council Voting**
```python
# 15 expert agents vote on prediction
experts = [
    TheAnalyst(), TheGambler(), TheScholar(),
    TheRebel(), TheSharpMoney(), # ... 10 more
]

# Top 5 need fast consensus
top_5 = select_top_performers(experts, n=5)
```

**Recommended Topology**: **Mesh (top 5) + Hierarchical (full 15)**

**Reasoning**:
- Top 5 need direct communication for fast agreement
- Full 15 too expensive for mesh (105 connections)
- Hierarchical coordinates all, mesh accelerates top tier

**Code Example**:
```python
class ConsensusCoordinator:
    async def get_prediction(self, game_id):
        # All experts predict via hierarchical
        all_predictions = await self.hierarchical.gather(game_id)

        # Top 5 reach consensus via mesh
        top_5 = self.select_top_5(all_predictions)
        mesh = MeshTopology(top_5)
        consensus = await mesh.vote()

        return consensus
```

---

### 3. Pipeline Processing Tasks

**Characteristics**: Sequential stages with dependencies

**Example: Prediction Pipeline**
```python
pipeline_stages = [
    DataIngestion(),      # Stage 1: Fetch data
    FeatureEngineering(), # Stage 2: Transform
    ModelInference(),     # Stage 3: Predict
    Calibration(),        # Stage 4: Adjust
    OutputFormatting()    # Stage 5: Format
]
```

**Recommended Topology**: **Hierarchical (preferred) or Ring**

**Reasoning**:
- Hierarchical: Parallel stages when possible
- Ring: Sequential processing with minimal overhead
- Avoid mesh (no need for all-to-all)

**Code Example**:
```python
class PipelineCoordinator:
    def __init__(self):
        self.topology = HierarchicalTopology([
            ParallelStage([DataIngestion(), FeatureEngineering()]),
            SequentialStage([ModelInference(), Calibration()]),
            FinalStage([OutputFormatting()])
        ])

    async def process(self, input_data):
        return await self.topology.execute_pipeline(input_data)
```

---

### 4. Parallel Independent Tasks

**Characteristics**: No dependencies, embarrassingly parallel

**Example: Batch Prediction for Multiple Games**
```python
games = [
    Game("SF vs KC"), Game("BUF vs MIA"),
    Game("DAL vs PHI"), Game("GB vs CHI"),
    # ... 12 more games per week
]

experts = [Expert(i) for i in range(15)]
```

**Recommended Topology**: **Star (simple) or Hierarchical (large scale)**

**Reasoning**:
- No inter-task communication needed
- Simple work distribution
- Scale with hierarchical if >20 tasks per agent

**Code Example**:
```python
class BatchCoordinator:
    async def predict_all_games(self, games, experts):
        # Star topology: Hub assigns games to experts
        assignments = self.hub.assign_work(games, experts)

        # Parallel execution
        results = await asyncio.gather(
            *[expert.predict(game) for game, expert in assignments]
        )

        return results
```

---

### 5. Real-Time Coordination Tasks

**Characteristics**: Low latency critical (<500ms)

**Example: Live Game Prediction Updates**
```python
class LivePredictionService:
    def __init__(self):
        self.cache = RedisCache()  # <10ms lookups
        self.predictor = PredictionEngine()
        self.updater = RealtimeUpdater()
```

**Recommended Topology**: **Star with Cache Layer**

**Reasoning**:
- 2 hops maximum (low latency)
- Centralized caching reduces DB hits
- Simple architecture for speed

**Code Example**:
```python
class RealtimeCoordinator:
    async def get_prediction(self, game_id):
        # Star hub checks cache first
        cached = await self.cache.get(game_id)
        if cached:
            return cached  # <10ms

        # Generate prediction via star workers
        prediction = await self.star_topology.predict(game_id)

        # Cache for 5 minutes
        await self.cache.set(game_id, prediction, ttl=300)
        return prediction
```

---

### 6. Distributed ML Training Tasks

**Characteristics**: Gradient synchronization, iterative

**Example: Expert Agent Training**
```python
experts = [ExpertAgent(personality) for personality in [
    "analyst", "gambler", "scholar", "rebel",
    "sharp", "weather_wizard", # ... 9 more
]]

training_data = historical_nfl_games(2020, 2024)
```

**Recommended Topology**: **Ring (AllReduce) or Hierarchical**

**Reasoning**:
- Ring AllReduce: Bandwidth efficient for gradient passing
- Hierarchical: Better if agents train at different speeds
- Avoid mesh (15 agents = 105 connections too expensive)

**Code Example**:
```python
class TrainingCoordinator:
    def __init__(self, experts):
        self.ring = RingTopology(experts)

    async def training_step(self):
        # Each expert computes gradient
        gradients = await asyncio.gather(
            *[e.compute_gradient() for e in self.ring.nodes]
        )

        # Ring AllReduce to average
        avg_gradient = await self.ring.all_reduce(gradients)

        # Apply averaged gradient
        await asyncio.gather(
            *[e.apply_gradient(avg_gradient) for e in self.ring.nodes]
        )
```

---

### 7. Monitoring/Observability Tasks

**Characteristics**: Continuous metrics collection

**Example: System Health Monitoring**
```python
monitors = [
    APIHealthMonitor(),
    DatabaseMonitor(),
    CacheMonitor(),
    PredictionQualityMonitor(),
    BankrollMonitor()
]
```

**Recommended Topology**: **Star (simple) or Hierarchical (many metrics)**

**Reasoning**:
- Centralized metrics aggregation
- Time-series database at hub
- Alerts generated from hub

**Code Example**:
```python
class MonitoringCoordinator:
    def __init__(self):
        self.hub = MetricsAggregator()
        self.topology = StarTopology([
            self.hub,
            *monitors
        ])

    async def collect_metrics(self):
        metrics = await self.topology.gather_all()
        await self.hub.store_metrics(metrics)
        await self.hub.check_alerts()
```

---

### 8. ACID Transaction Tasks

**Characteristics**: Consistency critical, no tolerance for errors

**Example: Virtual Betting System**
```python
class BettingSystem:
    # Place bets, deduct bankroll, record transactions
    # ALL OR NOTHING - consistency critical
```

**Recommended Topology**: **Star (Centralized DB) - ALWAYS**

**Reasoning**:
- Single source of truth required
- ACID transactions need centralized coordinator
- Correctness > distribution

**Code Example**:
```python
class BettingCoordinator:
    async def place_bet(self, expert_id, bet_size, game_id):
        # Centralized database transaction
        async with self.db.transaction():
            # ACID guarantees
            await self.deduct_bankroll(expert_id, bet_size)
            await self.record_bet(expert_id, game_id, bet_size)
            await self.update_stats(expert_id)

        # NO DISTRIBUTED COORDINATION - correctness critical
```

---

## Task-Topology Mapping Table

| Task Type | Team Size | Latency | Fault Tol. | Recommended | Alternative |
|-----------|-----------|---------|------------|-------------|-------------|
| **Data Aggregation** | 5-10 | Medium | Medium | Star | Hierarchical |
| **Consensus/Voting** | 5-15 | Low | High | Mesh (small) | Hierarchical |
| **Pipeline Processing** | Any | Medium | Medium | Hierarchical | Ring |
| **Parallel Independent** | Any | Low | Low | Star | Hierarchical |
| **Real-Time Critical** | 3-8 | Very Low | Medium | Star + Cache | Hierarchical |
| **ML Training** | 10-50 | High | Low | Ring | Hierarchical |
| **Monitoring** | 5-20 | Low | Low | Star | Hierarchical |
| **ACID Transactions** | Any | Medium | Very High | Star (Centralized) | NONE |
| **Broadcast Messages** | Any | Medium | Medium | Hierarchical | Mesh (small) |
| **Resource Allocation** | Any | Medium | High | Hierarchical | Star |

---

## NFL Predictor API Subsystem Mapping

### Complete System Architecture

```
NFL PREDICTOR API
├── Data Ingestion (5 sources)
│   └── Topology: Star → Hierarchical (if >10 sources)
│
├── Expert Council (15 agents)
│   ├── Top 5 Consensus: Mesh (10 connections)
│   └── Full 15 Coordination: Hierarchical
│
├── ML Training (15 experts)
│   └── Topology: Ring AllReduce (bandwidth efficient)
│
├── Real-Time Predictions
│   └── Topology: Star + Redis Cache (low latency)
│
├── Betting System
│   └── Topology: Star Centralized (ACID required)
│
└── Monitoring (5 monitors)
    └── Topology: Star (simple aggregation)
```

### Detailed Subsystem Breakdown

#### 1. Data Ingestion Pipeline

**Current State**: 5 data sources (Weather, Odds, Injury, Social, Stats)

**Topology Choice**: **Star**

**Implementation**:
```python
class DataCoordinator:
    def __init__(self):
        self.topology = StarTopology([
            WeatherService(),    # OpenWeatherMap
            OddsService(),       # The Odds API
            InjuryService(),     # ESPN
            SentimentService(),  # Reddit
            StatsService()       # nflfastR
        ])
        self.cache = RedisCache()

    async def fetch_game_data(self, game_id):
        # Check cache first (hub)
        cached = await self.cache.get(f"game:{game_id}")
        if cached:
            return cached

        # Fetch from all sources via star
        data = await self.topology.gather_all(game_id)

        # Cache result
        await self.cache.set(f"game:{game_id}", data, ttl=300)
        return data
```

**Performance Targets**:
- Latency: <1 second
- Availability: 99% (cached fallback)
- Cost: $0/month

**Adaptive Trigger**: Switch to Hierarchical if >10 sources

---

#### 2. Expert Council Consensus

**Current State**: 15 expert agents, top 5 vote

**Topology Choice**: **Hybrid (Mesh for Top 5 + Hierarchical for Full 15)**

**Implementation**:
```python
class ExpertCouncilCoordinator:
    def __init__(self, experts):
        self.all_experts = experts
        self.hierarchical = HierarchicalTopology(experts)

    async def get_consensus(self, game_id):
        # All 15 predict via hierarchical (efficient)
        all_predictions = await self.hierarchical.predict(game_id)

        # Select top 5 by recent performance
        top_5 = self.rank_experts(all_predictions)[:5]

        # Top 5 consensus via mesh (fast)
        mesh = MeshTopology(top_5)
        consensus = await mesh.vote()

        return {
            'consensus': consensus,
            'all_predictions': all_predictions
        }
```

**Performance Targets**:
- Consensus time: <100ms
- Accuracy: >62% ATS
- Communication: <50 messages

**Adaptive Trigger**:
- Mesh if top council ≤8
- Hierarchical if top council >8

---

#### 3. ML Model Training

**Current State**: 15 expert agents with RL

**Topology Choice**: **Ring AllReduce**

**Implementation**:
```python
class MLTrainingCoordinator:
    def __init__(self, expert_agents):
        self.ring = RingTopology(expert_agents)
        self.optimizer = torch.optim.Adam()

    async def training_epoch(self, historical_games):
        for batch in batches(historical_games):
            # Each expert computes local gradient
            gradients = await asyncio.gather(
                *[expert.forward_backward(batch)
                  for expert in self.ring.nodes]
            )

            # Ring AllReduce averages gradients efficiently
            avg_gradient = await self.ring.all_reduce(gradients)

            # Apply averaged gradient to all experts
            await asyncio.gather(
                *[expert.apply_gradient(avg_gradient)
                  for expert in self.ring.nodes]
            )
```

**Performance Targets**:
- Training time: <5 minutes per week
- Convergence: Visible after 4-6 weeks
- Cost: $0/month (CPU sufficient)

**Adaptive Trigger**: Switch to Hierarchical if >20 experts

---

#### 4. Real-Time Prediction Service

**Current State**: WebSocket live updates

**Topology Choice**: **Star + Redis Cache**

**Implementation**:
```python
class RealtimePredictionService:
    def __init__(self):
        self.cache = RedisCache()
        self.predictor = StarTopology([
            PredictionEngine(),
            ConfidenceCalculator(),
            RiskAssessor()
        ])

    async def predict(self, game_id):
        # Cache-first for speed
        cached = await self.cache.get(f"prediction:{game_id}")
        if cached:
            return cached  # <10ms

        # Generate via star topology (2 hops)
        prediction = await self.predictor.compute(game_id)

        # Cache for 5 minutes
        await self.cache.set(
            f"prediction:{game_id}",
            prediction,
            ttl=300
        )
        return prediction
```

**Performance Targets**:
- Latency: <500ms (P99)
- Cache hit rate: >80%
- Availability: 99.5%

**Adaptive Trigger**: Add read replicas (→ Hierarchical) if >1000 req/s

---

#### 5. Virtual Betting System

**Current State**: Expert bets with bankroll management

**Topology Choice**: **Star Centralized (NO ALTERNATIVES)**

**Implementation**:
```python
class CentralizedBettingSystem:
    def __init__(self):
        self.db = PostgreSQLDatabase()  # Single source of truth

    async def place_bet(self, expert_id, game_id, prediction):
        # ACID transaction - no distribution allowed
        async with self.db.transaction():
            # Get current bankroll
            bankroll = await self.db.get_bankroll(expert_id)

            # Calculate bet size
            bet_size = self.kelly_criterion(
                bankroll, prediction.confidence, prediction.odds
            )

            # Atomic update
            await self.db.deduct_bankroll(expert_id, bet_size)
            await self.db.record_bet(
                expert_id, game_id, bet_size, prediction
            )

        # NO COORDINATION - correctness required
```

**Performance Targets**:
- Consistency: 100% (ACID)
- Latency: <100ms (not real-time critical)
- Availability: 99.9%

**Adaptive Trigger**: NONE (always centralized)

---

## Performance Comparison by Topology

### Message Overhead

For 15 agents performing consensus:

| Topology | Messages | Overhead |
|----------|----------|----------|
| **Mesh** | 105 (all-to-all) | Very High |
| **Hierarchical** | 28 (tree depth 3) | Low |
| **Star** | 30 (hub relay) | Low |
| **Ring** | 15 (sequential) | Very Low |

### Latency

For 15 agents reaching agreement:

| Topology | Hops | Latency Estimate |
|----------|------|------------------|
| **Mesh** | 1 | 20ms (direct) |
| **Hierarchical** | 4 (log₂ 15) | 80ms (4 × 20ms) |
| **Star** | 2 | 40ms (2 × 20ms) |
| **Ring** | 8 (avg) | 160ms (8 × 20ms) |

### Scalability

Maximum practical team size:

| Topology | Max Agents | Limiting Factor |
|----------|-----------|-----------------|
| **Mesh** | 10-15 | O(n²) messages |
| **Hierarchical** | 100+ | Root bottleneck |
| **Star** | 20 | Hub capacity |
| **Ring** | 30 | Sequential latency |

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Using Mesh for Large Teams

**Problem**: 20 agents = 190 connections = communication explosion

**Solution**: Use Hierarchical for >10 agents

---

### ❌ Mistake 2: Using Star for Critical Systems

**Problem**: Hub failure brings down entire system

**Solution**: Use Mesh (small) or Hierarchical with failover

---

### ❌ Mistake 3: Using Ring for Real-Time

**Problem**: Sequential propagation causes high latency

**Solution**: Use Star or Hierarchical for <500ms requirement

---

### ❌ Mistake 4: Distributing ACID Transactions

**Problem**: Consistency impossible without centralized coordinator

**Solution**: Always use Star (centralized DB) for financial/betting

---

### ❌ Mistake 5: Static Topology Selection

**Problem**: Optimal topology changes as system evolves

**Solution**: Implement adaptive switching based on metrics

---

## Adaptive Switching Logic

```python
class AdaptiveTopologyCoordinator:
    def __init__(self, agents):
        self.agents = agents
        self.topology = self.select_initial_topology()

    def select_initial_topology(self):
        if len(self.agents) <= 5:
            return StarTopology(self.agents)
        elif len(self.agents) <= 10:
            return HierarchicalTopology(self.agents)
        else:
            return HierarchicalTopology(self.agents)

    async def monitor_and_adapt(self):
        while True:
            metrics = await self.collect_metrics()

            # Check for topology change triggers
            if self.should_switch_topology(metrics):
                new_topology = self.select_optimal_topology(metrics)
                await self.graceful_migration(new_topology)

            await asyncio.sleep(60)  # Check every minute

    def should_switch_topology(self, metrics):
        return (
            metrics.message_overhead > 10 or  # Too many messages
            metrics.latency_p99 > 500 or      # Too slow
            metrics.error_rate > 0.05 or      # Too many errors
            metrics.resource_usage > 0.85     # Resource exhausted
        )

    def select_optimal_topology(self, metrics):
        team_size = len(self.agents)

        if metrics.message_overhead > 10 and isinstance(self.topology, MeshTopology):
            # Mesh overhead too high
            return HierarchicalTopology(self.agents)

        elif metrics.latency_p99 > 500 and isinstance(self.topology, RingTopology):
            # Ring too slow
            return HierarchicalTopology(self.agents)

        elif team_size > 10 and isinstance(self.topology, StarTopology):
            # Star bottleneck
            return HierarchicalTopology(self.agents)

        return self.topology  # Keep current
```

---

## Summary: Quick Selection Rules

### Rule 1: Team Size Dominates

- **1-5 agents**: Star (unless critical → Mesh)
- **5-10 agents**: Star or Hierarchical
- **10-50 agents**: Hierarchical
- **50+ agents**: Hierarchical only

### Rule 2: Latency Matters

- **Real-time (<100ms)**: Star or Mesh
- **Interactive (<500ms)**: Star or Hierarchical
- **Batch (>1s)**: Any topology

### Rule 3: Reliability Trumps Efficiency

- **Must not fail**: Mesh (small) or Hierarchical with failover
- **Should not fail**: Hierarchical with backups
- **Can tolerate failures**: Star acceptable

### Rule 4: ACID = Centralized

- **Financial/Betting**: Always Star (no distribution)
- **Consistency critical**: Always Star
- **Eventual consistency OK**: Any topology

### Rule 5: When in Doubt

- **MVP/Prototype**: Start with Star (simplest)
- **Production**: Migrate to Hierarchical (scalable)
- **Critical small team**: Consider Mesh (resilient)

---

**Document Maintained By**: Research Agent
**Applied To**: NFL Predictor API Multi-Agent Coordination
**Last Updated**: 2025-09-30
**Status**: ✅ Complete - Ready for Implementation
