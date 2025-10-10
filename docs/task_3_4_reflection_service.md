# Task 3.4: Post-Game Reflection Service - Implementation Guide

## Overview

Task 3.4 implements the Post-Game Reflection System that provides optional reflion LLM calls for the Expert Council Betting System. The service includes environment flag gating, reflection storage, Neo4j emission with retry/backoff logic, and degraded fallback when reflection fails.

## Implementation

### Core Service (`src/services/reflection_service.py`)

The Reflection Service provides comprehensive post-game analysis with:

1. **Optional Reflection LLM Calls**: Environment flag-controlled reflection generation
2. **Reflection Storage**: Comprehensive metadata and structured insights
3. **Neo4j Emission**: Async emission with retry/backoff logic
4. **Degraded Fallback**: Graceful handling when reflection fails
5. **Performance Tracking**: Complete monitoring and metrics

### Key Components

#### Reflection Process Flow
```
1. Check environment flag (ENABLE_REFLECTION)
2. Evaluate triggering conditions
3. Generate reflection prompt with game context
4. Execute LLM call with timeout protection
5. Parse and validate reflection response
6. Store reflection with comprehensive metadata
7. Emit to Neo4j asynchronously with retry logic
8. Track performance metrics and audit trail
```

#### Environment Flag Gating
```python
# Environment variable control
ENABLE_REFLECTION=true|false

# Service checks flag on initialization and per-request
enabled = os.getenv('ENABLE_REFLECTION', 'false').lower() in ['true', '1', 'yes', 'on', 'enabled']

# Graceful fallback when disabled
if not enabled:
    return skipped_reflection_result
```

#### Reflection Triggers
```python
class ReflectionTrigger(Enum):
    POST_GAME = "post_game"              # After every game
    POOR_PERFORMANCE = "poor_performance" # When performance < threshold
    CALIBRATION_DRIFT = "calibration_drift" # When calibration changes significantly
    MANUAL = "manual"                    # Manually triggered
    SCHEDULED = "scheduled"              # Scheduled reflection
```

### Data Structures

#### ReflectionResult
```python
@dataclass
class ReflectionResult:
    reflection_id: str
    expert_id: str
    game_id: str
    trigger: ReflectionTrigger

    # Reflection content
    lessons_learned: List[str]
    performance_analysis: str
    factor_recommendations: Dict[str, float]
    calibration_insights: List[str]
    insights: List[ReflectionInsight]

    # Processing metadata
    reflection_status: ReflectionStatus
    processing_time_ms: float
    model_used: str
    prompt_tokens: int
    completion_tokens: int

    # Context
    game_context: Dict[str, Any]
    performance_metrics: Dict[str, float]
    learning_summary: Dict[str, Any]

    # Neo4j emission tracking
    neo4j_emitted: bool
    neo4j_emission_attempts: int
    neo4j_last_attempt: Optional[datetime]
```

#### ReflectionInsight
```python
@dataclass
class ReflectionInsight:
    insight_id: str
    category: str
    insight_text: str
    confidence: float
    actionable: bool
    factor_adjustments: Dict[str, float]
    learning_cues: List[str]
```

#### ReflectionConfig
```python
@dataclass
class ReflectionConfig:
    enabled: bool = True
    model_provider: str = "anthropic"
    model_name: str = "claude-3-sonnet-20240229"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout_seconds: int = 30

    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_multiplier: float = 2.0

    # Neo4j emission
    neo4j_enabled: bool = True
    neo4j_max_retries: int = 5
    neo4j_retry_delay: float = 2.0
    neo4j_backoff_multiplier: float = 1.5

    # Triggering conditions
    trigger_on_poor_performance: bool = True
    poor_performance_threshold: float = 0.3
    trigger_on_calibration_drift: bool = True
    calibration_drift_threshold: float = 0.1

    # Environment flags
    env_flag_key: str = "ENABLE_REFLECTION"
    fallback_mode: str = "graceful"
```

### Reflection Prompt Generation

The service generates persona-aware reflection prompts:

```python
def _generate_reflection_prompt(self, reflection: ReflectionResult) -> str:
    """Generate reflection prompt for LLM"""

    prompt = f"""
You are an expert NFL analyst reflecting on your performance after game {reflection.game_id}.

EXPERT IDENTITY: {expert_id}
GAME CONTEXT: {json.dumps(game_context, indent=2)}
PERFORMANCE METRICS: {json.dumps(performance_metrics, indent=2)}
LEARNING SUMMARY: {json.dumps(learning_summary, indent=2)}

Please provide a structured reflection in JSON format with:
- lessons_learned: Key insights from this game
- performance_analysis: What went well and what didn't
- factor_recommendations: Suggested factor adjustments
- calibration_insights: Insights about prediction calibration
- key_insights: Actionable insights with confidence levels

Focus on prediction accuracy, confidence calibration, factor adjustments,
and specific lessons for future performance improvement.
"""
```

