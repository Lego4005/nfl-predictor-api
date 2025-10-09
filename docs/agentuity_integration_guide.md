# Agentuity Integration Guide - NFL Expert Council Betting System

## Overview

This guide covers the hybrid Agentuity integration for the NFL Expert Council Betting System. Agentuity handles **orchestration only** - parallel expert coordination, streaming, telemetry, and shadow runs. All operational data and hot path processing remains in Postgres/pgvector.

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agentuity     │    │   NFL Predictor  │    │   Postgres +    │
│   Orchestrator  │◄──►│   FastAPI        │◄──►│   pgvector      │
│                 │    │                  │    │   (Hot Path)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                       │
         │                        │                       │
         ▼                        ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Shadow Runs   │    │   Expert LLM     │    │   Neo4j         │
│   (A/B Testing) │    │   Calls          │    │   (Write-behind)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Quick Start

### 1. Install Agentuity CLI

```bash
npm install -g @agentuity/cli
```

### 2. Initialize Project

```bash
# Create Agentuity workspace
agentuity init nfl-expert-council

# Navigate to project
cd nfl-expert-council

# Copy our agent configurations
cp -r /path/to/nfl-predictor-api/agentuity/* .

# Set environment variables
cp .env.example .env
# Edit .env with your API keys and endpoints
```

### 3. Configure Environment

```bash
# Required environment variables
export API_BASE_URL="http://localhost:8000/api"
export SUPABASE_URL="your-supabase-url"
export SUPABASE_ANON_KEY="your-anon-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"

# Optional feature flags
export ENABLE_SHADOW_RUNS="false"
export ENABLE_POST_GAME_REFLECTION="false"
export MAX_PARALLEL_EXPERTS="8"
```

### 4. Deploy Agents

```bash
# Deploy to Agentuity
agentuity deploy

# Verify deployment
agentuity agents list
```

### 5. Test Integration

```bash
# Test orchestrator agent
curl -X POST "https://your-agentuity-url/agents/game-orchestrator/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-agentuity-token" \
  -d '{
    "game_id": "test_game_001",
    "expert_ids": ["conservative_analyzer", "risk_taking_gambler"],
    "api_base_url": "http://localhost:8000/api",
    "enable_shadow_runs": false,
    "shadow_models": {},
    "orchestration_id": "test_orch_001"
  }'
```

## Integration Points

### 1. NFL Predictor API Endpoints

The Agentuity agents call these endpoints in our FastAPI service:

#### Memory Context Retrieval
```
GET /api/context/{expert_id}/{game_id}
```
Returns memory context with episodic memories, team knowledge, and matchup data.

#### Prediction Storage
```
POST /api/expert/predictions
```
Stores validated 83-assertion prediction bundles and creates betting tickets.

#### Health Check
```
GET /api/health/agentuity
```
Returns system health for Agentuity monitoring.

### 2. AgentuityAdapter Integration

Add to your FastAPI service:

```python
from src.services.agentuity_adapter import agentuity_adapter

@app.post("/api/orchestrate/game/{game_id}")
async def orchestrate_game_predictions(
    game_id: str,
    expert_ids: List[str] = Query(...),
    enable_shadow_runs: bool = False
):
    """Trigger Agentuity orchestration for a game"""
    result = await agentuity_adapter.run_game_orchestration(
        game_id=game_id,
        expert_ids=expert_ids,
        enable_shadow_runs=enable_shadow_runs
    )
    return result

@app.get("/api/health/agentuity")
async def agentuity_health():
    """Check Agentuity orchestrator health"""
    return await agentuity_adapter.get_orchestration_health()
```

## Agent Specifications

### GameOrchestrator Agent

**Purpose**: Coordinate parallel expert prediction generation

**Input**:
```json
{
  "game_id": "string",
  "expert_ids": ["string"],
  "api_base_url": "string",
  "enable_shadow_runs": "boolean",
  "shadow_models": {"expert_id": "model_name"},
  "orchestration_id": "string"
}
```

**Output**:
```json
{
  "orchestration_id": "string",
  "game_id": "string",
  "experts_processed": ["string"],
  "experts_failed": ["string"],
  "total_duration_ms": "number",
  "retrieval_duration_ms": "number",
  "llm_duration_ms": "number",
  "validation_duration_ms": "number",
  "schema_compliance_rate": "number",
  "shadow_results": "object|null"
}
```

### ReflectionAgent Agent

**Purpose**: Generate post-game learning insights

**Input**:
```json
{
  "game_id": "string",
  "expert_id": "string",
  "game_outcome": "object",
  "expert_predictions": "object"
}
```

