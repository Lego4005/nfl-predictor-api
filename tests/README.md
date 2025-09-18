# NFL Predictor API - Test Suite Documentation

## Overview

This comprehensive test suite provides extensive coverage for the NFL Predictor Platform, a sophisticated system combining real-time data processing, machine learning predictions, and WebSocket-based live updates.

## Test Architecture

### Test Categories

#### 🧪 Unit Tests (`tests/unit/`)
- **Purpose**: Test individual components in isolation
- **Coverage**: Functions, classes, and small modules
- **Speed**: Fast execution (< 1 second per test)
- **Dependencies**: Mocked external services
- **Pattern**: Arrange-Act-Assert (AAA)

#### 🔗 Integration Tests (`tests/integration/`)
- **Purpose**: Test component interactions
- **Coverage**: Database operations, API endpoints, service integrations
- **Speed**: Medium execution (1-10 seconds per test)
- **Dependencies**: Test database and Redis
- **Pattern**: Given-When-Then

#### 🌐 End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete user workflows
- **Coverage**: Full system functionality from API to database
- **Speed**: Slow execution (10+ seconds per test)
- **Dependencies**: Full test environment
- **Pattern**: User journey scenarios

#### 🤖 ML Model Tests (`tests/ml/`)
- **Purpose**: Validate machine learning models and pipelines
- **Coverage**: Model training, predictions, feature engineering
- **Speed**: Variable (depends on model complexity)
- **Dependencies**: Test datasets and model artifacts
- **Pattern**: Data-Model-Validation

#### 🚀 Performance Tests (`tests/performance/`)
- **Purpose**: Ensure system meets performance requirements
- **Coverage**: Response times, throughput, resource usage
- **Speed**: Variable (benchmarking duration)
- **Dependencies**: Performance baseline data
- **Pattern**: Benchmark-Compare-Assert

#### 🔐 Security Tests (`tests/security/`)
- **Purpose**: Validate security measures and vulnerability prevention
- **Coverage**: Authentication, authorization, input validation
- **Speed**: Medium execution
- **Dependencies**: Security test scenarios
- **Pattern**: Attack-Defend-Verify

## Test Configuration

### Core Configuration Files

#### `pytest.ini`
```ini
[tool:pytest]
# Comprehensive pytest configuration with:
# - Coverage reporting (HTML, XML, terminal)
# - Async test support
# - Parallel execution
# - Custom markers for test categorization
# - Performance thresholds
```

#### `jest.config.js`
```javascript
// Frontend test configuration for:
// - React component testing
// - TypeScript support
// - Coverage thresholds (80%+)
// - Mock configurations
// - Path aliases
```

#### `conftest.py`
```python
# Global test fixtures including:
# - Database session management
# - Redis client mocking
# - HTTP client setup
# - Sample data generators
# - Performance profiling utilities
```

### Environment Setup

#### Test Database
- **Engine**: PostgreSQL 15
- **URL**: `postgresql://test_user:test_password@localhost:5433/nfl_predictor_test`
- **Isolation**: Each test runs in a transaction that's rolled back
- **Fixtures**: Pre-loaded with sample NFL data

#### Test Cache
- **Engine**: Redis 7
- **URL**: `redis://localhost:6380/0`
- **Isolation**: Different Redis databases for different test types
- **Mocking**: FakeRedis for unit tests

#### External APIs
- **Mocking**: Comprehensive mock responses for all external services
- **Patterns**: Realistic data patterns matching production APIs
- **Error Simulation**: Network failures, rate limiting, invalid responses

## Running Tests

### Quick Start

```bash
# Install dependencies
make install

# Run basic test suite
make test

# Run all tests with coverage
make test-all

# Start test services
make start-services
```

### Detailed Commands

#### Unit Tests
```bash
# Run unit tests with coverage
make test-unit

# Run specific test file
make test-single FILE=tests/unit/test_predictions.py

# Run tests with specific marker
make test-marker MARKER=ml

# Run tests in watch mode
make test-watch
```

