# Memory-Enhanced Prediction System - Testing Guide

## Overview

This test suite provides comprehensive validation of the memory-enhanced prediction system, covering baseline operations, memory integration, belief revision, and performance characteristics.

## Test Structure

### Test Files

- **`test_memory_enhanced_predictions.py`** - Complete test suite (16 tests)
  - Unit tests for memory retrieval
  - Integration tests for prediction flow
  - Comparison tests (baseline vs enhanced)
  - Performance benchmarks
  - Edge case handling

### Test Categories

#### 1. Unit Tests - Memory Retrieval Integration (4 tests)

**Test 1: `test_retrieve_memories_no_history`**
- **Scenario**: Prediction with no memories (baseline)
- **Expected**: Empty memory list, no confidence adjustment
- **Purpose**: Validate system handles new experts gracefully

**Test 2: `test_retrieve_relevant_memories`**
- **Scenario**: Prediction with relevant historical memories
- **Expected**: Retrieved memories have similarity scores, confidence adjusts
- **Purpose**: Validate memory retrieval and similarity matching

**Test 3: `test_retrieve_contradictory_memories`**
- **Scenario**: Memories with mixed success/failure outcomes
- **Expected**: System retrieves both positive and negative memories
- **Purpose**: Validate handling of conflicting historical data

**Test 4: `test_memory_similarity_scoring`**
- **Scenario**: Memories with varying similarity to current situation
- **Expected**: Higher similarity scores for more relevant memories
- **Purpose**: Validate similarity algorithm accuracy

#### 2. Integration Tests - Full Prediction Flow (4 tests)

**Test 5: `test_baseline_prediction_no_memory`**
- **Scenario**: Fresh prediction without any memory enhancement
- **Expected**: Standard prediction, zero memory stats
- **Purpose**: Establish baseline performance

**Test 6: `test_memory_enhanced_prediction_with_history`**
- **Scenario**: Prediction using historical memory insights
- **Expected**: Confidence adjustment, learning insights generated
- **Purpose**: Validate full memory-enhanced prediction cycle

**Test 7: `test_belief_revision_on_consecutive_failures`**
- **Scenario**: Multiple consecutive incorrect predictions
- **Expected**: Belief revision triggers, confidence recalibration
- **Purpose**: Validate learning from mistakes

**Test 8: `test_confidence_calibration_from_accuracy`**
- **Scenario**: 10 predictions with 70% accuracy
- **Expected**: System learns accuracy patterns, calibrates confidence
- **Purpose**: Validate statistical learning

#### 3. Comparison Tests - Baseline vs Memory-Enhanced (2 tests)

**Test 9: `test_confidence_adjustment_comparison`**
- **Scenario**: Compare predictions before and after memory training
- **Expected**: Measurable confidence adjustments from memory
- **Purpose**: Quantify memory enhancement impact

**Test 10: `test_learning_insights_generation`**
- **Scenario**: Predictions with various memory patterns
- **Expected**: Relevant learning insights in results
- **Purpose**: Validate insight extraction quality

#### 4. Performance Tests - Memory Lookup Speed (3 tests)

**Test 11: `test_memory_retrieval_performance`**
- **Scenario**: Retrieve from 50 memories
- **Expected**: < 1 second retrieval time
- **Purpose**: Ensure scalability

**Test 12: `test_full_prediction_performance`**
- **Scenario**: Complete prediction cycle with 15 experts
- **Expected**: < 5 seconds total time
- **Purpose**: Validate production readiness

**Test 13: `test_memory_consolidation_performance`**
- **Scenario**: Consolidate 20 memories
- **Expected**: < 2 seconds consolidation time
- **Purpose**: Validate maintenance operations

#### 5. Edge Cases and Error Handling (3 tests)

**Test 14: `test_empty_memory_handling`**
- **Scenario**: Expert with no memory history
- **Expected**: Graceful fallback to baseline
- **Purpose**: Ensure robustness

**Test 15: `test_memory_with_missing_data`**
- **Scenario**: Incomplete memory records
- **Expected**: No errors, graceful degradation
- **Purpose**: Validate data quality handling

**Test 16: `test_high_volume_concurrent_predictions`**
- **Scenario**: 5 concurrent prediction requests
- **Expected**: All complete successfully
- **Purpose**: Validate concurrency handling

## Running the Tests

### Prerequisites

1. **Database Setup**
   ```bash
   # Set environment variables
   export DB_HOST=localhost
   export DB_PORT=5432
   export DB_USER=postgres
   export DB_PASSWORD=your_password
   export DB_NAME=nfl_predictor_test
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio
   ```

3. **Initialize Test Database**
   ```bash
   python scripts/setup_test_database.py
   ```

### Run All Tests

```bash
# Run complete test suite
pytest tests/test_memory_enhanced_predictions.py -v -s

# Run with coverage
pytest tests/test_memory_enhanced_predictions.py --cov=src.ml --cov-report=html

# Run specific test class
pytest tests/test_memory_enhanced_predictions.py::TestMemoryRetrievalIntegration -v

# Run specific test
pytest tests/test_memory_enhanced_predictions.py::TestMemoryRetrievalIntegration::test_retrieve_memories_no_history -v
```

### Run by Category

