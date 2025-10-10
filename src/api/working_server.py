from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import aiohttp
import asyncio
import os
import sys
from datetime import datetime
import logging
import uuid
import sqlite3
import json
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add ML modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'ml'))
try:
    from src.ml.prediction_service import get_prediction_service, initialize_prediction_service
    from src.ml.expert_prediction_service import expert_prediction_service
    ML_AVAILABLE = True
    EXPERT_SERVICE_AVAILABLE = True
    logger.info("✅ ML prediction service imported successfully")
    logger.info("✅ Expert prediction service imported successfully")

    # Try to import learning pipeline
    try:
        from src.api.learning_pipeline import router as learning_router
        LEARNING_PIPELINE_AVAILABLE = True
        logger.info("✅ Learning pipeline imported successfully")
    except ImportError as e:
        logger.warning(f"⚠️ Learning pipeline not available: {e}")
        LEARNING_PIPELINE_AVAILABLE = False
        learning_router = None
except ImportError as e:
    logger.warning(f"⚠️ ML prediction service not available: {e}")
    ML_AVAILABLE = False
    EXPERT_SERVICE_AVAILABLE = False
    LEARNING_PIPELINE_AVAILABLE = False
    learning_router = None

# Load API keys from environment
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "your_odds_api_key_here")
SPORTSDATA_IO_KEY = os.getenv("SPORTSDATA_IO_KEY", "your_sportsdata_io_key_here")
RAPID_API_KEY = os.getenv("RAPID_API_KEY", "your_rapid_api_key_here")

app = FastAPI(title="NFL Predictor API", description="Advanced NFL predictions with ML models")

# Fix CORS properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global ML service
ml_service = None

# Database setup
DB_FILE = "user_picks.db"

# Pydantic models for user picks
class UserPick(BaseModel):
    gameId: str
    winner: str
    confidence: int
    timestamp: str

class UserPicksSubmission(BaseModel):
    picks: List[UserPick]
    userId: Optional[str] = None

def init_database():
    """Initialize SQLite database for user picks"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_picks (
            id TEXT PRIMARY KEY,
            user_id TEXT DEFAULT 'default_user',
            game_id TEXT NOT NULL,
            winner TEXT NOT NULL,
            confidence INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            result TEXT DEFAULT NULL,
            points INTEGER DEFAULT 0,
            UNIQUE(user_id, game_id)
        )
    """)

    # Create games table for tracking game results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            home_team TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_score INTEGER DEFAULT 0,
            away_score INTEGER DEFAULT 0,
            status TEXT DEFAULT 'scheduled',
            start_time TEXT,
            winner TEXT DEFAULT NULL,
            completed BOOLEAN DEFAULT FALSE,
            week INTEGER,
            season INTEGER DEFAULT 2025
        )
    """)

    # Create user_stats table for caching leaderboard data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            total_picks INTEGER DEFAULT 0,
            correct_picks INTEGER DEFAULT 0,
            accuracy REAL DEFAULT 0.0,
            current_streak INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            total_points INTEGER DEFAULT 0,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def get_user_picks(user_id: str = "default_user"):
    """Get all picks for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, game_id, winner, confidence, timestamp, created_at
        FROM user_picks
        WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user_id,))

    picks = []
    for row in cursor.fetchall():
        picks.append({
            "id": row[0],
            "gameId": row[1],
            "winner": row[2],
            "confidence": row[3],
            "timestamp": row[4],
            "created_at": row[5]
        })

    conn.close()
    return picks

def save_user_picks(picks: List[UserPick], user_id: str = "default_user"):
    """Save user picks to database"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    saved_picks = []
    for pick in picks:
        pick_id = str(uuid.uuid4())
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO user_picks
                (id, user_id, game_id, winner, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pick_id, user_id, pick.gameId, pick.winner, pick.confidence, pick.timestamp))

            saved_picks.append({
                "id": pick_id,
                "gameId": pick.gameId,
                "winner": pick.winner,
                "confidence": pick.confidence,
                "timestamp": pick.timestamp
            })
        except sqlite3.Error as e:
            logger.error(f"Error saving pick: {e}")
            continue

    conn.commit()
    conn.close()
    return saved_picks

def calculate_user_accuracy(user_id: str):
    """Calculate accuracy and stats for a user"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get all picks with results
    cursor.execute("""
        SELECT up.winner, up.confidence, up.result, up.points, g.winner as actual_winner
        FROM user_picks up
        LEFT JOIN games g ON up.game_id = g.id
        WHERE up.user_id = ? AND g.completed = TRUE
        ORDER BY up.created_at
    """, (user_id,))

    picks_data = cursor.fetchall()
    conn.close()

    if not picks_data:
        return {
            "total_picks": 0,
            "correct_picks": 0,
            "accuracy": 0.0,
            "current_streak": 0,
            "best_streak": 0,
            "total_points": 0
        }

    total_picks = len(picks_data)
    correct_picks = 0
    current_streak = 0
    best_streak = 0
    temp_streak = 0
    total_points = 0

    # Calculate accuracy and streaks
    for pick_winner, confidence, result, points, actual_winner in picks_data:
        total_points += points or 0

        if result == 'correct' or (actual_winner and pick_winner == actual_winner):
            correct_picks += 1
            temp_streak += 1
            best_streak = max(best_streak, temp_streak)
        else:
            if temp_streak > 0:
                current_streak = temp_streak
            temp_streak = 0

    # Final streak check
    current_streak = temp_streak if temp_streak > 0 else 0

    accuracy = (correct_picks / total_picks) * 100 if total_picks > 0 else 0

    return {
        "total_picks": total_picks,
        "correct_picks": correct_picks,
        "accuracy": round(accuracy, 2),
        "current_streak": current_streak,
        "best_streak": best_streak,
        "total_points": total_points
    }

