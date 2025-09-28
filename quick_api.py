#!/usr/bin/env python3
"""
Simple FastAPI server for NFL predictions dashboard
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="NFL Predictions API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "NFL Predictions API is running", "status": "active"}

@app.get("/api/health")
async def health():
    return {"status": "healthy", "server": "quick_api"}

@app.get("/api/games")
async def get_games():
    """Mock games data for dashboard"""
    return {
        "games": [
            {
                "id": "BUF@NYJ_20250915",
                "home_team": "NYJ",
                "away_team": "BUF",
                "game_time": "2025-09-15T22:00:00",
                "status": "completed",
                "predictions": {
                    "winner": "BUF",
                    "confidence": 0.72,
                    "spread": -3.0,
                    "total": 48.5
                }
            }
        ]
    }

@app.get("/api/predictions")
async def get_predictions():
    """Mock expert predictions"""
    return {
        "experts": [
            {"name": "Conservative Analyzer", "accuracy": 0.68, "predictions": 24},
            {"name": "Risk Taking Gambler", "accuracy": 0.71, "predictions": 24},
            {"name": "Contrarian Rebel", "accuracy": 0.65, "predictions": 24}
        ]
    }

@app.get("/v1/best-picks/2025/{week}")
async def get_best_picks(week: int):
    """Mock best picks data for dashboard"""
    return {
        "best_picks": [
            {
                "home": "KC",
                "away": "BUF",
                "su_pick": "KC",
                "su_confidence": 0.72,
                "game_time": "2025-09-15T20:20:00Z"
            },
            {
                "home": "SF",
                "away": "DAL",
                "su_pick": "SF",
                "su_confidence": 0.68,
                "game_time": "2025-09-15T23:20:00Z"
            }
        ],
        "ats_picks": [
            {
                "spread": -3.5,
                "ats_pick": "KC",
                "ats_confidence": 0.65
            },
            {
                "spread": 2.5,
                "ats_pick": "SF",
                "ats_confidence": 0.62
            }
        ],
        "totals_picks": [
            {
                "total_line": 48.5,
                "tot_pick": "Over",
                "tot_confidence": 0.58
            },
            {
                "total_line": 44.0,
                "tot_pick": "Under",
                "tot_confidence": 0.55
            }
        ],
        "prop_bets": [
            {
                "player": "Patrick Mahomes",
                "team": "KC",
                "opponent": "BUF",
                "prop_type": "Passing Yards",
                "line": 275.5,
                "pick": "Over",
                "confidence": 0.75,
                "bookmaker": "DraftKings"
            },
            {
                "player": "Josh Allen",
                "team": "BUF",
                "opponent": "KC",
                "prop_type": "Rushing Yards",
                "line": 25.5,
                "pick": "Under",
                "confidence": 0.68,
                "bookmaker": "FanDuel"
            }
        ],
        "fantasy_picks": [
            {
                "player": "Patrick Mahomes",
                "position": "QB",
                "team": "KC",
                "salary": 8500,
                "projected_points": 22.5,
                "value_score": 2.65
            },
            {
                "player": "Josh Allen",
                "position": "QB",
                "team": "BUF",
                "salary": 8200,
                "projected_points": 21.8,
                "value_score": 2.66
            }
        ]
    }

if __name__ == "__main__":
    print("🚀 Starting Quick NFL API on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)