"""
NFL Predictor Betting Analytics Engine

A comprehensive betting analytics system providing:
- Value bet identification using Kelly Criterion
- Arbitrage opportunity detection
- Line movement analysis and sharp money tracking
- Public betting vs money percentage analysis
- Historical ROI tracking by bet type
- Bankroll management recommendations
- Risk assessment for parlays and teasers
- Live betting opportunity alerts
- Multi-channel notification system
"""

from .betting_engine import (
    BettingAnalyticsEngine,
    OddsData,
    ValueBet,
    ArbitrageOpportunity,
    LineMovement,
    BetType,
    RiskLevel
)

from .notification_system import (
    NotificationSystem,
    NotificationConfig,
    Alert,
    AlertPriority,
    NotificationChannel
)

from .api_endpoints import router as analytics_router

__version__ = "1.0.0"
__all__ = [
    "BettingAnalyticsEngine",
    "NotificationSystem",
    "analytics_router",
    "OddsData",
    "ValueBet",
    "ArbitrageOpportunity",
    "LineMovement",
    "BetType",
    "RiskLevel",
    "NotificationConfig",
    "Alert",
    "AlertPriority",
    "NotificationChannel"
]