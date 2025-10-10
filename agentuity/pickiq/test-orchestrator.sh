#!/bin/bash
# Test script for NFL Expert Orchestrator

echo "🧪 Testing NFL Expert Orchestrator..."
echo ""
echo "📡 Sending request to http://localhost:3500/run/game-orchestrator"
echo ""

curl -X POST http://localhost:3500/run/game-orchestrator \
  -H "Content-Type: application/json" \
  -d '{
    "game_id": "test_chiefs_bills_2025",
    "expert_ids": ["the-analyst", "the-rebel", "the-rider", "the-hunter"],
    "gameContext": {
      "homeTeam": "Kansas City Chiefs",
      "awayTeam": "Buffalo Bills",
      "gameTime": "2025-01-26T20:00:00Z"
    },
    "memories": [
      {
        "memoryId": "mem_playoff_history_001",
        "content": "Chiefs vs Bills playoff history: 3 meetings, Chiefs lead 2-1. Average margin: 6.3 points.",
        "similarity": 0.87
      },
      {
        "memoryId": "mem_defensive_stats_002",
        "content": "Buffalo defense allows 19.2 PPG, Kansas City defense allows 21.5 PPG this season.",
        "similarity": 0.82
      }
    ],
    "run_id": "run_test_2025_10_10"
  }' | jq '.'

echo ""
echo "✅ Test complete!"
echo ""
echo "📊 Check DevMode Dashboard at: https://app.agentuity.com/"
echo "   You should see 5 sessions: 1 orchestrator + 4 experts"
