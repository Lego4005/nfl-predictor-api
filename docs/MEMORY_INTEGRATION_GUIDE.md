# Memory Integration Guide: Conservative Analyzer

## Overview

This guide documents the memory retrieval integration into the `ConservativeAnalyzer` prediction process, enabling the expert to learn from past experiences and adjust predictions accordingly.

## Implementation Summary

### Core Features

1. **Memory Retrieval Before Prediction**
   - Retrieves relevant past experiences before making predictions
   - Uses game context (teams, weather, injuries, market data) to find similar situations

2. **Memory-Influenced Confidence Adjustment**
   - Analyzes success rates from similar past predictions
   - Adjusts confidence based on historical performance patterns
   - Applies conservative adjustments (+/- 15% maximum)

3. **Learned Principles Application**
   - Extracts insights from memory patterns
   - Applies learned principles to current prediction logic
   - Tracks high/low success rate scenarios

4. **Backward Compatibility**
   - Works seamlessly with or without memory service
   - No breaking changes to existing API
   - Graceful degradation when memory service unavailable

## Architecture

### Modified Components

#### 1. PersonalityDrivenExpert Base Class

```python
class PersonalityDrivenExpert(ABC):
    def __init__(self, expert_id: str, name: str, personality_profile: PersonalityProfile,
                 memory_service=None):
        # ...
        self.memory_service = memory_service  # New: Optional memory service
```

**New Methods:**

- `retrieve_relevant_memories(game_context)` - Retrieves memories for current context
- `apply_memory_insights(prediction, memories)` - Adjusts prediction based on memories
- `calculate_memory_influenced_confidence(base_confidence, memories)` - Calculates confidence adjustment

#### 2. ConservativeAnalyzer

```python
class ConservativeAnalyzer(PersonalityDrivenExpert):
    def __init__(self, memory_service=None):
        # Now accepts optional memory_service parameter
        super().__init__(
            expert_id="conservative_analyzer",
            name="The Analyst",
            personality_profile=personality,
            memory_service=memory_service  # Pass to parent
        )
```

**Enhanced Prediction Flow:**

```
1. Retrieve relevant memories (if memory service available)
   ↓
2. Process data through personality lens
   ↓
3. Generate personality-driven predictions
   ↓
4. Synthesize base prediction
   ↓
5. Apply memory insights (if memories retrieved)
   ↓
6. Record decision in memory
```

## Usage Examples

### Example 1: Without Memory Service (Backward Compatible)

```python
from src.ml.personality_driven_experts import ConservativeAnalyzer, UniversalGameData

# Create analyzer without memory service
analyzer = ConservativeAnalyzer(memory_service=None)

# Create game data
game_data = UniversalGameData(
    home_team="KC",
    away_team="BAL",
    weather={'temperature': 32, 'wind_speed': 15},
    injuries={'home': [...], 'away': [...]},
    line_movement={'opening_line': -3.0, 'current_line': -2.5},
    team_stats={...}
)

# Make prediction (works as before)
prediction = analyzer.make_personality_driven_prediction(game_data)

# Output: Standard prediction without memory enhancement
print(f"Winner: {prediction['winner_prediction']}")
print(f"Confidence: {prediction['winner_confidence']:.1%}")
print(f"Memory Enhanced: {prediction.get('memory_enhanced', False)}")  # False
```

### Example 2: With Memory Service (Memory-Enhanced)

```python
from src.ml.personality_driven_experts import ConservativeAnalyzer, UniversalGameData
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from supabase import create_client

# Initialize memory service
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
memory_service = SupabaseEpisodicMemoryManager(supabase)

# Create analyzer WITH memory service
analyzer = ConservativeAnalyzer(memory_service=memory_service)

# Create game data
game_data = UniversalGameData(
    home_team="KC",
    away_team="BAL",
    weather={'temperature': 32, 'wind_speed': 15},
    injuries={'home': [...], 'away': [...]},
    line_movement={'opening_line': -3.0, 'current_line': -2.5},
    team_stats={...}
)

# Make prediction (enhanced with memory)
prediction = analyzer.make_personality_driven_prediction(game_data)

# Output: Memory-enhanced prediction
print(f"Winner: {prediction['winner_prediction']}")
print(f"Base Confidence: {prediction['winner_confidence']:.1%}")
print(f"Memory Enhanced: {prediction.get('memory_enhanced', False)}")  # True
print(f"Memories Consulted: {prediction.get('memories_consulted', 0)}")
print(f"Success Rate: {prediction.get('memory_success_rate', 0):.1%}")
print(f"Confidence Adjustment: {prediction.get('confidence_adjustment', 0):+.3f}")
print(f"\nLearned Principles:")
for principle in prediction.get('learned_principles', []):
    print(f"  • {principle}")
```