#### Integration Tests
```bash
# Run integration tests (requires services)
make test-integration

# Run with debugging
make test-debug

# Run with custom database
DATABASE_URL=postgresql://user:pass@host/db make test-integration
```

#### Performance Tests
```bash
# Run performance benchmarks
make benchmark

# Run load tests
make load-test

# Check for performance regressions
make regression-test
```

#### Frontend Tests
```bash
# Run React/TypeScript tests
make test-frontend

# Run with coverage
npm test -- --coverage

# Run specific test suite
npx vitest run tests/frontend/components/
```

### Docker Testing

```bash
# Run tests in Docker environment
make docker-test

# Start test services with Docker
make docker-up

# View logs
make docker-logs

# Clean up
make docker-clean
```

## Test Data and Fixtures

### Database Fixtures (`tests/fixtures/database_fixtures.py`)

#### Team Data
```python
# 32 NFL teams with complete information
teams = NFLTestDataFactory().get_teams()
# - Team IDs, names, conferences, divisions
# - Colors, logos, stadium information
# - Historical performance data
```

#### Game Data
```python
# Comprehensive game scenarios
game = factory.create_game(
    home_team="KC",
    away_team="DET",
    status="live",  # scheduled, live, completed
    weather_conditions="clear"
)
```

#### Player Statistics
```python
# Realistic player performance data
stats = factory.create_player_stats(
    position="QB",
    season=2024,
    performance_level="elite"  # rookie, average, good, elite
)
```

#### ML Training Data
```python
# Feature-rich datasets for model testing
dataset = create_sample_dataset(size=1000)
# - 11 engineered features
# - Realistic target distributions
# - Historical seasonal patterns
```

### Mock API Responses (`tests/fixtures/mock_responses.py`)

#### External API Mocking
- **NFL API**: Game schedules, scores, player stats
- **ESPN API**: Live game data, team information
- **Weather API**: Stadium weather conditions
- **Odds API**: Betting lines and market data

#### WebSocket Messages
```python
# Live game update simulation
messages = create_websocket_test_scenario("game_001")
# - Score updates
# - Prediction changes
# - System health notifications
# - Error handling scenarios
```

## Coverage and Quality Metrics

### Coverage Thresholds

| Component | Minimum Coverage | Target Coverage |
|-----------|------------------|-----------------|
| Core API | 85% | 90% |
| ML Models | 80% | 85% |
| Database Layer | 90% | 95% |
| WebSocket Service | 75% | 80% |
| Frontend Components | 80% | 85% |

### Quality Gates

#### Code Quality
- **Black**: Code formatting compliance
- **isort**: Import organization
- **Flake8**: PEP 8 compliance and code complexity
- **MyPy**: Type safety validation
- **Bandit**: Security vulnerability scanning

#### Test Quality
- **Test Isolation**: No shared state between tests
- **Deterministic**: Reproducible results with fixed seeds
- **Fast Feedback**: Unit tests complete in < 30 seconds
- **Clear Assertions**: Descriptive error messages

## Performance Baselines

### API Response Times

| Endpoint | P50 (ms) | P95 (ms) | P99 (ms) |
|----------|----------|----------|----------|
| `/health` | 10 | 25 | 50 |
| `/games` | 100 | 250 | 500 |
| `/predictions` | 150 | 400 | 800 |
| `/teams/{id}/stats` | 75 | 200 | 400 |

### ML Model Performance

| Model | Prediction Time (ms) | Accuracy Threshold | Memory Usage (MB) |
|-------|---------------------|-------------------|-------------------|
| XGBoost | 50 | 65% | 100 |
| LightGBM | 30 | 63% | 80 |
| Neural Network | 100 | 67% | 200 |
| Ensemble | 200 | 70% | 400 |

### System Resource Usage

| Component | CPU (%) | Memory (MB) | Disk I/O (MB/s) |
|-----------|---------|-------------|-----------------|
| API Server | 15 | 200 | 5 |
| ML Service | 30 | 500 | 2 |
| WebSocket | 10 | 100 | 1 |
| Database | 20 | 300 | 10 |

