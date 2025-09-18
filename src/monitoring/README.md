# NFL Predictor Performance Monitoring System

A comprehensive performance monitoring dashboard with real-time metrics, alerting, bottleneck detection, and automated reporting for the NFL Predictor API.

## Features

### 🔍 Real-Time Monitoring
- **API Performance**: Response times, throughput, error rates
- **ML Model Performance**: Prediction accuracy, confidence scores, training metrics
- **System Resources**: CPU, memory, disk, network utilization
- **Cache Performance**: Hit rates, size, eviction patterns
- **Data Source Health**: External API availability and freshness
- **WebSocket Connections**: Active connections, message rates

### 📊 Prometheus Metrics Export
- Custom metrics for all performance indicators
- Standard Prometheus exposition format
- Configurable collection intervals
- Historical data retention

### 📈 Grafana Dashboard Integration
- Pre-configured dashboard templates
- Interactive performance visualizations
- Real-time alerting rules
- Custom metric exploration

### 🚨 Intelligent Alerting
- Multi-level alert severity (Low, Medium, High, Critical)
- Configurable thresholds and conditions
- Multiple notification channels (Email, Slack, etc.)
- Auto-resolution tracking

### 🔧 Advanced Bottleneck Detection
- Statistical anomaly detection using machine learning
- Correlation analysis between metrics
- Root cause identification
- Automated performance recommendations

### 📋 Automated Reporting
- Daily and weekly performance reports
- HTML email reports with charts
- SLA compliance tracking
- Executive summary generation

### 🎯 SLA Compliance Tracking
- Configurable SLA targets
- Real-time compliance monitoring
- Historical compliance analysis
- Breach tracking and notifications

## Architecture

```
src/monitoring/
├── performance_dashboard.py      # Main monitoring engine
├── bottleneck_detector.py       # AI-powered bottleneck detection
├── report_generator.py          # Automated report generation
├── sla_tracker.py              # SLA compliance monitoring
├── config/                     # Configuration files
│   ├── grafana_dashboard.json  # Grafana dashboard config
│   ├── prometheus.yml          # Prometheus configuration
│   └── alert_rules.yml         # Prometheus alert rules
├── templates/                  # Report templates
│   └── performance_report.html # HTML report template
└── __init__.py                 # Module initialization
```

## Quick Start

### 1. Install Dependencies

```bash
pip install prometheus_client redis sqlalchemy pandas numpy plotly scipy scikit-learn aiohttp psutil jinja2
```

### 2. Configuration

```python
from src.monitoring import PerformanceDashboard
import redis

config = {
    'database_url': 'postgresql://user:password@localhost/nfl_predictor',
    'redis_host': 'localhost',
    'redis_port': 6379,
    'api_base_url': 'http://localhost:8080',
    'prometheus_port': 8000,
    'collection_interval': 30,  # seconds
    'sla_targets': {
        'api_response_time': 200,  # ms
        'prediction_accuracy': 0.75,
        'cache_hit_rate': 0.8
    },
    'alert_thresholds': {
        'api_response_time': 1000,
        'system_cpu': 80,
        'system_memory': 85
    }
}

dashboard = PerformanceDashboard(config)
```

### 3. Start Monitoring

```python
import asyncio

# Start the monitoring system
await dashboard.start_monitoring()
```

### 4. Access Metrics

```python
# Get current system status
status = dashboard.get_current_status()

# Get historical data
history = dashboard.metrics_history[-100:]  # Last 100 measurements
```

## API Endpoints

The monitoring system exposes several REST API endpoints:

```
GET /api/monitoring/status          # Current system status
GET /api/monitoring/metrics/history # Historical metrics data
GET /api/monitoring/alerts          # Recent alerts
GET /api/monitoring/bottlenecks     # Bottleneck detections
GET /api/monitoring/sla/status      # SLA compliance status
GET /api/monitoring/reports/daily   # Daily performance report
GET /api/monitoring/reports/weekly  # Weekly performance report
```

## Frontend Component

Include the React SystemHealth component in your dashboard:

```tsx
import SystemHealth from './src/components/SystemHealth';

function Dashboard() {
  return (
    <div>
      <SystemHealth />
    </div>
  );
}
```

## Configuration Options

### Core Settings

```python
config = {
    # Database connection
    'database_url': 'postgresql://...',

    # Redis configuration
    'redis_host': 'localhost',
    'redis_port': 6379,
    'redis_db': 0,

    # API settings
    'api_base_url': 'http://localhost:8080',
    'prometheus_port': 8000,

    # Collection intervals
    'collection_interval': 30,      # seconds
    'alert_check_interval': 60,     # seconds
    'max_history_size': 10000,      # number of measurements

    # SLA targets
    'sla_targets': {
        'api_response_time': 200,    # milliseconds
        'prediction_accuracy': 0.75, # 75%
        'uptime': 0.999,            # 99.9%
        'cache_hit_rate': 0.8       # 80%
    },

    # Alert thresholds
    'alert_thresholds': {
        'api_response_time': 1000,   # ms
        'prediction_accuracy': 0.6,
        'cache_hit_rate': 0.5,
        'system_cpu': 80,           # %
        'system_memory': 85,        # %
        'error_rate': 0.1           # 10%
    }
}
```

