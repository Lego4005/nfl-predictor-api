# Vector Memory System Documentation

## Overview

The Vector Memory System provides semantic similarity search capabilities for NFL expert epmemories using vector embeddings. This system enables experts to find contextually relevant past experiences to improve prediction accuracy and reasoning quality.

## Architecture

### Core Components

1. **MemoryEmbeddingGenerator** - Generates vector embeddings for game contexts, predictions, and outcomes
2. **VectorMemoryRetrievalService** - Retrieves relevant memories using vector similarity search
3. **MemoryQualityAnalyzer** - Analyzes memory usage patterns and quality metrics

### Database Schema

The system extends the existing `expert_episodic_memories` table with vector embedding columns:

```sql
-- Vector embedding columns (1536 dimensions each)
game_context_embedding vector(1536)    -- Game situation similarity
prediction_embedding vector(1536)      -- Prediction pattern similarity
outcome_embedding vector(1536)         -- Outcome pattern similarity
combined_embedding vector(1536)        -- Comprehensive similarity

-- Embedding metadata
embedding_model VARCHAR(100)           -- Model used for embeddings
embedding_generated_at TIMESTAMP       -- When embeddings were created
embedding_version INTEGER              -- Version for tracking updates
```

## Key Features

### 1. Multi-Dimensional Embeddings

The system generates four types of embeddings for each memory:

- **Game Context**: Weather, teams, injuries, betting lines, situational factors
- **Prediction**: Expert's picks, confidence, reasoning, key factors
- **Outcome**: Actual results, accuracy, game flow
- **Combined**: Comprehensive representation of the entire experience

### 2. Adaptive Retrieval Strategies

Three retrieval strategies optimize for different scenarios:

- **Similarity Only**: Prioritizes semantic similarity (70% weight)
- **Recency Weighted**: Emphasizes recent memories (50% weight)
- **Adaptive**: Adjusts weights based on season timing and context

### 3. Relevance Scoring

Memories are scored using multiple factors:

```python
relevance_score = (
    similarity_weight * similarity_score +
    vividness_weight * memory_vividness +
    recency_weight * (1.0 - age_factor)
)
```

### 4. Quality Analysis

Memory quality is assessed across five dimensions:

- **Relevance Accuracy**: How often retrieved memories are actually useful
- **Prediction Impact**: Effect on prediction accuracy when used
- **Retrieval Efficiency**: How efficiently memories are found and used
- **Content Richness**: Depth and detail of memory content
- **Temporal Stability**: Consistency of relevance over time

## Usage Examples

### Basic Memory Creation

```python
from src.services.memory_embedding_generator import MemoryEmbeddingGenerator

# Initialize service
embedding_generator = MemoryEmbeddingGenerator(supabase_client, openai_api_key)

# Create memory with embeddings
memory_embedding = await embedding_generator.generate_memory_embeddings(
    memory_id="memory_123",
    expert_id="the_momentum_rider",
    game_context={
        'home_team': 'SEA',
        'away_team': 'SF',
        'weather': {'temperature': 45, 'conditions': 'rain'},
        'week': 8
    },
    prediction_data={
        'predicted_winner': 'SF',
        'confidence': 0.72,
        'key_factors': ['weather_advantage']
    },
    outcome_data={
        'winner': 'SF',
        'margin': 4
    }
)
```

### Memory Retrieval for Predictions

```python
from src.services.vector_memory_retrieval_service import VectorMemoryRetrievalService

# Initialize service
retrieval_service = VectorMemoryRetrievalService(supabase_client, embedding_generator)

# Retrieve relevant memories
result = await retrieval_service.retrieve_memories_for_prediction(
    expert_id="the_momentum_rider",
    game_context={
        'home_team': 'GB',
        'away_team': 'CHI',
        'weather': {'temperature': 32, 'conditions': 'snow'},
        'week': 15
    },
    max_memories=7,
    strategy='adaptive'
)

# Use retrieved memories in prediction logic
for memory in result.retrieved_memories:
    print(f"Similar situation: {memory.similarity_score:.3f}")
    print(f"Lessons learned: {memory.lessons_learned}")
```

### Quality Analysis

```python
from src.services.memory_quality_analyzer import MemoryQualityAnalyzer

# Initialize analyzer
quality_analyzer = MemoryQualityAnalyzer(supabase_client)

# Analyze expert's memory profile
profile = await quality_analyzer.generate_expert_memory_profile("the_momentum_rider")

print(f"Total memories: {profile.total_memories}")
print(f"Average quality: {profile.avg_memory_quality:.3f}")
print(f"Recommendations: {profile.recommendations}")

# System-wide analysis
report = await quality_analyzer.generate_comprehensive_analysis_report()
print(f"System quality: {report.system_wide_metrics['avg_system_quality']:.3f}")
```