**Output**:
```json
{
  "success": "boolean",
  "reflection": {
    "expert_id": "string",
    "game_id": "string",
    "lessons_learned": ["string"],
    "factor_adjustments": [
      {
        "factor_name": "string",
        "direction": "increase|decrease|maintain",
        "confidence": "number",
        "reasoning": "string"
      }
    ],
    "prediction_quality_assessment": "object",
    "meta_insights": "object"
  }
}
```

## Performance Monitoring

### Key Metrics

Agentuity automatically tracks:
- **Agent execution time**: Total orchestration duration
- **Success rates**: Expert processing success/failure rates
- **Schema compliance**: JSON validation pass rates
- **Parallel efficiency**: Concurrent expert processing metrics

### Custom Telemetry

Additional metrics forwarded to your monitoring:
- Vector retrieval latency (p95 < 100ms target)
- LLM call duration per expert
- Memory context size and relevance scores
- Shadow model comparison results

### Dashboards

Access via Agentuity console:
- Real-time agent execution logs
- Performance trend analysis
- Error rate monitoring
- Shadow run A/B test results

## Shadow Runs (A/B Testing)

### Purpose
Test alternate LLM models without affecting production predictions.

### Configuration
```bash
# Enable shadow runs
export ENABLE_SHADOW_RUNS="true"

# Configure shadow models per expert
{
  "shadow_models": {
    "conservative_analyzer": "gpt-4-turbo",
    "risk_taking_gambler": "claude-3-opus"
  }
}
```

### Results
Shadow predictions are:
- Generated in parallel with main predictions
- Stored separately for comparison
- Never used in hot path or council selection
- Available for analysis and model evaluation

## Fallback & Resilience

### Circuit Breaker
If Agentuity is unavailable:
1. AgentuityAdapter detects failure
2. Falls back to local sequential processing
3. Processes up to 4 experts (rate limited)
4. Logs degraded mode operation
5. Alerts operators

### Health Monitoring
```bash
# Check agent health
agentuity agents health

# View execution logs
agentuity logs --agent game-orchestrator --tail

# Monitor performance
agentuity metrics --agent game-orchestrator
```

## Security

### API Keys
- Store in Agentuity secret manager
- Rotate regularly via CLI
- Scope permissions appropriately

### Network Security
- Use HTTPS for all agent communications
- Implement rate limiting on API endpoints
- Monitor for unusual traffic patterns

### Data Protection
- No PII stored in Agentuity
- Operational data remains in Postgres
- Audit logs for all orchestration activities

## Troubleshooting

### Common Issues

**Agent deployment fails**:
```bash
# Check configuration
agentuity validate

# View deployment logs
agentuity deploy --verbose
```

**Orchestration timeouts**:
```bash
# Increase timeout in environment
export EXPERT_TIMEOUT_MS="45000"

# Check API endpoint health
curl http://localhost:8000/api/health
```

**Schema validation errors**:
```bash
# View failed payloads in logs
agentuity logs --agent game-orchestrator --filter "schema_valid:false"

# Test schema locally
python -c "import json; from src.validation import validate_expert_predictions; ..."
```

### Performance Optimization

**Slow vector retrieval**:
- Check HNSW index status
- Monitor K parameter adaptation
- Verify pgvector configuration

**High LLM latency**:
- Review model selection per expert
- Check provider API status
- Consider model switching via shadow runs

**Memory usage**:
- Monitor agent resource consumption
- Adjust parallel expert limits
- Optimize memory context size

## Best Practices

### Development
1. Test agents locally with `agentuity dev`
2. Use shadow runs for model experimentation
3. Monitor schema compliance rates closely
4. Implement comprehensive error handling

### Production
1. Set appropriate resource limits
2. Monitor performance metrics continuously
3. Implement alerting for failures
4. Maintain fallback capabilities

### Scaling
1. Adjust `MAX_PARALLEL_EXPERTS` based on load
2. Use Agentuity's auto-scaling features
3. Monitor database connection pools
4. Implement request queuing if needed

## Support

### Documentation
- [Agentuity SDK Reference](https://agentuity.dev/SDKs/javascript)
- [Agent Development Guide](https://agentuity.dev/agents)
- [Performance Optimization](https://agentuity.dev/performance)

### Community
- [Agentuity Discord](https://discord.gg/agentuity)
- [GitHub Issues](https://github.com/agentuity/kitchen-sink-ts/issues)

### Internal
- Check `src/services/agentuity_adapter.py` for implementation details
- Review agent logs in Agentuity console
- Monitor hot path performance in Postgres/pgvector
