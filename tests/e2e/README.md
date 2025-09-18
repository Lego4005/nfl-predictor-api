# NFL Predictor Platform - End-to-End Tests

Comprehensive end-to-end test suite for the NFL Predictor Platform using Playwright and pytest.

## 🎯 Overview

This E2E test suite provides comprehensive testing for:
- **User Journey Tests**: Complete user workflows from registration to betting decisions
- **Real-time Updates**: WebSocket connections and live data synchronization
- **Betting Flow**: Value bet identification, arbitrage opportunities, and bankroll management
- **Performance**: Page load times, API response times, and concurrent user scenarios

## 📁 Test Structure

```
tests/e2e/
├── conftest.py                 # Pytest configuration and shared fixtures
├── requirements.txt            # E2E test dependencies
├── docker-compose.test.yml     # Docker environment for testing
├── README.md                   # This file
├── .github/workflows/          # CI/CD workflows
│   └── e2e-tests.yml
├── config/                     # Test configuration
│   ├── __init__.py
│   └── test_environment.py     # Environment setup and management
├── fixtures/                   # Test data and fixtures
│   └── test_data_factory.py    # Factory classes for test data generation
├── scripts/                    # Test runner and utilities
│   └── run_tests.py           # Main test runner script
├── utils/                     # Test utilities and helpers
│   ├── __init__.py
│   └── test_helpers.py        # Common test helper functions
├── test_user_journey.py        # User journey E2E tests
├── test_realtime_updates.py    # Real-time WebSocket tests
├── test_betting_flow.py        # Betting workflow tests
└── test_performance.py         # Performance and load tests
```

## 🚀 Quick Start

### Prerequisites

1. **Python 3.11+** with pip
2. **Node.js 18+** (for Playwright)
3. **Docker & Docker Compose** (optional, for containerized testing)
4. **PostgreSQL** and **Redis** (for local testing)

### Installation

```bash
# Install Python dependencies
pip install -r tests/e2e/requirements.txt

# Install Playwright browsers
playwright install
```

### Running Tests

#### Basic Usage

```bash
# Run all E2E tests
python tests/e2e/scripts/run_tests.py

# Run specific test types
python tests/e2e/scripts/run_tests.py -m smoke          # Smoke tests only
python tests/e2e/scripts/run_tests.py -m integration   # Integration tests
python tests/e2e/scripts/run_tests.py --performance    # Performance tests

# Run specific test files
python tests/e2e/scripts/run_tests.py tests/e2e/test_user_journey.py

# Run with parallel workers
python tests/e2e/scripts/run_tests.py --workers 4
```

#### Advanced Options

```bash
# Run in headed mode for debugging
python tests/e2e/scripts/run_tests.py --headed --slowmo 1000

# Generate HTML reports
python tests/e2e/scripts/run_tests.py --html-report --junit-xml

# Run specific tests with keyword matching
python tests/e2e/scripts/run_tests.py -k "login and not performance"

# Run with video recording
python tests/e2e/scripts/run_tests.py --video

# Run in Docker environment
python tests/e2e/scripts/run_tests.py --env docker
```

## 📊 Test Categories

### 1. User Journey Tests (`test_user_journey.py`)

Tests complete user workflows:

- **Registration & Login**: New user onboarding, form validation, authentication
- **Dashboard Navigation**: Main interface navigation, responsive design
- **Predictions Viewing**: Game predictions, filtering, detailed views
- **Mock Betting**: Value bet selection, bet slip functionality
- **Historical Performance**: Analytics dashboard, performance metrics

**Key Test Classes:**
- `TestUserRegistrationFlow`
- `TestUserLoginFlow`
- `TestDashboardNavigation`
- `TestPredictionsViewing`
- `TestMockBettingFlow`
- `TestHistoricalPerformance`

### 2. Real-time Updates (`test_realtime_updates.py`)

Tests live data synchronization:

- **WebSocket Connections**: Connection establishment, authentication, reconnection
- **Live Score Updates**: Real-time game score changes, animations
- **Odds Changes**: Sportsbook odds updates, movement indicators
- **Prediction Updates**: Model refinements, confidence changes
- **Multi-user Sync**: Concurrent user data synchronization

**Key Test Classes:**
- `TestWebSocketConnection`
- `TestLiveScoreUpdates`
- `TestOddsChangesReflection`
- `TestPredictionUpdates`
- `TestMultiUserSynchronization`