## Performance Optimization

### Caching Strategy

The retrieval service implements LRU caching with:
- 5-minute cache expiration
- Configurable cache size (default: 1000 entries)
- Cache key based on expert, game context, and parameters

### Vector Index Optimization

HNSW indexes are created for fast similarity search:

```sql
CREATE INDEX idx_episodic_memories_combined_embedding
ON expert_episodic_memories USING hnsw (combined_embedding vector_cosine_ops);
```

### Performance Monitoring

Track key metrics:
- Average retrieval time
- Cache hit rate
- Memory usage
- Successful vs failed retrievals

## Configuration

### Environment Variables

```bash
# Required
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key

# Optional (for better embeddings)
OPENAI_API_KEY=your_openai_key

# Performance tuning
VECTOR_CACHE_SIZE=1000
VECTOR_CACHE_TTL=300
```

### Embedding Models

The system supports multiple embedding models:

- **OpenAI text-embedding-3-small** (1536 dimensions) - Recommended
- **Local LLM fallback** - For offline operation
- **Zero vectors** - Ultimate fallback for testing

## Integration with Training Loop

### Memory Creation During Training

```python
# After each game prediction and outcome
await embedding_generator.generate_memory_embeddings(
    memory_id=memory_id,
    expert_id=expert_id,
    game_context=game_data,
    prediction_data=expert_prediction,
    outcome_data=actual_outcome,
    expert_reasoning=expert_reasoning
)
```

### Memory Retrieval for Predictions

```python
# Before making predictions
relevant_memories = await retrieval_service.retrieve_memories_for_prediction(
    expert_id=expert_id,
    game_context=current_game_context,
    max_memories=7,  # Working memory limit
    strategy='adaptive'
)

# Include memories in expert prompt
memory_context = format_memories_for_prompt(relevant_memories)
expert_prediction = await generate_expert_prediction(
    expert_config=expert_config,
    game_context=game_context,
    memory_context=memory_context
)
```

## Monitoring and Maintenance

### Quality Monitoring

Run regular quality analysis:

```python
# Weekly quality check
report = await quality_analyzer.generate_comprehensive_analysis_report()

# Identify underperforming memories
cleanup_result = await quality_analyzer.cleanup_low_quality_memories(
    quality_threshold=0.3,
    dry_run=True  # Preview before actual cleanup
)
```

### Performance Monitoring

```python
# Check retrieval performance
metrics = await retrieval_service.get_performance_metrics()

if metrics.average_retrieval_time_ms > 100:
    print("Warning: Slow retrieval performance")

if metrics.cache_hit_rate < 0.3:
    print("Warning: Low cache hit rate")
```

### Memory Cleanup

Periodically clean up low-quality memories:

```python
# Remove memories with quality score < 0.3
cleanup_result = await quality_analyzer.cleanup_low_quality_memories(
    quality_threshold=0.3,
    dry_run=False
)

print(f"Deleted {cleanup_result['memories_deleted']} low-quality memories")
```

## Troubleshooting

### Common Issues

1. **Slow Retrieval Performance**
   - Check vector indexes are created
   - Increase cache size
   - Lower similarity threshold
   - Reduce max_memories parameter

2. **Low Quality Scores**
   - Verify embedding generation is working
   - Check memory content richness
   - Ensure memories are being retrieved and used

3. **High Memory Usage**
   - Run memory cleanup
   - Reduce cache size
   - Archive old memories

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger('src.services.memory_embedding_generator').setLevel(logging.DEBUG)
logging.getLogger('src.services.vector_memory_retrieval_service').setLevel(logging.DEBUG)
```

## Testing

Run the integration test:

```bash
cd src/tests
python test_vector_memory_integration.py
```

Run the usage example:

```bash
cd examples
python vector_memory_usage_example.py
```

## Future Enhancements

### Planned Features

1. **Cross-Expert Memory Sharing** - Allow experts to learn from each other's memories
2. **Memory Clustering** - Group similar memories for pattern discovery
3. **Temporal Memory Decay** - Implement more sophisticated decay functions
4. **Memory Importance Weighting** - Weight memories by prediction accuracy impact
5. **Real-time Memory Updates** - Update memory relevance based on new outcomes

### Performance Improvements

1. **Batch Embedding Generation** - Process multiple memories simultaneously
2. **Approximate Nearest Neighbor** - Use faster similarity search algorithms
3. **Memory Compression** - Reduce storage requirements for old memories
4. **Distributed Caching** - Scale caching across multiple instances

## API Reference

See the individual service files for detailed API documentation:

- `src/services/memory_embedding_generator.py`
- `src/services/vector_memory_retrieval_service.py`
- `src/services/memory_quality_analyzer.py`