## CI/CD Integration

### GitHub Actions Workflow

#### Parallel Execution
```yaml
# Six parallel job execution:
# 1. Code quality (linting, security)
# 2. Backend unit tests
# 3. Frontend tests
# 4. Integration tests
# 5. Performance tests
# 6. Security scans
```

#### Automated Reporting
- **Coverage Reports**: Uploaded to Codecov
- **Performance Metrics**: Stored as artifacts
- **Security Scans**: OWASP ZAP integration
- **Test Results**: JUnit XML for GitHub integration

#### Deployment Gates
- All tests must pass for deployment
- Coverage thresholds enforced
- Performance regression detection
- Security vulnerability blocking

### Pre-commit Hooks

#### Automated Checks
- Code formatting (Black, isort)
- Linting (Flake8, ESLint)
- Type checking (MyPy, TypeScript)
- Security scanning (Bandit)
- Secrets detection
- Test coverage validation

## Test Utilities

### Performance Testing (`tests/utils/performance_utils.py`)

```python
# Performance profiling
with performance_test("api_endpoint_test") as profiler:
    response = await client.get("/predictions")
    profiler.record_response_time(response.elapsed.total_seconds())

# Load testing
load_tester = LoadTestRunner("API Load Test")
results = await load_tester.run_concurrent_requests(
    request_func=make_request,
    concurrent_users=50,
    requests_per_user=20
)
```

### Test Helpers (`tests/utils/test_helpers.py`)

```python
# API testing
api_client = APITestClient(test_client)
response = api_client.get("/games")
api_client.assert_success()
api_client.assert_json_structure(["games", "total", "page"])

# Database testing
db_helper = DatabaseTestHelper(db_session)
game = await db_helper.insert_test_data(Game, game_data)
count = await db_helper.count_records(Game)

# ML testing
ml_helper = MLTestHelper()
features = ml_helper.create_sample_features(n_samples=100)
metrics = ml_helper.assert_model_performance(y_true, y_pred, min_accuracy=0.65)
```

### WebSocket Testing

```python
# Mock WebSocket client
async with mock_websocket_connection() as ws_client:
    # Send test message
    await ws_client.send_json({"type": "subscribe", "game_id": "test_001"})

    # Add expected response
    ws_client.add_received_message({
        "type": "game_update",
        "data": {"score": "14-7"}
    })

    # Receive and validate
    response = await ws_client.receive_json()
    assert response["type"] == "game_update"
```

## Best Practices

### Test Writing Guidelines

#### 1. Clear Test Names
```python
def test_prediction_accuracy_above_threshold_for_high_confidence_games():
    """Test that high-confidence predictions meet accuracy requirements."""
    pass

# NOT: test_prediction()
```

#### 2. Arrange-Act-Assert Pattern
```python
def test_game_score_update():
    # Arrange
    game = create_test_game(home_score=0, away_score=0)

    # Act
    updated_game = update_game_score(game, home_score=14, away_score=7)

    # Assert
    assert updated_game.home_score == 14
    assert updated_game.away_score == 7
```

#### 3. Meaningful Assertions
```python
# Good
assert response.status_code == 200, f"API returned {response.status_code}: {response.text}"
assert len(games) == 16, f"Expected 16 games for week 1, got {len(games)}"

# Avoid
assert response.status_code == 200
assert games
```

#### 4. Test Data Independence
```python
# Use factories and fixtures
def test_team_stats(sample_team_data):
    team = create_team(**sample_team_data)
    # Test logic...

# Avoid hardcoded data
def test_team_stats():
    team = Team(id="KC", name="Kansas City Chiefs")  # Fragile
```

### Performance Testing Guidelines

#### 1. Establish Baselines
```python
# Document expected performance
@pytest.mark.benchmark
def test_prediction_performance():
    with performance_test("prediction_benchmark") as profiler:
        predictions = generate_predictions(games)
        profiler.add_metric("games_processed", len(games))

    # Assert performance meets baseline
    assert profiler.elapsed_time < 2.0, "Prediction took too long"
```

