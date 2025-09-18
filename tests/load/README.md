# NFL Predictor Load Testing Suite

## Overview

This comprehensive load testing suite is designed to validate the performance, scalability, and reliability of the NFL Predictor Platform under various traffic conditions. The suite includes multiple testing scenarios to simulate real-world usage patterns and stress conditions.

## Test Types

### 1. API Load Testing (`test_api_load.py`)
- **Purpose**: Test API endpoints under high concurrent load
- **Target**: 10,000 concurrent users
- **Focus Areas**:
  - Response time degradation analysis
  - Cache effectiveness validation
  - Database connection pooling
  - Error rate monitoring

### 2. WebSocket Stress Testing (`test_websocket_load.py`)
- **Purpose**: Validate WebSocket performance under extreme load
- **Target**: 5,000 concurrent connections
- **Focus Areas**:
  - Message broadcasting performance
  - Connection/disconnection storms
  - Memory leak detection
  - CPU usage monitoring

### 3. ML Model Performance Testing (`test_ml_performance.py`)
- **Purpose**: Test ML model performance under load
- **Target**: Batch processing and concurrent predictions
- **Focus Areas**:
  - Model loading/unloading cycles
  - Batch prediction processing
  - Feature engineering pipeline stress
  - Memory usage optimization

### 4. Spike Testing (`test_spike_scenarios.py`)
- **Purpose**: Test system resilience during traffic spikes
- **Scenarios**:
  - Sudden traffic increases (40x baseline)
  - Gradual ramp-up (150x baseline)
  - NFL game day traffic patterns
  - Sustained high load testing

## Performance Baselines

### Acceptable Performance Thresholds

| Metric | Target | Warning | Critical |
|--------|---------|---------|----------|
| Average Response Time | < 200ms | 200-500ms | > 500ms |
| P95 Response Time | < 500ms | 500ms-1s | > 1s |
| P99 Response Time | < 1s | 1-2s | > 2s |
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| CPU Usage | < 70% | 70-85% | > 85% |
| Memory Usage | < 80% | 80-90% | > 90% |
| Cache Hit Rate | > 85% | 70-85% | < 70% |

### Expected Throughput

| Endpoint Type | Target RPS | Peak RPS | Notes |
|---------------|------------|----------|-------|
| Health Checks | 1000+ | 2000+ | Should be highly cached |
| Predictions | 500+ | 1000+ | Main business logic |
| Downloads | 100+ | 200+ | File generation overhead |
| Monitoring | 200+ | 500+ | System status queries |

## Quick Start

### Prerequisites
```bash
# Install dependencies
pip install -r tests/load/requirements.txt

# Verify target system is running
curl http://localhost:8000/v1/health
```

### Running Tests

#### 1. Basic API Load Test
```bash
# Quick 5-minute test with 100 users
./tests/load/scripts/run_load_tests.sh api-load --users 100 --duration 5m

# High-volume test
./tests/load/scripts/run_load_tests.sh api-load --users 1000 --duration 10m
```

#### 2. WebSocket Stress Test
```bash
# Test 500 concurrent connections
python tests/load/test_websocket_load.py --host ws://localhost:8000 --max-connections 500

# Comprehensive WebSocket testing
python tests/load/test_websocket_load.py --comprehensive --max-connections 2000
```

#### 3. ML Performance Test
```bash
# Test ML model performance
python tests/load/test_ml_performance.py --concurrent-requests 100 --test-duration 300

# Save detailed results
python tests/load/test_ml_performance.py --output-file ml_results.json --report-file ml_report.txt
```

#### 4. Spike Testing
```bash
# Sudden spike simulation
locust -f tests/load/test_spike_scenarios.py SuddenSpikeShape --host http://localhost:8000

# Game day traffic simulation
locust -f tests/load/test_spike_scenarios.py GameTimeSpikesShape --host http://localhost:8000
```

#### 5. Comprehensive Test Suite
```bash
# Run all tests sequentially
./tests/load/scripts/run_load_tests.sh comprehensive --duration 10m
```

### Web UI Mode
```bash
# Interactive testing with Locust web interface
locust -f tests/load/locustfile.py --host http://localhost:8000 --web-host 0.0.0.0 --web-port 8089
```

## Monitoring and Analysis

### Real-time Monitoring Dashboard
```bash
# Start monitoring dashboard
python tests/load/monitoring_dashboard.py --host 0.0.0.0 --port 5000

# Access dashboard at: http://localhost:5000
```