### 3. Betting Flow (`test_betting_flow.py`)

Tests betting functionality:

- **Value Bet Identification**: Edge calculation, filtering, real-time updates
- **Arbitrage Detection**: Opportunity identification, profit calculations
- **Bankroll Management**: Kelly Criterion, risk tolerance, validation
- **Alert Subscriptions**: Email/push notifications, preferences
- **ROI Tracking**: Performance analytics, goal tracking

**Key Test Classes:**
- `TestValueBetIdentification`
- `TestArbitrageOpportunityDetection`
- `TestBankrollRecommendationAcceptance`
- `TestAlertSubscription`
- `TestROITrackingOverTime`

### 4. Performance Tests (`test_performance.py`)

Tests system performance:

- **Page Load Times**: Dashboard, predictions, live games performance
- **API Response Times**: Single requests, concurrent load, database queries
- **WebSocket Latency**: Message delivery speed, throughput
- **Large Dataset Rendering**: Table virtualization, memory usage
- **Concurrent Users**: Multi-user scenarios, system resource usage

**Key Test Classes:**
- `TestPageLoadTimes`
- `TestAPIResponseTimes`
- `TestWebSocketLatency`
- `TestDashboardRenderingWithLargeDatasets`
- `TestConcurrentUserScenarios`

## 🔧 Configuration

### Environment Variables

```bash
# Test Environment
TEST_ENV=local|docker|ci|remote
TEST_BASE_URL=http://localhost:8001
TEST_DATABASE_URL=postgresql://test:test@localhost:5432/nfl_predictor_test
TEST_REDIS_URL=redis://localhost:6379/1

# Browser Configuration
TEST_BROWSER=chromium|firefox|webkit
TEST_HEADLESS=true|false
TEST_SLOW_MO=0
TEST_TIMEOUT=30000
TEST_VIDEO=false
TEST_SCREENSHOTS=on-failure

# Performance Settings
TEST_CONCURRENT_USERS=25
```

### Test Configuration Files

- **`config/test_environment.py`**: Environment setup, database management, server lifecycle
- **`conftest.py`**: Pytest fixtures, browser setup, test server configuration
- **`docker-compose.test.yml`**: Containerized test environment

## 📈 Performance Benchmarks

### Target Performance Metrics

| Metric | Target | Test Location |
|--------|--------|---------------|
| Dashboard Load Time | < 3.0s | `test_performance.py::test_dashboard_load_time` |
| API Response Time (avg) | < 500ms | `test_performance.py::test_api_response_time` |
| WebSocket Latency | < 50ms | `test_performance.py::test_websocket_latency` |
| Large Dataset Render | < 5.0s | `test_performance.py::test_large_dataset_rendering` |
| Concurrent Users Success Rate | > 95% | `test_performance.py::test_concurrent_users` |

### Core Web Vitals

- **LCP (Largest Contentful Paint)**: < 2.5s
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1

## 🧪 Test Data Management

### Test Data Factories

The `fixtures/test_data_factory.py` provides factory classes for generating test data:

```python
from fixtures.test_data_factory import UserFactory, GameFactory, TestDataBuilder

# Generate single objects
user = UserFactory()
game = GameFactory(status='live')

# Generate complex scenarios
user_with_history = TestDataBuilder.create_user_with_history(bet_count=100)
game_week = TestDataBuilder.create_game_week_scenario(week=1)
```

### Available Factories

- `UserFactory`: Test user accounts with various subscription tiers
- `TeamFactory`: NFL teams with realistic data
- `GameFactory`: NFL games with different statuses
- `PredictionFactory`: ML model predictions
- `BettingOddsFactory`: Sportsbook odds data
- `ValueBetFactory`: Value betting opportunities
- `ArbitrageOpportunityFactory`: Arbitrage scenarios
- `PerformanceMetricsFactory`: User performance data

## 🔄 CI/CD Integration

### GitHub Actions Workflow

The `.github/workflows/e2e-tests.yml` provides:

- **Multi-browser testing** (Chromium, Firefox, WebKit)
- **Parallel test execution** across test types (smoke, integration, performance)
- **Service dependencies** (PostgreSQL, Redis)
- **Artifact management** (screenshots, videos, reports)
- **PR comments** with test results
- **Scheduled load testing**

### Running in CI