```bash
# Unit tests only
pytest tests/test_memory_enhanced_predictions.py::TestMemoryRetrievalIntegration -v

# Integration tests only
pytest tests/test_memory_enhanced_predictions.py::TestMemoryEnhancedPredictionFlow -v

# Performance tests only
pytest tests/test_memory_enhanced_predictions.py::TestMemoryPerformance -v

# Comparison tests only
pytest tests/test_memory_enhanced_predictions.py::TestBaselineVsMemoryEnhanced -v
```

## Test Results Interpretation

### Success Criteria

**Unit Tests**
- ✅ Memory retrieval returns correct number of results
- ✅ Similarity scoring ranks memories appropriately
- ✅ Contradictory memories handled without errors

**Integration Tests**
- ✅ Baseline predictions complete successfully
- ✅ Memory enhancement adjusts confidence (±0.02 to ±0.10)
- ✅ Belief revision triggers after 2-3 consecutive failures
- ✅ Confidence calibration converges to actual accuracy

**Performance Tests**
- ✅ Memory retrieval: < 1 second
- ✅ Full prediction cycle: < 5 seconds
- ✅ Memory consolidation: < 2 seconds

### Expected Output

```
MEMORY-ENHANCED PREDICTION SYSTEM - COMPREHENSIVE TEST SUITE
================================================================================

Test 1: test_retrieve_memories_no_history
✅ Test 1 passed: No memories retrieved for new expert
PASSED

Test 2: test_retrieve_relevant_memories
✅ Test 2 passed: Retrieved 5 relevant memories
PASSED

Test 3: test_retrieve_contradictory_memories
✅ Test 3 passed: Retrieved 4 contradictory memories
   Emotional states: {'satisfaction', 'disappointment'}
PASSED

[... continues for all 16 tests ...]

================================================================================
16 passed in 12.34s
```

## Metrics and KPIs

### Memory Enhancement Metrics

1. **Confidence Adjustment**
   - Typical range: ±0.02 to ±0.10
   - Positive adjustment: High success rate in similar situations (>70%)
   - Negative adjustment: Low success rate in similar situations (<40%)

2. **Memory Utilization**
   - Average memories consulted per prediction: 3-8
   - Experts with memory insights: 60-90% (after training)
   - Memory retrieval hit rate: >80%

3. **Learning Effectiveness**
   - Accuracy improvement: +3% to +8% over baseline
   - Confidence calibration error: <5% after 20+ predictions
   - Belief revision frequency: 10-20% of predictions

### Performance Benchmarks

| Operation | Target | Actual (Expected) |
|-----------|--------|-------------------|
| Memory retrieval (10 items) | <100ms | 20-50ms |
| Single expert prediction | <200ms | 100-150ms |
| Full council prediction (15 experts) | <5s | 2-4s |
| Memory consolidation (20 items) | <500ms | 100-300ms |
| Concurrent predictions (5x) | <10s | 5-8s |

## Troubleshooting

### Common Issues

**Issue: Database connection errors**
```bash
# Solution: Check environment variables
echo $DB_HOST $DB_PORT $DB_USER $DB_NAME

# Verify database is running
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
```

**Issue: Async test failures**
```bash
# Solution: Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Run with explicit asyncio mode
pytest tests/test_memory_enhanced_predictions.py --asyncio-mode=auto
```

**Issue: Performance tests fail**
```bash
# Solution: Check system resources
# Performance targets assume:
# - Modern CPU (4+ cores)
# - 8GB+ RAM
# - SSD storage
# - Local database connection

# Run performance tests in isolation
pytest tests/test_memory_enhanced_predictions.py::TestMemoryPerformance -v
```

**Issue: Memory retrieval returns no results**
```bash
# Solution: Verify database schema
python scripts/validate_episodic_memory_schema.py

# Check if memories were created
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \
  "SELECT COUNT(*) FROM expert_episodic_memories"
```

## Test Data Patterns

### Sample Prediction Data
```python
{
    'expert_id': 'conservative_analyzer',
    'winner_prediction': 'KC',
    'winner_confidence': 0.75,
    'spread_prediction': -3.5,
    'reasoning': 'Strong home field advantage',
    'key_factors': ['home_field', 'offensive_epa']
}
```

### Sample Outcome Data
```python
{
    'winner': 'BAL',
    'home_score': 17,
    'away_score': 20,
    'margin': 3,
    'total_score': 37
}
```

### Sample Memory Statistics
```python
{
    'total_memories_consulted': 45,
    'experts_with_memories': 12,
    'average_confidence_adjustment': 0.023
}
```

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Memory System Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: nfl_predictor_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_USER: postgres
          DB_PASSWORD: postgres
          DB_NAME: nfl_predictor_test
        run: |
          pytest tests/test_memory_enhanced_predictions.py \
            -v --cov=src.ml --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## Next Steps

After running these tests:

1. **Review Results**: Check all 16 tests pass
2. **Analyze Metrics**: Compare actual vs expected performance
3. **Optimize**: Address any performance bottlenecks
4. **Integrate**: Add to CI/CD pipeline
5. **Monitor**: Set up alerts for production metrics

## Contributing

To add new tests:

1. Follow the existing test structure
2. Add docstrings explaining scenario and expected outcome
3. Include performance assertions where relevant
4. Update this guide with new test descriptions

## References

- **Memory System Architecture**: `/docs/EPISODIC_MEMORY_ARCHITECTURE.md`
- **Belief Revision System**: `/docs/BELIEF_REVISION_DESIGN.md`
- **Performance Tuning**: `/docs/PERFORMANCE_OPTIMIZATION.md`
- **API Integration**: `/docs/MEMORY_API_INTEGRATION.md`