### Performance Reports

Test results are automatically saved to `tests/load/reports/`:
- **HTML Reports**: Interactive Locust reports
- **CSV Data**: Raw performance metrics
- **JSON Summaries**: Structured test results
- **Markdown Summaries**: Human-readable reports

## Test Scenarios

### 1. Development Testing
- **Users**: 10-50
- **Duration**: 2-5 minutes
- **Purpose**: Quick validation during development

### 2. CI/CD Integration
- **Users**: 100-200
- **Duration**: 5-10 minutes
- **Purpose**: Automated performance regression testing

### 3. Staging Validation
- **Users**: 500-1000
- **Duration**: 15-30 minutes
- **Purpose**: Pre-production performance validation

### 4. Production Load Testing
- **Users**: 2000-10000
- **Duration**: 1-2 hours
- **Purpose**: Capacity planning and bottleneck identification

### 5. Disaster Recovery Testing
- **Scenario**: Extreme spike scenarios
- **Purpose**: Validate system recovery and failover mechanisms

## Configuration

### Environment Variables
```bash
export LOCUST_HOST=http://localhost:8000
export LOCUST_USERS=1000
export LOCUST_SPAWN_RATE=50
export LOCUST_RUN_TIME=10m
```

### Locust Configuration (`locust.conf`)
```ini
host = http://localhost:8000
users = 100
spawn-rate = 10
run-time = 5m
html = tests/load/reports/locust_report.html
csv = tests/load/reports/locust_stats
```

## Troubleshooting

### Common Issues

1. **Connection Refused Errors**
   - Verify target application is running
   - Check firewall settings
   - Validate host URL format

2. **High Response Times**
   - Monitor system resources (CPU, Memory, I/O)
   - Check database performance
   - Validate cache effectiveness

3. **WebSocket Connection Failures**
   - Check WebSocket endpoint availability
   - Verify WebSocket protocol (ws:// vs wss://)
   - Monitor connection limits

4. **Memory Issues During Testing**
   - Reduce concurrent users
   - Implement connection pooling
   - Monitor for memory leaks

### Performance Debugging

1. **Enable Detailed Logging**
   ```bash
   export LOCUST_LOGLEVEL=DEBUG
   ```

2. **System Resource Monitoring**
   ```bash
   # Monitor during tests
   htop
   iotop
   netstat -i 1
   ```

3. **Application Profiling**
   ```bash
   # Profile the target application
   py-spy record -o profile.svg -d 60 -p <PID>
   ```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Load Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r tests/load/requirements.txt
      - name: Run load tests
        run: |
          ./tests/load/scripts/run_load_tests.sh api-load --users 200 --duration 10m
      - name: Upload reports
        uses: actions/upload-artifact@v2
        with:
          name: load-test-reports
          path: tests/load/reports/
```

## Best Practices

### 1. Test Planning
- Define clear performance requirements
- Identify critical user journeys
- Plan for gradual load increases
- Include negative testing scenarios

### 2. Test Execution
- Start with baseline tests
- Monitor system resources continuously
- Run tests from multiple locations
- Document environmental conditions

### 3. Results Analysis
- Compare against historical baselines
- Identify performance trends
- Focus on P95/P99 metrics
- Analyze error patterns

### 4. Reporting
- Create executive summaries
- Include actionable recommendations
- Track improvements over time
- Share results with stakeholders

## Support and Maintenance

### Regular Tasks
- Update performance baselines quarterly
- Review and update test scenarios
- Monitor for new bottlenecks
- Validate infrastructure changes

### Performance Optimization Cycle
1. **Measure**: Run comprehensive load tests
2. **Analyze**: Identify bottlenecks and trends
3. **Optimize**: Implement performance improvements
4. **Validate**: Re-test to confirm improvements
5. **Document**: Update baselines and procedures

## Advanced Features

### Distributed Testing
```bash
# Master node
locust -f tests/load/locustfile.py --master --host http://localhost:8000

# Worker nodes
locust -f tests/load/locustfile.py --worker --master-host=<master-ip>
```

### Custom Metrics Collection
- Extend monitoring dashboard with application-specific metrics
- Integrate with APM tools (New Relic, DataDog, etc.)
- Set up automated alerting for performance degradation

### Load Testing in Different Environments
- **Development**: Quick validation tests
- **Staging**: Full-scale performance validation
- **Production**: Careful capacity testing with traffic shadowing

---

For questions or support, please refer to the project documentation or contact the development team.