```bash
# Triggered on push/PR
git push origin feature-branch

# Manual load testing
git commit -m "feat: new feature [load-test]"

# Docker environment testing
git commit -m "test: verify Docker setup [docker-test]"
```

## 📝 Writing New Tests

### Test Structure Template

```python
import pytest
from playwright.async_api import Page, expect
from fixtures.test_data_factory import UserFactory

class TestNewFeature:
    """Test description"""

    @pytest.fixture(autouse=True)
    async def setup(self, page: Page):
        """Setup method run before each test"""
        # Login user, navigate to page, etc.
        pass

    @pytest.mark.asyncio
    @pytest.mark.smoke
    async def test_feature_basic_functionality(self, page: Page):
        """Test basic feature functionality"""
        # Arrange
        test_data = UserFactory()

        # Act
        await page.goto("/feature")
        await page.click("[data-testid='feature-button']")

        # Assert
        await expect(page.locator("[data-testid='result']")).to_be_visible()
```

### Best Practices

1. **Use data-testid attributes** for reliable element selection
2. **Create reusable fixtures** for common setup
3. **Use page object patterns** for complex interactions
4. **Add performance assertions** for critical paths
5. **Include error scenario testing**
6. **Mock external dependencies** appropriately

### Test Markers

- `@pytest.mark.smoke`: Critical functionality tests
- `@pytest.mark.integration`: Cross-component integration tests
- `@pytest.mark.performance`: Performance and load tests
- `@pytest.mark.slow`: Long-running tests

## 🐛 Debugging Tests

### Local Debugging

```bash
# Run in headed mode with slow motion
python tests/e2e/scripts/run_tests.py --headed --slowmo 1000 -k "specific_test"

# Enable debug logging
DEBUG=true python tests/e2e/scripts/run_tests.py --debug

# Keep browser open on failure
python tests/e2e/scripts/run_tests.py --headed --no-capture
```

### Screenshots and Videos

- **Screenshots**: Automatically taken on test failure
- **Videos**: Record full test runs with `--video` flag
- **Traces**: Playwright traces for detailed debugging

### Log Analysis

```bash
# View test logs
tail -f test-results/test.log

# Analyze performance metrics
cat test-results/metrics/*.json | jq '.metrics'
```

## 📊 Reporting

### HTML Reports

Generate comprehensive HTML reports:

```bash
python tests/e2e/scripts/run_tests.py --html-report
# Output: test-results/reports/report.html
```

### JUnit XML

For CI integration:

```bash
python tests/e2e/scripts/run_tests.py --junit-xml
# Output: test-results/reports/junit.xml
```

### Allure Reports

For advanced reporting:

```bash
python tests/e2e/scripts/run_tests.py --allure
# Generate report: allure serve test-results/allure-results
```

## 🔍 Monitoring & Maintenance

### Performance Monitoring

- Monitor Core Web Vitals trends
- Track API response time degradation
- Watch for memory leaks in long-running tests
- Analyze concurrent user test failures

### Test Maintenance

- **Update test data** when API schemas change
- **Review performance thresholds** quarterly
- **Update browser versions** regularly
- **Maintain test environment parity** with production

### Health Checks

```bash
# Verify test environment
python tests/e2e/config/test_environment.py setup

# Check test data integrity
python tests/e2e/scripts/verify_test_data.py

# Validate test coverage
python -m pytest --cov=src tests/e2e/ --cov-report=html
```

## 🤝 Contributing

### Adding New Tests

1. **Identify the test category** (user journey, real-time, betting, performance)
2. **Create test data factories** if needed
3. **Write focused, isolated tests**
4. **Add appropriate markers and documentation**
5. **Verify CI integration works**

### Test Review Checklist

- [ ] Tests are deterministic and reliable
- [ ] Appropriate use of test data factories
- [ ] Performance assertions included where relevant
- [ ] Error scenarios covered
- [ ] CI integration verified
- [ ] Documentation updated

## 📞 Support

For issues with E2E tests:

1. **Check test logs** in `test-results/test.log`
2. **Review screenshots/videos** from failed runs
3. **Verify test environment** setup
4. **Check CI workflow status**
5. **Review recent changes** to test files

## 🔗 Related Documentation

- [Project Setup Guide](../../README.md)
- [API Documentation](../../docs/api.md)
- [Performance Optimization](../../docs/performance.md)
- [Deployment Guide](../../docs/deployment.md)