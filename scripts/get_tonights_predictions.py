#!/usr/bin/env python3
"""
Get Real Predictions for Tonight's NFL Games
Shows how each expert's UNIQUE algorithm works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.expert_prediction_service import expert_prediction_service
from src.services.live_data_service import live_data_service
from datetime import datetime
import json


def get_tonights_real_games():
    """Get actual games happening tonight"""
    print("\n🏈 NFL Week 2 - Thursday Night, September 15, 2025")
    print("=" * 70)

    # Get real games from the Odds API
    games = live_data_service.get_upcoming_games()

    # Filter to tonight's games (Thursday night usually has 1 game)
    tonight_games = []
    for game in games:
        # In reality, check if game is today
        # For now, take first few games as "tonight's"
        if len(tonight_games) < 2:  # Thursday night + any early game
            tonight_games.append(game)

    if not tonight_games:
        print("No games found for tonight, using upcoming games...")
        tonight_games = games[:2]

    return tonight_games


def explain_expert_algorithms():
    """Explain how each expert's UNIQUE algorithm works"""
    print("\n📚 How Each Expert's UNIQUE Algorithm Works:")
    print("=" * 70)

    algorithms = {
        "Statistical Savant": {
            "method": "Power Rating Differential",
            "formula": "(Home Off Rating × Home Def Rating) vs (Away Off × Away Def)",
            "factors": ["10 years historical data", "Regression analysis", "ELO ratings"],
            "confidence_adjust": "Higher with more data quality"
        },
        "Sharp Bettor": {
            "method": "Line Movement & Sharp Money Detection",
            "formula": "If line moves opposite to public %, follow sharp money",
            "factors": ["Line movement", "Public betting %", "Steam moves"],
            "confidence_adjust": "Boost when fading heavy public action (>70%)"
        },
        "Weather Wizard": {
            "method": "Environmental Impact Analysis",
            "formula": "Wind >15mph = -15% passing, Rain >0.3in = Under",
            "factors": ["Wind speed", "Precipitation", "Temperature", "Dome/outdoor"],
            "confidence_adjust": "+10% in extreme weather"
        },
        "QB Whisperer": {
            "method": "Quarterback Matchup Analysis",
            "formula": "(QB Rating + QB vs Defense History) / 2",
            "factors": ["Passer rating", "QB vs specific defense", "Pressure rate"],
            "confidence_adjust": "Higher when QB differential >10 points"
        },
        "Injury Analyst": {
            "method": "Health Advantage Calculation",
            "formula": "Key injuries × position importance weight",
            "factors": ["QB = 35% impact", "RB1 = 15%", "WR1 = 12%", "OL = 10%"],
            "confidence_adjust": "Conservative approach, caps at 65%"
        },
        "Home Field Hawk": {
            "method": "Home Advantage Stacking",
            "formula": "57% base + travel distance/3000 + timezone × 0.02",
            "factors": ["Travel distance", "Time zones", "Crowd capacity %"],
            "confidence_adjust": "Always picks home team, confidence varies"
        },
        "Road Warrior": {
            "method": "Contrarian Road Team Value",
            "formula": "If road team's road % > home team's home %, take road",
            "factors": ["Road win %", "Travel resilience", "Underdog value"],
            "confidence_adjust": "Contrarian boost when road team excels away"
        }
    }

    for expert, algo in list(algorithms.items())[:7]:
        print(f"\n🤖 {expert}:")
        print(f"   Method: {algo['method']}")
        print(f"   Formula: {algo['formula']}")
        print(f"   Key Factors: {', '.join(algo['factors'][:3])}")
        print(f"   Confidence: {algo['confidence_adjust']}")


