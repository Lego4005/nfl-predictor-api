# NFL Predictor Load Testing - Quick Start Guide

## 🚀 Quick Start Commands

### 1. Install Dependencies
```bash
cd /home/iris/code/experimental/nfl-predictor-api
pip install -r tests/load/requirements.txt
```

### 2. Basic Tests (Choose One)

#### API Load Test (Recommended for beginners)
```bash
# Quick 5-minute test with 100 users
./tests/load/scripts/run_load_tests.sh api-load --users 100 --duration 5m

# Production-scale test
./tests/load/scripts/run_load_tests.sh api-load --users 1000 --duration 10m
```

#### WebSocket Stress Test
```bash
# Test 500 concurrent WebSocket connections
python tests/load/test_websocket_load.py --host ws://localhost:8000 --max-connections 500
```

#### ML Model Performance Test
```bash
# Test ML models with concurrent requests
python tests/load/test_ml_performance.py --concurrent-requests 100 --test-duration 300
```

#### Spike Testing
```bash
# Sudden traffic spike simulation
locust -f tests/load/test_spike_scenarios.py SuddenSpikeShape --host http://localhost:8000 --headless
```

### 3. Advanced Testing

#### Comprehensive Test Suite
```bash
# Run all test types
./tests/load/scripts/run_load_tests.sh comprehensive --duration 15m
```

#### Interactive Web UI Testing
```bash
# Start Locust web interface at http://localhost:8089
locust -f tests/load/locustfile.py --host http://localhost:8000 --web-host 0.0.0.0 --web-port 8089
```

#### Real-time Monitoring
```bash
# Start monitoring dashboard at http://localhost:5000
python tests/load/monitoring_dashboard.py --host 0.0.0.0 --port 5000
```

#### Memory Leak Detection
```bash
# Monitor for memory leaks during testing
python tests/load/memory_leak_detector.py --target-process nfl-predictor --duration 600
```

## 📊 Test Results

All results are saved to `/home/iris/code/experimental/nfl-predictor-api/tests/load/reports/`:
- **HTML Reports**: `locust_report_*.html` - Interactive performance reports
- **CSV Data**: `locust_stats_*.csv` - Raw metrics for analysis
- **JSON Reports**: `load_test_report_*.json` - Structured test results

## 🎯 Performance Targets

| Metric | Target | Warning | Critical |
|--------|---------|---------|----------|
| Avg Response Time | < 200ms | 200-500ms | > 500ms |
| P95 Response Time | < 500ms | 500ms-1s | > 1s |
| Error Rate | < 0.1% | 0.1-1% | > 1% |
| CPU Usage | < 70% | 70-85% | > 85% |

## 🔧 Configuration

### Quick Configuration Changes

Edit `/home/iris/code/experimental/nfl-predictor-api/tests/load/locust.conf`:
```ini
host = http://localhost:8000  # Change target host
users = 100                   # Default concurrent users
spawn-rate = 10              # Users per second
run-time = 5m                # Test duration
```

### Environment Variables
```bash
export LOCUST_HOST=http://localhost:8000
export LOCUST_USERS=500
export LOCUST_RUN_TIME=10m
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if NFL Predictor is running
   curl http://localhost:8000/v1/health
   ```

2. **High Response Times**
   ```bash
   # Monitor system resources
   htop
   # Check memory usage
   python tests/load/memory_leak_detector.py --duration 60
   ```

3. **Module Not Found Errors**
   ```bash
   # Install missing dependencies
   pip install -r tests/load/requirements.txt
   ```

## 📈 Next Steps

1. **Development**: Run small tests (50-100 users, 5 minutes)
2. **Pre-production**: Run medium tests (500-1000 users, 15 minutes)
3. **Capacity Planning**: Run large tests (2000-5000 users, 30+ minutes)
4. **Continuous Monitoring**: Set up automated daily tests

## 📞 Support

- View detailed documentation: `tests/load/README.md`
- Check test configurations: `tests/load/locust.conf`
- Review example scripts: `tests/load/scripts/`

---

**Remember**: Start small, monitor closely, and gradually increase load! 🚀