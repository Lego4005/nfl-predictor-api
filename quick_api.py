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

if __name__ == "__main__":
    print("🚀 Starting Quick NFL API on http://localhost:8080")
    uvicorn.run(app, host="0.0.0.0", port=8080)