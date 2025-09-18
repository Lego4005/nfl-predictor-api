"""
API Endpoints for Betting Analytics Engine

Provides REST API endpoints for accessing betting analytics features:
- Value bet identification
- Arbitrage opportunities
- Line movement analysis
- ROI tracking
- Bankroll management
- Live alerts
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Body, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

from .betting_engine import (
    BettingAnalyticsEngine,
    OddsData,
    ValueBet,
    ArbitrageOpportunity,
    LineMovement,
    BetType,
    RiskLevel
)
from .notification_system import NotificationSystem, Alert, AlertPriority, NotificationChannel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Router
router = APIRouter(prefix="/api/v1/analytics", tags=["Betting Analytics"])

# Global instances (would be dependency injected in production)
analytics_engine = BettingAnalyticsEngine()
notification_system = None  # Will be initialized

# Pydantic Models
class OddsRequest(BaseModel):
    sportsbook: str
    odds: float
    line: Optional[float] = None
    volume: Optional[float] = None

class ValueBetRequest(BaseModel):
    game_id: str
    true_probabilities: Dict[str, float]
    odds_data: List[OddsRequest]
    bankroll: float = 10000

class ArbitrageRequest(BaseModel):
    game_id: str
    odds_matrix: Dict[str, List[OddsRequest]]

class LineMovementRequest(BaseModel):
    game_id: str
    historical_odds: List[Dict]

class ROIRequest(BaseModel):
    bet_history: List[Dict]
    group_by: str = Field(default="bet_type", description="Group ROI analysis by: bet_type, sportsbook, selection, month")

class BankrollRequest(BaseModel):
    bankroll: float
    risk_tolerance: str = Field(default="medium", description="Risk tolerance: conservative, medium, aggressive")
    betting_history: Optional[List[Dict]] = None

class ParlayRiskRequest(BaseModel):
    legs: List[Dict]
    correlation_matrix: Optional[List[List[float]]] = None

class AlertConfigRequest(BaseModel):
    monitoring_games: List[str]
    alert_thresholds: Dict = Field(default_factory=dict)

class NotificationConfigRequest(BaseModel):
    channels: List[str]
    email_recipients: Optional[List[str]] = None
    sms_recipients: Optional[List[str]] = None
    webhook_urls: Optional[List[str]] = None
    min_priority: str = "medium"

# Response Models
class ValueBetResponse(BaseModel):
    game_id: str
    bet_type: str
    selection: str
    true_probability: float
    implied_probability: float
    odds: float
    kelly_fraction: float
    expected_value: float
    confidence: float
    risk_level: str
    recommended_stake: float
    max_stake: float
    sportsbook: str

class ArbitrageResponse(BaseModel):
    game_id: str
    bet_type: str
    selections: List[str]
    odds: List[float]
    sportsbooks: List[str]
    profit_margin: float
    total_stake: float
    stakes: List[float]
    guaranteed_profit: float
    risk_level: str

class LineMovementResponse(BaseModel):
    game_id: str
    bet_type: str
    selection: str
    opening_line: float
    current_line: float
    movement: float
    movement_percentage: float
    sharp_money_indicator: bool
    public_percentage: Optional[float]
    money_percentage: Optional[float]
    reverse_line_movement: bool
    steam_move: bool

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API token - simplified for demo"""
    # In production, this would validate JWT tokens against a database
    valid_tokens = ["demo_token_123", "api_key_456"]  # Demo tokens

    if credentials.credentials not in valid_tokens:
        raise HTTPException(status_code=401, detail="Invalid authentication token")

    return {"user_id": "demo_user", "token": credentials.credentials}

# Endpoints

