#!/bin/bash
# Test script for a single NFL Expert (The Analyst)

echo "🧪 Testing Single Expert: The Analyst..."
echo ""
echo "📡 Sending request to http://localhost:3500/run/the-analyst"
echo ""

curl -X POST http://localhost:3500/run/the-analyst \
  -H "Content-Type: application/json" \
  -d '{
    "gameId": "test_single_expert",
    "expertId": "the-analyst",
    "gameContext": {
      "homeTeam": "Kansas City Chiefs",
      "awayTeam": "Buffalo Bills",
      "gameTime": "2025-01-26T20:00:00Z"
    },
    "memories": [
      {
        "memoryId": "mem_001",
        "content": "KC has strong home field advantage, averaging 27.5 points at home",
        "similarity": 0.85
      }
    ]
  }' | jq '.'

echo ""
echo "✅ Single expert test complete!"
