"""
Real Data API Endpoints for NFL Predictor

Provides endpoints for accessing real NFL data through the SportsData.io connector
and enhanced predictions with real-time data.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our real data services (with fallback handling)
try:
    from services.real_data_connector import SportsDataIOConnector, fetch_all_game_data
    from services.prediction_integration import PredictionDataIntegrator, get_game_prediction_data, get_all_games_prediction_data
    from ml.real_data_prediction_service import RealDataNFLPredictionService, get_real_data_predictions, get_live_updates
    REAL_DATA_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Real data services not available: {e}")
    REAL_DATA_AVAILABLE = False

# Set up logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/real-data", tags=["real-data"])

# Pydantic models for API responses
class GameData(BaseModel):
    game_id: Optional[str] = None
    week: Optional[int] = None
    season: Optional[int] = None
    date: Optional[str] = None
    home_team: str
    away_team: str
    home_score: Optional[int] = 0
    away_score: Optional[int] = 0
    status: Optional[str] = "Scheduled"
    is_final: Optional[bool] = False
    is_in_progress: Optional[bool] = False

class TeamStats(BaseModel):
    team: str
    season: Optional[int] = None
    games_played: Optional[int] = 0
    offense: Optional[Dict[str, Any]] = {}
    defense: Optional[Dict[str, Any]] = {}
    special_teams: Optional[Dict[str, Any]] = {}
    advanced: Optional[Dict[str, Any]] = {}

class InjuryReport(BaseModel):
    player_id: Optional[str] = None
    player_name: str
    team: str
    position: str
    injury_status: str  # Out, Doubtful, Questionable, Probable
    injury_body_part: Optional[str] = None
    injury_description: Optional[str] = None
    updated: Optional[str] = None

class BettingOdds(BaseModel):
    game_id: Optional[str] = None
    home_team: str
    away_team: str
    point_spread: Optional[float] = None
    home_moneyline: Optional[int] = None
    away_moneyline: Optional[int] = None
    over_under: Optional[float] = None
    updated: Optional[str] = None

class EnhancedPrediction(BaseModel):
    game_id: Optional[str] = None
    week: Optional[int] = None
    season: Optional[int] = None
    home_team: str
    away_team: str
    winner: str
    winner_confidence: float
    predicted_spread: float
    predicted_total: float
    ats_pick: str
    ats_confidence: float
    market_data: Optional[Dict[str, Any]] = {}
    enhanced_factors: Optional[Dict[str, Any]] = {}
    data_quality: Optional[Dict[str, Any]] = {}
    overall_confidence: float

class ServiceStatus(BaseModel):
    service_available: bool
    real_data_enabled: bool
    api_key_configured: bool
    last_updated: str
    total_games_available: int = 0
    data_sources: Dict[str, bool] = {}

# Helper function to check service availability
def check_real_data_service() -> bool:
    """Check if real data service is available"""
    if not REAL_DATA_AVAILABLE:
        return False

    api_key = os.getenv('VITE_SPORTSDATA_IO_KEY')
    return bool(api_key)

# API Endpoints

@router.get("/status", response_model=ServiceStatus)
async def get_service_status():
    """Get the status of the real data service"""
    try:
        service_available = check_real_data_service()
        api_key = os.getenv('VITE_SPORTSDATA_IO_KEY')

        status = ServiceStatus(
            service_available=service_available,
            real_data_enabled=REAL_DATA_AVAILABLE,
            api_key_configured=bool(api_key),
            last_updated=datetime.now().isoformat(),
            data_sources={
                "sportsdata_io": service_available,
                "prediction_integration": REAL_DATA_AVAILABLE,
                "enhanced_predictions": REAL_DATA_AVAILABLE
            }
        )

        if service_available:
            try:
                # Test connectivity and get game count
                async with SportsDataIOConnector() as connector:
                    games = await connector.get_current_week_games()
                    status.total_games_available = len(games)
            except Exception as e:
                logger.warning(f"Could not fetch game count: {e}")

        return status

    except Exception as e:
        logger.error(f"Error checking service status: {e}")
        raise HTTPException(status_code=500, detail=f"Service status check failed: {str(e)}")

@router.get("/games/current", response_model=List[GameData])
async def get_current_games():
    """Get current week games with real data"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with SportsDataIOConnector() as connector:
            games = await connector.get_current_week_games()

            game_data = []
            for game in games:
                game_data.append(GameData(
                    game_id=str(game.get('game_id', '')),
                    week=game.get('week'),
                    season=game.get('season'),
                    date=game.get('date'),
                    home_team=game.get('home_team', ''),
                    away_team=game.get('away_team', ''),
                    home_score=game.get('home_score', 0),
                    away_score=game.get('away_score', 0),
                    status=game.get('status', 'Scheduled'),
                    is_final=game.get('is_final', False),
                    is_in_progress=game.get('is_in_progress', False)
                ))

            logger.info(f"Retrieved {len(game_data)} current games")
            return game_data

    except Exception as e:
        logger.error(f"Error fetching current games: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch games: {str(e)}")

