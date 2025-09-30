# MetaLearning Orchestrator AI - Complete System Design

**Status**: 🚧 In Development
**Version**: 1.0.0
**Last Updated**: 2025-09-30

---

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [Database Schema](#database-schema)
4. [Core Components](#core-components)
5. [API Endpoints](#api-endpoints)
6. [Integration](#integration)
7. [Deployment Strategy](#deployment-strategy)
8. [Testing Strategy](#testing-strategy)
9. [Security & Compliance](#security--compliance)
10. [Monitoring & Alerts](#monitoring--alerts)
11. [Cost Management](#cost-management)
12. [Edge Cases & Failure Handling](#edge-cases--failure-handling)

---

## Executive Summary

### 🎯 Purpose

The MetaLearning Orchestrator is an intelligent meta-layer that sits above the existing ML learning system (`AdaptiveLearningEngine`) to automatically optimize which prediction algorithms each expert uses.

### ✨ Key Capabilities

- **Automatic Model Testing**: Run multiple algorithm variants in parallel (shadow predictions)
- **Smart Selection**: Use Thompson Sampling to balance exploration vs exploitation
- **Statistical Rigor**: Chi-square and Mann-Whitney U tests with Bonferroni correction
- **Auto-Healing**: Exponential backoff retry + circuit breakers + intelligent fallbacks
- **Cost Optimization**: Real-time cost tracking with automatic throttling
- **Admin Intelligence**: ML-driven recommendations with ROI analysis
- **Zero Downtime**: Backwards compatible, gradual rollout, instant rollback capability

### 📊 Expected Outcomes

- **5-10% accuracy improvement** over 3 months through automated model optimization
- **30% cost reduction** through intelligent resource allocation
- **99.5%+ uptime** with auto-healing and circuit breakers
- **< 500ms prediction latency** (p95) with parallel execution
- **60%+ recommendation acceptance rate** from admins

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        User Request (Prediction)                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   MetaLearning Orchestrator                          │
│                                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────────┐│
│  │   Model     │  │  Experiment  │  │    Cost    │  │   Alert    ││
│  │  Registry   │  │   Manager    │  │  Tracker   │  │  System    ││
│  └─────────────┘  └──────────────┘  └────────────┘  └────────────┘│
│                                                                       │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────────┐│
│  │Auto-Healing │  │Recommendation│  │  Statistical Test Engine   ││
│  │   & Retry   │  │   Engine     │  │  (Chi-square, Mann-Whitney)││
│  └─────────────┘  └──────────────┘  └────────────────────────────┘│
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 Parallel Model Execution                             │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Champion    │  │ Challenger 1 │  │ Challenger 2 │   Shadow    │
│  │  Model       │  │   (Shadow)   │  │   (Shadow)   │   Mode      │
│  │  (Production)│  │              │  │              │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                  │                  │                       │
│         └──────────────────┴──────────────────┘                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Existing ML Learning System (Unchanged)                 │
│                                                                       │
│  ┌────────────────────────┐       ┌──────────────────────────────┐│
│  │ AdaptiveLearningEngine │       │  SupabaseEpisodicMemory      ││
│  │ - Gradient descent     │◄─────►│  - Pattern recognition       ││
│  │ - Weight optimization  │       │  - Historical experiences    ││
│  │ - Confidence calibrate │       │  - Factor success analysis   ││
│  └────────────────────────┘       └──────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  User receives │
                    │Champion pred.  │
                    └────────────────┘
```

### Layered Responsibility Model

| Layer | Responsibility | Timeframe |
|-------|---------------|-----------|
| **Orchestrator (Meta-Learning)** | Which algorithm should this expert use? | Weeks to months |
| **AdaptiveLearningEngine (Micro-Learning)** | What factor weights should this algorithm use? | Games to weeks |
| **Expert Model (Prediction)** | What's my prediction for this game? | Milliseconds |

---

## Database Schema

### Overview: 6 New Tables

1. `orchestrator_model_registry` - All model versions
2. `orchestrator_model_performance` - Every prediction made
3. `orchestrator_experiments` - A/B test management
4. `orchestrator_cost_tracking` - Resource usage
5. `orchestrator_failure_log` - Error tracking
6. `orchestrator_recommendations` - Admin suggestions

### 1. orchestrator_model_registry

**Purpose**: Version control for prediction models

```sql
CREATE TABLE orchestrator_model_registry (
    model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,  -- Semantic versioning "1.2.3"
    algorithm_type TEXT NOT NULL,
    -- Options: "gradient_descent", "adam", "bayesian", "neural_network", "ensemble"

    hyperparameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example: {"learning_rate": 0.01, "regularization": 0.1, "momentum": 0.9}

    is_active BOOLEAN DEFAULT false,
    is_champion BOOLEAN DEFAULT false,  -- Production model
    performance_threshold FLOAT,  -- Min accuracy to remain active (e.g., 0.52)

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT,  -- "orchestrator_auto" or "admin_manual"
    deployment_strategy TEXT,  -- "shadow", "canary", "full"
    rollback_to UUID REFERENCES orchestrator_model_registry(model_id),

    UNIQUE(expert_id, model_name, model_version)
);

CREATE INDEX idx_model_registry_expert ON orchestrator_model_registry(expert_id);
CREATE INDEX idx_model_registry_champion ON orchestrator_model_registry(expert_id, is_champion)
    WHERE is_champion = true;
```

**Model Lifecycle States**:
- `development`: Being tested in isolation
- `shadow`: Running predictions but not exposed to users
- `canary`: Exposed to 10% of traffic
- `champion`: Production model serving all traffic
- `deprecated`: No longer used, kept for historical analysis
- `failed`: Auto-disabled due to poor performance

### 2. orchestrator_model_performance

**Purpose**: Record every prediction made by every model

```sql
CREATE TABLE orchestrator_model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES orchestrator_model_registry(model_id),
    game_id UUID NOT NULL REFERENCES games(id),

    prediction_winner TEXT NOT NULL,
    prediction_confidence FLOAT NOT NULL,
    actual_winner TEXT,  -- NULL until game completes
    was_correct BOOLEAN,  -- NULL until game completes

    -- Performance metrics
    prediction_time_ms INTEGER,  -- How long to compute
    api_calls_made INTEGER DEFAULT 0,  -- Cost tracking
    tokens_used INTEGER DEFAULT 0,
    memory_used_mb INTEGER DEFAULT 0,

    -- Debugging
    error_occurred BOOLEAN DEFAULT false,
    error_message TEXT,
    factors_used JSONB,  -- Which factors influenced this prediction

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_model_perf_model ON orchestrator_model_performance(model_id);
CREATE INDEX idx_model_perf_game ON orchestrator_model_performance(game_id);
CREATE INDEX idx_model_perf_created ON orchestrator_model_performance(created_at DESC);
CREATE INDEX idx_model_perf_correct ON orchestrator_model_performance(model_id, was_correct)
    WHERE was_correct IS NOT NULL;
```

**Usage**:
- Calculate accuracy: `SELECT AVG(was_correct::int) FROM ... WHERE model_id = ?`
- Find slow predictions: `SELECT * FROM ... WHERE prediction_time_ms > 1000`
- Cost analysis: `SELECT SUM(api_calls_made * 0.01) FROM ... WHERE created_at > NOW() - INTERVAL '1 day'`

### 3. orchestrator_experiments

**Purpose**: Manage A/B/C/D tests between champion and challengers

```sql
CREATE TABLE orchestrator_experiments (
    experiment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    experiment_name TEXT NOT NULL,
    experiment_type TEXT NOT NULL,
    -- Options: "ab_test", "shadow", "canary", "multi_armed_bandit"

    champion_model_id UUID NOT NULL REFERENCES orchestrator_model_registry(model_id),
    challenger_models UUID[] NOT NULL,  -- Array of model_ids

    traffic_split JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Example: {"champion": 0.7, "challenger_1": 0.15, "challenger_2": 0.15}

    start_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    end_date TIMESTAMPTZ,
    status TEXT DEFAULT 'active',  -- "active", "concluded", "paused", "failed"

    -- Statistical testing config
    min_sample_size INTEGER DEFAULT 30,
    significance_level FLOAT DEFAULT 0.05,  -- p-value threshold

    -- Results
    results JSONB,
    -- Example: {
    --   "champion": {"wins": 45, "losses": 23, "accuracy": 0.662},
    --   "challenger_1": {"wins": 52, "losses": 18, "accuracy": 0.743},
    --   "statistical_test": {"test": "chi_square", "p_value": 0.012, "significant": true}
    -- }

    winner_model_id UUID REFERENCES orchestrator_model_registry(model_id),
    conclusion_reason TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by TEXT DEFAULT 'orchestrator_auto'
);

CREATE INDEX idx_experiments_expert ON orchestrator_experiments(expert_id);
CREATE INDEX idx_experiments_status ON orchestrator_experiments(status) WHERE status = 'active';
```

**Experiment Types**:
- **ab_test**: Fixed traffic split, run until statistical significance
- **shadow**: Challenger makes predictions but users never see them
- **canary**: Gradually increase challenger traffic (10% → 25% → 50% → 100%)
- **multi_armed_bandit**: Thompson Sampling adjusts traffic dynamically

### 4. orchestrator_cost_tracking

**Purpose**: Track resource usage and costs

```sql
CREATE TABLE orchestrator_cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_id UUID NOT NULL REFERENCES orchestrator_model_registry(model_id),
    game_id UUID REFERENCES games(id),

    cost_type TEXT NOT NULL,
    -- Options: "api_call", "computation", "storage", "llm_tokens"

    provider TEXT NOT NULL,
    -- Options: "odds_api", "sportsdata_io", "supabase", "openai", "internal"

    units_consumed INTEGER NOT NULL,  -- API calls, tokens, ms compute
    unit_cost_usd DECIMAL(10, 6),
    estimated_cost_usd DECIMAL(10, 6),

    metadata JSONB,  -- Additional context
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cost_tracking_expert ON orchestrator_cost_tracking(expert_id);
CREATE INDEX idx_cost_tracking_occurred ON orchestrator_cost_tracking(occurred_at DESC);
CREATE INDEX idx_cost_tracking_type ON orchestrator_cost_tracking(cost_type);

-- Materialized view for fast cost queries
CREATE MATERIALIZED VIEW orchestrator_cost_summary AS
SELECT
    expert_id,
    model_id,
    DATE_TRUNC('day', occurred_at) as date,
    cost_type,
    COUNT(*) as transaction_count,
    SUM(units_consumed) as total_units,
    SUM(estimated_cost_usd) as total_cost_usd
FROM orchestrator_cost_tracking
GROUP BY expert_id, model_id, DATE_TRUNC('day', occurred_at), cost_type;

CREATE INDEX idx_cost_summary_date ON orchestrator_cost_summary(date DESC);
```

**Budget Management**:
```sql
CREATE TABLE orchestrator_budget_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resource_type TEXT NOT NULL,
    -- Options: "api_calls_daily", "tokens_per_game", "cost_daily_usd", "cost_monthly_usd"

    limit_value DECIMAL(10, 2) NOT NULL,
    current_usage DECIMAL(10, 2) DEFAULT 0,

    reset_period TEXT DEFAULT 'daily',  -- "hourly", "daily", "weekly", "monthly"
    last_reset TIMESTAMPTZ DEFAULT NOW(),

    alert_threshold DECIMAL(3, 2) DEFAULT 0.8,  -- Alert at 80% usage
    auto_throttle BOOLEAN DEFAULT true,  -- Slow down when approaching limit

    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 5. orchestrator_failure_log

**Purpose**: Track all failures and recovery attempts

```sql
CREATE TABLE orchestrator_failure_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    expert_id TEXT NOT NULL,
    model_id UUID REFERENCES orchestrator_model_registry(model_id),
    game_id UUID REFERENCES games(id),

    failure_type TEXT NOT NULL,
    -- Options: "prediction_error", "api_timeout", "db_error", "validation_error",
    --          "circuit_breaker_open", "budget_exceeded"

    error_message TEXT NOT NULL,
    stack_trace TEXT,

    -- Retry tracking
    retry_attempt INTEGER DEFAULT 0,
    max_retries INTEGER,
    backoff_strategy TEXT,  -- "exponential", "linear", "constant"

    -- Recovery
    was_recovered BOOLEAN DEFAULT false,
    recovery_method TEXT,
    -- Options: "retry_success", "fallback_cache", "fallback_ensemble",
    --          "fallback_baseline", "manual_fix"

    recovered_at TIMESTAMPTZ,
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_failure_log_expert ON orchestrator_failure_log(expert_id);
CREATE INDEX idx_failure_log_type ON orchestrator_failure_log(failure_type);
CREATE INDEX idx_failure_log_occurred ON orchestrator_failure_log(occurred_at DESC);
CREATE INDEX idx_failure_log_unrecovered ON orchestrator_failure_log(was_recovered)
    WHERE was_recovered = false;
```

**Circuit Breaker State Table**:
```sql
CREATE TABLE orchestrator_circuit_breakers (
    expert_id TEXT PRIMARY KEY,
    state TEXT NOT NULL DEFAULT 'closed',  -- "closed", "open", "half_open"
    failure_count INTEGER DEFAULT 0,
    failure_threshold INTEGER DEFAULT 5,
    last_failure TIMESTAMPTZ,
    open_until TIMESTAMPTZ,
    timeout_ms INTEGER DEFAULT 60000,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 6. orchestrator_recommendations

**Purpose**: Auto-generated recommendations for admin

```sql
CREATE TABLE orchestrator_recommendations (
    recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_type TEXT NOT NULL,
    -- Options: "model_promotion", "expert_disable", "budget_increase",
    --          "experiment_start", "data_source_add", "hyperparameter_tune"

    priority TEXT DEFAULT 'medium',  -- "low", "medium", "high", "critical"

    expert_id TEXT,
    current_model_id UUID REFERENCES orchestrator_model_registry(model_id),
    suggested_model_id UUID REFERENCES orchestrator_model_registry(model_id),

    title TEXT NOT NULL,
    description TEXT NOT NULL,

    reasoning JSONB NOT NULL,
    -- Example: {
    --   "accuracy_gain": 0.087,
    --   "statistical_confidence": 0.977,
    --   "sample_size": 45,
    --   "evidence": ["Challenger won 52/70 games vs champion's 45/68"]
    -- }

    expected_impact JSONB,
    -- Example: {
    --   "accuracy_change": "+8.7%",
    --   "cost_change": "+$0.15/prediction",
    --   "latency_change": "+50ms",
    --   "roi": "2.3x"
    -- }

    status TEXT DEFAULT 'pending',  -- "pending", "accepted", "rejected", "auto_applied", "expired"
    auto_apply_after TIMESTAMPTZ,  -- Auto-apply if not reviewed by this time

    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT
);

CREATE INDEX idx_recommendations_status ON orchestrator_recommendations(status)
    WHERE status = 'pending';
CREATE INDEX idx_recommendations_priority ON orchestrator_recommendations(priority DESC);
CREATE INDEX idx_recommendations_expert ON orchestrator_recommendations(expert_id);
```

**Alert Rules Table**:
```sql
CREATE TABLE orchestrator_alert_rules (
    alert_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    -- Options: "accuracy_drop", "cost_spike", "error_rate", "latency",
    --          "expert_inactive", "budget_exceeded"

    condition_expression JSONB NOT NULL,
    -- Example: {"metric": "rolling_10_accuracy", "operator": "<", "threshold": 0.50}

    severity TEXT DEFAULT 'warning',  -- "info", "warning", "critical"
    notification_channels TEXT[] DEFAULT ARRAY['dashboard'],  -- ["email", "slack", "dashboard"]

    cooldown_minutes INTEGER DEFAULT 60,  -- Don't spam alerts
    last_triggered TIMESTAMPTZ,

    is_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orchestrator_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    alert_rule_id UUID REFERENCES orchestrator_alert_rules(alert_id),

    expert_id TEXT,
    model_id UUID REFERENCES orchestrator_model_registry(model_id),

    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,

    was_acknowledged BOOLEAN DEFAULT false,
    acknowledged_by TEXT,
    acknowledged_at TIMESTAMPTZ,

    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMPTZ,

    triggered_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_status ON orchestrator_alerts(was_acknowledged, resolved);
CREATE INDEX idx_alerts_severity ON orchestrator_alerts(severity) WHERE resolved = false;
```

---

## Core Components

### 1. MetaLearningOrchestrator (Main Engine)

**File**: `src/ml/meta_learning_orchestrator.py`

```python
class MetaLearningOrchestrator:
    """
    Meta-learning system that optimizes which models experts use.

    Responsibilities:
    1. Select which model variant to use for each prediction
    2. Execute predictions in parallel (champion + challengers)
    3. Record all results for statistical analysis
    4. Manage auto-healing and retry logic
    5. Generate recommendations for admin
    6. Track costs and enforce budgets
    """

    def __init__(self, supabase_client, config: OrchestratorConfig):
        self.supabase = supabase_client
        self.config = config

        # Initialize sub-components
        self.model_registry = ModelRegistry(supabase_client)
        self.experiment_manager = ExperimentManager(supabase_client)
        self.cost_tracker = CostTracker(supabase_client)
        self.alert_system = AlertSystem(supabase_client)
        self.recommendation_engine = RecommendationEngine(supabase_client)

        # Circuit breakers per expert
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Cache for frequently accessed data
        self.champion_cache: Dict[str, Model] = {}
        self.cache_ttl = 300  # 5 minutes

    async def orchestrate_prediction(
        self,
        expert_id: str,
        game_id: str,
        game_data: GameData
    ) -> Prediction:
        """
        Main entry point: orchestrates prediction with model selection and shadow testing.

        Flow:
        1. Check circuit breaker status
        2. Get champion and challenger models
        3. Execute predictions in parallel
        4. Record all predictions (shadow + champion)
        5. Track costs
        6. Return champion prediction to user (only this is visible)

        Args:
            expert_id: Which expert is making prediction
            game_id: Game being predicted
            game_data: All data needed for prediction

        Returns:
            Champion prediction (user-facing)

        Raises:
            CircuitBreakerOpen: If expert is disabled due to failures
            BudgetExceeded: If cost limit reached
        """

        # 1. Check circuit breaker
        if self.circuit_breakers.get(expert_id, CircuitBreaker()).is_open():
            logger.warning(f"Circuit breaker open for {expert_id}, using fallback")
            return await self._use_fallback_prediction(expert_id, game_data)

        # 2. Get champion model
        champion = await self._get_champion_model(expert_id)

        # 3. Get active challengers from experiments
        challengers = await self.experiment_manager.get_active_challengers(
            expert_id,
            max_challengers=self.config.max_challengers_per_expert
        )

        # 4. Execute predictions in parallel
        try:
            start_time = time.time()

            predictions = await self._parallel_predict(
                champion=champion,
                challengers=challengers,
                game_data=game_data,
                timeout=self.config.prediction_timeout_ms
            )

            prediction_time = (time.time() - start_time) * 1000  # ms

            # 5. Record all predictions
            for model, prediction in predictions.items():
                await self.model_registry.record_prediction(
                    model_id=model.model_id,
                    game_id=game_id,
                    prediction=prediction,
                    prediction_time_ms=prediction_time
                )

            # 6. Track costs
            await self.cost_tracker.record_prediction_cost(
                expert_id=expert_id,
                model_id=champion.model_id,
                game_id=game_id,
                api_calls=game_data.api_calls_made,
                tokens=game_data.tokens_used
            )

            # 7. Return champion prediction (only this is user-facing)
            return predictions[champion]

        except Exception as e:
            # 8. Auto-healing: retry with exponential backoff
            logger.error(f"Prediction failed for {expert_id}: {e}")
            return await self._handle_prediction_failure(
                expert_id, game_id, game_data, e
            )

    async def process_game_result(
        self,
        game_id: str,
        actual_winner: str
    ) -> None:
        """
        Process game result and update all models that made predictions.

        Flow:
        1. Get all predictions for this game
        2. Update performance metrics for each model
        3. Check if any experiments reached conclusion
        4. Generate recommendations if patterns detected
        5. Evaluate alert conditions
        6. Auto-apply high-confidence recommendations

        Args:
            game_id: Game that just completed
            actual_winner: Team that won
        """

        # 1. Get all predictions
        predictions = await self.model_registry.get_predictions_for_game(game_id)

        # 2. Update performance metrics
        for prediction in predictions:
            was_correct = (prediction.predicted_winner == actual_winner)

            await self.model_registry.update_performance(
                model_id=prediction.model_id,
                game_id=game_id,
                was_correct=was_correct
            )

        # 3. Check experiment conclusions
        concluded_experiments = await self.experiment_manager.check_conclusions()

        for experiment in concluded_experiments:
            logger.info(f"Experiment {experiment.experiment_id} concluded: {experiment.winner_model_id}")

            # Generate promotion recommendation if challenger won
            if experiment.winner_model_id != experiment.champion_model_id:
                await self.recommendation_engine.generate_promotion_recommendation(
                    experiment
                )

        # 4. Generate recommendations from patterns
        recommendations = await self.recommendation_engine.analyze_performance()

        # 5. Evaluate alert rules
        await self.alert_system.evaluate_rules()

        # 6. Auto-apply high-confidence recommendations
        for rec in recommendations:
            if rec.should_auto_apply():
                await self._auto_apply_recommendation(rec)

    async def _parallel_predict(
        self,
        champion: Model,
        challengers: List[Model],
        game_data: GameData,
        timeout: int
    ) -> Dict[Model, Prediction]:
        """
        Execute predictions in parallel using asyncio.gather().

        Returns predictions from all models (champion + challengers).
        If a challenger fails, it's excluded but doesn't fail the whole operation.
        """

        all_models = [champion] + challengers

        # Create prediction tasks
        tasks = [
            self._safe_predict(model, game_data)
            for model in all_models
        ]

        # Execute in parallel with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=timeout / 1000.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Predictions timed out after {timeout}ms")
            results = [None] * len(all_models)

        # Map models to their predictions
        predictions = {}
        for model, result in zip(all_models, results):
            if isinstance(result, Exception):
                logger.error(f"Model {model.model_id} failed: {result}")
                await self._log_failure(model.expert_id, model.model_id, result)
            elif result is not None:
                predictions[model] = result

        # Ensure we have at least champion prediction
        if champion not in predictions:
            raise Exception(f"Champion model {champion.model_id} failed")

        return predictions

    async def _handle_prediction_failure(
        self,
        expert_id: str,
        game_id: str,
        game_data: GameData,
        error: Exception
    ) -> Prediction:
        """
        Retry logic with exponential backoff and fallback strategies.

        Retry Strategy:
        1. Exponential backoff: 1s, 2s, 4s
        2. If all retries fail, use fallback:
           a) Cached prediction from similar game
           b) Ensemble average from other experts
           c) Historical baseline (50% + home advantage)
        3. Log failure and alert admin
        4. Update circuit breaker
        """

        retry_policy = await self._get_retry_policy(type(error).__name__)

        for attempt in range(retry_policy.max_retries):
            delay = retry_policy.get_delay(attempt)
            await asyncio.sleep(delay / 1000.0)

            try:
                logger.info(f"Retry {attempt + 1}/{retry_policy.max_retries} for {expert_id}")

                # Retry prediction
                champion = await self._get_champion_model(expert_id)
                result = await self._safe_predict(champion, game_data)

                if result:
                    # Success! Record recovery
                    await self._log_failure_recovery(
                        expert_id, game_id, attempt, "retry_success"
                    )
                    return result

            except Exception as retry_error:
                logger.error(f"Retry {attempt + 1} failed: {retry_error}")

        # All retries failed, use fallback
        logger.error(f"All retries failed for {expert_id}, using fallback")

        # Update circuit breaker
        if expert_id not in self.circuit_breakers:
            self.circuit_breakers[expert_id] = CircuitBreaker()
        self.circuit_breakers[expert_id].record_failure()

        # Alert admin
        await self.alert_system.trigger_alert(
            alert_type="prediction_failure",
            expert_id=expert_id,
            severity="critical",
            message=f"Expert {expert_id} failed after {retry_policy.max_retries} retries"
        )

        # Use fallback
        return await self._use_fallback_prediction(expert_id, game_data)

    async def _use_fallback_prediction(
        self,
        expert_id: str,
        game_data: GameData
    ) -> Prediction:
        """
        Fallback strategies when all else fails.

        Priority order:
        1. Cached prediction from similar past game
        2. Ensemble average from other working experts
        3. Historical baseline (home team favored 55%)
        """

        # Try cache
        cached = await self._get_cached_similar_prediction(expert_id, game_data)
        if cached:
            logger.info(f"Using cached prediction for {expert_id}")
            await self._log_failure_recovery(
                expert_id, game_data.game_id, 0, "fallback_cache"
            )
            return cached

        # Try ensemble
        ensemble = await self._get_ensemble_prediction(game_data)
        if ensemble:
            logger.info(f"Using ensemble average for {expert_id}")
            await self._log_failure_recovery(
                expert_id, game_data.game_id, 0, "fallback_ensemble"
            )
            return ensemble

        # Use baseline
        logger.info(f"Using baseline prediction for {expert_id}")
        await self._log_failure_recovery(
            expert_id, game_data.game_id, 0, "fallback_baseline"
        )
        return self._get_baseline_prediction(game_data)
```

### 2. ModelRegistry

**File**: `src/ml/model_registry.py`

```python
class ModelRegistry:
    """
    CRUD operations for model versions.

    Responsibilities:
    - Register new models
    - Get champion model for expert
    - Get all models for expert
    - Update model status (activate, deprecate, fail)
    - Record predictions
    - Query performance metrics
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def register_model(
        self,
        expert_id: str,
        model_name: str,
        model_version: str,
        algorithm_type: str,
        hyperparameters: Dict[str, Any],
        deployment_strategy: str = "shadow"
    ) -> Model:
        """
        Register a new model version.

        Example:
            await registry.register_model(
                expert_id="conservative_analyzer",
                model_name="gradient_descent",
                model_version="1.2.0",
                algorithm_type="gradient_descent",
                hyperparameters={"learning_rate": 0.03, "regularization": 0.1},
                deployment_strategy="shadow"
            )
        """

        model_data = {
            'expert_id': expert_id,
            'model_name': model_name,
            'model_version': model_version,
            'algorithm_type': algorithm_type,
            'hyperparameters': hyperparameters,
            'is_active': deployment_strategy in ['shadow', 'canary', 'full'],
            'is_champion': False,  # Must be promoted separately
            'deployment_strategy': deployment_strategy,
            'created_by': 'orchestrator_auto',
            'created_at': datetime.utcnow().isoformat()
        }

        result = self.supabase.table('orchestrator_model_registry') \
            .insert(model_data) \
            .execute()

        return Model.from_dict(result.data[0])

    async def get_champion(self, expert_id: str) -> Model:
        """Get the current champion (production) model for an expert."""

        result = self.supabase.table('orchestrator_model_registry') \
            .select('*') \
            .eq('expert_id', expert_id) \
            .eq('is_champion', True) \
            .execute()

        if not result.data:
            raise Exception(f"No champion model found for {expert_id}")

        return Model.from_dict(result.data[0])

    async def promote_to_champion(
        self,
        model_id: str,
        demote_current: bool = True
    ) -> None:
        """
        Promote a model to champion status.

        Args:
            model_id: Model to promote
            demote_current: If True, demote current champion to deprecated
        """

        # Get model being promoted
        model = await self.get_model(model_id)

        if demote_current:
            # Demote current champion
            current_champion = await self.get_champion(model.expert_id)
            await self.update_model_status(
                current_champion.model_id,
                is_champion=False,
                deployment_strategy="deprecated"
            )

        # Promote new champion
        await self.update_model_status(
            model_id,
            is_champion=True,
            is_active=True,
            deployment_strategy="full"
        )

        logger.info(f"Promoted {model_id} to champion for {model.expert_id}")

    async def record_prediction(
        self,
        model_id: str,
        game_id: str,
        prediction: Prediction,
        prediction_time_ms: int
    ) -> None:
        """Record a prediction made by a model."""

        perf_data = {
            'model_id': model_id,
            'game_id': game_id,
            'prediction_winner': prediction.winner,
            'prediction_confidence': prediction.winner_confidence,
            'prediction_time_ms': prediction_time_ms,
            'api_calls_made': prediction.api_calls_made,
            'tokens_used': prediction.tokens_used,
            'factors_used': prediction.key_factors,
            'created_at': datetime.utcnow().isoformat()
        }

        self.supabase.table('orchestrator_model_performance') \
            .insert(perf_data) \
            .execute()

    async def update_performance(
        self,
        model_id: str,
        game_id: str,
        was_correct: bool
    ) -> None:
        """Update prediction performance after game completes."""

        self.supabase.table('orchestrator_model_performance') \
            .update({
                'was_correct': was_correct,
                'actual_winner': actual_winner
            }) \
            .eq('model_id', model_id) \
            .eq('game_id', game_id) \
            .execute()

    async def get_model_accuracy(
        self,
        model_id: str,
        since: datetime = None,
        min_games: int = 10
    ) -> Optional[float]:
        """
        Calculate model accuracy.

        Returns None if insufficient games.
        """

        query = self.supabase.table('orchestrator_model_performance') \
            .select('was_correct') \
            .eq('model_id', model_id) \
            .not_.is_('was_correct', 'null')

        if since:
            query = query.gte('created_at', since.isoformat())

        result = query.execute()

        if len(result.data) < min_games:
            return None

        correct_count = sum(1 for r in result.data if r['was_correct'])
        return correct_count / len(result.data)
```

### 3. ExperimentManager

**File**: `src/ml/experiment_manager.py`

```python
class ExperimentManager:
    """
    A/B test lifecycle management.

    Responsibilities:
    - Create experiments
    - Allocate traffic using Thompson Sampling
    - Check statistical significance
    - Conclude experiments
    - Generate winner reports
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def create_experiment(
        self,
        expert_id: str,
        experiment_name: str,
        champion_model_id: str,
        challenger_model_ids: List[str],
        experiment_type: str = "multi_armed_bandit",
        min_sample_size: int = 30
    ) -> Experiment:
        """
        Create a new A/B test experiment.

        Example:
            await exp_mgr.create_experiment(
                expert_id="conservative_analyzer",
                experiment_name="test_higher_learning_rate",
                champion_model_id=champion.model_id,
                challenger_model_ids=[challenger.model_id],
                experiment_type="multi_armed_bandit",
                min_sample_size=30
            )
        """

        exp_data = {
            'expert_id': expert_id,
            'experiment_name': experiment_name,
            'experiment_type': experiment_type,
            'champion_model_id': champion_model_id,
            'challenger_models': challenger_model_ids,
            'traffic_split': self._initial_traffic_split(len(challenger_model_ids)),
            'start_date': datetime.utcnow().isoformat(),
            'status': 'active',
            'min_sample_size': min_sample_size,
            'created_by': 'orchestrator_auto'
        }

        result = self.supabase.table('orchestrator_experiments') \
            .insert(exp_data) \
            .execute()

        return Experiment.from_dict(result.data[0])

    async def get_active_challengers(
        self,
        expert_id: str,
        max_challengers: int = 3
    ) -> List[Model]:
        """
        Get challenger models that should make predictions for this expert.

        Uses Thompson Sampling to decide which challengers to run.
        """

        # Get active experiments
        experiments = await self._get_active_experiments(expert_id)

        if not experiments:
            return []

        # Collect all challengers from all experiments
        all_challengers = []
        for exp in experiments:
            for challenger_id in exp.challenger_models:
                # Get model performance
                wins, losses = await self._get_model_wins_losses(challenger_id)

                # Thompson Sampling: sample from Beta distribution
                sample = np.random.beta(wins + 1, losses + 1)

                all_challengers.append({
                    'model_id': challenger_id,
                    'sample': sample,
                    'wins': wins,
                    'losses': losses
                })

        # Sort by sample value (highest first)
        all_challengers.sort(key=lambda x: x['sample'], reverse=True)

        # Return top N challengers
        selected = all_challengers[:max_challengers]

        # Load full model objects
        models = []
        for c in selected:
            model = await self.model_registry.get_model(c['model_id'])
            models.append(model)

        return models

    async def check_conclusions(self) -> List[Experiment]:
        """
        Check if any experiments have reached statistical significance.

        Runs statistical tests (Chi-square) on all active experiments.
        Concludes experiments where p < 0.05 and sample size >= min.
        """

        experiments = await self._get_all_active_experiments()
        concluded = []

        for exp in experiments:
            # Get performance data for all models
            champion_results = await self._get_model_results(exp.champion_model_id, exp.start_date)

            challenger_results_list = []
            for challenger_id in exp.challenger_models:
                results = await self._get_model_results(challenger_id, exp.start_date)
                challenger_results_list.append((challenger_id, results))

            # Check sample size
            if len(champion_results) < exp.min_sample_size:
                continue

            # Run statistical tests
            for challenger_id, challenger_results in challenger_results_list:
                if len(challenger_results) < exp.min_sample_size:
                    continue

                # Chi-square test
                p_value = self._chi_square_test(champion_results, challenger_results)

                if p_value < exp.significance_level:
                    # Statistically significant difference found!

                    champion_acc = np.mean(champion_results)
                    challenger_acc = np.mean(challenger_results)

                    winner_model_id = challenger_id if challenger_acc > champion_acc else exp.champion_model_id

                    # Conclude experiment
                    await self._conclude_experiment(
                        exp.experiment_id,
                        winner_model_id=winner_model_id,
                        results={
                            'champion': {
                                'accuracy': float(champion_acc),
                                'sample_size': len(champion_results)
                            },
                            'challenger': {
                                'model_id': challenger_id,
                                'accuracy': float(challenger_acc),
                                'sample_size': len(challenger_results)
                            },
                            'statistical_test': {
                                'test': 'chi_square',
                                'p_value': float(p_value),
                                'significant': True
                            }
                        },
                        conclusion_reason=f"Statistical significance reached (p={p_value:.4f})"
                    )

                    concluded.append(exp)
                    break

        return concluded

    def _chi_square_test(
        self,
        champion_results: List[bool],
        challenger_results: List[bool]
    ) -> float:
        """
        Chi-square test for difference in accuracy.

        H0: Both models have the same accuracy
        H1: Models have different accuracy

        Returns p-value.
        """

        from scipy.stats import chi2_contingency

        # Contingency table
        champion_correct = sum(champion_results)
        champion_incorrect = len(champion_results) - champion_correct

        challenger_correct = sum(challenger_results)
        challenger_incorrect = len(challenger_results) - challenger_correct

        table = [
            [champion_correct, champion_incorrect],
            [challenger_correct, challenger_incorrect]
        ]

        chi2, p_value, dof, expected = chi2_contingency(table)

        return p_value
```

### 4. CostTracker

**File**: `src/ml/cost_tracker.py`

```python
class CostTracker:
    """
    Track resource usage and enforce budget limits.

    Responsibilities:
    - Record costs per prediction
    - Calculate daily/weekly/monthly totals
    - Enforce budget limits
    - Generate cost reports
    - Alert on cost spikes
    """

    # Cost constants (update based on actual pricing)
    COST_PER_API_CALL = {
        'odds_api': 0.01,
        'sportsdata_io': 0.005,
        'rapidapi': 0.02
    }

    COST_PER_TOKEN = 0.00001  # $0.01 per 1000 tokens
    COST_PER_COMPUTE_MS = 0.000001  # $0.001 per 1000ms

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def record_prediction_cost(
        self,
        expert_id: str,
        model_id: str,
        game_id: str,
        api_calls: Dict[str, int],
        tokens: int,
        compute_ms: int = 0
    ) -> None:
        """
        Record costs for a single prediction.

        Args:
            api_calls: {"odds_api": 1, "sportsdata_io": 2}
            tokens: Number of LLM tokens used
            compute_ms: Computation time in milliseconds
        """

        cost_entries = []

        # API call costs
        for provider, count in api_calls.items():
            if count > 0:
                unit_cost = self.COST_PER_API_CALL.get(provider, 0.01)
                cost_entries.append({
                    'expert_id': expert_id,
                    'model_id': model_id,
                    'game_id': game_id,
                    'cost_type': 'api_call',
                    'provider': provider,
                    'units_consumed': count,
                    'unit_cost_usd': unit_cost,
                    'estimated_cost_usd': count * unit_cost,
                    'occurred_at': datetime.utcnow().isoformat()
                })

        # Token costs
        if tokens > 0:
            token_cost = tokens * self.COST_PER_TOKEN
            cost_entries.append({
                'expert_id': expert_id,
                'model_id': model_id,
                'game_id': game_id,
                'cost_type': 'llm_tokens',
                'provider': 'openai',
                'units_consumed': tokens,
                'unit_cost_usd': self.COST_PER_TOKEN,
                'estimated_cost_usd': token_cost,
                'occurred_at': datetime.utcnow().isoformat()
            })

        # Compute costs
        if compute_ms > 0:
            compute_cost = compute_ms * self.COST_PER_COMPUTE_MS
            cost_entries.append({
                'expert_id': expert_id,
                'model_id': model_id,
                'game_id': game_id,
                'cost_type': 'computation',
                'provider': 'internal',
                'units_consumed': compute_ms,
                'unit_cost_usd': self.COST_PER_COMPUTE_MS,
                'estimated_cost_usd': compute_cost,
                'occurred_at': datetime.utcnow().isoformat()
            })

        # Batch insert
        if cost_entries:
            self.supabase.table('orchestrator_cost_tracking') \
                .insert(cost_entries) \
                .execute()

    async def get_daily_cost(
        self,
        expert_id: Optional[str] = None,
        date: datetime = None
    ) -> float:
        """Get total cost for a specific day."""

        if date is None:
            date = datetime.utcnow()

        start = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)

        query = self.supabase.table('orchestrator_cost_tracking') \
            .select('estimated_cost_usd') \
            .gte('occurred_at', start.isoformat()) \
            .lt('occurred_at', end.isoformat())

        if expert_id:
            query = query.eq('expert_id', expert_id)

        result = query.execute()

        total = sum(r['estimated_cost_usd'] for r in result.data)
        return float(total)

    async def check_budget_limits(self) -> List[BudgetAlert]:
        """
        Check if any budget limits are being approached or exceeded.

        Returns alerts for budgets at 80%+ usage.
        """

        alerts = []

        # Get all active budget limits
        result = self.supabase.table('orchestrator_budget_limits') \
            .select('*') \
            .eq('is_active', True) \
            .execute()

        for limit in result.data:
            # Calculate current usage
            current = await self._calculate_current_usage(limit)

            # Update current usage
            await self._update_budget_usage(limit['id'], current)

            # Check threshold
            utilization = current / limit['limit_value']

            if utilization >= limit['alert_threshold']:
                alerts.append(BudgetAlert(
                    resource_type=limit['resource_type'],
                    limit_value=limit['limit_value'],
                    current_usage=current,
                    utilization=utilization,
                    should_throttle=limit['auto_throttle'] and utilization >= 0.9
                ))

        return alerts

    async def enforce_budget_limit(
        self,
        expert_id: str
    ) -> bool:
        """
        Check if expert has budget remaining.

        Returns False if budget exceeded, True otherwise.
        """

        daily_cost = await self.get_daily_cost(expert_id=expert_id)

        # Get budget limit
        result = self.supabase.table('orchestrator_budget_limits') \
            .select('*') \
            .eq('resource_type', 'cost_daily_usd') \
            .eq('is_active', True) \
            .execute()

        if not result.data:
            return True  # No limit set

        limit = result.data[0]

        return daily_cost < limit['limit_value']
```

### 5. AlertSystem

**File**: `src/ml/alert_system.py`

```python
class AlertSystem:
    """
    Real-time monitoring and alerting.

    Responsibilities:
    - Evaluate alert rules
    - Trigger notifications (email, slack, dashboard)
    - Manage alert cooldowns
    - Track alert acknowledgments
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self.last_triggered = {}  # For cooldown tracking

    async def evaluate_rules(self) -> List[Alert]:
        """
        Evaluate all active alert rules.

        Called after each game result to check conditions.
        """

        alerts = []

        # Get all active rules
        result = self.supabase.table('orchestrator_alert_rules') \
            .select('*') \
            .eq('is_enabled', True) \
            .execute()

        for rule in result.data:
            # Check cooldown
            if self._is_in_cooldown(rule):
                continue

            # Evaluate condition
            if await self._evaluate_condition(rule):
                alert = await self._trigger_alert(rule)
                alerts.append(alert)

        return alerts

    async def trigger_alert(
        self,
        alert_type: str,
        expert_id: str,
        severity: str,
        message: str,
        details: Dict[str, Any] = None
    ) -> Alert:
        """
        Manually trigger an alert (for programmatic alerts).
        """

        alert_data = {
            'alert_rule_id': None,  # Manual alert
            'expert_id': expert_id,
            'severity': severity,
            'message': message,
            'details': details or {},
            'triggered_at': datetime.utcnow().isoformat()
        }

        result = self.supabase.table('orchestrator_alerts') \
            .insert(alert_data) \
            .execute()

        alert = Alert.from_dict(result.data[0])

        # Send notifications
        await self._send_notifications(alert, ['dashboard', 'email'])

        return alert

    async def _evaluate_condition(self, rule: Dict) -> bool:
        """
        Evaluate if alert condition is met.

        Condition format:
        {
            "metric": "rolling_10_accuracy",
            "operator": "<",
            "threshold": 0.50,
            "expert_id": "conservative_analyzer"  # optional
        }
        """

        condition = rule['condition_expression']
        metric = condition['metric']
        operator = condition['operator']
        threshold = condition['threshold']
        expert_id = condition.get('expert_id')

        # Calculate metric value
        value = await self._calculate_metric(metric, expert_id)

        # Evaluate condition
        if operator == '<':
            return value < threshold
        elif operator == '>':
            return value > threshold
        elif operator == '<=':
            return value <= threshold
        elif operator == '>=':
            return value >= threshold
        elif operator == '==':
            return value == threshold
        else:
            logger.error(f"Unknown operator: {operator}")
            return False

    async def _calculate_metric(
        self,
        metric: str,
        expert_id: Optional[str]
    ) -> float:
        """
        Calculate metric value.

        Supported metrics:
        - rolling_10_accuracy: Accuracy over last 10 games
        - error_rate: Percentage of failed predictions
        - latency_p95: 95th percentile prediction time
        - daily_cost: Total cost today
        """

        if metric == 'rolling_10_accuracy':
            # Get last 10 predictions for expert
            query = self.supabase.table('orchestrator_model_performance') \
                .select('was_correct') \
                .not_.is_('was_correct', 'null') \
                .order('created_at', desc=True) \
                .limit(10)

            if expert_id:
                # Get champion model for this expert
                champion = await self.model_registry.get_champion(expert_id)
                query = query.eq('model_id', champion.model_id)

            result = query.execute()

            if len(result.data) < 10:
                return 0.5  # Not enough data

            correct = sum(1 for r in result.data if r['was_correct'])
            return correct / len(result.data)

        elif metric == 'error_rate':
            # Percentage of failed predictions in last hour
            since = datetime.utcnow() - timedelta(hours=1)

            failures = self.supabase.table('orchestrator_model_performance') \
                .select('id') \
                .eq('error_occurred', True) \
                .gte('created_at', since.isoformat()) \
                .execute()

            total = self.supabase.table('orchestrator_model_performance') \
                .select('id') \
                .gte('created_at', since.isoformat()) \
                .execute()

            if len(total.data) == 0:
                return 0.0

            return len(failures.data) / len(total.data)

        elif metric == 'daily_cost':
            return await self.cost_tracker.get_daily_cost(expert_id=expert_id)

        else:
            logger.error(f"Unknown metric: {metric}")
            return 0.0
```

### 6. RecommendationEngine

**File**: `src/ml/recommendation_engine.py`

```python
class RecommendationEngine:
    """
    Generate ML-driven recommendations for admin.

    Responsibilities:
    - Detect patterns in model performance
    - Generate promotion recommendations
    - Suggest new experiments
    - Calculate ROI for changes
    - Auto-apply high-confidence recommendations
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def analyze_performance(self) -> List[Recommendation]:
        """
        Analyze all experts and generate recommendations.

        Run daily to find opportunities for improvement.
        """

        recommendations = []

        # Get all experts
        experts = await self._get_all_experts()

        for expert_id in experts:
            # Check for underperforming experts
            rec = await self._check_underperformance(expert_id)
            if rec:
                recommendations.append(rec)

            # Check for plateau (no improvement in 30 games)
            rec = await self._check_plateau(expert_id)
            if rec:
                recommendations.append(rec)

            # Check for cost optimization opportunities
            rec = await self._check_cost_optimization(expert_id)
            if rec:
                recommendations.append(rec)

        # Save recommendations
        for rec in recommendations:
            await self._save_recommendation(rec)

        return recommendations

    async def generate_promotion_recommendation(
        self,
        experiment: Experiment
    ) -> Recommendation:
        """
        Generate recommendation to promote winning model.

        Called when experiment concludes with statistical significance.
        """

        # Get experiment results
        results = experiment.results

        champion_acc = results['champion']['accuracy']
        challenger_acc = results['challenger']['accuracy']

        accuracy_gain = challenger_acc - champion_acc

        # Calculate expected impact
        # Assume 100 games per week
        games_per_week = 100
        accuracy_points_gained = accuracy_gain * games_per_week

        # Estimate value per accuracy point ($10)
        value_per_point = 10.0
        weekly_value = accuracy_points_gained * value_per_point

        # Get cost difference
        champion_cost = await self._get_model_cost(experiment.champion_model_id)
        challenger_cost = await self._get_model_cost(results['challenger']['model_id'])
        cost_diff = challenger_cost - champion_cost

        # Calculate ROI
        if cost_diff > 0:
            roi = weekly_value / cost_diff
        else:
            roi = float('inf')  # Free improvement!

        rec = Recommendation(
            recommendation_type='model_promotion',
            priority='high' if accuracy_gain > 0.05 else 'medium',
            expert_id=experiment.expert_id,
            current_model_id=experiment.champion_model_id,
            suggested_model_id=results['challenger']['model_id'],
            title=f"Promote {results['challenger']['model_id']} for {experiment.expert_id}",
            description=f"Challenger model showed {accuracy_gain*100:.1f}% accuracy improvement with statistical significance (p={results['statistical_test']['p_value']:.4f})",
            reasoning={
                'accuracy_gain': accuracy_gain,
                'statistical_confidence': 1 - results['statistical_test']['p_value'],
                'sample_size': results['challenger']['sample_size'],
                'evidence': [f"Challenger: {challenger_acc*100:.1f}% vs Champion: {champion_acc*100:.1f}%"]
            },
            expected_impact={
                'accuracy_change': f"+{accuracy_gain*100:.1f}%",
                'cost_change': f"+${cost_diff:.2f}/prediction" if cost_diff > 0 else f"-${abs(cost_diff):.2f}/prediction",
                'roi': f"{roi:.1f}x",
                'weekly_value': f"${weekly_value:.2f}"
            },
            auto_apply_after=datetime.utcnow() + timedelta(hours=24)  # Auto-apply in 24h
        )

        await self._save_recommendation(rec)

        return rec

    async def _check_underperformance(
        self,
        expert_id: str
    ) -> Optional[Recommendation]:
        """
        Check if expert is performing below 48% accuracy.

        Recommend disabling until model improves.
        """

        champion = await self.model_registry.get_champion(expert_id)
        accuracy = await self.model_registry.get_model_accuracy(
            champion.model_id,
            min_games=20
        )

        if accuracy and accuracy < 0.48:
            return Recommendation(
                recommendation_type='expert_disable',
                priority='critical',
                expert_id=expert_id,
                current_model_id=champion.model_id,
                title=f"Disable {expert_id} - performing worse than coin flip",
                description=f"Current accuracy: {accuracy*100:.1f}% over last 20 games. Below 48% threshold.",
                reasoning={
                    'accuracy': accuracy,
                    'threshold': 0.48,
                    'sample_size': 20
                },
                expected_impact={
                    'user_experience': "Prevent confusion from poor predictions"
                },
                auto_apply_after=datetime.utcnow() + timedelta(hours=48)
            )

        return None

    async def _check_plateau(
        self,
        expert_id: str
    ) -> Optional[Recommendation]:
        """
        Check if expert accuracy has plateaued.

        Recommend starting experiment with new algorithm.
        """

        champion = await self.model_registry.get_champion(expert_id)

        # Get accuracy trend over last 30 games
        recent_30 = await self._get_accuracy_trend(champion.model_id, 30)

        if not recent_30 or len(recent_30) < 30:
            return None

        # Check if flat (no improvement)
        first_10 = np.mean(recent_30[:10])
        last_10 = np.mean(recent_30[-10:])
        improvement = last_10 - first_10

        if abs(improvement) < 0.02:  # Less than 2% change
            return Recommendation(
                recommendation_type='experiment_start',
                priority='medium',
                expert_id=expert_id,
                current_model_id=champion.model_id,
                title=f"Start experiment for {expert_id} - accuracy plateaued",
                description=f"No significant improvement over last 30 games ({first_10*100:.1f}% → {last_10*100:.1f}%). Try alternative algorithm.",
                reasoning={
                    'improvement': improvement,
                    'sample_size': 30,
                    'plateau_threshold': 0.02
                },
                expected_impact={
                    'potential_gain': "5-10% accuracy improvement",
                    'risk': "Low (shadow testing)"
                },
                auto_apply_after=datetime.utcnow() + timedelta(days=7)
            )

        return None
```

---

## API Endpoints

**File**: `src/api/orchestrator_endpoints.py`

### Dashboard Overview

```python
@app.get("/api/orchestrator/dashboard")
async def get_dashboard():
    """
    Main dashboard overview.

    Returns platform health, active experiments, pending recommendations, alerts.
    """

    orchestrator = MetaLearningOrchestrator(supabase)

    # Platform health
    error_rate = await orchestrator.alert_system._calculate_metric('error_rate', None)
    health = "healthy" if error_rate < 0.05 else ("degraded" if error_rate < 0.15 else "critical")

    # Active experiments
    experiments = await orchestrator.experiment_manager._get_all_active_experiments()

    # Pending recommendations
    pending_recs = await supabase.table('orchestrator_recommendations') \
        .select('*') \
        .eq('status', 'pending') \
        .execute()

    # Active alerts
    active_alerts = await supabase.table('orchestrator_alerts') \
        .select('*') \
        .eq('was_acknowledged', False) \
        .eq('resolved', False) \
        .execute()

    # Expert summaries
    experts = await get_all_expert_ids()
    expert_summaries = []

    for expert_id in experts:
        try:
            champion = await orchestrator.model_registry.get_champion(expert_id)
            accuracy = await orchestrator.model_registry.get_model_accuracy(champion.model_id)

            # Get prediction count today
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
            pred_count = await supabase.table('orchestrator_model_performance') \
                .select('id', count='exact') \
                .eq('model_id', champion.model_id) \
                .gte('created_at', today_start.isoformat()) \
                .execute()

            expert_summaries.append({
                'expert_id': expert_id,
                'status': 'healthy' if accuracy and accuracy > 0.52 else 'degraded',
                'current_model': f"{champion.model_name}_v{champion.model_version}",
                'accuracy_7d': accuracy,
                'predictions_today': pred_count.count
            })
        except Exception as e:
            logger.error(f"Error getting expert summary for {expert_id}: {e}")

    # Cost summary
    daily_cost = await orchestrator.cost_tracker.get_daily_cost()
    budget = await get_daily_budget()

    return {
        'platform_health': health,
        'active_experiments': len(experiments),
        'pending_recommendations': len(pending_recs.data),
        'active_alerts': len(active_alerts.data),
        'experts': expert_summaries,
        'cost_summary': {
            'today': daily_cost,
            'budget': budget,
            'utilization': daily_cost / budget if budget > 0 else 0
        }
    }
```

### Expert Detail View

```python
@app.get("/api/orchestrator/experts/{expert_id}")
async def get_expert_detail(expert_id: str):
    """
    Detailed view of single expert.

    Returns champion model, challengers, experiments, performance history, costs.
    """

    orchestrator = MetaLearningOrchestrator(supabase)

    # Champion model
    champion = await orchestrator.model_registry.get_champion(expert_id)

    # Active challengers
    challengers = await orchestrator.experiment_manager.get_active_challengers(expert_id)

    # Active experiments
    experiments = await orchestrator.experiment_manager._get_active_experiments(expert_id)

    # Performance history (last 50 games)
    history = await supabase.table('orchestrator_model_performance') \
        .select('*') \
        .eq('model_id', champion.model_id) \
        .not_.is_('was_correct', 'null') \
        .order('created_at', desc=True) \
        .limit(50) \
        .execute()

    # Cost breakdown
    cost_7d = await orchestrator.cost_tracker.get_daily_cost(expert_id=expert_id)

    return {
        'expert_id': expert_id,
        'champion_model': champion.to_dict(),
        'challenger_models': [c.to_dict() for c in challengers],
        'active_experiments': [e.to_dict() for e in experiments],
        'performance_history': history.data,
        'cost_7d': cost_7d
    }
```

### Model Comparison

```python
@app.get("/api/orchestrator/models/compare")
async def compare_models(model_ids: str):
    """
    Compare performance of multiple models.

    Query param: model_ids=id1,id2,id3
    """

    model_id_list = model_ids.split(',')

    orchestrator = MetaLearningOrchestrator(supabase)

    comparisons = []

    for model_id in model_id_list:
        model = await orchestrator.model_registry.get_model(model_id)
        accuracy = await orchestrator.model_registry.get_model_accuracy(model_id)

        # Get prediction count
        perf = await supabase.table('orchestrator_model_performance') \
            .select('*') \
            .eq('model_id', model_id) \
            .not_.is_('was_correct', 'null') \
            .execute()

        # Average confidence
        avg_conf = np.mean([p['prediction_confidence'] for p in perf.data]) if perf.data else 0

        # Cost per prediction
        cost_data = await supabase.table('orchestrator_cost_tracking') \
            .select('estimated_cost_usd') \
            .eq('model_id', model_id) \
            .execute()

        total_cost = sum(c['estimated_cost_usd'] for c in cost_data.data)
        cost_per_pred = total_cost / len(perf.data) if perf.data else 0

        comparisons.append({
            'model_id': model_id,
            'model_name': model.model_name,
            'model_version': model.model_version,
            'accuracy': accuracy,
            'sample_size': len(perf.data),
            'avg_confidence': avg_conf,
            'cost_per_pred': cost_per_pred
        })

    # Statistical test if 2 models
    if len(comparisons) == 2:
        results_0 = [p['was_correct'] for p in perf_data_0]
        results_1 = [p['was_correct'] for p in perf_data_1]

        p_value = chi_square_test(results_0, results_1)

        return {
            'models': comparisons,
            'statistical_test': {
                'test_type': 'chi_square',
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        }

    return {'models': comparisons}
```

### Recommendations

```python
@app.get("/api/orchestrator/recommendations")
async def get_recommendations(status: str = "pending"):
    """Get all recommendations filtered by status."""

    result = await supabase.table('orchestrator_recommendations') \
        .select('*') \
        .eq('status', status) \
        .order('priority', desc=True) \
        .execute()

    return {'recommendations': result.data}

@app.post("/api/orchestrator/recommendations/{rec_id}/accept")
async def accept_recommendation(rec_id: str, admin_id: str):
    """Accept and apply a recommendation."""

    # Get recommendation
    rec = await get_recommendation(rec_id)

    if rec.recommendation_type == 'model_promotion':
        # Promote model
        await orchestrator.model_registry.promote_to_champion(
            rec.suggested_model_id
        )
    elif rec.recommendation_type == 'expert_disable':
        # Disable expert
        await disable_expert(rec.expert_id)

    # Mark as accepted
    await supabase.table('orchestrator_recommendations') \
        .update({
            'status': 'accepted',
            'reviewed_by': admin_id,
            'reviewed_at': datetime.utcnow().isoformat()
        }) \
        .eq('recommendation_id', rec_id) \
        .execute()

    return {'status': 'accepted'}

@app.post("/api/orchestrator/recommendations/{rec_id}/reject")
async def reject_recommendation(rec_id: str, admin_id: str, reason: str):
    """Reject a recommendation."""

    await supabase.table('orchestrator_recommendations') \
        .update({
            'status': 'rejected',
            'reviewed_by': admin_id,
            'reviewed_at': datetime.utcnow().isoformat(),
            'review_notes': reason
        }) \
        .eq('recommendation_id', rec_id) \
        .execute()

    return {'status': 'rejected'}
```

### Manual Interventions

```python
@app.post("/api/orchestrator/experts/{expert_id}/disable")
async def disable_expert(expert_id: str, admin_id: str, reason: str):
    """Manually disable an expert."""

    # Get champion
    champion = await orchestrator.model_registry.get_champion(expert_id)

    # Deactivate
    await orchestrator.model_registry.update_model_status(
        champion.model_id,
        is_active=False
    )

    # Log action
    logger.info(f"Expert {expert_id} disabled by {admin_id}: {reason}")

    return {'status': 'disabled'}

@app.post("/api/orchestrator/models/{model_id}/promote")
async def promote_model(model_id: str, admin_id: str):
    """Manually promote a model to champion."""

    await orchestrator.model_registry.promote_to_champion(model_id)

    logger.info(f"Model {model_id} promoted by {admin_id}")

    return {'status': 'promoted'}

@app.post("/api/orchestrator/experiments/{exp_id}/stop")
async def stop_experiment(exp_id: str, admin_id: str, reason: str):
    """Manually stop an active experiment."""

    await supabase.table('orchestrator_experiments') \
        .update({
            'status': 'paused',
            'conclusion_reason': f"Manually stopped by {admin_id}: {reason}"
        }) \
        .eq('experiment_id', exp_id) \
        .execute()

    return {'status': 'stopped'}
```

---

## Integration

### How Orchestrator Integrates with Existing System

**Current Flow** (without orchestrator):
```python
# User requests prediction
@app.get("/api/predictions/{expert_id}/{game_id}")
async def get_prediction(expert_id: str, game_id: str):
    model = get_expert_model(expert_id)
    game_data = await get_game_data(game_id)
    prediction = await model.predict(game_data)
    return prediction
```

**New Flow** (with orchestrator):
```python
# User requests prediction
@app.get("/api/predictions/{expert_id}/{game_id}")
async def get_prediction(expert_id: str, game_id: str):
    orchestrator = MetaLearningOrchestrator(supabase)
    game_data = await get_game_data(game_id)

    # Orchestrator handles:
    # - Model selection (champion vs challengers)
    # - Parallel execution
    # - Cost tracking
    # - Auto-healing
    prediction = await orchestrator.orchestrate_prediction(
        expert_id, game_id, game_data
    )

    return prediction  # User gets champion prediction only
```

### Game Result Webhook

```python
# New endpoint: called when game completes
@app.post("/api/orchestrator/game-result")
async def process_game_result(game_id: str, winner: str):
    orchestrator = MetaLearningOrchestrator(supabase)

    # Orchestrator handles:
    # - Update all model performances
    # - Check experiment conclusions
    # - Generate recommendations
    # - Evaluate alerts
    await orchestrator.process_game_result(game_id, winner)

    return {'status': 'processed'}
```

### Backwards Compatibility

```python
# Feature flag for gradual rollout
ORCHESTRATOR_ENABLED = os.getenv('ORCHESTRATOR_ENABLED', 'false') == 'true'

@app.get("/api/predictions/{expert_id}/{game_id}")
async def get_prediction(expert_id: str, game_id: str):
    game_data = await get_game_data(game_id)

    if ORCHESTRATOR_ENABLED:
        # New path
        orchestrator = MetaLearningOrchestrator(supabase)
        return await orchestrator.orchestrate_prediction(expert_id, game_id, game_data)
    else:
        # Old path (fallback)
        model = get_expert_model(expert_id)
        return await model.predict(game_data)
```

---

## Deployment Strategy

### Phase 1: Foundation (Week 1) - Database & Classes

**Goals**:
- Create database tables
- Implement core classes (no behavior changes yet)
- Seed data for existing models

**Tasks**:
1. Apply migration `023_orchestrator_tables.sql`
2. Implement `ModelRegistry` class
3. Implement `CostTracker` class
4. Create seed script to register existing `AdaptiveLearningEngine` as "gradient_descent_v1.0.0" for all 15 experts
5. Verify tables created and seed data loaded

**Acceptance Criteria**:
- [ ] All 6 tables created in Supabase
- [ ] 15 experts registered with champion models
- [ ] ModelRegistry can read/write models
- [ ] CostTracker can record costs
- [ ] No behavior changes to existing system

### Phase 2: Shadow Mode (Week 2) - Observation Only

**Goals**:
- Deploy orchestrator in observation-only mode
- Record predictions but don't change behavior
- Verify data collection works

**Tasks**:
1. Implement `MetaLearningOrchestrator` core class
2. Deploy with feature flag `ORCHESTRATOR_SHADOW_MODE=true`
3. Record all predictions to `orchestrator_model_performance`
4. Monitor data collection for 7 days
5. Verify no performance degradation

**Acceptance Criteria**:
- [ ] Orchestrator records all predictions
- [ ] Prediction latency < 500ms (p95)
- [ ] No errors or crashes
- [ ] User sees no changes

### Phase 3: Single Expert Pilot (Week 3)

**Goals**:
- Enable orchestrator for 1 expert
- Run first A/B test
- Practice rollback procedures

**Tasks**:
1. Enable orchestrator for `conservative_analyzer` only
2. Create challenger model: `gradient_descent_v1.1.0` with `learning_rate=0.03`
3. Implement `ExperimentManager` class
4. Start A/B test experiment
5. Run for 20 games
6. Check statistical significance
7. Practice rollback (revert to old system)

**Acceptance Criteria**:
- [ ] Orchestrator makes predictions for 1 expert
- [ ] A/B test runs successfully
- [ ] Statistical test detects winner
- [ ] Rollback procedure tested and works

### Phase 4: Gradual Rollout (Week 4)

**Goals**:
- Enable for 5 experts
- Implement auto-healing
- Add basic admin dashboard

**Tasks**:
1. Enable orchestrator for 5 experts
2. Implement `CircuitBreaker` and retry logic
3. Implement `AlertSystem` class
4. Create basic admin dashboard (read-only)
5. Monitor for 7 days

**Acceptance Criteria**:
- [ ] 5 experts using orchestrator
- [ ] Auto-healing prevents failures
- [ ] Alerts triggered correctly
- [ ] Dashboard shows real-time metrics

### Phase 5: Full Production (Week 5)

**Goals**:
- Enable for all 15 experts
- Full recommendation engine
- Complete admin dashboard

**Tasks**:
1. Enable orchestrator for all 15 experts
2. Implement `RecommendationEngine` class
3. Add admin controls (accept/reject recommendations)
4. Add WebSocket for real-time updates
5. Production monitoring

**Acceptance Criteria**:
- [ ] All 15 experts using orchestrator
- [ ] Recommendations generated automatically
- [ ] Admin can accept/reject recommendations
- [ ] Real-time dashboard updates

### Phase 6: Advanced Features (Week 6+)

**Goals**:
- New algorithm variants
- Automatic experiment generation
- Cost optimization

**Tasks**:
1. Implement Bayesian optimizer variant
2. Implement Adam optimizer variant
3. Auto-generate experiments when plateau detected
4. Implement cost optimization algorithms
5. Add predictive maintenance

---

## Testing Strategy

### Unit Tests

**File**: `src/tests/test_orchestrator.py`

```python
import pytest
from src.ml.meta_learning_orchestrator import MetaLearningOrchestrator

@pytest.mark.asyncio
async def test_model_selection():
    """Test champion model selection."""
    registry = ModelRegistry(mock_supabase)
    champion = await registry.get_champion("conservative_analyzer")
    assert champion.is_champion == True

@pytest.mark.asyncio
async def test_parallel_predictions():
    """Test parallel execution of predictions."""
    orchestrator = MetaLearningOrchestrator(mock_supabase)
    predictions = await orchestrator._parallel_predict(
        champion, [challenger1, challenger2], game_data
    )
    assert len(predictions) == 3

@pytest.mark.asyncio
async def test_circuit_breaker():
    """Test circuit breaker opens after failures."""
    cb = CircuitBreaker(threshold=3)

    for _ in range(3):
        cb.record_failure()

    assert cb.is_open() == True

@pytest.mark.asyncio
async def test_statistical_significance():
    """Test Chi-square detects significant differences."""
    champion_results = [1, 0, 1, 1, 0, 1, 1, 1, 0, 1]  # 70%
    challenger_results = [1, 1, 1, 1, 1, 0, 1, 1, 1, 1]  # 90%

    p_value = chi_square_test(champion_results, challenger_results)
    assert p_value < 0.05

@pytest.mark.asyncio
async def test_retry_exponential_backoff():
    """Test retry delays grow exponentially."""
    policy = RetryPolicy(max_retries=3, backoff="exponential", initial_delay=100)
    delays = [policy.get_delay(i) for i in range(3)]
    assert delays == [100, 200, 400]

@pytest.mark.asyncio
async def test_cost_tracking():
    """Test cost is recorded correctly."""
    tracker = CostTracker(mock_supabase)
    await tracker.record_prediction_cost(
        "conservative_analyzer", model_id, game_id,
        api_calls={"odds_api": 1}, tokens=100
    )

    daily_cost = await tracker.get_daily_cost()
    assert daily_cost > 0
```

### Integration Tests

**File**: `scripts/test_orchestrator_integration.py`

```python
@pytest.mark.asyncio
async def test_full_prediction_flow():
    """Test complete flow from prediction to result."""
    orchestrator = MetaLearningOrchestrator(supabase)

    # Make prediction
    prediction = await orchestrator.orchestrate_prediction(
        "conservative_analyzer", game_id, game_data
    )
    assert prediction is not None

    # Process result
    await orchestrator.process_game_result(game_id, "PHI")

    # Verify performance recorded
    perf = await get_model_performance(prediction.model_id, game_id)
    assert perf.was_correct == (prediction.winner == "PHI")

@pytest.mark.asyncio
async def test_a_b_test_lifecycle():
    """Test complete A/B test from start to conclusion."""
    # Create experiment
    exp = await create_experiment(
        expert_id="conservative_analyzer",
        champion=champion_model,
        challengers=[challenger_model]
    )

    # Run 30 predictions
    for game in games[:30]:
        await orchestrator.orchestrate_prediction(...)
        await orchestrator.process_game_result(...)

    # Check if experiment concluded
    result = await get_experiment_result(exp.id)
    assert result.status == "concluded"
    assert result.winner_model_id is not None

@pytest.mark.asyncio
async def test_auto_healing():
    """Test retry and fallback on failures."""
    # Inject failure
    with mock.patch('expert_model.predict', side_effect=Exception("API timeout")):
        prediction = await orchestrator.orchestrate_prediction(...)

    # Should still return prediction via fallback
    assert prediction is not None

    # Should log failure
    failures = await get_failure_log()
    assert len(failures) > 0
```

### Load Testing

```python
@pytest.mark.asyncio
async def test_concurrent_predictions():
    """Test 100 concurrent predictions."""
    orchestrator = MetaLearningOrchestrator(supabase)

    # Create 100 prediction tasks
    tasks = [
        orchestrator.orchestrate_prediction(
            random.choice(expert_ids),
            game_id,
            game_data
        )
        for _ in range(100)
    ]

    # Execute concurrently
    start = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start

    # Verify
    assert len(results) == 100
    assert elapsed < 10.0  # Less than 10 seconds for 100 predictions
    assert all(r is not None for r in results)
```

---

## Security & Compliance

### Authentication

- All admin API endpoints require JWT token
- Token validated against Supabase auth
- Role-based access control (admin vs read-only)

### Authorization

- Admins can accept/reject recommendations
- Admins can manually disable experts
- Admins can promote models
- Read-only users can view dashboard only

### Data Privacy

- No PII stored in orchestrator tables
- Prediction data anonymized
- Cost data aggregated only

### Audit Logging

```sql
CREATE TABLE orchestrator_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_id TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,  -- "model", "expert", "experiment", "recommendation"
    target_id TEXT NOT NULL,
    details JSONB,
    ip_address TEXT,
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Input Validation

- All hyperparameters validated before model registration
- SQL injection prevention (use parameterized queries)
- Rate limiting on API endpoints (100 req/min per user)

### Budget Protection

- Hard limits in database (cannot be exceeded)
- Require admin approval for budget increases
- Auto-disable expensive features if spike detected

---

## Monitoring & Alerts

### Key Metrics

1. **Accuracy Metrics**:
   - Rolling 10-game accuracy per expert
   - Week-over-week accuracy change
   - Confidence calibration score

2. **Performance Metrics**:
   - Average prediction latency
   - 95th percentile latency
   - Error rate

3. **Cost Metrics**:
   - Cost per prediction
   - Daily burn rate
   - Cost per accuracy point

4. **System Health**:
   - Uptime percentage
   - Circuit breaker status
   - Active experiment count

### Alert Rules

```python
# Accuracy drop
{
    "metric": "rolling_10_accuracy",
    "operator": "<",
    "threshold": 0.50,
    "severity": "critical"
}

# Error rate spike
{
    "metric": "error_rate",
    "operator": ">",
    "threshold": 0.15,
    "severity": "critical"
}

# Cost spike
{
    "metric": "daily_cost",
    "operator": ">",
    "threshold": 50.0,
    "severity": "warning"
}

# Latency high
{
    "metric": "latency_p95",
    "operator": ">",
    "threshold": 1000,
    "severity": "warning"
}
```

### Notification Channels

1. **Email**: Critical alerts sent to admin
2. **Slack**: All alerts posted to #ml-alerts
3. **Dashboard**: Real-time alerts in UI
4. **PagerDuty**: Critical alerts for on-call

---

## Cost Management

### Cost Breakdown

| Resource | Cost per Unit | Typical Usage | Daily Cost |
|----------|--------------|---------------|------------|
| Odds API | $0.01/call | 15 experts × 16 games | $2.40 |
| SportsData.io | $0.005/call | 30 calls/game | $2.40 |
| Supabase | $0.00001/query | 1000 queries/day | $0.01 |
| Compute | $0.001/1000ms | 500ms/prediction | $1.20 |
| **Total** | | | **$6.01/day** |

### Budget Limits

```python
# Set daily budget
await set_budget_limit(
    resource_type="cost_daily_usd",
    limit_value=50.0,
    alert_threshold=0.8,  # Alert at $40
    auto_throttle=True
)
```

### Cost Optimization Strategies

1. **Caching**: Reduce API calls by 60%
2. **Smart Fetching**: Only get odds for high-stakes games
3. **Model Efficiency**: Prefer faster models if accuracy similar
4. **Batch Processing**: Combine API requests when possible

---

## Edge Cases & Failure Handling

### Edge Case 1: No Historical Data

**Scenario**: New expert with 0 games

**Solution**:
- Use uniform prior in Thompson Sampling: Beta(1,1)
- Fallback to baseline model
- Start with conservative hyperparameters
- Require 10 games before statistical testing

### Edge Case 2: All Models Failing

**Scenario**: Circuit breakers open for all challengers

**Solution**:
- Keep champion always available (highest priority)
- If champion fails, use cached predictions
- Alert admin immediately
- Use ensemble average from other experts
- Last resort: historical baseline (home team 55%)

### Edge Case 3: Budget Exhausted Mid-Game

**Scenario**: Cost limit reached during prediction

**Solution**:
- Complete current predictions with cached data
- Alert admin immediately
- Auto-throttle expensive features
- Use free APIs only for next games
- Suggest budget increase to admin

### Edge Case 4: Tied Statistical Results

**Scenario**: Two models have identical accuracy

**Solution**:
- Use secondary metrics:
  - Confidence calibration
  - Prediction latency
  - Cost per prediction
- If still tied, keep current champion (avoid churn)
- Run extended experiment (50 more games)

### Edge Case 5: Extreme Outlier Game

**Scenario**: All 15 experts get it wrong

**Solution**:
- Don't overreact to single game
- Use rolling window for evaluation
- Mark as "high surprise" game
- Analyze patterns in episodic memory
- Don't trigger model changes from single outlier

---

## Success Metrics

### Week 1 (Foundation)
- [ ] All 6 tables created
- [ ] 15 experts registered
- [ ] Seed data loaded

### Week 2 (Shadow Mode)
- [ ] 1000+ predictions recorded
- [ ] Latency < 500ms p95
- [ ] 0 errors

### Week 3 (Pilot)
- [ ] 1 expert using orchestrator
- [ ] 1 A/B test completed
- [ ] Statistical test works

### Week 4 (Gradual Rollout)
- [ ] 5 experts using orchestrator
- [ ] Auto-healing prevents failures
- [ ] Dashboard deployed

### Week 5 (Full Production)
- [ ] 15 experts using orchestrator
- [ ] Recommendations generated
- [ ] Admin controls working

### 3 Months (Long-term)
- [ ] 5-10% accuracy improvement
- [ ] 30% cost reduction
- [ ] 99.5%+ uptime
- [ ] 60%+ recommendation acceptance

---

## Appendix: File Manifest

### New Files to Create

1. `src/ml/meta_learning_orchestrator.py` (500 lines)
2. `src/ml/model_registry.py` (300 lines)
3. `src/ml/experiment_manager.py` (400 lines)
4. `src/ml/cost_tracker.py` (200 lines)
5. `src/ml/auto_healing.py` (250 lines)
6. `src/ml/recommendation_engine.py` (350 lines)
7. `src/ml/alert_system.py` (300 lines)
8. `src/api/orchestrator_endpoints.py` (400 lines)
9. `src/database/migrations/023_orchestrator_tables.sql` (200 lines)
10. `scripts/seed_orchestrator_data.py` (150 lines)
11. `src/tests/test_orchestrator.py` (500 lines)
12. `scripts/test_orchestrator_integration.py` (300 lines)

**Total**: ~3,850 lines of code

---

## Appendix: Configuration

```python
# config/orchestrator_config.py

class OrchestratorConfig:
    # Prediction
    max_challengers_per_expert = 3
    prediction_timeout_ms = 2000

    # Retry
    max_retries = 3
    retry_backoff = "exponential"
    initial_delay_ms = 1000

    # Circuit Breaker
    failure_threshold = 5
    circuit_timeout_ms = 60000

    # Experiments
    min_sample_size = 30
    significance_level = 0.05

    # Cost
    daily_budget_usd = 50.0
    alert_threshold = 0.8
    auto_throttle = True

    # Cache
    champion_cache_ttl_seconds = 300
```

---

**End of Document**

**Version**: 1.0.0
**Last Updated**: 2025-09-30
**Status**: Ready for Implementation