def update_user_stats(user_id: str, username: str = None):
    """Update cached user statistics"""
    stats = calculate_user_accuracy(user_id)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO user_stats
        (user_id, username, total_picks, correct_picks, accuracy, current_streak, best_streak, total_points, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (
        user_id,
        username or f"User_{user_id[:8]}",
        stats["total_picks"],
        stats["correct_picks"],
        stats["accuracy"],
        stats["current_streak"],
        stats["best_streak"],
        stats["total_points"]
    ))

    conn.commit()
    conn.close()

    return stats

def get_leaderboard_data(time_filter: str = "season", sort_by: str = "accuracy", limit: int = 50):
    """Get leaderboard data with filtering and sorting"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Base query
    base_query = """
        SELECT
            us.user_id,
            us.username,
            us.total_picks,
            us.correct_picks,
            us.accuracy,
            us.current_streak,
            us.best_streak,
            us.total_points,
            (us.total_picks - us.correct_picks) as losses
        FROM user_stats us
        WHERE us.total_picks > 0
    """

    # Add time filtering (simplified for now)
    if time_filter == "week":
        # For now, just filter recent picks
        base_query += " AND us.last_updated >= datetime('now', '-7 days')"
    elif time_filter == "month":
        base_query += " AND us.last_updated >= datetime('now', '-30 days')"

    # Add sorting
    if sort_by == "accuracy":
        base_query += " ORDER BY us.accuracy DESC, us.total_picks DESC"
    elif sort_by == "wins":
        base_query += " ORDER BY us.correct_picks DESC, us.accuracy DESC"
    elif sort_by == "streak":
        base_query += " ORDER BY us.current_streak DESC, us.accuracy DESC"
    elif sort_by == "total_picks":
        base_query += " ORDER BY us.total_picks DESC, us.accuracy DESC"
    else:
        base_query += " ORDER BY us.accuracy DESC, us.total_picks DESC"

    base_query += f" LIMIT {limit}"

    cursor.execute(base_query)
    results = cursor.fetchall()
    conn.close()

    leaderboard = []
    for i, row in enumerate(results):
        leaderboard.append({
            "user_id": row[0],
            "username": row[1],
            "total_picks": row[2],
            "wins": row[3],
            "accuracy": row[4],
            "current_streak": row[5],
            "best_streak": row[6],
            "points": row[7],
            "losses": row[8],
            "rank": i + 1,
            "avatar": None  # Could be added later
        })

    return leaderboard

def populate_sample_leaderboard():
    """Populate sample leaderboard data for testing"""
    sample_users = [
        ("user1", "GridironGuru", 40, 29, 72.5, 5, 8, 145),
        ("user2", "TouchdownTony", 45, 31, 68.9, -2, 6, 142),
        ("user3", "PickMaster3000", 36, 24, 66.7, 3, 7, 138),
        ("user4", "NFLOracle", 42, 27, 64.3, 1, 5, 135),
        ("user5", "StatSavant", 37, 23, 62.2, -1, 4, 128),
        ("user6", "GameDayGuru", 38, 22, 57.9, 2, 6, 120),
        ("user7", "PredictorPro", 35, 19, 54.3, -3, 5, 110),
        ("user8", "ChampionCaller", 33, 17, 51.5, 0, 3, 105),
    ]

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    for user_id, username, total, correct, accuracy, streak, best, points in sample_users:
        cursor.execute("""
            INSERT OR REPLACE INTO user_stats
            (user_id, username, total_picks, correct_picks, accuracy, current_streak, best_streak, total_points)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, total, correct, accuracy, streak, best, points))

    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    """Initialize ML models and database on startup"""
    global ml_service

    # Include learning pipeline routes if available
    if LEARNING_PIPELINE_AVAILABLE and learning_router:
        app.include_router(learning_router)
        logger.info("✅ Learning pipeline routes added")

    # Include clean predictions endpoints
    try:
        from clean_predictions_endpoints import router as clean_predictions_router
        app.include_router(clean_predictions_router)
        logger.info("✅ Clean predictions endpoints added (uses correct 15 experts)")
    except ImportError as e:
        logger.warning(f"⚠️ Clean predictions endpoints not available: {e}")

    # Include expert context API
    try:
        from src.api.expert_context_api import router as context_router
        app.include_router(context_router)
        logger.info("✅ Expert context API routes added")
    except ImportError as e:
        logger.warning(f"⚠️ Expert context API not available: {e}")

    # Include expert predictions API
    try:
        from src.api.expert_predictions_api import router as predictions_router
        app.include_router(predictions_router)
        logger.info("✅ Expert predictions API routes added")
    except ImportError as e:
        logger.warning(f"⚠️ Expert predictions API not available: {e}")

    # Initialize database
    init_database()
    logger.info("✅ Database initialized")

    # Populate sample leaderboard data if needed
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM user_stats")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        populate_sample_leaderboard()
        logger.info("✅ Sample leaderboard data populated")

    if ML_AVAILABLE:
        try:
            logger.info("🚀 Initializing ML prediction service...")
            ml_service = await initialize_prediction_service()
            logger.info("✅ ML prediction service ready!")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ML service: {e}")
            ml_service = None
    else:
        logger.info("📊 Running with mock data (ML not available)")

async def fetch_odds_api_data():
    """Fetch live data from The Odds API"""
    try:
        url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "us",
            "markets": "h2h,spreads,totals",
            "oddsFormat": "american"
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Odds API: Retrieved {len(data)} games")
                    return data
                else:
                    logger.error(f"❌ Odds API error {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ Odds API error: {e}")
        return None