@router.get("/teams/{team_id}/stats", response_model=TeamStats)
async def get_team_statistics(
    team_id: str = Path(..., description="Team abbreviation (e.g., 'KC', 'SF')")
):
    """Get comprehensive team statistics"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with SportsDataIOConnector() as connector:
            stats = await connector.get_team_stats(team_id.upper())

            if not stats:
                raise HTTPException(status_code=404, detail=f"No stats found for team: {team_id}")

            return TeamStats(**stats)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching team stats for {team_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch team stats: {str(e)}")

@router.get("/injuries", response_model=List[InjuryReport])
async def get_injury_reports(
    team: Optional[str] = Query(None, description="Team abbreviation to filter by")
):
    """Get injury reports for all teams or specific team"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with SportsDataIOConnector() as connector:
            injuries = await connector.get_injuries(team.upper() if team else None)

            injury_data = []
            for injury in injuries:
                injury_data.append(InjuryReport(
                    player_id=injury.get('player_id'),
                    player_name=injury.get('player_name', ''),
                    team=injury.get('team', ''),
                    position=injury.get('position', ''),
                    injury_status=injury.get('injury_status', 'Unknown'),
                    injury_body_part=injury.get('injury_body_part'),
                    injury_description=injury.get('injury_description'),
                    updated=injury.get('updated')
                ))

            logger.info(f"Retrieved {len(injury_data)} injury reports")
            return injury_data

    except Exception as e:
        logger.error(f"Error fetching injury reports: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch injuries: {str(e)}")

@router.get("/betting/odds", response_model=List[BettingOdds])
async def get_betting_odds(
    game_id: Optional[int] = Query(None, description="Specific game ID")
):
    """Get betting odds for current games"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with SportsDataIOConnector() as connector:
            odds_data = await connector.get_betting_data(game_id)

            if isinstance(odds_data, dict) and game_id:
                # Single game odds
                if not odds_data:
                    raise HTTPException(status_code=404, detail=f"No odds found for game: {game_id}")
                odds_list = [odds_data]
            else:
                # Multiple games odds
                odds_list = list(odds_data.values()) if isinstance(odds_data, dict) else []

            betting_data = []
            for odds in odds_list:
                betting_data.append(BettingOdds(
                    game_id=str(odds.get('game_id', '')),
                    home_team=odds.get('home_team', ''),
                    away_team=odds.get('away_team', ''),
                    point_spread=odds.get('point_spread'),
                    home_moneyline=odds.get('home_moneyline'),
                    away_moneyline=odds.get('away_moneyline'),
                    over_under=odds.get('over_under'),
                    updated=odds.get('updated')
                ))

            logger.info(f"Retrieved odds for {len(betting_data)} games")
            return betting_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching betting odds: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch odds: {str(e)}")

@router.get("/predictions/enhanced", response_model=List[EnhancedPrediction])
async def get_enhanced_predictions(
    week: Optional[int] = Query(None, description="NFL week number"),
    season: Optional[int] = Query(2024, description="NFL season year")
):
    """Get enhanced predictions with real NFL data"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with RealDataNFLPredictionService() as service:
            await service.initialize_models()
            predictions = await service.get_enhanced_game_predictions(week, season)

            enhanced_data = []
            for pred in predictions:
                enhanced_data.append(EnhancedPrediction(
                    game_id=pred.get('game_id'),
                    week=pred.get('week'),
                    season=pred.get('season'),
                    home_team=pred.get('home_team', ''),
                    away_team=pred.get('away_team', ''),
                    winner=pred.get('winner', ''),
                    winner_confidence=pred.get('winner_confidence', 0.5),
                    predicted_spread=pred.get('predicted_spread', 0.0),
                    predicted_total=pred.get('predicted_total', 44.0),
                    ats_pick=pred.get('ats_pick', ''),
                    ats_confidence=pred.get('ats_confidence', 0.5),
                    market_data=pred.get('market_data', {}),
                    enhanced_factors=pred.get('enhanced_factors', {}),
                    data_quality=pred.get('data_quality', {}),
                    overall_confidence=pred.get('overall_confidence', 0.5)
                ))

            logger.info(f"Generated {len(enhanced_data)} enhanced predictions")
            return enhanced_data

    except Exception as e:
        logger.error(f"Error generating enhanced predictions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate predictions: {str(e)}")

