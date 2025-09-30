# Memory-Enhanced Prediction System - Test Scenarios Quick Reference

## Test Scenario Matrix

| # | Test Name | Scenario | Input | Expected Output | Validation |
|---|-----------|----------|-------|-----------------|------------|
| **1** | No Memories Baseline | Fresh expert, no history | New game data | Empty memory list, baseline prediction | `len(memories) == 0` |
| **2** | Relevant Memories | Expert with 5 similar experiences | Similar game matchup | 3-5 memories retrieved, confidence adjustment | `len(memories) > 0`, similarity scores present |
| **3** | Contradictory Memories | Expert with mixed success/failure | Same matchup, varied outcomes | Both positive and negative memories | Mixed emotional states |
| **4** | Similarity Scoring | Highly similar vs dissimilar memories | Two memory types | Higher scores for similar situations | `similar_score > dissimilar_score` |
| **5** | Baseline Prediction | No memory enhancement | Standard game data | Standard prediction, zero memory stats | `memory_stats == 0` |
| **6** | Memory-Enhanced Prediction | Expert with training history | Game with similar context | Adjusted confidence, learning insights | `memory_enhanced == True`, insights present |
| **7** | Consecutive Failures | 3 consecutive wrong predictions | Same matchup repeated | Belief revision, confidence decrease | Confidence adjustment detected |
| **8** | Confidence Calibration | 10 predictions, 70% accuracy | Mixed correct/incorrect | Calibrated confidence, accuracy tracking | `recent_accuracy ≈ 0.70` |
| **9** | Confidence Comparison | Before and after training | Same game data | Measurable adjustment from memory | `enhanced_conf != baseline_conf` |
| **10** | Learning Insights | Predictions with patterns | Various scenarios | Generated learning insights | `total_insights > 0` |
| **11** | Retrieval Performance | 50 memories in database | Query for 10 memories | Fast retrieval (< 1s) | `elapsed_time < 1.0` |
| **12** | Full Cycle Performance | All 15 experts | Complete prediction cycle | Fast completion (< 5s) | `elapsed_time < 5.0` |
| **13** | Consolidation Performance | 20 memories, 5 frequently accessed | Consolidate memories | Fast consolidation (< 2s) | `elapsed_time < 2.0` |
| **14** | Empty Memory Graceful | Expert with zero memories | Request prediction | Successful baseline prediction | No errors, fallback works |
| **15** | Incomplete Data | Memory with minimal fields | Store and retrieve | Graceful handling | No exceptions raised |
| **16** | Concurrent Load | 5 simultaneous requests | Parallel predictions | All complete successfully | All 5 return valid results |

## Detailed Scenario Descriptions

### Scenario 1: No Memories (Baseline)
```python
# Setup
expert_id = "new_expert_001"
situation = {"home_team": "KC", "away_team": "BAL"}

# Expected
memories = []
confidence_adjustment = 0.0
memory_enhanced = False

# Validates
- New experts can make predictions
- System doesn't break without memories
- Baseline prediction quality maintained
```

### Scenario 2: Relevant Memories
```python
# Setup
expert_id = "experienced_expert"
historical_games = [
    {"teams": ["KC", "BAL"], "outcome": "KC wins", "confidence": 0.75},
    {"teams": ["KC", "BUF"], "outcome": "KC wins", "confidence": 0.80},
    # ... 3 more similar games
]

# Expected
memories = 3-5 relevant memories
similarity_scores = [0.7, 0.65, 0.60, ...]
confidence_adjustment = +0.03 to +0.08

# Validates
- Memory retrieval works correctly
- Similarity algorithm ranks appropriately
- Confidence adjusts based on past success
```

### Scenario 3: Contradictory Memories
```python
# Setup
expert_id = "inconsistent_expert"
historical_games = [
    {"prediction": "KC", "actual": "KC"},    # Success
    {"prediction": "KC", "actual": "BAL"},   # Failure
    {"prediction": "KC", "actual": "KC"},    # Success
    {"prediction": "KC", "actual": "BAL"},   # Failure
]

# Expected
memories_retrieved = 4
emotional_states = ["satisfaction", "disappointment", "satisfaction", "disappointment"]
confidence_adjustment = -0.02 to +0.02  # Neutral or cautious

# Validates
- System handles conflicting evidence
- Doesn't over-rely on any single pattern
- Balances positive and negative memories
```