### Example 3: With Hooks for Coordination (CLAUDE.md Pattern)

```python
import subprocess
import json

# Hook 1: Pre-task coordination
subprocess.run([
    "npx", "claude-flow@alpha", "hooks", "pre-task",
    "--description", "Memory-enhanced prediction for KC@BAL"
], check=True)

# Hook 2: Session restore
subprocess.run([
    "npx", "claude-flow@alpha", "hooks", "session-restore",
    "--session-id", "swarm-analyzer-001"
], check=True)

# Initialize memory-enabled analyzer
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
memory_service = SupabaseEpisodicMemoryManager(supabase)
analyzer = ConservativeAnalyzer(memory_service=memory_service)

# Make prediction
game_data = UniversalGameData(...)
prediction = analyzer.make_personality_driven_prediction(game_data)

# Hook 3: Post-edit notification (store prediction in memory)
subprocess.run([
    "npx", "claude-flow@alpha", "hooks", "post-edit",
    "--file", "predictions/KC_BAL_2024.json",
    "--memory-key", f"swarm/conservative_analyzer/prediction_{datetime.now().isoformat()}"
], check=True)

# Hook 4: Notify completion
subprocess.run([
    "npx", "claude-flow@alpha", "hooks", "notify",
    "--message", f"Prediction complete: {prediction['winner_prediction']} ({prediction['winner_confidence']:.1%})"
], check=True)

# Hook 5: Post-task
subprocess.run([
    "npx", "claude-flow@alpha", "hooks", "post-task",
    "--task-id", "memory-prediction-001"
], check=True)
```

## Memory Data Structure

### Retrieved Memory Format

```python
{
    'memory_id': 'mem_001',
    'expert_id': 'conservative_analyzer',
    'game_id': 'KC@BAL_2023',
    'memory_type': 'prediction_outcome',
    'prediction_data': {  # JSON or dict
        'winner': 'home',
        'confidence': 0.75,
        'spread': -3.5,
        'reasoning': '...'
    },
    'actual_outcome': {  # JSON or dict
        'winner': 'home',
        'home_score': 27,
        'away_score': 20,
        'margin': 7
    },
    'lessons_learned': [
        'High confidence was validated',
        'Home field advantage significant'
    ],
    'contextual_factors': [...],
    'created_at': '2023-12-15T10:00:00'
}
```

### Enhanced Prediction Output

```python
{
    'expert_name': 'The Analyst',
    'winner_prediction': 'home',
    'winner_confidence': 0.70,  # Adjusted from base 0.65
    'spread_prediction': -3.0,
    'total_prediction': 45.5,
    'reasoning': '...',
    'key_factors': [...],

    # Memory enhancement metadata
    'memory_enhanced': True,
    'memories_consulted': 3,
    'memory_success_rate': 0.667,
    'confidence_adjustment': +0.050,
    'learned_principles': [
        'High success rate (67%) in similar situations'
    ]
}
```

## Confidence Adjustment Algorithm

### Pattern Analysis

The system analyzes three key patterns from memory:

1. **Overall Success Rate**
   - Success rate > 70% → +5% confidence boost
   - Success rate < 30% → -5% confidence reduction

2. **High Confidence Track Record**
   - When making high confidence predictions (>70%):
     - More past successes than failures → +3% boost
     - More past failures than successes → -3% reduction

3. **Consistency Patterns** (5+ memories)
   - Very consistent success (>80%) → +2% boost
   - Very consistent failure (<20%) → -2% reduction

### Total Adjustment Range

- Maximum boost: +15% (0.15)
- Maximum reduction: -15% (-0.15)
- Ensures stability while allowing meaningful adjustments