@router.post("/value-bets", response_model=List[ValueBetResponse])
async def identify_value_bets(
    request: ValueBetRequest,
    user: dict = Depends(get_current_user)
):
    """
    Identify value betting opportunities using Kelly Criterion

    Analyzes true probabilities vs sportsbook odds to find profitable bets
    """
    try:
        # Convert request data to engine format
        odds_data = [
            OddsData(
                sportsbook=odds.sportsbook,
                odds=odds.odds,
                line=odds.line,
                volume=odds.volume
            ) for odds in request.odds_data
        ]

        # Get value bets
        value_bets = analytics_engine.identify_value_bets(
            game_id=request.game_id,
            true_probabilities=request.true_probabilities,
            odds_data=odds_data,
            bankroll=request.bankroll
        )

        # Convert to response format
        response_bets = [
            ValueBetResponse(
                game_id=bet.game_id,
                bet_type=bet.bet_type.value,
                selection=bet.selection,
                true_probability=bet.true_probability,
                implied_probability=bet.implied_probability,
                odds=bet.odds,
                kelly_fraction=bet.kelly_fraction,
                expected_value=bet.expected_value,
                confidence=bet.confidence,
                risk_level=bet.risk_level.value,
                recommended_stake=bet.recommended_stake,
                max_stake=bet.max_stake,
                sportsbook=bet.sportsbook
            ) for bet in value_bets
        ]

        logger.info(f"Found {len(response_bets)} value bets for game {request.game_id}")
        return response_bets

    except Exception as e:
        logger.error(f"Error identifying value bets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/arbitrage", response_model=List[ArbitrageResponse])
async def detect_arbitrage(
    request: ArbitrageRequest,
    user: dict = Depends(get_current_user)
):
    """
    Detect arbitrage opportunities across multiple sportsbooks

    Identifies guaranteed profit opportunities by betting on all outcomes
    """
    try:
        # Convert request data to engine format
        odds_matrix = {}
        for selection, odds_list in request.odds_matrix.items():
            odds_matrix[selection] = [
                OddsData(
                    sportsbook=odds.sportsbook,
                    odds=odds.odds,
                    line=odds.line,
                    volume=odds.volume
                ) for odds in odds_list
            ]

        # Detect arbitrage opportunities
        arbitrage_ops = analytics_engine.detect_arbitrage_opportunities(
            game_id=request.game_id,
            odds_matrix=odds_matrix
        )

        # Convert to response format
        response_ops = [
            ArbitrageResponse(
                game_id=arb.game_id,
                bet_type=arb.bet_type.value,
                selections=arb.selections,
                odds=arb.odds,
                sportsbooks=arb.sportsbooks,
                profit_margin=arb.profit_margin,
                total_stake=arb.total_stake,
                stakes=arb.stakes,
                guaranteed_profit=arb.guaranteed_profit,
                risk_level=arb.risk_level.value
            ) for arb in arbitrage_ops
        ]

        logger.info(f"Found {len(response_ops)} arbitrage opportunities for game {request.game_id}")
        return response_ops

    except Exception as e:
        logger.error(f"Error detecting arbitrage: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/line-movement", response_model=List[LineMovementResponse])
async def analyze_line_movement(
    request: LineMovementRequest,
    user: dict = Depends(get_current_user)
):
    """
    Analyze line movement and detect sharp money indicators

    Tracks how betting lines change over time and identifies professional betting patterns
    """
    try:
        movements = analytics_engine.analyze_line_movement(
            game_id=request.game_id,
            historical_odds=request.historical_odds
        )

        # Convert to response format
        response_movements = [
            LineMovementResponse(
                game_id=move.game_id,
                bet_type=move.bet_type.value,
                selection=move.selection,
                opening_line=move.opening_line,
                current_line=move.current_line,
                movement=move.movement,
                movement_percentage=move.movement_percentage,
                sharp_money_indicator=move.sharp_money_indicator,
                public_percentage=move.public_percentage,
                money_percentage=move.money_percentage,
                reverse_line_movement=move.reverse_line_movement,
                steam_move=move.steam_move
            ) for move in movements
        ]

        logger.info(f"Analyzed line movement for {len(response_movements)} selections in game {request.game_id}")
        return response_movements

    except Exception as e:
        logger.error(f"Error analyzing line movement: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/public-vs-money")
async def analyze_public_vs_money(
    betting_data: List[Dict] = Body(...),
    user: dict = Depends(get_current_user)
):
    """
    Analyze public betting percentage vs money percentage

    Identifies contrarian opportunities and sharp consensus plays
    """
    try:
        analysis = analytics_engine.analyze_public_vs_money(betting_data)

        logger.info(f"Public vs money analysis complete: {analysis['summary_stats']['contrarian_opportunities_count']} contrarian opportunities found")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing public vs money: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/roi-analysis")