### Scenario 4: Similarity Scoring
```python
# Setup
memory_similar = {
    "teams": ["KC", "BAL"],
    "confidence": 0.75,
    "reasoning_factors": ["home_field", "offensive_epa"]
}

memory_dissimilar = {
    "teams": ["SF", "NYG"],
    "confidence": 0.55,
    "reasoning_factors": ["rushing_yards"]
}

current_situation = {
    "teams": ["KC", "BAL"],
    "confidence": 0.75,
    "reasoning_factors": ["home_field", "offensive_epa"]
}

# Expected
similarity_similar = 0.85 (high)
similarity_dissimilar = 0.25 (low)

# Validates
- Team overlap weighted correctly (30%)
- Confidence proximity matters (20%)
- Reasoning factor overlap counts (30%)
- Vividness bonus applied (20%)
```

### Scenario 5-6: Baseline vs Enhanced Comparison
```python
# Baseline (Test 5)
prediction_baseline = {
    "confidence": 0.75,
    "memory_enhanced": False,
    "memories_consulted": 0
}

# Enhanced (Test 6)
prediction_enhanced = {
    "confidence": 0.78,  # Adjusted
    "memory_enhanced": True,
    "memories_consulted": 5,
    "confidence_boost": +0.03,
    "learning_insights": [
        "High success rate (80%) in similar situations",
        "Strong performance in similar weather conditions"
    ]
}

# Validates
- Memory enhancement adds value
- Insights are actionable
- Confidence adjustment is reasonable
```

### Scenario 7: Belief Revision
```python
# Consecutive failures trigger
prediction_1 = {"winner": "KC", "confidence": 0.75}  # Wrong
prediction_2 = {"winner": "KC", "confidence": 0.72}  # Wrong (slight decrease)
prediction_3 = {"winner": "KC", "confidence": 0.65}  # Major revision

# Or switch prediction
prediction_3_alt = {"winner": "BAL", "confidence": 0.60}  # Changed pick

# Validates
- System learns from mistakes
- Confidence decreases appropriately
- May change prediction entirely
- Belief revision logged
```

### Scenario 8: Confidence Calibration
```python
# After 10 predictions with 70% accuracy
predictions = [
    {"confidence": 0.75, "correct": True},
    {"confidence": 0.80, "correct": True},
    # ... 8 more (7 correct, 3 incorrect)
]

# System learns
recent_accuracy = 0.70
confidence_calibration = "learns to be 70% confident when 70% accurate"

# Future predictions
new_prediction_confidence ≈ 0.70 (calibrated to actual performance)

# Validates
- Statistical learning works
- Over-confidence is corrected
- Under-confidence is boosted
- Convergence to true accuracy
```

## Performance Benchmarks

### Target Metrics

| Operation | Target | Baseline | With Optimization |
|-----------|--------|----------|-------------------|
| Memory retrieval (10 items) | < 100ms | 50ms | 20ms |
| Similarity scoring (50 items) | < 200ms | 150ms | 80ms |
| Single prediction (no memory) | < 100ms | 80ms | 60ms |
| Single prediction (with memory) | < 200ms | 180ms | 120ms |
| Full council (15 experts) | < 5s | 3.5s | 2.2s |
| Memory creation | < 50ms | 30ms | 20ms |
| Memory consolidation (20 items) | < 500ms | 300ms | 150ms |
| Concurrent requests (5x) | < 10s | 8s | 5s |

### Load Testing Scenarios

**Light Load**
- 1 prediction/second
- Expected: < 200ms response time
- Expected: 0% error rate

**Medium Load**
- 10 predictions/second
- Expected: < 500ms response time
- Expected: < 1% error rate

**Heavy Load**
- 50 predictions/second
- Expected: < 2s response time
- Expected: < 5% error rate

