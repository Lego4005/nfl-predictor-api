# NFL Predictor Betting Analytics Engine

A comprehensive betting analytics system providing advanced analytics for NFL predictions and betting strategy optimization.

## Features

### 🎯 Core Analytics
- **Value Bet Identification**: Kelly Criterion-based analysis to identify profitable betting opportunities
- **Arbitrage Detection**: Cross-sportsbook arbitrage opportunity identification with guaranteed profit calculations
- **Line Movement Analysis**: Sharp money tracking and reverse line movement detection
- **Public vs Money Analysis**: Contrarian opportunity identification through betting pattern analysis
- **Historical ROI Tracking**: Comprehensive performance analysis by bet type, sportsbook, and time period

### 💰 Bankroll Management
- **Risk Assessment**: Personalized bankroll management based on risk tolerance and performance history
- **Parlay Risk Analysis**: Advanced risk assessment for multi-leg bets including correlation effects
- **Position Sizing**: Kelly Criterion-based stake recommendations with safety limits

### 🚨 Live Monitoring
- **Real-time Alerts**: Live betting opportunity notifications across multiple channels
- **Steam Move Detection**: Rapid line movement identification
- **Sharp Money Indicators**: Professional betting pattern recognition

### 📡 Notification System
- **Multi-channel Support**: Email, SMS, Slack, Discord, webhooks
- **Priority-based Routing**: Alert filtering based on importance and user preferences
- **Delivery Tracking**: Comprehensive delivery statistics and reliability monitoring

### ⚡ Performance Optimization
- **Multi-level Caching**: Memory and Redis caching with intelligent TTL management
- **Data Volatility Optimization**: Cache strategies based on data update frequency
- **Background Processing**: Asynchronous analysis and notification delivery

## Quick Start

### Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Set up Redis (required for caching)
docker run -d --name redis -p 6379:6379 redis:alpine

# Configure environment variables
cp .env.example .env
# Edit .env with your settings
```

### Basic Usage

```python
from analytics import BettingAnalyticsEngine, NotificationSystem
from analytics.betting_engine import OddsData

# Initialize analytics engine
engine = BettingAnalyticsEngine()

# Example: Find value bets
game_id = "NFL_2024_W15_KC_vs_LV"
true_probabilities = {"Kansas City Chiefs": 0.65, "Las Vegas Raiders": 0.35}
odds_data = [OddsData("DraftKings", -140), OddsData("FanDuel", +120)]

value_bets = engine.identify_value_bets(
    game_id=game_id,
    true_probabilities=true_probabilities,
    odds_data=odds_data,
    bankroll=10000
)

for bet in value_bets:
    print(f"Value bet: {bet.selection} at {bet.odds}")
    print(f"Expected value: {bet.expected_value:.3f}")
    print(f"Recommended stake: ${bet.recommended_stake:.2f}")
```

## API Usage

The betting analytics engine provides REST API endpoints for integration:

### Authentication

All API endpoints require authentication using Bearer tokens:

```bash
curl -H "Authorization: Bearer your_token_here" \
     https://api.example.com/api/v1/analytics/value-bets
```

### Key Endpoints

#### Value Bet Identification
```bash
POST /api/v1/analytics/value-bets
Content-Type: application/json

{
  "game_id": "NFL_2024_W15_KC_vs_LV",
  "true_probabilities": {
    "Kansas City Chiefs": 0.65,
    "Las Vegas Raiders": 0.35
  },
  "odds_data": [
    {"sportsbook": "DraftKings", "odds": -140},
    {"sportsbook": "FanDuel", "odds": +120}
  ],
  "bankroll": 10000
}
```

#### Arbitrage Detection
```bash
POST /api/v1/analytics/arbitrage
Content-Type: application/json

{
  "game_id": "NFL_2024_W15_BUF_vs_MIA",
  "odds_matrix": {
    "Buffalo Bills": [
      {"sportsbook": "BookA", "odds": -110},
      {"sportsbook": "BookB", "odds": -105}
    ],
    "Miami Dolphins": [
      {"sportsbook": "BookA", "odds": +105},
      {"sportsbook": "BookB", "odds": +110}
    ]
  }
}
```

#### ROI Analysis
```bash
POST /api/v1/analytics/roi-analysis
Content-Type: application/json

{
  "bet_history": [
    {"bet_type": "moneyline", "stake": 100, "payout": 150, "result": "win", "odds": 1.5},
    {"bet_type": "spread", "stake": 110, "payout": 0, "result": "loss", "odds": 1.91}
  ],
  "group_by": "bet_type"
}
```

#### Bankroll Management
```bash
POST /api/v1/analytics/bankroll-management
Content-Type: application/json