async def calculate_roi(
    request: ROIRequest,
    user: dict = Depends(get_current_user)
):
    """
    Calculate historical ROI by various groupings

    Provides detailed return on investment analysis with performance metrics
    """
    try:
        roi_analysis = analytics_engine.calculate_historical_roi(
            bet_history=request.bet_history,
            group_by=request.group_by
        )

        logger.info(f"ROI analysis complete for {len(request.bet_history)} bets grouped by {request.group_by}")
        return roi_analysis

    except Exception as e:
        logger.error(f"Error calculating ROI: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/bankroll-management")
async def get_bankroll_recommendations(
    request: BankrollRequest,
    user: dict = Depends(get_current_user)
):
    """
    Get bankroll management recommendations

    Provides personalized bankroll management strategies based on risk tolerance and performance
    """
    try:
        recommendations = analytics_engine.recommend_bankroll_management(
            bankroll=request.bankroll,
            risk_tolerance=request.risk_tolerance,
            betting_history=request.betting_history
        )

        logger.info(f"Bankroll recommendations generated for ${request.bankroll} bankroll with {request.risk_tolerance} risk tolerance")
        return recommendations

    except Exception as e:
        logger.error(f"Error generating bankroll recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/parlay-risk-assessment")
async def assess_parlay_risk(
    request: ParlayRiskRequest,
    user: dict = Depends(get_current_user)
):
    """
    Assess risk for parlay and teaser bets

    Analyzes the risk profile of multi-leg bets including correlation effects
    """
    try:
        import numpy as np

        correlation_matrix = None
        if request.correlation_matrix:
            correlation_matrix = np.array(request.correlation_matrix)

        risk_assessment = analytics_engine.assess_parlay_risk(
            legs=request.legs,
            correlation_matrix=correlation_matrix
        )

        logger.info(f"Parlay risk assessment complete for {len(request.legs)} legs")
        return risk_assessment

    except Exception as e:
        logger.error(f"Error assessing parlay risk: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/live-alerts/start")
async def start_live_alerts(
    request: AlertConfigRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user)
):
    """
    Start live betting opportunity alerts

    Begins monitoring specified games for value bets, arbitrage, and line movements
    """
    try:
        # Start background monitoring task
        background_tasks.add_task(
            monitor_live_opportunities,
            request.monitoring_games,
            request.alert_thresholds,
            user["user_id"]
        )

        return {
            "status": "started",
            "monitoring_games": len(request.monitoring_games),
            "message": "Live alerts monitoring started"
        }

    except Exception as e:
        logger.error(f"Error starting live alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live-alerts/status")
async def get_alerts_status(user: dict = Depends(get_current_user)):
    """Get status of live alerts monitoring"""
    # This would check the status of background monitoring tasks
    return {
        "status": "active",  # or "inactive"
        "monitored_games": 5,
        "alerts_sent_today": 12,
        "last_alert": "2024-01-15T10:30:00Z"
    }

@router.post("/notifications/configure")
async def configure_notifications(
    request: NotificationConfigRequest,
    user: dict = Depends(get_current_user)
):
    """
    Configure notification settings

    Set up email, SMS, webhook, and other notification preferences
    """
    try:
        global notification_system

        # Convert channels to enum
        channels = []
        for channel_str in request.channels:
            try:
                channels.append(NotificationChannel(channel_str.lower()))
            except ValueError:
                logger.warning(f"Unknown notification channel: {channel_str}")

        # Convert priority
        try:
            min_priority = AlertPriority[request.min_priority.upper()]
        except KeyError:
            min_priority = AlertPriority.MEDIUM

        # Create notification configs
        from .notification_system import NotificationConfig

        notification_configs = {}
        for channel in channels:
            config = {}

            if channel == NotificationChannel.EMAIL and request.email_recipients:
                config['recipients'] = request.email_recipients
            elif channel == NotificationChannel.SMS and request.sms_recipients:
                config['recipients'] = request.sms_recipients
            elif channel == NotificationChannel.WEBHOOK and request.webhook_urls:
                config['urls'] = request.webhook_urls

            notification_configs[channel.value] = NotificationConfig(
                channel=channel,
                enabled=True,
                config=config,
                min_priority=min_priority
            )

        # Initialize notification system
        notification_system = NotificationSystem(notification_configs)

        return {
            "status": "configured",
            "channels": [ch.value for ch in channels],
            "min_priority": min_priority.name,
            "message": "Notification settings configured successfully"
        }

    except Exception as e:
        logger.error(f"Error configuring notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/notifications/test")