### Example Calculation

```python
# Scenario: Base confidence = 65%, 5 memories retrieved
# Memory 1-4: Successful predictions (80% success rate)
# Memory 5: Failed prediction with high confidence

# Step 1: Overall success rate (80% > 70%)
adjustment = +0.05

# Step 2: High confidence check (base 65% not > 70%)
# No additional adjustment

# Step 3: Consistency check (80% > 80%)
adjustment += 0.02

# Total adjustment: +0.07
# Final confidence: 65% + 7% = 72%
```

## Testing

### Test Coverage

1. **Backward Compatibility Test**
   - Verifies analyzer works without memory service
   - Ensures no breaking changes

2. **Memory Integration Test**
   - Confirms memory retrieval works
   - Validates enhancement metadata

3. **Confidence Adjustment Test**
   - Tests high/low success rate scenarios
   - Verifies adjustment boundaries

4. **Memory Insights Application Test**
   - Confirms insights properly applied
   - Validates learned principles extraction

### Running Tests

```bash
# Run memory integration tests
python3 tests/test_conservative_analyzer_memory.py

# Expected output:
# ✅ ALL TESTS PASSED
# 🎉 Memory integration successfully implemented!
```

## Performance Considerations

### Memory Retrieval Performance

- **Retrieval limit**: 5 memories by default (configurable)
- **Query optimization**: Uses indexed fields (expert_id, created_at)
- **Async support**: Full async version available for non-blocking retrieval

### Memory Storage

- Memories stored in Supabase `expert_episodic_memories` table
- Automatic cleanup of old memories (optional)
- Memory decay system for reduced influence over time

## Future Enhancements

1. **Similarity-Based Retrieval**
   - Use pgvector for semantic similarity search
   - Weight memories by relevance score

2. **Advanced Pattern Recognition**
   - Weather-specific patterns
   - Market movement patterns
   - Injury impact patterns

3. **Dynamic Adjustment Weights**
   - Personality-specific adjustment scales
   - Adaptive learning rates

4. **Cross-Expert Learning**
   - Share successful patterns across experts
   - Collective intelligence from expert memories

## Integration with Other Systems

### Episodic Memory Manager

```python
from src.ml.supabase_memory_services import SupabaseEpisodicMemoryManager

memory_manager = SupabaseEpisodicMemoryManager(supabase_client)
await memory_manager.store_memory(
    expert_id='conservative_analyzer',
    game_id='KC@BAL_2024',
    memory_data={...}
)
```

### Belief Revision Service

```python
from src.ml.belief_revision_service import BeliefRevisionService

belief_service = BeliefRevisionService(db_config)
await belief_service.detect_revision(
    expert_id='conservative_analyzer',
    old_prediction={...},
    new_prediction={...}
)
```

### Reasoning Chain Logger

```python
from src.ml.reasoning_chain_logger import ReasoningChainLogger

reasoning_logger = ReasoningChainLogger()
await reasoning_logger.log_reasoning_chain(
    expert_id='conservative_analyzer',
    game_id='KC@BAL_2024',
    prediction={...},
    factors=[...],
    monologue="..."
)
```

## Troubleshooting

### Common Issues

1. **No memories retrieved**
   - Check Supabase connection
   - Verify expert_id matches stored memories
   - Ensure memories exist in database

2. **Confidence adjustment too aggressive**
   - Adjustment is capped at ±15%
   - Check memory quality/quantity
   - Review success rate calculation

3. **Async event loop errors**
   - Use async version in async contexts
   - Sync wrapper handles most cases
   - Create new event loop if needed

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailed logs for memory operations
analyzer = ConservativeAnalyzer(memory_service=memory_service)
prediction = analyzer.make_personality_driven_prediction(game_data)
```

## Conclusion

The memory integration enables the `ConservativeAnalyzer` to learn from experience while maintaining full backward compatibility. The system gracefully handles scenarios with or without memory, making it robust for production deployment.

Key benefits:

- ✅ Learning from past predictions
- ✅ Confidence calibration based on success patterns
- ✅ Backward compatible implementation
- ✅ Coordination-ready with hooks
- ✅ Comprehensive test coverage