{
  "bankroll": 10000,
  "risk_tolerance": "medium",
  "betting_history": [...]
}
```

## Configuration

### Environment Variables

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379

# Notification Settings
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Twilio SMS
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Webhooks
WEBHOOK_URLS=https://your-webhook-url.com/alerts

# Slack Integration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# Discord Integration
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK
```

### Notification Setup

```python
from analytics.notification_system import NotificationSystem, NotificationConfig, NotificationChannel, AlertPriority

# Configure notification channels
configs = {
    'email': NotificationConfig(
        channel=NotificationChannel.EMAIL,
        enabled=True,
        config={'recipients': ['trader@example.com']},
        min_priority=AlertPriority.MEDIUM
    ),
    'slack': NotificationConfig(
        channel=NotificationChannel.SLACK,
        enabled=True,
        config={'webhook_url': 'https://hooks.slack.com/services/YOUR/WEBHOOK'},
        min_priority=AlertPriority.HIGH
    )
}

notification_system = NotificationSystem(configs)
```

## Advanced Features

### Custom Cache Configuration

```python
from analytics.cache_manager import CacheManager, CacheConfig, DataVolatility

# Configure advanced caching
cache_config = CacheConfig(
    default_ttl=300,  # 5 minutes
    memory_limit=2000,  # 2000 items in memory
    volatility_ttls={
        DataVolatility.STATIC: 86400,    # 24 hours for historical data
        DataVolatility.DYNAMIC: 300,     # 5 minutes for odds
        DataVolatility.VOLATILE: 60      # 1 minute for live data
    },
    compression=True,
    metrics_enabled=True
)

cache_manager = CacheManager(config=cache_config)
```

### Parlay Risk Assessment

```python
# Assess complex parlay risk
parlay_legs = [
    {'probability': 0.60, 'odds': 1.67},
    {'probability': 0.55, 'odds': 1.82},
    {'probability': 0.65, 'odds': 1.54}
]

# Optional correlation matrix
correlation_matrix = [
    [1.0, 0.2, 0.1],
    [0.2, 1.0, 0.3],
    [0.1, 0.3, 1.0]
]

risk_assessment = engine.assess_parlay_risk(
    legs=parlay_legs,
    correlation_matrix=correlation_matrix
)
```

### Live Alert Monitoring

```python
# Start live monitoring
monitoring_games = ["NFL_2024_W15_KC_vs_LV", "NFL_2024_W15_BUF_vs_MIA"]
alert_thresholds = {
    'min_expected_value': 0.05,
    'min_arbitrage_profit': 0.02,
    'min_line_movement': 1.0
}

# This runs as a background task
alerts = await engine.generate_live_alerts(monitoring_games, alert_thresholds)

# Send notifications
if notification_system and alerts:
    await notification_system.bulk_send_alerts(alerts)
```

## Performance Monitoring

### Cache Metrics

```bash
GET /api/v1/analytics/cache/stats

{
  "global_metrics": {
    "hits": 1250,
    "misses": 185,
    "hit_rate": 0.871,
    "total_operations": 1435
  },
  "memory_cache_size": 450,
  "redis_info": {
    "used_memory_human": "2.1M",
    "connected_clients": 3,
    "keyspace_hits": 8945,
    "keyspace_misses": 1205
  }
}
```

### Notification Statistics

```bash
GET /api/v1/analytics/notifications/stats?hours=24

{
  "period_hours": 24,
  "total_alerts": 45,
  "overall_success_rate": 0.956,
  "channel_stats": {
    "email": {"attempted": 45, "successful": 43, "success_rate": 0.956},
    "slack": {"attempted": 12, "successful": 12, "success_rate": 1.0}
  }
}
```

## Error Handling

The system includes comprehensive error handling:

- **Graceful Degradation**: Falls back to alternative methods when services are unavailable
- **Retry Logic**: Automatic retries for transient failures
- **Circuit Breakers**: Prevents cascading failures
- **Detailed Logging**: Structured logging for debugging and monitoring

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/analytics --cov-report=html

# Run specific test categories
pytest tests/test_betting_engine.py
pytest tests/test_notification_system.py
pytest tests/test_cache_manager.py
```

## Example Integration

See `example_usage.py` for comprehensive examples of:
- Value bet identification
- Arbitrage detection
- Line movement analysis
- ROI tracking
- Bankroll management
- Parlay risk assessment
- Notification system setup
- Cache performance optimization

## Support

For questions, issues, or feature requests:
1. Check the API documentation
2. Review example usage patterns
3. Monitor system health endpoints
4. Check logs for detailed error information

## License

This betting analytics engine is part of the NFL Predictor API system.