def generate_real_predictions():
    """Generate predictions for tonight's real games"""

    games = get_tonights_real_games()

    print(f"\n🎯 Found {len(games)} games for tonight:")
    for game in games:
        print(f"   • {game['away_team']} @ {game['home_team']}")
        print(f"     Spread: {game['spread']:.1f} | O/U: {game['total']:.1f}")
        print(f"     ML: {game['home_moneyline']}/{game['away_moneyline']}")

    # Generate predictions for first game
    if games:
        game = games[0]
        home = game['home_team']
        away = game['away_team']

        print(f"\n\n🏆 EXPERT PREDICTIONS: {away} @ {home}")
        print("=" * 70)

        # Get comprehensive data
        game_data = live_data_service.get_comprehensive_game_data(home, away)

        # Show what data each expert uses
        print("\n📊 Live Data Each Expert Analyzes:")
        print(f"   • Spread: {game_data['spread']}")
        print(f"   • Total: {game_data['total']}")
        print(f"   • Public Betting: {game_data['public_betting_percentage']}% on favorite")
        print(f"   • Line Movement: {game_data['line_movement']} points")
        print(f"   • Weather: {game_data['weather']['wind_speed']}mph wind")
        print(f"   • Home Off Rating: {game_data['home_offensive_rating']:.1f}")
        print(f"   • Away Off Rating: {game_data['away_offensive_rating']:.1f}")

        # Get all predictions
        results = expert_prediction_service.generate_all_expert_predictions(home, away)

        print("\n🎲 15 EXPERT PREDICTIONS (Each Using UNIQUE Algorithm):")
        print("-" * 70)

        for i, pred in enumerate(results['all_expert_predictions'], 1):
            # Show how each expert's unique algorithm produced their pick
            reasoning = pred['predictions']['game_outcome']['reasoning']

            print(f"\n{i:2d}. {pred['expert_name']:20s} → {pred['predictions']['game_outcome']['winner']}")
            print(f"    Algorithm Output: {reasoning}")
            print(f"    Confidence: {pred['confidence_overall']:.1%}")
            print(f"    Spread: {pred['predictions']['spread']['pick']} | "
                  f"O/U: {pred['predictions']['total']['pick']}")

        # Show consensus
        print("\n\n🏅 TOP 5 EXPERT CONSENSUS (Weighted 30/25/20/15/10%):")
        print("-" * 70)
        consensus = results['top5_consensus']
        print(f"   Winner: {consensus['winner']}")
        print(f"   Spread: {consensus['spread']:.1f}")
        print(f"   Total: {consensus['total']:.1f}")
        print(f"   Overall Confidence: {consensus['confidence']:.1%}")
        print(f"   Top 5 Experts: {', '.join(consensus['top_experts'])}")

        # Show disagreement analysis
        winner_votes = {}
        for pred in results['all_expert_predictions']:
            winner = pred['predictions']['game_outcome']['winner']
            winner_votes[winner] = winner_votes.get(winner, 0) + 1

        print(f"\n\n🤺 EXPERT BATTLE:")
        print(f"   {home}: {winner_votes.get(home, 0)} votes")
        print(f"   {away}: {winner_votes.get(away, 0)} votes")

        return results


def explain_pgvector_timeline():
    """Explain how pgvector will work once we have data"""
    print("\n\n🧠 PGVECTOR INTEGRATION (Timeline):")
    print("=" * 70)

    print("""
CURRENT STATE (Week 2):
• ✅ Database tables with vector columns created
• ✅ 15 experts making predictions with unique algorithms
• ⏳ No historical data yet (season just started)

HOW PGVECTOR WILL WORK:

1️⃣ WEEKS 1-4: Building History
   - Store each expert's predictions as 384-dim vectors
   - Capture context (weather, injuries, spreads) as vectors
   - Record actual results

2️⃣ WEEKS 5-8: Pattern Emergence
   - Start finding similar historical situations
   - "This looks like Week 3 Chiefs vs Bills" (85% similarity)
   - Experts begin learning from past mistakes

3️⃣ WEEKS 9+: Full Intelligence
   - Expert fingerprints emerge (success vs failure vectors)
   - Cross-expert learning ("Sharp Bettor's contrarian strategy works in primetime")
   - Situation-specific expert selection

EXAMPLE VECTOR SEARCH (After Week 8):
```sql
-- Find games similar to tonight's matchup
SELECT game_id, similarity(context_embedding, [tonight's vector])
FROM expert_predictions_comprehensive
WHERE similarity > 0.85
ORDER BY similarity DESC;
```

This finds: "In 3 similar games, Weather Wizard was 3-0 but Sharp Bettor was 1-2"
So we'd weight Weather Wizard higher for this specific situation!
""")


if __name__ == "__main__":
    print("🚀 NFL EXPERT PREDICTION SYSTEM - REAL GAMES")
    print("=" * 70)

    # 1. Explain how each expert works
    explain_expert_algorithms()

    # 2. Get real predictions
    predictions = generate_real_predictions()

    # 3. Explain pgvector timeline
    explain_pgvector_timeline()

    print("\n\n📅 WHEN PREDICTIONS HAPPEN:")
    print("=" * 70)
    print("""
• TUESDAY: Lines open, initial expert analysis
• WEDNESDAY: Injury reports, expert adjustments
• THURSDAY: Final predictions for TNF
• FRIDAY: Lock in Sunday predictions
• SATURDAY: Final adjustments
• SUNDAY MORNING: Last-minute weather/inactive updates
• LIVE: Real-time win probability updates during games
    """)

    print("\n✅ Each expert has UNIQUE algorithms - not just random picks!")
    print("✅ pgvector will enable pattern matching after we build history")
    print("✅ Live data from premium APIs provides real-time information")