#### 2. Monitor Resource Usage
```python
def test_memory_usage_within_limits():
    profiler = MemoryProfiler()
    profiler.start()

    # Execute memory-intensive operation
    large_dataset = process_season_data(2023)

    memory_delta = profiler.get_memory_delta()
    assert memory_delta < 500, f"Memory usage {memory_delta}MB exceeds limit"
```

### Security Testing Guidelines

#### 1. Input Validation
```python
def test_api_rejects_malicious_input():
    malicious_inputs = [
        "'; DROP TABLE games; --",
        "<script>alert('xss')</script>",
        "' OR 1=1 --",
    ]

    for malicious_input in malicious_inputs:
        response = client.get(f"/games?team={malicious_input}")
        assert response.status_code == 400, f"Should reject: {malicious_input}"
```

#### 2. Authentication Testing
```python
def test_protected_endpoint_requires_auth():
    # Test without authentication
    response = client.get("/admin/models")
    assert response.status_code == 401

    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/admin/models", headers=headers)
    assert response.status_code == 401

    # Test with valid token
    token = create_test_jwt_token({"role": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/admin/models", headers=headers)
    assert response.status_code == 200
```

## Troubleshooting

### Common Issues

#### Test Database Connection
```bash
# Check database status
make status-services

# Reset database
make reset-db

# Check connection manually
psql postgresql://test_user:test_password@localhost:5433/nfl_predictor_test
```

#### Redis Connection
```bash
# Check Redis status
docker-compose -f docker-compose.test.yml exec test-redis redis-cli ping

# Clear Redis data
docker-compose -f docker-compose.test.yml exec test-redis redis-cli FLUSHALL
```

#### Performance Issues
```bash
# Run tests with profiling
pytest --profile --profile-svg tests/unit/

# Check test timing
pytest --durations=10 tests/

# Parallel execution
pytest -n auto tests/unit/
```

#### Coverage Issues
```bash
# Generate detailed coverage report
coverage html --show-contexts
coverage report --show-missing

# Check coverage for specific files
coverage report src/ml/models.py
```

### Debug Mode

#### Python Debugging
```bash
# Run with pdb
make test-debug

# Or directly with pytest
pytest tests/unit/test_example.py --pdb -s
```

#### Frontend Debugging
```bash
# Run tests in debug mode
npm test -- --verbose

# Run single test file
npx vitest tests/frontend/components/GameCard.test.tsx
```

### Test Data Issues

#### Regenerate Fixtures
```python
# Regenerate test data
python scripts/generate_test_fixtures.py

# Reset to known good state
python scripts/reset_test_environment.py
```

#### Validate Test Data
```python
# Check data integrity
python scripts/validate_test_data.py

# Update mock responses
python scripts/update_mock_responses.py
```

## Contributing

### Adding New Tests

1. **Choose appropriate test category** (unit/integration/e2e)
2. **Follow naming conventions** (`test_<functionality>_<scenario>`)
3. **Use existing fixtures** when possible
4. **Add new fixtures** for reusable test data
5. **Document test purpose** with docstrings
6. **Update this README** for significant additions

### Test Review Checklist

- [ ] Tests are properly categorized
- [ ] Test names clearly describe the scenario
- [ ] Tests use appropriate fixtures
- [ ] Assertions are meaningful and descriptive
- [ ] Tests are isolated and independent
- [ ] Performance tests have baseline comparisons
- [ ] Security tests cover threat scenarios
- [ ] Tests pass in CI environment

### Performance Considerations

- [ ] Unit tests complete in < 1 second each
- [ ] Integration tests complete in < 10 seconds each
- [ ] Total test suite completes in < 5 minutes
- [ ] Memory usage stays within acceptable limits
- [ ] Database connections are properly managed
- [ ] External API calls are mocked

---

For questions or support, please refer to the main project documentation or create an issue in the repository.