async def test_notifications(user: dict = Depends(get_current_user)):
    """Send test notifications to verify configuration"""
    if notification_system is None:
        raise HTTPException(status_code=400, detail="Notifications not configured")

    try:
        test_alert = Alert(
            id="test_alert_001",
            title="Test Alert - NFL Predictor Analytics",
            message="This is a test notification to verify your configuration is working correctly.",
            priority=AlertPriority.LOW,
            alert_type="test",
            data={"test": True, "timestamp": datetime.utcnow().isoformat()}
        )

        results = await notification_system.send_alert(test_alert)

        return {
            "status": "sent",
            "results": results,
            "message": "Test notifications sent"
        }

    except Exception as e:
        logger.error(f"Error sending test notifications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/stats")
async def get_notification_stats(
    hours: int = Query(24, description="Hours to analyze"),
    user: dict = Depends(get_current_user)
):
    """Get notification delivery statistics"""
    if notification_system is None:
        raise HTTPException(status_code=400, detail="Notifications not configured")

    try:
        stats = await notification_system.get_delivery_stats(hours=hours)
        return stats

    except Exception as e:
        logger.error(f"Error getting notification stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/stats")
async def get_cache_stats(user: dict = Depends(get_current_user)):
    """Get Redis cache statistics"""
    try:
        # Get Redis info
        info = analytics_engine.redis_client.info()

        # Get key counts by pattern
        patterns = [
            "betting_analytics:value_bets:*",
            "betting_analytics:arbitrage:*",
            "betting_analytics:line_movement:*",
            "betting_analytics:public_money_analysis:*",
            "betting_analytics:roi_analysis:*",
            "betting_analytics:bankroll_mgmt:*",
            "betting_analytics:parlay_risk:*"
        ]

        key_counts = {}
        for pattern in patterns:
            keys = analytics_engine.redis_client.keys(pattern)
            category = pattern.split(':')[1]
            key_counts[category] = len(keys)

        return {
            "redis_info": {
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": info.get("keyspace_hits", 0) / (info.get("keyspace_hits", 0) + info.get("keyspace_misses", 1))
            },
            "cached_categories": key_counts,
            "total_cached_keys": sum(key_counts.values()),
            "cache_ttl_seconds": analytics_engine.cache_ttl
        }

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/clear")
async def clear_cache(
    category: Optional[str] = Query(None, description="Specific category to clear (optional)"),
    user: dict = Depends(get_current_user)
):
    """Clear Redis cache"""
    try:
        if category:
            pattern = f"betting_analytics:{category}:*"
            keys = analytics_engine.redis_client.keys(pattern)
            if keys:
                deleted = analytics_engine.redis_client.delete(*keys)
                return {"status": "cleared", "category": category, "keys_deleted": deleted}
            else:
                return {"status": "no_keys", "category": category, "keys_deleted": 0}
        else:
            # Clear all betting analytics cache
            pattern = "betting_analytics:*"
            keys = analytics_engine.redis_client.keys(pattern)
            if keys:
                deleted = analytics_engine.redis_client.delete(*keys)
                return {"status": "cleared", "category": "all", "keys_deleted": deleted}
            else:
                return {"status": "no_keys", "category": "all", "keys_deleted": 0}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task for live monitoring
async def monitor_live_opportunities(games: List[str], thresholds: Dict, user_id: str):
    """Background task to monitor live betting opportunities"""
    logger.info(f"Starting live monitoring for {len(games)} games")

    while True:  # In production, this would have proper start/stop controls
        try:
            # Generate alerts for all games
            all_alerts = await analytics_engine.generate_live_alerts(games, thresholds)

            # Send notifications if configured
            if notification_system and all_alerts:
                await notification_system.bulk_send_alerts(all_alerts)
                logger.info(f"Sent {len(all_alerts)} live alerts")

            # Wait before next check
            await asyncio.sleep(60)  # Check every minute

        except Exception as e:
            logger.error(f"Error in live monitoring: {e}")
            await asyncio.sleep(300)  # Wait 5 minutes before retry on error

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for the analytics API"""
    try:
        # Test Redis connection
        redis_healthy = analytics_engine.redis_client.ping()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "redis": "healthy" if redis_healthy else "unhealthy",
                "analytics_engine": "healthy",
                "notifications": "configured" if notification_system else "not_configured"
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }