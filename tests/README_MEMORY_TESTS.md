# Memory-Enhanced Prediction System - Test Suite

## 🚀 Quick Start

### Run All Tests (1 command)

```bash
./tests/run_memory_tests.sh --mode all --verbose
```

### Expected Output

```
✅ 16/16 tests passed in 12.45s
✅ All tests passed! 🎉
```

## 📁 Files Created

| File | Purpose | Size |
|------|---------|------|
| `test_memory_enhanced_predictions.py` | **Main test suite** - 16 comprehensive tests | 31KB |
| `run_memory_tests.sh` | **Test runner script** - Easy execution | 6KB |
| `MEMORY_TESTING_GUIDE.md` | **Detailed documentation** - Setup, running, troubleshooting | 12KB |
| `MEMORY_TEST_SCENARIOS.md` | **Quick reference** - All test scenarios in matrix format | 12KB |
| `MEMORY_TEST_SUMMARY.md` | **Executive summary** - Overview and metrics | 11KB |

## 🎯 Test Coverage

### 16 Tests Across 5 Categories

1. **Unit Tests (4)** - Memory retrieval integration
2. **Integration Tests (4)** - Full prediction flow
3. **Comparison Tests (2)** - Baseline vs memory-enhanced
4. **Performance Tests (3)** - Memory lookup speed
5. **Edge Cases (3)** - Error handling and robustness

## ✅ Test Scenarios Covered

### Core Functionality
- ✅ Prediction with no memories (baseline)
- ✅ Prediction with relevant memories (confidence adjustment)
- ✅ Prediction with contradictory memories (conflict handling)
- ✅ Memory similarity scoring accuracy
- ✅ Full prediction cycle with memory enhancement

### Learning Mechanisms
- ✅ Belief revision triggers (consecutive failures)
- ✅ Confidence calibration (learns from accuracy)
- ✅ Learning insights generation
- ✅ Memory pattern analysis

### Performance
- ✅ Memory retrieval speed (< 1 second)
- ✅ Full prediction performance (< 5 seconds)
- ✅ Memory consolidation speed (< 2 seconds)

### Robustness
- ✅ Empty memory handling
- ✅ Incomplete data handling
- ✅ Concurrent request handling

## 🔧 Setup (One-Time)

```bash
# 1. Set environment variables
export DB_HOST=localhost
export DB_PORT=5432
export DB_USER=postgres
export DB_PASSWORD=your_password
export DB_NAME=nfl_predictor_test

# 2. Install dependencies
pip install pytest pytest-asyncio pytest-cov

# 3. Make test runner executable (already done)
chmod +x tests/run_memory_tests.sh
```

## 🎮 Usage Examples

### Run All Tests
```bash
./tests/run_memory_tests.sh --mode all --verbose
```

### Run Unit Tests Only
```bash
./tests/run_memory_tests.sh --mode unit --verbose
```

### Run Integration Tests Only
```bash
./tests/run_memory_tests.sh --mode integration --verbose
```

### Run Performance Tests Only
```bash
./tests/run_memory_tests.sh --mode performance
```

### Run Comparison Tests Only
```bash
./tests/run_memory_tests.sh --mode comparison
```

### Run Edge Case Tests Only
```bash
./tests/run_memory_tests.sh --mode edge
```

### Run with Coverage Report
```bash
./tests/run_memory_tests.sh --mode all --coverage
# Opens htmlcov/index.html
```

### Run Tests in Parallel
```bash
./tests/run_memory_tests.sh --mode all --parallel
```

## 📊 Success Criteria

### Must Pass (Critical)
- ✅ All 16 tests pass
- ✅ No exceptions or errors
- ✅ Memory retrieval works correctly
- ✅ Predictions complete successfully

### Should Achieve (Important)
- ✅ Performance benchmarks met
- ✅ Code coverage > 80%
- ✅ Learning mechanisms functional
- ✅ Confidence adjustments within expected range (±0.02 to ±0.10)

### Nice to Have (Optional)
- ✅ All tests pass in < 10 seconds
- ✅ Parallel execution successful
- ✅ Zero warnings in output

## 🐛 Troubleshooting

### Tests Won't Run
```bash
# Check pytest installed
python3 -m pytest --version

# Install if missing
pip install pytest pytest-asyncio
```