### Email Configuration

```python
config['smtp'] = {
    'host': 'smtp.gmail.com',
    'port': 587,
    'use_tls': True,
    'username': 'alerts@nflpredictor.com',
    'password': 'app_password',
    'from_email': 'alerts@nflpredictor.com',
    'to_emails': ['admin@nflpredictor.com']
}
```

### Slack Integration

```python
config['slack_webhook'] = 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
```

## Metrics Collected

### API Metrics
- Request count by method, endpoint, status
- Response time percentiles (50th, 95th, 99th)
- Error rate by endpoint
- Throughput (requests per second)

### ML Model Metrics
- Prediction accuracy by model type
- Model confidence scores
- Training duration and frequency
- Feature importance tracking

### System Metrics
- CPU usage percentage
- Memory usage and available
- Disk I/O and space utilization
- Network throughput

### Cache Metrics
- Hit/miss rates
- Cache size and utilization
- Eviction patterns
- Key distribution

### Data Source Metrics
- External API availability
- Data freshness timestamps
- Connection pool utilization
- Query performance

## Bottleneck Detection

The system uses advanced machine learning techniques to automatically detect performance bottlenecks:

### Detection Methods
- **Statistical Analysis**: Z-score and standard deviation analysis
- **Isolation Forest**: Multivariate anomaly detection
- **Correlation Analysis**: Identifies related performance issues
- **Pattern Recognition**: Detects recurring bottleneck patterns

### Bottleneck Types
- CPU-bound operations
- Memory pressure
- Database performance issues
- Cache inefficiencies
- Network latency problems
- I/O bottlenecks
- Algorithm inefficiencies

### Automated Recommendations
Each bottleneck detection includes:
- Root cause analysis
- Impact assessment
- Specific action items
- Expected improvement estimates

## SLA Management

### Configurable Targets
```python
sla_targets = {
    'api_response_time': {
        'target_value': 200,         # ms
        'comparison_type': 'less_than',
        'warning_threshold': 0.8,    # 160ms
        'critical_threshold': 2.0,   # 400ms
        'measurement_window': 5      # minutes
    }
}
```

### Compliance Tracking
- Real-time compliance percentage
- Historical compliance trends
- Breach duration tracking
- Availability calculations

## Alerting System

### Alert Levels
1. **Low**: Minor deviations from normal
2. **Medium**: Significant performance degradation
3. **High**: SLA breaches or major issues
4. **Critical**: System failure or severe degradation

### Notification Channels
- Email with HTML formatting
- Slack with rich message formatting
- System logs with structured data
- Dashboard UI notifications

### Alert Conditions
```python
# CPU usage alert
if system_cpu > 80:
    create_alert(severity='medium', metric='system_cpu')

# Response time alert
if api_response_time > 1000:
    create_alert(severity='high', metric='api_response_time')

# Prediction accuracy alert
if prediction_accuracy < 0.6:
    create_alert(severity='critical', metric='prediction_accuracy')
```

## Reporting Features

### Daily Reports
- Performance summary statistics
- SLA compliance status
- Alert summary
- Trend analysis
- Bottleneck identification

### Weekly Reports
- Executive summary
- Capacity planning analysis
- Cost analysis and optimization
- Strategic recommendations
- Historical comparisons

### Report Delivery
- Automated email delivery
- HTML formatted reports
- Interactive charts and graphs
- PDF export capability

## Docker Integration

```dockerfile
# Dockerfile example
FROM python:3.9-slim

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
EXPOSE 8000

CMD ["python", "-m", "src.monitoring.performance_dashboard"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  monitoring:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/nfl_predictor
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis

  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./src/monitoring/config/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - ./src/monitoring/config/grafana_dashboard.json:/etc/grafana/provisioning/dashboards/dashboard.json
```

## Performance Optimization

### Collection Optimization
- Configurable sampling rates
- Efficient data structures
- Background processing
- Memory management

### Storage Optimization
- Time-series data compression
- Automatic data cleanup
- Configurable retention periods
- Efficient querying patterns

### Network Optimization
- Connection pooling
- Batch data collection
- Compression for data transfer
- Caching strategies

## Troubleshooting

### Common Issues

1. **High Memory Usage**
   ```python
   # Reduce history size
   config['max_history_size'] = 1000

   # Increase cleanup frequency
   config['cleanup_interval'] = 300  # 5 minutes
   ```

2. **Slow Metric Collection**
   ```python
   # Increase collection interval
   config['collection_interval'] = 60  # 1 minute

   # Disable expensive checks
   config['enable_ml_detection'] = False
   ```

3. **Database Connection Issues**
   ```python
   # Add connection pooling
   config['database_pool_size'] = 20
   config['database_max_overflow'] = 30
   ```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

config['debug'] = True
dashboard = PerformanceDashboard(config)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This monitoring system is part of the NFL Predictor API project and follows the same licensing terms.