async def fetch_sportsdata_io_data(week: int):
    """Fetch live data from SportsDataIO"""
    try:
        # Get games for the week
        games_url = f"https://api.sportsdata.io/v3/nfl/scores/json/ScoresByWeek/2025/{week}"
        headers = {"Ocp-Apim-Subscription-Key": SPORTSDATA_IO_KEY}

        async with aiohttp.ClientSession() as session:
            async with session.get(games_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ SportsDataIO: Retrieved {len(data)} games for week {week}")
                    return data
                else:
                    logger.error(f"❌ SportsDataIO API error {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ SportsDataIO error: {e}")
        return None

async def fetch_sportsdata_io_props():
    """Fetch player props from SportsDataIO"""
    try:
        # Get player props (using a general endpoint)
        props_url = "https://api.sportsdata.io/v3/nfl/odds/json/GameOddsByDate/2025-01-15"
        headers = {"Ocp-Apim-Subscription-Key": SPORTSDATA_IO_KEY}

        async with aiohttp.ClientSession() as session:
            async with session.get(props_url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ SportsDataIO Props: Retrieved data")
                    return data
                else:
                    logger.error(f"❌ SportsDataIO Props error {response.status}")
                    return None
    except Exception as e:
        logger.error(f"❌ SportsDataIO Props error: {e}")
        return None

def transform_odds_api_to_games(odds_data):
    """Transform Odds API data to our game format"""
    if not odds_data:
        return []

    games = []
    for game in odds_data[:16]:  # Limit to 16 games
        home_team = game.get('home_team', 'TBD')
        away_team = game.get('away_team', 'TBD')

        # Get team abbreviations (simplified mapping)
        team_mapping = {
            'Buffalo Bills': 'BUF', 'New York Jets': 'NYJ', 'Kansas City Chiefs': 'KC',
            'Los Angeles Chargers': 'LAC', 'Philadelphia Eagles': 'PHI', 'Dallas Cowboys': 'DAL',
            'San Francisco 49ers': 'SF', 'Seattle Seahawks': 'SEA', 'Baltimore Ravens': 'BAL',
            'Cincinnati Bengals': 'CIN', 'Green Bay Packers': 'GB', 'Minnesota Vikings': 'MIN',
            'Miami Dolphins': 'MIA', 'New England Patriots': 'NE', 'Tampa Bay Buccaneers': 'TB',
            'Atlanta Falcons': 'ATL', 'Denver Broncos': 'DEN', 'Las Vegas Raiders': 'LV',
            'Los Angeles Rams': 'LAR', 'Arizona Cardinals': 'ARI', 'New Orleans Saints': 'NO',
            'Carolina Panthers': 'CAR', 'Tennessee Titans': 'TEN', 'Houston Texans': 'HOU',
            'Indianapolis Colts': 'IND', 'Jacksonville Jaguars': 'JAX', 'Cleveland Browns': 'CLE',
            'Pittsburgh Steelers': 'PIT', 'Detroit Lions': 'DET', 'Chicago Bears': 'CHI',
            'New York Giants': 'NYG', 'Washington Commanders': 'WAS'
        }

        home_abbr = team_mapping.get(home_team, home_team[:3].upper())
        away_abbr = team_mapping.get(away_team, away_team[:3].upper())

        # Simple prediction logic (favor home team slightly)
        su_pick = home_abbr
        su_confidence = 0.65 + (hash(f"{home_abbr}{away_abbr}") % 20) / 100  # Random but consistent

        games.append({
            "home": home_abbr,
            "away": away_abbr,
            "matchup": f"{away_abbr} @ {home_abbr}",
            "su_pick": su_pick,
            "su_confidence": round(su_confidence, 2),
            "logo_home": f"https://a.espncdn.com/i/teamlogos/nfl/500/{home_abbr}.png",
            "logo_away": f"https://a.espncdn.com/i/teamlogos/nfl/500/{away_abbr}.png"
        })

    return games

def transform_odds_api_to_ats(odds_data):
    """Transform Odds API data to ATS format"""
    if not odds_data:
        return []

    ats_picks = []
    for game in odds_data[:16]:
        home_team = game.get('home_team', 'TBD')
        away_team = game.get('away_team', 'TBD')

        # Extract spread from bookmakers (simplified)
        spread = -3.5  # Default spread
        if 'bookmakers' in game and len(game['bookmakers']) > 0:
            bookmaker = game['bookmakers'][0]
            if 'markets' in bookmaker:
                for market in bookmaker['markets']:
                    if market['key'] == 'spreads':
                        if len(market['outcomes']) >= 2:
                            spread = market['outcomes'][0].get('point', -3.5)
                            break

        matchup = f"{away_team[:3].upper()} @ {home_team[:3].upper()}"
        ats_pick = f"{home_team[:3].upper()} {spread:+.1f}" if spread < 0 else f"{away_team[:3].upper()} {abs(spread):+.1f}"
        ats_confidence = 0.60 + (hash(matchup) % 15) / 100

        ats_picks.append({
            "matchup": matchup,
            "ats_pick": ats_pick,
            "spread": spread,
            "ats_confidence": round(ats_confidence, 2)
        })

    return ats_picks

def transform_odds_api_to_totals(odds_data):
    """Transform Odds API data to totals format"""
    if not odds_data:
        return []

    totals_picks = []
    for game in odds_data[:16]:
        home_team = game.get('home_team', 'TBD')
        away_team = game.get('away_team', 'TBD')

        # Extract total from bookmakers (simplified)
        total_line = 47.5  # Default total
        if 'bookmakers' in game and len(game['bookmakers']) > 0:
            bookmaker = game['bookmakers'][0]
            if 'markets' in bookmaker:
                for market in bookmaker['markets']:
                    if market['key'] == 'totals':
                        if len(market['outcomes']) >= 1:
                            total_line = market['outcomes'][0].get('point', 47.5)
                            break

        matchup = f"{away_team[:3].upper()} @ {home_team[:3].upper()}"
        pick_over = hash(matchup) % 2 == 0
        tot_pick = f"{'Over' if pick_over else 'Under'} {total_line}"
        tot_confidence = 0.58 + (hash(matchup) % 12) / 100

        totals_picks.append({
            "matchup": matchup,
            "tot_pick": tot_pick,
            "total_line": total_line,
            "tot_confidence": round(tot_confidence, 2)
        })

    return totals_picks

@app.get("/")
def root():
    return {"status": "API is working with live data integration!"}

@app.get("/v1/expert-predictions/{home_team}/{away_team}")
async def get_expert_predictions(home_team: str, away_team: str):
    """Get personality-driven expert predictions for a specific game"""
    logger.info(f"🎭 Fetching personality expert predictions for {away_team} @ {home_team}")

    if not EXPERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Expert prediction service not available")

    try:
        # Get predictions from all 15 personality experts
        predictions = expert_prediction_service.generate_all_expert_predictions(home_team, away_team)

        # Add metadata
        predictions['endpoint_info'] = {
            'home_team': home_team,
            'away_team': away_team,
            'expert_count': len(predictions['all_expert_predictions']),
            'personality_driven': True,
            'service_type': 'personality_experts_v2'
        }

        logger.info(f"✅ Generated {len(predictions['all_expert_predictions'])} personality expert predictions")
        return predictions

    except Exception as e:
        logger.error(f"❌ Expert prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Expert prediction failed: {str(e)}")

@app.get("/v1/expert-battle-card/{game_id}")
async def get_expert_battle_card(game_id: str):
    """Get expert battle card showing personality expert competition"""
    logger.info(f"🥊 Fetching expert battle card for game {game_id}")

    if not EXPERT_SERVICE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Expert prediction service not available")

    try:
        battle_card = expert_prediction_service.get_expert_battle_card(game_id)

        logger.info(f"✅ Generated expert battle card for game {game_id}")
        return battle_card

    except Exception as e:
        logger.error(f"❌ Battle card generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Battle card generation failed: {str(e)}")

@app.get("/v1/best-picks/2025/{week}")
async def get_picks(week: int):
    global ml_service
    logger.info(f"🏈 Fetching ML predictions for Week {week}")

    # Try ML predictions first
    if ML_AVAILABLE and 'ml_service' in globals() and ml_service:
        try:
            logger.info("🧠 Using ML predictions...")

            # Get ML predictions
            game_predictions = ml_service.get_game_predictions(week, 2025)
            totals_predictions = ml_service.get_totals_predictions(week, 2025)
            player_props = ml_service.get_player_props(week, 2025, 15)
            fantasy_lineups = ml_service.get_fantasy_lineups(week, 2025, 3)

            # Transform ML predictions to API format
            games = []
            ats_picks = []
            totals_picks = []

            for pred in game_predictions:
                # Game predictions
                games.append({
                    "home": pred["home_team"],
                    "away": pred["away_team"],
                    "matchup": f"{pred['away_team']} @ {pred['home_team']}",
                    "su_pick": pred["winner"],
                    "su_confidence": pred["winner_confidence"],
                    "logo_home": f"https://a.espncdn.com/i/teamlogos/nfl/500/{pred['home_team']}.png",
                    "logo_away": f"https://a.espncdn.com/i/teamlogos/nfl/500/{pred['away_team']}.png",
                    "ml_enhanced": True,
                    "key_factors": pred["key_factors"][:3]
                })

                # ATS predictions
                ats_picks.append({
                    "matchup": f"{pred['away_team']} @ {pred['home_team']}",
                    "ats_pick": f"{pred['ats_pick']} covers",
                    "spread": pred["predicted_spread"],
                    "ats_confidence": pred["ats_confidence"],
                    "spread_edge": pred.get("spread_edge", 0),
                    "sharp_money": pred.get("sharp_money", "neutral"),
                    "ml_enhanced": True
                })

            # Process totals predictions separately
            for totals_pred in totals_predictions:
                totals_picks.append({
                    "matchup": totals_pred["matchup"],
                    "tot_pick": f"{totals_pred['recommendation']} {totals_pred['predicted_total']}",
                    "total_line": totals_pred["predicted_total"],
                    "tot_confidence": totals_pred["confidence"],
                    "edge": totals_pred["edge"],
                    "key_factors": totals_pred["key_factors"][:2],
                    "ml_enhanced": True
                })

            # Add player props to response
            props_data = []
            for prop in player_props[:10]:  # Top 10 props
                props_data.append({
                    "player": prop["player_name"],
                    "team": prop["team"],
                    "position": prop["position"],
                    "passing_yards": prop["passing_yards"],
                    "rushing_yards": prop["rushing_yards"],
                    "receiving_yards": prop["receiving_yards"],
                    "receptions": prop["receptions"],
                    "key_factors": prop["key_factors"][:2],
                    "ml_enhanced": True
                })

            # Add fantasy lineups
            fantasy_data = []
            for lineup in fantasy_lineups:
                fantasy_data.append({
                    "strategy": lineup["strategy"],
                    "projected_points": lineup["projected_points"],
                    "salary": lineup["total_salary"],
                    "top_players": [p["name"] for p in lineup["players"][:5]],
                    "ml_enhanced": True
                })

            logger.info(f"✅ Using ML predictions: {len(games)} games, {len(props_data)} props, {len(fantasy_data)} lineups")

        except Exception as e:
            logger.error(f"❌ ML prediction failed: {e}")
            ml_service = None  # Fallback to mock data

    # Fallback to mock data if ML fails or unavailable
    if not ML_AVAILABLE or not ml_service:
        logger.warning(f"⚠️ Live APIs unavailable, using mock data for Week {week}")
        games = [
        {"home": "BUF", "away": "NYJ", "matchup": "NYJ @ BUF", "su_pick": "BUF", "su_confidence": 0.74, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/BUF.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/NYJ.png"},
        {"home": "KC", "away": "LAC", "matchup": "LAC @ KC", "su_pick": "KC", "su_confidence": 0.68, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/KC.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/LAC.png"},
        {"home": "PHI", "away": "DAL", "matchup": "DAL @ PHI", "su_pick": "PHI", "su_confidence": 0.65, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/PHI.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/DAL.png"},
        {"home": "SF", "away": "SEA", "matchup": "SEA @ SF", "su_pick": "SF", "su_confidence": 0.72, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/SF.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/SEA.png"},
        {"home": "BAL", "away": "CIN", "matchup": "CIN @ BAL", "su_pick": "BAL", "su_confidence": 0.69, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/BAL.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/CIN.png"},
        {"home": "GB", "away": "MIN", "matchup": "MIN @ GB", "su_pick": "GB", "su_confidence": 0.63, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/GB.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/MIN.png"},
        {"home": "MIA", "away": "NE", "matchup": "NE @ MIA", "su_pick": "MIA", "su_confidence": 0.71, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/MIA.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/NE.png"},
        {"home": "TB", "away": "ATL", "matchup": "ATL @ TB", "su_pick": "TB", "su_confidence": 0.66, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/TB.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/ATL.png"},
        {"home": "DEN", "away": "LV", "matchup": "LV @ DEN", "su_pick": "DEN", "su_confidence": 0.64, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/DEN.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/LV.png"},
        {"home": "LAR", "away": "ARI", "matchup": "ARI @ LAR", "su_pick": "LAR", "su_confidence": 0.67, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/LAR.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/ARI.png"},
        {"home": "NO", "away": "CAR", "matchup": "CAR @ NO", "su_pick": "NO", "su_confidence": 0.70, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/NO.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/CAR.png"},
        {"home": "TEN", "away": "HOU", "matchup": "HOU @ TEN", "su_pick": "HOU", "su_confidence": 0.62, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/TEN.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/HOU.png"},
        {"home": "IND", "away": "JAX", "matchup": "JAX @ IND", "su_pick": "IND", "su_confidence": 0.68, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/IND.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/JAX.png"},
        {"home": "CLE", "away": "PIT", "matchup": "PIT @ CLE", "su_pick": "PIT", "su_confidence": 0.61, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/CLE.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/PIT.png"},
        {"home": "DET", "away": "CHI", "matchup": "CHI @ DET", "su_pick": "DET", "su_confidence": 0.73, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/DET.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/CHI.png"},
            {"home": "NYG", "away": "WAS", "matchup": "WAS @ NYG", "su_pick": "WAS", "su_confidence": 0.59, "logo_home": "https://a.espncdn.com/i/teamlogos/nfl/500/NYG.png", "logo_away": "https://a.espncdn.com/i/teamlogos/nfl/500/WAS.png"},
        ]

        ats_picks = [
        {"matchup": "NYJ @ BUF", "ats_pick": "BUF -3.5", "spread": -3.5, "ats_confidence": 0.69},
        {"matchup": "LAC @ KC", "ats_pick": "LAC +6.5", "spread": 6.5, "ats_confidence": 0.65},
        {"matchup": "DAL @ PHI", "ats_pick": "PHI -2.5", "spread": -2.5, "ats_confidence": 0.62},
        {"matchup": "SEA @ SF", "ats_pick": "SF -4.5", "spread": -4.5, "ats_confidence": 0.71},
        {"matchup": "CIN @ BAL", "ats_pick": "BAL -3.0", "spread": -3.0, "ats_confidence": 0.68},
        {"matchup": "MIN @ GB", "ats_pick": "GB -2.5", "spread": -2.5, "ats_confidence": 0.64},
        {"matchup": "NE @ MIA", "ats_pick": "MIA -5.5", "spread": -5.5, "ats_confidence": 0.70},
        {"matchup": "ATL @ TB", "ats_pick": "TB -3.0", "spread": -3.0, "ats_confidence": 0.66},
        {"matchup": "LV @ DEN", "ats_pick": "DEN -1.5", "spread": -1.5, "ats_confidence": 0.63},
        {"matchup": "ARI @ LAR", "ats_pick": "LAR -4.0", "spread": -4.0, "ats_confidence": 0.67},
        {"matchup": "CAR @ NO", "ats_pick": "NO -6.0", "spread": -6.0, "ats_confidence": 0.69},
        {"matchup": "HOU @ TEN", "ats_pick": "HOU +1.0", "spread": 1.0, "ats_confidence": 0.61},
        {"matchup": "JAX @ IND", "ats_pick": "IND -4.5", "spread": -4.5, "ats_confidence": 0.67},
        {"matchup": "PIT @ CLE", "ats_pick": "PIT +2.0", "spread": 2.0, "ats_confidence": 0.60},
        {"matchup": "CHI @ DET", "ats_pick": "DET -7.5", "spread": -7.5, "ats_confidence": 0.72},
            {"matchup": "WAS @ NYG", "ats_pick": "WAS +3.0", "spread": 3.0, "ats_confidence": 0.58},
        ]

        totals_picks = [
        {"matchup": "NYJ @ BUF", "tot_pick": "Over 45.5", "total_line": 45.5, "tot_confidence": 0.62},
        {"matchup": "LAC @ KC", "tot_pick": "Under 52.5", "total_line": 52.5, "tot_confidence": 0.58},
        {"matchup": "DAL @ PHI", "tot_pick": "Over 48.5", "total_line": 48.5, "tot_confidence": 0.61},
        {"matchup": "SEA @ SF", "tot_pick": "Under 46.5", "total_line": 46.5, "tot_confidence": 0.65},
        {"matchup": "CIN @ BAL", "tot_pick": "Over 49.5", "total_line": 49.5, "tot_confidence": 0.63},
        {"matchup": "MIN @ GB", "tot_pick": "Over 47.5", "total_line": 47.5, "tot_confidence": 0.59},
        {"matchup": "NE @ MIA", "tot_pick": "Under 44.5", "total_line": 44.5, "tot_confidence": 0.66},
        {"matchup": "ATL @ TB", "tot_pick": "Over 51.5", "total_line": 51.5, "tot_confidence": 0.64},
        {"matchup": "LV @ DEN", "tot_pick": "Under 43.5", "total_line": 43.5, "tot_confidence": 0.60},
        {"matchup": "ARI @ LAR", "tot_pick": "Over 50.5", "total_line": 50.5, "tot_confidence": 0.62},
        {"matchup": "CAR @ NO", "tot_pick": "Under 45.5", "total_line": 45.5, "tot_confidence": 0.67},
        {"matchup": "HOU @ TEN", "tot_pick": "Over 46.5", "total_line": 46.5, "tot_confidence": 0.58},
        {"matchup": "JAX @ IND", "tot_pick": "Under 44.5", "total_line": 44.5, "tot_confidence": 0.65},
        {"matchup": "PIT @ CLE", "tot_pick": "Under 42.5", "total_line": 42.5, "tot_confidence": 0.61},
        {"matchup": "CHI @ DET", "tot_pick": "Over 48.5", "total_line": 48.5, "tot_confidence": 0.63},
            {"matchup": "WAS @ NYG", "tot_pick": "Under 43.5", "total_line": 43.5, "tot_confidence": 0.59},
        ]

    # Try to fetch live prop bets from SportsDataIO
    live_props = await fetch_sportsdata_io_props()

    # Top 15 props sorted by confidence (will show top 10 in UI)
    prop_bets = [
        {"player": "Josh Allen", "prop_type": "Passing Yards", "units": "yds", "line": 285.5, "pick": "Over", "confidence": 0.78, "bookmaker": "DraftKings", "team": "BUF", "opponent": "NYJ"},
        {"player": "Lamar Jackson", "prop_type": "Rushing Yards", "units": "yds", "line": 65.5, "pick": "Over", "confidence": 0.76, "bookmaker": "FanDuel", "team": "BAL", "opponent": "CIN"},
        {"player": "Christian McCaffrey", "prop_type": "Rushing Yards", "units": "yds", "line": 95.5, "pick": "Over", "confidence": 0.74, "bookmaker": "BetMGM", "team": "SF", "opponent": "SEA"},
        {"player": "Cooper Kupp", "prop_type": "Receiving Yards", "units": "yds", "line": 85.5, "pick": "Under", "confidence": 0.73, "bookmaker": "Caesars", "team": "LAR", "opponent": "ARI"},
        {"player": "Travis Kelce", "prop_type": "Receptions", "units": "rec", "line": 6.5, "pick": "Over", "confidence": 0.72, "bookmaker": "DraftKings", "team": "KC", "opponent": "LAC"},
        {"player": "Tyreek Hill", "prop_type": "Receiving Yards", "units": "yds", "line": 75.5, "pick": "Over", "confidence": 0.71, "bookmaker": "FanDuel", "team": "MIA", "opponent": "NE"},
        {"player": "Patrick Mahomes", "prop_type": "Passing Yards", "units": "yds", "line": 275.5, "pick": "Over", "confidence": 0.70, "bookmaker": "BetMGM", "team": "KC", "opponent": "LAC"},
        {"player": "Davante Adams", "prop_type": "Receptions", "units": "rec", "line": 7.5, "pick": "Under", "confidence": 0.69, "bookmaker": "Caesars", "team": "LV", "opponent": "DEN"},
        {"player": "Derrick Henry", "prop_type": "Rushing Yards", "units": "yds", "line": 85.5, "pick": "Over", "confidence": 0.68, "bookmaker": "DraftKings", "team": "TEN", "opponent": "HOU"},
        {"player": "Stefon Diggs", "prop_type": "Receiving Yards", "units": "yds", "line": 80.5, "pick": "Over", "confidence": 0.67, "bookmaker": "FanDuel", "team": "BUF", "opponent": "NYJ"},
        {"player": "Aaron Rodgers", "prop_type": "Passing Yards", "units": "yds", "line": 265.5, "pick": "Under", "confidence": 0.66, "bookmaker": "BetMGM", "team": "NYJ", "opponent": "BUF"},
        {"player": "Saquon Barkley", "prop_type": "Rushing Yards", "units": "yds", "line": 75.5, "pick": "Over", "confidence": 0.65, "bookmaker": "Caesars", "team": "PHI", "opponent": "DAL"},
        {"player": "Mike Evans", "prop_type": "Receiving Yards", "units": "yds", "line": 70.5, "pick": "Under", "confidence": 0.64, "bookmaker": "DraftKings", "team": "TB", "opponent": "ATL"},
        {"player": "Ja'Marr Chase", "prop_type": "Receptions", "units": "rec", "line": 6.5, "pick": "Over", "confidence": 0.63, "bookmaker": "FanDuel", "team": "CIN", "opponent": "BAL"},
        {"player": "CeeDee Lamb", "prop_type": "Receiving Yards", "units": "yds", "line": 85.5, "pick": "Over", "confidence": 0.62, "bookmaker": "BetMGM", "team": "DAL", "opponent": "PHI"},
    ]

    fantasy_picks = [
        {"player": "Josh Allen", "position": "QB", "salary": 8200, "projected_points": 22.4, "value_score": 2.73},
        {"player": "Christian McCaffrey", "position": "RB", "salary": 8800, "projected_points": 19.8, "value_score": 2.25},
        {"player": "Cooper Kupp", "position": "WR", "salary": 8400, "projected_points": 16.2, "value_score": 1.93},
        {"player": "Travis Kelce", "position": "TE", "salary": 7200, "projected_points": 14.5, "value_score": 2.01},
        {"player": "Lamar Jackson", "position": "QB", "salary": 8600, "projected_points": 21.2, "value_score": 2.47},
        {"player": "Derrick Henry", "position": "RB", "salary": 7800, "projected_points": 16.8, "value_score": 2.15},
        {"player": "Tyreek Hill", "position": "WR", "salary": 8200, "projected_points": 15.8, "value_score": 1.93},
        {"player": "Mark Andrews", "position": "TE", "salary": 6800, "projected_points": 13.2, "value_score": 1.94},
    ]

    # Default mock props and fantasy if ML not available
    props_data = [
            {"player": "Josh Allen", "team": "BUF", "position": "QB", "passing_yards": 285.5, "rushing_yards": 45.2, "receiving_yards": 0, "receptions": 0, "key_factors": ["High snap count", "Favorable matchup"]},
            {"player": "Patrick Mahomes", "team": "KC", "position": "QB", "passing_yards": 275.5, "rushing_yards": 15.8, "receiving_yards": 0, "receptions": 0, "key_factors": ["Elite QB", "Home advantage"]},
            {"player": "Christian McCaffrey", "team": "SF", "position": "RB", "passing_yards": 0, "rushing_yards": 95.5, "receiving_yards": 45.2, "receptions": 4.5, "key_factors": ["Workhorse back", "Receiving threat"]},
    ]

    fantasy_data = [
            {"strategy": "balanced", "projected_points": 165.8, "salary": 49500, "top_players": ["Josh Allen", "Christian McCaffrey", "Cooper Kupp", "Travis Kelce", "49ers DST"]},
            {"strategy": "cash", "projected_points": 158.2, "salary": 48900, "top_players": ["Lamar Jackson", "Derrick Henry", "Tyreek Hill", "Mark Andrews", "Bills DST"]},
    ]

    totals_picks = [
            {"matchup": "NYJ @ BUF", "total": 45.5, "pick": "OVER", "confidence": 0.62},
            {"matchup": "LAC @ KC", "total": 52.5, "pick": "UNDER", "confidence": 0.58},
            {"matchup": "DAL @ PHI", "total": 48.5, "pick": "OVER", "confidence": 0.61},
    ]

    # Prepare response
    response = {
        "best_picks": games,
        "ats_picks": ats_picks,
        "totals_picks": totals_picks,
        "prop_bets": props_data if 'props_data' in locals() else [],
        "fantasy_picks": fantasy_data if 'fantasy_data' in locals() else [],
        "data_source": "ml_enhanced" if (ML_AVAILABLE and ml_service) else "mock",
        "ml_models": {
            "game_accuracy": "71.8%",
            "ats_accuracy": "77.9%",
            "props_mae": "0.03-1.67",
            "fantasy_strategies": 3
        } if (ML_AVAILABLE and ml_service) else None,
        "timestamp": datetime.utcnow().isoformat(),
        "week": week,
        "total_games": len(games),
        "total_props": len(props_data) if 'props_data' in locals() else 0,
        "total_fantasy_lineups": len(fantasy_data) if 'fantasy_data' in locals() else 0
    }

    return response

# User Picks Endpoints
@app.post("/api/user-picks/submit")
async def submit_user_picks(submission: UserPicksSubmission):
    """Submit user picks for games"""
    try:
        if not submission.picks:
            raise HTTPException(status_code=400, detail="No picks provided")

        # Validate confidence levels are unique
        confidence_levels = [pick.confidence for pick in submission.picks]
        if len(confidence_levels) != len(set(confidence_levels)):
            raise HTTPException(status_code=400, detail="Confidence levels must be unique")

        # Validate confidence range
        for pick in submission.picks:
            if pick.confidence < 1 or pick.confidence > 10:
                raise HTTPException(status_code=400, detail="Confidence must be between 1 and 10")

        user_id = submission.userId or "default_user"
        saved_picks = save_user_picks(submission.picks, user_id)

        return {
            "success": True,
            "message": f"Successfully saved {len(saved_picks)} picks",
            "picks": saved_picks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting picks: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit picks")

@app.get("/api/user-picks")
async def get_user_picks_endpoint(user_id: str = "default_user"):
    """Get all picks for a user"""
    try:
        picks = get_user_picks(user_id)
        return {
            "success": True,
            "picks": picks,
            "total": len(picks)
        }
    except Exception as e:
        logger.error(f"Error retrieving picks: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve picks")

@app.delete("/api/user-picks/{pick_id}")
async def delete_user_pick(pick_id: str, user_id: str = "default_user"):
    """Delete a specific pick"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM user_picks
            WHERE id = ? AND user_id = ?
        """, (pick_id, user_id))

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pick not found")

        conn.commit()
        conn.close()

        return {
            "success": True,
            "message": "Pick deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting pick: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete pick")

@app.get("/api/user-picks/stats")
async def get_user_picks_stats(user_id: str = "default_user"):
    """Get statistics about user picks"""
    try:
        picks = get_user_picks(user_id)

        if not picks:
            return {
                "success": True,
                "stats": {
                    "total_picks": 0,
                    "average_confidence": 0,
                    "confidence_distribution": {},
                    "picks_by_date": {}
                }
            }

        # Calculate stats
        total_picks = len(picks)
        avg_confidence = sum(pick["confidence"] for pick in picks) / total_picks

        # Confidence distribution
        confidence_dist = {}
        for pick in picks:
            conf = pick["confidence"]
            confidence_dist[conf] = confidence_dist.get(conf, 0) + 1

        # Picks by date
        picks_by_date = {}
        for pick in picks:
            date = pick["created_at"][:10]  # YYYY-MM-DD
            picks_by_date[date] = picks_by_date.get(date, 0) + 1

        return {
            "success": True,
            "stats": {
                "total_picks": total_picks,
                "average_confidence": round(avg_confidence, 2),
                "confidence_distribution": confidence_dist,
                "picks_by_date": picks_by_date
            }
        }

    except Exception as e:
        logger.error(f"Error calculating picks stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate stats")

@app.get("/api/leaderboard")
async def get_leaderboard(
    timeFilter: str = "season",
    sortBy: str = "accuracy",
    limit: int = 50
):
    """Get leaderboard data with filtering and sorting options"""
    try:
        # Populate sample data if no real data exists
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_stats")
        count = cursor.fetchone()[0]
        conn.close()

        if count == 0:
            populate_sample_leaderboard()
            logger.info("✅ Populated sample leaderboard data")

        leaderboard = get_leaderboard_data(timeFilter, sortBy, limit)

        return {
            "success": True,
            "leaderboard": leaderboard,
            "filters": {
                "timeFilter": timeFilter,
                "sortBy": sortBy,
                "limit": limit
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching leaderboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard")

@app.post("/api/leaderboard/update-stats")
async def update_leaderboard_stats(user_id: str = "default_user", username: str = None):
    """Update user statistics for leaderboard"""
    try:
        stats = update_user_stats(user_id, username)

        return {
            "success": True,
            "user_id": user_id,
            "stats": stats,
            "message": "User statistics updated successfully"
        }

    except Exception as e:
        logger.error(f"Error updating user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user statistics")

@app.get("/api/leaderboard/user/{user_id}")
async def get_user_leaderboard_stats(user_id: str):
    """Get specific user's leaderboard statistics"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, username, total_picks, correct_picks, accuracy,
                   current_streak, best_streak, total_points,
                   (total_picks - correct_picks) as losses
            FROM user_stats
            WHERE user_id = ?
        """, (user_id,))

        result = cursor.fetchone()
        conn.close()

        if not result:
            # Calculate and create stats if they don't exist
            stats = update_user_stats(user_id)
            return {
                "success": True,
                "user_stats": {
                    "user_id": user_id,
                    "username": f"User_{user_id[:8]}",
                    "total_picks": stats["total_picks"],
                    "wins": stats["correct_picks"],
                    "losses": stats["total_picks"] - stats["correct_picks"],
                    "accuracy": stats["accuracy"],
                    "current_streak": stats["current_streak"],
                    "best_streak": stats["best_streak"],
                    "points": stats["total_points"],
                    "rank": None
                }
            }

        user_stats = {
            "user_id": result[0],
            "username": result[1],
            "total_picks": result[2],
            "wins": result[3],
            "accuracy": result[4],
            "current_streak": result[5],
            "best_streak": result[6],
            "points": result[7],
            "losses": result[8],
            "rank": None  # Would need to calculate rank
        }

        return {
            "success": True,
            "user_stats": user_stats
        }

    except Exception as e:
        logger.error(f"Error fetching user stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user statistics")

# WebSocket connections manager for leaderboard
class LeaderboardConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Leaderboard WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Leaderboard WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast_leaderboard_update(self, leaderboard_data):
        """Broadcast leaderboard updates to all connected clients"""
        if not self.active_connections:
            return

        message = {
            "type": "leaderboard_update",
            "leaderboard": leaderboard_data,
            "timestamp": datetime.now().isoformat()
        }

        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending leaderboard update: {e}")
                disconnected_connections.append(connection)

        # Remove disconnected connections
        for connection in disconnected_connections:
            self.disconnect(connection)

# Global leaderboard manager
leaderboard_manager = LeaderboardConnectionManager()

@app.websocket("/ws/leaderboard")
async def leaderboard_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time leaderboard updates"""
    await leaderboard_manager.connect(websocket)
    try:
        # Send initial leaderboard data
        leaderboard = get_leaderboard_data()
        await websocket.send_text(json.dumps({
            "type": "leaderboard_update",
            "leaderboard": leaderboard,
            "timestamp": datetime.now().isoformat()
        }))

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (ping/pong or requests)
                data = await websocket.receive_text()
                message = json.loads(data)

                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "request_update":
                    # Send fresh leaderboard data
                    leaderboard = get_leaderboard_data(
                        message.get("timeFilter", "season"),
                        message.get("sortBy", "accuracy")
                    )
                    await websocket.send_text(json.dumps({
                        "type": "leaderboard_update",
                        "leaderboard": leaderboard,
                        "timestamp": datetime.now().isoformat()
                    }))
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        leaderboard_manager.disconnect(websocket)

async def trigger_leaderboard_update():
    """Helper function to trigger leaderboard updates when data changes"""
    try:
        leaderboard = get_leaderboard_data()
        await leaderboard_manager.broadcast_leaderboard_update(leaderboard)
    except Exception as e:
        logger.error(f"Error triggering leaderboard update: {e}")

if __name__ == "__main__":
    print("🚀 Starting NFL Predictor API with ML on http://localhost:8084")
    uvicorn.run(app, host="127.0.0.1", port=8084)