### Database Connection Errors
```bash
# Check environment variables
echo $DB_HOST $DB_PORT $DB_USER $DB_NAME

# Test database connection
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1"
```

### Performance Tests Fail
```bash
# Run in isolation
./tests/run_memory_tests.sh --mode performance

# Check system resources
top
df -h
```

### Specific Test Fails
```bash
# Run single test with verbose output
pytest tests/test_memory_enhanced_predictions.py::TestMemoryRetrievalIntegration::test_retrieve_memories_no_history -vv -s
```

## 📚 Documentation

- **Quick Start**: This file (you are here!)
- **Detailed Guide**: `MEMORY_TESTING_GUIDE.md` - Complete documentation
- **Test Scenarios**: `MEMORY_TEST_SCENARIOS.md` - All scenarios in matrix format
- **Summary**: `MEMORY_TEST_SUMMARY.md` - Executive overview

## 🎯 What Each Test Validates

| Test # | Validates | Expected Result |
|--------|-----------|-----------------|
| 1 | Fresh expert baseline | No errors, empty memories |
| 2 | Memory retrieval | 3-8 relevant memories |
| 3 | Contradictory data | Both success/failure memories |
| 4 | Similarity scoring | Higher scores for similar games |
| 5 | Baseline prediction | Standard operation |
| 6 | Memory enhancement | Confidence adjustment |
| 7 | Consecutive failures | Belief revision triggers |
| 8 | Accuracy tracking | Calibration to 70% |
| 9 | Before/after | Measurable improvement |
| 10 | Learning insights | Actionable insights |
| 11 | Retrieval speed | < 1 second |
| 12 | Full cycle speed | < 5 seconds |
| 13 | Consolidation speed | < 2 seconds |
| 14 | Empty handling | Graceful fallback |
| 15 | Missing data | No exceptions |
| 16 | Concurrent load | All requests succeed |

## 📈 Expected Metrics

### Memory Enhancement Impact
- **Confidence Adjustment**: ±0.02 to ±0.10
- **Memories per Prediction**: 3-8
- **Experts with Memories**: 60-90% (after training)
- **Accuracy Improvement**: +3% to +8%

### Performance Targets
- **Memory Retrieval**: < 100ms
- **Single Prediction**: < 200ms
- **Full Council (15 experts)**: < 5 seconds
- **Memory Creation**: < 50ms

## ✨ Key Features Tested

### Memory Retrieval
- ✅ Similarity-based retrieval
- ✅ Emotional state tracking
- ✅ Vividness scoring
- ✅ Memory decay modeling

### Prediction Enhancement
- ✅ Confidence adjustment from history
- ✅ Learning insights generation
- ✅ Pattern recognition
- ✅ Weather/market pattern learning

### Learning Mechanisms
- ✅ Belief revision on failures
- ✅ Confidence calibration
- ✅ Statistical learning
- ✅ Accuracy tracking

### System Robustness
- ✅ Graceful degradation
- ✅ Error handling
- ✅ Concurrent operations
- ✅ Data validation

## 🔄 Continuous Integration

Add to `.github/workflows/tests.yml`:

```yaml
- name: Run Memory Tests
  env:
    DB_HOST: localhost
    DB_PORT: 5432
    DB_USER: postgres
    DB_PASSWORD: postgres
    DB_NAME: nfl_predictor_test
  run: |
    ./tests/run_memory_tests.sh --mode all --coverage
```

## 📞 Support

**Questions?** Check:
1. `MEMORY_TESTING_GUIDE.md` - Comprehensive guide
2. `MEMORY_TEST_SCENARIOS.md` - Scenario details
3. `MEMORY_TEST_SUMMARY.md` - Executive summary

**Issues?**
- Review troubleshooting section above
- Check logs for detailed error messages
- Verify database connection and schema
- Ensure all dependencies installed

---

**Total Test Files**: 5 files
**Total Tests**: 16 comprehensive tests
**Total Lines**: ~2,000 lines (code + documentation)
**Estimated Setup Time**: 5 minutes
**Estimated Test Time**: 12-15 seconds

**Ready to test? Run:**
```bash
./tests/run_memory_tests.sh --mode all --verbose
```