**Stress Test**
- 100 predictions/second
- Expected: System remains stable
- Expected: Graceful degradation

## Test Data Templates

### Universal Game Data Template
```python
UniversalGameData(
    home_team="KC",
    away_team="BAL",
    game_time="2024-01-15 21:00:00",
    location="Kansas City",
    weather={
        'temperature': 28,
        'wind_speed': 22,
        'conditions': 'Snow',
        'humidity': 85
    },
    injuries={
        'home': [
            {'position': 'WR', 'severity': 'questionable', 'probability_play': 0.6}
        ],
        'away': [
            {'position': 'RB', 'severity': 'doubtful', 'probability_play': 0.3}
        ]
    },
    line_movement={
        'opening_line': -2.5,
        'current_line': -1.0,
        'public_percentage': 78
    },
    team_stats={
        'home': {
            'offensive_yards_per_game': 415,
            'defensive_yards_allowed': 298
        },
        'away': {
            'offensive_yards_per_game': 389,
            'defensive_yards_allowed': 312
        }
    }
)
```

### Prediction Template
```python
{
    'expert_id': 'conservative_analyzer',
    'expert_name': 'The Analyst',
    'winner_prediction': 'KC',
    'winner_confidence': 0.75,
    'spread_prediction': -3.5,
    'total_prediction': 45.5,
    'reasoning': 'Strong home field advantage and offensive metrics favor KC',
    'key_factors': ['home_field', 'offensive_epa', 'weather_conditions'],
    'memory_enhanced': True,
    'similar_experiences': 5,
    'memory_confidence_boost': 0.03,
    'learning_insights': [
        'High success rate (80%) in similar situations',
        'Strong performance in similar weather conditions'
    ]
}
```

### Outcome Template
```python
{
    'winner': 'BAL',
    'home_score': 17,
    'away_score': 20,
    'margin': 3,
    'total_score': 37,
    'spread_result': 'away_cover',
    'total_result': 'under'
}
```

## Quick Test Commands

```bash
# Run all tests
pytest tests/test_memory_enhanced_predictions.py -v

# Run specific scenario
pytest tests/test_memory_enhanced_predictions.py::TestMemoryRetrievalIntegration::test_retrieve_memories_no_history -v

# Run with performance profiling
pytest tests/test_memory_enhanced_predictions.py --profile

# Run with coverage
pytest tests/test_memory_enhanced_predictions.py --cov=src.ml --cov-report=html

# Run in parallel
pytest tests/test_memory_enhanced_predictions.py -n auto

# Run with detailed output
pytest tests/test_memory_enhanced_predictions.py -vv -s

# Run performance tests only
pytest tests/test_memory_enhanced_predictions.py::TestMemoryPerformance -v

# Run and generate report
pytest tests/test_memory_enhanced_predictions.py --html=report.html --self-contained-html
```

## Validation Checklist

### Before Running Tests
- [ ] Database is running and accessible
- [ ] Environment variables are set (DB_HOST, DB_PORT, etc.)
- [ ] pytest and pytest-asyncio are installed
- [ ] Test database is initialized with schema
- [ ] No other tests are modifying the database

### After Tests Complete
- [ ] All 16 tests passed
- [ ] No memory leaks detected
- [ ] Performance benchmarks met
- [ ] Coverage > 80%
- [ ] No errors in logs

### For Production Deployment
- [ ] All test scenarios pass consistently
- [ ] Performance under load is acceptable
- [ ] Memory consumption is stable
- [ ] Concurrent requests handle correctly
- [ ] Error handling is robust

## Debugging Failed Tests

### Test 1-4 Failures (Memory Retrieval)
**Check**: Database connection, schema, expert IDs match

### Test 5-8 Failures (Prediction Flow)
**Check**: Service initialization, async operations, memory creation

### Test 9-10 Failures (Comparison)
**Check**: Memory training data, confidence calculation logic

### Test 11-13 Failures (Performance)
**Check**: Database performance, connection pooling, indexing

### Test 14-16 Failures (Edge Cases)
**Check**: Error handling, null checks, concurrency locks