### Neo4j Emission with Retry Logic

```python
def _emit_to_neo4j(self, reflection: ReflectionResult) -> bool:
    """Emit reflection to Neo4j with retry logic"""

    max_retries = self.config.neo4j_max_retries
    retry_delay = self.config.neo4j_retry_delay

    for attempt in range(max_retries + 1):
        try:
            # Create Neo4j nodes and relationships
            neo4j_operations = {
                'create_reflection_node': {...},
                'create_insights': [...],
                'create_relationships': [
                    "(Expert)-[:REFLECTED_ON]->(Game)",
                    "(Reflection)-[:LEARNED_FROM]->(Game)"
                ]
            }

            success = self.neo4j_client.execute(neo4j_operations)
            if success:
                return True

        except Exception as e:
            if attempt < max_retries:
                time.sleep(retry_delay)
                retry_delay *= self.config.neo4j_backoff_multiplier

    return False
```

### Timeout and Error Handling

```python
def _perform_reflection_with_timeout(self, reflection: ReflectionResult) -> ReflectionResult:
    """Perform reflection with timeout handling"""

    try:
        # Submit to thread pool with timeout
        future = self.executor.submit(self._perform_reflection, reflection)
        result = future.result(timeout=self.config.timeout_seconds)
        return result

    except FutureTimeoutError:
        reflection.reflection_status = ReflectionStatus.TIMEOUT
        reflection.performance_analysis = "Reflection timed out"
        return reflection

    except Exception as e:
        reflection.reflection_status = ReflectionStatus.FAILED
        reflection.performance_analysis = f"Reflection failed: {str(e)}"
        return reflection
```

### Persona-Aware Responses

The service generates different reflection responses based on expert persona:

- **Conservative Analyzer**: Focus on risk management and conservative strategies
- **Momentum Rider**: Emphasize momentum detection and timing insights
- **Contrarian Rebel**: Highlight contrarian opportunities and market inefficiencies
- **Value Hunter**: Concentrate on value identification and betting opportunities

## API Methods

### Core Reflection Methods

- `trigger_reflection()`: Trigger reflection for an expert after a game
- `get_reflection_history()`: Get reflection history with optional filters
- `get_performance_metrics()`: Get reflection service performance metrics

### Configuration Methods

- `update_config()`: Update reflection configuration parameters
- `clear_all_data()`: Clear all reflection data (for testing)

### Internal Methods

- `_check_environment_flag()`: Check if reflection is enabled via environment
- `_should_trigger_reflection()`: Determine if reflection should be triggered
- `_generate_reflection_prompt()`: Generate persona-aware reflection prompts
- `_perform_reflection()`: Execute LLM call and parse response
- `_emit_to_neo4j()`: Emit reflection to Neo4j with retry logic

## Integration Points

### With Learning Service (Task 3.3)
- Receives learning summaries for reflection context
- Reflection insights can inform future learning adjustments
- Factor recommendations feed back into learning system

### With Settlement Service (Task 3.2)
- Reflection triggered after settlement completion
- Performance metrics from settlement inform reflection
- Reflection insights can improve future betting strategies

### With Neo4j Provenance System (Task 4.x)
- Async emission of reflection nodes and relationships
- Provenance tracking of reflection insights
- Learning relationship creation between reflections and outcomes

## Performance Characteristics

- **Environment Flag Control**: Instant enable/disable via environment variable
- **Timeout Protection**: Configurable timeout for LLM calls (default 30s)
- **Async Operations**: Non-blocking Neo4j emission with thread pool
- **Retry Logic**: Exponential backoff for Neo4j emission failures
- **Graceful Degradation**: Fallback responses when reflection fails

## Testing

Comprehensive test coverage includes:
- Environment flag checking and service enabling/disabling
- Configuration management and updates
- Trigger condition evaluation
- Reflection prompt generation
- Mock LLM call simulation
- Response parsing and validation
- Full reflection trigger workflow
- Reflection history and filtering
- Performance metrics tracking
- Neo4j emission with retry logic
- Edge case handling (empty data, timeouts, failures)

## Next Steps

1. **LLM Integration**: Connect to real LLM providers (Claude, GPT-4, etc.)
2. **Neo4j Client**: Implement real Neo4j client with proper authentication
3. **Learning Integration**: Use reflection insights to adjust learning parameters
4. **Performance Monitoring**: Add reflection effectiveness dashboards
5. **Production Deployment**: Monitor reflection performance in live environment

## Requirements Satisfied

✅ **2.6 Learning & calibration (reflection component)**
- Optional reflection LLM calls with environment flag gating
- Reflection storage with comprehensive metadata
- Neo4j emission with retry/backoff logic
- Degraded fallback when reflection fails
- Performance tracking and monitoring
- Persona-aware reflection generation
