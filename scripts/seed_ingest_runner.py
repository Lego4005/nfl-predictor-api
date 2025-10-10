"""
2020-2023 Training Pass - Build Memory Corpus
Runs all historical games through experts to build episodic memories and calibration

Usage:
  python scripts/seed_ingest_runner.py \
    --run-id run_2025_pilot4 \
    --seasons 2020-2023 \
    --experts the-analyst,the-rebel,the-rider,the-hunter \
    --stakes 0 \
    --reflections off
"""

import asyncio
import argparse
import requests
import time
from datetime import datetime
from typing import List

AGENTUITY_URL = "http://localhost:3500"
BACKEND_URL = "http://localhost:8001"

# Mock historical games for 2020-2023
HISTORICAL_GAMES = [
    {"game_id": "2020_W1_KC_HOU", "season": 2020, "week": 1, "home": "KC", "away": "HOU", "home_score": 34, "away_score": 20},
    {"game_id": "2020_W1_SEA_ATL", "season": 2020, "week": 1, "home": "ATL", "away": "SEA", "home_score": 25, "away_score": 38},
    {"game_id": "2020_W2_BUF_MIA", "season": 2020, "week": 2, "home": "BUF", "away": "MIA", "home_score": 31, "away_score": 28},
    # ... would include all games from 2020-2023
]

async def run_training_pass(
    run_id: str,
    seasons: str,
    experts: List[str],
    stakes: int,
    reflections: bool
):
    """Run training pass through historical games"""
    
    start_year, end_year = map(int, seasons.split('-'))
    games_to_process = [
        game for game in HISTORICAL_GAMES
        if start_year <= game['season'] <= end_year
    ]
    
    print(f"🏈 NFL Training Pass: {seasons}")
    print(f"Run ID: {run_id}")
    print(f"Experts: {', '.join(experts)}")
    print(f"Games to process: {len(games_to_process)}")
    print(f"Stakes: {stakes} (training mode)")
    print(f"Reflections: {'enabled' if reflections else 'disabled'}")
    print("=" * 70)
    
    total_assertions = 0
    total_games = 0
    total_time = 0
    
    for game in games_to_process:
        game_start = time.time()
        
        print(f"\n📊 Processing {game['game_id']} ({game['season']} Week {game['week']})")
        print(f"   {game['away']} @ {game['home']}")
        
        try:
            # Call orchestrator for this game
            response = requests.post(
                f"{AGENTUITY_URL}/agent_game_orchestrator",
                json={
                    "game_id": game['game_id'],
                    "expert_ids": experts,
                    "gameContext": {
                        "homeTeam": game['home'],
                        "awayTeam": game['away'],
                        "gameTime": f"{game['season']}-09-10T20:00:00Z",
                        "week": game['week'],
                        "season": game['season']
                    },
                    "memories": [],
                    "run_id": run_id
                },
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                game_assertions = result.get('orchestration_summary', {}).get('total_predictions', 0)
                successful = result.get('orchestration_summary', {}).get('successful_experts', 0)
                
                total_assertions += game_assertions
                total_games += 1
                
                game_time = time.time() - game_start
                total_time += game_time
                
                print(f"   ✅ {successful}/{len(experts)} experts succeeded")
                print(f"   📝 {game_assertions} assertions generated")
                print(f"   ⏱️  {game_time:.1f}s")
                
                # Simulate settlement (would call real API in production)
                if stakes > 0:
                    print(f"   💰 Settlement skipped (training mode)")
                
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Rate limiting
        await asyncio.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TRAINING PASS SUMMARY")
    print("=" * 70)
    print(f"Total games processed: {total_games}/{len(games_to_process)}")
    print(f"Total assertions: {total_assertions}")
    print(f"Assertions per game: {total_assertions / max(total_games, 1):.1f}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Avg time per game: {total_time / max(total_games, 1):.1f}s")
    print(f"\n✅ Training pass complete!")
    print(f"📈 Memory corpus should now contain {total_games * len(experts)} expert experiences")
    print(f"🎯 Ready for 2024 baseline testing")
    print("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='Run 2020-2023 training pass')
    parser.add_argument('--run-id', required=True, help='Run ID for this training pass')
    parser.add_argument('--seasons', required=True, help='Season range (e.g., 2020-2023)')
    parser.add_argument('--experts', required=True, help='Comma-separated expert list')
    parser.add_argument('--stakes', type=int, default=0, help='Stakes per prediction (0 for training)')
    parser.add_argument('--reflections', choices=['on', 'off'], default='off', help='Enable reflections')
    
    args = parser.parse_args()
    
    experts = args.experts.split(',')
    reflections = args.reflections == 'on'
    
    asyncio.run(run_training_pass(
        args.run_id,
        args.seasons,
        experts,
        args.stakes,
        reflections
    ))

if __name__ == "__main__":
    main()