@router.get("/predictions/live")
async def get_live_game_updates():
    """Get live updates for in-progress games"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        live_updates = await get_live_updates()
        logger.info(f"Retrieved live updates for {len(live_updates)} games")
        return {
            "live_games": live_updates,
            "count": len(live_updates),
            "updated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching live updates: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch live updates: {str(e)}")

@router.get("/analysis/comprehensive")
async def get_comprehensive_analysis(
    week: Optional[int] = Query(None, description="NFL week number"),
    season: Optional[int] = Query(2024, description="NFL season year")
):
    """Get comprehensive week analysis with real data insights"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with RealDataNFLPredictionService() as service:
            await service.initialize_models()
            analysis = await service.get_comprehensive_week_analysis(week, season)

            logger.info(f"Generated comprehensive analysis for week {week}")
            return analysis

    except Exception as e:
        logger.error(f"Error generating comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate analysis: {str(e)}")

@router.get("/analysis/injuries")
async def get_injury_impact_analysis(
    team: Optional[str] = Query(None, description="Team abbreviation to filter by")
):
    """Get detailed injury impact analysis"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with RealDataNFLPredictionService() as service:
            analysis = await service.get_injury_impact_analysis(team.upper() if team else None)

            logger.info("Generated injury impact analysis")
            return analysis

    except Exception as e:
        logger.error(f"Error generating injury analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze injuries: {str(e)}")

@router.get("/analysis/weather")
async def get_weather_impact_analysis():
    """Get weather impact analysis for outdoor games"""
    if not check_real_data_service():
        raise HTTPException(status_code=503, detail="Real data service not available")

    try:
        async with RealDataNFLPredictionService() as service:
            analysis = await service.get_weather_impact_analysis()

            logger.info("Generated weather impact analysis")
            return analysis

    except Exception as e:
        logger.error(f"Error generating weather analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze weather: {str(e)}")

# Fallback endpoints when real data is not available
@router.get("/fallback/status")
async def fallback_status():
    """Fallback status when real data service is unavailable"""
    return {
        "service_available": False,
        "real_data_enabled": REAL_DATA_AVAILABLE,
        "api_key_configured": bool(os.getenv('VITE_SPORTSDATA_IO_KEY')),
        "message": "Real data service is not available. Check dependencies and API key.",
        "dependencies": {
            "aiohttp": "Not available" if not REAL_DATA_AVAILABLE else "Available",
            "api_key": "Configured" if os.getenv('VITE_SPORTSDATA_IO_KEY') else "Not configured"
        },
        "last_updated": datetime.now().isoformat()
    }

# Test endpoint for connectivity
@router.get("/test/connectivity")
async def test_connectivity():
    """Test API connectivity without full service initialization"""
    api_key = os.getenv('VITE_SPORTSDATA_IO_KEY')

    if not api_key:
        raise HTTPException(status_code=400, detail="API key not configured")

    try:
        import requests

        # Simple test with requests library
        base_url = "https://api.sportsdata.io/v3/nfl"
        endpoint = f"{base_url}/scores/json/Scores/2024"

        params = {'key': api_key}

        response = requests.get(endpoint, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "api_responsive": True,
                "games_available": len(data),
                "sample_game": {
                    "away_team": data[0].get('AwayTeam') if data else None,
                    "home_team": data[0].get('HomeTeam') if data else None,
                    "week": data[0].get('Week') if data else None
                } if data else None,
                "tested_at": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "api_responsive": False,
                "status_code": response.status_code,
                "error": "API request failed",
                "tested_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Connectivity test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Connectivity test failed: {str(e)}")

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check for the real data service"""
    return {
        "status": "healthy" if check_real_data_service() else "degraded",
        "real_data_available": REAL_DATA_AVAILABLE,
        "api_key_configured": bool(os.getenv('VITE_SPORTSDATA_IO_KEY')),
        "timestamp": datetime.now().isoformat()
    }